"""End-to-End: kompletter Lauf gegen eine simulierte API (kein Netzwerk)."""

import json
from datetime import UTC, datetime, timedelta
from urllib.parse import parse_qs, urlsplit

import pytest

from gw2tp import __main__ as cli
from gw2tp import history
from gw2tp.__main__ import RunError, run, write_outputs
from gw2tp.models import Price

from .conftest import FakeOpener, hourly_snapshots, raw_item, raw_price

PRICES = {
    1: raw_price(1, bid=10_000, ask=15_000),  # guter Flip
    2: raw_price(2, bid=10_000, ask=15_000),  # gebunden → raus
    3: raw_price(3, bid=10_000, ask=10_500),  # ROI zu klein
    4: raw_price(4, bid=50, ask=200),  # zu billig
    5: raw_price(5, bid=20_000, ask=30_000, demand=100),  # zu dünn
    6: raw_price(6, bid=5_000, ask=8_000),  # guter Flip
    7: {"id": 7, "buys": "kaputt"},  # ungültig → verworfen
}
ITEMS = {
    1: raw_item(1, "Glob of Ectoplasm"),
    2: raw_item(2, "Bound Thing", flags=["AccountBound"]),
    6: raw_item(6, "Mystic Coin"),
}


def api(req):
    url = urlsplit(req.full_url)
    assert url.hostname == "api.guildwars2.com"
    query = parse_qs(url.query)
    if url.path == "/v2/commerce/prices" and not query:
        return (200, sorted(PRICES))
    ids = [int(x) for x in query["ids"][0].split(",")]
    table = PRICES if url.path == "/v2/commerce/prices" else ITEMS
    found = [table[i] for i in ids if i in table]
    return (200 if len(found) == len(ids) else 206, found)


def test_full_run(make_client, cfg, tmp_path):
    client = make_client(FakeOpener(handler=api))
    result = run(client, cfg)
    # Item 6: 39 Stück × 17s 98c > Item 1: 19 Stück × 27s 49c
    assert [p.candidate.item_id for p in result.positions] == [6, 1]
    assert result.stats.prices_rejected == 1
    assert result.stats.prices_total == 6

    now = datetime(2026, 11, 1, 4, 23, tzinfo=UTC)
    write_outputs(result, tmp_path, cfg, now)
    md = (tmp_path / "shopping-list.md").read_text(encoding="utf-8")
    data = json.loads((tmp_path / "shopping-list.json").read_text(encoding="utf-8"))
    assert "Glob of Ectoplasm" in md and "Mystic Coin" in md
    assert "Bound Thing" not in md
    assert [p["id"] for p in data["positions"]] == [6, 1]


def test_aborts_when_too_many_batches_fail(make_client, cfg):
    def flaky(req):
        if "ids=" in req.full_url:
            return (503, {})
        return (200, list(range(1, 1001)))

    client = make_client(FakeOpener(handler=flaky), max_retries=0)
    with pytest.raises(RunError, match="fehlgeschlagen"):
        run(client, cfg)


def test_aborts_on_invalid_id_list(make_client, cfg):
    with pytest.raises(RunError):
        run(make_client(FakeOpener([(200, {"not": "a list"})])), cfg)


# --- Phase 2: Historie, Snapshots, Verdichtung ---------------------------------------------


NOW = datetime(2026, 11, 20, 4, 23, tzinfo=UTC)


def _history_for(ids, hours=48, supply_drop=50, demand_drop=50):
    def prices(h):
        return [
            Price.parse(
                raw_price(
                    i,
                    bid=PRICES[i]["buys"]["unit_price"],
                    ask=PRICES[i]["sells"]["unit_price"],
                    demand=100_000 - demand_drop * h,
                    supply=100_000 - supply_drop * h,
                )
            )
            for i in ids
        ]

    return hourly_snapshots(NOW - timedelta(hours=hours), hours, prices)


def test_run_in_history_mode(make_client, cfg):
    # Nur Item 1 hat Historie → Item 6 fällt im Historien-Modus heraus.
    result = run(make_client(FakeOpener(handler=api)), cfg, _history_for([1]))
    assert result.stats.mode == "snapshots"
    assert result.stats.history_items == 1
    [pos] = result.positions
    assert pos.candidate.item_id == 1
    assert pos.stats.daily_volume == 1_200  # 50/h × 24
    assert result.universe  # Universum wird mitbestimmt


def test_run_falls_back_to_orderbook_without_enough_history(make_client, cfg):
    result = run(make_client(FakeOpener(handler=api)), cfg, _history_for([1], hours=10))
    assert result.stats.mode == "orderbook_depth"
    assert [p.candidate.item_id for p in result.positions] == [6, 1]


def test_markdown_shows_history_columns(make_client, cfg, tmp_path):
    result = run(make_client(FakeOpener(handler=api)), cfg, _history_for([1, 6]))
    write_outputs(result, tmp_path, cfg, NOW)
    md = (tmp_path / "shopping-list.md").read_text(encoding="utf-8")
    assert "Vol./Tag | Trend |" in md
    assert "stündlichen Snapshots" in md
    data = json.loads((tmp_path / "shopping-list.json").read_text(encoding="utf-8"))
    assert data["volume_source"] == "snapshots"
    assert all(p["daily_volume"] == 1_200 for p in data["positions"])
    assert history.load_universe(tmp_path / "universe.json") == result.universe


def test_snapshot_bootstraps_universe_without_data_dir(make_client, cfg, tmp_path):
    client = make_client(FakeOpener(handler=api))
    path = cli.take_snapshot(client, cfg, None, tmp_path, NOW)
    assert path == tmp_path / "snapshots/2026-11-20/0423.json.gz"
    snap = history.decode_snapshot(path.read_bytes())
    # Universum: Tiefe ≥ 200, Kaufpreis ≥ 1 s, ROI ≥ 0 → 1, 2, 6 (3: Spread zu klein)
    assert sorted(snap.prices) == [1, 2, 6]


def test_snapshot_uses_existing_universe(make_client, cfg, tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "universe.json").write_text(history.encode_universe([6, 3], NOW))
    opener = FakeOpener(handler=api)
    path = cli.take_snapshot(make_client(opener), cfg, data_dir, tmp_path / "out", NOW)
    assert sorted(history.decode_snapshot(path.read_bytes()).prices) == [3, 6]
    assert len(opener.requests) == 1  # nur ein Preis-Block, kein Komplettabruf


def test_main_analyze_with_data_dir(monkeypatch, make_client, tmp_path):
    data_dir = tmp_path / "data"
    for snap in _history_for([1, 6]):
        p = data_dir / history.snapshot_relpath(snap.taken_at)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(history.encode_snapshot(snap.taken_at, snap.prices.values()))
    old = data_dir / "snapshots/2026-10-01/0017.json.gz"
    old.parent.mkdir(parents=True)
    old.write_bytes(history.encode_snapshot(datetime(2026, 10, 1, 0, 17, tzinfo=UTC), []))

    monkeypatch.setattr(cli, "_client", lambda cfg: make_client(FakeOpener(handler=api)))

    class FixedDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return NOW

    monkeypatch.setattr(cli, "datetime", FixedDatetime)
    out = tmp_path / "out"
    rc = cli.main(
        ["analyze", "--config", "config.yaml", "--data-dir", str(data_dir), "--out", str(out)]
    )
    assert rc == 0
    names = sorted(str(p.relative_to(out)) for p in out.rglob("*") if p.is_file())
    assert names == [
        "archive.json",
        "daily/2026-10-01.json.gz",
        "evaluation.md",
        "remove.txt",
        "shopping-list.json",
        "shopping-list.md",
        "universe.json",
    ]
    assert (out / "remove.txt").read_text() == "snapshots/2026-10-01/0017.json.gz\n"


def test_main_snapshot_without_data_branch(monkeypatch, make_client, tmp_path):
    monkeypatch.setattr(cli, "_client", lambda cfg: make_client(FakeOpener(handler=api)))
    rc = cli.main(
        [
            "snapshot",
            "--config",
            "config.yaml",
            "--data-dir",
            str(tmp_path / "missing"),
            "--out",
            str(tmp_path / "out"),
        ]
    )
    assert rc == 0
    assert len(list((tmp_path / "out/snapshots").rglob("*.json.gz"))) == 1
