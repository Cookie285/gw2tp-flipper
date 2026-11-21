# Auswertung – 2026-11-21

Rückblick auf frühere Einkaufslisten anhand der stündlichen Snapshots. Grundlage für das Feintuning der Schwellwerte in `config.yaml` (Phase 5).

Ausgewertet: 12 Listen vom 07.11.2026 bis 18.11.2026.

## Gesamt

| | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| alle | 116 | 112 | 93 % | +16.0 % | 75 % | 90 % | 0.75 |
| Historien-Modus | 116 | 112 | 93 % | +16.0 % | 75 % | 90 % | 0.75 |

## Nach Ampel

| Ampel | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| grün | 11 | 11 | 91 % | +19.4 % | 73 % | 82 % | 0.73 |
| gelb | 87 | 86 | 94 % | +15.5 % | 74 % | 94 % | 0.73 |
| rot | 18 | 15 | 92 % | +14.6 % | 85 % | 73 % | 0.86 |

## Nach geplanter ROI

| geplanter ROI | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| 10 % – 20 % | 73 | 69 | 92 % | +12.4 % | 73 % | 91 % | 0.78 |
| 20 % – 35 % | 30 | 30 | 93 % | +22.1 % | 79 % | 100 % | 0.73 |
| 35 % – 60 % | 8 | 8 | 100 % | +36.8 % | 62 % | 38 % | 0.86 |
| 60 % – 100 % | 5 | 5 | 100 % | +72.3 % | 100 % | 100 % | 0.38 |

## Nach Volatilität (CV)

| Volatilität (CV) | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0 % – 2 % | 12 | 9 | 100 % | +24.8 % | 100 % | 89 % | 0.42 |
| 2 % – 4 % | 31 | 31 | 93 % | +12.9 % | 79 % | 81 % | 0.83 |
| 4 % – 7 % | 70 | 69 | 94 % | +16.2 % | 71 % | 96 % | 0.75 |
| 7 % – 10 % | 3 | 3 | 50 % | +10.3 % | 50 % | 67 % | 1.11 |

## Nach Tagesvolumen

| Tagesvolumen | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0 – 200 | 61 | 58 | 93 % | +13.1 % | 80 % | 86 % | 0.69 |
| 200 – 1.000 | 44 | 43 | 98 % | +18.1 % | 78 % | 93 % | 0.74 |
| 1.000 – 5.000 | 10 | 10 | 75 % | +6.0 % | 38 % | 100 % | 0.95 |
| 5.000 – 20.000 | 1 | 1 | 100 % | +8.0 % | 0 % | 100 % | 0.80 |

**Lesehilfe:** *profitabel nach 48 h* = Kauf zum geplanten Gebot und Verkauf zum dann günstigsten Angebot − 1 wäre nach Gebühren im Plus gewesen. *Preis gehalten* = günstigstes Angebot höchstens 5 % unter dem geplanten Verkaufspreis. *Gebot überholt* = jemand bot binnen 24 h mehr. *Volumen* < 1 heißt: Die Schätzung war zu optimistisch.

## Filter-Trichter der heutigen Analyse

| Filter | Items | Anteil |
|---|---:|---:|
| kein Kaufgebot oder kein Verkaufsangebot | 3331 | 11.9 % |
| kein Spread nach Über-/Unterbieten | 329 | 1.2 % |
| Kaufpreis unter Minimum | 6095 | 21.8 % |
| ROI unter Minimum | 2425 | 8.7 % |
| ROI über Maximum (Ausreißer) | 6214 | 22.2 % |
| zu wenig Nachfrage im Orderbuch | 5900 | 21.1 % |
| zu wenig Angebot im Orderbuch | 1665 | 5.9 % |
| keine ausreichende Historie | 1401 | 5.0 % |
| Tagesvolumen unter Minimum | 397 | 1.4 % |
| Volatilität zu hoch | 141 | 0.5 % |
| Abwärtstrend | 1 | 0.0 % |
| besteht alle budgetunabhängigen Filter | 110 | 0.4 % |
