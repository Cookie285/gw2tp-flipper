# Auswertung – 2026-11-19

Rückblick auf frühere Einkaufslisten anhand der stündlichen Snapshots. Grundlage für das Feintuning der Schwellwerte in `config.yaml` (Phase 5).

Ausgewertet: 13 Listen vom 05.11.2026 bis 17.11.2026.

## Gesamt

| | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| alle | 126 | 123 | 93 % | +16.1 % | 74 % | 92 % | 0.78 |
| Historien-Modus | 126 | 123 | 93 % | +16.1 % | 74 % | 92 % | 0.78 |

## Nach Ampel

| Ampel | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| grün | 9 | 9 | 89 % | +19.4 % | 78 % | 78 % | 0.73 |
| gelb | 92 | 92 | 94 % | +16.1 % | 75 % | 95 % | 0.74 |
| rot | 25 | 22 | 89 % | +13.6 % | 68 % | 86 % | 0.89 |

## Nach geplanter ROI

| geplanter ROI | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| 10 % – 20 % | 77 | 74 | 91 % | +12.3 % | 72 % | 93 % | 0.81 |
| 20 % – 35 % | 37 | 37 | 94 % | +22.8 % | 77 % | 100 % | 0.65 |
| 35 % – 60 % | 8 | 8 | 100 % | +35.1 % | 62 % | 38 % | 0.82 |
| 60 % – 100 % | 4 | 4 | 100 % | +76.5 % | 100 % | 100 % | 0.49 |

## Nach Volatilität (CV)

| Volatilität (CV) | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0 % – 2 % | 11 | 8 | 100 % | +24.9 % | 100 % | 88 % | 0.47 |
| 2 % – 4 % | 33 | 33 | 94 % | +12.8 % | 77 % | 82 % | 0.73 |
| 4 % – 7 % | 72 | 72 | 94 % | +16.2 % | 74 % | 97 % | 0.81 |
| 7 % – 10 % | 10 | 10 | 75 % | +8.1 % | 38 % | 90 % | 0.94 |

## Nach Tagesvolumen

| Tagesvolumen | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0 – 200 | 60 | 57 | 93 % | +13.0 % | 82 % | 86 % | 0.72 |
| 200 – 1.000 | 55 | 55 | 96 % | +17.6 % | 71 % | 96 % | 0.78 |
| 1.000 – 5.000 | 11 | 11 | 78 % | +6.0 % | 44 % | 100 % | 0.96 |

**Lesehilfe:** *profitabel nach 48 h* = Kauf zum geplanten Gebot und Verkauf zum dann günstigsten Angebot − 1 wäre nach Gebühren im Plus gewesen. *Preis gehalten* = günstigstes Angebot höchstens 5 % unter dem geplanten Verkaufspreis. *Gebot überholt* = jemand bot binnen 24 h mehr. *Volumen* < 1 heißt: Die Schätzung war zu optimistisch.

## Filter-Trichter der heutigen Analyse

| Filter | Items | Anteil |
|---|---:|---:|
| kein Kaufgebot oder kein Verkaufsangebot | 3333 | 11.9 % |
| kein Spread nach Über-/Unterbieten | 341 | 1.2 % |
| Kaufpreis unter Minimum | 6081 | 21.7 % |
| ROI unter Minimum | 2482 | 8.9 % |
| ROI über Maximum (Ausreißer) | 6216 | 22.2 % |
| zu wenig Nachfrage im Orderbuch | 5862 | 20.9 % |
| zu wenig Angebot im Orderbuch | 1666 | 5.9 % |
| keine ausreichende Historie | 1388 | 5.0 % |
| Tagesvolumen unter Minimum | 393 | 1.4 % |
| Volatilität zu hoch | 121 | 0.4 % |
| Abwärtstrend | 1 | 0.0 % |
| besteht alle budgetunabhängigen Filter | 125 | 0.4 % |
