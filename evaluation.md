# Auswertung – 2026-11-15

Rückblick auf frühere Einkaufslisten anhand der stündlichen Snapshots. Grundlage für das Feintuning der Schwellwerte in `config.yaml` (Phase 5).

Ausgewertet: 10 Listen vom 02.11.2026 bis 12.11.2026.

## Gesamt

| | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| alle | 99 | 91 | 93 % | +16.2 % | 76 % | 91 % | 0.75 |
| Historien-Modus | 89 | 86 | 93 % | +16.1 % | 76 % | 97 % | 0.75 |
| Orderbuch-Modus | 10 | 5 | 100 % | +112.6 % | 80 % | 0 % | – |

Die Aufschlüsselung unten enthält nur Listen aus dem Historien-Modus. Listen aus dem Orderbuch-Modus (ohne Volumenschätzung) enthalten oft illiquide Ausreißer, deren Gebote kaum gefüllt würden, und verzerren sonst die Statistik.

## Nach Ampel

| Ampel | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| gelb | 63 | 63 | 95 % | +17.4 % | 79 % | 97 % | 0.72 |
| rot | 26 | 23 | 86 % | +11.9 % | 67 % | 96 % | 0.86 |

## Nach geplanter ROI

| geplanter ROI | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| 10 % – 20 % | 56 | 53 | 92 % | +13.0 % | 78 % | 96 % | 0.90 |
| 20 % – 35 % | 29 | 29 | 93 % | +24.8 % | 71 % | 100 % | 0.55 |
| 35 % – 60 % | 4 | 4 | 100 % | +34.8 % | 75 % | 75 % | 0.63 |

## Nach Volatilität (CV)

| Volatilität (CV) | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0 % – 2 % | 7 | 4 | 100 % | +24.9 % | 100 % | 100 % | 0.47 |
| 2 % – 4 % | 19 | 19 | 100 % | +13.0 % | 89 % | 95 % | 0.73 |
| 4 % – 7 % | 51 | 51 | 94 % | +16.2 % | 78 % | 98 % | 0.81 |
| 7 % – 10 % | 12 | 12 | 70 % | +8.1 % | 30 % | 92 % | 0.68 |

## Nach Tagesvolumen

| Tagesvolumen | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0 – 200 | 34 | 31 | 90 % | +14.6 % | 84 % | 94 % | 0.72 |
| 200 – 1.000 | 48 | 48 | 96 % | +16.9 % | 69 % | 98 % | 0.75 |
| 1.000 – 5.000 | 6 | 6 | 83 % | +10.8 % | 83 % | 100 % | 0.98 |
| 5.000 – 20.000 | 1 | 1 | 100 % | +5.3 % | 100 % | 100 % | 0.73 |

**Lesehilfe:** *profitabel nach 48 h* = Kauf zum geplanten Gebot und Verkauf zum dann günstigsten Angebot − 1 wäre nach Gebühren im Plus gewesen. *Preis gehalten* = günstigstes Angebot höchstens 5 % unter dem geplanten Verkaufspreis. *Gebot überholt* = jemand bot binnen 24 h mehr. *Volumen* < 1 heißt: Die Schätzung war zu optimistisch.

## Filter-Trichter der heutigen Analyse

| Filter | Items | Anteil |
|---|---:|---:|
| kein Kaufgebot oder kein Verkaufsangebot | 3317 | 11.8 % |
| kein Spread nach Über-/Unterbieten | 327 | 1.2 % |
| Kaufpreis unter Minimum | 6102 | 21.8 % |
| ROI unter Minimum | 2387 | 8.5 % |
| ROI über Maximum (Ausreißer) | 6208 | 22.2 % |
| zu wenig Nachfrage im Orderbuch | 5918 | 21.1 % |
| zu wenig Angebot im Orderbuch | 1679 | 6.0 % |
| keine ausreichende Historie | 1421 | 5.1 % |
| Tagesvolumen unter Minimum | 397 | 1.4 % |
| Volatilität zu hoch | 140 | 0.5 % |
| Abwärtstrend | 1 | 0.0 % |
| besteht alle budgetunabhängigen Filter | 112 | 0.4 % |
