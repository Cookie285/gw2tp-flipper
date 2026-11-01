import json
from datetime import UTC, datetime

import pytest

from gw2tp.analyze import finalize, preselect
from gw2tp.report import RunStats, escape_markdown, format_coins, to_json, to_markdown

from .conftest import make_item, make_price

NOW = datetime(2026, 11, 1, 4, 23, tzinfo=UTC)
STATS = RunStats(
    prices_total=3, prices_rejected=1, items_rejected=0, candidates=2, failed_batches=0
)


@pytest.mark.parametrize(
    ("copper", "text"),
    [
        (0, "0c"),
        (7, "7c"),
        (100, "1s 0c"),
        (1_234, "12s 34c"),
        (10_000, "1g 0s 0c"),
        (1_234_567, "123g 45s 67c"),
        (-150, "-1s 50c"),
    ],
)
def test_format_coins(copper, text):
    assert format_coins(copper) == text


@pytest.mark.parametrize(
    "evil",
    [
        "[click](https://evil.example)",
        "<img src=x onerror=alert(1)>",
        "a | b | c",
        "`code`",
        "![x](https://evil.example/x.png)",
    ],
)
def test_escape_markdown_neutralises_syntax(evil):
    out = escape_markdown(evil)
    for ch in "[]()<>|`!":
        # Jedes Sonderzeichen muss escaped sein (vorangestellter Backslash).
        idx = [i for i, c in enumerate(out) if c == ch]
        assert all(out[i - 1] == "\\" for i in idx)


def _positions(cfg, names):
    prices = [make_price(i, bid=10_000, ask=15_000 + i) for i in range(1, len(names) + 1)]
    items = {i: make_item(i, name=n) for i, n in enumerate(names, 1)}
    return finalize(preselect(prices, cfg), items, cfg)


def test_markdown_table(cfg):
    positions = _positions(cfg, ["Glob of Ectoplasm", "Mystic Coin"])
    md = to_markdown(positions, generated_at=NOW, budget_copper=cfg.budget_copper, stats=STATS)
    assert md.startswith("# Einkaufsliste – 2026-11-01")
    assert "Budget: 200g 0s 0c" in md
    assert "Orderbuch-Tiefe" in md
    rows = [line for line in md.splitlines() if line.startswith("| ") and "Item" not in line]
    assert len(rows) == 2
    assert "Mystic Coin" in rows[0]  # höherer Verkaufspreis → höherer Score
    assert "`[&AgGpTAAA]`" in rows[0]
    assert "1g 0s 1c" in rows[0]  # Kaufgebot = 1 g + 1 c
    assert "**Summe:**" in md


def test_markdown_escapes_item_names(cfg):
    positions = _positions(cfg, ["Evil | [x](https://evil.example) <b>"])
    md = to_markdown(positions, generated_at=NOW, budget_copper=cfg.budget_copper, stats=STATS)
    row = next(line for line in md.splitlines() if "Evil" in line)
    assert row.count(" | ") == 10  # 11 Spalten → 10 innere Trenner, unverändert
    assert "](https" not in row
    assert "<b>" not in row


def test_markdown_empty_list(cfg):
    md = to_markdown([], generated_at=NOW, budget_copper=cfg.budget_copper, stats=STATS)
    assert "kein Item" in md


def test_json_output(cfg):
    positions = _positions(cfg, ["Glob of Ectoplasm"])
    data = json.loads(
        to_json(positions, generated_at=NOW, budget_copper=cfg.budget_copper, stats=STATS)
    )
    assert data["schema_version"] == 1
    assert data["generated_at"] == "2026-11-01T04:23:00Z"
    assert data["volume_source"] == "orderbook_depth"
    [p] = data["positions"]
    assert p["rank"] == 1
    assert p["name"] == "Glob of Ectoplasm"
    assert p["buy_price"] == 10_001
    assert p["quantity"] * p["buy_price"] == p["invest"]
    assert p["risk"] in {"green", "yellow", "red"}
