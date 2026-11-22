# Auswertung – 2026-11-22

Rückblick auf frühere Einkaufslisten anhand der stündlichen Snapshots. Grundlage für das Feintuning der Schwellwerte in `config.yaml` (Phase 5).

Ausgewertet: 13 Listen vom 08.11.2026 bis 20.11.2026.

## Gesamt

| | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| alle | 122 | 118 | 95 % | +16.1 % | 77 % | 90 % | 0.72 |
| Historien-Modus | 122 | 118 | 95 % | +16.1 % | 77 % | 90 % | 0.72 |

## Nach Ampel

| Ampel | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| grün | 12 | 12 | 92 % | +23.2 % | 75 % | 83 % | 0.66 |
| gelb | 92 | 91 | 94 % | +15.5 % | 74 % | 93 % | 0.72 |
| rot | 18 | 15 | 100 % | +25.4 % | 93 % | 73 % | 0.78 |

## Nach geplanter ROI

| geplanter ROI | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| 10 % – 20 % | 74 | 70 | 94 % | +12.4 % | 75 % | 91 % | 0.79 |
| 20 % – 35 % | 30 | 30 | 93 % | +21.9 % | 76 % | 100 % | 0.63 |
| 35 % – 60 % | 11 | 11 | 100 % | +35.5 % | 73 % | 45 % | 0.84 |
| 60 % – 100 % | 7 | 7 | 100 % | +72.2 % | 100 % | 100 % | 0.36 |

## Nach Volatilität (CV)

| Volatilität (CV) | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0 % – 2 % | 13 | 10 | 100 % | +24.2 % | 100 % | 90 % | 0.42 |
| 2 % – 4 % | 31 | 31 | 93 % | +12.9 % | 79 % | 74 % | 0.79 |
| 4 % – 7 % | 78 | 77 | 95 % | +16.2 % | 73 % | 96 % | 0.74 |

## Nach Tagesvolumen

| Tagesvolumen | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0 – 200 | 72 | 69 | 94 % | +15.6 % | 82 % | 86 % | 0.60 |
| 200 – 1.000 | 40 | 39 | 97 % | +17.5 % | 76 % | 95 % | 0.74 |
| 1.000 – 5.000 | 9 | 9 | 86 % | +7.7 % | 43 % | 100 % | 0.95 |
| 5.000 – 20.000 | 1 | 1 | 100 % | +8.0 % | 0 % | 100 % | 0.80 |

**Lesehilfe:** *profitabel nach 48 h* = Kauf zum geplanten Gebot und Verkauf zum dann günstigsten Angebot − 1 wäre nach Gebühren im Plus gewesen. *Preis gehalten* = günstigstes Angebot höchstens 5 % unter dem geplanten Verkaufspreis. *Gebot überholt* = jemand bot binnen 24 h mehr. *Volumen* < 1 heißt: Die Schätzung war zu optimistisch.

## Filter-Trichter der heutigen Analyse

| Filter | Items | Anteil |
|---|---:|---:|
| kein Kaufgebot oder kein Verkaufsangebot | 3369 | 12.0 % |
| kein Spread nach Über-/Unterbieten | 323 | 1.2 % |
| Kaufpreis unter Minimum | 6080 | 21.7 % |
| ROI unter Minimum | 2410 | 8.6 % |
| ROI über Maximum (Ausreißer) | 6208 | 22.2 % |
| zu wenig Nachfrage im Orderbuch | 5873 | 21.0 % |
| zu wenig Angebot im Orderbuch | 1675 | 6.0 % |
| keine ausreichende Historie | 1407 | 5.0 % |
| Tagesvolumen unter Minimum | 398 | 1.4 % |
| Volatilität zu hoch | 157 | 0.6 % |
| Abwärtstrend | 2 | 0.0 % |
| besteht alle budgetunabhängigen Filter | 107 | 0.4 % |
