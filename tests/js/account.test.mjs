// Tests für Phase 4: Gebühren, Key-Speicher, API-Client (Key-Handling) und Kontoauswertung.
import assert from "node:assert/strict";
import { test } from "node:test";

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
} from "../../web/account.js";
import { exchangeFee, listingFee, netProceeds, totalFees } from "../../web/fees.js";
import { ApiError, buildUrl, request, requestAllPages, requestByIds } from "../../web/gw2api.js";
import { STORAGE_KEY, createKeyStore } from "../../web/keystore.js";

const KEY = "01234567-89AB-CDEF-0123-456789ABCDEF01234567-89AB-CDEF-0123-456789ABCDEF";

// --- Gebühren (gleiche Tabelle wie tests/test_fees.py) ----------------------------------------

test("Gebühren wie fees.py", () => {
  for (const [price, listing, exchange] of [
    [1, 1, 1], [10, 1, 1], [29, 1, 3], [30, 2, 3], [100, 5, 10], [1500, 75, 150],
    [10_000_000, 500_000, 1_000_000],
  ]) {
    assert.equal(listingFee(price), listing, `listing ${price}`);
    assert.equal(exchangeFee(price), exchange, `exchange ${price}`);
    assert.equal(totalFees(price), listing + exchange);
  }
  assert.equal(totalFees(0), 0);
  assert.equal(netProceeds(1500, 1), 1275);
  assert.equal(netProceeds(1000, 3), 3000 - 150 - 300);
});

// --- Key-Format und Speicher ------------------------------------------------------------------

test("Key-Format", () => {
  assert.equal(normalizeKey(` ${KEY.toLowerCase()} `), KEY);
  for (const bad of ["", "abc", KEY.slice(1), `${KEY}X`, KEY.replace("-", "_"), null, undefined]) {
    assert.equal(normalizeKey(bad), null);
  }
  assert.equal(maskKey(KEY), "…CDEF");
});

function fakeStorage() {
  const m = new Map();
  return {
    getItem: (k) => (m.has(k) ? m.get(k) : null),
    setItem: (k, v) => m.set(k, String(v)),
    removeItem: (k) => m.delete(k),
    dump: () => Object.fromEntries(m),
  };
}

test("Key-Speicher: Sitzung, Merken, Löschen", () => {
  const win = { sessionStorage: fakeStorage(), localStorage: fakeStorage() };
  const store = createKeyStore(win);
  assert.equal(store.load(), null);
  store.save(KEY, "session");
  assert.deepEqual(store.load(), { key: KEY, mode: "session" });
  assert.deepEqual(win.localStorage.dump(), {});
  store.save(KEY, "local");
  assert.deepEqual(store.load(), { key: KEY, mode: "local" });
  assert.deepEqual(win.sessionStorage.dump(), {}); // Wechsel räumt den anderen Speicher
  store.clear();
  assert.equal(store.load(), null);
  assert.deepEqual(win.localStorage.dump(), {});
  assert.throws(() => store.save(KEY, "cookie"));
  assert.equal(STORAGE_KEY, "gw2tp.apiKey");
});

test("Key-Speicher übersteht blockierten Speicher", () => {
  const win = {};
  Object.defineProperty(win, "localStorage", { get() { throw new Error("blocked"); } });
  win.sessionStorage = fakeStorage();
  const store = createKeyStore(win);
  store.save(KEY, "session");
  assert.equal(store.load().key, KEY);
  assert.throws(() => store.save(KEY, "local"), /nicht verfügbar/);
  store.clear();
});

// --- API-Client -------------------------------------------------------------------------------

function fakeFetch(handler) {
  const calls = [];
  const fn = async (url, init) => {
    calls.push({ url, init });
    const r = await handler(url, init, calls.length);
    if (r instanceof Error) throw r;
    const { status = 200, body = [], headers = {} } = r;
    return {
      status,
      ok: status >= 200 && status < 300,
      headers: { get: (h) => headers[h] ?? null },
      text: async () => (typeof body === "string" ? body : JSON.stringify(body)),
    };
  };
  fn.calls = calls;
  return fn;
}

const noSleep = async () => {};

test("Key nur im Authorization-Header, nie in der URL", async () => {
  const f = fakeFetch(() => ({ body: { name: "x", permissions: ["account", "tradingpost"] } }));
  await request("/v2/tokeninfo", { key: KEY, fetchImpl: f, sleep: noSleep });
  const { url, init } = f.calls[0];
  assert.equal(url, "https://api.guildwars2.com/v2/tokeninfo");
  assert.ok(!url.includes(KEY));
  assert.ok(!url.includes("access_token"));
  assert.equal(init.headers.Authorization, `Bearer ${KEY}`);
  assert.equal(init.credentials, "omit");
  assert.equal(init.referrerPolicy, "no-referrer");
  assert.equal(init.redirect, "error");
  assert.equal(init.method, "GET");
});

test("öffentliche Abfragen senden nie einen Key", async () => {
  const f = fakeFetch(() => ({ body: [{ id: 1 }] }));
  await requestByIds("/v2/commerce/prices", [1, 2, 2, 3], { key: KEY, fetchImpl: f, sleep: noSleep });
  for (const c of f.calls) {
    assert.equal(c.init.headers.Authorization, undefined);
    assert.ok(!c.url.includes(KEY));
  }
  assert.equal(f.calls[0].url, "https://api.guildwars2.com/v2/commerce/prices?ids=1%2C2%2C3");
});

test("IDs in Blöcken zu 200", async () => {
  const f = fakeFetch(() => ({ body: [] }));
  const ids = Array.from({ length: 450 }, (_, i) => i + 1);
  await requestByIds("/v2/items", ids, { fetchImpl: f, sleep: noSleep });
  assert.equal(f.calls.length, 3);
});

test("nur api.guildwars2.com, nur erlaubte Pfade und Parameter", () => {
  for (const path of ["/v2/../v1", "//evil.example/v2", "/v2/items?x=1", "https://evil.example/v2", "/v2/Items"]) {
    assert.throws(() => buildUrl(path), ApiError, path);
  }
  assert.throws(() => buildUrl("/v2/items", { access_token: KEY }), ApiError);
  assert.throws(() => buildUrl("/v2/items", { "x&y": 1 }), ApiError);
  assert.equal(buildUrl("/v2/items", { ids: "1,2" }), "https://api.guildwars2.com/v2/items?ids=1%2C2");
});

test("Paginierung über X-Page-Total", async () => {
  const f = fakeFetch((url) => {
    const page = Number(new URL(url).searchParams.get("page"));
    return { body: Array.from({ length: page < 2 ? 200 : 5 }, (_, i) => ({ i })), headers: { "X-Page-Total": "3" } };
  });
  const all = await requestAllPages("/v2/commerce/transactions/history/buys", { key: KEY, fetchImpl: f, sleep: noSleep });
  assert.equal(all.length, 405);
  assert.equal(f.calls.length, 3);
  assert.ok(f.calls.every((c) => !c.url.includes(KEY)));
});

test("Paginierung ist begrenzt", async () => {
  const f = fakeFetch(() => ({ body: Array.from({ length: 200 }, () => ({})), headers: { "X-Page-Total": "999" } }));
  await requestAllPages("/v2/commerce/transactions/history/buys", { key: KEY, fetchImpl: f, sleep: noSleep, maxPages: 4 });
  assert.equal(f.calls.length, 4);
});

test("leere Historie (404 auf Seite 0) ist kein Fehler", async () => {
  const f = fakeFetch(() => ({ status: 404, body: { text: "page out of range" } }));
  assert.deepEqual(await requestAllPages("/v2/commerce/transactions/history/sells", { key: KEY, fetchImpl: f, sleep: noSleep }), []);
});

test("Wiederholung bei 429/5xx, dann Erfolg", async () => {
  const sleeps = [];
  const f = fakeFetch((url, init, n) => (n < 3 ? { status: n === 1 ? 429 : 503, headers: { "Retry-After": "2" } } : { body: [1] }));
  const r = await request("/v2/commerce/prices", { fetchImpl: f, sleep: async (ms) => sleeps.push(ms) });
  assert.deepEqual(r.data, [1]);
  assert.deepEqual(sleeps, [2000, 2000]);
});

test("Fehlermeldungen enthalten weder Key noch URL", async () => {
  for (const [handler, kind] of [
    [() => ({ status: 401 }), "auth"],
    [() => ({ status: 400 }), "api"],
    [() => new TypeError("Failed to fetch"), "network"],
    [() => ({ body: "<html>" }), "api"],
  ]) {
    const f = fakeFetch(handler);
    await assert.rejects(
      request("/v2/tokeninfo", { key: KEY, fetchImpl: f, sleep: noSleep, retries: 0 }),
      (err) => err instanceof ApiError && err.kind === kind && !err.message.includes(KEY) && !err.message.includes("http"),
    );
  }
});

test("ungültiger Key wird gar nicht erst gesendet", async () => {
  const f = fakeFetch(() => ({ body: [] }));
  await assert.rejects(request("/v2/tokeninfo", { key: "", fetchImpl: f }), ApiError);
  assert.equal(f.calls.length, 0);
});

// --- Validierung --------------------------------------------------------------------------------

test("tokeninfo und Rechte", () => {
  const info = validateTokenInfo({ name: "Flips", permissions: ["account", "tradingpost", "<x>", 5] });
  assert.deepEqual(info.permissions, ["account", "tradingpost"]);
  assert.deepEqual(checkPermissions(["account", "tradingpost"]), { ok: true, extra: [] });
  assert.deepEqual(checkPermissions(["account", "wallet", "tradingpost", "inventories"]), { ok: true, extra: ["inventories", "wallet"] });
  assert.equal(checkPermissions(["account"]).ok, false);
  assert.throws(() => validateTokenInfo({ name: "x" }));
});

test("Transaktionen: ungültige werden verworfen", () => {
  const ok = { id: 1, item_id: 19721, price: 2000, quantity: 5, created: "2026-11-01T10:00:00+00:00", purchased: "2026-11-01T11:00:00+00:00" };
  const { items, rejected } = validateTransactions(
    [ok, { ...ok, price: "1" }, { ...ok, quantity: 0 }, { ...ok, created: "gestern" }, null, { ...ok, item_id: -1 }],
    { completed: true },
  );
  assert.equal(items.length, 1);
  assert.equal(rejected, 5);
  assert.ok(items[0].purchased instanceof Date);
  const { rejected: r2 } = validateTransactions([{ ...ok, purchased: undefined }], { completed: true });
  assert.equal(r2, 1);
  assert.equal(validateTransactions([{ ...ok, purchased: undefined }]).items.length, 1);
});

test("Items, Preise, Abholbox", () => {
  const items = validateItems([
    { id: 1, name: "Ekto", icon: "https://render.guildwars2.com/file/A/1.png", chat_link: "[&AgGpTAAA]", rarity: "Exotic" },
    { id: 2, name: "Böse", icon: "https://evil.example/x.png", chat_link: "[&AgGpTAAA]" },
    { id: 3, name: "<b>", chat_link: "javascript:x" },
  ]);
  assert.deepEqual([...items.keys()], [1, 2]);
  assert.equal(items.get(2).icon, null); // fremdes Icon entfernt
  const prices = validatePrices([{ id: 1, buys: { unit_price: 100 }, sells: { unit_price: 150 } }, { id: 2, buys: {} }]);
  assert.deepEqual([...prices.entries()], [[1, { bid: 100, ask: 150 }]]);
  assert.deepEqual(validateDelivery({ coins: 1234, items: [{ id: 1, count: 3 }, { id: "x", count: 1 }] }), { coins: 1234, items: [{ id: 1, count: 3 }] });
  assert.deepEqual(validateDelivery(null), { coins: 0, items: [] });
});

// --- Orders -------------------------------------------------------------------------------------

test("Überbietung und Unterbietung", () => {
  const prices = new Map([[1, { bid: 1001, ask: 1500 }], [2, { bid: 1000, ask: 1400 }], [3, { bid: 0, ask: 0 }]]);
  const buys = analyzeBuyOrders([{ item_id: 1, price: 1000 }, { item_id: 2, price: 1000 }, { item_id: 3, price: 5 }, { item_id: 4, price: 5 }], prices);
  assert.deepEqual(buys.map((b) => b.status), ["outbid", "top", "unknown", "unknown"]);
  assert.equal(buys[0].best, 1001);
  const sells = analyzeSellOrders([{ item_id: 1, price: 1499 }, { item_id: 2, price: 1500 }], prices);
  assert.deepEqual(sells.map((s) => s.status), ["lowest", "undercut"]);
});

test("fällige Verkäufe mit Preisvorschlag und Gewinn", () => {
  const prices = new Map([[1, { bid: 1000, ask: 1501 }]]);
  const t = (d) => new Date(`2026-11-0${d}T12:00:00Z`);
  const buys = [
    { item_id: 1, price: 900, quantity: 10, purchased: t(1) },
    { item_id: 1, price: 1000, quantity: 5, purchased: t(3) },
  ];
  const [due] = dueSales({ coins: 0, items: [{ id: 1, count: 8 }] }, prices, buys);
  // jüngste Käufe zuerst: 5 × 1000 + 3 × 900 → Ø 962,5
  assert.equal(due.cost, 962.5);
  assert.equal(due.suggested, 1500);
  assert.equal(due.profitPerUnit, Math.round(1500 - 225 - 962.5));
  const [unknown] = dueSales({ coins: 0, items: [{ id: 9, count: 1 }] }, prices, buys);
  assert.equal(unknown.suggested, null);
  assert.equal(unknown.profitPerUnit, null);
});

// --- Gewinn -------------------------------------------------------------------------------------

const at = (s) => new Date(s);

test("FIFO-Gewinn nach Gebühren", () => {
  const buys = [
    { id: 1, item_id: 7, price: 1000, quantity: 10, purchased: at("2026-10-01T10:00:00Z") },
    { id: 2, item_id: 7, price: 1200, quantity: 10, purchased: at("2026-10-02T10:00:00Z") },
  ];
  const sells = [
    { id: 3, item_id: 7, price: 1500, quantity: 15, purchased: at("2026-10-03T10:00:00Z") },
  ];
  const { sales, unmatchedQty } = realizedProfit(buys, sells);
  assert.equal(unmatchedQty, 0);
  const [s] = sales;
  assert.equal(s.cost, 10 * 1000 + 5 * 1200);
  assert.equal(s.net, netProceeds(1500, 15));
  assert.equal(s.profit, s.net - s.cost);
});

test("Verkäufe vor dem Einkauf oder ohne Einkauf zählen nicht", () => {
  const buys = [{ id: 1, item_id: 7, price: 1000, quantity: 4, purchased: at("2026-10-05T10:00:00Z") }];
  const sells = [
    { id: 2, item_id: 7, price: 1500, quantity: 3, purchased: at("2026-10-01T10:00:00Z") }, // vor dem Kauf
    { id: 3, item_id: 7, price: 1500, quantity: 6, purchased: at("2026-10-06T10:00:00Z") }, // 4 von 6 gedeckt
    { id: 4, item_id: 8, price: 1500, quantity: 2, purchased: at("2026-10-06T10:00:00Z") }, // nie gekauft
  ];
  const { sales, unmatchedQty } = realizedProfit(buys, sells);
  assert.equal(unmatchedQty, 3 + 2 + 2);
  assert.equal(sales.length, 1);
  assert.equal(sales[0].quantity, 4);
  assert.equal(sales[0].cost, 4000);
  assert.equal(sales[0].net, Math.round((netProceeds(1500, 6) * 4) / 6));
});

test("Kalenderwochen nach ISO 8601", () => {
  const d = (y, m, day) => new Date(y, m - 1, day, 12);
  assert.equal(isoWeekKey(d(2026, 11, 1)), "2026-W44"); // Sonntag
  assert.equal(isoWeekKey(d(2026, 11, 2)), "2026-W45"); // Montag
  assert.equal(isoWeekKey(d(2027, 1, 1)), "2026-W53");
  assert.equal(isoWeekKey(d(2025, 12, 29)), "2026-W01");
  assert.equal(isoWeekKey(d(2024, 12, 30)), "2025-W01");
  assert.equal(dayKey(d(2026, 3, 7)), "2026-03-07");
});

test("Aggregation und Zeiträume", () => {
  const s = (date, profit) => ({ purchased: new Date(date), quantity: 2, net: 100, cost: 100 - profit, profit });
  const sales = [s("2026-11-01T12:00:00", 10), s("2026-11-01T18:00:00", -4), s("2026-10-20T12:00:00", 7)];
  const days = aggregate(sales, dayKey);
  assert.deepEqual(days.map((r) => [r.key, r.profit, r.quantity, r.sales]), [
    ["2026-11-01", 6, 4, 2],
    ["2026-10-20", 7, 2, 1],
  ]);
  const now = new Date("2026-11-02T00:00:00");
  assert.equal(totalSince(sales, now, 7).profit, 6);
  assert.equal(totalSince(sales, now, 30).profit, 13);
});
