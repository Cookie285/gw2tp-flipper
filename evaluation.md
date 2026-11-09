# Auswertung – 2026-11-09

Rückblick auf frühere Einkaufslisten anhand der stündlichen Snapshots. Grundlage für das Feintuning der Schwellwerte in `config.yaml` (Phase 5).

Ausgewertet: 5 Listen vom 02.11.2026 bis 07.11.2026.

## Gesamt

| | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| alle | 50 | 45 | 95 % | +17.5 % | 78 % | 87 % | 0.75 |
| Historien-Modus | 40 | 40 | 94 % | +14.6 % | 77 % | 98 % | 0.75 |
| Orderbuch-Modus | 10 | 5 | 100 % | +112.6 % | 80 % | 0 % | – |

Die Aufschlüsselung unten enthält nur Listen aus dem Historien-Modus. Listen aus dem Orderbuch-Modus (ohne Volumenschätzung) enthalten oft illiquide Ausreißer, deren Gebote kaum gefüllt würden, und verzerren sonst die Statistik.

## Nach Ampel

| Ampel | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| gelb | 20 | 20 | 100 % | +21.0 % | 89 % | 100 % | 0.74 |
| rot | 20 | 20 | 88 % | +10.9 % | 62 % | 95 % | 0.79 |

## Nach geplanter ROI

| geplanter ROI | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| 10 % – 20 % | 25 | 25 | 95 % | +12.3 % | 81 % | 96 % | 0.81 |
| 20 % – 35 % | 13 | 13 | 92 % | +26.2 % | 67 % | 100 % | 0.65 |
| 35 % – 60 % | 2 | 2 | 100 % | +34.8 % | 100 % | 100 % | 0.63 |

## Nach Volatilität (CV)

| Volatilität (CV) | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2 % – 4 % | 12 | 12 | 100 % | +14.6 % | 91 % | 100 % | 0.69 |
| 4 % – 7 % | 16 | 16 | 100 % | +18.2 % | 93 % | 100 % | 0.86 |
| 7 % – 10 % | 12 | 12 | 78 % | +9.8 % | 33 % | 92 % | 0.68 |

## Nach Tagesvolumen

| Tagesvolumen | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten | Gebot überholt (24 h) | Volumen beobachtet/geschätzt |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0 – 200 | 12 | 12 | 100 % | +18.2 % | 100 % | 100 % | 0.71 |
| 200 – 1.000 | 23 | 23 | 89 % | +13.6 % | 58 % | 96 % | 0.70 |
| 1.000 – 5.000 | 4 | 4 | 100 % | +9.7 % | 100 % | 100 % | 1.05 |
| 5.000 – 20.000 | 1 | 1 | 100 % | +5.3 % | 100 % | 100 % | 0.73 |

**Lesehilfe:** *profitabel nach 48 h* = Kauf zum geplanten Gebot und Verkauf zum dann günstigsten Angebot − 1 wäre nach Gebühren im Plus gewesen. *Preis gehalten* = günstigstes Angebot höchstens 5 % unter dem geplanten Verkaufspreis. *Gebot überholt* = jemand bot binnen 24 h mehr. *Volumen* < 1 heißt: Die Schätzung war zu optimistisch.

## Filter-Trichter der heutigen Analyse

| Filter | Items | Anteil |
|---|---:|---:|
| kein Kaufgebot oder kein Verkaufsangebot | 3319 | 11.9 % |
| kein Spread nach Über-/Unterbieten | 336 | 1.2 % |
| Kaufpreis unter Minimum | 6074 | 21.7 % |
| ROI unter Minimum | 2395 | 8.6 % |
| ROI über Maximum (Ausreißer) | 6248 | 22.3 % |
| zu wenig Nachfrage im Orderbuch | 5934 | 21.2 % |
| zu wenig Angebot im Orderbuch | 1681 | 6.0 % |
| keine ausreichende Historie | 1381 | 4.9 % |
| Tagesvolumen unter Minimum | 384 | 1.4 % |
| Volatilität zu hoch | 137 | 0.5 % |
| Abwärtstrend | 2 | 0.0 % |
| besteht alle budgetunabhängigen Filter | 108 | 0.4 % |
