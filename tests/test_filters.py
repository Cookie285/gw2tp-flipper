import pytest

from gw2tp.analyze import (
    evaluate,
    finalize,
    passes_item_filters,
    passes_market_filters,
    passes_profit_filter,
    preselect,
)
from gw2tp.config import Filters
from gw2tp.fees import DEFAULT_FEES

from .conftest import make_item, make_price

F = Filters()


def cand(**kw):
    c = evaluate(make_price(**kw), DEFAULT_FEES)
    assert c is not None
    return c


def test_evaluate_computes_prices_and_profit():
    c = cand(bid=1000, ask=1500)
    assert (c.buy_price, c.sell_price) == (1001, 1499)
    # 1499 − 75 − 150 − 1001
    assert c.profit_per_unit == 273
    assert c.roi == pytest.approx(273 / 1001)


@pytest.mark.parametrize(
    ("bid", "ask"),
    [(0, 1500), (1000, 0), (1000, 1001), (1000, 1002), (1500, 1000)],
)
def test_evaluate_rejects_missing_side_or_no_spread(bid, ask):
    assert evaluate(make_price(bid=bid, ask=ask), DEFAULT_FEES) is None


def test_market_filter_accepts_good_candidate():
    assert passes_market_filters(cand(), F)


def test_roi_threshold_is_inclusive():
    c = cand(bid=1000, ask=1500)
    assert passes_market_filters(c, Filters(min_roi=c.roi))
    assert not passes_market_filters(c, Filters(min_roi=c.roi + 1e-9))


def test_roi_below_ten_percent_rejected():
    # Kauf 1001, Verkauf 1299 → Netto 1299-65-130-1001 = 103 → ROI ≈ 10,3 %
    assert passes_market_filters(cand(bid=1000, ask=1300), F)
    # Verkauf 1279 → 1279-64-128-1001 = 86 → ROI ≈ 8,6 %
    assert not passes_market_filters(cand(bid=1000, ask=1280), F)


def test_max_roi_rejects_outliers():
    assert not passes_market_filters(cand(bid=1000, ask=10_000), F)


def test_min_buy_price_one_silver():
    # Kaufpreis 99c → raus, 100c → drin
    assert not passes_market_filters(cand(bid=98, ask=200), F)
    assert passes_market_filters(cand(bid=99, ask=200), F)


@pytest.mark.parametrize("side", ["demand", "supply"])
def test_orderbook_depth_proxy(side):
    assert passes_market_filters(cand(**{side: 500}), F)
    assert not passes_market_filters(cand(**{side: 499}), F)


def test_profit_filter_per_unit_or_per_position():
    # 10 s pro Stück reicht, auch bei 1 Stück
    assert passes_profit_filter(1_000, 1, F)
    # 9 s pro Stück, aber 12 Stück → 1,08 g Positionsgewinn
    assert passes_profit_filter(900, 12, F)
    # 9 s × 11 = 99 s → weder noch
    assert not passes_profit_filter(900, 11, F)


def test_profit_filter_rejects_zero_quantity_and_losses():
    assert not passes_profit_filter(5_000, 0, F)
    assert not passes_profit_filter(-1, 100_000, F)
    assert not passes_profit_filter(0, 100_000, F)


@pytest.mark.parametrize("flag", ["AccountBound", "SoulbindOnAcquire"])
def test_bound_items_excluded(flag):
    assert not passes_item_filters(make_item(flags=[flag]), F)


def test_bind_on_use_items_allowed():
    assert passes_item_filters(make_item(flags=["SoulBindOnUse", "NoSalvage"]), F)


def test_finalize_drops_items_without_details_or_bound(cfg):
    prices = [
        make_price(1, bid=10_000, ask=15_000),
        make_price(2, bid=10_000, ask=15_000),
        make_price(3, bid=10_000, ask=15_000),
    ]
    ranked = preselect(prices, cfg)
    items = {1: make_item(1), 2: make_item(2, flags=["AccountBound"])}  # 3 fehlt
    result = finalize(ranked, items, cfg)
    assert [p.candidate.item_id for p in result] == [1]
    assert result[0].item is not None and result[0].item.id == 1
