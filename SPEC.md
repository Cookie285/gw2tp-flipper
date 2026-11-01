# GW2 Flip-Einkaufsliste – Projektspezifikation für Claude Code

## Ziel

Ein Tool, das täglich automatisch eine kurze, risikoarme **Einkaufsliste** für Handelsposten-Flips in Guild Wars 2 erzeugt. Kein automatisches Kaufen oder Verkaufen (die API ist read-only und Bots verstoßen gegen die Nutzungsbedingungen). Der Nutzer arbeitet die Liste in etwa 10 Minuten manuell im Spiel ab.

**Rahmenbedingung:** keine eigene Infrastruktur. Alles läuft auf GitHub (Actions + Pages).

## Architektur (nur GitHub)

- **GitHub Actions (cron):** ruft stündlich die GW2-API ab und speichert Preis-Snapshots.
- **Datenspeicher im Repo:** komprimierte JSON- oder SQLite-Datei in einem eigenen `data`-Branch (hält die `main`-History sauber).
- **Täglicher Analyse-Job:** berechnet Kennzahlen und schreibt `shopping-list.json`.
- **GitHub Pages:** statisches Dashboard (HTML + JS, z. B. Vite oder reines HTML mit Alpine.js) liest `shopping-list.json`.
- **Persönliche Daten (optional):** Das Dashboard fragt `/v2/commerce/transactions` **im Browser** mit einem API-Key ab, der nur in `localStorage` liegt. So landen keine persönlichen Daten im öffentlichen Repo und es braucht kein Secret auf GitHub.

Hinweis: Pages für private Repos erfordert einen kostenpflichtigen GitHub-Plan. Marktdaten sind öffentlich, daher ist ein öffentliches Repo unproblematisch.

## GW2-API-Endpunkte

- `GET /v2/commerce/prices?ids=...` – bester Kauf-/Verkaufspreis und Menge (max. 200 IDs pro Request)
- `GET /v2/commerce/listings?ids=...` – Orderbuch-Tiefe
- `GET /v2/items?ids=...` – Namen, Icons, Gebundenheit (Account-/Seelengebunden ausschließen)
- `GET /v2/commerce/transactions/current/buys|sells` – eigene offene Orders (API-Key mit Scope `tradingpost`)
- `GET /v2/commerce/transactions/history/buys|sells` – abgeschlossene Trades für Gewinntracking

Rate-Limit beachten (ca. 300 Requests/Minute, Burst). Requests bündeln und bei 429 mit Backoff wiederholen.

## Item-Universum

Nicht alle \~27.000 handelbaren Items stündlich speichern. Vorschlag:

1. Einmal täglich alle Preise abrufen und nach Mindestvolumen vorfiltern.
2. Stündlich nur die \~500–1.000 liquidesten Kandidaten speichern.
3. Optional eine Whitelist-Kategorie: Crafting-Materialien, Ektoplasma, Veredelungsmaterialien, Legendary-Zutaten.

## Kennzahlen und Filter

Gebühren: 5 % Einstellgebühr + 10 % Verkaufssteuer = 15 %.

- **Kaufpreis:** höchstes Kaufgebot + 1 Kupfer
- **Verkaufspreis:** niedrigstes Verkaufsangebot − 1 Kupfer
- **Netto-Gewinn pro Stück:** Verkaufspreis × 0,85 − Kaufpreis
- **ROI:** Netto-Gewinn ÷ Kaufpreis

Standard-Filter (konfigurierbar in `config.yaml`):

- ROI ≥ 10 %
- Netto-Gewinn ≥ 10 Silber pro Stück **oder** Gesamtgewinn ≥ 1 Gold pro Position
- Tagesvolumen (geschätzt aus Mengenänderungen der Snapshots) ≥ 10× geplante Stückzahl
- Preis-Volatilität über 7 Tage gering (Variationskoeffizient unter Schwellwert)
- Kein starker Abwärtstrend (Steigung des 7-Tage-Medians nicht deutlich negativ)
- Kaufpreis ≥ 1 Silber (Kleinstbeträge ausschließen)

## Positionsgröße und Risiko

- Budget wird im Dashboard eingegeben (z. B. 200 Gold).
- Maximal 10 % des Budgets pro Item.
- Stückzahl = min(Budgetanteil ÷ Kaufpreis, 5 % des Tagesvolumens, 250).
- Maximal 10 Positionen pro Tag.

## Ranking

Score = erwarteter Tagesgewinn × Liquiditätsfaktor × Stabilitätsfaktor. Top 5–10 Items kommen auf die Liste.

## Dashboard

**Einkaufsliste (Hauptansicht):** Icon, Name, Kaufgebot, Stückzahl, geplanter Verkaufspreis, erwarteter Gewinn, Ampel für das Risiko. Ein Klick kopiert den Chatcode des Items, damit es im Spiel schnell gefunden wird.

**Meine Orders (optional, mit API-Key):** offene Kaufgebote, Warnung bei Überbietung, fällige Verkäufe.

**Gewinn-Tracking:** realisierter Gewinn pro Tag und Woche aus der Transaktionshistorie.

## Repo-Struktur

- `.github/workflows/snapshot.yml` – stündlicher Preis-Snapshot
- `.github/workflows/analyze.yml` – tägliche Analyse und Pages-Deploy
- `src/fetch.py` – API-Client mit Batching und Backoff
- `src/analyze.py` – Kennzahlen, Filter, Ranking
- `config.yaml` – Schwellwerte
- `web/` – statisches Dashboard
- `tests/` – Unit-Tests für Gebühren- und Filterlogik

## Umsetzungsphasen

1. **MVP:** täglicher Job nur mit aktuellen Preisen, einfache ROI-Liste als Markdown im Repo.
2. **Historie:** stündliche Snapshots, Volumen- und Trendschätzung.
3. **Dashboard:** GitHub Pages mit Einkaufsliste.
4. **Persönlich:** API-Key im Browser, offene Orders und Gewinn-Tracking.
5. **Feintuning:** Schwellwerte anhand der echten Ergebnisse anpassen.

## Hinweise

- Cron-Workflows in GitHub Actions können sich verzögern und werden in inaktiven Repos nach 60 Tagen pausiert.
- Datengröße im Blick behalten: alte Snapshots zu Tageswerten verdichten.
- Kein Scraping fremder Seiten, nur die offizielle API.
