# Auswertung – 2026-11-20

Rückblick auf frühere Einkaufslisten anhand der stündlichen Snapshots. Grundlage für das Feintuning der Schwellwerte in `config.yaml` (Phase 5).

Ausgewertet: 13 Listen vom 06.11.2026 bis 18.11.2026.

## Gesamt

| | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| alle | 126 | 122 | 94 % | +16.1 % | 77 % | 91 % | 0.74 |
| Historien-Modus | 126 | 122 | 94 % | +16.1 % | 77 % | 91 % | 0.74 |

## Nach Ampel

| Ampel | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| grün | 11 | 11 | 91 % | +19.4 % | 73 % | 82 % | 0.73 |
| gelb | 93 | 92 | 94 % | +16.1 % | 77 % | 95 % | 0.72 |
| rot | 22 | 19 | 94 % | +14.0 % | 81 % | 79 % | 0.86 |

## Nach geplanter ROI

| geplanter ROI | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| 10 % – 20 % | 79 | 75 | 93 % | +12.4 % | 75 % | 92 % | 0.75 |
| 20 % – 35 % | 34 | 34 | 94 % | +23.2 % | 81 % | 100 % | 0.73 |
| 35 % – 60 % | 8 | 8 | 100 % | +36.8 % | 62 % | 38 % | 0.86 |
| 60 % – 100 % | 5 | 5 | 100 % | +72.3 % | 100 % | 100 % | 0.38 |

## Nach Volatilität (CV)

| Volatilität (CV) | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0 % – 2 % | 12 | 9 | 100 % | +24.8 % | 100 % | 89 % | 0.42 |
| 2 % – 4 % | 33 | 33 | 94 % | +12.9 % | 81 % | 82 % | 0.79 |
| 4 % – 7 % | 75 | 74 | 94 % | +16.4 % | 74 % | 96 % | 0.75 |
| 7 % – 10 % | 6 | 6 | 75 % | +5.9 % | 50 % | 83 % | 1.01 |

## Nach Tagesvolumen

| Tagesvolumen | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0 – 200 | 64 | 61 | 93 % | +13.2 % | 81 % | 87 % | 0.65 |
| 200 – 1.000 | 51 | 50 | 98 % | +18.1 % | 79 % | 94 % | 0.76 |
| 1.000 – 5.000 | 10 | 10 | 75 % | +6.0 % | 38 % | 100 % | 0.95 |
| 5.000 – 20.000 | 1 | 1 | – | – | – | 100 % | 0.80 |

**Lesehilfe:** *profitabel nach 48 h* = Kauf zum geplanten Gebot und Verkauf zum dann günstigsten Angebot − 1 wäre nach Gebühren im Plus gewesen. *Preis gehalten* = günstigstes Angebot höchstens 5 % unter dem geplanten Verkaufspreis. *Gebot überholt* = jemand bot binnen 24 h mehr. *Volumen* < 1 heißt: Die Schätzung war zu optimistisch.

## Filter-Trichter der heutigen Analyse

| Filter | Items | Anteil |
|---|---:|---:|
| kein Kaufgebot oder kein Verkaufsangebot | 3330 | 11.9 % |
| kein Spread nach Über-/Unterbieten | 346 | 1.2 % |
| Kaufpreis unter Minimum | 6086 | 21.7 % |
| ROI unter Minimum | 2425 | 8.7 % |
| ROI über Maximum (Ausreißer) | 6196 | 22.1 % |
| zu wenig Nachfrage im Orderbuch | 5898 | 21.1 % |
| zu wenig Angebot im Orderbuch | 1666 | 5.9 % |
| keine ausreichende Historie | 1410 | 5.0 % |
| Tagesvolumen unter Minimum | 392 | 1.4 % |
| Volatilität zu hoch | 143 | 0.5 % |
| besteht alle budgetunabhängigen Filter | 117 | 0.4 % |
