# Auswertung – 2026-11-22

Rückblick auf frühere Einkaufslisten anhand der stündlichen Snapshots. Grundlage für das Feintuning der Schwellwerte in `config.yaml` (Phase 5).

Ausgewertet: 12 Listen vom 08.11.2026 bis 19.11.2026.

## Gesamt

| | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| alle | 115 | 111 | 94 % | +16.0 % | 75 % | 91 % | 0.72 |
| Historien-Modus | 115 | 111 | 94 % | +16.0 % | 75 % | 91 % | 0.72 |

## Nach Ampel

| Ampel | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| grün | 11 | 11 | 91 % | +19.4 % | 73 % | 82 % | 0.73 |
| gelb | 88 | 87 | 94 % | +15.1 % | 73 % | 94 % | 0.71 |
| rot | 16 | 13 | 100 % | +18.6 % | 92 % | 77 % | 0.84 |

## Nach geplanter ROI

| geplanter ROI | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| 10 % – 20 % | 70 | 66 | 94 % | +12.4 % | 74 % | 92 % | 0.74 |
| 20 % – 35 % | 29 | 29 | 93 % | +21.8 % | 75 % | 100 % | 0.65 |
| 35 % – 60 % | 10 | 10 | 100 % | +36.8 % | 70 % | 50 % | 0.86 |
| 60 % – 100 % | 6 | 6 | 100 % | +72.2 % | 100 % | 100 % | 0.37 |

## Nach Volatilität (CV)

| Volatilität (CV) | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0 % – 2 % | 13 | 10 | 100 % | +24.2 % | 100 % | 90 % | 0.42 |
| 2 % – 4 % | 29 | 29 | 93 % | +12.9 % | 78 % | 79 % | 0.79 |
| 4 % – 7 % | 73 | 72 | 94 % | +16.1 % | 71 % | 96 % | 0.73 |

## Nach Tagesvolumen

| Tagesvolumen | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0 – 200 | 65 | 62 | 93 % | +14.1 % | 80 % | 87 % | 0.59 |
| 200 – 1.000 | 40 | 39 | 97 % | +17.5 % | 76 % | 95 % | 0.74 |
| 1.000 – 5.000 | 9 | 9 | 86 % | +7.7 % | 43 % | 100 % | 0.95 |
| 5.000 – 20.000 | 1 | 1 | 100 % | +8.0 % | 0 % | 100 % | 0.80 |

**Lesehilfe:** *profitabel nach 48 h* = Kauf zum geplanten Gebot und Verkauf zum dann günstigsten Angebot − 1 wäre nach Gebühren im Plus gewesen. *Preis gehalten* = günstigstes Angebot höchstens 5 % unter dem geplanten Verkaufspreis. *Gebot überholt* = jemand bot binnen 24 h mehr. *Volumen* < 1 heißt: Die Schätzung war zu optimistisch.

## Filter-Trichter der heutigen Analyse

| Filter | Items | Anteil |
|---|---:|---:|
| kein Kaufgebot oder kein Verkaufsangebot | 3341 | 11.9 % |
| kein Spread nach Über-/Unterbieten | 322 | 1.1 % |
| Kaufpreis unter Minimum | 6093 | 21.8 % |
| ROI unter Minimum | 2400 | 8.6 % |
| ROI über Maximum (Ausreißer) | 6221 | 22.2 % |
| zu wenig Nachfrage im Orderbuch | 5916 | 21.1 % |
| zu wenig Angebot im Orderbuch | 1668 | 6.0 % |
| keine ausreichende Historie | 1398 | 5.0 % |
| Tagesvolumen unter Minimum | 401 | 1.4 % |
| Volatilität zu hoch | 145 | 0.5 % |
| Abwärtstrend | 1 | 0.0 % |
| besteht alle budgetunabhängigen Filter | 103 | 0.4 % |
