"""Filter, Größe, Score und Ampel im Historien-Modus sowie Universumsauswahl."""

import pytest

from gw2tp.analyze import (
    RiskLevel,
    evaluate,
    passes_history_filters,
    position_size,
    preselect,
    risk_level,
    select_universe,
    stability_factor,
)
from gw2tp.config import Filters, Risk, Sizing, Universe
from gw2tp.fees import COPPER_PER_GOLD, DEFAULT_FEES

from .conftest import make_price, make_stats

F = Filters()


# --- Filter -------------------------------------------------------------------------------


def test_history_filter_accepts_liquid_stable_item():
    assert passes_history_filters(make_stats(), 100, F)


def test_volume_must_be_ten_times_quantity():
    assert passes_history_filters(make_stats(bought=1_000, sold=5_000), 100, F)
    assert not passes_history_filters(make_stats(bought=999, sold=5_000), 100, F)
    assert not passes_history_filters(make_stats(bought=5_000, sold=999), 100, F)


def test_min_daily_volume():
    assert not passes_history_filters(make_stats(bought=49, sold=49), 1, F)


def test_volatility_threshold():
    assert passes_history_filters(make_stats(cv=0.10), 10, F)
    assert not passes_history_filters(make_stats(cv=0.1001), 10, F)
    assert not passes_history_filters(make_stats(cv=None), 10, F)


def test_downtrend_threshold():
    assert passes_history_filters(make_stats(trend=-0.02), 10, F)
    assert not passes_history_filters(make_stats(trend=-0.0201), 10, F)
    assert passes_history_filters(make_stats(trend=0.05), 10, F)
    assert passes_history_filters(make_stats(trend=None), 10, F)  # zu wenig Tage


# --- Größe --------------------------------------------------------------------------------


def test_size_uses_five_percent_of_daily_volume():
    c = evaluate(make_price(bid=100, ask=200, demand=10**6, supply=10**6), DEFAULT_FEES)
    budget = 200 * COPPER_PER_GOLD
    assert position_size(c, budget, Sizing(), daily_volume=1_000) == 50
    assert position_size(c, budget, Sizing(), daily_volume=100_000) == 250  # Obergrenze
    assert position_size(c, budget, Sizing(), daily_volume=10) == 0


# --- Score / Stabilität / Ampel -----------------------------------------------------------


def test_stability_factor():
    assert stability_factor(None, F) == 1.0
    assert stability_factor(make_stats(cv=0.0, trend=0.01), F) == pytest.approx(1.0)
    assert stability_factor(make_stats(cv=0.05, trend=0.0), F) == pytest.approx(0.75)
    assert stability_factor(make_stats(cv=0.0, trend=-0.01), F) == pytest.approx(0.75)
    assert stability_factor(make_stats(cv=0.10, trend=-0.02), F) == pytest.approx(0.25)
    assert stability_factor(make_stats(cv=0.0, trend=None), F) == pytest.approx(0.9)


def test_stable_item_outranks_volatile_one(cfg):
    prices = [make_price(1, bid=10_000, ask=15_000), make_price(2, bid=10_000, ask=15_000)]
    stats = {1: make_stats(cv=0.08), 2: make_stats(cv=0.01)}
    assert [p.candidate.item_id for p in preselect(prices, cfg, stats)] == [2, 1]


def test_items_without_history_excluded_in_history_mode(cfg):
    prices = [make_price(1, bid=10_000, ask=15_000), make_price(2, bid=10_000, ask=15_000)]
    ranked = preselect(prices, cfg, {1: make_stats()})
    assert [p.candidate.item_id for p in ranked] == [1]
    assert ranked[0].stats is not None


def test_low_volume_limits_quantity_and_profit_rule(cfg):
    # 400/Tag → 5 % = 20 Stück, aber das Budget (20 g ÷ 1g 1c) erlaubt nur 19
    [pos] = preselect([make_price(1, bid=10_000, ask=15_000)], cfg, {1: make_stats(400, 400)})
    assert pos.quantity == 19
    # 100/Tag → 5 % = 5 Stück; Volumen 100 ≥ 10 × 5 → besteht
    [pos] = preselect([make_price(1, bid=10_000, ask=15_000)], cfg, {1: make_stats(100, 100)})
    assert pos.quantity == 5


def _cand(bid=1000, ask=1600):
    return evaluate(make_price(bid=bid, ask=ask), DEFAULT_FEES)


@pytest.mark.parametrize(
    ("stats", "qty", "level"),
    [
        (make_stats(cv=0.02, trend=0.001), 100, RiskLevel.GREEN),
        (make_stats(cv=0.02, trend=None), 100, RiskLevel.YELLOW),  # Trend unbekannt
        (make_stats(cv=0.05, trend=0.0), 100, RiskLevel.YELLOW),
        (make_stats(cv=0.07, trend=0.0), 100, RiskLevel.RED),
        (make_stats(cv=0.02, trend=-0.011), 100, RiskLevel.RED),
        (make_stats(bought=3_000, cv=0.02, trend=0.0), 100, RiskLevel.YELLOW),  # < 40×
    ],
)
def test_risk_level_with_history(stats, qty, level):
    assert risk_level(_cand(), Risk(), stats, qty) is level


def test_low_roi_is_red_regardless_of_history():
    assert risk_level(_cand(ask=1300), Risk(), make_stats(), 10) is RiskLevel.RED


# --- Universum ----------------------------------------------------------------------------


def test_universe_sorted_by_depth_and_limited():
    prices = [
        make_price(1, demand=1_000, supply=5_000),  # Tiefe 1000
        make_price(2, demand=50_000, supply=40_000),  # 40000
        make_price(3, demand=9_000, supply=9_000),  # 9000
    ]
    assert select_universe(prices, Universe(max_items=2), DEFAULT_FEES) == [2, 3]


def test_universe_excludes_thin_cheap_and_unprofitable():
    prices = [
        make_price(1, demand=100, supply=10_000),  # zu dünn
        make_price(2, bid=50, ask=100),  # zu billig
        make_price(3, bid=1_000, ask=1_050),  # Spread deckt Gebühren nicht
        make_price(4, bid=1_000, ask=0),  # kein Angebot
        make_price(5),
    ]
    assert select_universe(prices, Universe(), DEFAULT_FEES) == [5]


def test_universe_whitelist_always_included():
    u = Universe(max_items=1, whitelist_ids=(19721, 2))
    prices = [make_price(1), make_price(2, demand=10, supply=10)]
    assert select_universe(prices, u, DEFAULT_FEES) == [1, 2, 19721]


def test_green_min_trend_threshold():
    r = Risk(green_min_trend=-0.005)
    assert risk_level(_cand(), r, make_stats(cv=0.02, trend=-0.004), 100) is RiskLevel.GREEN
    assert risk_level(_cand(), r, make_stats(cv=0.02, trend=-0.006), 100) is RiskLevel.YELLOW
    # Standard (0.0) wie bisher
    assert risk_level(_cand(), Risk(), make_stats(cv=0.02, trend=-0.004), 100) is RiskLevel.YELLOW
