# Auswertung – 2026-11-27

Rückblick auf frühere Einkaufslisten anhand der stündlichen Snapshots. Grundlage für das Feintuning der Schwellwerte in `config.yaml` (Phase 5).

Ausgewertet: 13 Listen vom 13.11.2026 bis 25.11.2026.

## Gesamt

| | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| alle | 112 | 111 | 97 % | +16.2 % | 80 % | 86 % | 0.71 |
| Historien-Modus | 112 | 111 | 97 % | +16.2 % | 80 % | 86 % | 0.71 |

## Nach Ampel

| Ampel | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| grün | 19 | 19 | 95 % | +18.7 % | 84 % | 79 % | 0.73 |
| gelb | 78 | 77 | 97 % | +14.4 % | 80 % | 90 % | 0.71 |
| rot | 15 | 15 | 100 % | +25.4 % | 79 % | 73 % | 0.65 |

## Nach geplanter ROI

| geplanter ROI | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| 10 % – 20 % | 73 | 72 | 97 % | +12.9 % | 80 % | 88 % | 0.72 |
| 20 % – 35 % | 22 | 22 | 95 % | +21.9 % | 75 % | 95 % | 0.70 |
| 35 % – 60 % | 9 | 9 | 100 % | +35.5 % | 78 % | 44 % | 0.84 |
| 60 % – 100 % | 7 | 7 | 100 % | +72.2 % | 100 % | 100 % | 0.36 |
| ≥ 100 % | 1 | 1 | 100 % | +102.1 % | 100 % | 0 % | 0.00 |

## Nach Volatilität (CV)

| Volatilität (CV) | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0 % – 2 % | 8 | 8 | 100 % | +14.1 % | 100 % | 75 % | 0.31 |
| 2 % – 4 % | 33 | 33 | 94 % | +13.9 % | 84 % | 73 % | 0.58 |
| 4 % – 7 % | 71 | 70 | 98 % | +17.6 % | 76 % | 93 % | 0.71 |

## Nach Tagesvolumen

| Tagesvolumen | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0 – 200 | 81 | 81 | 99 % | +17.6 % | 87 % | 83 % | 0.66 |
| 200 – 1.000 | 21 | 20 | 94 % | +14.9 % | 72 % | 90 % | 0.73 |
| 1.000 – 5.000 | 9 | 9 | 80 % | +6.0 % | 20 % | 100 % | 0.90 |
| 5.000 – 20.000 | 1 | 1 | 100 % | +8.0 % | 0 % | 100 % | 0.80 |

**Lesehilfe:** *profitabel nach 48 h* = Kauf zum geplanten Gebot und Verkauf zum dann günstigsten Angebot − 1 wäre nach Gebühren im Plus gewesen. *Preis gehalten* = günstigstes Angebot höchstens 5 % unter dem geplanten Verkaufspreis. *Gebot überholt* = jemand bot binnen 24 h mehr. *Volumen* < 1 heißt: Die Schätzung war zu optimistisch.

## Filter-Trichter der heutigen Analyse

| Filter | Items | Anteil |
|---|---:|---:|
| kein Kaufgebot oder kein Verkaufsangebot | 3291 | 11.7 % |
| kein Spread nach Über-/Unterbieten | 278 | 1.0 % |
| Kaufpreis unter Minimum | 6121 | 21.9 % |
| ROI unter Minimum | 2292 | 8.2 % |
| ROI über Maximum (Ausreißer) | 6283 | 22.4 % |
| zu wenig Nachfrage im Orderbuch | 5935 | 21.2 % |
| zu wenig Angebot im Orderbuch | 1675 | 6.0 % |
| keine ausreichende Historie | 1473 | 5.3 % |
| Tagesvolumen unter Minimum | 403 | 1.4 % |
| Volatilität zu hoch | 149 | 0.5 % |
| Abwärtstrend | 1 | 0.0 % |
| besteht alle budgetunabhängigen Filter | 108 | 0.4 % |
