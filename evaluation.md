# Auswertung – 2026-11-23

Rückblick auf frühere Einkaufslisten anhand der stündlichen Snapshots. Grundlage für das Feintuning der Schwellwerte in `config.yaml` (Phase 5).

Ausgewertet: 12 Listen vom 09.11.2026 bis 20.11.2026.

## Gesamt

| | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| alle | 112 | 109 | 96 % | +16.2 % | 79 % | 89 % | 0.71 |
| Historien-Modus | 112 | 109 | 96 % | +16.2 % | 79 % | 89 % | 0.71 |

## Nach Ampel

| Ampel | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| grün | 12 | 12 | 92 % | +23.2 % | 75 % | 83 % | 0.66 |
| gelb | 84 | 83 | 96 % | +15.5 % | 77 % | 93 % | 0.71 |
| rot | 16 | 14 | 100 % | +28.9 % | 92 % | 71 % | 0.57 |

## Nach geplanter ROI

| geplanter ROI | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| 10 % – 20 % | 68 | 65 | 95 % | +12.4 % | 75 % | 91 % | 0.78 |
| 20 % – 35 % | 27 | 27 | 96 % | +22.0 % | 81 % | 100 % | 0.65 |
| 35 % – 60 % | 10 | 10 | 100 % | +36.8 % | 80 % | 40 % | 0.60 |
| 60 % – 100 % | 7 | 7 | 100 % | +72.2 % | 100 % | 100 % | 0.36 |

## Nach Volatilität (CV)

| Volatilität (CV) | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0 % – 2 % | 12 | 10 | 100 % | +24.2 % | 100 % | 90 % | 0.42 |
| 2 % – 4 % | 30 | 30 | 93 % | +12.9 % | 79 % | 73 % | 0.81 |
| 4 % – 7 % | 70 | 69 | 97 % | +16.7 % | 75 % | 96 % | 0.72 |

## Nach Tagesvolumen

| Tagesvolumen | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0 – 200 | 66 | 64 | 97 % | +16.1 % | 84 % | 84 % | 0.59 |
| 200 – 1.000 | 36 | 35 | 97 % | +17.9 % | 79 % | 94 % | 0.72 |
| 1.000 – 5.000 | 9 | 9 | 86 % | +7.7 % | 43 % | 100 % | 0.95 |
| 5.000 – 20.000 | 1 | 1 | 100 % | +8.0 % | 0 % | 100 % | 0.80 |

**Lesehilfe:** *profitabel nach 48 h* = Kauf zum geplanten Gebot und Verkauf zum dann günstigsten Angebot − 1 wäre nach Gebühren im Plus gewesen. *Preis gehalten* = günstigstes Angebot höchstens 5 % unter dem geplanten Verkaufspreis. *Gebot überholt* = jemand bot binnen 24 h mehr. *Volumen* < 1 heißt: Die Schätzung war zu optimistisch.

## Filter-Trichter der heutigen Analyse

| Filter | Items | Anteil |
|---|---:|---:|
| kein Kaufgebot oder kein Verkaufsangebot | 3370 | 12.0 % |
| kein Spread nach Über-/Unterbieten | 326 | 1.2 % |
| Kaufpreis unter Minimum | 6072 | 21.7 % |
| ROI unter Minimum | 2454 | 8.8 % |
| ROI über Maximum (Ausreißer) | 6205 | 22.2 % |
| zu wenig Nachfrage im Orderbuch | 5870 | 21.0 % |
| zu wenig Angebot im Orderbuch | 1681 | 6.0 % |
| keine ausreichende Historie | 1383 | 4.9 % |
| Tagesvolumen unter Minimum | 402 | 1.4 % |
| Volatilität zu hoch | 140 | 0.5 % |
| Abwärtstrend | 1 | 0.0 % |
| besteht alle budgetunabhängigen Filter | 105 | 0.4 % |
