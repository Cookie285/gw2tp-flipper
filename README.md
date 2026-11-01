# gw2tp-flipper

Erzeugt täglich eine kurze, risikoarme **Einkaufsliste für Flips** am Handelsposten von
Guild Wars 2. Die Liste arbeitest du in etwa 10 Minuten **manuell im Spiel** ab.
Das Tool kauft und verkauft nichts: Die API ist read-only, und Bots verstoßen gegen die
Nutzungsbedingungen.

Alles läuft auf GitHub (Actions, später Pages). Details: [SPEC.md](SPEC.md),
Sicherheit: [SECURITY.md](SECURITY.md).

## Stand: Phase 1 (MVP)

- `analyze.yml` läuft täglich um 04:23 UTC (oder manuell über „Run workflow“). Der Job lädt alle
  aktuellen Preise, filtert und rankt sie und committet die Liste in den Branch **`data`**:
  - `shopping-list.md`: aktuelle Liste
  - `shopping-list.json`: dieselben Daten für das spätere Dashboard
  - `lists/YYYY-MM-DD.md`: Archiv
- Ohne Historie wird das Volumen in Phase 1 aus der **Orderbuch-Tiefe** geschätzt.
  Volatilität und Trend kommen in Phase 2.

### Rechenregeln (alles in Kupfer)

| Größe | Formel |
|---|---|
| Kaufpreis | höchstes Kaufgebot + 1c |
| Verkaufspreis | niedrigstes Angebot − 1c |
| Netto/Stück | Verkauf − 5 % Einstellgebühr − 10 % Steuer − Kauf (jede Gebühr ≥ 1c) |
| ROI | Netto ÷ Kaufpreis |
| Stückzahl | min(10 % Budget ÷ Kaufpreis, 5 % der Orderbuch-Tiefe, 250) |
| Score | erwarteter Gewinn × Liquiditätsfaktor × Stabilitätsfaktor (Phase 1: 1,0) |

Alle Schwellwerte stehen in [`config.yaml`](config.yaml).

## Lokal ausführen

```bash
python3.12 -m venv .venv
.venv/bin/pip install --require-hashes --only-binary=:all: --no-deps -r requirements-dev.txt
.venv/bin/python -m pytest
PYTHONPATH=src .venv/bin/python -m gw2tp analyze --config config.yaml --out out
```

## Abhängigkeiten aktualisieren

```bash
pip-compile --generate-hashes --allow-unsafe --strip-extras --no-emit-index-url requirements.in
pip-compile --generate-hashes --allow-unsafe --strip-extras --no-emit-index-url requirements-dev.in
```

Im Normalfall übernimmt Dependabot das.

## Hinweise

- Geplante Workflows können sich verzögern. GitHub pausiert sie, wenn das Repo 60 Tage lang
  keine Aktivität hat.
- Datenquelle ist ausschließlich die offizielle API, kein Scraping.
