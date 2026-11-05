# Auswertung – 2026-11-05

Rückblick auf frühere Einkaufslisten anhand der stündlichen Snapshots. Grundlage für das Feintuning der Schwellwerte in `config.yaml` (Phase 5).

Ausgewertet: 1 Listen vom 02.11.2026 bis 02.11.2026.

## Gesamt

| | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| alle | 10 | 5 | 100 % | +112.6 % | 80 % | 0 % | – |

## Nach Ampel

| Ampel | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| grün | 3 | 3 | 100 % | +112.6 % | 100 % | 0 % | – |
| gelb | 6 | 2 | 100 % | +118.4 % | 50 % | 0 % | – |
| rot | 1 | 0 | – | – | – | – | – |

## Nach geplanter ROI

| geplanter ROI | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| ≥ 100 % | 10 | 5 | 100 % | +112.6 % | 80 % | 0 % | – |

## Nach Volatilität (CV)

| Volatilität (CV) | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|

## Nach Tagesvolumen

| Tagesvolumen | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|

**Lesehilfe:** *profitabel nach 48 h* = Kauf zum geplanten Gebot und Verkauf zum dann günstigsten Angebot − 1 wäre nach Gebühren im Plus gewesen. *Preis gehalten* = günstigstes Angebot höchstens 5 % unter dem geplanten Verkaufspreis. *Gebot überholt* = jemand bot binnen 24 h mehr. *Volumen* < 1 heißt: Die Schätzung war zu optimistisch.

## Filter-Trichter der heutigen Analyse

| Filter | Items | Anteil |
|---|---:|---:|
| kein Kaufgebot oder kein Verkaufsangebot | 3259 | 11.6 % |
| kein Spread nach Über-/Unterbieten | 325 | 1.2 % |
| Kaufpreis unter Minimum | 6129 | 21.9 % |
| ROI unter Minimum | 2365 | 8.4 % |
| ROI über Maximum (Ausreißer) | 6324 | 22.6 % |
| zu wenig Nachfrage im Orderbuch | 5908 | 21.1 % |
| zu wenig Angebot im Orderbuch | 1651 | 5.9 % |
| keine ausreichende Historie | 1423 | 5.1 % |
| Tagesvolumen unter Minimum | 409 | 1.5 % |
| Volatilität zu hoch | 54 | 0.2 % |
| Abwärtstrend | 14 | 0.1 % |
| besteht alle budgetunabhängigen Filter | 138 | 0.5 % |
