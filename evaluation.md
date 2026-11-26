# Auswertung – 2026-11-26

Rückblick auf frühere Einkaufslisten anhand der stündlichen Snapshots. Grundlage für das Feintuning der Schwellwerte in `config.yaml` (Phase 5).

Ausgewertet: 13 Listen vom 12.11.2026 bis 24.11.2026.

## Gesamt

| | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| alle | 112 | 111 | 96 % | +16.1 % | 77 % | 85 % | 0.71 |
| Historien-Modus | 112 | 111 | 96 % | +16.1 % | 77 % | 85 % | 0.71 |

## Nach Ampel

| Ampel | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| grün | 18 | 18 | 94 % | +17.4 % | 83 % | 78 % | 0.88 |
| gelb | 79 | 78 | 96 % | +14.2 % | 75 % | 88 % | 0.70 |
| rot | 15 | 15 | 100 % | +25.4 % | 79 % | 73 % | 0.65 |

## Nach geplanter ROI

| geplanter ROI | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| 10 % – 20 % | 72 | 71 | 95 % | +12.4 % | 74 % | 87 % | 0.71 |
| 20 % – 35 % | 22 | 22 | 95 % | +22.0 % | 75 % | 95 % | 0.73 |
| 35 % – 60 % | 10 | 10 | 100 % | +36.8 % | 80 % | 40 % | 0.60 |
| 60 % – 100 % | 7 | 7 | 100 % | +72.2 % | 100 % | 100 % | 0.36 |
| ≥ 100 % | 1 | 1 | 100 % | +102.1 % | 100 % | 0 % | 0.00 |

## Nach Volatilität (CV)

| Volatilität (CV) | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0 % – 2 % | 9 | 9 | 100 % | +15.1 % | 100 % | 78 % | 0.41 |
| 2 % – 4 % | 34 | 34 | 94 % | +13.5 % | 81 % | 71 % | 0.70 |
| 4 % – 7 % | 69 | 68 | 97 % | +17.6 % | 71 % | 93 % | 0.71 |

## Nach Tagesvolumen

| Tagesvolumen | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0 – 200 | 79 | 79 | 97 % | +17.1 % | 84 % | 81 % | 0.66 |
| 200 – 1.000 | 23 | 22 | 95 % | +15.3 % | 67 % | 91 % | 0.73 |
| 1.000 – 5.000 | 9 | 9 | 80 % | +6.0 % | 20 % | 100 % | 0.90 |
| 5.000 – 20.000 | 1 | 1 | 100 % | +8.0 % | 0 % | 100 % | 0.80 |

**Lesehilfe:** *profitabel nach 48 h* = Kauf zum geplanten Gebot und Verkauf zum dann günstigsten Angebot − 1 wäre nach Gebühren im Plus gewesen. *Preis gehalten* = günstigstes Angebot höchstens 5 % unter dem geplanten Verkaufspreis. *Gebot überholt* = jemand bot binnen 24 h mehr. *Volumen* < 1 heißt: Die Schätzung war zu optimistisch.

## Filter-Trichter der heutigen Analyse

| Filter | Items | Anteil |
|---|---:|---:|
| kein Kaufgebot oder kein Verkaufsangebot | 3297 | 11.8 % |
| kein Spread nach Über-/Unterbieten | 278 | 1.0 % |
| Kaufpreis unter Minimum | 6115 | 21.8 % |
| ROI unter Minimum | 2342 | 8.4 % |
| ROI über Maximum (Ausreißer) | 6296 | 22.5 % |
| zu wenig Nachfrage im Orderbuch | 5916 | 21.1 % |
| zu wenig Angebot im Orderbuch | 1670 | 6.0 % |
| keine ausreichende Historie | 1432 | 5.1 % |
| Tagesvolumen unter Minimum | 407 | 1.5 % |
| Volatilität zu hoch | 142 | 0.5 % |
| Abwärtstrend | 2 | 0.0 % |
| besteht alle budgetunabhängigen Filter | 112 | 0.4 % |
