// Tabs „Meine Orders“ und „Gewinn“: persönlicher API-Key (nur im Browser), offene Orders,
// fällige Verkäufe und realisierter Gewinn. Persönliche Daten werden nur im Speicher gehalten.

import {
  aggregate,
  analyzeBuyOrders,
  analyzeSellOrders,
  checkPermissions,
  dayKey,
  dueSales,
  isoWeekKey,
  maskKey,
  normalizeKey,
  realizedProfit,
  totalSince,
  validateDelivery,
  validateItems,
  validatePrices,
  validateTokenInfo,
  validateTransactions,
} from "./account.js";
import { $, cell, coins, el, itemCell } from "./dom.js";
import { ApiError, request, requestAllPages, requestByIds } from "./gw2api.js";
import { createKeyStore } from "./keystore.js";

const store = createKeyStore(window);
const MODE_TEXT = { session: "nur für diese Sitzung", local: "auf diesem Gerät gemerkt" };
const state = { key: null, mode: null, info: null, data: null, loading: false };

// --- Hilfen ---------------------------------------------------------------------------------

function errorText(err) {
  return err instanceof ApiError ? err.message : "Unerwarteter Fehler beim Laden der Kontodaten.";
}

function showKeyError(message) {
  $("key-error").textContent = message;
  $("key-error").hidden = !message;
}

function itemOf(id) {
  const it = state.data?.items.get(id);
  if (it) return itemCell(it);
  return el("span", { cls: "name", text: `Item ${id}` });
}

function table(id, headers, rows, emptyText) {
  const tbl = $(id);
  const thead = el("thead", {}, [
    el("tr", {}, headers.map(([label, cls]) => el("th", { cls, text: label }))),
  ]);
  const tbody = el("tbody", {}, rows);
  tbl.replaceChildren(thead, tbody);
  tbl.hidden = rows.length === 0;
  const empty = $(`${id}-empty`);
  empty.textContent = emptyText;
  empty.hidden = rows.length !== 0;
}

function badge(kind, text) {
  return el("span", { cls: `badge badge-${kind}`, text });
}

function signedCoins(copper) {
  const span = coins(copper);
  span.classList.add(copper >= 0 ? "pos" : "neg");
  return span;
}

// --- Key-Verwaltung -------------------------------------------------------------------------

function renderKeyPanel() {
  const active = state.key !== null;
  $("key-form-wrap").hidden = active;
  $("key-active").hidden = !active;
  $("account-content").hidden = !active;
  $("profit-content").hidden = !active;
  if (!active) return;
  $("key-name").textContent = state.info?.name ?? "API-Key";
  $("key-mask").textContent = maskKey(state.key);
  $("key-mode-text").textContent = MODE_TEXT[state.mode] ?? "";
  const extra = state.info ? checkPermissions(state.info.permissions).extra : [];
  $("key-extra").hidden = extra.length === 0;
  $("key-extra").textContent =
    `Dieser Key hat zusätzliche Rechte (${extra.join(", ")}). Empfohlen ist ein eigener Key ` +
    "nur mit „account“ und „tradingpost“.";
}

async function verifyKey(key) {
  const { data } = await request("/v2/tokeninfo", { key });
  const info = validateTokenInfo(data);
  if (!checkPermissions(info.permissions).ok) {
    throw new ApiError("Dem Key fehlt die Berechtigung „tradingpost“.", "auth");
  }
  return info;
}

async function connect(event) {
  event.preventDefault();
  const input = $("api-key");
  const key = normalizeKey(input.value);
  input.value = ""; // Key nicht länger als nötig im DOM halten
  if (key === null) {
    showKeyError("Das sieht nicht wie ein GW2-API-Key aus.");
    return;
  }
  const mode = document.querySelector('input[name="key-mode"]:checked')?.value ?? "session";
  showKeyError("");
  $("key-submit").disabled = true;
  try {
    const info = await verifyKey(key);
    store.save(key, mode);
    Object.assign(state, { key, mode, info, data: null });
    renderKeyPanel();
    await loadAccountData();
  } catch (err) {
    showKeyError(errorText(err));
  } finally {
    $("key-submit").disabled = false;
  }
}

function clearKey() {
  store.clear();
  Object.assign(state, { key: null, mode: null, info: null, data: null });
  $("api-key").value = "";
  showKeyError("");
  for (const id of ["buys", "sells", "due", "weeks", "days"]) $(id).replaceChildren();
  $("profit-summary").replaceChildren();
  renderKeyPanel();
}

// --- Daten laden ----------------------------------------------------------------------------

async function loadAccountData() {
  if (state.key === null || state.loading) return;
  state.loading = true;
  $("account-status").textContent = "Lade Kontodaten …";
  $("key-refresh").disabled = true;
  try {
    if (state.info === null) state.info = await verifyKey(state.key);
    renderKeyPanel();
    const key = state.key;
    const [buys, sells, histBuys, histSells, delivery] = await Promise.all([
      requestAllPages("/v2/commerce/transactions/current/buys", { key }),
      requestAllPages("/v2/commerce/transactions/current/sells", { key }),
      requestAllPages("/v2/commerce/transactions/history/buys", { key }),
      requestAllPages("/v2/commerce/transactions/history/sells", { key }),
      request("/v2/commerce/delivery", { key }).then((r) => r.data),
    ]);
    const d = {
      buys: validateTransactions(buys).items,
      sells: validateTransactions(sells).items,
      histBuys: validateTransactions(histBuys, { completed: true }).items,
      histSells: validateTransactions(histSells, { completed: true }).items,
      delivery: validateDelivery(delivery),
    };
    const ids = [
      ...d.buys.map((t) => t.item_id),
      ...d.sells.map((t) => t.item_id),
      ...d.histSells.map((t) => t.item_id),
      ...d.delivery.items.map((t) => t.id),
    ];
    // Öffentliche Daten – ohne Key.
    const [prices, items] = await Promise.all([
      requestByIds("/v2/commerce/prices", ids),
      requestByIds("/v2/items", ids),
    ]);
    d.prices = validatePrices(prices);
    d.items = validateItems(items);
    d.loadedAt = new Date();
    state.data = d;
    renderOrders();
    renderProfit();
    $("account-status").textContent =
      `Stand: ${d.loadedAt.toLocaleTimeString("de-DE", { timeStyle: "short" })} Uhr`;
  } catch (err) {
    $("account-status").textContent = "";
    showKeyError(errorText(err));
  } finally {
    state.loading = false;
    $("key-refresh").disabled = false;
  }
}

// --- Orders ---------------------------------------------------------------------------------

const STATUS_ORDER = { outbid: 0, undercut: 0, unknown: 1, top: 2, lowest: 2 };

function renderOrders() {
  const d = state.data;
  const buys = analyzeBuyOrders(d.buys, d.prices).sort(
    (a, b) => STATUS_ORDER[a.status] - STATUS_ORDER[b.status] || b.created - a.created,
  );
  table(
    "buys",
    [["Status"], ["Item"], ["Dein Gebot", "num"], ["Menge", "num"], ["Höchstgebot", "num"], ["Seit", "num"]],
    buys.map((o) =>
      el("tr", { cls: o.status === "outbid" ? "alert" : "" }, [
        cell("Status", o.status === "outbid" ? badge("red", "überboten") : o.status === "top" ? badge("green", "Höchstgebot") : badge("yellow", "unbekannt")),
        cell("Item", itemOf(o.item_id), "item-cell"),
        cell("Dein Gebot", coins(o.price), "num"),
        cell("Menge", String(o.quantity), "num"),
        cell("Höchstgebot", o.best ? coins(o.best) : "–", "num"),
        cell("Seit", o.created.toLocaleDateString("de-DE"), "num"),
      ]),
    ),
    "Keine offenen Kaufgebote.",
  );

  const sells = analyzeSellOrders(d.sells, d.prices).sort(
    (a, b) => STATUS_ORDER[a.status] - STATUS_ORDER[b.status] || b.created - a.created,
  );
  table(
    "sells",
    [["Status"], ["Item"], ["Dein Preis", "num"], ["Menge", "num"], ["Günstigstes Angebot", "num"], ["Seit", "num"]],
    sells.map((o) =>
      el("tr", { cls: o.status === "undercut" ? "alert" : "" }, [
        cell("Status", o.status === "undercut" ? badge("red", "unterboten") : o.status === "lowest" ? badge("green", "günstigstes") : badge("yellow", "unbekannt")),
        cell("Item", itemOf(o.item_id), "item-cell"),
        cell("Dein Preis", coins(o.price), "num"),
        cell("Menge", String(o.quantity), "num"),
        cell("Günstigstes Angebot", o.best ? coins(o.best) : "–", "num"),
        cell("Seit", o.created.toLocaleDateString("de-DE"), "num"),
      ]),
    ),
    "Keine offenen Verkaufsangebote.",
  );

  const due = dueSales(d.delivery, d.prices, d.histBuys);
  table(
    "due",
    [["Item"], ["Menge", "num"], ["Einkauf Ø", "num"], ["Verkaufen zu", "num"], ["Gewinn/Stück", "num"]],
    due.map((x) =>
      el("tr", {}, [
        cell("Item", itemOf(x.item_id), "item-cell"),
        cell("Menge", String(x.count), "num"),
        cell("Einkauf Ø", x.cost === null ? "–" : coins(Math.round(x.cost)), "num"),
        cell("Verkaufen zu", x.suggested === null ? "–" : coins(x.suggested), "num"),
        cell("Gewinn/Stück", x.profitPerUnit === null ? "–" : signedCoins(x.profitPerUnit), "num"),
      ]),
    ),
    "Keine Items in der Abholbox.",
  );
  const coinsBox = $("delivery-coins");
  coinsBox.replaceChildren();
  if (d.delivery.coins > 0) {
    coinsBox.append("Zum Abholen bereit: ", coins(d.delivery.coins));
  }
  coinsBox.hidden = d.delivery.coins === 0;
}

// --- Gewinn ---------------------------------------------------------------------------------

function summaryCard(label, copper, sub) {
  return el("div", { cls: "stat" }, [
    el("div", { cls: "stat-label", text: label }),
    el("div", { cls: "stat-value" }, [signedCoins(copper)]),
    el("div", { cls: "stat-sub muted", text: sub }),
  ]);
}

function profitRows(rows, label) {
  return rows.map((r) =>
    el("tr", {}, [
      cell(label, r.key),
      cell("Stück", r.quantity.toLocaleString("de-DE"), "num"),
      cell("Erlös netto", coins(r.net), "num"),
      cell("Einkauf", coins(r.cost), "num"),
      cell("Gewinn", signedCoins(r.profit), "num profit"),
    ]),
  );
}

function renderProfit() {
  const d = state.data;
  const { sales, unmatchedQty } = realizedProfit(d.histBuys, d.histSells);
  const now = d.loadedAt;
  const sums = [
    ["Letzte 7 Tage", totalSince(sales, now, 7)],
    ["Letzte 30 Tage", totalSince(sales, now, 30)],
    ["Letzte 90 Tage", totalSince(sales, now, 90)],
  ];
  $("profit-summary").replaceChildren(
    ...sums.map(([label, s]) =>
      summaryCard(label, s.profit, `${s.quantity.toLocaleString("de-DE")} Stück verkauft`),
    ),
  );
  const head = (first) => [[first], ["Stück", "num"], ["Erlös netto", "num"], ["Einkauf", "num"], ["Gewinn", "num"]];
  table("weeks", head("Woche"), profitRows(aggregate(sales, isoWeekKey).slice(0, 13), "Woche"),
    "Noch keine abgeschlossenen Flips in den letzten 90 Tagen.");
  table("days", head("Tag"), profitRows(aggregate(sales, dayKey).slice(0, 14), "Tag"),
    "Noch keine abgeschlossenen Flips in den letzten 90 Tagen.");
  $("profit-note").textContent =
    "Gewinn = Verkaufserlös nach 5 % Einstellgebühr und 10 % Steuer minus Einkaufspreis " +
    "(FIFO-Zuordnung, Daten der letzten 90 Tage laut GW2-API)." +
    (unmatchedQty > 0
      ? ` ${unmatchedQty.toLocaleString("de-DE")} verkaufte Stück ohne passenden Einkauf ` +
        "(z. B. Drops oder ältere Käufe) sind nicht eingerechnet."
      : "");
}

// --- Öffentliche Schnittstelle --------------------------------------------------------------

export function initAccount() {
  $("key-form").addEventListener("submit", connect);
  $("key-clear").addEventListener("click", clearKey);
  $("key-refresh").addEventListener("click", () => loadAccountData());
  const saved = store.load();
  if (saved) {
    const key = normalizeKey(saved.key);
    if (key) Object.assign(state, { key, mode: saved.mode });
    else store.clear();
  }
  renderKeyPanel();
}

/** Wird beim Wechsel auf „Meine Orders“ oder „Gewinn“ aufgerufen. */
export function onAccountTabShown() {
  if (state.key !== null && state.data === null && !state.loading) loadAccountData();
}
