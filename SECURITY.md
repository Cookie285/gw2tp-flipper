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
- Der Job mit Schreibrecht führt keinen Projektcode aus. Er prüft das Artifact und committet es.
- `zizmor` prüft die Workflows in der CI.

**Daten**
- Marktdaten landen nur im Branch `data`, nie in `main`. Kein Force-Push.

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
- Das Dashboard (ab Phase 3) rendert API-Daten nur per `textContent` und nutzt eine strikte
  Content-Security-Policy ohne `unsafe-inline` und `unsafe-eval`.
