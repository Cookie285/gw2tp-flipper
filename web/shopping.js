// Tab „Einkaufsliste“: lädt shopping-list.json (gleicher Ursprung) und plant für das Budget.

import { $, cell, coins, el, itemCell } from "./dom.js";
import {
  COPPER_PER_GOLD,
  DataError,
  formatPct,
  formatTrend,
  parseBudgetGold,
  plan,
  validateData,
} from "./plan.js";

const DATA_URL = "shopping-list.json";
const MAX_BYTES = 5 * 1024 * 1024;
const STALE_HOURS = 36;
const BUDGET_KEY = "gw2tp.budgetGold";
const RISK_TEXT = { green: "gering", yellow: "mittel", red: "erhöht" };

// --- localStorage nur für die Budget-Komfortfunktion (keine sensiblen Daten) --------------

function loadBudget() {
  try {
    return parseBudgetGold(window.localStorage.getItem(BUDGET_KEY) ?? "");
  } catch {
    return null;
  }
}

function saveBudget(gold) {
  try {
    window.localStorage.setItem(BUDGET_KEY, gold);
  } catch {
    /* privater Modus o. Ä.: ignorieren */
  }
}

// --- Daten laden ---------------------------------------------------------------------------

async function loadData() {
  const resp = await fetch(DATA_URL, { cache: "no-store", credentials: "omit" });
  if (resp.status === 404) throw new DataError("Noch keine Einkaufsliste veröffentlicht.");
  if (!resp.ok) throw new DataError(`Daten konnten nicht geladen werden (HTTP ${resp.status}).`);
  const text = await resp.text();
  if (text.length > MAX_BYTES) throw new DataError("Datendatei ist zu groß.");
  let raw;
  try {
    raw = JSON.parse(text);
  } catch {
    throw new DataError("Datendatei ist kein gültiges JSON.");
  }
  return validateData(raw);
}

// --- Rendering -----------------------------------------------------------------------------

function renderTable(positions, history) {
  const tbody = $("rows");
  tbody.replaceChildren();
  positions.forEach((p, i) => {
    const tr = el("tr", { cls: `risk-${p.risk}` });
    tr.append(
      cell("#", String(i + 1), "num rank"),
      cell(
        "Risiko",
        el("span", { cls: `badge badge-${p.risk}`, text: RISK_TEXT[p.risk] }),
        "risk",
      ),
      cell("Item", itemCell(p), "item-cell"),
      cell("Kaufgebot", coins(p.buy_price), "num"),
      cell("Stück", String(p.quantity), "num"),
      cell("Verkaufspreis", coins(p.sell_price), "num"),
      cell("Netto/Stück", coins(p.profit_per_unit), "num"),
      cell("ROI", formatPct(p.roi), "num"),
      cell("Einsatz", coins(p.invest), "num"),
      cell("Erw. Gewinn", coins(p.expected_profit), "num profit"),
    );
    if (history) {
      tr.append(
        cell("Vol./Tag", p.daily_volume.toLocaleString("de-DE"), "num"),
        cell("Trend/Tag", formatTrend(p.trend), "num"),
      );
    }
    tbody.append(tr);
  });
  for (const th of document.querySelectorAll(".history-col")) th.hidden = !history;
  $("table").hidden = positions.length === 0;
  $("empty").hidden = positions.length !== 0;
}

function renderSummary(positions, budget) {
  const invest = positions.reduce((s, p) => s + p.invest, 0);
  const profit = positions.reduce((s, p) => s + p.expected_profit, 0);
  const box = $("summary");
  box.replaceChildren(
    el("span", { text: `${positions.length} Positionen · Einsatz ` }),
    coins(invest),
    el("span", { text: " von " }),
    coins(budget),
    el("span", { text: " · erwarteter Gewinn " }),
    coins(profit),
    el("span", { cls: "muted", text: " (nach 15 % Gebühren)" }),
  );
}

function renderMeta(data) {
  const stamp = data.generatedAt.toLocaleString("de-DE", {
    dateStyle: "medium",
    timeStyle: "short",
  });
  $("generated").textContent = `Stand: ${stamp}`;
  const hours = (Date.now() - data.generatedAt.getTime()) / 3_600_000;
  $("stale").hidden = !(hours > STALE_HOURS);
  $("mode").textContent = data.history
    ? `Volumen, Volatilität und Trend aus stündlichen Snapshots der letzten ${data.windowDays} Tage.`
    : "Noch keine ausreichende Historie: Das Volumen wird aus der Orderbuch-Tiefe geschätzt, " +
      "Volatilität und Trend werden noch nicht geprüft.";
  $("mode").className = data.history ? "note" : "note warn";
  $("rejected").hidden = data.rejected === 0;
  $("rejected").textContent = `${data.rejected} fehlerhafte Datensätze wurden ignoriert.`;
}

const fmtShare = (v) => (v === null ? "–" : `${Math.round(v * 100)} %`);
const fmtDate = (iso) => {
  const [y, m, d] = iso.split("-");
  return `${d}.${m}.${y}`;
};

function renderReview(review) {
  const box = $("review");
  if (review === null) {
    box.textContent =
      "Bilanz: Noch keine Auswertung. Eine Liste wird frühestens 48 Stunden nach ihrer " +
      "Erstellung gegen die Snapshots geprüft.";
    return;
  }
  const roi = review.medianRoi48 === null ? "–" : formatPct(review.medianRoi48);
  box.textContent =
    `Bilanz der Listen vom ${fmtDate(review.from)} bis ${fmtDate(review.to)} ` +
    `(${review.withData} von ${review.positions} Positionen mit Daten): ` +
    `${fmtShare(review.profitable48)} wären nach 48 h mit Gewinn verkaufbar gewesen ` +
    `(Median-ROI ${roi}), Preis gehalten bei ${fmtShare(review.priceHeld48)}, ` +
    `Gebot binnen 24 h überholt bei ${fmtShare(review.outbid24)}. ` +
    "Details: evaluation.md im Branch data.";
}

function renderFunnel(funnel) {
  const total = funnel.reduce((s, f) => s + f.count, 0);
  const rows = funnel.map((f) =>
    el("tr", {}, [
      el("td", { text: f.label }),
      el("td", { cls: "num", text: f.count.toLocaleString("de-DE") }),
      el("td", { cls: "num", text: formatPct(f.count / total) }),
    ]),
  );
  $("funnel").replaceChildren(el("tbody", {}, rows));
  $("funnel-box").hidden = funnel.length === 0;
}

function showError(message) {
  $("error").textContent = message;
  $("error").hidden = false;
  $("content").hidden = true;
}

export async function initShopping() {
  let data;
  try {
    data = await loadData();
  } catch (err) {
    showError(err instanceof DataError ? err.message : "Daten konnten nicht geladen werden.");
    return;
  }
  renderMeta(data);
  renderReview(data.review);
  renderFunnel(data.funnel);

  const input = $("budget");
  const initial = loadBudget() ?? data.defaultBudget;
  input.value = String(initial / COPPER_PER_GOLD);

  const update = () => {
    const budget = parseBudgetGold(input.value);
    input.setAttribute("aria-invalid", budget === null ? "true" : "false");
    $("budget-error").hidden = budget !== null;
    if (budget === null) return;
    saveBudget(input.value.trim());
    const positions = plan(data, budget);
    renderTable(positions, data.history);
    renderSummary(positions, budget);
  };
  input.addEventListener("input", update);
  $("budget-form").addEventListener("submit", (e) => {
    e.preventDefault();
    update();
  });
  $("budget-reset").addEventListener("click", () => {
    input.value = String(data.defaultBudget / COPPER_PER_GOLD);
    update();
  });
  update();
  $("content").hidden = false;
}
