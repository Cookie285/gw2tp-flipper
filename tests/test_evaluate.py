"""Phase 5: Filter-Trichter und Rückblick auf frühere Listen."""

import json
from collections import Counter
from datetime import UTC, date, datetime, timedelta

import pytest

from gw2tp import evaluate
from gw2tp.__main__ import review_lists, review_summary
from gw2tp.analyze import FUNNEL_STEPS, attach_items, build_pool, plan, rejection_reason
from gw2tp.config import Config, Filters
from gw2tp.evaluate import (
    ArchivedPosition,
    encode_archive,
    evaluate_lists,
    evaluate_position,
    grouped,
    parse_archive,
    summarize,
    to_markdown,
)
from gw2tp.fees import DEFAULT_FEES
from gw2tp.history import encode_snapshot, snapshot_relpath
from gw2tp.models import Price, Quote, ValidationError

from .conftest import hourly_snapshots, make_item, make_price, make_stats

T0 = datetime(2026, 11, 10, 4, 23, tzinfo=UTC)
GAP = 3 * 3600


# --- Filter-Trichter ----------------------------------------------------------------------


@pytest.mark.parametrize(
    ("price", "stats", "reason"),
    [
        (make_price(bid=0), None, "no_quotes"),
        (make_price(bid=1000, ask=1001), None, "no_spread"),
        (make_price(bid=50, ask=200), None, "min_buy_price"),
        (make_price(bid=1000, ask=1100), None, "roi_low"),
        (make_price(bid=1000, ask=5000), None, "roi_high"),
        (make_price(demand=10), None, "demand"),
        (make_price(supply=10), None, "supply"),
        (make_price(), {}, "no_history"),
        (make_price(), {1: make_stats(bought=10, sold=10)}, "volume"),
        (make_price(), {1: make_stats(cv=0.5)}, "volatility"),
        (make_price(), {1: make_stats(trend=-0.1)}, "downtrend"),
        (make_price(), {1: make_stats()}, None),
        (make_price(), None, None),
    ],
)
def test_rejection_reason(price, stats, reason, cfg):
    assert rejection_reason(price, cfg, stats) == reason


def test_funnel_counts_every_item(cfg):
    prices = [make_price(1), make_price(2, bid=0), make_price(3, demand=1), make_price(4)]
    funnel: Counter[str] = Counter()
    pool = build_pool(prices, cfg, None, funnel)
    assert funnel == {"passed": 2, "no_quotes": 1, "demand": 1}
    assert sum(funnel.values()) == len(prices)
    assert len(pool) == 2
    assert set(funnel) <= set(FUNNEL_STEPS)


def test_funnel_order_matches_filters():
    # Jeder Grund im Trichter ist beschrieben, "passed" kommt zuletzt.
    assert list(FUNNEL_STEPS)[-1] == "passed"


# --- Archiv -------------------------------------------------------------------------------


def _positions(cfg):
    prices = [make_price(1, bid=10_000, ask=15_000), make_price(2, bid=5_000, ask=8_000)]
    stats = {1: make_stats(cv=0.01, trend=0.002), 2: make_stats(cv=0.05, trend=None)}
    pool = attach_items(
        build_pool(prices, cfg, stats), {1: make_item(1), 2: make_item(2)}, cfg.filters
    )
    return plan(pool, cfg)


def test_archive_roundtrip(cfg):
    positions = _positions(cfg)
    text = encode_archive(positions, T0, "snapshots")
    lst = parse_archive(text, T0.date())
    assert lst.generated_at == T0 and lst.mode == "snapshots"
    assert [p.item_id for p in lst.positions] == [p.candidate.item_id for p in positions]
    p = lst.positions[0]
    src = positions[0]
    assert (p.buy_price, p.sell_price, p.quantity) == (
        src.candidate.buy_price,
        src.candidate.sell_price,
        src.quantity,
    )
    assert p.daily_volume == src.stats.daily_volume
    assert len(text) < 5_000  # kompakt


def test_archive_drops_invalid_rows():
    good = {
        "id": 1,
        "name": "x",
        "buy_price": 100,
        "sell_price": 150,
        "quantity": 2,
        "roi": 0.2,
        "risk": "green",
        "daily_volume": None,
        "price_cv": None,
        "trend": None,
    }
    data = {
        "schema_version": 1,
        "generated_at": "2026-11-10T04:23:00Z",
        "mode": "x",
        "positions": [
            good,
            {**good, "risk": "pink"},
            {**good, "quantity": 0},
            {**good, "roi": "0.2"},
            {**good, "roi": None},
            "junk",
        ],
    }
    assert len(parse_archive(json.dumps(data), T0.date()).positions) == 1


@pytest.mark.parametrize(
    "text",
    ['{"schema_version": 2}', "[]", '{"schema_version": 1, "generated_at": "x", "positions": []}'],
)
def test_archive_rejects_bad_structure(text):
    with pytest.raises(ValidationError):
        parse_archive(text, T0.date())


# --- Auswertung einzelner Positionen ------------------------------------------------------


def _pos(**kw):
    base = dict(
        item_id=1,
        name="Ekto",
        buy_price=1001,
        sell_price=1499,
        quantity=10,
        roi=0.27,
        risk="green",
        daily_volume=1200,
        price_cv=0.01,
        trend=0.0,
    )
    return ArchivedPosition(**{**base, **kw})


def _series(hours, fn):
    snaps = hourly_snapshots(T0 - timedelta(hours=1), hours + 2, fn)
    return [(s.taken_at, s.prices[1]) for s in snaps]


def test_stable_spread_is_profitable_and_held():
    # Angebot bleibt bei 1500, Gebot bei 1000; Volumen 50/h je Seite → 1200/Tag
    series = _series(
        50, lambda h: [Price(1, Quote(1000, 10**5 - 50 * h), Quote(1500, 10**5 - 50 * h))]
    )
    o = evaluate_position(_pos(), T0, T0.date(), series, DEFAULT_FEES, GAP)
    assert o.has_data
    assert o.roi_48 == pytest.approx((1499 - 75 - 150 - 1001) / 1001)
    assert o.price_held_48 is True
    assert o.outbid_24 is False
    assert o.volume_ratio == pytest.approx(1.0)


def test_falling_price_and_outbid():
    def fn(h):
        return [Price(1, Quote(1000 + (5 if h > 3 else 0), 10**5), Quote(1500 - 8 * h, 10**5))]

    o = evaluate_position(_pos(), T0, T0.date(), _series(50, fn), DEFAULT_FEES, GAP)
    assert o.outbid_24 is True
    assert o.price_held_48 is False
    assert o.roi_48 < 0
    assert o.volume_ratio == pytest.approx(0.0)


def test_missing_data():
    o = evaluate_position(_pos(), T0, T0.date(), [], DEFAULT_FEES, GAP)
    assert not o.has_data and o.roi_48 is None and o.outbid_24 is None


def test_horizon_without_nearby_snapshot_is_unknown():
    # Nur Snapshots in den ersten 10 Stunden → kein Wert nach 24/48 h
    series = _series(10, lambda h: [Price(1, Quote(1000, 1), Quote(1500, 1))])
    o = evaluate_position(_pos(), T0, T0.date(), series, DEFAULT_FEES, GAP)
    assert o.roi_24 is None and o.roi_48 is None
    assert o.outbid_24 is False and o.has_data


def test_summary_and_groups():
    good = _series(
        50, lambda h: [Price(1, Quote(1000, 10**5 - 50 * h), Quote(1500, 10**5 - 50 * h))]
    )
    bad = _series(50, lambda h: [Price(1, Quote(1100, 10**5), Quote(1100, 10**5))])
    outcomes = [
        evaluate_position(_pos(risk="green", roi=0.25), T0, T0.date(), good, DEFAULT_FEES, GAP),
        evaluate_position(
            _pos(risk="red", roi=0.5, price_cv=0.08), T0, T0.date(), bad, DEFAULT_FEES, GAP
        ),
    ]
    s = summarize(outcomes)
    assert s.positions == 2 and s.with_data == 2
    assert s.profitable_48 == 0.5
    assert s.outbid_24 == 0.5
    g = grouped(outcomes)
    risk = dict(g["risk"])
    assert risk["grün"].profitable_48 == 1.0 and risk["rot"].profitable_48 == 0.0
    assert [label for label, _ in g["risk"]] == ["grün", "rot"]
    assert [label for label, _ in g["roi"]] == ["20 % – 35 %", "35 % – 60 %"]
    assert [label for label, _ in g["cv"]] == ["0 % – 2 %", "7 % – 10 %"]


def test_bucket_order_is_numeric():
    labels = evaluate._bucket_labels(evaluate.VOLUME_EDGES, evaluate._count)
    assert labels == [
        "< 0",
        "0 – 200",
        "200 – 1.000",
        "1.000 – 5.000",
        "5.000 – 20.000",
        "≥ 20.000",
    ]


def test_markdown_report():
    series = _series(50, lambda h: [Price(1, Quote(1000, 10**5), Quote(1500, 10**5))])
    lst = evaluate.ArchivedList(T0.date(), T0, "snapshots", [_pos()])
    outcomes = [
        *evaluate_lists([lst], [], DEFAULT_FEES, GAP),
        evaluate_position(_pos(), T0, T0.date(), series, DEFAULT_FEES, GAP),
    ]
    md = to_markdown(outcomes, [lst], {"passed": 10, "roi_low": 90}, T0 + timedelta(days=3))
    assert "## Gesamt" in md and "## Nach Ampel" in md
    assert "| ROI unter Minimum | 90 | 90.0 % |" in md
    empty = to_markdown([], [], {}, T0)
    assert "Noch keine Listen auswertbar" in empty


# --- Integration: Archive im data-Verzeichnis ---------------------------------------------


def test_review_only_lists_older_than_48h(tmp_path, cfg):
    positions = _positions(cfg)
    lists_dir = tmp_path / "lists"
    lists_dir.mkdir()
    now = datetime(2026, 11, 13, 4, 23, tzinfo=UTC)
    for days_ago in (1, 3, 20):
        t = now - timedelta(days=days_ago)
        (lists_dir / f"{t.date()}.json").write_text(encode_archive(positions, t, "snapshots"))
    (lists_dir / "2026-11-12.md").write_text("ignoriert")
    (lists_dir / "evil.json").write_text("{}")

    snaps = hourly_snapshots(
        now - timedelta(days=4),
        24 * 4,
        lambda h: [Price(i, Quote(5_000, 10**5), Quote(9_000, 10**5)) for i in (1, 2)],
    )
    for s in snaps:
        p = tmp_path / snapshot_relpath(s.taken_at)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(encode_snapshot(s.taken_at, s.prices.values()))

    lists, outcomes = review_lists(tmp_path, snaps, cfg, now)
    assert [lst.day for lst in lists] == [date(2026, 11, 10)]  # 1 Tag zu jung, 20 Tage zu alt
    assert len(outcomes) == len(positions)
    summary = review_summary(lists, outcomes)
    assert summary["lists"] == 1 and summary["from"] == "2026-11-10"
    assert summary["with_data"] == len(positions)
    assert review_summary([], []) is None


def test_static_filters_unchanged_by_funnel(cfg):
    # Der Trichter darf das Ergebnis des Pools nicht verändern.
    prices = [make_price(i, bid=1_000 * i, ask=1_600 * i) for i in range(1, 30)]
    with_funnel = build_pool(prices, cfg, None, Counter())
    without = build_pool(prices, cfg)
    assert [e.candidate.item_id for e in with_funnel] == [e.candidate.item_id for e in without]


def test_filters_default_unchanged():
    # Phase 5 ändert keine Schwellwerte ohne Daten (siehe README).
    f = Filters()
    assert (f.min_roi, f.max_roi, f.max_price_cv, f.max_negative_trend) == (0.10, 2.0, 0.10, 0.02)
    assert Config().budget_copper == 2_000_000


def test_funnel_labels_match_dashboard():
    # web/plan.js enthält dieselben Schlüssel und Texte wie FUNNEL_STEPS.
    import re as _re
    from pathlib import Path

    src = (Path(__file__).resolve().parents[1] / "web/plan.js").read_text(encoding="utf-8")
    block = _re.search(r"FUNNEL_LABELS = \{(.*?)\};", src, _re.DOTALL).group(1)
    js = dict(_re.findall(r'(\w+): "([^"]+)"', block))
    assert js == FUNNEL_STEPS


# --- Trennung nach Modus (Phase-5-Anpassung) ----------------------------------------------


def _mixed_outcomes():
    series = _series(50, lambda h: [Price(1, Quote(1000, 10**5), Quote(1500, 10**5))])
    hist = evaluate.ArchivedList(T0.date(), T0, "snapshots", [_pos(risk="yellow")])
    book = evaluate.ArchivedList(
        T0.date() - timedelta(days=1),
        T0 - timedelta(days=1),
        "orderbook_depth",
        [_pos(risk="green", roi=1.5, daily_volume=None)],
    )
    outcomes = [
        evaluate_position(
            _pos(risk="yellow"), T0, T0.date(), series, DEFAULT_FEES, GAP, "snapshots"
        ),
        evaluate_position(
            _pos(risk="green", roi=1.5, daily_volume=None),
            T0,
            T0.date(),
            series,
            DEFAULT_FEES,
            GAP,
            "orderbook_depth",
        ),
    ]
    return [hist, book], outcomes


def test_evaluate_lists_keeps_mode():
    lst = evaluate.ArchivedList(T0.date(), T0, "snapshots", [_pos()])
    [o] = evaluate_lists([lst], [], DEFAULT_FEES, GAP)
    assert o.mode == "snapshots"


def test_review_summary_counts_only_history_mode():
    lists, outcomes = _mixed_outcomes()
    s = review_summary(lists, outcomes)
    assert s["lists"] == 1 and s["positions"] == 1
    assert s["from"] == s["to"] == T0.date().isoformat()
    # Nur Orderbuch-Listen → keine Bilanz statt verzerrter Zahlen
    assert review_summary(lists[1:], outcomes[1:]) is None


def test_markdown_separates_modes():
    lists, outcomes = _mixed_outcomes()
    md = to_markdown(outcomes, lists, {}, T0 + timedelta(days=3))
    assert "| Historien-Modus | 1 |" in md
    assert "| Orderbuch-Modus | 1 |" in md
    assert "enthält nur Listen aus dem Historien-Modus" in md
    # Aufschlüsselung nach Ampel nur mit der Historien-Position (gelb), nicht der grünen
    ampel = md.split("## Nach Ampel")[1].split("##")[0]
    assert "| gelb |" in ampel and "| grün |" not in ampel
