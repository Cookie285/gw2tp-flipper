# Auswertung – 2026-11-07

Rückblick auf frühere Einkaufslisten anhand der stündlichen Snapshots. Grundlage für das Feintuning der Schwellwerte in `config.yaml` (Phase 5).

Ausgewertet: 2 Listen vom 02.11.2026 bis 04.11.2026.

## Gesamt

| | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| alle | 20 | 15 | 93 % | +24.7 % | 79 % | 67 % | 0.59 |

## Nach Ampel

| Ampel | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| grün | 3 | 3 | 100 % | +112.6 % | 100 % | 0 % | – |
| gelb | 10 | 6 | 100 % | +38.1 % | 80 % | 67 % | 0.43 |
| rot | 7 | 6 | 83 % | +10.8 % | 67 % | 100 % | 0.92 |

## Nach geplanter ROI

| geplanter ROI | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| 10 % – 20 % | 6 | 6 | 100 % | +12.0 % | 100 % | 100 % | 0.92 |
| 20 % – 35 % | 3 | 3 | 67 % | +12.6 % | 33 % | 100 % | 0.43 |
| 35 % – 60 % | 1 | 1 | 100 % | +38.1 % | 100 % | 100 % | 0.45 |
| ≥ 100 % | 10 | 5 | 100 % | +112.6 % | 80 % | 0 % | – |

## Nach Volatilität (CV)

| Volatilität (CV) | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2 % – 4 % | 5 | 5 | 100 % | +16.7 % | 100 % | 100 % | 0.73 |
| 4 % – 7 % | 3 | 3 | 100 % | +12.0 % | 100 % | 100 % | 1.11 |
| 7 % – 10 % | 2 | 2 | 50 % | +3.7 % | 0 % | 100 % | 0.35 |

## Nach Tagesvolumen

| Tagesvolumen | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0 – 200 | 4 | 4 | 100 % | +16.7 % | 100 % | 100 % | 0.94 |
| 200 – 1.000 | 4 | 4 | 67 % | +12.6 % | 33 % | 100 % | 0.42 |
| 1.000 – 5.000 | 1 | 1 | 100 % | +9.7 % | 100 % | 100 % | 1.43 |
| 5.000 – 20.000 | 1 | 1 | 100 % | +5.3 % | 100 % | 100 % | 0.73 |

**Lesehilfe:** *profitabel nach 48 h* = Kauf zum geplanten Gebot und Verkauf zum dann günstigsten Angebot − 1 wäre nach Gebühren im Plus gewesen. *Preis gehalten* = günstigstes Angebot höchstens 5 % unter dem geplanten Verkaufspreis. *Gebot überholt* = jemand bot binnen 24 h mehr. *Volumen* < 1 heißt: Die Schätzung war zu optimistisch.

## Filter-Trichter der heutigen Analyse

| Filter | Items | Anteil |
|---|---:|---:|
| kein Kaufgebot oder kein Verkaufsangebot | 3323 | 11.9 % |
| kein Spread nach Über-/Unterbieten | 307 | 1.1 % |
| Kaufpreis unter Minimum | 6067 | 21.7 % |
| ROI unter Minimum | 2379 | 8.5 % |
| ROI über Maximum (Ausreißer) | 6281 | 22.4 % |
| zu wenig Nachfrage im Orderbuch | 5905 | 21.1 % |
| zu wenig Angebot im Orderbuch | 1664 | 5.9 % |
| keine ausreichende Historie | 1438 | 5.1 % |
| Tagesvolumen unter Minimum | 396 | 1.4 % |
| Volatilität zu hoch | 63 | 0.2 % |
| Abwärtstrend | 9 | 0.0 % |
| besteht alle budgetunabhängigen Filter | 167 | 0.6 % |
