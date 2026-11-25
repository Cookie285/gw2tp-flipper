# Auswertung – 2026-11-25

Rückblick auf frühere Einkaufslisten anhand der stündlichen Snapshots. Grundlage für das Feintuning der Schwellwerte in `config.yaml` (Phase 5).

Ausgewertet: 13 Listen vom 11.11.2026 bis 23.11.2026.

## Gesamt

| | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| alle | 112 | 111 | 96 % | +16.1 % | 78 % | 87 % | 0.68 |
| Historien-Modus | 112 | 111 | 96 % | +16.1 % | 78 % | 87 % | 0.68 |

## Nach Ampel

| Ampel | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| grün | 16 | 16 | 94 % | +17.4 % | 81 % | 88 % | 0.89 |
| gelb | 80 | 79 | 96 % | +14.8 % | 77 % | 90 % | 0.67 |
| rot | 16 | 16 | 100 % | +21.9 % | 80 % | 75 % | 0.68 |

## Nach geplanter ROI

| geplanter ROI | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| 10 % – 20 % | 72 | 71 | 95 % | +12.4 % | 76 % | 90 % | 0.71 |
| 20 % – 35 % | 23 | 23 | 95 % | +21.8 % | 77 % | 96 % | 0.65 |
| 35 % – 60 % | 10 | 10 | 100 % | +36.8 % | 80 % | 40 % | 0.60 |
| 60 % – 100 % | 7 | 7 | 100 % | +72.2 % | 100 % | 100 % | 0.36 |

## Nach Volatilität (CV)

| Volatilität (CV) | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0 % – 2 % | 9 | 9 | 100 % | +15.1 % | 100 % | 89 % | 0.42 |
| 2 % – 4 % | 34 | 34 | 94 % | +13.1 % | 81 % | 74 % | 0.66 |
| 4 % – 7 % | 69 | 68 | 97 % | +16.8 % | 73 % | 94 % | 0.70 |

## Nach Tagesvolumen

| Tagesvolumen | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0 – 200 | 74 | 74 | 97 % | +16.2 % | 85 % | 84 % | 0.62 |
| 200 – 1.000 | 29 | 28 | 96 % | +16.9 % | 74 % | 93 % | 0.71 |
| 1.000 – 5.000 | 8 | 8 | 83 % | +6.8 % | 33 % | 100 % | 0.92 |
| 5.000 – 20.000 | 1 | 1 | 100 % | +8.0 % | 0 % | 100 % | 0.80 |

**Lesehilfe:** *profitabel nach 48 h* = Kauf zum geplanten Gebot und Verkauf zum dann günstigsten Angebot − 1 wäre nach Gebühren im Plus gewesen. *Preis gehalten* = günstigstes Angebot höchstens 5 % unter dem geplanten Verkaufspreis. *Gebot überholt* = jemand bot binnen 24 h mehr. *Volumen* < 1 heißt: Die Schätzung war zu optimistisch.

## Filter-Trichter der heutigen Analyse

| Filter | Items | Anteil |
|---|---:|---:|
| kein Kaufgebot oder kein Verkaufsangebot | 3300 | 11.8 % |
| kein Spread nach Über-/Unterbieten | 289 | 1.0 % |
| Kaufpreis unter Minimum | 6107 | 21.8 % |
| ROI unter Minimum | 2298 | 8.2 % |
| ROI über Maximum (Ausreißer) | 6252 | 22.3 % |
| zu wenig Nachfrage im Orderbuch | 5942 | 21.2 % |
| zu wenig Angebot im Orderbuch | 1692 | 6.0 % |
| keine ausreichende Historie | 1477 | 5.3 % |
| Tagesvolumen unter Minimum | 388 | 1.4 % |
| Volatilität zu hoch | 160 | 0.6 % |
| besteht alle budgetunabhängigen Filter | 104 | 0.4 % |
