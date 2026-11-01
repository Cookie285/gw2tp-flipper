"""Ausgabe der Einkaufsliste als Markdown und JSON."""

from __future__ import annotations

import json
import re
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .analyze import Position, RiskLevel
from .fees import COPPER_PER_GOLD, COPPER_PER_SILVER

SCHEMA_VERSION = 1
RISK_ICON = {RiskLevel.GREEN: "🟢", RiskLevel.YELLOW: "🟡", RiskLevel.RED: "🔴"}
RISK_LABEL = {RiskLevel.GREEN: "gering", RiskLevel.YELLOW: "mittel", RiskLevel.RED: "erhöht"}
# Zeichen mit Markdown-/HTML-Bedeutung, die in Item-Namen escaped werden.
_MD_SPECIAL = re.compile(r"([\\`*_{}\[\]()<>#+\-.!|~&\"'=:])")


@dataclass(frozen=True, slots=True)
class RunStats:
    prices_total: int
    prices_rejected: int
    items_rejected: int
    candidates: int
    failed_batches: int


def format_coins(copper: int) -> str:
    """1234567 → '123g 45s 67c'. Negative Beträge mit Minus."""
    sign = "-" if copper < 0 else ""
    copper = abs(copper)
    gold, rest = divmod(copper, COPPER_PER_GOLD)
    silver, cop = divmod(rest, COPPER_PER_SILVER)
    parts = []
    if gold:
        parts.append(f"{gold}g")
    if gold or silver:
        parts.append(f"{silver}s")
    parts.append(f"{cop}c")
    return sign + " ".join(parts)


def escape_markdown(text: str) -> str:
    """Text für eine Markdown-Tabellenzelle unschädlich machen (keine Links, HTML, Spalten)."""
    text = " ".join(text.split())
    return _MD_SPECIAL.sub(r"\\\1", text)


def _pct(value: float) -> str:
    return f"{value * 100:.1f} %"


def to_markdown(
    positions: Sequence[Position], *, generated_at: datetime, budget_copper: int, stats: RunStats
) -> str:
    lines = [
        f"# Einkaufsliste – {generated_at:%Y-%m-%d}",
        "",
        f"Erstellt: {generated_at:%Y-%m-%d %H:%M} UTC · Budget: {format_coins(budget_copper)}",
        "",
        "> **Phase 1 (MVP):** Das Volumen wird aus der aktuellen Orderbuch-Tiefe geschätzt, "
        "nicht aus echten Umsätzen. Volatilität und Trend werden noch nicht geprüft. "
        "Preise vor dem Kauf im Spiel kontrollieren. Es wird nichts automatisch gekauft.",
        "",
    ]
    if not positions:
        lines += ["Heute erfüllt kein Item alle Filter.", ""]
    else:
        lines += [
            "| # | Risiko | Item | Chatcode | Kaufgebot | Stück | Verkaufspreis "
            "| Netto/Stück | ROI | Einsatz | Erw. Gewinn |",
            "|---:|:---:|---|---|---:|---:|---:|---:|---:|---:|---:|",
        ]
        for i, p in enumerate(positions, 1):
            c = p.candidate
            name = escape_markdown(p.item.name) if p.item else f"Item {c.item_id}"
            chat = f"`{p.item.chat_link}`" if p.item else ""
            lines.append(
                f"| {i} | {RISK_ICON[p.risk]} {RISK_LABEL[p.risk]} | {name} | {chat} "
                f"| {format_coins(c.buy_price)} | {p.quantity} | {format_coins(c.sell_price)} "
                f"| {format_coins(c.profit_per_unit)} | {_pct(c.roi)} | {format_coins(p.invest)} "
                f"| {format_coins(p.expected_profit)} |"
            )
        total_invest = sum(p.invest for p in positions)
        total_profit = sum(p.expected_profit for p in positions)
        lines += [
            "",
            f"**Summe:** Einsatz {format_coins(total_invest)} · "
            f"erwarteter Gewinn {format_coins(total_profit)} (nach 15 % Gebühren)",
            "",
        ]
    lines += [
        "<details><summary>Lauf-Statistik</summary>",
        "",
        f"- Preise geladen: {stats.prices_total} (verworfen: {stats.prices_rejected})",
        f"- Kandidaten nach Markt- und Gewinnfiltern: {stats.candidates}",
        f"- Item-Datensätze verworfen: {stats.items_rejected}",
        f"- Fehlgeschlagene API-Blöcke: {stats.failed_batches}",
        "",
        "</details>",
        "",
    ]
    return "\n".join(lines)


def to_json_data(
    positions: Sequence[Position], *, generated_at: datetime, budget_copper: int, stats: RunStats
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "phase": 1,
        "volume_source": "orderbook_depth",
        "budget_copper": budget_copper,
        "stats": {
            "prices_total": stats.prices_total,
            "prices_rejected": stats.prices_rejected,
            "items_rejected": stats.items_rejected,
            "candidates": stats.candidates,
            "failed_batches": stats.failed_batches,
        },
        "positions": [
            {
                "rank": i,
                "id": p.candidate.item_id,
                "name": p.item.name if p.item else None,
                "icon": p.item.icon if p.item else None,
                "chat_link": p.item.chat_link if p.item else None,
                "rarity": p.item.rarity if p.item else None,
                "buy_price": p.candidate.buy_price,
                "sell_price": p.candidate.sell_price,
                "quantity": p.quantity,
                "profit_per_unit": p.candidate.profit_per_unit,
                "roi": round(p.candidate.roi, 4),
                "invest": p.invest,
                "expected_profit": p.expected_profit,
                "demand": p.candidate.demand,
                "supply": p.candidate.supply,
                "liquidity_factor": round(p.liquidity_factor, 4),
                "stability_factor": round(p.stability_factor, 4),
                "score": round(p.score, 2),
                "risk": p.risk.value,
            }
            for i, p in enumerate(positions, 1)
        ],
    }


def to_json(positions: Sequence[Position], **kwargs: Any) -> str:
    return json.dumps(to_json_data(positions, **kwargs), ensure_ascii=False, indent=2) + "\n"
