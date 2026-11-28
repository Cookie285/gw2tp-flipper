# Auswertung – 2026-11-28

Rückblick auf frühere Einkaufslisten anhand der stündlichen Snapshots. Grundlage für das Feintuning der Schwellwerte in `config.yaml` (Phase 5).

Ausgewertet: 12 Listen vom 14.11.2026 bis 25.11.2026.

## Gesamt

| | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| alle | 102 | 101 | 97 % | +16.2 % | 81 % | 85 % | 0.68 |
| Historien-Modus | 102 | 101 | 97 % | +16.2 % | 81 % | 85 % | 0.68 |

## Nach Ampel

| Ampel | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| grün | 19 | 19 | 95 % | +18.7 % | 84 % | 79 % | 0.73 |
| gelb | 70 | 69 | 97 % | +14.4 % | 79 % | 90 % | 0.70 |
| rot | 13 | 13 | 100 % | +28.9 % | 85 % | 69 % | 0.35 |

## Nach geplanter ROI

| geplanter ROI | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| 10 % – 20 % | 67 | 66 | 97 % | +13.1 % | 80 % | 86 % | 0.71 |
| 20 % – 35 % | 19 | 19 | 94 % | +22.1 % | 71 % | 95 % | 0.71 |
| 35 % – 60 % | 8 | 8 | 100 % | +36.8 % | 88 % | 50 % | 0.60 |
| 60 % – 100 % | 7 | 7 | 100 % | +72.2 % | 100 % | 100 % | 0.36 |
| ≥ 100 % | 1 | 1 | 100 % | +102.1 % | 100 % | 0 % | 0.00 |

## Nach Volatilität (CV)

| Volatilität (CV) | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0 % – 2 % | 7 | 7 | 100 % | +15.1 % | 100 % | 71 % | 0.20 |
| 2 % – 4 % | 29 | 29 | 93 % | +13.5 % | 86 % | 72 % | 0.54 |
| 4 % – 7 % | 66 | 65 | 98 % | +17.7 % | 76 % | 92 % | 0.71 |

## Nach Tagesvolumen

| Tagesvolumen | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0 – 200 | 75 | 75 | 99 % | +17.7 % | 88 % | 83 % | 0.60 |
| 200 – 1.000 | 18 | 17 | 94 % | +14.1 % | 69 % | 88 % | 0.74 |
| 1.000 – 5.000 | 8 | 8 | 75 % | +6.8 % | 25 % | 100 % | 0.80 |
| 5.000 – 20.000 | 1 | 1 | 100 % | +8.0 % | 0 % | 100 % | 0.80 |

**Lesehilfe:** *profitabel nach 48 h* = Kauf zum geplanten Gebot und Verkauf zum dann günstigsten Angebot − 1 wäre nach Gebühren im Plus gewesen. *Preis gehalten* = günstigstes Angebot höchstens 5 % unter dem geplanten Verkaufspreis. *Gebot überholt* = jemand bot binnen 24 h mehr. *Volumen* < 1 heißt: Die Schätzung war zu optimistisch.

## Filter-Trichter der heutigen Analyse

| Filter | Items | Anteil |
|---|---:|---:|
| kein Kaufgebot oder kein Verkaufsangebot | 3290 | 11.7 % |
| kein Spread nach Über-/Unterbieten | 272 | 1.0 % |
| Kaufpreis unter Minimum | 6124 | 21.9 % |
| ROI unter Minimum | 2269 | 8.1 % |
| ROI über Maximum (Ausreißer) | 6275 | 22.4 % |
| zu wenig Nachfrage im Orderbuch | 5941 | 21.2 % |
| zu wenig Angebot im Orderbuch | 1682 | 6.0 % |
| keine ausreichende Historie | 1489 | 5.3 % |
| Tagesvolumen unter Minimum | 411 | 1.5 % |
| Volatilität zu hoch | 139 | 0.5 % |
| besteht alle budgetunabhängigen Filter | 117 | 0.4 % |
