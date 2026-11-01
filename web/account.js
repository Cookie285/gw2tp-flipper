// Kontodaten auswerten (ohne DOM): Validierung der API-Antworten, Überbietungs-Warnungen,
// fällige Verkäufe und realisierter Gewinn (FIFO). Alle Beträge in Kupfer.

import { netProceeds, totalFees } from "./fees.js";
import { CHAT_RE, ICON_RE, WORD_RE, cleanName } from "./plan.js";

// Format eines GW2-API-Keys (z. B. 8-4-4-4-20-4-4-4-12 Hex-Zeichen).
export const KEY_RE =
  /^[0-9A-F]{8}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{20}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{12}$/;
export const RECOMMENDED_PERMISSIONS = ["account", "tradingpost"];
const TIME_RE = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})$/;
const MAX_PRICE = 10_000_000_000;
const MAX_QTY = 1_000_000;
const MAX_RECORDS = 5000;

const isInt = (v, min, max) => Number.isSafeInteger(v) && v >= min && v <= max;

/** Eingabe säubern; ``null``, wenn es kein gültiger Key ist. */
export function normalizeKey(input) {
  const key = String(input ?? "").trim().toUpperCase();
  return KEY_RE.test(key) ? key : null;
}

/** Nur die letzten 4 Zeichen anzeigen. */
export const maskKey = (key) => `…${key.slice(-4)}`;

export function validateTokenInfo(raw) {
  if (!raw || typeof raw !== "object" || !Array.isArray(raw.permissions)) {
    throw new Error("Unerwartete Antwort von /v2/tokeninfo");
  }
  const permissions = raw.permissions.filter((p) => typeof p === "string" && WORD_RE.test(p));
  return { name: cleanName(raw.name) ?? "API-Key", permissions };
}

/** Prüft die Rechte: ``tradingpost`` ist Pflicht, alles außer account/tradingpost ist zu viel. */
export function checkPermissions(permissions) {
  return {
    ok: permissions.includes("tradingpost"),
    extra: permissions.filter((p) => !RECOMMENDED_PERMISSIONS.includes(p)).sort(),
  };
}

function parseTime(v) {
  if (typeof v !== "string" || !TIME_RE.test(v)) return null;
  const d = new Date(v);
  return Number.isNaN(d.getTime()) ? null : d;
}

/** Transaktionen prüfen; ``completed`` verlangt das Feld ``purchased``. */
export function validateTransactions(list, { completed = false } = {}) {
  if (!Array.isArray(list)) return { items: [], rejected: 0 };
  const items = [];
  let rejected = 0;
  for (const t of list.slice(0, MAX_RECORDS)) {
    const created = parseTime(t?.created);
    const purchased = completed ? parseTime(t?.purchased) : null;
    if (
      !t ||
      !isInt(t.id, 1, Number.MAX_SAFE_INTEGER) ||
      !isInt(t.item_id, 1, 10_000_000) ||
      !isInt(t.price, 1, MAX_PRICE) ||
      !isInt(t.quantity, 1, MAX_QTY) ||
      created === null ||
      (completed && purchased === null)
    ) {
      rejected += 1;
      continue;
    }
    items.push({
      id: t.id,
      item_id: t.item_id,
      price: t.price,
      quantity: t.quantity,
      created,
      purchased,
    });
  }
  return { items, rejected: rejected + Math.max(0, list.length - MAX_RECORDS) };
}

/** Preise → Map(id → { bid, ask }) (0 = keine Gebote/Angebote). */
export function validatePrices(list) {
  const out = new Map();
  if (!Array.isArray(list)) return out;
  for (const p of list) {
    const bid = p?.buys?.unit_price;
    const ask = p?.sells?.unit_price;
    if (isInt(p?.id, 1, 10_000_000) && isInt(bid, 0, MAX_PRICE) && isInt(ask, 0, MAX_PRICE)) {
      out.set(p.id, { bid, ask });
    }
  }
  return out;
}

/** Item-Details → Map(id → { name, icon, chat_link, rarity }). */
export function validateItems(list) {
  const out = new Map();
  if (!Array.isArray(list)) return out;
  for (const it of list) {
    const name = cleanName(it?.name);
    const icon = typeof it?.icon === "string" && ICON_RE.test(it.icon) ? it.icon : null;
    const chat = typeof it?.chat_link === "string" && CHAT_RE.test(it.chat_link) ? it.chat_link : null;
    const rarity = typeof it?.rarity === "string" && WORD_RE.test(it.rarity) ? it.rarity : null;
    if (isInt(it?.id, 1, 10_000_000) && name !== null && chat !== null) {
      out.set(it.id, { name, icon, chat_link: chat, rarity });
    }
  }
  return out;
}

/** Abholbox: ``{ coins, items: [{ id, count }] }``. */
export function validateDelivery(raw) {
  const coins = isInt(raw?.coins, 0, MAX_PRICE * 100) ? raw.coins : 0;
  const items = [];
  if (Array.isArray(raw?.items)) {
    for (const it of raw.items) {
      if (isInt(it?.id, 1, 10_000_000) && isInt(it?.count, 1, MAX_QTY)) {
        items.push({ id: it.id, count: it.count });
      }
    }
  }
  return { coins, items };
}

// --- Offene Orders --------------------------------------------------------------------------

/** Kaufgebote: "outbid" = jemand bietet mehr, "top" = Höchstgebot (oder gleichauf). */
export function analyzeBuyOrders(orders, prices) {
  return orders.map((o) => {
    const p = prices.get(o.item_id);
    let status = "unknown";
    if (p && p.bid > 0) status = p.bid > o.price ? "outbid" : "top";
    return { ...o, best: p ? p.bid : null, status };
  });
}

/** Verkaufsangebote: "undercut" = jemand verkauft billiger, "lowest" = günstigstes Angebot. */
export function analyzeSellOrders(orders, prices) {
  return orders.map((o) => {
    const p = prices.get(o.item_id);
    let status = "unknown";
    if (p && p.ask > 0) status = p.ask < o.price ? "undercut" : "lowest";
    return { ...o, best: p ? p.ask : null, status };
  });
}

/** Durchschnittlicher Einkaufspreis der jüngsten Käufe, die ``count`` Stück abdecken. */
function recentCostBasis(buys, itemId, count) {
  const lots = buys
    .filter((b) => b.item_id === itemId)
    .sort((a, b) => b.purchased - a.purchased);
  let need = count;
  let qty = 0;
  let cost = 0;
  for (const b of lots) {
    if (need <= 0) break;
    const take = Math.min(need, b.quantity);
    qty += take;
    cost += take * b.price;
    need -= take;
  }
  return qty > 0 ? cost / qty : null;
}

/**
 * Fällige Verkäufe: Items in der Abholbox mit Preisvorschlag (niedrigstes Angebot − 1) und
 * erwartetem Gewinn gegenüber dem Einkaufspreis aus der Historie.
 */
export function dueSales(delivery, prices, historyBuys) {
  return delivery.items.map((it) => {
    const p = prices.get(it.id);
    const suggested = p && p.ask > 1 ? p.ask - 1 : null;
    const cost = recentCostBasis(historyBuys, it.id, it.count);
    let profitPerUnit = null;
    if (suggested !== null && cost !== null) {
      profitPerUnit = Math.round(suggested - totalFees(suggested) - cost);
    }
    return { item_id: it.id, count: it.count, suggested, cost, profitPerUnit };
  });
}

// --- Realisierter Gewinn ----------------------------------------------------------------------

/**
 * Verkäufe per FIFO den Käufen zuordnen. Ein Verkauf kann nur Käufe nutzen, die vor ihm
 * abgeschlossen wurden. Nicht zuordenbare Mengen (z. B. Käufe älter als 90 Tage, Drops) fließen
 * nicht in den Gewinn ein, sondern werden als ``unmatchedQty`` gezählt.
 */
export function realizedProfit(historyBuys, historySells) {
  const lotsByItem = new Map();
  for (const b of [...historyBuys].sort((a, b) => a.purchased - b.purchased || a.id - b.id)) {
    if (!lotsByItem.has(b.item_id)) lotsByItem.set(b.item_id, []);
    lotsByItem.get(b.item_id).push({ purchased: b.purchased, price: b.price, left: b.quantity });
  }
  const sales = [];
  let unmatchedQty = 0;
  for (const s of [...historySells].sort((a, b) => a.purchased - b.purchased || a.id - b.id)) {
    const lots = lotsByItem.get(s.item_id) ?? [];
    let need = s.quantity;
    let cost = 0;
    for (const lot of lots) {
      if (need === 0) break;
      if (lot.left === 0 || lot.purchased > s.purchased) continue;
      const take = Math.min(need, lot.left);
      lot.left -= take;
      need -= take;
      cost += take * lot.price;
    }
    const matched = s.quantity - need;
    unmatchedQty += need;
    if (matched === 0) continue;
    const net = Math.round((netProceeds(s.price, s.quantity) * matched) / s.quantity);
    sales.push({
      item_id: s.item_id,
      quantity: matched,
      net,
      cost,
      profit: net - cost,
      purchased: s.purchased,
    });
  }
  return { sales, unmatchedQty };
}

const pad = (n) => String(n).padStart(2, "0");

/** Lokales Datum YYYY-MM-DD. */
export function dayKey(date) {
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
}

/** ISO-Kalenderwoche „YYYY-Www“ (lokale Zeit, Woche beginnt Montag). */
export function isoWeekKey(date) {
  const d = new Date(date.getFullYear(), date.getMonth(), date.getDate());
  const weekday = (d.getDay() + 6) % 7; // Montag = 0
  d.setDate(d.getDate() - weekday + 3); // Donnerstag derselben Woche
  const year = d.getFullYear();
  const jan4 = new Date(year, 0, 4);
  const week = 1 + Math.round(((d - jan4) / 86400000 - 3 + ((jan4.getDay() + 6) % 7)) / 7);
  return `${year}-W${pad(week)}`;
}

/** Verkäufe nach Schlüssel (Tag/Woche) summieren, neueste zuerst. */
export function aggregate(sales, keyFn) {
  const rows = new Map();
  for (const s of sales) {
    const key = keyFn(s.purchased);
    const r = rows.get(key) ?? { key, quantity: 0, net: 0, cost: 0, profit: 0, sales: 0 };
    r.quantity += s.quantity;
    r.net += s.net;
    r.cost += s.cost;
    r.profit += s.profit;
    r.sales += 1;
    rows.set(key, r);
  }
  return [...rows.values()].sort((a, b) => (a.key < b.key ? 1 : a.key > b.key ? -1 : 0));
}

/** Summen für die letzten ``days`` Tage relativ zu ``now``. */
export function totalSince(sales, now, days) {
  const from = now.getTime() - days * 86400000;
  return sales
    .filter((s) => s.purchased.getTime() >= from)
    .reduce(
      (t, s) => ({ profit: t.profit + s.profit, net: t.net + s.net, quantity: t.quantity + s.quantity }),
      { profit: 0, net: 0, quantity: 0 },
    );
}
