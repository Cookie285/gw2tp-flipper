# Auswertung – 2026-11-08

Rückblick auf frühere Einkaufslisten anhand der stündlichen Snapshots. Grundlage für das Feintuning der Schwellwerte in `config.yaml` (Phase 5).

Ausgewertet: 4 Listen vom 02.11.2026 bis 06.11.2026.

## Gesamt

| | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| alle | 40 | 35 | 94 % | +16.6 % | 73 % | 86 % | 0.72 |
| Historien-Modus | 30 | 30 | 93 % | +13.1 % | 71 % | 100 % | 0.72 |
| Orderbuch-Modus | 10 | 5 | 100 % | +112.6 % | 80 % | 0 % | – |

Die Aufschlüsselung unten enthält nur Listen aus dem Historien-Modus. Listen aus dem Orderbuch-Modus (ohne Volumenschätzung) enthalten oft illiquide Ausreißer, deren Gebote kaum gefüllt würden, und verzerren sonst die Statistik.

## Nach Ampel

| Ampel | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| gelb | 16 | 16 | 100 % | +18.7 % | 87 % | 100 % | 0.69 |
| rot | 14 | 14 | 85 % | +9.8 % | 54 % | 100 % | 0.82 |

## Nach geplanter ROI

| geplanter ROI | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| 10 % – 20 % | 18 | 18 | 94 % | +12.2 % | 76 % | 100 % | 0.86 |
| 20 % – 35 % | 10 | 10 | 89 % | +27.4 % | 56 % | 100 % | 0.49 |
| 35 % – 60 % | 2 | 2 | 100 % | +34.8 % | 100 % | 100 % | 0.63 |

## Nach Volatilität (CV)

| Volatilität (CV) | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2 % – 4 % | 9 | 9 | 100 % | +16.7 % | 88 % | 100 % | 0.65 |
| 4 % – 7 % | 12 | 12 | 100 % | +15.7 % | 92 % | 100 % | 0.86 |
| 7 % – 10 % | 9 | 9 | 75 % | +8.1 % | 25 % | 100 % | 0.43 |

## Nach Tagesvolumen

| Tagesvolumen | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0 – 200 | 9 | 9 | 100 % | +17.7 % | 100 % | 100 % | 0.65 |
| 200 – 1.000 | 18 | 18 | 88 % | +12.4 % | 50 % | 100 % | 0.62 |
| 1.000 – 5.000 | 2 | 2 | 100 % | +13.2 % | 100 % | 100 % | 1.21 |
| 5.000 – 20.000 | 1 | 1 | 100 % | +5.3 % | 100 % | 100 % | 0.73 |

**Lesehilfe:** *profitabel nach 48 h* = Kauf zum geplanten Gebot und Verkauf zum dann günstigsten Angebot − 1 wäre nach Gebühren im Plus gewesen. *Preis gehalten* = günstigstes Angebot höchstens 5 % unter dem geplanten Verkaufspreis. *Gebot überholt* = jemand bot binnen 24 h mehr. *Volumen* < 1 heißt: Die Schätzung war zu optimistisch.

## Filter-Trichter der heutigen Analyse

| Filter | Items | Anteil |
|---|---:|---:|
| kein Kaufgebot oder kein Verkaufsangebot | 3333 | 11.9 % |
| kein Spread nach Über-/Unterbieten | 338 | 1.2 % |
| Kaufpreis unter Minimum | 6053 | 21.6 % |
| ROI unter Minimum | 2394 | 8.6 % |
| ROI über Maximum (Ausreißer) | 6228 | 22.2 % |
| zu wenig Nachfrage im Orderbuch | 5939 | 21.2 % |
| zu wenig Angebot im Orderbuch | 1682 | 6.0 % |
| keine ausreichende Historie | 1402 | 5.0 % |
| Tagesvolumen unter Minimum | 391 | 1.4 % |
| Volatilität zu hoch | 135 | 0.5 % |
| Abwärtstrend | 3 | 0.0 % |
| besteht alle budgetunabhängigen Filter | 101 | 0.4 % |
