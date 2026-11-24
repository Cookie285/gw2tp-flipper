# Auswertung – 2026-11-24

Rückblick auf frühere Einkaufslisten anhand der stündlichen Snapshots. Grundlage für das Feintuning der Schwellwerte in `config.yaml` (Phase 5).

Ausgewertet: 12 Listen vom 10.11.2026 bis 21.11.2026.

## Gesamt

| | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| alle | 110 | 108 | 96 % | +16.4 % | 78 % | 88 % | 0.71 |
| Historien-Modus | 110 | 108 | 96 % | +16.4 % | 78 % | 88 % | 0.71 |

## Nach Ampel

| Ampel | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| grün | 14 | 14 | 93 % | +19.1 % | 79 % | 86 % | 0.89 |
| gelb | 80 | 79 | 96 % | +15.6 % | 77 % | 91 % | 0.71 |
| rot | 16 | 15 | 100 % | +25.4 % | 86 % | 73 % | 0.65 |

## Nach geplanter ROI

| geplanter ROI | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| 10 % – 20 % | 68 | 66 | 95 % | +12.4 % | 75 % | 91 % | 0.76 |
| 20 % – 35 % | 25 | 25 | 96 % | +22.0 % | 79 % | 96 % | 0.65 |
| 35 % – 60 % | 10 | 10 | 100 % | +36.8 % | 80 % | 40 % | 0.60 |
| 60 % – 100 % | 7 | 7 | 100 % | +72.2 % | 100 % | 100 % | 0.36 |

## Nach Volatilität (CV)

| Volatilität (CV) | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0 % – 2 % | 11 | 10 | 100 % | +19.4 % | 100 % | 90 % | 0.47 |
| 2 % – 4 % | 31 | 31 | 93 % | +13.0 % | 79 % | 71 % | 0.79 |
| 4 % – 7 % | 68 | 67 | 97 % | +16.7 % | 75 % | 96 % | 0.71 |

## Nach Tagesvolumen

| Tagesvolumen | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0 – 200 | 68 | 67 | 97 % | +16.4 % | 83 % | 84 % | 0.60 |
| 200 – 1.000 | 33 | 32 | 97 % | +17.2 % | 81 % | 94 % | 0.73 |
| 1.000 – 5.000 | 8 | 8 | 83 % | +6.8 % | 33 % | 100 % | 0.92 |
| 5.000 – 20.000 | 1 | 1 | 100 % | +8.0 % | 0 % | 100 % | 0.80 |

**Lesehilfe:** *profitabel nach 48 h* = Kauf zum geplanten Gebot und Verkauf zum dann günstigsten Angebot − 1 wäre nach Gebühren im Plus gewesen. *Preis gehalten* = günstigstes Angebot höchstens 5 % unter dem geplanten Verkaufspreis. *Gebot überholt* = jemand bot binnen 24 h mehr. *Volumen* < 1 heißt: Die Schätzung war zu optimistisch.

## Filter-Trichter der heutigen Analyse

| Filter | Items | Anteil |
|---|---:|---:|
| kein Kaufgebot oder kein Verkaufsangebot | 2753 | 12.4 % |
| kein Spread nach Über-/Unterbieten | 218 | 1.0 % |
| Kaufpreis unter Minimum | 4724 | 21.3 % |
| ROI unter Minimum | 1978 | 8.9 % |
| ROI über Maximum (Ausreißer) | 4899 | 22.1 % |
| zu wenig Nachfrage im Orderbuch | 4592 | 20.7 % |
| zu wenig Angebot im Orderbuch | 1323 | 6.0 % |
| keine ausreichende Historie | 1180 | 5.3 % |
| Tagesvolumen unter Minimum | 341 | 1.5 % |
| Volatilität zu hoch | 116 | 0.5 % |
| besteht alle budgetunabhängigen Filter | 76 | 0.3 % |
