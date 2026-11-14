"""Ausgabe der Einkaufsliste als Markdown und JSON."""

from __future__ import annotations

import json
import re
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .analyze import PoolEntry, Position, RiskLevel
from .config import Config
from .fees import COPPER_PER_GOLD, COPPER_PER_SILVER

SCHEMA_VERSION = 2
MODE_HISTORY = "snapshots"
MODE_ORDERBOOK = "orderbook_depth"
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
    mode: str = MODE_ORDERBOOK
    snapshots: int = 0
    history_items: int = 0
    universe_size: int = 0


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


def _trend(value: float | None) -> str:
    if value is None:
        return "–"
    arrow = "↗" if value > 0.002 else "↘" if value < -0.002 else "→"
    pct = round(value * 100, 1) + 0.0  # + 0.0 macht aus −0,0 eine 0,0
    return f"{arrow} {pct:+.1f} %/Tag"


_BANNER = {
    MODE_HISTORY: (
        "> Volumen, Volatilität und Trend stammen aus den stündlichen Snapshots der letzten "
        "{days} Tage ({snapshots} Snapshots, {items} Items mit Historie). Das Volumen ist eine "
        "Schätzung aus Mengenänderungen. Preise vor dem Kauf im Spiel kontrollieren. "
        "Es wird nichts automatisch gekauft."
    ),
    MODE_ORDERBOOK: (
        "> **Noch keine ausreichende Historie:** Das Volumen wird aus der aktuellen "
        "Orderbuch-Tiefe geschätzt, nicht aus echten Umsätzen. Volatilität und Trend werden "
        "noch nicht geprüft. Preise vor dem Kauf im Spiel kontrollieren. "
        "Es wird nichts automatisch gekauft."
    ),
}


def to_markdown(
    positions: Sequence[Position],
    *,
    generated_at: datetime,
    budget_copper: int,
    stats: RunStats,
    window_days: int = 7,
) -> str:
    history = stats.mode == MODE_HISTORY
    lines = [
        f"# Einkaufsliste – {generated_at:%Y-%m-%d}",
        "",
        f"Erstellt: {generated_at:%Y-%m-%d %H:%M} UTC · Budget: {format_coins(budget_copper)}",
        "",
        _BANNER[stats.mode].format(
            days=window_days, snapshots=stats.snapshots, items=stats.history_items
        ),
        "",
    ]
    if not positions:
        lines += ["Heute erfüllt kein Item alle Filter.", ""]
    else:
        extra_head = " Vol./Tag | Trend |" if history else ""
        extra_align = "---:|---:|" if history else ""
        lines += [
            "| # | Risiko | Item | Chatcode | Kaufgebot | Stück | Verkaufspreis "
            "| Netto/Stück | ROI | Einsatz | Erw. Gewinn |" + extra_head,
            "|---:|:---:|---|---|---:|---:|---:|---:|---:|---:|---:|" + extra_align,
        ]
        for i, p in enumerate(positions, 1):
            c = p.candidate
            name = escape_markdown(p.item.name) if p.item else f"Item {c.item_id}"
            chat = f"`{p.item.chat_link}`" if p.item else ""
            lines.append(
                f"| {i} | {RISK_ICON[p.risk]} {RISK_LABEL[p.risk]} | {name} | {chat} "
                f"| {format_coins(c.buy_price)} | {p.quantity} | {format_coins(c.sell_price)} "
                f"| {format_coins(c.profit_per_unit)} | {_pct(c.roi)} | {format_coins(p.invest)} "
                f"| {format_coins(p.expected_profit)} |" + (_history_cells(p) if history else "")
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
        f"- Modus: {'Historie' if history else 'Orderbuch (Rückfall)'}",
        f"- Universum (stündlich gespeichert): {stats.universe_size} Items",
        f"- Snapshots im Fenster: {stats.snapshots}, Items mit Historie: {stats.history_items}",
        f"- Preise geladen: {stats.prices_total} (verworfen: {stats.prices_rejected})",
        f"- Kandidaten im Pool (nach Markt- und Historienfiltern): {stats.candidates}",
        f"- Item-Datensätze verworfen: {stats.items_rejected}",
        f"- Fehlgeschlagene API-Blöcke: {stats.failed_batches}",
        "",
        "</details>",
        "",
    ]
    return "\n".join(lines)


def _history_cells(p: Position) -> str:
    if p.stats is None:
        return " – | – |"
    return f" {p.stats.daily_volume} | {_trend(p.stats.trend)} |"


def to_json_data(
    positions: Sequence[Position],
    *,
    generated_at: datetime,
    budget_copper: int,
    stats: RunStats,
    window_days: int = 7,
    pool: Sequence[PoolEntry] = (),
    cfg: Config | None = None,
    funnel: dict[str, int] | None = None,
    review: dict[str, Any] | None = None,
) -> dict[str, Any]:
    cfg = cfg or Config()
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "phase": 3,
        "volume_source": stats.mode,
        "window_days": window_days,
        "budget_copper": budget_copper,
        "stats": {
            "prices_total": stats.prices_total,
            "prices_rejected": stats.prices_rejected,
            "items_rejected": stats.items_rejected,
            "candidates": stats.candidates,
            "failed_batches": stats.failed_batches,
            "snapshots": stats.snapshots,
            "history_items": stats.history_items,
            "universe_size": stats.universe_size,
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
                "daily_volume": p.stats.daily_volume if p.stats else None,
                "price_cv": round(p.stats.price_cv, 4)
                if p.stats and p.stats.price_cv is not None
                else None,
                "trend": round(p.stats.trend, 4) if p.stats and p.stats.trend is not None else None,
                "demand": p.candidate.demand,
                "supply": p.candidate.supply,
                "liquidity_factor": round(p.liquidity_factor, 4),
                "stability_factor": round(p.stability_factor, 4),
                "score": round(p.score, 2),
                "risk": p.risk.value,
            }
            for i, p in enumerate(positions, 1)
        ],
        # Für das Dashboard: Parameter und Pool, um die Liste für ein anderes Budget
        # neu zu berechnen (web/plan.js). Faktoren ungerundet, damit beide Seiten gleich rechnen.
        "params": _params(cfg),
        "candidates": [_candidate(e) for e in pool],
        # Phase 5: Filter-Trichter dieses Laufs und Rückblick auf frühere Listen.
        "funnel": dict(funnel or {}),
        "review": review,
    }


def _params(cfg: Config) -> dict[str, Any]:
    s, f, r = cfg.sizing, cfg.filters, cfg.risk
    return {
        "sizing": {
            "max_budget_share": s.max_budget_share,
            "max_volume_share": s.max_volume_share,
            "max_depth_share": s.max_depth_share,
            "max_units": s.max_units,
            "max_positions": s.max_positions,
        },
        "filters": {
            "min_profit_per_unit_copper": f.min_profit_per_unit_copper,
            "min_profit_per_position_copper": f.min_profit_per_position_copper,
            "min_volume_multiple": f.min_volume_multiple,
            "min_daily_volume": f.min_daily_volume,
        },
        "risk": {
            "green_min_roi": r.green_min_roi,
            "green_min_depth": r.green_min_depth,
            "red_below_roi": r.red_below_roi,
            "red_below_depth": r.red_below_depth,
            "green_max_cv": r.green_max_cv,
            "red_min_cv": r.red_min_cv,
            "red_below_trend": r.red_below_trend,
            "green_min_volume_multiple": r.green_min_volume_multiple,
            "green_min_trend": r.green_min_trend,
        },
    }


def _candidate(e: PoolEntry) -> dict[str, Any]:
    c, st, it = e.candidate, e.stats, e.item
    return {
        "id": c.item_id,
        "name": it.name if it else None,
        "icon": it.icon if it else None,
        "chat_link": it.chat_link if it else None,
        "rarity": it.rarity if it else None,
        "buy_price": c.buy_price,
        "sell_price": c.sell_price,
        "profit_per_unit": c.profit_per_unit,
        "roi": c.roi,
        "demand": c.demand,
        "supply": c.supply,
        "daily_volume": st.daily_volume if st else None,
        "price_cv": st.price_cv if st else None,
        "trend": st.trend if st else None,
        "liquidity_factor": e.liquidity_factor,
        "stability_factor": e.stability_factor,
    }


def to_json(positions: Sequence[Position], **kwargs: Any) -> str:
    return json.dumps(to_json_data(positions, **kwargs), ensure_ascii=False, indent=2) + "\n"
