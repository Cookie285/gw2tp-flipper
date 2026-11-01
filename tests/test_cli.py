"""End-to-End: kompletter Lauf gegen eine simulierte API (kein Netzwerk)."""

import json
from datetime import UTC, datetime
from urllib.parse import parse_qs, urlsplit

import pytest

from gw2tp.__main__ import RunError, run, write_outputs

from .conftest import FakeOpener, raw_item, raw_price

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
