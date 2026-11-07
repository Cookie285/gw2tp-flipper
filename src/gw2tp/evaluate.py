"""Rückblick: Wie gut waren frühere Einkaufslisten?

Jede tägliche Liste wird als kompaktes Archiv (``lists/YYYY-MM-DD.json``) abgelegt. Zwei Tage
später wird jede Position gegen die stündlichen Snapshots geprüft:

* **ROI nach 24 h / 48 h:** Kauf zum geplanten Gebot, Verkauf zum dann niedrigsten Angebot − 1,
  nach Gebühren. Zeigt, ob der Spread gehalten hat.
* **Preis gehalten:** Lag das niedrigste Angebot nach 48 h noch höchstens 5 % unter dem
  geplanten Verkaufspreis?
* **Gebot überholt:** Bot jemand innerhalb von 24 h mehr als unser Gebot? Dann hätte das Gebot
  nachgezogen werden müssen.
* **Volumen-Treffer:** tatsächlich beobachtetes Tagesvolumen ÷ geschätztes Tagesvolumen.

Die Ergebnisse werden nach Ampel und nach Bereichen von ROI, Volatilität und Volumen gruppiert.
So lässt sich ablesen, welche Schwellwerte in ``config.yaml`` angepasst werden sollten.
Das ist eine Näherung: Ob ein Gebot wirklich gefüllt worden wäre, kann niemand wissen.
"""

from __future__ import annotations

import itertools
import json
import logging
import re
import statistics
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

from .analyze import FUNNEL_STEPS, Position
from .fees import FeeSchedule, net_profit
from .history import SECONDS_PER_DAY, Snapshot, order_flow
from .models import ValidationError, clean_text, item_id
from .report import MODE_HISTORY

log = logging.getLogger(__name__)

ARCHIVE_SCHEMA = 1
LISTS_DIR = "lists"
ARCHIVE_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})\.json$")
MAX_ARCHIVE_BYTES = 512 * 1024
HORIZONS_H = (24, 48)
TOLERANCE_H = 3  # Snapshot muss höchstens so weit vom Zielzeitpunkt entfernt sein
PRICE_HELD_SLACK = 0.05


# --- Archiv -------------------------------------------------------------------------------


def encode_archive(positions: Sequence[Position], generated_at: datetime, mode: str) -> str:
    """Kompaktes Archiv einer Liste (nur, was für die Auswertung nötig ist)."""
    rows = []
    for p in positions:
        st = p.stats
        rows.append(
            {
                "id": p.candidate.item_id,
                "name": p.item.name if p.item else None,
                "buy_price": p.candidate.buy_price,
                "sell_price": p.candidate.sell_price,
                "quantity": p.quantity,
                "roi": round(p.candidate.roi, 4),
                "risk": p.risk.value,
                "daily_volume": st.daily_volume if st else None,
                "price_cv": round(st.price_cv, 4) if st and st.price_cv is not None else None,
                "trend": round(st.trend, 4) if st and st.trend is not None else None,
            }
        )
    return (
        json.dumps(
            {
                "schema_version": ARCHIVE_SCHEMA,
                "generated_at": generated_at.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "mode": mode,
                "positions": rows,
            },
            ensure_ascii=False,
            separators=(",", ":"),
        )
        + "\n"
    )


@dataclass(frozen=True, slots=True)
class ArchivedPosition:
    item_id: int
    name: str | None
    buy_price: int
    sell_price: int
    quantity: int
    roi: float
    risk: str
    daily_volume: int | None
    price_cv: float | None
    trend: float | None


@dataclass(frozen=True, slots=True)
class ArchivedList:
    day: date
    generated_at: datetime
    mode: str
    positions: list[ArchivedPosition]


def _opt_num(v: Any, lo: float, hi: float) -> float | None:
    if v is None:
        return None
    if isinstance(v, bool) or not isinstance(v, int | float) or not lo <= v <= hi:
        raise ValidationError("Zahl außerhalb des Bereichs")
    return float(v)


def _required_num(v: Any, lo: float, hi: float) -> float:
    n = _opt_num(v, lo, hi)
    if n is None:
        raise ValidationError("Zahl erwartet")
    return n


def _int(v: Any, lo: int, hi: int) -> int:
    if isinstance(v, bool) or not isinstance(v, int) or not lo <= v <= hi:
        raise ValidationError("Ganzzahl erwartet")
    return v


def parse_archive(text: str, day: date) -> ArchivedList:
    data = json.loads(text)
    if not isinstance(data, dict) or data.get("schema_version") != ARCHIVE_SCHEMA:
        raise ValidationError("unbekanntes Archivformat")
    stamp = data.get("generated_at")
    if not isinstance(stamp, str) or not re.fullmatch(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", stamp
    ):
        raise ValidationError("generated_at ungültig")
    rows = data.get("positions")
    if not isinstance(rows, list) or len(rows) > 100:
        raise ValidationError("positions ungültig")
    positions = []
    for r in rows:
        try:
            if not isinstance(r, dict):
                raise ValidationError("Objekt erwartet")
            risk = r.get("risk")
            if risk not in ("green", "yellow", "red"):
                raise ValidationError("risk ungültig")
            volume = r.get("daily_volume")
            positions.append(
                ArchivedPosition(
                    item_id=item_id(r.get("id")),
                    name=clean_text(r["name"], "name") if r.get("name") is not None else None,
                    buy_price=_int(r.get("buy_price"), 1, 10**10),
                    sell_price=_int(r.get("sell_price"), 1, 10**10),
                    quantity=_int(r.get("quantity"), 1, 10**6),
                    roi=_required_num(r.get("roi"), -1, 1e6),
                    risk=risk,
                    daily_volume=None if volume is None else _int(volume, 0, 10**9),
                    price_cv=_opt_num(r.get("price_cv"), 0, 1e3),
                    trend=_opt_num(r.get("trend"), -1e3, 1e3),
                )
            )
        except (ValidationError, KeyError):
            continue
    return ArchivedList(
        day=day,
        generated_at=datetime.strptime(stamp, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC),
        mode=str(data.get("mode", "")),
        positions=positions,
    )


def load_archives(root: Path, first: date, last: date) -> list[ArchivedList]:
    base = root / LISTS_DIR
    if not base.is_dir() or base.is_symlink():
        return []
    out = []
    for f in sorted(base.iterdir()):
        m = ARCHIVE_RE.fullmatch(f.name)
        if not m or not f.is_file() or f.is_symlink():
            continue
        try:
            day = date.fromisoformat(m.group(1))
        except ValueError:
            continue
        if not first <= day <= last:
            continue
        try:
            if f.stat().st_size > MAX_ARCHIVE_BYTES:
                raise ValidationError("zu groß")
            out.append(parse_archive(f.read_text(encoding="utf-8"), day))
        except (OSError, ValueError, ValidationError) as exc:
            log.warning("Archiv %s übersprungen: %s", f.name, exc)
    return out


# --- Auswertung einzelner Positionen ------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Outcome:
    position: ArchivedPosition
    list_day: date
    has_data: bool
    roi_24: float | None
    roi_48: float | None
    price_held_48: bool | None
    outbid_24: bool | None
    volume_ratio: float | None
    mode: str = ""  # Modus der Liste: "snapshots" (Historie) oder "orderbook_depth"


def _nearest(series: Sequence[tuple[datetime, Any]], target: datetime) -> Any | None:
    best = None
    best_dt = timedelta(hours=TOLERANCE_H)
    for t, p in series:
        dt = abs(t - target)
        if dt <= best_dt:
            best, best_dt = p, dt
    return best


def _roi_at(p: ArchivedPosition, price: Any, fees: FeeSchedule) -> float | None:
    if price is None or price.sells.unit_price <= 1:
        return None
    sell = price.sells.unit_price - 1
    return net_profit(p.buy_price, sell, fees) / p.buy_price


def evaluate_position(
    p: ArchivedPosition,
    generated_at: datetime,
    list_day: date,
    series: Sequence[tuple[datetime, Any]],
    fees: FeeSchedule,
    max_gap_s: float,
    mode: str = "",
) -> Outcome:
    after = [(t, pr) for t, pr in series if t > generated_at]
    if not after:
        return Outcome(p, list_day, False, None, None, None, None, None, mode)
    at = {h: _nearest(after, generated_at + timedelta(hours=h)) for h in HORIZONS_H}
    roi_24 = _roi_at(p, at[24], fees)
    roi_48 = _roi_at(p, at[48], fees)
    held = None
    if at[48] is not None and at[48].sells.unit_price > 1:
        held = at[48].sells.unit_price - 1 >= p.sell_price * (1 - PRICE_HELD_SLACK)
    within_24 = [pr for t, pr in after if t <= generated_at + timedelta(hours=24)]
    outbid = max(pr.buys.unit_price for pr in within_24) > p.buy_price if within_24 else None
    ratio = None
    window = [(t, pr) for t, pr in after if t <= generated_at + timedelta(hours=48)]
    bought, sold, covered = order_flow(window, max_gap_s)
    if p.daily_volume and covered >= 12 * 3600:
        observed = min(bought, sold) * SECONDS_PER_DAY / covered
        ratio = observed / p.daily_volume
    has = any(v is not None for v in (roi_24, roi_48, outbid))
    return Outcome(p, list_day, has, roi_24, roi_48, held, outbid, ratio, mode)


def evaluate_lists(
    lists: Iterable[ArchivedList],
    snapshots: Sequence[Snapshot],
    fees: FeeSchedule,
    max_gap_s: float,
) -> list[Outcome]:
    series: dict[int, list[tuple[datetime, Any]]] = {}
    for snap in snapshots:
        for pid, price in snap.prices.items():
            series.setdefault(pid, []).append((snap.taken_at, price))
    out = []
    for lst in lists:
        for p in lst.positions:
            out.append(
                evaluate_position(
                    p,
                    lst.generated_at,
                    lst.day,
                    series.get(p.item_id, []),
                    fees,
                    max_gap_s,
                    lst.mode,
                )
            )
    return out


# --- Zusammenfassung ----------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Summary:
    positions: int
    with_data: int
    profitable_48: float | None  # Anteil mit ROI nach 48 h > 0
    median_roi_48: float | None
    price_held_48: float | None
    outbid_24: float | None
    median_volume_ratio: float | None

    def to_dict(self) -> dict[str, Any]:
        def r(v: float | None) -> float | None:
            return None if v is None else round(v, 4)

        return {
            "positions": self.positions,
            "with_data": self.with_data,
            "profitable_48": r(self.profitable_48),
            "median_roi_48": r(self.median_roi_48),
            "price_held_48": r(self.price_held_48),
            "outbid_24": r(self.outbid_24),
            "median_volume_ratio": r(self.median_volume_ratio),
        }


def history_outcomes(outcomes: Sequence[Outcome]) -> list[Outcome]:
    """Nur Positionen aus Listen im Historien-Modus (mit Volumen-, CV- und Trendschätzung)."""
    return [o for o in outcomes if o.mode == MODE_HISTORY]


def _share(values: list[bool]) -> float | None:
    return sum(values) / len(values) if values else None


def summarize(outcomes: Sequence[Outcome]) -> Summary:
    rois = [o.roi_48 for o in outcomes if o.roi_48 is not None]
    ratios = [o.volume_ratio for o in outcomes if o.volume_ratio is not None]
    return Summary(
        positions=len(outcomes),
        with_data=sum(o.has_data for o in outcomes),
        profitable_48=_share([r > 0 for r in rois]),
        median_roi_48=statistics.median(rois) if rois else None,
        price_held_48=_share([o.price_held_48 for o in outcomes if o.price_held_48 is not None]),
        outbid_24=_share([o.outbid_24 for o in outcomes if o.outbid_24 is not None]),
        median_volume_ratio=statistics.median(ratios) if ratios else None,
    )


Bucketer = Callable[[ArchivedPosition], str | None]


def _bucket_labels(edges: Sequence[float], fmt: Callable[[float], str]) -> list[str]:
    """Alle Bereichsnamen in natürlicher Reihenfolge."""
    return (
        [f"< {fmt(edges[0])}"]
        + [f"{fmt(lo)} – {fmt(hi)}" for lo, hi in itertools.pairwise(edges)]
        + [f"≥ {fmt(edges[-1])}"]
    )


def _bucket(value: float | None, edges: Sequence[float], fmt: Callable[[float], str]) -> str | None:
    if value is None:
        return None
    for lo, hi in itertools.pairwise(edges):
        if lo <= value < hi:
            return f"{fmt(lo)} – {fmt(hi)}"
    return f"≥ {fmt(edges[-1])}" if value >= edges[-1] else f"< {fmt(edges[0])}"


def _pct(v: float) -> str:
    return f"{v * 100:.0f} %"


def _count(v: float) -> str:
    return f"{v:,.0f}".replace(",", ".")


RISK_LABELS = {"green": "grün", "yellow": "gelb", "red": "rot"}
ROI_EDGES = [0.10, 0.20, 0.35, 0.60, 1.0]
CV_EDGES = [0, 0.02, 0.04, 0.07, 0.10]
VOLUME_EDGES = [0, 200, 1000, 5000, 20000]

# Gruppe → (Titel, Zuordnung, Reihenfolge der Bereiche)
GROUPS: dict[str, tuple[str, Bucketer, list[str]]] = {
    "risk": ("Ampel", lambda p: RISK_LABELS[p.risk], list(RISK_LABELS.values())),
    "roi": (
        "geplanter ROI",
        lambda p: _bucket(p.roi, ROI_EDGES, _pct),
        _bucket_labels(ROI_EDGES, _pct),
    ),
    "cv": (
        "Volatilität (CV)",
        lambda p: _bucket(p.price_cv, CV_EDGES, _pct),
        _bucket_labels(CV_EDGES, _pct),
    ),
    "volume": (
        "Tagesvolumen",
        lambda p: _bucket(
            float(p.daily_volume) if p.daily_volume is not None else None, VOLUME_EDGES, _count
        ),
        _bucket_labels(VOLUME_EDGES, _count),
    ),
}


def grouped(outcomes: Sequence[Outcome]) -> dict[str, list[tuple[str, Summary]]]:
    """Zusammenfassung je Bereich, in natürlicher Reihenfolge der Bereiche."""
    result: dict[str, list[tuple[str, Summary]]] = {}
    for key, (_, fn, order) in GROUPS.items():
        buckets: dict[str, list[Outcome]] = {}
        for o in outcomes:
            label = fn(o.position)
            if label is not None:
                buckets.setdefault(label, []).append(o)
        result[key] = [(label, summarize(buckets[label])) for label in order if label in buckets]
    return result


# --- Report -------------------------------------------------------------------------------


def _fmt_share(v: float | None) -> str:
    return "–" if v is None else f"{v * 100:.0f} %"


def _fmt_roi(v: float | None) -> str:
    return "–" if v is None else f"{v * 100:+.1f} %"


def _fmt_ratio(v: float | None) -> str:
    return "–" if v is None else f"{v:.2f}"


def _row(label: str, s: Summary) -> str:
    return (
        f"| {label} | {s.positions} | {s.with_data} | {_fmt_share(s.profitable_48)} "
        f"| {_fmt_roi(s.median_roi_48)} | {_fmt_share(s.price_held_48)} "
        f"| {_fmt_share(s.outbid_24)} | {_fmt_ratio(s.median_volume_ratio)} |"
    )


HEADER = (
    "| | Positionen | mit Daten | profitabel nach 48 h | Median-ROI 48 h | Preis gehalten "
    "| Gebot überholt (24 h) | Volumen beobachtet/geschätzt |\n"
    "|---|---:|---:|---:|---:|---:|---:|---:|"
)


def to_markdown(
    outcomes: Sequence[Outcome],
    lists: Sequence[ArchivedList],
    funnel: dict[str, int],
    generated_at: datetime,
) -> str:
    lines = [
        f"# Auswertung – {generated_at:%Y-%m-%d}",
        "",
        "Rückblick auf frühere Einkaufslisten anhand der stündlichen Snapshots. Grundlage für das "
        "Feintuning der Schwellwerte in `config.yaml` (Phase 5).",
        "",
    ]
    if not outcomes:
        lines += [
            "Noch keine Listen auswertbar. Eine Liste wird frühestens 48 Stunden nach ihrer "
            "Erstellung bewertet.",
            "",
        ]
    else:
        days = sorted({lst.day for lst in lists})
        history = history_outcomes(outcomes)
        orderbook = [o for o in outcomes if o.mode != MODE_HISTORY]
        lines += [
            f"Ausgewertet: {len(lists)} Listen vom {days[0]:%d.%m.%Y} bis {days[-1]:%d.%m.%Y}.",
            "",
            "## Gesamt",
            "",
            HEADER,
            _row("alle", summarize(outcomes)),
        ]
        if history:
            lines.append(_row("Historien-Modus", summarize(history)))
        if orderbook:
            lines.append(_row("Orderbuch-Modus", summarize(orderbook)))
        lines.append("")
        if history and orderbook:
            lines += [
                "Die Aufschlüsselung unten enthält nur Listen aus dem Historien-Modus. Listen aus "
                "dem Orderbuch-Modus (ohne Volumenschätzung) enthalten oft illiquide Ausreißer, "
                "deren Gebote kaum gefüllt würden, und verzerren sonst die Statistik.",
                "",
            ]
        for key, rows in grouped(history or outcomes).items():
            title = GROUPS[key][0]
            lines += [f"## Nach {title}", "", HEADER.replace("| |", f"| {title} |", 1)]
            lines += [_row(label, s) for label, s in rows]
            lines.append("")
        lines += [
            "**Lesehilfe:** *profitabel nach 48 h* = Kauf zum geplanten Gebot und Verkauf zum "
            "dann günstigsten Angebot − 1 wäre nach Gebühren im Plus gewesen. *Preis gehalten* = "
            "günstigstes Angebot höchstens 5 % unter dem geplanten Verkaufspreis. "
            "*Gebot überholt* = jemand bot binnen 24 h mehr. *Volumen* < 1 heißt: Die Schätzung "
            "war zu optimistisch.",
            "",
        ]
    if funnel:
        total = sum(funnel.values())
        lines += [
            "## Filter-Trichter der heutigen Analyse",
            "",
            "| Filter | Items | Anteil |",
            "|---|---:|---:|",
        ]
        for key, label in FUNNEL_STEPS.items():
            n = funnel.get(key, 0)
            if n:
                lines.append(f"| {label} | {n} | {n / total * 100:.1f} % |")
        lines.append("")
    return "\n".join(lines)
