# Auswertung – 2026-11-19

Rückblick auf frühere Einkaufslisten anhand der stündlichen Snapshots. Grundlage für das Feintuning der Schwellwerte in `config.yaml` (Phase 5).

Ausgewertet: 12 Listen vom 05.11.2026 bis 16.11.2026.

## Gesamt

| | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| alle | 118 | 115 | 93 % | +16.1 % | 73 % | 95 % | 0.79 |
| Historien-Modus | 118 | 115 | 93 % | +16.1 % | 73 % | 95 % | 0.79 |

## Nach Ampel

| Ampel | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| grün | 6 | 6 | 83 % | +33.0 % | 83 % | 100 % | 0.90 |
| gelb | 89 | 89 | 94 % | +16.1 % | 74 % | 96 % | 0.75 |
| rot | 23 | 20 | 88 % | +11.9 % | 65 % | 90 % | 0.89 |

## Nach geplanter ROI

| geplanter ROI | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| 10 % – 20 % | 72 | 69 | 91 % | +12.3 % | 72 % | 97 % | 0.83 |
| 20 % – 35 % | 36 | 36 | 94 % | +23.2 % | 76 % | 100 % | 0.65 |
| 35 % – 60 % | 7 | 7 | 100 % | +34.8 % | 57 % | 43 % | 0.81 |
| 60 % – 100 % | 3 | 3 | 100 % | +80.8 % | 100 % | 100 % | 0.60 |

## Nach Volatilität (CV)

| Volatilität (CV) | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0 % – 2 % | 10 | 7 | 100 % | +25.0 % | 100 % | 100 % | 0.52 |
| 2 % – 4 % | 29 | 29 | 93 % | +12.8 % | 79 % | 86 % | 0.73 |
| 4 % – 7 % | 69 | 69 | 94 % | +16.2 % | 73 % | 99 % | 0.81 |
| 7 % – 10 % | 10 | 10 | 75 % | +8.1 % | 38 % | 90 % | 0.94 |

## Nach Tagesvolumen

| Tagesvolumen | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0 – 200 | 53 | 50 | 92 % | +13.0 % | 82 % | 90 % | 0.72 |
| 200 – 1.000 | 54 | 54 | 96 % | +17.3 % | 71 % | 98 % | 0.79 |
| 1.000 – 5.000 | 11 | 11 | 78 % | +6.0 % | 44 % | 100 % | 0.96 |

**Lesehilfe:** *profitabel nach 48 h* = Kauf zum geplanten Gebot und Verkauf zum dann günstigsten Angebot − 1 wäre nach Gebühren im Plus gewesen. *Preis gehalten* = günstigstes Angebot höchstens 5 % unter dem geplanten Verkaufspreis. *Gebot überholt* = jemand bot binnen 24 h mehr. *Volumen* < 1 heißt: Die Schätzung war zu optimistisch.

## Filter-Trichter der heutigen Analyse

| Filter | Items | Anteil |
|---|---:|---:|
| kein Kaufgebot oder kein Verkaufsangebot | 3330 | 11.9 % |
| kein Spread nach Über-/Unterbieten | 332 | 1.2 % |
| Kaufpreis unter Minimum | 6084 | 21.7 % |
| ROI unter Minimum | 2522 | 9.0 % |
| ROI über Maximum (Ausreißer) | 6214 | 22.2 % |
| zu wenig Nachfrage im Orderbuch | 5858 | 20.9 % |
| zu wenig Angebot im Orderbuch | 1658 | 5.9 % |
| keine ausreichende Historie | 1379 | 4.9 % |
| Tagesvolumen unter Minimum | 397 | 1.4 % |
| Volatilität zu hoch | 126 | 0.4 % |
| Abwärtstrend | 1 | 0.0 % |
| besteht alle budgetunabhängigen Filter | 108 | 0.4 % |
