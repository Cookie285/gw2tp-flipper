# Auswertung – 2026-11-23

Rückblick auf frühere Einkaufslisten anhand der stündlichen Snapshots. Grundlage für das Feintuning der Schwellwerte in `config.yaml` (Phase 5).

Ausgewertet: 13 Listen vom 09.11.2026 bis 21.11.2026.

## Gesamt

| | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| alle | 120 | 117 | 96 % | +16.2 % | 79 % | 89 % | 0.72 |
| Historien-Modus | 120 | 117 | 96 % | +16.2 % | 79 % | 89 % | 0.72 |

## Nach Ampel

| Ampel | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| grün | 14 | 14 | 93 % | +19.1 % | 79 % | 86 % | 0.89 |
| gelb | 88 | 87 | 96 % | +16.0 % | 78 % | 92 % | 0.71 |
| rot | 18 | 16 | 100 % | +21.9 % | 87 % | 75 % | 0.72 |

## Nach geplanter ROI

| geplanter ROI | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| 10 % – 20 % | 74 | 71 | 95 % | +12.6 % | 77 % | 92 % | 0.80 |
| 20 % – 35 % | 29 | 29 | 96 % | +22.0 % | 79 % | 97 % | 0.65 |
| 35 % – 60 % | 10 | 10 | 100 % | +36.8 % | 80 % | 40 % | 0.60 |
| 60 % – 100 % | 7 | 7 | 100 % | +72.2 % | 100 % | 100 % | 0.36 |

## Nach Volatilität (CV)

| Volatilität (CV) | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0 % – 2 % | 13 | 11 | 100 % | +23.6 % | 100 % | 91 % | 0.42 |
| 2 % – 4 % | 32 | 32 | 93 % | +13.0 % | 80 % | 72 % | 0.81 |
| 4 % – 7 % | 75 | 74 | 97 % | +16.7 % | 76 % | 96 % | 0.73 |

## Nach Tagesvolumen

| Tagesvolumen | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0 – 200 | 72 | 70 | 97 % | +16.2 % | 84 % | 84 % | 0.62 |
| 200 – 1.000 | 38 | 37 | 97 % | +17.5 % | 81 % | 95 % | 0.74 |
| 1.000 – 5.000 | 9 | 9 | 86 % | +7.7 % | 43 % | 100 % | 0.95 |
| 5.000 – 20.000 | 1 | 1 | 100 % | +8.0 % | 0 % | 100 % | 0.80 |

**Lesehilfe:** *profitabel nach 48 h* = Kauf zum geplanten Gebot und Verkauf zum dann günstigsten Angebot − 1 wäre nach Gebühren im Plus gewesen. *Preis gehalten* = günstigstes Angebot höchstens 5 % unter dem geplanten Verkaufspreis. *Gebot überholt* = jemand bot binnen 24 h mehr. *Volumen* < 1 heißt: Die Schätzung war zu optimistisch.

## Filter-Trichter der heutigen Analyse

| Filter | Items | Anteil |
|---|---:|---:|
| kein Kaufgebot oder kein Verkaufsangebot | 3351 | 12.0 % |
| kein Spread nach Über-/Unterbieten | 308 | 1.1 % |
| Kaufpreis unter Minimum | 6082 | 21.7 % |
| ROI unter Minimum | 2465 | 8.8 % |
| ROI über Maximum (Ausreißer) | 6206 | 22.2 % |
| zu wenig Nachfrage im Orderbuch | 5882 | 21.0 % |
| zu wenig Angebot im Orderbuch | 1681 | 6.0 % |
| keine ausreichende Historie | 1387 | 5.0 % |
| Tagesvolumen unter Minimum | 397 | 1.4 % |
| Volatilität zu hoch | 150 | 0.5 % |
| Abwärtstrend | 1 | 0.0 % |
| besteht alle budgetunabhängigen Filter | 99 | 0.4 % |
