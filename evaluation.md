# Auswertung – 2026-11-14

Rückblick auf frühere Einkaufslisten anhand der stündlichen Snapshots. Grundlage für das Feintuning der Schwellwerte in `config.yaml` (Phase 5).

Ausgewertet: 9 Listen vom 02.11.2026 bis 11.11.2026.

## Gesamt

| | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| alle | 90 | 82 | 94 % | +16.2 % | 78 % | 93 % | 0.73 |
| Historien-Modus | 80 | 77 | 93 % | +16.1 % | 78 % | 99 % | 0.73 |
| Orderbuch-Modus | 10 | 5 | 100 % | +112.6 % | 80 % | 0 % | – |

Die Aufschlüsselung unten enthält nur Listen aus dem Historien-Modus. Listen aus dem Orderbuch-Modus (ohne Volumenschätzung) enthalten oft illiquide Ausreißer, deren Gebote kaum gefüllt würden, und verzerren sonst die Statistik.

## Nach Ampel

| Ampel | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| gelb | 54 | 54 | 96 % | +17.7 % | 83 % | 100 % | 0.72 |
| rot | 26 | 23 | 86 % | +11.9 % | 67 % | 96 % | 0.86 |

## Nach geplanter ROI

| geplanter ROI | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| 10 % – 20 % | 50 | 47 | 93 % | +13.9 % | 84 % | 98 % | 0.90 |
| 20 % – 35 % | 27 | 27 | 92 % | +24.8 % | 69 % | 100 % | 0.55 |
| 35 % – 60 % | 3 | 3 | 100 % | +31.6 % | 67 % | 100 % | 0.81 |

## Nach Volatilität (CV)

| Volatilität (CV) | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0 % – 2 % | 6 | 3 | 100 % | +25.0 % | 100 % | 100 % | 0.52 |
| 2 % – 4 % | 17 | 17 | 100 % | +13.8 % | 94 % | 100 % | 0.72 |
| 4 % – 7 % | 45 | 45 | 96 % | +16.2 % | 82 % | 100 % | 0.81 |
| 7 % – 10 % | 12 | 12 | 70 % | +8.1 % | 30 % | 92 % | 0.68 |

## Nach Tagesvolumen

| Tagesvolumen | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0 – 200 | 29 | 26 | 92 % | +14.8 % | 88 % | 100 % | 0.69 |
| 200 – 1.000 | 44 | 44 | 95 % | +16.9 % | 71 % | 98 % | 0.72 |
| 1.000 – 5.000 | 6 | 6 | 83 % | +10.8 % | 83 % | 100 % | 0.98 |
| 5.000 – 20.000 | 1 | 1 | 100 % | +5.3 % | 100 % | 100 % | 0.73 |

**Lesehilfe:** *profitabel nach 48 h* = Kauf zum geplanten Gebot und Verkauf zum dann günstigsten Angebot − 1 wäre nach Gebühren im Plus gewesen. *Preis gehalten* = günstigstes Angebot höchstens 5 % unter dem geplanten Verkaufspreis. *Gebot überholt* = jemand bot binnen 24 h mehr. *Volumen* < 1 heißt: Die Schätzung war zu optimistisch.

## Filter-Trichter der heutigen Analyse

| Filter | Items | Anteil |
|---|---:|---:|
| kein Kaufgebot oder kein Verkaufsangebot | 3311 | 11.8 % |
| kein Spread nach Über-/Unterbieten | 316 | 1.1 % |
| Kaufpreis unter Minimum | 6100 | 21.8 % |
| ROI unter Minimum | 2396 | 8.6 % |
| ROI über Maximum (Ausreißer) | 6204 | 22.2 % |
| zu wenig Nachfrage im Orderbuch | 5918 | 21.1 % |
| zu wenig Angebot im Orderbuch | 1681 | 6.0 % |
| keine ausreichende Historie | 1435 | 5.1 % |
| Tagesvolumen unter Minimum | 408 | 1.5 % |
| Volatilität zu hoch | 132 | 0.5 % |
| Abwärtstrend | 1 | 0.0 % |
| besteht alle budgetunabhängigen Filter | 107 | 0.4 % |
