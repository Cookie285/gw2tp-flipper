from __future__ import annotations

import io
import json
import urllib.error
from email.message import Message
from typing import Any

import pytest

from gw2tp.config import Config
from gw2tp.fetch import Gw2Client
from gw2tp.models import Item, Price, Quote


def make_price(
    item_id: int = 1, bid: int = 1000, ask: int = 1500, demand: int = 10_000, supply: int = 10_000
) -> Price:
    return Price(id=item_id, buys=Quote(bid, demand), sells=Quote(ask, supply))


def raw_price(
    item_id: int = 1, bid: int = 1000, ask: int = 1500, demand: int = 10_000, supply: int = 10_000
) -> dict[str, Any]:
    return {
        "id": item_id,
        "whitelisted": False,
        "buys": {"quantity": demand, "unit_price": bid},
        "sells": {"quantity": supply, "unit_price": ask},
    }


def raw_item(item_id: int = 1, name: str = "Glob of Ectoplasm", flags=None) -> dict[str, Any]:
    return {
        "id": item_id,
        "name": name,
        "type": "CraftingMaterial",
        "rarity": "Exotic",
        "flags": flags if flags is not None else [],
        "chat_link": "[&AgGpTAAA]",
        "icon": f"https://render.guildwars2.com/file/ABCDEF/{item_id}.png",
    }


def make_item(item_id: int = 1, name: str = "Glob of Ectoplasm", flags=()) -> Item:
    return Item.parse(raw_item(item_id, name, list(flags)))


class FakeResponse:
    def __init__(self, body: bytes, url: str, status: int = 200):
        self._body = io.BytesIO(body)
        self._url = url
        self.status = status

    def read(self, n: int = -1) -> bytes:
        return self._body.read(n)

    def geturl(self) -> str:
        return self._url

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class FakeOpener:
    """Antwortet der Reihe nach mit vorgegebenen Antworten oder ruft einen Handler auf."""

    def __init__(self, responses=None, handler=None):
        self.responses = list(responses or [])
        self.handler = handler
        self.requests: list[Any] = []

    def open(self, req, timeout):
        self.requests.append(req)
        assert timeout > 0
        spec = self.handler(req) if self.handler else self.responses.pop(0)
        if isinstance(spec, BaseException):
            raise spec
        status, payload, *rest = spec
        headers = rest[0] if rest else {}
        body = payload if isinstance(payload, bytes) else json.dumps(payload).encode()
        if status >= 400:
            hdrs = Message()
            for k, v in headers.items():
                hdrs[k] = v
            raise urllib.error.HTTPError(req.full_url, status, "err", hdrs, io.BytesIO(body))
        return FakeResponse(body, headers.get("_url", req.full_url), status)


class FakeTime:
    def __init__(self):
        self.now = 0.0
        self.sleeps: list[float] = []

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.now += seconds

    def clock(self) -> float:
        return self.now


@pytest.fixture
def fake_time() -> FakeTime:
    return FakeTime()


@pytest.fixture
def make_client(fake_time):
    def _make(opener: FakeOpener, **kwargs) -> Gw2Client:
        return Gw2Client(
            opener=opener,
            sleep=fake_time.sleep,
            clock=fake_time.clock,
            jitter=lambda: 0.0,
            **kwargs,
        )

    return _make


@pytest.fixture
def cfg() -> Config:
    return Config()


def make_stats(
    bought: int = 10_000,
    sold: int = 10_000,
    cv: float | None = 0.02,
    trend: float | None = 0.0,
    coverage_hours: float = 168.0,
):
    from gw2tp.history import MarketStats

    return MarketStats(
        samples=168,
        coverage_hours=coverage_hours,
        daily_bought=bought,
        daily_sold=sold,
        price_cv=cv,
        trend=trend,
        trend_days=7 if trend is not None else 0,
    )


def hourly_snapshots(start, hours: int, price_fn):
    """Snapshots im Stundentakt; ``price_fn(hour_index) -> list[Price]``."""
    from datetime import timedelta

    from gw2tp.history import Snapshot

    return [
        Snapshot(
            taken_at=start + timedelta(hours=h),
            prices={p.id: p for p in price_fn(h)},
        )
        for h in range(hours)
    ]
