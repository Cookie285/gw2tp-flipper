# Auswertung – 2026-11-08

Rückblick auf frühere Einkaufslisten anhand der stündlichen Snapshots. Grundlage für das Feintuning der Schwellwerte in `config.yaml` (Phase 5).

Ausgewertet: 3 Listen vom 02.11.2026 bis 05.11.2026.

## Gesamt

| | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| alle | 30 | 25 | 92 % | +15.6 % | 67 % | 80 % | 0.75 |
| Historien-Modus | 20 | 20 | 89 % | +12.3 % | 63 % | 100 % | 0.75 |
| Orderbuch-Modus | 10 | 5 | 100 % | +112.6 % | 80 % | 0 % | – |

Die Aufschlüsselung unten enthält nur Listen aus dem Historien-Modus. Listen aus dem Orderbuch-Modus (ohne Volumenschätzung) enthalten oft illiquide Ausreißer, deren Gebote kaum gefüllt würden, und verzerren sonst die Statistik.

## Nach Ampel

| Ampel | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| gelb | 10 | 10 | 100 % | +18.7 % | 78 % | 100 % | 0.74 |
| rot | 10 | 10 | 80 % | +10.8 % | 50 % | 100 % | 0.82 |

## Nach geplanter ROI

| geplanter ROI | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| 10 % – 20 % | 12 | 12 | 91 % | +12.0 % | 73 % | 100 % | 0.91 |
| 20 % – 35 % | 6 | 6 | 83 % | +15.0 % | 33 % | 100 % | 0.35 |
| 35 % – 60 % | 2 | 2 | 100 % | +34.8 % | 100 % | 100 % | 0.63 |

## Nach Volatilität (CV)

| Volatilität (CV) | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2 % – 4 % | 7 | 7 | 100 % | +16.7 % | 83 % | 100 % | 0.72 |
| 4 % – 7 % | 7 | 7 | 100 % | +12.2 % | 86 % | 100 % | 0.90 |
| 7 % – 10 % | 6 | 6 | 67 % | +9.5 % | 17 % | 100 % | 0.35 |

## Nach Tagesvolumen

| Tagesvolumen | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0 – 200 | 6 | 6 | 100 % | +16.7 % | 100 % | 100 % | 0.79 |
| 200 – 1.000 | 11 | 11 | 80 % | +9.7 % | 30 % | 100 % | 0.45 |
| 1.000 – 5.000 | 2 | 2 | 100 % | +13.2 % | 100 % | 100 % | 1.21 |
| 5.000 – 20.000 | 1 | 1 | 100 % | +5.3 % | 100 % | 100 % | 0.73 |

**Lesehilfe:** *profitabel nach 48 h* = Kauf zum geplanten Gebot und Verkauf zum dann günstigsten Angebot − 1 wäre nach Gebühren im Plus gewesen. *Preis gehalten* = günstigstes Angebot höchstens 5 % unter dem geplanten Verkaufspreis. *Gebot überholt* = jemand bot binnen 24 h mehr. *Volumen* < 1 heißt: Die Schätzung war zu optimistisch.

## Filter-Trichter der heutigen Analyse

| Filter | Items | Anteil |
|---|---:|---:|
| kein Kaufgebot oder kein Verkaufsangebot | 3332 | 11.9 % |
| kein Spread nach Über-/Unterbieten | 318 | 1.1 % |
| Kaufpreis unter Minimum | 6063 | 21.7 % |
| ROI unter Minimum | 2384 | 8.5 % |
| ROI über Maximum (Ausreißer) | 6250 | 22.3 % |
| zu wenig Nachfrage im Orderbuch | 5911 | 21.1 % |
| zu wenig Angebot im Orderbuch | 1678 | 6.0 % |
| keine ausreichende Historie | 1439 | 5.1 % |
| Tagesvolumen unter Minimum | 382 | 1.4 % |
| Volatilität zu hoch | 128 | 0.5 % |
| Abwärtstrend | 3 | 0.0 % |
| besteht alle budgetunabhängigen Filter | 111 | 0.4 % |
