# Auswertung – 2026-11-16

Rückblick auf frühere Einkaufslisten anhand der stündlichen Snapshots. Grundlage für das Feintuning der Schwellwerte in `config.yaml` (Phase 5).

Ausgewertet: 12 Listen vom 02.11.2026 bis 14.11.2026.

## Gesamt

| | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| alle | 119 | 111 | 94 % | +16.2 % | 75 % | 91 % | 0.81 |
| Historien-Modus | 109 | 106 | 94 % | +16.1 % | 75 % | 95 % | 0.81 |
| Orderbuch-Modus | 10 | 5 | 100 % | +112.6 % | 80 % | 0 % | – |

Die Aufschlüsselung unten enthält nur Listen aus dem Historien-Modus. Listen aus dem Orderbuch-Modus (ohne Volumenschätzung) enthalten oft illiquide Ausreißer, deren Gebote kaum gefüllt würden, und verzerren sonst die Statistik.

## Nach Ampel

| Ampel | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| grün | 3 | 3 | 100 % | +26.9 % | 100 % | 100 % | 1.08 |
| gelb | 78 | 78 | 96 % | +16.8 % | 78 % | 95 % | 0.75 |
| rot | 28 | 25 | 86 % | +10.9 % | 64 % | 96 % | 0.92 |

## Nach geplanter ROI

| geplanter ROI | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| 10 % – 20 % | 68 | 65 | 93 % | +12.4 % | 79 % | 97 % | 0.90 |
| 20 % – 35 % | 34 | 34 | 94 % | +23.6 % | 73 % | 100 % | 0.59 |
| 35 % – 60 % | 6 | 6 | 100 % | +34.7 % | 50 % | 50 % | 0.84 |
| 60 % – 100 % | 1 | 1 | 100 % | +81.0 % | 100 % | 100 % | 1.07 |

## Nach Volatilität (CV)

| Volatilität (CV) | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0 % – 2 % | 9 | 6 | 100 % | +24.9 % | 100 % | 100 % | 0.54 |
| 2 % – 4 % | 27 | 27 | 100 % | +13.0 % | 84 % | 89 % | 0.79 |
| 4 % – 7 % | 61 | 61 | 95 % | +16.2 % | 77 % | 98 % | 0.82 |
| 7 % – 10 % | 12 | 12 | 70 % | +8.1 % | 30 % | 92 % | 0.68 |

## Nach Tagesvolumen

| Tagesvolumen | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0 – 200 | 46 | 43 | 93 % | +13.9 % | 81 % | 91 % | 0.79 |
| 200 – 1.000 | 54 | 54 | 96 % | +17.2 % | 70 % | 98 % | 0.79 |
| 1.000 – 5.000 | 8 | 8 | 86 % | +9.7 % | 71 % | 100 % | 0.98 |
| 5.000 – 20.000 | 1 | 1 | 100 % | +5.3 % | 100 % | 100 % | 0.73 |

**Lesehilfe:** *profitabel nach 48 h* = Kauf zum geplanten Gebot und Verkauf zum dann günstigsten Angebot − 1 wäre nach Gebühren im Plus gewesen. *Preis gehalten* = günstigstes Angebot höchstens 5 % unter dem geplanten Verkaufspreis. *Gebot überholt* = jemand bot binnen 24 h mehr. *Volumen* < 1 heißt: Die Schätzung war zu optimistisch.

## Filter-Trichter der heutigen Analyse

| Filter | Items | Anteil |
|---|---:|---:|
| kein Kaufgebot oder kein Verkaufsangebot | 3326 | 11.9 % |
| kein Spread nach Über-/Unterbieten | 340 | 1.2 % |
| Kaufpreis unter Minimum | 6088 | 21.7 % |
| ROI unter Minimum | 2403 | 8.6 % |
| ROI über Maximum (Ausreißer) | 6183 | 22.1 % |
| zu wenig Nachfrage im Orderbuch | 5933 | 21.2 % |
| zu wenig Angebot im Orderbuch | 1687 | 6.0 % |
| keine ausreichende Historie | 1396 | 5.0 % |
| Tagesvolumen unter Minimum | 426 | 1.5 % |
| Volatilität zu hoch | 122 | 0.4 % |
| Abwärtstrend | 3 | 0.0 % |
| besteht alle budgetunabhängigen Filter | 102 | 0.4 % |
