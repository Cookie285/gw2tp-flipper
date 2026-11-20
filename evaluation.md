# Auswertung – 2026-11-20

Rückblick auf frühere Einkaufslisten anhand der stündlichen Snapshots. Grundlage für das Feintuning der Schwellwerte in `config.yaml` (Phase 5).

Ausgewertet: 12 Listen vom 06.11.2026 bis 17.11.2026.

## Gesamt

| | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| alle | 116 | 113 | 93 % | +16.2 % | 76 % | 91 % | 0.75 |
| Historien-Modus | 116 | 113 | 93 % | +16.2 % | 76 % | 91 % | 0.75 |

## Nach Ampel

| Ampel | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| grün | 9 | 9 | 89 % | +19.4 % | 78 % | 78 % | 0.73 |
| gelb | 86 | 86 | 94 % | +16.2 % | 76 % | 94 % | 0.73 |
| rot | 21 | 18 | 93 % | +13.6 % | 80 % | 83 % | 0.91 |

## Nach geplanter ROI

| geplanter ROI | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| 10 % – 20 % | 71 | 68 | 92 % | +12.4 % | 75 % | 93 % | 0.79 |
| 20 % – 35 % | 34 | 34 | 94 % | +23.2 % | 81 % | 100 % | 0.73 |
| 35 % – 60 % | 7 | 7 | 100 % | +35.5 % | 57 % | 29 % | 0.84 |
| 60 % – 100 % | 4 | 4 | 100 % | +76.5 % | 100 % | 100 % | 0.49 |

## Nach Volatilität (CV)

| Volatilität (CV) | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0 % – 2 % | 11 | 8 | 100 % | +24.9 % | 100 % | 88 % | 0.47 |
| 2 % – 4 % | 31 | 31 | 93 % | +12.8 % | 79 % | 81 % | 0.79 |
| 4 % – 7 % | 68 | 68 | 94 % | +16.6 % | 74 % | 97 % | 0.76 |
| 7 % – 10 % | 6 | 6 | 75 % | +5.9 % | 50 % | 83 % | 1.01 |

## Nach Tagesvolumen

| Tagesvolumen | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0 – 200 | 58 | 55 | 92 % | +13.0 % | 81 % | 85 % | 0.72 |
| 200 – 1.000 | 48 | 48 | 98 % | +18.2 % | 78 % | 96 % | 0.76 |
| 1.000 – 5.000 | 10 | 10 | 75 % | +6.0 % | 38 % | 100 % | 0.95 |

**Lesehilfe:** *profitabel nach 48 h* = Kauf zum geplanten Gebot und Verkauf zum dann günstigsten Angebot − 1 wäre nach Gebühren im Plus gewesen. *Preis gehalten* = günstigstes Angebot höchstens 5 % unter dem geplanten Verkaufspreis. *Gebot überholt* = jemand bot binnen 24 h mehr. *Volumen* < 1 heißt: Die Schätzung war zu optimistisch.

## Filter-Trichter der heutigen Analyse

| Filter | Items | Anteil |
|---|---:|---:|
| kein Kaufgebot oder kein Verkaufsangebot | 3333 | 11.9 % |
| kein Spread nach Über-/Unterbieten | 334 | 1.2 % |
| Kaufpreis unter Minimum | 6095 | 21.8 % |
| ROI unter Minimum | 2456 | 8.8 % |
| ROI über Maximum (Ausreißer) | 6213 | 22.2 % |
| zu wenig Nachfrage im Orderbuch | 5881 | 21.0 % |
| zu wenig Angebot im Orderbuch | 1672 | 6.0 % |
| keine ausreichende Historie | 1383 | 4.9 % |
| Tagesvolumen unter Minimum | 394 | 1.4 % |
| Volatilität zu hoch | 126 | 0.4 % |
| besteht alle budgetunabhängigen Filter | 122 | 0.4 % |
