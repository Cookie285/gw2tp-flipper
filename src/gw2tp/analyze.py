"""Kennzahlen, Filter, Positionsgröße und Ranking.

Zwei Modi:

* **Historien-Modus** (ab Phase 2): Tagesvolumen, Volatilität und Trend aus den stündlichen
  Snapshots (siehe ``history.py``). Items ohne ausreichende Historie werden ausgeschlossen.
* **Orderbuch-Modus** (Phase 1, Rückfall solange noch keine Historie existiert): Die aktuelle
  Orderbuch-Tiefe dient als Ersatz für das Volumen. Volatilität und Trend sind unbekannt.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, replace
from enum import StrEnum

from .config import Config, Filters, Risk, Sizing, Universe
from .fees import FeeSchedule, buy_price_from_bid, net_profit, roi, sell_price_from_ask
from .history import MarketStats
from .models import Item, Price

UNKNOWN_TREND_FACTOR = 0.9


class RiskLevel(StrEnum):
    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"


@dataclass(frozen=True, slots=True)
class Candidate:
    item_id: int
    buy_price: int
    sell_price: int
    profit_per_unit: int
    roi: float
    demand: int  # Gesamtmenge aller Kaufgebote
    supply: int  # Gesamtmenge aller Verkaufsangebote

    @property
    def depth(self) -> int:
        """Engpass des Orderbuchs: die kleinere der beiden Seiten."""
        return min(self.demand, self.supply)


@dataclass(frozen=True, slots=True)
class Position:
    candidate: Candidate
    quantity: int
    expected_profit: int
    liquidity_factor: float
    stability_factor: float
    score: float
    risk: RiskLevel
    stats: MarketStats | None = None
    item: Item | None = None

    @property
    def invest(self) -> int:
        return self.candidate.buy_price * self.quantity


def evaluate(price: Price, fees: FeeSchedule) -> Candidate | None:
    """Kauf-/Verkaufspreis und Gewinn für einen Preis-Datensatz. ``None``, wenn eine Seite fehlt
    oder nach Unterbieten kein Spread übrig bleibt."""
    if price.buys.unit_price <= 0 or price.sells.unit_price <= 0:
        return None
    buy = buy_price_from_bid(price.buys.unit_price)
    sell = sell_price_from_ask(price.sells.unit_price)
    if sell <= buy:
        return None
    profit = net_profit(buy, sell, fees)
    return Candidate(
        item_id=price.id,
        buy_price=buy,
        sell_price=sell,
        profit_per_unit=profit,
        roi=roi(buy, profit),
        demand=price.buys.quantity,
        supply=price.sells.quantity,
    )


# --- Filter -------------------------------------------------------------------------------


def passes_market_filters(c: Candidate, f: Filters) -> bool:
    """Filter, die nur aktuelle Preisdaten brauchen (vor der Positionsgröße)."""
    return (
        c.buy_price >= f.min_buy_price_copper
        and f.min_roi <= c.roi <= f.max_roi
        and c.demand >= f.min_demand_quantity
        and c.supply >= f.min_supply_quantity
    )


def passes_profit_filter(profit_per_unit: int, quantity: int, f: Filters) -> bool:
    """Netto ≥ X pro Stück ODER Gesamtgewinn der Position ≥ Y."""
    if profit_per_unit <= 0 or quantity <= 0:
        return False
    return (
        profit_per_unit >= f.min_profit_per_unit_copper
        or profit_per_unit * quantity >= f.min_profit_per_position_copper
    )


def passes_history_filters(stats: MarketStats, quantity: int, f: Filters) -> bool:
    """Volumen ≥ Vielfaches der Stückzahl, geringe Volatilität, kein starker Abwärtstrend."""
    if stats.daily_volume < f.min_daily_volume:
        return False
    if stats.daily_volume < f.min_volume_multiple * quantity:
        return False
    if stats.price_cv is None or stats.price_cv > f.max_price_cv:
        return False
    return stats.trend is None or stats.trend >= -f.max_negative_trend


def passes_item_filters(item: Item, f: Filters) -> bool:
    return not (item.flags & set(f.excluded_flags))


# --- Größe und Score ----------------------------------------------------------------------


def position_size(
    c: Candidate, budget_copper: int, s: Sizing, daily_volume: int | None = None
) -> int:
    """Stückzahl = min(Budgetanteil ÷ Kaufpreis, Anteil am Tagesvolumen, Obergrenze).

    Ohne Historie (``daily_volume is None``) ersetzt die Orderbuch-Tiefe das Tagesvolumen."""
    if c.buy_price <= 0:
        return 0
    by_budget = int(budget_copper * s.max_budget_share) // c.buy_price
    if daily_volume is None:
        by_volume = math.floor(c.depth * s.max_depth_share)
    else:
        by_volume = math.floor(daily_volume * s.max_volume_share)
    return max(0, min(by_budget, by_volume, s.max_units))


def liquidity_factor(amount: int, reference: int) -> float:
    """Log-skaliert auf [0, 1]: 1,0 ab ``reference``."""
    if amount <= 0:
        return 0.0
    return min(1.0, math.log10(1 + amount) / math.log10(1 + max(1, reference)))


def stability_factor(stats: MarketStats | None, f: Filters) -> float:
    """1,0 = stabil. Volatilität und fallender Trend senken den Faktor auf bis zu 0,25."""
    if stats is None:
        return 1.0  # Orderbuch-Modus: unbekannt, siehe Hinweis im Report
    cv = stats.price_cv if stats.price_cv is not None else f.max_price_cv
    cv_part = 1 - 0.5 * min(1.0, cv / f.max_price_cv) if f.max_price_cv > 0 else 0.5
    if stats.trend is None:
        trend_part = UNKNOWN_TREND_FACTOR
    elif f.max_negative_trend > 0:
        trend_part = 1 - 0.5 * min(1.0, max(0.0, -stats.trend) / f.max_negative_trend)
    else:
        trend_part = 1.0 if stats.trend >= 0 else 0.5
    return cv_part * trend_part


def risk_level(
    c: Candidate, r: Risk, stats: MarketStats | None = None, quantity: int = 0
) -> RiskLevel:
    if c.roi < r.red_below_roi:
        return RiskLevel.RED
    if stats is None:
        if c.depth < r.red_below_depth:
            return RiskLevel.RED
        if c.roi >= r.green_min_roi and c.depth >= r.green_min_depth:
            return RiskLevel.GREEN
        return RiskLevel.YELLOW

    cv = stats.price_cv if stats.price_cv is not None else math.inf
    if cv >= r.red_min_cv or (stats.trend is not None and stats.trend < -r.red_below_trend):
        return RiskLevel.RED
    if (
        c.roi >= r.green_min_roi
        and cv <= r.green_max_cv
        and stats.trend is not None
        and stats.trend >= 0
        and stats.daily_volume >= r.green_min_volume_multiple * max(1, quantity)
    ):
        return RiskLevel.GREEN
    return RiskLevel.YELLOW


def build_position(c: Candidate, cfg: Config, stats: MarketStats | None = None) -> Position | None:
    volume = stats.daily_volume if stats is not None else None
    qty = position_size(c, cfg.budget_copper, cfg.sizing, volume)
    if not passes_profit_filter(c.profit_per_unit, qty, cfg.filters):
        return None
    if stats is not None and not passes_history_filters(stats, qty, cfg.filters):
        return None
    expected = c.profit_per_unit * qty
    if stats is None:
        liq = liquidity_factor(c.depth, cfg.ranking.liquidity_reference_quantity)
    else:
        liq = liquidity_factor(stats.daily_volume, cfg.ranking.liquidity_reference_volume)
    stability = stability_factor(stats, cfg.filters)
    return Position(
        candidate=c,
        quantity=qty,
        expected_profit=expected,
        liquidity_factor=liq,
        stability_factor=stability,
        score=expected * liq * stability,
        risk=risk_level(c, cfg.risk, stats, qty),
        stats=stats,
    )


def rank(positions: Iterable[Position]) -> list[Position]:
    """Absteigend nach Score; bei Gleichstand nach Item-ID (deterministisch)."""
    return sorted(positions, key=lambda p: (-p.score, p.candidate.item_id))


def preselect(
    prices: Iterable[Price], cfg: Config, stats: Mapping[int, MarketStats] | None = None
) -> list[Position]:
    """Alle Filter ohne Item-Details anwenden und nach Score sortieren.

    ``stats is None`` → Orderbuch-Modus. Sonst werden nur Items mit Historie berücksichtigt."""
    positions: list[Position] = []
    for price in prices:
        item_stats = None
        if stats is not None:
            item_stats = stats.get(price.id)
            if item_stats is None:
                continue
        cand = evaluate(price, cfg.fees)
        if cand is None or not passes_market_filters(cand, cfg.filters):
            continue
        pos = build_position(cand, cfg, item_stats)
        if pos is not None:
            positions.append(pos)
    return rank(positions)


def finalize(ranked: Iterable[Position], items: Mapping[int, Item], cfg: Config) -> list[Position]:
    """Item-Filter anwenden (Gebundenheit, fehlende Details) und auf max. N Positionen kürzen."""
    result: list[Position] = []
    for pos in ranked:
        item = items.get(pos.candidate.item_id)
        if item is None or not passes_item_filters(item, cfg.filters):
            continue
        result.append(replace(pos, item=item))
        if len(result) >= cfg.sizing.max_positions:
            break
    return result


# --- Universum ----------------------------------------------------------------------------


def select_universe(prices: Iterable[Price], u: Universe, fees: FeeSchedule) -> list[int]:
    """Die liquidesten Items für die stündlichen Snapshots plus Whitelist.

    Kriterien: beide Orderbuch-Seiten ≥ ``min_quantity``, Kaufpreis ≥ Minimum, aktueller Spread
    nach Gebühren ≥ ``min_roi``. Sortiert nach der kleineren Orderbuch-Seite."""
    scored: list[tuple[int, int]] = []
    for price in prices:
        c = evaluate(price, fees)
        if c is None:
            continue
        if c.buy_price < u.min_buy_price_copper or c.depth < u.min_quantity or c.roi < u.min_roi:
            continue
        scored.append((c.depth, c.item_id))
    scored.sort(key=lambda t: (-t[0], t[1]))
    chosen = [pid for _, pid in scored[: u.max_items]]
    return sorted(set(chosen) | set(u.whitelist_ids))
