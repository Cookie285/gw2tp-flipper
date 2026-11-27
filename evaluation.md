# Auswertung – 2026-11-27

Rückblick auf frühere Einkaufslisten anhand der stündlichen Snapshots. Grundlage für das Feintuning der Schwellwerte in `config.yaml` (Phase 5).

Ausgewertet: 12 Listen vom 13.11.2026 bis 24.11.2026.

## Gesamt

| | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| alle | 103 | 102 | 97 % | +16.1 % | 79 % | 85 % | 0.69 |
| Historien-Modus | 103 | 102 | 97 % | +16.1 % | 79 % | 85 % | 0.69 |

## Nach Ampel

| Ampel | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| grün | 18 | 18 | 94 % | +17.4 % | 83 % | 78 % | 0.88 |
| gelb | 70 | 69 | 97 % | +14.3 % | 77 % | 90 % | 0.68 |
| rot | 15 | 15 | 100 % | +25.4 % | 79 % | 73 % | 0.65 |

## Nach geplanter ROI

| geplanter ROI | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| 10 % – 20 % | 66 | 65 | 97 % | +12.4 % | 78 % | 88 % | 0.71 |
| 20 % – 35 % | 20 | 20 | 94 % | +21.8 % | 72 % | 95 % | 0.73 |
| 35 % – 60 % | 9 | 9 | 100 % | +35.5 % | 78 % | 44 % | 0.84 |
| 60 % – 100 % | 7 | 7 | 100 % | +72.2 % | 100 % | 100 % | 0.36 |
| ≥ 100 % | 1 | 1 | 100 % | +102.1 % | 100 % | 0 % | 0.00 |

## Nach Volatilität (CV)

| Volatilität (CV) | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0 % – 2 % | 8 | 8 | 100 % | +14.1 % | 100 % | 75 % | 0.31 |
| 2 % – 4 % | 32 | 32 | 93 % | +13.9 % | 83 % | 72 % | 0.63 |
| 4 % – 7 % | 63 | 62 | 98 % | +17.6 % | 73 % | 94 % | 0.71 |

## Nach Tagesvolumen

| Tagesvolumen | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0 – 200 | 74 | 74 | 99 % | +17.6 % | 86 % | 82 % | 0.66 |
| 200 – 1.000 | 19 | 18 | 94 % | +15.3 % | 71 % | 89 % | 0.71 |
| 1.000 – 5.000 | 9 | 9 | 80 % | +6.0 % | 20 % | 100 % | 0.90 |
| 5.000 – 20.000 | 1 | 1 | 100 % | +8.0 % | 0 % | 100 % | 0.80 |

**Lesehilfe:** *profitabel nach 48 h* = Kauf zum geplanten Gebot und Verkauf zum dann günstigsten Angebot − 1 wäre nach Gebühren im Plus gewesen. *Preis gehalten* = günstigstes Angebot höchstens 5 % unter dem geplanten Verkaufspreis. *Gebot überholt* = jemand bot binnen 24 h mehr. *Volumen* < 1 heißt: Die Schätzung war zu optimistisch.

## Filter-Trichter der heutigen Analyse

| Filter | Items | Anteil |
|---|---:|---:|
| kein Kaufgebot oder kein Verkaufsangebot | 3290 | 11.7 % |
| kein Spread nach Über-/Unterbieten | 279 | 1.0 % |
| Kaufpreis unter Minimum | 6125 | 21.9 % |
| ROI unter Minimum | 2288 | 8.2 % |
| ROI über Maximum (Ausreißer) | 6269 | 22.4 % |
| zu wenig Nachfrage im Orderbuch | 5947 | 21.2 % |
| zu wenig Angebot im Orderbuch | 1679 | 6.0 % |
| keine ausreichende Historie | 1462 | 5.2 % |
| Tagesvolumen unter Minimum | 406 | 1.4 % |
| Volatilität zu hoch | 157 | 0.6 % |
| Abwärtstrend | 1 | 0.0 % |
| besteht alle budgetunabhängigen Filter | 106 | 0.4 % |
