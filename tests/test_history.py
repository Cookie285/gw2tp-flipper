import gzip
import json
import os
from datetime import UTC, date, datetime, timedelta

import pytest

from gw2tp import history
from gw2tp.config import History
from gw2tp.history import (
    build_stats,
    compact,
    compute_stats,
    decode_snapshot,
    encode_snapshot,
    encode_universe,
    load_snapshots,
    load_universe,
    order_flow,
    snapshot_relpath,
    usable_stats,
)
from gw2tp.models import ValidationError

from .conftest import hourly_snapshots, make_price

H = History()
T0 = datetime(2026, 11, 1, 0, 17, tzinfo=UTC)


def series_of(snaps, pid=1):
    return [(s.taken_at, s.prices[pid]) for s in snaps if pid in s.prices]


# --- Kodierung ----------------------------------------------------------------------------


def test_snapshot_relpath():
    assert snapshot_relpath(datetime(2026, 11, 1, 5, 17, 3, tzinfo=UTC)) == (
        "snapshots/2026-11-01/0517.json.gz"
    )


def test_snapshot_roundtrip_and_reproducible():
    prices = [make_price(2, bid=10, ask=20), make_price(1, bid=100, ask=150, demand=5, supply=6)]
    blob = encode_snapshot(T0, prices)
    assert blob == encode_snapshot(T0, list(reversed(prices)))  # sortiert, mtime=0
    snap = decode_snapshot(blob)
    assert snap.taken_at == T0
    assert snap.prices[1] == prices[1]
    assert snap.prices[2] == prices[0]


def _blob(data) -> bytes:
    return gzip.compress(json.dumps(data).encode(), mtime=0)


def test_invalid_rows_dropped():
    blob = _blob(
        {
            "schema_version": 1,
            "taken_at": "2026-11-01T00:17:00Z",
            "fields": history.FIELDS,
            "rows": [[1, 10, 1, 20, 1], [2, "x", 1, 20, 1], [3, 10], "junk", [-4, 1, 1, 1, 1]],
        }
    )
    assert list(decode_snapshot(blob).prices) == [1]


@pytest.mark.parametrize(
    "data",
    [
        {
            "schema_version": 2,
            "taken_at": "2026-11-01T00:17:00Z",
            "fields": history.FIELDS,
            "rows": [],
        },
        {"schema_version": 1, "taken_at": "gestern", "fields": history.FIELDS, "rows": []},
        {"schema_version": 1, "taken_at": "2026-11-01T00:17:00Z", "fields": ["id"], "rows": []},
        {
            "schema_version": 1,
            "taken_at": "2026-11-01T00:17:00Z",
            "fields": history.FIELDS,
            "rows": {},
        },
        [1, 2, 3],
    ],
)
def test_invalid_snapshot_structure_rejected(data):
    with pytest.raises(ValidationError):
        decode_snapshot(_blob(data))


def test_not_gzip_rejected():
    with pytest.raises(ValidationError, match="gzip"):
        decode_snapshot(b"not gzip at all")


def test_gzip_bomb_rejected(monkeypatch):
    monkeypatch.setattr(history, "MAX_SNAPSHOT_BYTES", 1_000)
    blob = gzip.compress(b" " * 100_000)
    with pytest.raises(ValidationError, match="zu groß"):
        decode_snapshot(blob)


# --- Laden --------------------------------------------------------------------------------


def _write(root, t, prices):
    path = root / snapshot_relpath(t)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(encode_snapshot(t, prices))
    return path


def test_load_snapshots_window_and_robustness(tmp_path):
    now = datetime(2026, 11, 10, 12, 0, tzinfo=UTC)
    _write(tmp_path, now - timedelta(days=8), [make_price(1)])  # außerhalb
    _write(tmp_path, now - timedelta(days=6), [make_price(1)])
    _write(tmp_path, now - timedelta(hours=1), [make_price(1)])
    _write(tmp_path, now + timedelta(hours=2), [make_price(1)])  # Zukunft
    bad = tmp_path / "snapshots/2026-11-10/0900.json.gz"
    bad.write_bytes(b"kaputt")
    (tmp_path / "snapshots/2026-11-10/notes.txt").write_text("x")
    (tmp_path / "snapshots/evil").mkdir()
    snaps = load_snapshots(tmp_path, now, 7)
    assert [s.taken_at for s in snaps] == [now - timedelta(days=6), now - timedelta(hours=1)]


def test_load_snapshots_ignores_symlinks(tmp_path):
    now = datetime(2026, 11, 10, 12, 0, tzinfo=UTC)
    real = _write(tmp_path / "elsewhere", now - timedelta(hours=1), [make_price(1)])
    day = tmp_path / "snapshots/2026-11-10"
    day.mkdir(parents=True)
    os.symlink(real, day / "1100.json.gz")
    assert load_snapshots(tmp_path, now, 7) == []


def test_load_snapshots_missing_dir(tmp_path):
    assert load_snapshots(tmp_path, T0, 7) == []


# --- Kennzahlen ---------------------------------------------------------------------------


def test_order_flow_counts_only_decreases_within_gap():
    t = T0
    p = lambda bq, sq: make_price(1, demand=bq, supply=sq)  # noqa: E731
    series = [
        (t, p(100, 100)),
        (t + timedelta(hours=1), p(90, 80)),  # −10 Nachfrage, −20 Angebot
        (t + timedelta(hours=2), p(120, 130)),  # Zuwächse zählen nicht
        (t + timedelta(hours=7), p(0, 0)),  # Lücke > 3 h → ignoriert
        (t + timedelta(hours=8), p(0, 0)),
    ]
    bought, sold, covered = order_flow(series, 3 * 3600)
    assert (bought, sold) == (10, 20)
    assert covered == 3 * 3600


def test_daily_volume_extrapolated_from_coverage():
    # 25 stündliche Snapshots (24 h Abdeckung): Angebot −10/h, Nachfrage −5/h
    snaps = hourly_snapshots(
        T0, 25, lambda h: [make_price(1, demand=10_000 - 5 * h, supply=10_000 - 10 * h)]
    )
    s = compute_stats(series_of(snaps), H)
    assert s.coverage_hours == pytest.approx(24)
    assert s.daily_sold == 240
    assert s.daily_bought == 120
    assert s.daily_volume == 120


def test_cv_zero_for_constant_prices_and_positive_otherwise():
    flat = hourly_snapshots(T0, 30, lambda h: [make_price(1, bid=1000, ask=1500)])
    assert compute_stats(series_of(flat), H).price_cv == pytest.approx(0.0)
    wobbly = hourly_snapshots(
        T0, 30, lambda h: [make_price(1, bid=1000 + (100 if h % 2 else 0), ask=1500)]
    )
    cv = compute_stats(series_of(wobbly), H).price_cv
    # Gebote 1000/1100 → σ = 50, Mittel 1050 → CV ≈ 4,8 %; das Maximum beider Seiten zählt
    assert cv == pytest.approx(50 / 1050)


def test_trend_from_daily_medians():
    # 5 Tage, Mittelpreis steigt pro Tag um 10c bei ~1000c Basis
    def prices(h):
        day = h // 24
        return [make_price(1, bid=950 + 10 * day, ask=1050 + 10 * day)]

    s = compute_stats(series_of(hourly_snapshots(T0, 24 * 5, prices)), H)
    assert s.trend_days == 5
    # Steigung 10c/Tag, Mittel der Tagesmediane 1020c
    assert s.trend == pytest.approx(10 / 1020)


def test_trend_unknown_with_too_few_days():
    s = compute_stats(series_of(hourly_snapshots(T0, 48, lambda h: [make_price(1)])), H)
    assert s.trend is None


def test_days_with_few_samples_ignored_for_trend():
    snaps = hourly_snapshots(T0, 24 * 3, lambda h: [make_price(1)])
    snaps = [s for s in snaps if s.taken_at.date() != date(2026, 11, 2) or s.taken_at.hour < 3]
    s = compute_stats(series_of(snaps), H)
    assert s.trend_days == 2
    assert s.trend is None


def test_build_and_usable_stats():
    snaps = hourly_snapshots(T0, 30, lambda h: [make_price(1), *([make_price(2)] if h < 5 else [])])
    stats = build_stats(snaps, H)
    assert set(stats) == {1, 2}
    assert set(usable_stats(stats, H)) == {1}  # Item 2 hat nur 4 h Abdeckung


# --- Verdichtung --------------------------------------------------------------------------


def test_compaction_of_old_snapshots(tmp_path):
    today = date(2026, 11, 20)
    old_day = datetime(2026, 11, 1, tzinfo=UTC)
    for h in range(3):
        _write(tmp_path, old_day + timedelta(hours=h), [make_price(1, supply=100 - h)])
    recent = _write(tmp_path, datetime(2026, 11, 15, tzinfo=UTC), [make_price(1)])

    c = compact(tmp_path, today, H)
    assert c.removed == [
        "snapshots/2026-11-01/0000.json.gz",
        "snapshots/2026-11-01/0100.json.gz",
        "snapshots/2026-11-01/0200.json.gz",
    ]
    assert list(c.daily_files) == ["daily/2026-11-01.json.gz"]
    assert recent.exists()

    daily = json.loads(gzip.decompress(c.daily_files["daily/2026-11-01.json.gz"]))
    assert daily["date"] == "2026-11-01"
    row = dict(zip(daily["fields"], daily["rows"][0], strict=True))
    assert row["id"] == 1 and row["n"] == 3 and row["sold"] == 2 and row["covered_s"] == 7200


def test_compaction_nothing_to_do(tmp_path):
    _write(tmp_path, datetime(2026, 11, 15, tzinfo=UTC), [make_price(1)])
    c = compact(tmp_path, date(2026, 11, 20), H)
    assert c.daily_files == {} and c.removed == []


def test_compaction_limited_per_run(tmp_path):
    for d in range(10):
        _write(tmp_path, datetime(2026, 10, 1 + d, tzinfo=UTC), [make_price(1)])
    c = compact(tmp_path, date(2026, 11, 20), H, max_days=3)
    assert len(c.daily_files) == 3


# --- Universum ----------------------------------------------------------------------------


def test_universe_roundtrip(tmp_path):
    path = tmp_path / "universe.json"
    path.write_text(encode_universe([3, 1, 2], T0))
    assert load_universe(path) == [3, 1, 2]


@pytest.mark.parametrize(
    "content",
    [
        "kaputt",
        "[]",
        '{"schema_version": 1, "ids": []}',
        '{"schema_version": 1, "ids": [1, "2"]}',
        '{"schema_version": 1, "ids": [0]}',
        '{"schema_version": 9, "ids": [1]}',
    ],
)
def test_invalid_universe_ignored(tmp_path, content):
    path = tmp_path / "universe.json"
    path.write_text(content)
    assert load_universe(path) is None


def test_universe_missing_or_symlink(tmp_path):
    assert load_universe(tmp_path / "nope.json") is None
    real = tmp_path / "real.json"
    real.write_text(encode_universe([1], T0))
    (tmp_path / "universe.json").symlink_to(real)
    assert load_universe(tmp_path / "universe.json") is None
