"""Kandidaten-Pool und budgetabhängige Planung (Grundlage fürs Dashboard)."""

from dataclasses import replace

from gw2tp.analyze import attach_items, build_pool, finalize, plan, preselect
from gw2tp.config import Ranking
from gw2tp.fees import COPPER_PER_GOLD

from .conftest import make_item, make_price, make_stats


def _prices():
    return [
        # teuer, hoher Stückgewinn, sehr liquide → gewinnt bei großem Budget
        make_price(1, bid=100_000, ask=130_000, demand=10**6, supply=10**6),
        # billig, sehr hoher ROI, wenig Volumen → gewinnt bei kleinem Budget
        make_price(2, bid=1_000, ask=2_000, demand=2_000, supply=2_000),
        make_price(3, bid=10_000, ask=15_000),
        make_price(4, bid=10_000, ask=10_500),  # ROI zu klein → nicht im Pool
    ]


def test_pool_contains_only_qualified_candidates(cfg):
    ids = [e.candidate.item_id for e in build_pool(_prices(), cfg)]
    assert ids == [1, 2, 3]


def test_pool_respects_history_static_filters(cfg):
    stats = {1: make_stats(), 2: make_stats(cv=0.5), 3: make_stats(trend=-0.1)}
    assert [e.candidate.item_id for e in build_pool(_prices(), cfg, stats)] == [1]


def test_pool_is_union_of_both_regimes(cfg):
    small = replace(cfg, ranking=Ranking(pool_size_per_regime=1))
    ids = [e.candidate.item_id for e in build_pool(_prices(), small)]
    assert ids == [1, 2]  # 1 = bester bei großem Budget, 2 = bester ROI


def test_plan_matches_preselect_finalize_for_default_budget(cfg):
    prices = [make_price(i, bid=1_000 * i, ask=1_500 * i + 7 * i) for i in range(1, 40)]
    items = {i: make_item(i) for i in range(1, 40)}
    pool = attach_items(build_pool(prices, cfg), items, cfg.filters)
    via_pool = plan(pool, cfg)
    classic = finalize(preselect(prices, cfg), items, cfg)
    assert [(p.candidate.item_id, p.quantity, p.score) for p in via_pool] == [
        (p.candidate.item_id, p.quantity, p.score) for p in classic
    ]


def test_budget_changes_ranking(cfg):
    pool = attach_items(
        build_pool(_prices(), cfg), {i: make_item(i) for i in (1, 2, 3)}, cfg.filters
    )
    big = plan(pool, cfg, 10_000 * COPPER_PER_GOLD)
    tiny = plan(pool, cfg, 20 * COPPER_PER_GOLD)
    assert big[0].candidate.item_id == 1
    assert tiny[0].candidate.item_id == 2
    # Beim kleinen Budget passt Item 1 (10 g/Stück > 10 % von 20 g) gar nicht hinein.
    assert 1 not in [p.candidate.item_id for p in tiny]


def test_attach_items_drops_bound_and_unknown(cfg):
    pool = build_pool(_prices(), cfg)
    items = {1: make_item(1), 2: make_item(2, flags=["AccountBound"])}
    assert [e.candidate.item_id for e in attach_items(pool, items, cfg.filters)] == [1]
