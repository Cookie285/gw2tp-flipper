// Unit-Tests für web/plan.js – Ausführung: node --test tests/js/
import assert from "node:assert/strict";
import { test } from "node:test";

import {
  formatCoins,
  formatPct,
  formatTrend,
  parseBudgetGold,
  passesHistory,
  passesProfit,
  plan,
  positionSize,
  riskLevel,
  validateCandidate,
  validateData,
  validateFunnel,
  validateReview,
} from "../../web/plan.js";

const PARAMS = {
  sizing: { max_budget_share: 0.1, max_volume_share: 0.05, max_depth_share: 0.05, max_units: 250, max_positions: 10 },
  filters: { min_profit_per_unit_copper: 1000, min_profit_per_position_copper: 10000, min_volume_multiple: 10, min_daily_volume: 50 },
  risk: { green_min_roi: 0.2, green_min_depth: 5000, red_below_roi: 0.12, red_below_depth: 1000, green_max_cv: 0.04, red_min_cv: 0.07, red_below_trend: 0.01, green_min_volume_multiple: 40 },
};

function cand(over = {}) {
  return {
    id: 1, name: "Glob of Ectoplasm", icon: "https://render.guildwars2.com/file/AB/1.png",
    chat_link: "[&AgGpTAAA]", rarity: "Exotic", buy_price: 10001, sell_price: 14999,
    profit_per_unit: 2749, roi: 0.2749, demand: 10000, supply: 10000, daily_volume: 5000,
    price_cv: 0.02, trend: 0.001, liquidity_factor: 0.8, stability_factor: 0.9, ...over,
  };
}

function data(candidates, history = true) {
  return validateData({
    schema_version: 2, generated_at: "2026-11-20T04:23:00Z",
    volume_source: history ? "snapshots" : "orderbook_depth", window_days: 7,
    budget_copper: 2000000, params: PARAMS, candidates,
  });
}

// --- Validierung ---------------------------------------------------------------------------

test("gültige Daten werden übernommen", () => {
  const d = data([cand()]);
  assert.equal(d.candidates.length, 1);
  assert.equal(d.rejected, 0);
  assert.equal(d.history, true);
});

for (const [label, over] of [
  ["fremder Icon-Host", { icon: "https://evil.example/x.png" }],
  ["http-Icon", { icon: "http://render.guildwars2.com/x.png" }],
  ["javascript-URL", { icon: "javascript:alert(1)" }],
  ["Icon mit Anführungszeichen", { icon: 'https://render.guildwars2.com/x".png' }],
  ["Chatcode mit HTML", { chat_link: "[&AgGpTAAA]<img>" }],
  ["Name kein Text", { name: 42 }],
  ["leerer Name", { name: "  " }],
  ["Preis als Text", { buy_price: "100" }],
  ["negativer Preis", { buy_price: -1 }],
  ["Bruch als Menge", { demand: 1.5 }],
  ["NaN-Faktor", { liquidity_factor: NaN }],
  ["Faktor > 1", { stability_factor: 2 }],
  ["fehlendes Volumen im Historien-Modus", { daily_volume: null }],
  ["Rarität mit Leerzeichen", { rarity: "x y" }],
]) {
  test(`verwirft Kandidat: ${label}`, () => {
    const d = data([cand(over), cand({ id: 2 })]);
    assert.deepEqual(d.candidates.map((c) => c.id), [2]);
    assert.equal(d.rejected, 1);
  });
}

test("Steuerzeichen im Namen werden entfernt", () => {
  assert.equal(validateCandidate(cand({ name: "Böse‮\nItem\u0000" }), true).name, "Böse Item");
});

for (const [label, mutate] of [
  ["falsche Version", (r) => (r.schema_version = 1)],
  ["kaputtes Datum", (r) => (r.generated_at = "gestern")],
  ["unbekannter Modus", (r) => (r.volume_source = "magic")],
  ["Parameter fehlen", (r) => delete r.params],
  ["Parameter falsch", (r) => (r.params = { ...PARAMS, sizing: { ...PARAMS.sizing, max_units: "250" } })],
  ["kein Array", (r) => (r.candidates = {})],
]) {
  test(`lehnt Datei ab: ${label}`, () => {
    const raw = {
      schema_version: 2, generated_at: "2026-11-20T04:23:00Z", volume_source: "snapshots",
      window_days: 7, budget_copper: 2000000, params: PARAMS, candidates: [],
    };
    mutate(raw);
    assert.throws(() => validateData(raw));
  });
}

test("lehnt Nicht-Objekte ab", () => {
  for (const v of [null, [], "x", 1]) assert.throws(() => validateData(v));
});

// --- Planung -------------------------------------------------------------------------------

test("Stückzahl: Budget, Volumen und Obergrenze", () => {
  const s = PARAMS.sizing;
  assert.equal(positionSize(cand(), 2000000, s), 19); // 20 g / 1g 1c
  assert.equal(positionSize(cand({ buy_price: 100, daily_volume: 1000 }), 2000000, s), 50);
  assert.equal(positionSize(cand({ buy_price: 100, daily_volume: 10 ** 6 }), 2000000, s), 250);
  assert.equal(positionSize(cand({ buy_price: 300000 }), 2000000, s), 0);
  // Orderbuch-Modus: 5 % der kleineren Seite
  assert.equal(positionSize(cand({ buy_price: 100, daily_volume: null, demand: 2000, supply: 3000 }), 2000000, s), 100);
});

test("Gewinnregel: pro Stück ODER pro Position", () => {
  const f = PARAMS.filters;
  assert.ok(passesProfit(1000, 1, f));
  assert.ok(passesProfit(900, 12, f));
  assert.ok(!passesProfit(900, 11, f));
  assert.ok(!passesProfit(5000, 0, f));
  assert.ok(!passesProfit(-1, 10 ** 6, f));
});

test("Volumen ≥ 10 × Stückzahl und Mindestvolumen", () => {
  const f = PARAMS.filters;
  assert.ok(passesHistory(cand({ daily_volume: 1000 }), 100, f));
  assert.ok(!passesHistory(cand({ daily_volume: 999 }), 100, f));
  assert.ok(!passesHistory(cand({ daily_volume: 49 }), 1, f));
});

test("Ampel", () => {
  const r = PARAMS.risk;
  assert.equal(riskLevel(cand(), r, 100, true), "green");
  assert.equal(riskLevel(cand({ trend: null }), r, 100, true), "yellow");
  assert.equal(riskLevel(cand({ price_cv: 0.07 }), r, 100, true), "red");
  assert.equal(riskLevel(cand({ trend: -0.011 }), r, 100, true), "red");
  assert.equal(riskLevel(cand({ roi: 0.1 }), r, 1, true), "red");
  assert.equal(riskLevel(cand({ daily_volume: 3000 }), r, 100, true), "yellow");
  assert.equal(riskLevel(cand({ demand: 900 }), r, 1, false), "red");
  assert.equal(riskLevel(cand(), r, 1, false), "green");
});

test("plan sortiert nach Score, Gleichstand nach ID, max. Positionen", () => {
  const cs = [];
  for (let i = 1; i <= 15; i++) cs.push(cand({ id: 16 - i }));
  cs.push(cand({ id: 99, liquidity_factor: 1 }));
  const out = plan(data(cs), 2000000);
  assert.equal(out.length, 10);
  assert.equal(out[0].id, 99);
  assert.deepEqual(out.slice(1, 4).map((p) => p.id), [1, 2, 3]);
  assert.equal(out[0].expected_profit, 2749 * 19);
  assert.equal(out[0].invest, 10001 * 19);
});

test("Budget ändert die Liste", () => {
  const cheap = cand({ id: 2, buy_price: 1001, sell_price: 1999, profit_per_unit: 698, roi: 0.697, daily_volume: 2000 });
  const pricey = cand({ id: 1, buy_price: 100001, sell_price: 129999, profit_per_unit: 10498, roi: 0.105, daily_volume: 100000 });
  const d = data([cheap, pricey]);
  assert.equal(plan(d, 20 * 10000)[0].id, 2);
  assert.ok(!plan(d, 20 * 10000).some((p) => p.id === 1)); // 10 g/Stück > 2 g Budgetanteil
  assert.equal(plan(d, 100000 * 10000)[0].id, 1);
});

// --- Formatierung --------------------------------------------------------------------------

test("Münzformat wie report.py", () => {
  assert.equal(formatCoins(0), "0c");
  assert.equal(formatCoins(100), "1s 0c");
  assert.equal(formatCoins(1234567), "123g 45s 67c");
  assert.equal(formatCoins(-150), "-1s 50c");
});

test("Prozent und Trend", () => {
  assert.equal(formatPct(0.2749), "27,5 %");
  assert.equal(formatTrend(null), "–");
  assert.equal(formatTrend(-0.0001), "→ +0,0 %");
  assert.equal(formatTrend(0.015), "↗ +1,5 %");
  assert.equal(formatTrend(-0.03), "↘ −3,0 %");
});

test("Budget-Eingabe", () => {
  assert.equal(parseBudgetGold("200"), 2000000);
  assert.equal(parseBudgetGold(" 12,5 "), 125000);
  assert.equal(parseBudgetGold("0.5"), null); // < 1 g
  assert.equal(parseBudgetGold("abc"), null);
  assert.equal(parseBudgetGold("1e3"), null);
  assert.equal(parseBudgetGold("-5"), null);
  assert.equal(parseBudgetGold("10000000"), null);
});

// --- Phase 5 -----------------------------------------------------------------------------

const REVIEW = {
  lists: 3, from: "2026-11-10", to: "2026-11-12", positions: 30, with_data: 28,
  profitable_48: 0.75, median_roi_48: 0.12, price_held_48: 0.8, outbid_24: 0.4,
  median_volume_ratio: 0.9,
};

test("Rückblick wird validiert", () => {
  assert.equal(validateReview(REVIEW).profitable48, 0.75);
  assert.equal(validateReview(null), null);
  assert.equal(validateReview({ ...REVIEW, profitable_48: 1.5 }), null);
  assert.equal(validateReview({ ...REVIEW, from: "<b>" }), null);
  assert.equal(validateReview({ ...REVIEW, with_data: 31 }), null);
  assert.equal(validateReview({ ...REVIEW, median_roi_48: null }).medianRoi48, null);
});

test("Trichter: nur bekannte Schlüssel, feste Reihenfolge", () => {
  const f = validateFunnel({ passed: 10, roi_low: 90, evil: 5, demand: "3", no_quotes: 0 });
  assert.deepEqual(f.map((x) => x.key), ["roi_low", "passed"]);
  assert.deepEqual(validateFunnel(null), []);
});

test("validateData übernimmt Rückblick und Trichter optional", () => {
  const raw = {
    schema_version: 2, generated_at: "2026-11-20T04:23:00Z", volume_source: "snapshots",
    window_days: 7, budget_copper: 2000000, params: PARAMS, candidates: [],
  };
  assert.equal(validateData(raw).review, null);
  const d = validateData({ ...raw, review: REVIEW, funnel: { passed: 1 } });
  assert.equal(d.review.lists, 3);
  assert.equal(d.funnel.length, 1);
});

test("Grün mit Trend-Untergrenze (green_min_trend)", () => {
  const r = { ...PARAMS.risk, green_min_trend: -0.005 };
  assert.equal(riskLevel(cand({ trend: -0.004 }), r, 100, true), "green");
  assert.equal(riskLevel(cand({ trend: -0.006 }), r, 100, true), "yellow");
  // ohne Parameter wie früher: Trend ≥ 0
  assert.equal(riskLevel(cand({ trend: -0.004 }), { ...PARAMS.risk, green_min_trend: 0 }, 100, true), "yellow");
});

test("green_min_trend ist optional, aber validiert", () => {
  const raw = {
    schema_version: 2, generated_at: "2026-11-20T04:23:00Z", volume_source: "snapshots",
    window_days: 7, budget_copper: 2000000, params: PARAMS, candidates: [],
  };
  assert.equal(validateData(raw).params.risk.green_min_trend, 0);
  const withParam = structuredClone(raw);
  withParam.params.risk.green_min_trend = -0.005;
  assert.equal(validateData(withParam).params.risk.green_min_trend, -0.005);
  withParam.params.risk.green_min_trend = "x";
  assert.throws(() => validateData(withParam));
  withParam.params.risk.green_min_trend = -5;
  assert.throws(() => validateData(withParam));
});
