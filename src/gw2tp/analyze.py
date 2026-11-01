"""Kennzahlen, Filter, Positionsgröße und Ranking.

Phase 1 kennt noch keine Historie. Als Liquiditätsmaß dient die aktuelle Orderbuch-Tiefe
(Gesamtmenge aller Kaufgebote bzw. Verkaufsangebote laut /v2/commerce/prices). Volatilität und
Trend kommen in Phase 2; der Stabilitätsfaktor ist bis dahin 1,0.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, replace
from enum import StrEnum

from .config import Config, Filters, Ranking, Risk, Sizing
from .fees import FeeSchedule, buy_price_from_bid, net_profit, roi, sell_price_from_ask
from .models import Item, Price


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


def passes_market_filters(c: Candidate, f: Filters) -> bool:
    """Filter, die nur Preisdaten brauchen (vor der Positionsgröße)."""
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


def passes_item_filters(item: Item, f: Filters) -> bool:
    return not (item.flags & set(f.excluded_flags))


def position_size(c: Candidate, budget_copper: int, s: Sizing) -> int:
    """Stückzahl = min(Budgetanteil ÷ Kaufpreis, Anteil der Orderbuch-Tiefe, Obergrenze)."""
    if c.buy_price <= 0:
        return 0
    by_budget = int(budget_copper * s.max_budget_share) // c.buy_price
    by_depth = math.floor(c.depth * s.max_depth_share)
    return max(0, min(by_budget, by_depth, s.max_units))


def liquidity_factor(depth: int, r: Ranking) -> float:
    """Log-skaliert auf [0, 1]: 1,0 ab ``liquidity_reference_quantity``."""
    if depth <= 0:
        return 0.0
    return min(1.0, math.log10(1 + depth) / math.log10(1 + r.liquidity_reference_quantity))


def risk_level(c: Candidate, r: Risk) -> RiskLevel:
    if c.roi < r.red_below_roi or c.depth < r.red_below_depth:
        return RiskLevel.RED
    if c.roi >= r.green_min_roi and c.depth >= r.green_min_depth:
        return RiskLevel.GREEN
    return RiskLevel.YELLOW


def build_position(c: Candidate, cfg: Config) -> Position | None:
    qty = position_size(c, cfg.budget_copper, cfg.sizing)
    if not passes_profit_filter(c.profit_per_unit, qty, cfg.filters):
        return None
    expected = c.profit_per_unit * qty
    liq = liquidity_factor(c.depth, cfg.ranking)
    stability = 1.0  # Phase 2: aus Volatilität und Trend der Snapshots
    return Position(
        candidate=c,
        quantity=qty,
        expected_profit=expected,
        liquidity_factor=liq,
        stability_factor=stability,
        score=expected * liq * stability,
        risk=risk_level(c, cfg.risk),
    )


def rank(positions: Iterable[Position]) -> list[Position]:
    """Absteigend nach Score; bei Gleichstand nach Item-ID (deterministisch)."""
    return sorted(positions, key=lambda p: (-p.score, p.candidate.item_id))


def preselect(prices: Iterable[Price], cfg: Config) -> list[Position]:
    """Alle Filter ohne Item-Details anwenden und nach Score sortieren."""
    positions: list[Position] = []
    for price in prices:
        cand = evaluate(price, cfg.fees)
        if cand is None or not passes_market_filters(cand, cfg.filters):
            continue
        pos = build_position(cand, cfg)
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
