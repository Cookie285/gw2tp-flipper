import pytest

from gw2tp.analyze import RiskLevel, evaluate, liquidity_factor, preselect, rank, risk_level
from gw2tp.config import Risk
from gw2tp.fees import DEFAULT_FEES

from .conftest import make_price


def test_liquidity_factor_scaling():
    assert liquidity_factor(0, 100_000) == 0.0
    assert liquidity_factor(100_000, 100_000) == pytest.approx(1.0)
    assert liquidity_factor(10_000_000, 100_000) == 1.0  # gedeckelt
    assert 0 < liquidity_factor(500, 100_000) < liquidity_factor(5_000, 100_000) < 1


def test_score_is_profit_times_liquidity_times_stability(cfg):
    [pos] = preselect([make_price(1, bid=10_000, ask=15_000)], cfg)
    assert pos.stability_factor == 1.0
    assert pos.score == pytest.approx(pos.expected_profit * pos.liquidity_factor)
    assert pos.expected_profit == pos.candidate.profit_per_unit * pos.quantity


def test_higher_expected_profit_ranks_first(cfg):
    prices = [
        make_price(1, bid=10_000, ask=13_000),  # kleiner Spread
        make_price(2, bid=10_000, ask=16_000),  # großer Spread
    ]
    assert [p.candidate.item_id for p in preselect(prices, cfg)] == [2, 1]


def test_liquidity_breaks_equal_profit(cfg):
    prices = [
        make_price(1, bid=10_000, ask=15_000, demand=1_000, supply=1_000),
        make_price(2, bid=10_000, ask=15_000, demand=50_000, supply=50_000),
    ]
    # Gleiche Stückzahl (Budget-limitiert, 19), aber Item 2 ist liquider.
    ranked = preselect(prices, cfg)
    assert ranked[0].quantity == ranked[1].quantity
    assert [p.candidate.item_id for p in ranked] == [2, 1]


def test_ties_sorted_by_item_id(cfg):
    prices = [make_price(i, bid=10_000, ask=15_000) for i in (7, 3, 5)]
    ranked = rank(preselect(prices, cfg))
    assert [p.candidate.item_id for p in ranked] == [3, 5, 7]


@pytest.mark.parametrize(
    ("bid", "ask", "depth", "level"),
    [
        (1000, 1600, 10_000, RiskLevel.GREEN),  # ROI ≈ 27 %, tief
        (1000, 1600, 2_000, RiskLevel.YELLOW),  # ROI gut, Tiefe mittel
        (1000, 1400, 10_000, RiskLevel.YELLOW),  # ROI ≈ 18 %
        (1000, 1300, 10_000, RiskLevel.RED),  # ROI ≈ 10 %
        (1000, 1600, 900, RiskLevel.RED),  # zu dünn
    ],
)
def test_risk_level(bid, ask, depth, level):
    c = evaluate(make_price(bid=bid, ask=ask, demand=depth, supply=depth), DEFAULT_FEES)
    assert risk_level(c, Risk()) is level
