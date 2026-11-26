# Auswertung – 2026-11-26

Rückblick auf frühere Einkaufslisten anhand der stündlichen Snapshots. Grundlage für das Feintuning der Schwellwerte in `config.yaml` (Phase 5).

Ausgewertet: 12 Listen vom 12.11.2026 bis 23.11.2026.

## Gesamt

| | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| alle | 102 | 101 | 96 % | +16.0 % | 76 % | 86 % | 0.71 |
| Historien-Modus | 102 | 101 | 96 % | +16.0 % | 76 % | 86 % | 0.71 |

## Nach Ampel

| Ampel | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| grün | 16 | 16 | 94 % | +17.4 % | 81 % | 88 % | 0.89 |
| gelb | 71 | 70 | 95 % | +13.0 % | 74 % | 89 % | 0.70 |
| rot | 15 | 15 | 100 % | +25.4 % | 79 % | 73 % | 0.65 |

## Nach geplanter ROI

| geplanter ROI | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| 10 % – 20 % | 66 | 65 | 95 % | +12.2 % | 73 % | 89 % | 0.71 |
| 20 % – 35 % | 19 | 19 | 94 % | +21.8 % | 72 % | 95 % | 0.71 |
| 35 % – 60 % | 10 | 10 | 100 % | +36.8 % | 80 % | 40 % | 0.60 |
| 60 % – 100 % | 7 | 7 | 100 % | +72.2 % | 100 % | 100 % | 0.36 |

## Nach Volatilität (CV)

| Volatilität (CV) | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0 % – 2 % | 8 | 8 | 100 % | +14.1 % | 100 % | 88 % | 0.42 |
| 2 % – 4 % | 32 | 32 | 93 % | +13.1 % | 80 % | 72 % | 0.66 |
| 4 % – 7 % | 62 | 61 | 96 % | +16.7 % | 70 % | 93 % | 0.71 |

## Nach Tagesvolumen

| Tagesvolumen | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0 – 200 | 71 | 71 | 97 % | +16.4 % | 84 % | 83 % | 0.65 |
| 200 – 1.000 | 23 | 22 | 95 % | +15.3 % | 67 % | 91 % | 0.73 |
| 1.000 – 5.000 | 7 | 7 | 80 % | +6.0 % | 20 % | 100 % | 0.95 |
| 5.000 – 20.000 | 1 | 1 | 100 % | +8.0 % | 0 % | 100 % | 0.80 |

**Lesehilfe:** *profitabel nach 48 h* = Kauf zum geplanten Gebot und Verkauf zum dann günstigsten Angebot − 1 wäre nach Gebühren im Plus gewesen. *Preis gehalten* = günstigstes Angebot höchstens 5 % unter dem geplanten Verkaufspreis. *Gebot überholt* = jemand bot binnen 24 h mehr. *Volumen* < 1 heißt: Die Schätzung war zu optimistisch.

## Filter-Trichter der heutigen Analyse

| Filter | Items | Anteil |
|---|---:|---:|
| kein Kaufgebot oder kein Verkaufsangebot | 3292 | 11.8 % |
| kein Spread nach Über-/Unterbieten | 274 | 1.0 % |
| Kaufpreis unter Minimum | 6118 | 21.8 % |
| ROI unter Minimum | 2341 | 8.4 % |
| ROI über Maximum (Ausreißer) | 6274 | 22.4 % |
| zu wenig Nachfrage im Orderbuch | 5932 | 21.2 % |
| zu wenig Angebot im Orderbuch | 1678 | 6.0 % |
| keine ausreichende Historie | 1450 | 5.2 % |
| Tagesvolumen unter Minimum | 403 | 1.4 % |
| Volatilität zu hoch | 141 | 0.5 % |
| Abwärtstrend | 3 | 0.0 % |
| besteht alle budgetunabhängigen Filter | 103 | 0.4 % |
