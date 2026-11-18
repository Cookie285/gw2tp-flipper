# Auswertung – 2026-11-18

Rückblick auf frühere Einkaufslisten anhand der stündlichen Snapshots. Grundlage für das Feintuning der Schwellwerte in `config.yaml` (Phase 5).

Ausgewertet: 12 Listen vom 04.11.2026 bis 15.11.2026.

## Gesamt

| | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| alle | 119 | 116 | 93 % | +16.0 % | 74 % | 96 % | 0.76 |
| Historien-Modus | 119 | 116 | 93 % | +16.0 % | 74 % | 96 % | 0.76 |

## Nach Ampel

| Ampel | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| grün | 5 | 5 | 100 % | +39.0 % | 100 % | 100 % | 1.07 |
| gelb | 86 | 86 | 94 % | +16.4 % | 75 % | 95 % | 0.73 |
| rot | 28 | 25 | 86 % | +10.9 % | 64 % | 96 % | 0.92 |

## Nach geplanter ROI

| geplanter ROI | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| 10 % – 20 % | 73 | 70 | 92 % | +12.4 % | 76 % | 97 % | 0.83 |
| 20 % – 35 % | 37 | 37 | 92 % | +23.2 % | 72 % | 100 % | 0.61 |
| 35 % – 60 % | 7 | 7 | 100 % | +34.8 % | 57 % | 57 % | 0.81 |
| 60 % – 100 % | 2 | 2 | 100 % | +80.9 % | 100 % | 100 % | 0.83 |

## Nach Volatilität (CV)

| Volatilität (CV) | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0 % – 2 % | 10 | 7 | 100 % | +25.0 % | 100 % | 100 % | 0.52 |
| 2 % – 4 % | 30 | 30 | 96 % | +12.9 % | 82 % | 90 % | 0.75 |
| 4 % – 7 % | 67 | 67 | 94 % | +16.2 % | 74 % | 99 % | 0.81 |
| 7 % – 10 % | 12 | 12 | 70 % | +8.1 % | 30 % | 92 % | 0.68 |

## Nach Tagesvolumen

| Tagesvolumen | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0 – 200 | 51 | 48 | 94 % | +13.9 % | 83 % | 92 % | 0.74 |
| 200 – 1.000 | 58 | 58 | 94 % | +17.2 % | 69 % | 98 % | 0.73 |
| 1.000 – 5.000 | 9 | 9 | 78 % | +7.7 % | 56 % | 100 % | 1.00 |
| 5.000 – 20.000 | 1 | 1 | 100 % | +5.3 % | 100 % | 100 % | 0.73 |

**Lesehilfe:** *profitabel nach 48 h* = Kauf zum geplanten Gebot und Verkauf zum dann günstigsten Angebot − 1 wäre nach Gebühren im Plus gewesen. *Preis gehalten* = günstigstes Angebot höchstens 5 % unter dem geplanten Verkaufspreis. *Gebot überholt* = jemand bot binnen 24 h mehr. *Volumen* < 1 heißt: Die Schätzung war zu optimistisch.

## Filter-Trichter der heutigen Analyse

| Filter | Items | Anteil |
|---|---:|---:|
| kein Kaufgebot oder kein Verkaufsangebot | 3332 | 11.9 % |
| kein Spread nach Über-/Unterbieten | 331 | 1.2 % |
| Kaufpreis unter Minimum | 6077 | 21.7 % |
| ROI unter Minimum | 2483 | 8.9 % |
| ROI über Maximum (Ausreißer) | 6200 | 22.1 % |
| zu wenig Nachfrage im Orderbuch | 5873 | 21.0 % |
| zu wenig Angebot im Orderbuch | 1675 | 6.0 % |
| keine ausreichende Historie | 1393 | 5.0 % |
| Tagesvolumen unter Minimum | 406 | 1.4 % |
| Volatilität zu hoch | 128 | 0.5 % |
| besteht alle budgetunabhängigen Filter | 111 | 0.4 % |
