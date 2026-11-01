"""Python (analyze.plan) und Dashboard (web/plan.js) müssen für jedes Budget gleich rechnen."""

from __future__ import annotations

import json
import os
import random
import shutil
import subprocess
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from gw2tp import analyze
from gw2tp.fees import COPPER_PER_GOLD
from gw2tp.history import build_stats, usable_stats
from gw2tp.models import Price, Quote
from gw2tp.report import MODE_HISTORY, MODE_ORDERBOOK, RunStats, to_json

from .conftest import hourly_snapshots, make_item

ROOT = Path(__file__).resolve().parents[1]
NODE = shutil.which("node")

pytestmark = pytest.mark.skipif(
    NODE is None and not os.environ.get("REQUIRE_NODE"), reason="node nicht installiert"
)

BUDGETS = [5, 20, 77.5, 200, 1_000, 25_000]


def _market(seed: int, n: int = 300) -> list[Price]:
    rng = random.Random(seed)
    prices = []
    for i in range(1, n + 1):
        bid = rng.choice(
            [rng.randint(100, 2_000), rng.randint(2_000, 50_000), rng.randint(50_000, 400_000)]
        )
        ask = int(bid * rng.uniform(1.05, 2.2))
        prices.append(
            Price(i, Quote(bid, rng.randint(300, 300_000)), Quote(ask, rng.randint(300, 300_000)))
        )
    return prices


def _history(prices: list[Price], seed: int):
    rng = random.Random(seed)
    now = datetime(2026, 11, 20, 4, 0, tzinfo=UTC)
    drops = {
        p.id: (
            rng.randint(0, 400),
            rng.randint(0, 400),
            rng.uniform(0, 0.08),
            rng.uniform(-0.03, 0.03),
        )
        for p in prices
    }

    def at(h):
        out = []
        for p in prices:
            bd, sd, noise, trend = drops[p.id]
            f = (1 + trend * h / 24) * (1 + noise * (1 if h % 2 else -1))
            out.append(
                Price(
                    p.id,
                    Quote(max(1, int(p.buys.unit_price * f)), max(0, 10**6 - bd * h)),
                    Quote(max(2, int(p.sells.unit_price * f)), max(0, 10**6 - sd * h)),
                )
            )
        return out

    return hourly_snapshots(now - timedelta(days=5), 24 * 5, at)


def _run_node(path: Path, budget: int) -> dict:
    assert NODE is not None, "REQUIRE_NODE gesetzt, aber node fehlt"
    out = subprocess.run(
        [NODE, str(ROOT / "tests/js/parity.mjs"), str(path), str(budget)],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(out.stdout)


@pytest.mark.parametrize("history", [False, True], ids=["orderbuch", "historie"])
@pytest.mark.parametrize("seed", [1, 2, 3])
def test_python_and_js_plan_identically(tmp_path, cfg, seed, history):
    prices = _market(seed)
    stats = (
        usable_stats(build_stats(_history(prices, seed), cfg.history), cfg.history)
        if history
        else None
    )
    pool = analyze.attach_items(
        analyze.build_pool(prices, cfg, stats),
        {p.id: make_item(p.id, name=f"Item {p.id}") for p in prices},
        cfg.filters,
    )
    assert len(pool) > 20
    positions = analyze.plan(pool, cfg)
    path = tmp_path / "shopping-list.json"
    path.write_text(
        to_json(
            positions,
            generated_at=datetime(2026, 11, 20, 4, 23, tzinfo=UTC),
            budget_copper=cfg.budget_copper,
            stats=RunStats(
                len(prices), 0, 0, len(pool), 0, mode=MODE_HISTORY if history else MODE_ORDERBOOK
            ),
            pool=pool,
            cfg=cfg,
        ),
        encoding="utf-8",
    )

    for gold in BUDGETS:
        budget = round(gold * COPPER_PER_GOLD)
        py = [
            {
                "id": p.candidate.item_id,
                "quantity": p.quantity,
                "expected_profit": p.expected_profit,
                "invest": p.invest,
                "risk": p.risk.value,
            }
            for p in analyze.plan(pool, cfg, budget)
        ]
        js = _run_node(path, budget)
        assert js["rejected"] == 0
        assert [{k: v for k, v in p.items() if k != "score"} for p in js["positions"]] == py, gold
        py_scores = [p.score for p in analyze.plan(pool, cfg, budget)]
        assert [p["score"] for p in js["positions"]] == pytest.approx(py_scores, rel=1e-12)
