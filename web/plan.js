// Reine Logik ohne DOM: Validierung der Daten und Planung der Einkaufsliste für ein Budget.
// Die Regeln entsprechen src/gw2tp/analyze.py (build_position, risk_level, plan). Ein
// Paritätstest in der CI (tests/test_dashboard_parity.py) stellt sicher, dass beide gleich rechnen.

export const COPPER_PER_GOLD = 10000;
export const SCHEMA_VERSION = 2;
export const MODE_HISTORY = "snapshots";
export const MODE_ORDERBOOK = "orderbook_depth";

const MAX_CANDIDATES = 2000;
const MAX_NAME_LENGTH = 200;
const MAX_PRICE = 10_000_000_000;
const MAX_QUANTITY = 1_000_000_000;
export const ICON_RE = /^https:\/\/render\.guildwars2\.com\/[A-Za-z0-9/._-]+$/;
export const CHAT_RE = /^\[&[A-Za-z0-9+/]{1,64}={0,2}\]$/;
export const WORD_RE = /^[A-Za-z]{1,64}$/;
const TIME_RE = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$/;
// Steuerzeichen inkl. Bidi-Overrides (Unicode-Kategorie C*), wie clean_text in models.py.
const CONTROL_RE = /\p{C}/gu;

export class DataError extends Error {}

const isInt = (v, min = 0, max = MAX_PRICE) =>
  Number.isSafeInteger(v) && v >= min && v <= max;
const isNum = (v, min = 0, max = 1e9) =>
  typeof v === "number" && Number.isFinite(v) && v >= min && v <= max;
const isNullableNum = (v, min, max) => v === null || isNum(v, min, max);

export function cleanName(v) {
  if (typeof v !== "string") return null;
  const s = v.replace(CONTROL_RE, " ").split(/\s+/).filter(Boolean).join(" ");
  return s && s.length <= MAX_NAME_LENGTH ? s : null;
}

function requireNumbers(obj, spec, section) {
  if (!obj || typeof obj !== "object" || Array.isArray(obj)) {
    throw new DataError(`${section}: Objekt erwartet`);
  }
  const out = {};
  for (const [key, [min, max, integer]] of Object.entries(spec)) {
    const v = obj[key];
    const ok = integer ? isInt(v, min, max) : isNum(v, min, max);
    if (!ok) throw new DataError(`${section}.${key} ungültig`);
    out[key] = v;
  }
  return out;
}

const PARAM_SPEC = {
  sizing: {
    max_budget_share: [0, 1],
    max_volume_share: [0, 1],
    max_depth_share: [0, 1],
    max_units: [0, 1e6, true],
    max_positions: [1, 50, true],
  },
  filters: {
    min_profit_per_unit_copper: [0, MAX_PRICE, true],
    min_profit_per_position_copper: [0, MAX_PRICE, true],
    min_volume_multiple: [0, 1e6],
    min_daily_volume: [0, MAX_QUANTITY, true],
  },
  risk: {
    green_min_roi: [0, 1],
    green_min_depth: [0, MAX_QUANTITY, true],
    red_below_roi: [0, 1],
    red_below_depth: [0, MAX_QUANTITY, true],
    green_max_cv: [0, 1],
    red_min_cv: [0, 1],
    red_below_trend: [0, 1],
    green_min_volume_multiple: [0, 1e6],
  },
};

/** Einen Kandidaten prüfen; ``null`` bei ungültigen Daten. */
export function validateCandidate(raw, history) {
  if (!raw || typeof raw !== "object" || Array.isArray(raw)) return null;
  const name = cleanName(raw.name);
  const chat = raw.chat_link;
  const icon = raw.icon;
  if (!isInt(raw.id, 1, 10_000_000) || name === null) return null;
  if (typeof chat !== "string" || !CHAT_RE.test(chat)) return null;
  if (icon !== null && (typeof icon !== "string" || icon.length > 500 || !ICON_RE.test(icon))) {
    return null;
  }
  if (raw.rarity !== null && (typeof raw.rarity !== "string" || !WORD_RE.test(raw.rarity))) {
    return null;
  }
  if (!isInt(raw.buy_price, 1) || !isInt(raw.sell_price, 1)) return null;
  if (!isInt(raw.profit_per_unit, -MAX_PRICE)) return null;
  if (!isNum(raw.roi, -1, 1e6)) return null;
  if (!isInt(raw.demand, 0, MAX_QUANTITY) || !isInt(raw.supply, 0, MAX_QUANTITY)) return null;
  if (!isNum(raw.liquidity_factor, 0, 1) || !isNum(raw.stability_factor, 0, 1)) return null;
  const volumeOk = history
    ? isInt(raw.daily_volume, 0, MAX_QUANTITY)
    : raw.daily_volume === null;
  if (!volumeOk) return null;
  if (!isNullableNum(raw.price_cv, 0, 1e3) || !isNullableNum(raw.trend, -1e3, 1e3)) return null;
  return {
    id: raw.id,
    name,
    icon,
    chat_link: chat,
    rarity: raw.rarity,
    buy_price: raw.buy_price,
    sell_price: raw.sell_price,
    profit_per_unit: raw.profit_per_unit,
    roi: raw.roi,
    demand: raw.demand,
    supply: raw.supply,
    daily_volume: raw.daily_volume,
    price_cv: raw.price_cv,
    trend: raw.trend,
    liquidity_factor: raw.liquidity_factor,
    stability_factor: raw.stability_factor,
  };
}

/** shopping-list.json prüfen. Wirft ``DataError`` bei strukturellen Fehlern; ungültige
 *  Kandidaten werden verworfen und gezählt. */
export function validateData(raw) {
  if (!raw || typeof raw !== "object" || Array.isArray(raw)) {
    throw new DataError("Objekt erwartet");
  }
  if (raw.schema_version !== SCHEMA_VERSION) throw new DataError("Unbekannte Datenversion");
  if (typeof raw.generated_at !== "string" || !TIME_RE.test(raw.generated_at)) {
    throw new DataError("generated_at ungültig");
  }
  if (raw.volume_source !== MODE_HISTORY && raw.volume_source !== MODE_ORDERBOOK) {
    throw new DataError("volume_source ungültig");
  }
  if (!isInt(raw.budget_copper, 1)) throw new DataError("budget_copper ungültig");
  if (!isInt(raw.window_days, 1, 365)) throw new DataError("window_days ungültig");
  const p = raw.params;
  if (!p || typeof p !== "object") throw new DataError("params fehlt");
  const params = {
    sizing: requireNumbers(p.sizing, PARAM_SPEC.sizing, "sizing"),
    filters: requireNumbers(p.filters, PARAM_SPEC.filters, "filters"),
    risk: requireNumbers(p.risk, PARAM_SPEC.risk, "risk"),
  };
  if (!Array.isArray(raw.candidates) || raw.candidates.length > MAX_CANDIDATES) {
    throw new DataError("candidates ungültig");
  }
  const history = raw.volume_source === MODE_HISTORY;
  const candidates = [];
  let rejected = 0;
  for (const c of raw.candidates) {
    const v = validateCandidate(c, history);
    if (v === null) rejected += 1;
    else candidates.push(v);
  }
  return {
    generatedAt: new Date(raw.generated_at),
    history,
    windowDays: raw.window_days,
    defaultBudget: raw.budget_copper,
    params,
    candidates,
    rejected,
  };
}

// --- Planung (gleich wie analyze.py) -------------------------------------------------------

export const depth = (c) => Math.min(c.demand, c.supply);

export function positionSize(c, budget, sizing) {
  if (c.buy_price <= 0) return 0;
  const byBudget = Math.floor(Math.trunc(budget * sizing.max_budget_share) / c.buy_price);
  const byVolume =
    c.daily_volume === null
      ? Math.floor(depth(c) * sizing.max_depth_share)
      : Math.floor(c.daily_volume * sizing.max_volume_share);
  return Math.max(0, Math.min(byBudget, byVolume, sizing.max_units));
}

export function passesProfit(profitPerUnit, qty, f) {
  if (profitPerUnit <= 0 || qty <= 0) return false;
  return (
    profitPerUnit >= f.min_profit_per_unit_copper ||
    profitPerUnit * qty >= f.min_profit_per_position_copper
  );
}

/** Mengenabhängige Historienfilter (Volatilität und Trend sind im Pool schon geprüft). */
export function passesHistory(c, qty, f) {
  return c.daily_volume >= f.min_daily_volume && c.daily_volume >= f.min_volume_multiple * qty;
}

export function riskLevel(c, r, qty, history) {
  if (c.roi < r.red_below_roi) return "red";
  if (!history) {
    if (depth(c) < r.red_below_depth) return "red";
    if (c.roi >= r.green_min_roi && depth(c) >= r.green_min_depth) return "green";
    return "yellow";
  }
  const cv = c.price_cv === null ? Infinity : c.price_cv;
  if (cv >= r.red_min_cv || (c.trend !== null && c.trend < -r.red_below_trend)) return "red";
  if (
    c.roi >= r.green_min_roi &&
    cv <= r.green_max_cv &&
    c.trend !== null &&
    c.trend >= 0 &&
    c.daily_volume >= r.green_min_volume_multiple * Math.max(1, qty)
  ) {
    return "green";
  }
  return "yellow";
}

/** Einkaufsliste für ``budget`` (Kupfer) aus den validierten Daten. */
export function plan(data, budget) {
  const { sizing, filters, risk } = data.params;
  const positions = [];
  for (const c of data.candidates) {
    const quantity = positionSize(c, budget, sizing);
    if (!passesProfit(c.profit_per_unit, quantity, filters)) continue;
    if (data.history && !passesHistory(c, quantity, filters)) continue;
    const expected = c.profit_per_unit * quantity;
    positions.push({
      ...c,
      quantity,
      invest: c.buy_price * quantity,
      expected_profit: expected,
      score: expected * c.liquidity_factor * c.stability_factor,
      risk: riskLevel(c, risk, quantity, data.history),
    });
  }
  positions.sort((a, b) => b.score - a.score || a.id - b.id);
  return positions.slice(0, sizing.max_positions);
}

// --- Formatierung --------------------------------------------------------------------------

/** 1234567 → [{v:123,u:"g"},{v:45,u:"s"},{v:67,u:"c"}] (wie format_coins in report.py). */
export function coinParts(copper) {
  const neg = copper < 0;
  let rest = Math.abs(copper);
  const g = Math.floor(rest / 10000);
  rest %= 10000;
  const s = Math.floor(rest / 100);
  const c = rest % 100;
  const parts = [];
  if (g) parts.push({ v: g, u: "g" });
  if (g || s) parts.push({ v: s, u: "s" });
  parts.push({ v: c, u: "c" });
  return { neg, parts };
}

export function formatCoins(copper) {
  const { neg, parts } = coinParts(copper);
  return (neg ? "-" : "") + parts.map((p) => `${p.v}${p.u}`).join(" ");
}

export function formatPct(value) {
  return `${(value * 100).toFixed(1).replace(".", ",")} %`;
}

export function formatTrend(value) {
  if (value === null) return "–";
  const arrow = value > 0.002 ? "↗" : value < -0.002 ? "↘" : "→";
  const pct = Math.round(value * 1000) / 10 + 0; // + 0 macht aus −0 eine 0
  const sign = pct >= 0 ? "+" : "−";
  return `${arrow} ${sign}${Math.abs(pct).toFixed(1).replace(".", ",")} %`;
}

/** Budget-Eingabe in Gold → Kupfer; ``null`` bei ungültiger Eingabe. */
export function parseBudgetGold(text) {
  const s = String(text).trim().replace(",", ".");
  if (!/^\d{1,6}(\.\d{1,4})?$/.test(s)) return null;
  const copper = Math.round(Number(s) * COPPER_PER_GOLD);
  return copper >= COPPER_PER_GOLD && copper <= 1_000_000 * COPPER_PER_GOLD ? copper : null;
}
