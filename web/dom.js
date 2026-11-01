// Gemeinsame DOM-Helfer. Inhalte werden ausschließlich per textContent bzw. setAttribute gesetzt,
// niemals per innerHTML (zusätzlich durch Trusted Types in der CSP erzwungen).

import { coinParts } from "./plan.js";

export const $ = (id) => document.getElementById(id);

export function el(tag, { cls, text, attrs } = {}, children = []) {
  const node = document.createElement(tag);
  if (cls) node.className = cls;
  if (text !== undefined) node.textContent = String(text);
  if (attrs) for (const [k, v] of Object.entries(attrs)) node.setAttribute(k, String(v));
  for (const child of children) node.append(child);
  return node;
}

export function coins(copper) {
  const { neg, parts } = coinParts(copper);
  const wrap = el("span", { cls: "coins" });
  if (neg) wrap.append("−");
  parts.forEach((p, i) => {
    if (i) wrap.append(" ");
    wrap.append(el("span", { cls: `coin coin-${p.u}`, text: `${p.v}${p.u}` }));
  });
  return wrap;
}

export function copyButton(chat) {
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

/** Item mit Icon, Name (Seltenheitsfarbe) und Chatcode-Button. Erwartet validierte Daten. */
export function itemCell(p) {
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

export function cell(label, content, cls) {
  const td = el("td", { cls, attrs: { "data-label": label } });
  td.append(content);
  return td;
}
