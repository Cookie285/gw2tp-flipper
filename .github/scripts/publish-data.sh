#!/usr/bin/env bash
# Schreibt geprüfte Ergebnisse in den Branch `data`.
#
# Läuft nur im Publish-Job (einziger Job mit `contents: write`). Er führt keinen Python-Projektcode
# und keine Abhängigkeiten aus: Das Skript prüft das Artifact streng, kopiert die erlaubten Dateien,
# committet und pusht als normalen Fast-Forward-Push. Nie mit --force.
#
# Aufruf:   publish-data.sh <snapshot|analyze> <incoming-dir>
# Umgebung: GITHUB_SERVER_URL, GITHUB_REPOSITORY, TOKEN
#           DATA_REMOTE (optional, nur für Tests: lokaler Remote statt GitHub)
set -euo pipefail
umask 022
export LC_ALL=C

mode="${1:-}"
incoming="${2:-}"
branch="data"
max_file_bytes=$((2 * 1024 * 1024))
max_remove_lines=2000
retry_sleep="${PUBLISH_RETRY_SLEEP:-5}"

snapshot_re='^snapshots/[0-9]{4}-[0-9]{2}-[0-9]{2}/[0-9]{4}\.json\.gz$'
analyze_re='^(shopping-list\.md|shopping-list\.json|universe\.json|remove\.txt|daily/[0-9]{4}-[0-9]{2}-[0-9]{2}\.json\.gz)$'

die() {
  echo "::error::$*" >&2
  exit 1
}

# Dateinamen nie roh ins Log schreiben (Schutz vor Workflow-Kommandos wie "::set-env").
quote() { printf '%q' "$1" | tr -d ':'; }

case "$mode" in
  snapshot) allowed_re="$snapshot_re" ;;
  analyze) allowed_re="$analyze_re" ;;
  *) die "Unbekannter Modus" ;;
esac
[ -n "$incoming" ] && [ -d "$incoming" ] && [ ! -L "$incoming" ] || die "Eingangsverzeichnis fehlt"
incoming="$(cd "$incoming" && pwd -P)"

# --- 1. Artifact prüfen --------------------------------------------------------------------

if [ -n "$(find "$incoming" -mindepth 1 ! -type f ! -type d -print -quit)" ]; then
  die "Artifact enthält Symlinks oder Sonderdateien"
fi
mapfile -d '' files < <(cd "$incoming" && find . -type f -printf '%P\0' | sort -z)
[ "${#files[@]}" -gt 0 ] || die "Artifact ist leer"

for f in "${files[@]}"; do
  [[ "$f" =~ $allowed_re ]] || die "Unerwartete Datei im Artifact: $(quote "$f")"
  size="$(stat -c %s "$incoming/$f")"
  [ "$size" -le "$max_file_bytes" ] || die "Datei zu groß: $(quote "$f")"
  case "$f" in
    *.json.gz) gzip -t "$incoming/$f" || die "Defektes gzip: $(quote "$f")" ;;
    *.json)
      python3 -I -c 'import json, sys; json.load(open(sys.argv[1], encoding="utf-8"))' \
        "$incoming/$f" || die "Defektes JSON: $(quote "$f")"
      ;;
  esac
done

if [ "$mode" = snapshot ]; then
  [ "${#files[@]}" -eq 1 ] || die "Genau ein Snapshot erwartet"
  commit_msg="Snapshot ${files[0]#snapshots/}"
else
  [ -f "$incoming/shopping-list.md" ] && [ -f "$incoming/shopping-list.json" ] \
    || die "Einkaufsliste fehlt"
  day="$(python3 -I -c 'import json, sys; print(json.load(open(sys.argv[1]))["generated_at"][:10])' \
    "$incoming/shopping-list.json")"
  [[ "$day" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]] || die "Ungültiges Datum in shopping-list.json"
  removals=()
  if [ -f "$incoming/remove.txt" ]; then
    mapfile -t removals < "$incoming/remove.txt"
    [ "${#removals[@]}" -le "$max_remove_lines" ] || die "remove.txt zu lang"
    for r in "${removals[@]}"; do
      [[ "$r" =~ $snapshot_re ]] || die "Ungültiger Eintrag in remove.txt: $(quote "$r")"
    done
  fi
  commit_msg="Einkaufsliste $day"
  if [ "${#removals[@]}" -gt 0 ]; then
    commit_msg="$commit_msg, ${#removals[@]} Snapshots zu Tageswerten verdichtet"
  fi
fi

# --- 2. Branch auschecken, anwenden, pushen ------------------------------------------------

work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

checkout_data() {
  rm -rf "$work/repo"
  git init -q "$work/repo"
  cd "$work/repo"
  git config user.name "github-actions[bot]"
  git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
  if [ -n "${DATA_REMOTE:-}" ]; then
    git remote add origin "$DATA_REMOTE"
  else
    : "${GITHUB_SERVER_URL:?}" "${GITHUB_REPOSITORY:?}" "${TOKEN:?}"
    # Token über einen Header statt in der Remote-URL, damit es nicht in .git/config-URLs landet.
    local auth
    auth="$(printf 'x-access-token:%s' "$TOKEN" | base64 -w0)"
    echo "::add-mask::$auth"
    git config http.extraheader "AUTHORIZATION: basic $auth"
    git remote add origin "$GITHUB_SERVER_URL/$GITHUB_REPOSITORY.git"
  fi
  if git ls-remote --exit-code --heads origin "$branch" >/dev/null; then
    git fetch -q --depth=1 origin "$branch"
    git checkout -q -B "$branch" FETCH_HEAD
  else
    echo "Branch $branch existiert noch nicht – wird als eigenständiger Branch angelegt."
    git checkout -q --orphan "$branch"
  fi
}

apply_changes() {
  local f r d
  for f in "${files[@]}"; do
    [ "$f" = remove.txt ] && continue
    mkdir -p "$(dirname "$f")"
    cp -- "$incoming/$f" "$f"
    git add -- "$f"
  done
  if [ "$mode" = analyze ]; then
    mkdir -p lists
    cp -- "$incoming/shopping-list.md" "lists/$day.md"
    git add -- "lists/$day.md"
    for r in "${removals[@]}"; do
      d="${r#snapshots/}"
      d="${d%%/*}"
      # Nur löschen, wenn die Tageswerte für diesen Tag vorliegen.
      if [ -f "daily/$d.json.gz" ]; then
        git rm -q --ignore-unmatch -- "$r"
      else
        echo "::warning::Tageswerte für $d fehlen – Snapshot bleibt erhalten"
      fi
    done
  fi
}

for attempt in 1 2 3; do
  checkout_data
  apply_changes
  if git diff --cached --quiet; then
    echo "Keine Änderungen."
    exit 0
  fi
  git commit -q -m "$commit_msg"
  if git push -q origin "HEAD:refs/heads/$branch"; then
    echo "Veröffentlicht: $commit_msg"
    exit 0
  fi
  echo "::warning::Push abgelehnt (Versuch $attempt) – setze auf dem neuesten Stand neu auf"
  cd "$work"
  sleep $((attempt * retry_sleep))
done
die "Push nach 3 Versuchen fehlgeschlagen"
