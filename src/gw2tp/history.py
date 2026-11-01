"""Preis-Snapshots: Speichern, Laden, Kennzahlen (Volumen, Volatilität, Trend) und Verdichtung.

Ablage im Branch ``data``:

* ``snapshots/YYYY-MM-DD/HHMM.json.gz``: ein stündlicher Snapshot (UTC)
* ``daily/YYYY-MM-DD.json.gz``: Tageswerte, verdichtet aus den Stunden-Snapshots

**Volumenschätzung:** Zwischen zwei aufeinanderfolgenden Snapshots gilt
* Rückgang der Angebotsmenge (``sells.quantity``) ≈ Sofortkäufe, füllt also unsere Verkaufsangebote,
* Rückgang der Nachfragemenge (``buys.quantity``) ≈ Sofortverkäufe, füllt also unsere Kaufgebote.

Neue Orders verdecken Umsätze, Stornierungen täuschen welche vor. Bei stündlicher Auflösung ist das
eine grobe, eher vorsichtige Schätzung. Als Tagesvolumen zählt die kleinere der beiden Seiten,
denn ein Flip braucht beide.
"""

from __future__ import annotations

import gzip
import io
import itertools
import json
import logging
import math
import re
import statistics
from collections import defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

from .config import History
from .models import Price, ValidationError, item_id

log = logging.getLogger(__name__)

SCHEMA_VERSION = 1
FIELDS = ["id", "bp", "bq", "sp", "sq"]
MAX_SNAPSHOT_BYTES = 5 * 1024 * 1024  # entpackt; Schutz vor gzip-Bomben
MAX_ROWS = 5_000
SNAPSHOT_DIR = "snapshots"
DAILY_DIR = "daily"
SNAPSHOT_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})/(\d{2})(\d{2})\.json\.gz$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
SECONDS_PER_DAY = 86_400


@dataclass(frozen=True, slots=True)
class Snapshot:
    taken_at: datetime
    prices: dict[int, Price]


@dataclass(frozen=True, slots=True)
class MarketStats:
    samples: int
    coverage_hours: float
    daily_bought: int  # Rückgang der Nachfrage pro Tag → füllt Kaufgebote
    daily_sold: int  # Rückgang des Angebots pro Tag → füllt Verkaufsangebote
    price_cv: float | None
    trend: float | None  # relative Steigung der Tagesmediane pro Tag (−0,02 = −2 %/Tag)
    trend_days: int

    @property
    def daily_volume(self) -> int:
        return min(self.daily_bought, self.daily_sold)


# --- Kodierung ----------------------------------------------------------------------------


def snapshot_relpath(taken_at: datetime) -> str:
    t = taken_at.astimezone(UTC)
    return f"{SNAPSHOT_DIR}/{t:%Y-%m-%d}/{t:%H%M}.json.gz"


def _gzip_json(data: Any) -> bytes:
    raw = json.dumps(data, separators=(",", ":"), ensure_ascii=True).encode()
    return gzip.compress(raw, compresslevel=9, mtime=0)  # mtime=0 → reproduzierbar


def _gunzip_json(blob: bytes) -> Any:
    try:
        with gzip.GzipFile(fileobj=io.BytesIO(blob)) as fh:
            raw = fh.read(MAX_SNAPSHOT_BYTES + 1)
    except (OSError, EOFError) as exc:
        raise ValidationError(f"kein gültiges gzip: {exc}") from None
    if len(raw) > MAX_SNAPSHOT_BYTES:
        raise ValidationError("entpackt zu groß")
    try:
        return json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise ValidationError("kein gültiges JSON") from None


def encode_snapshot(taken_at: datetime, prices: Iterable[Price]) -> bytes:
    rows = [
        [p.id, p.buys.unit_price, p.buys.quantity, p.sells.unit_price, p.sells.quantity]
        for p in sorted(prices, key=lambda p: p.id)
    ]
    return _gzip_json(
        {
            "schema_version": SCHEMA_VERSION,
            "taken_at": taken_at.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "fields": FIELDS,
            "rows": rows,
        }
    )


def _parse_time(value: Any) -> datetime:
    if not isinstance(value, str) or not re.fullmatch(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", value
    ):
        raise ValidationError("taken_at ungültig")
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)


def decode_snapshot(blob: bytes) -> Snapshot:
    data = _gunzip_json(blob)
    if not isinstance(data, dict) or data.get("schema_version") != SCHEMA_VERSION:
        raise ValidationError("unbekanntes Snapshot-Format")
    if data.get("fields") != FIELDS:
        raise ValidationError("unerwartete Felder")
    rows = data.get("rows")
    if not isinstance(rows, list) or len(rows) > MAX_ROWS:
        raise ValidationError("rows ungültig")
    prices: dict[int, Price] = {}
    for row in rows:
        try:
            if not isinstance(row, list) or len(row) != len(FIELDS):
                raise ValidationError("Zeile ungültig")
            raw = {
                "id": row[0],
                "buys": {"unit_price": row[1], "quantity": row[2]},
                "sells": {"unit_price": row[3], "quantity": row[4]},
            }
            price = Price.parse(raw)
        except ValidationError:
            continue
        prices[price.id] = price
    return Snapshot(taken_at=_parse_time(data.get("taken_at")), prices=prices)


# --- Laden --------------------------------------------------------------------------------


def _safe_files(directory: Path) -> list[Path]:
    """Reguläre Dateien eines Verzeichnisses, ohne Symlinks zu folgen."""
    if not directory.is_dir() or directory.is_symlink():
        return []
    return sorted(p for p in directory.iterdir() if p.is_file() and not p.is_symlink())


def snapshot_files(root: Path, first_day: date, last_day: date) -> list[tuple[str, Path]]:
    """(relativer Pfad, Datei) aller Snapshot-Dateien zwischen ``first_day`` und ``last_day``."""
    base = root / SNAPSHOT_DIR
    if not base.is_dir() or base.is_symlink():
        return []
    result = []
    for day_dir in sorted(base.iterdir()):
        if not DATE_RE.fullmatch(day_dir.name) or day_dir.is_symlink():
            continue
        try:
            day = date.fromisoformat(day_dir.name)
        except ValueError:
            continue
        if not first_day <= day <= last_day:
            continue
        for f in _safe_files(day_dir):
            rel = f"{day_dir.name}/{f.name}"
            if SNAPSHOT_RE.fullmatch(rel):
                result.append((f"{SNAPSHOT_DIR}/{rel}", f))
    return result


def load_snapshots(root: Path, now: datetime, window_days: int) -> list[Snapshot]:
    """Snapshots der letzten ``window_days`` Tage, nach Zeit sortiert; defekte Dateien werden
    übersprungen."""
    start = now - timedelta(days=window_days)
    snaps = []
    for rel, path in snapshot_files(root, start.date(), now.date()):
        try:
            if path.stat().st_size > MAX_SNAPSHOT_BYTES:
                raise ValidationError("Datei zu groß")
            snap = decode_snapshot(path.read_bytes())
        except (OSError, ValidationError) as exc:
            log.warning("Snapshot %s übersprungen: %s", rel, exc)
            continue
        if start <= snap.taken_at <= now:
            snaps.append(snap)
    snaps.sort(key=lambda s: s.taken_at)
    return snaps


# --- Kennzahlen ---------------------------------------------------------------------------


def _cv(values: Sequence[int]) -> float | None:
    if len(values) < 2:
        return None
    mean = statistics.fmean(values)
    if mean <= 0:
        return None
    return statistics.pstdev(values) / mean


def _relative_slope(points: Sequence[tuple[float, float]]) -> float | None:
    """Kleinste-Quadrate-Steigung von (x, y), geteilt durch den Mittelwert von y."""
    if len(points) < 2:
        return None
    xs = [x for x, _ in points]
    ys = [y for _, y in points]
    mx, my = statistics.fmean(xs), statistics.fmean(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    if sxx == 0 or my <= 0:
        return None
    slope = sum((x - mx) * (y - my) for x, y in points) / sxx
    return slope / my


def order_flow(
    series: Sequence[tuple[datetime, Price]], max_gap_s: float
) -> tuple[int, int, float]:
    """(Summe Nachfragerückgang, Summe Angebotsrückgang, abgedeckte Sekunden)."""
    bought = sold = 0
    covered = 0.0
    for (t0, p0), (t1, p1) in itertools.pairwise(series):
        dt = (t1 - t0).total_seconds()
        if not 0 < dt <= max_gap_s:
            continue
        covered += dt
        bought += max(0, p0.buys.quantity - p1.buys.quantity)
        sold += max(0, p0.sells.quantity - p1.sells.quantity)
    return bought, sold, covered


def compute_stats(series: Sequence[tuple[datetime, Price]], cfg: History) -> MarketStats:
    series = sorted(series, key=lambda tp: tp[0])
    bought, sold, covered = order_flow(series, cfg.max_gap_hours * 3600)
    per_day = SECONDS_PER_DAY / covered if covered > 0 else 0.0

    both = [p for _, p in series if p.buys.unit_price > 0 and p.sells.unit_price > 0]
    cvs = [_cv([p.buys.unit_price for p in both]), _cv([p.sells.unit_price for p in both])]
    known = [c for c in cvs if c is not None]
    price_cv = max(known) if len(known) == 2 else None

    by_day: dict[date, list[float]] = defaultdict(list)
    for t, p in series:
        if p.buys.unit_price > 0 and p.sells.unit_price > 0:
            by_day[t.date()].append((p.buys.unit_price + p.sells.unit_price) / 2)
    medians = [
        (float(d.toordinal()), statistics.median(v))
        for d, v in sorted(by_day.items())
        if len(v) >= cfg.min_samples_per_day
    ]
    trend = _relative_slope(medians) if len(medians) >= cfg.min_trend_days else None

    return MarketStats(
        samples=len(series),
        coverage_hours=covered / 3600,
        daily_bought=math.floor(bought * per_day),
        daily_sold=math.floor(sold * per_day),
        price_cv=price_cv,
        trend=trend,
        trend_days=len(medians),
    )


def build_stats(snapshots: Sequence[Snapshot], cfg: History) -> dict[int, MarketStats]:
    series: dict[int, list[tuple[datetime, Price]]] = defaultdict(list)
    for snap in snapshots:
        for pid, price in snap.prices.items():
            series[pid].append((snap.taken_at, price))
    return {pid: compute_stats(s, cfg) for pid, s in series.items()}


def usable_stats(stats: dict[int, MarketStats], cfg: History) -> dict[int, MarketStats]:
    """Nur Items mit ausreichend abgedeckter Historie."""
    return {pid: s for pid, s in stats.items() if s.coverage_hours >= cfg.min_history_hours}


# --- Verdichtung --------------------------------------------------------------------------

DAILY_FIELDS = [
    "id",
    "n",
    "bp_med",
    "sp_med",
    "bp_min",
    "bp_max",
    "sp_min",
    "sp_max",
    "bought",
    "sold",
    "covered_s",
]


def encode_daily(day: date, snapshots: Sequence[Snapshot], cfg: History) -> bytes:
    series: dict[int, list[tuple[datetime, Price]]] = defaultdict(list)
    for snap in snapshots:
        for pid, price in snap.prices.items():
            series[pid].append((snap.taken_at, price))
    rows = []
    for pid in sorted(series):
        s = sorted(series[pid], key=lambda tp: tp[0])
        bps = [p.buys.unit_price for _, p in s]
        sps = [p.sells.unit_price for _, p in s]
        bought, sold, covered = order_flow(s, cfg.max_gap_hours * 3600)
        rows.append(
            [
                pid,
                len(s),
                int(statistics.median(bps)),
                int(statistics.median(sps)),
                min(bps),
                max(bps),
                min(sps),
                max(sps),
                bought,
                sold,
                int(covered),
            ]
        )
    return _gzip_json(
        {
            "schema_version": SCHEMA_VERSION,
            "date": day.isoformat(),
            "fields": DAILY_FIELDS,
            "rows": rows,
        }
    )


@dataclass(frozen=True, slots=True)
class Compaction:
    daily_files: dict[str, bytes]  # relativer Pfad → Inhalt
    removed: list[str]  # relative Pfade der verdichteten Stunden-Snapshots


def compact(root: Path, today: date, cfg: History, max_days: int = 7) -> Compaction:
    """Stunden-Snapshots, die älter als ``retention_days`` sind, zu Tageswerten verdichten."""
    cutoff = today - timedelta(days=cfg.retention_days)
    files = snapshot_files(root, date(2000, 1, 1), cutoff - timedelta(days=1))
    by_day: dict[str, list[tuple[str, Path]]] = defaultdict(list)
    for rel, path in files:
        by_day[rel.split("/")[1]].append((rel, path))

    daily: dict[str, bytes] = {}
    removed: list[str] = []
    for day_name in sorted(by_day)[:max_days]:
        snaps = []
        for _, path in by_day[day_name]:
            try:
                snaps.append(decode_snapshot(path.read_bytes()))
            except (OSError, ValidationError) as exc:
                log.warning("Beim Verdichten übersprungen: %s (%s)", path.name, exc)
        snaps.sort(key=lambda s: s.taken_at)
        daily[f"{DAILY_DIR}/{day_name}.json.gz"] = encode_daily(
            date.fromisoformat(day_name), snaps, cfg
        )
        removed.extend(rel for rel, _ in by_day[day_name])
    return Compaction(daily_files=daily, removed=removed)


# --- Universum ----------------------------------------------------------------------------

UNIVERSE_FILE = "universe.json"
MAX_UNIVERSE_BYTES = 256 * 1024
MAX_UNIVERSE_IDS = 2_500


def encode_universe(ids: Sequence[int], generated_at: datetime) -> str:
    return (
        json.dumps(
            {
                "schema_version": SCHEMA_VERSION,
                "generated_at": generated_at.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "ids": list(ids),
            },
            separators=(",", ":"),
        )
        + "\n"
    )


def load_universe(path: Path) -> list[int] | None:
    """Universum aus dem Branch ``data`` lesen. ``None``, wenn nicht vorhanden oder ungültig."""
    try:
        if not path.is_file() or path.is_symlink() or path.stat().st_size > MAX_UNIVERSE_BYTES:
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or data.get("schema_version") != SCHEMA_VERSION:
            return None
        ids = data.get("ids")
        if not isinstance(ids, list) or not 0 < len(ids) <= MAX_UNIVERSE_IDS:
            return None
        return list(dict.fromkeys(item_id(i) for i in ids))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValidationError) as exc:
        log.warning("universe.json unbrauchbar: %s", exc)
        return None
