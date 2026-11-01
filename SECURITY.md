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
- Das Dashboard kann optional einen persönlichen GW2-API-Key verwenden (Phase 4). Vergib dem
  Key nur die Berechtigungen `account` und `tradingpost`. Hat er weitere Rechte, warnt das
  Dashboard.

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

## Persönlicher API-Key (Phase 4)

- Der Key bleibt **ausschließlich im Browser**: sessionStorage („nur für diese Sitzung“, Standard)
  oder localStorage („merken“). Ein Button löscht ihn aus beiden Speichern.
- Er wird nur im Header `Authorization: Bearer …` an `https://api.guildwars2.com` gesendet:
  - nie in einer URL (`access_token` kommt im Code nicht vor)
  - nie an andere Hosts: Pfad-Allowlist, `redirect: "error"`, CSP `connect-src`
  - ohne Cookies und ohne Referrer
- Öffentliche Endpunkte (Preise, Items) werden ohne Key abgefragt.
- Der Key wird nicht geloggt. Fehlermeldungen enthalten weder Key noch URL, und das Eingabefeld
  wird nach dem Lesen sofort geleert.
- Persönliche Daten (Orders, Historie) liegen nur im Arbeitsspeicher des Tabs.
- Tests prüfen das: `tests/js/account.test.mjs` (Header statt URL, keine Keys bei öffentlichen
  Abfragen, Fehlertexte) und `tests/test_web_security.py` (Authorization nur in `gw2api.js`,
  kein `access_token`, Speicherzugriff nur in `keystore.js`, kein `console.*`).
- **Einschränkung:** Der Browser-Speicher gilt pro Ursprung. Alle GitHub-Pages-Projekte unter
  `cookie285.github.io` teilen sich denselben Ursprung und damit auch sessionStorage und
  localStorage. Liegen dort weitere (fremde) Inhalte, besser „nur für diese Sitzung“ nutzen oder
  eine eigene Domain einrichten. Darauf weist auch das Dashboard hin.
