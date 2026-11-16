# Auswertung – 2026-11-16

Rückblick auf frühere Einkaufslisten anhand der stündlichen Snapshots. Grundlage für das Feintuning der Schwellwerte in `config.yaml` (Phase 5).

Ausgewertet: 11 Listen vom 02.11.2026 bis 13.11.2026.

## Gesamt

| | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| alle | 109 | 101 | 94 % | +16.2 % | 76 % | 91 % | 0.79 |
| Historien-Modus | 99 | 96 | 93 % | +16.0 % | 76 % | 96 % | 0.79 |
| Orderbuch-Modus | 10 | 5 | 100 % | +112.6 % | 80 % | 0 % | – |

Die Aufschlüsselung unten enthält nur Listen aus dem Historien-Modus. Listen aus dem Orderbuch-Modus (ohne Volumenschätzung) enthalten oft illiquide Ausreißer, deren Gebote kaum gefüllt würden, und verzerren sonst die Statistik.

## Nach Ampel

| Ampel | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| gelb | 71 | 71 | 96 % | +17.4 % | 80 % | 96 % | 0.74 |
| rot | 28 | 25 | 86 % | +10.9 % | 64 % | 96 % | 0.92 |

## Nach geplanter ROI

| geplanter ROI | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| 10 % – 20 % | 62 | 59 | 93 % | +12.9 % | 79 % | 97 % | 0.90 |
| 20 % – 35 % | 32 | 32 | 94 % | +23.6 % | 74 % | 100 % | 0.56 |
| 35 % – 60 % | 5 | 5 | 100 % | +34.8 % | 60 % | 60 % | 0.81 |

## Nach Volatilität (CV)

| Volatilität (CV) | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0 % – 2 % | 8 | 5 | 100 % | +24.8 % | 100 % | 100 % | 0.52 |
| 2 % – 4 % | 23 | 23 | 100 % | +13.0 % | 86 % | 91 % | 0.77 |
| 4 % – 7 % | 56 | 56 | 95 % | +16.2 % | 79 % | 98 % | 0.81 |
| 7 % – 10 % | 12 | 12 | 70 % | +8.1 % | 30 % | 92 % | 0.68 |

## Nach Tagesvolumen

| Tagesvolumen | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0 – 200 | 40 | 37 | 92 % | +14.3 % | 84 % | 92 % | 0.77 |
| 200 – 1.000 | 51 | 51 | 96 % | +17.2 % | 70 % | 98 % | 0.72 |
| 1.000 – 5.000 | 7 | 7 | 86 % | +9.7 % | 71 % | 100 % | 1.00 |
| 5.000 – 20.000 | 1 | 1 | 100 % | +5.3 % | 100 % | 100 % | 0.73 |

**Lesehilfe:** *profitabel nach 48 h* = Kauf zum geplanten Gebot und Verkauf zum dann günstigsten Angebot − 1 wäre nach Gebühren im Plus gewesen. *Preis gehalten* = günstigstes Angebot höchstens 5 % unter dem geplanten Verkaufspreis. *Gebot überholt* = jemand bot binnen 24 h mehr. *Volumen* < 1 heißt: Die Schätzung war zu optimistisch.

## Filter-Trichter der heutigen Analyse

| Filter | Items | Anteil |
|---|---:|---:|
| kein Kaufgebot oder kein Verkaufsangebot | 3322 | 11.9 % |
| kein Spread nach Über-/Unterbieten | 345 | 1.2 % |
| Kaufpreis unter Minimum | 6081 | 21.7 % |
| ROI unter Minimum | 2363 | 8.4 % |
| ROI über Maximum (Ausreißer) | 6214 | 22.2 % |
| zu wenig Nachfrage im Orderbuch | 5938 | 21.2 % |
| zu wenig Angebot im Orderbuch | 1670 | 6.0 % |
| keine ausreichende Historie | 1438 | 5.1 % |
| Tagesvolumen unter Minimum | 406 | 1.4 % |
| Volatilität zu hoch | 121 | 0.4 % |
| Abwärtstrend | 3 | 0.0 % |
| besteht alle budgetunabhängigen Filter | 108 | 0.4 % |
