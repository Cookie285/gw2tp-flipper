# Sicherheitsrichtlinie

## Schwachstellen melden

Bitte **keine öffentlichen Issues** für Sicherheitsprobleme anlegen. Melde sie stattdessen über
**GitHub → Security → „Report a vulnerability“** (Private Vulnerability Reporting). Du bekommst
eine Rückmeldung, sobald das Problem gesichtet wurde.

Unterstützt wird jeweils nur der aktuelle Stand von `main`.

## Was dieses Projekt tut und was nicht

- Es liest ausschließlich **öffentliche Marktdaten** der offiziellen API `https://api.guildwars2.com`.
  Es kauft und verkauft nichts und automatisiert keine Spielaktionen.
- Für die Marktdaten wird **kein API-Key** benötigt. Im Repository gibt es **keine GitHub Secrets**.
- Ab Phase 4 kann das Dashboard optional einen persönlichen GW2-API-Key verwenden. Dieser Key
  bleibt **ausschließlich im Browser** (sessionStorage oder auf Wunsch localStorage). Er wird nur an
  `api.guildwars2.com` gesendet, nie in URLs, Logs oder an andere Hosts. Vergib dem Key nur die
  Berechtigungen `account` und `tradingpost`.

## Maßnahmen

**GitHub Actions**
- Jeder Workflow startet mit `permissions: {}`. Schreibrechte bekommt nur der Job, der sie braucht.
- Alle Actions sind auf vollständige Commit-SHAs gepinnt. Dependabot aktualisiert sie.
- Kein `pull_request_target`. Fork-PRs laufen ohne Schreibrechte und ohne Secrets.
- Keine Interpolation von Eingaben in `run:`-Skripte, nur Übergabe über Umgebungsvariablen.
- Jeder Job hat `timeout-minutes`. Schreibende Läufe teilen sich eine `concurrency`-Gruppe.
- Daten erzeugen und Daten schreiben sind getrennte Jobs. Der Job mit Schreibrecht führt keinen
  Python-Code und keine Abhängigkeiten aus, nur `.github/scripts/publish-data.sh` aus `main`.
  Das Skript lässt nur erwartete Dateinamen zu (Allowlist), verbietet Symlinks, begrenzt die
  Größe, prüft gzip und JSON und löscht Snapshots nur, wenn deren Tageswerte vorliegen.
- `shellcheck` und Tests prüfen das Publish-Skript in der CI.
- `zizmor` prüft die Workflows in der CI.

**Daten**
- Marktdaten landen nur im Branch `data`, nie in `main`. Kein Force-Push. Alte Snapshots werden
  über normale Commits verdichtet.
- Gelesene Snapshots werden validiert (Schema, Typen, Größenlimit gegen gzip-Bomben, keine Symlinks).

**Abhängigkeiten**
- Feste Versionen mit Hashes (`pip-compile --generate-hashes`), Installation mit
  `--require-hashes --only-binary=:all:`.
- Dependabot (pip, github-actions) mit 7 Tagen Cooldown.

**API-Client**
- Host-Allowlist (auch für Redirects), Timeouts, Größenlimit für Antworten.
- Backoff bei 429/5xx, Rate-Limit ≤ 240 Requests/Minute, max. 200 IDs pro Request.
- Alle Antworten werden validiert, ungültige Datensätze verworfen.

**Ausgabe**
- Item-Namen werden von Steuerzeichen bereinigt und für Markdown escaped.

**Dashboard (GitHub Pages)**
- Statisch, keine externen Skripte, Stylesheets oder Schriften, kein CDN, kein Build-Schritt.
- Content-Security-Policy als `<meta>`-Tag: `default-src 'self'`, `script-src 'self'`,
  `style-src 'self'`, `img-src 'self' https://render.guildwars2.com`,
  `connect-src 'self' https://api.guildwars2.com`, `object-src 'none'`, `base-uri 'none'`,
  `form-action 'none'` sowie `require-trusted-types-for 'script'`. Kein `unsafe-inline`,
  kein `unsafe-eval`, keine Inline-Skripte oder -Styles.
- API-Daten werden nur per `textContent` bzw. als Attribut bereits validierter URLs gesetzt,
  nie per `innerHTML`. Trusted Types erzwingen das zusätzlich im Browser.
- `shopping-list.json` wird im Browser erneut validiert (Typen, Wertebereiche, Icon-Host,
  Chatcode-Format). Ungültige Einträge werden verworfen.
- Ein Test (`tests/test_web_security.py`) prüft die CSP und verbietet gefährliche DOM-Senken,
  fremde Hosts sowie Inline-Code.
- Pages-Deploy: Der Build-Job liest nur (`contents: read`). Nur der Deploy-Job erhält
  `pages: write` und `id-token: write`.
