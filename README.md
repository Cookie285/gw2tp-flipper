# gw2tp-flipper

Erzeugt täglich eine kurze, risikoarme **Einkaufsliste für Flips** am Handelsposten von
Guild Wars 2. Die Liste arbeitest du in etwa 10 Minuten **manuell im Spiel** ab.
Das Tool kauft und verkauft nichts: Die API ist read-only, und Bots verstoßen gegen die
Nutzungsbedingungen.

Alles läuft auf GitHub (Actions, später Pages). Details: [SPEC.md](SPEC.md),
Sicherheit: [SECURITY.md](SECURITY.md).

## Dashboard (Phase 3)

**https://cookie285.github.io/gw2tp-flipper/**

- Zeigt die Einkaufsliste mit Icon, Name, Kaufgebot, Stückzahl, Verkaufspreis, erwartetem Gewinn,
  Volumen, Trend und Risiko-Ampel. „Kopieren“ legt den Chatcode in die Zwischenablage.
- **Budget eingeben:** Das Dashboard rechnet Stückzahl, Filter, Score und Ampel im Browser für
  dein Budget neu. Grundlage ist ein Pool von bis zu 200 vorgeprüften Kandidaten aus
  `shopping-list.json`. Python (`analyze.plan`) und JavaScript (`web/plan.js`) rechnen
  nachweislich gleich, ein Paritätstest in der CI prüft das. Das Budget wird nur lokal im
  Browser gespeichert.
- Statische Seite ohne Build-Schritt, ohne Bibliotheken, ohne CDN. Veröffentlicht durch
  `pages.yml` nach jeder Analyse und bei Änderungen an `web/`.

### Persönliche Ansichten (Phase 4)

Die Tabs **„Meine Orders“** und **„Gewinn“** brauchen einen eigenen GW2-API-Key. Erstelle ihn unter
[account.arena.net/applications](https://account.arena.net/applications) **nur mit den
Berechtigungen „account“ und „tradingpost“**.

- **Meine Orders:**
  - offene Kaufgebote mit Warnung, wenn jemand mehr bietet
  - offene Verkaufsangebote mit Warnung, wenn jemand billiger verkauft
  - fällige Verkäufe aus der Abholbox mit Preisvorschlag (niedrigstes Angebot − 1c) und
    erwartetem Gewinn gegenüber deinem Einkaufspreis
- **Gewinn:** realisierter Gewinn der letzten 7/30/90 Tage, pro Woche und pro Tag.
  Verkäufe werden per FIFO deinen Einkäufen zugeordnet, nach 5 % Einstellgebühr und 10 % Steuer.
  Die GW2-API liefert die Historie der letzten 90 Tage.
- **Datenschutz:**
  - Der Key bleibt im Browser: „nur für diese Sitzung“ (sessionStorage, Standard) oder
    „auf diesem Gerät merken“ (localStorage). „Key löschen“ entfernt ihn aus beiden.
  - Er wird nur im Header `Authorization: Bearer …` an `api.guildwars2.com` gesendet,
    nie in einer URL, nie an andere Hosts. Abfragen nach Preisen und Items laufen ohne Key.
  - Persönliche Daten werden nur im Arbeitsspeicher des Tabs gehalten und nie gespeichert.

## Stand: Phase 2 (Historie)

| Workflow | Zeitplan | Ergebnis im Branch **`data`** |
|---|---|---|
| `snapshot.yml` | stündlich, Minute 17 | `snapshots/YYYY-MM-DD/HHMM.json.gz`: Preise und Mengen des Universums |
| `analyze.yml` | täglich 04:23 UTC | `shopping-list.md`/`.json`, `lists/YYYY-MM-DD.md`, `universe.json`, `daily/` |

Beide lassen sich auch manuell starten (Actions → Workflow → „Run workflow“).

- **Universum:** Die ca. 800 Items mit der größten Orderbuch-Tiefe plus eine Whitelist
  (Ekto, Mystische Münzen, T6-Materialien) aus `config.yaml`. `analyze` aktualisiert es täglich.
- **Volumen:** Rückgänge der Angebots- und Nachfragemenge zwischen aufeinanderfolgenden Snapshots,
  hochgerechnet auf einen Tag. Es zählt die kleinere Seite, denn ein Flip braucht beide.
  Neue Orders verdecken Umsätze, Stornierungen täuschen welche vor. Es bleibt also eine Schätzung.
- **Volatilität:** Variationskoeffizient von Kauf- und Verkaufspreis über 7 Tage (der größere zählt).
- **Trend:** Steigung der Tagesmediane des Mittelpreises, relativ pro Tag (ab 3 Tagen Daten).
- **Rückfall:** Solange kein Item 24 Stunden Historie hat, rechnet `analyze` wie in Phase 1 mit
  der Orderbuch-Tiefe. Die Liste weist darauf hin.
- **Verdichtung:** Stunden-Snapshots älter als 14 Tage werden zu Tageswerten (`daily/`)
  zusammengefasst und per normalem Commit entfernt.
- **Datengröße:** etwa 10 KB pro Snapshot, also rund 250 KB pro Tag in der Git-Historie
  (ca. 90 MB pro Jahr). Der Arbeitsstand bleibt durch die Verdichtung klein.

### Rechenregeln (alles in Kupfer)

| Größe | Formel |
|---|---|
| Kaufpreis | höchstes Kaufgebot + 1c |
| Verkaufspreis | niedrigstes Angebot − 1c |
| Netto/Stück | Verkauf − 5 % Einstellgebühr − 10 % Steuer − Kauf (jede Gebühr ≥ 1c) |
| ROI | Netto ÷ Kaufpreis |
| Stückzahl | min(10 % Budget ÷ Kaufpreis, 5 % des Tagesvolumens, 250) |
| Score | erwarteter Gewinn × Liquiditätsfaktor × Stabilitätsfaktor |
| Stabilitätsfaktor | (1 − ½·CV/CV_max) × (1 − ½·Abwärtstrend/Trend_max), 0,9 bei unbekanntem Trend |

Filter: ROI ≥ 10 %, Netto ≥ 10 s/Stück oder ≥ 1 g/Position, Kaufpreis ≥ 1 s,
Tagesvolumen ≥ 10 × Stückzahl, CV ≤ 10 %, Trend ≥ −2 %/Tag. Alle Schwellwerte stehen in
[`config.yaml`](config.yaml).

## Lokal ausführen

```bash
python3.12 -m venv .venv
.venv/bin/pip install --require-hashes --only-binary=:all: --no-deps -r requirements-dev.txt
.venv/bin/python -m pytest
node --test tests/js/*.test.mjs
python3 -m http.server -d web 8000   # Dashboard lokal (shopping-list.json nach web/ kopieren)
PYTHONPATH=src .venv/bin/python -m gw2tp snapshot --out out
PYTHONPATH=src .venv/bin/python -m gw2tp analyze --data-dir <checkout-von-data> --out out
```

## Abhängigkeiten aktualisieren

```bash
pip-compile --generate-hashes --allow-unsafe --strip-extras --no-emit-index-url requirements.in
pip-compile --generate-hashes --allow-unsafe --strip-extras --no-emit-index-url requirements-dev.in
```

Im Normalfall übernimmt Dependabot das.

## Hinweise

- Actions-Minuten: In öffentlichen Repos sind die stündlichen Läufe kostenlos. In privaten Repos
  verbrauchen sie ca. 1.500 Minuten pro Monat.
- Geplante Workflows können sich verzögern. GitHub pausiert sie, wenn das Repo 60 Tage lang
  keine Aktivität hat.
- Datenquelle ist ausschließlich die offizielle API, kein Scraping.
