"""Kennzahlen, Filter, Positionsgröße und Ranking.

Zwei Modi:

* **Historien-Modus** (ab Phase 2): Tagesvolumen, Volatilität und Trend aus den stündlichen
  Snapshots (siehe ``history.py``). Items ohne ausreichende Historie werden ausgeschlossen.
* **Orderbuch-Modus** (Phase 1, Rückfall solange noch keine Historie existiert): Die aktuelle
  Orderbuch-Tiefe dient als Ersatz für das Volumen. Volatilität und Trend sind unbekannt.
"""

from __future__ import annotations

import math
from collections import Counter
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


def passes_static_history_filters(stats: MarketStats, f: Filters) -> bool:
    """Budgetunabhängige Historienfilter: Mindestvolumen, Volatilität, Trend."""
    if stats.daily_volume < f.min_daily_volume:
        return False
    if stats.price_cv is None or stats.price_cv > f.max_price_cv:
        return False
    return stats.trend is None or stats.trend >= -f.max_negative_trend


def passes_history_filters(stats: MarketStats, quantity: int, f: Filters) -> bool:
    """Volumen ≥ Vielfaches der Stückzahl, geringe Volatilität, kein starker Abwärtstrend."""
    if not passes_static_history_filters(stats, f):
        return False
    return stats.daily_volume >= f.min_volume_multiple * quantity


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


def build_position(
    c: Candidate, cfg: Config, stats: MarketStats | None = None, budget: int | None = None
) -> Position | None:
    """Position für ein Budget (Standard: ``cfg.budget_copper``) oder ``None``, wenn ein
    mengenabhängiger Filter greift. Das Dashboard rechnet dies in ``web/plan.js`` nach."""
    volume = stats.daily_volume if stats is not None else None
    budget = cfg.budget_copper if budget is None else budget
    qty = position_size(c, budget, cfg.sizing, volume)
    if not passes_profit_filter(c.profit_per_unit, qty, cfg.filters):
        return None
    if stats is not None and not passes_history_filters(stats, qty, cfg.filters):
        return None
    expected = c.profit_per_unit * qty
    liq = _liquidity(c, stats, cfg)
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


def _liquidity(c: Candidate, stats: MarketStats | None, cfg: Config) -> float:
    if stats is None:
        return liquidity_factor(c.depth, cfg.ranking.liquidity_reference_quantity)
    return liquidity_factor(stats.daily_volume, cfg.ranking.liquidity_reference_volume)


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


# --- Kandidaten-Pool für das Dashboard -----------------------------------------------------

UNLIMITED_BUDGET = 10**15


@dataclass(frozen=True, slots=True)
class PoolEntry:
    """Ein budgetunabhängig qualifizierter Kandidat. Das Dashboard berechnet daraus für das
    eingegebene Budget Stückzahl, mengenabhängige Filter, Score und Ampel neu."""

    candidate: Candidate
    stats: MarketStats | None
    liquidity_factor: float
    stability_factor: float
    item: Item | None = None


# Filter in Prüfreihenfolge mit Beschreibung (für den Filter-Trichter in Report und Dashboard).
FUNNEL_STEPS: dict[str, str] = {
    "no_quotes": "kein Kaufgebot oder kein Verkaufsangebot",
    "no_spread": "kein Spread nach Über-/Unterbieten",
    "min_buy_price": "Kaufpreis unter Minimum",
    "roi_low": "ROI unter Minimum",
    "roi_high": "ROI über Maximum (Ausreißer)",
    "demand": "zu wenig Nachfrage im Orderbuch",
    "supply": "zu wenig Angebot im Orderbuch",
    "no_history": "keine ausreichende Historie",
    "volume": "Tagesvolumen unter Minimum",
    "volatility": "Volatilität zu hoch",
    "downtrend": "Abwärtstrend",
    "passed": "besteht alle budgetunabhängigen Filter",
}


def rejection_reason(
    price: Price, cfg: Config, stats: Mapping[int, MarketStats] | None = None
) -> str | None:
    """Erster budgetunabhängiger Filter, an dem ein Item scheitert (``None`` = besteht)."""
    f = cfg.filters
    if price.buys.unit_price <= 0 or price.sells.unit_price <= 0:
        return "no_quotes"
    c = evaluate(price, cfg.fees)
    if c is None:
        return "no_spread"
    if c.buy_price < f.min_buy_price_copper:
        return "min_buy_price"
    if c.profit_per_unit <= 0 or c.roi < f.min_roi:
        return "roi_low"
    if c.roi > f.max_roi:
        return "roi_high"
    if c.demand < f.min_demand_quantity:
        return "demand"
    if c.supply < f.min_supply_quantity:
        return "supply"
    if stats is None:
        return None
    st = stats.get(price.id)
    if st is None:
        return "no_history"
    if st.daily_volume < f.min_daily_volume:
        return "volume"
    if st.price_cv is None or st.price_cv > f.max_price_cv:
        return "volatility"
    if st.trend is not None and st.trend < -f.max_negative_trend:
        return "downtrend"
    return None


def build_pool(
    prices: Iterable[Price],
    cfg: Config,
    stats: Mapping[int, MarketStats] | None = None,
    funnel: Counter[str] | None = None,
) -> list[PoolEntry]:
    """Kandidaten, die alle budgetunabhängigen Filter bestehen, als Vereinigung zweier Ranglisten:

    * großes Budget: Score bei unbegrenztem Budget (Menge nur durch Volumen und 250 begrenzt),
    * kleines Budget: ROI × Liquidität × Stabilität (Menge durch das Budget begrenzt).

    So enthält der Pool für jedes realistische Budget die besten Items."""
    entries: list[PoolEntry] = []
    for price in prices:
        item_stats = stats.get(price.id) if stats is not None else None
        reason = rejection_reason(price, cfg, stats)
        if funnel is not None:
            funnel[reason or "passed"] += 1
        if reason is not None:
            continue
        c = evaluate(price, cfg.fees)
        if c is None:  # pragma: no cover - durch rejection_reason ausgeschlossen
            continue
        entries.append(
            PoolEntry(
                candidate=c,
                stats=item_stats,
                liquidity_factor=_liquidity(c, item_stats, cfg),
                stability_factor=stability_factor(item_stats, cfg.filters),
            )
        )

    def unconstrained(e: PoolEntry) -> float:
        volume = e.stats.daily_volume if e.stats is not None else None
        qty = position_size(e.candidate, UNLIMITED_BUDGET, cfg.sizing, volume)
        return e.candidate.profit_per_unit * qty * e.liquidity_factor * e.stability_factor

    def budget_bound(e: PoolEntry) -> float:
        return e.candidate.roi * e.liquidity_factor * e.stability_factor

    k = cfg.ranking.pool_size_per_regime
    chosen: dict[int, PoolEntry] = {}
    for key in (unconstrained, budget_bound):
        for e in sorted(entries, key=lambda e: (-key(e), e.candidate.item_id))[:k]:
            chosen.setdefault(e.candidate.item_id, e)
    return sorted(chosen.values(), key=lambda e: e.candidate.item_id)


def attach_items(
    pool: Iterable[PoolEntry], items: Mapping[int, Item], f: Filters
) -> list[PoolEntry]:
    """Item-Details anhängen; Items ohne Details oder mit Gebunden-Flag entfernen."""
    result = []
    for e in pool:
        item = items.get(e.candidate.item_id)
        if item is not None and passes_item_filters(item, f):
            result.append(replace(e, item=item))
    return result


def plan(pool: Iterable[PoolEntry], cfg: Config, budget: int | None = None) -> list[Position]:
    """Einkaufsliste für ein Budget aus dem Pool (Gegenstück zu ``plan`` in web/plan.js)."""
    positions = []
    for e in pool:
        pos = build_position(e.candidate, cfg, e.stats, budget)
        if pos is not None:
            positions.append(replace(pos, item=e.item))
    return rank(positions)[: cfg.sizing.max_positions]


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
