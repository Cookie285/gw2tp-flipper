# Auswertung – 2026-11-13

Rückblick auf frühere Einkaufslisten anhand der stündlichen Snapshots. Grundlage für das Feintuning der Schwellwerte in `config.yaml` (Phase 5).

Ausgewertet: 8 Listen vom 02.11.2026 bis 10.11.2026.

## Gesamt

| | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| alle | 80 | 72 | 93 % | +16.1 % | 75 % | 92 % | 0.81 |
| Historien-Modus | 70 | 67 | 92 % | +15.3 % | 75 % | 99 % | 0.81 |
| Orderbuch-Modus | 10 | 5 | 100 % | +112.6 % | 80 % | 0 % | – |

Die Aufschlüsselung unten enthält nur Listen aus dem Historien-Modus. Listen aus dem Orderbuch-Modus (ohne Volumenschätzung) enthalten oft illiquide Ausreißer, deren Gebote kaum gefüllt würden, und verzerren sonst die Statistik.

## Nach Ampel

| Ampel | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| gelb | 45 | 45 | 95 % | +17.9 % | 80 % | 100 % | 0.81 |
| rot | 25 | 22 | 85 % | +11.9 % | 65 % | 95 % | 0.89 |

## Nach geplanter ROI

| geplanter ROI | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| 10 % – 20 % | 44 | 41 | 92 % | +13.6 % | 82 % | 98 % | 0.93 |
| 20 % – 35 % | 23 | 23 | 91 % | +24.9 % | 64 % | 100 % | 0.52 |
| 35 % – 60 % | 3 | 3 | 100 % | +31.6 % | 67 % | 100 % | 0.81 |

## Nach Volatilität (CV)

| Volatilität (CV) | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0 % – 2 % | 5 | 2 | 100 % | +25.1 % | 100 % | 100 % | 0.32 |
| 2 % – 4 % | 15 | 15 | 100 % | +13.8 % | 93 % | 100 % | 0.72 |
| 4 % – 7 % | 38 | 38 | 95 % | +16.1 % | 79 % | 100 % | 0.94 |
| 7 % – 10 % | 12 | 12 | 70 % | +8.1 % | 30 % | 92 % | 0.68 |

## Nach Tagesvolumen

| Tagesvolumen | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0 – 200 | 26 | 23 | 91 % | +14.6 % | 87 % | 100 % | 0.72 |
| 200 – 1.000 | 38 | 38 | 94 % | +16.1 % | 66 % | 97 % | 0.84 |
| 1.000 – 5.000 | 5 | 5 | 80 % | +9.7 % | 80 % | 100 % | 1.00 |
| 5.000 – 20.000 | 1 | 1 | 100 % | +5.3 % | 100 % | 100 % | 0.73 |

**Lesehilfe:** *profitabel nach 48 h* = Kauf zum geplanten Gebot und Verkauf zum dann günstigsten Angebot − 1 wäre nach Gebühren im Plus gewesen. *Preis gehalten* = günstigstes Angebot höchstens 5 % unter dem geplanten Verkaufspreis. *Gebot überholt* = jemand bot binnen 24 h mehr. *Volumen* < 1 heißt: Die Schätzung war zu optimistisch.

## Filter-Trichter der heutigen Analyse

| Filter | Items | Anteil |
|---|---:|---:|
| kein Kaufgebot oder kein Verkaufsangebot | 3326 | 11.9 % |
| kein Spread nach Über-/Unterbieten | 309 | 1.1 % |
| Kaufpreis unter Minimum | 6080 | 21.7 % |
| ROI unter Minimum | 2442 | 8.7 % |
| ROI über Maximum (Ausreißer) | 6229 | 22.2 % |
| zu wenig Nachfrage im Orderbuch | 5893 | 21.0 % |
| zu wenig Angebot im Orderbuch | 1659 | 5.9 % |
| keine ausreichende Historie | 1429 | 5.1 % |
| Tagesvolumen unter Minimum | 409 | 1.5 % |
| Volatilität zu hoch | 125 | 0.4 % |
| besteht alle budgetunabhängigen Filter | 108 | 0.4 % |
