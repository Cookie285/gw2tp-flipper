# Auswertung – 2026-11-11

Rückblick auf frühere Einkaufslisten anhand der stündlichen Snapshots. Grundlage für das Feintuning der Schwellwerte in `config.yaml` (Phase 5).

Ausgewertet: 6 Listen vom 02.11.2026 bis 08.11.2026.

## Gesamt

| | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| alle | 60 | 54 | 90 % | +16.2 % | 73 % | 89 % | 0.77 |
| Historien-Modus | 50 | 49 | 89 % | +14.6 % | 72 % | 98 % | 0.77 |
| Orderbuch-Modus | 10 | 5 | 100 % | +112.6 % | 80 % | 0 % | – |

Die Aufschlüsselung unten enthält nur Listen aus dem Historien-Modus. Listen aus dem Orderbuch-Modus (ohne Volumenschätzung) enthalten oft illiquide Ausreißer, deren Gebote kaum gefüllt würden, und verzerren sonst die Statistik.

## Nach Ampel

| Ampel | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| gelb | 28 | 28 | 93 % | +18.2 % | 78 % | 100 % | 0.74 |
| rot | 22 | 21 | 84 % | +12.0 % | 63 % | 95 % | 0.86 |

## Nach geplanter ROI

| geplanter ROI | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| 10 % – 20 % | 31 | 30 | 89 % | +12.3 % | 79 % | 97 % | 0.84 |
| 20 % – 35 % | 16 | 16 | 87 % | +24.8 % | 60 % | 100 % | 0.60 |
| 35 % – 60 % | 3 | 3 | 100 % | +31.6 % | 67 % | 100 % | 0.81 |

## Nach Volatilität (CV)

| Volatilität (CV) | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0 % – 2 % | 1 | 0 | – | – | – | – | – |
| 2 % – 4 % | 13 | 13 | 100 % | +16.7 % | 92 % | 100 % | 0.66 |
| 4 % – 7 % | 24 | 24 | 92 % | +16.2 % | 79 % | 100 % | 0.89 |
| 7 % – 10 % | 12 | 12 | 70 % | +8.1 % | 30 % | 92 % | 0.68 |

## Nach Tagesvolumen

| Tagesvolumen | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0 – 200 | 18 | 17 | 88 % | +16.2 % | 88 % | 100 % | 0.72 |
| 200 – 1.000 | 27 | 27 | 92 % | +15.4 % | 58 % | 96 % | 0.72 |
| 1.000 – 5.000 | 4 | 4 | 75 % | +7.8 % | 75 % | 100 % | 1.05 |
| 5.000 – 20.000 | 1 | 1 | 100 % | +5.3 % | 100 % | 100 % | 0.73 |

**Lesehilfe:** *profitabel nach 48 h* = Kauf zum geplanten Gebot und Verkauf zum dann günstigsten Angebot − 1 wäre nach Gebühren im Plus gewesen. *Preis gehalten* = günstigstes Angebot höchstens 5 % unter dem geplanten Verkaufspreis. *Gebot überholt* = jemand bot binnen 24 h mehr. *Volumen* < 1 heißt: Die Schätzung war zu optimistisch.

## Filter-Trichter der heutigen Analyse

| Filter | Items | Anteil |
|---|---:|---:|
| kein Kaufgebot oder kein Verkaufsangebot | 3340 | 11.9 % |
| kein Spread nach Über-/Unterbieten | 328 | 1.2 % |
| Kaufpreis unter Minimum | 6056 | 21.6 % |
| ROI unter Minimum | 2421 | 8.6 % |
| ROI über Maximum (Ausreißer) | 6242 | 22.3 % |
| zu wenig Nachfrage im Orderbuch | 5916 | 21.1 % |
| zu wenig Angebot im Orderbuch | 1667 | 6.0 % |
| keine ausreichende Historie | 1410 | 5.0 % |
| Tagesvolumen unter Minimum | 408 | 1.5 % |
| Volatilität zu hoch | 123 | 0.4 % |
| Abwärtstrend | 1 | 0.0 % |
| besteht alle budgetunabhängigen Filter | 97 | 0.3 % |
