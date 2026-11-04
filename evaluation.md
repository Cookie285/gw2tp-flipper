# Auswertung – 2026-11-04

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
| kein Kaufgebot oder kein Verkaufsangebot | 3251 | 11.6 % |
| kein Spread nach Über-/Unterbieten | 339 | 1.2 % |
| Kaufpreis unter Minimum | 6120 | 21.9 % |
| ROI unter Minimum | 2411 | 8.6 % |
| ROI über Maximum (Ausreißer) | 6348 | 22.7 % |
| zu wenig Nachfrage im Orderbuch | 5889 | 21.0 % |
| zu wenig Angebot im Orderbuch | 1640 | 5.9 % |
| keine ausreichende Historie | 1405 | 5.0 % |
| Tagesvolumen unter Minimum | 430 | 1.5 % |
| Volatilität zu hoch | 37 | 0.1 % |
| Abwärtstrend | 17 | 0.1 % |
| besteht alle budgetunabhängigen Filter | 112 | 0.4 % |
