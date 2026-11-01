from gw2tp.analyze import evaluate, finalize, position_size, preselect
from gw2tp.config import Config, Sizing
from gw2tp.fees import COPPER_PER_GOLD, DEFAULT_FEES

from .conftest import make_item, make_price

BUDGET = 200 * COPPER_PER_GOLD  # 200 g → max. 20 g pro Item
S = Sizing()


def cand(**kw):
    return evaluate(make_price(**kw), DEFAULT_FEES)


def test_budget_cap_ten_percent():
    # Kaufpreis 1g 1c → 20 g / 10 001 c = 19 Stück
    c = cand(bid=10_000, ask=15_000, demand=1_000_000, supply=1_000_000)
    assert position_size(c, BUDGET, S) == 19


def test_depth_cap_five_percent_of_smaller_side():
    # billig, Budget nicht limitierend; Tiefe min(2000, 3000) × 5 % = 100
    c = cand(bid=100, ask=200, demand=2_000, supply=3_000)
    assert position_size(c, BUDGET, S) == 100
    c = cand(bid=100, ask=200, demand=3_000, supply=2_000)
    assert position_size(c, BUDGET, S) == 100


def test_absolute_cap_250_units():
    c = cand(bid=100, ask=200, demand=1_000_000, supply=1_000_000)
    assert position_size(c, BUDGET, S) == 250


def test_too_expensive_gives_zero():
    # Kaufpreis > 20 g → 0 Stück
    c = cand(bid=250_000, ask=400_000)
    assert position_size(c, BUDGET, S) == 0


def test_zero_quantity_is_not_listed():
    cfg = Config()
    assert preselect([make_price(1, bid=250_000, ask=400_000)], cfg) == []


def test_max_ten_positions(cfg):
    prices = [make_price(i, bid=10_000, ask=15_000) for i in range(1, 30)]
    ranked = preselect(prices, cfg)
    items = {i: make_item(i) for i in range(1, 30)}
    assert len(finalize(ranked, items, cfg)) == 10


def test_positions_respect_total_budget(cfg):
    prices = [make_price(i, bid=10_000 + i, ask=15_000) for i in range(1, 30)]
    result = finalize(preselect(prices, cfg), {i: make_item(i) for i in range(1, 30)}, cfg)
    assert all(p.invest <= cfg.budget_copper * cfg.sizing.max_budget_share for p in result)
    assert sum(p.invest for p in result) <= cfg.budget_copper
