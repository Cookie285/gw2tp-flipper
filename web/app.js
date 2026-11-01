// Dashboard: lädt shopping-list.json (gleicher Ursprung) und rendert die Einkaufsliste.
// Sicherheit: Daten aus der API werden ausschließlich per textContent bzw. als Attribute bereits
// validierter URLs gesetzt, niemals per innerHTML. Die CSP erzwingt zusätzlich Trusted Types.

import {
  COPPER_PER_GOLD,
  DataError,
  coinParts,
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

const $ = (id) => document.getElementById(id);

function el(tag, { cls, text, attrs } = {}, children = []) {
  const node = document.createElement(tag);
  if (cls) node.className = cls;
  if (text !== undefined) node.textContent = String(text);
  if (attrs) for (const [k, v] of Object.entries(attrs)) node.setAttribute(k, String(v));
  for (const child of children) node.append(child);
  return node;
}

function coins(copper) {
  const { neg, parts } = coinParts(copper);
  const wrap = el("span", { cls: "coins" });
  if (neg) wrap.append("−");
  parts.forEach((p, i) => {
    if (i) wrap.append(" ");
    wrap.append(el("span", { cls: `coin coin-${p.u}`, text: `${p.v}${p.u}` }));
  });
  return wrap;
}

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

function copyButton(chat) {
  const btn = el("button", {
    cls: "copy",
    text: "Kopieren",
    attrs: { type: "button", title: `Chatcode ${chat} kopieren` },
  });
  const code = el("code", { cls: "chat", text: chat });
  btn.addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(chat);
      btn.textContent = "Kopiert ✓";
      btn.classList.add("done");
    } catch {
      // Fallback: Code markieren, damit er mit Strg+C kopiert werden kann.
      const range = document.createRange();
      range.selectNodeContents(code);
      const sel = window.getSelection();
      sel.removeAllRanges();
      sel.addRange(range);
      btn.textContent = "Markiert – Strg+C";
    }
    window.setTimeout(() => {
      btn.textContent = "Kopieren";
      btn.classList.remove("done");
    }, 1800);
  });
  return el("span", { cls: "chat-wrap" }, [code, btn]);
}

function itemCell(p) {
  const children = [];
  if (p.icon) {
    const img = el("img", {
      cls: "icon",
      attrs: {
        src: p.icon,
        alt: "",
        width: 32,
        height: 32,
        loading: "lazy",
        referrerpolicy: "no-referrer",
      },
    });
    img.addEventListener("error", () => {
      img.hidden = true;
    });
    children.push(img);
  }
  const rarity = (p.rarity || "basic").toLowerCase();
  const text = el("span", { cls: "item-text" }, [
    el("span", { cls: `name rarity-${rarity}`, text: p.name }),
    copyButton(p.chat_link),
  ]);
  children.push(text);
  return el("span", { cls: "item" }, children);
}

function cell(label, content, cls) {
  const td = el("td", { cls, attrs: { "data-label": label } });
  td.append(content);
  return td;
}

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

function showError(message) {
  $("error").textContent = message;
  $("error").hidden = false;
  $("content").hidden = true;
}

async function main() {
  let data;
  try {
    data = await loadData();
  } catch (err) {
    showError(err instanceof DataError ? err.message : "Daten konnten nicht geladen werden.");
    return;
  }
  renderMeta(data);

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

main();
