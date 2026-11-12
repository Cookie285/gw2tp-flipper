# Auswertung – 2026-11-12

Rückblick auf frühere Einkaufslisten anhand der stündlichen Snapshots. Grundlage für das Feintuning der Schwellwerte in `config.yaml` (Phase 5).

Ausgewertet: 7 Listen vom 02.11.2026 bis 09.11.2026.

## Gesamt

| | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| alle | 70 | 63 | 92 % | +16.2 % | 75 % | 90 % | 0.81 |
| Historien-Modus | 60 | 58 | 91 % | +14.6 % | 75 % | 98 % | 0.81 |
| Orderbuch-Modus | 10 | 5 | 100 % | +112.6 % | 80 % | 0 % | – |

Die Aufschlüsselung unten enthält nur Listen aus dem Historien-Modus. Listen aus dem Orderbuch-Modus (ohne Volumenschätzung) enthalten oft illiquide Ausreißer, deren Gebote kaum gefüllt würden, und verzerren sonst die Statistik.

## Nach Ampel

| Ampel | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| gelb | 36 | 36 | 94 % | +18.2 % | 80 % | 100 % | 0.79 |
| rot | 24 | 22 | 85 % | +11.9 % | 65 % | 95 % | 0.89 |

## Nach geplanter ROI

| geplanter ROI | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| 10 % – 20 % | 37 | 35 | 91 % | +12.3 % | 82 % | 97 % | 0.92 |
| 20 % – 35 % | 20 | 20 | 89 % | +24.8 % | 63 % | 100 % | 0.49 |
| 35 % – 60 % | 3 | 3 | 100 % | +31.6 % | 67 % | 100 % | 0.81 |

## Nach Volatilität (CV)

| Volatilität (CV) | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0 % – 2 % | 3 | 1 | 100 % | +25.1 % | 100 % | 100 % | 0.12 |
| 2 % – 4 % | 14 | 14 | 100 % | +14.6 % | 92 % | 100 % | 0.69 |
| 4 % – 7 % | 31 | 31 | 94 % | +16.1 % | 81 % | 100 % | 0.93 |
| 7 % – 10 % | 12 | 12 | 70 % | +8.1 % | 30 % | 92 % | 0.68 |

## Nach Tagesvolumen

| Tagesvolumen | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0 – 200 | 22 | 20 | 90 % | +15.4 % | 90 % | 100 % | 0.74 |
| 200 – 1.000 | 32 | 32 | 93 % | +16.1 % | 62 % | 97 % | 0.76 |
| 1.000 – 5.000 | 5 | 5 | 80 % | +9.7 % | 80 % | 100 % | 1.00 |
| 5.000 – 20.000 | 1 | 1 | 100 % | +5.3 % | 100 % | 100 % | 0.73 |

**Lesehilfe:** *profitabel nach 48 h* = Kauf zum geplanten Gebot und Verkauf zum dann günstigsten Angebot − 1 wäre nach Gebühren im Plus gewesen. *Preis gehalten* = günstigstes Angebot höchstens 5 % unter dem geplanten Verkaufspreis. *Gebot überholt* = jemand bot binnen 24 h mehr. *Volumen* < 1 heißt: Die Schätzung war zu optimistisch.

## Filter-Trichter der heutigen Analyse

| Filter | Items | Anteil |
|---|---:|---:|
| kein Kaufgebot oder kein Verkaufsangebot | 3340 | 11.9 % |
| kein Spread nach Über-/Unterbieten | 324 | 1.2 % |
| Kaufpreis unter Minimum | 6058 | 21.6 % |
| ROI unter Minimum | 2442 | 8.7 % |
| ROI über Maximum (Ausreißer) | 6231 | 22.2 % |
| zu wenig Nachfrage im Orderbuch | 5872 | 21.0 % |
| zu wenig Angebot im Orderbuch | 1670 | 6.0 % |
| keine ausreichende Historie | 1448 | 5.2 % |
| Tagesvolumen unter Minimum | 410 | 1.5 % |
| Volatilität zu hoch | 117 | 0.4 % |
| Abwärtstrend | 2 | 0.0 % |
| besteht alle budgetunabhängigen Filter | 95 | 0.3 % |
