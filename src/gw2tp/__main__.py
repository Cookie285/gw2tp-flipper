"""Kommandozeile.

* ``python -m gw2tp snapshot --data-dir datadir --out out``: stündlicher Preis-Snapshot
* ``python -m gw2tp analyze --data-dir datadir --out out``: tägliche Einkaufsliste, neues
  Universum und Verdichtung alter Snapshots

``--data-dir`` zeigt auf einen (schreibgeschützten) Checkout des Branches ``data``. Alle Ergebnisse
landen in ``--out``; geschrieben wird der Branch ausschließlich vom Publish-Job.
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from . import analyze, config, evaluate, history, report
from .fetch import ApiError, Gw2Client
from .models import Item, Price, ValidationError, parse_id_list, parse_many

log = logging.getLogger("gw2tp")

REMOVE_LIST = "remove.txt"
# Dauerlauf: GitHub-Jobs dürfen höchstens 6 h laufen; Puffer für Setup und Upload.
MAX_REPEAT_MIN = 345
MIN_EVERY_MIN = 5  # Dateinamen haben Minutenauflösung
ARCHIVE_FILE = "archive.json"  # wird vom Publish-Skript als lists/YYYY-MM-DD.json abgelegt
EVALUATION_FILE = "evaluation.md"


class RunError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class RunResult:
    positions: list[analyze.Position]
    stats: report.RunStats
    universe: list[int]
    pool: list[analyze.PoolEntry]
    funnel: dict[str, int]


def _check_failures(client: Gw2Client, cfg: config.Config) -> None:
    s = client.stats
    if s.total_batches and s.failed_batches / s.total_batches > cfg.api.max_failed_batch_share:
        raise RunError(
            f"{s.failed_batches} von {s.total_batches} API-Blöcken fehlgeschlagen – Abbruch"
        )


def fetch_all_prices(client: Gw2Client, cfg: config.Config) -> tuple[list[Price], int]:
    try:
        ids, _ = parse_id_list(client.get_price_ids())
    except ValidationError as exc:
        raise RunError(f"Ungültige ID-Liste: {exc}") from None
    if not ids:
        raise RunError("API lieferte keine Item-IDs")
    log.info("%d handelbare Items", len(ids))
    prices, rejected = parse_many(client.get_prices(ids), Price.parse)
    _check_failures(client, cfg)
    if not prices:
        raise RunError("Keine gültigen Preise erhalten")
    return prices, rejected


def run(
    client: Gw2Client,
    cfg: config.Config,
    snapshots: list[history.Snapshot] | None = None,
) -> RunResult:
    prices, prices_rejected = fetch_all_prices(client, cfg)
    universe = analyze.select_universe(prices, cfg.universe, cfg.fees)

    snapshots = snapshots or []
    usable = history.usable_stats(history.build_stats(snapshots, cfg.history), cfg.history)
    mode = report.MODE_HISTORY if usable else report.MODE_ORDERBOOK
    log.info("Modus %s: %d Snapshots, %d Items mit Historie", mode, len(snapshots), len(usable))

    funnel: Counter[str] = Counter()
    pool = analyze.build_pool(prices, cfg, usable if usable else None, funnel)
    pool = pool[: cfg.ranking.max_item_lookups]
    log.info("%d Kandidaten im Pool", len(pool))

    items_raw = client.get_items([e.candidate.item_id for e in pool]) if pool else []
    items, items_rejected = parse_many(items_raw, Item.parse)
    _check_failures(client, cfg)

    pool = analyze.attach_items(pool, {i.id: i for i in items}, cfg.filters)
    positions = analyze.plan(pool, cfg)
    stats = report.RunStats(
        prices_total=len(prices),
        prices_rejected=prices_rejected,
        items_rejected=items_rejected,
        candidates=len(pool),
        failed_batches=client.stats.failed_batches,
        mode=mode,
        snapshots=len(snapshots),
        history_items=len(usable),
        universe_size=len(universe),
    )
    return RunResult(
        positions=positions, stats=stats, universe=universe, pool=pool, funnel=dict(funnel)
    )


def write_outputs(
    result: RunResult,
    out_dir: Path,
    cfg: config.Config,
    now: datetime,
    review: dict[str, Any] | None = None,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    kwargs = {
        "generated_at": now,
        "budget_copper": cfg.budget_copper,
        "stats": result.stats,
        "window_days": cfg.history.window_days,
    }
    (out_dir / "shopping-list.md").write_text(
        report.to_markdown(result.positions, **kwargs), encoding="utf-8"
    )
    (out_dir / "shopping-list.json").write_text(
        report.to_json(
            result.positions,
            pool=result.pool,
            cfg=cfg,
            funnel=result.funnel,
            review=review,
            **kwargs,
        ),
        encoding="utf-8",
    )
    (out_dir / ARCHIVE_FILE).write_text(
        evaluate.encode_archive(result.positions, now, result.stats.mode), encoding="utf-8"
    )
    (out_dir / history.UNIVERSE_FILE).write_text(
        history.encode_universe(result.universe, now), encoding="utf-8"
    )


def review_lists(
    data_dir: Path, snapshots: list[history.Snapshot], cfg: config.Config, now: datetime
) -> tuple[list[evaluate.ArchivedList], list[evaluate.Outcome]]:
    """Frühere Listen (2 bis retention_days Tage alt) gegen die Snapshots auswerten."""
    cutoff = now - timedelta(hours=max(evaluate.HORIZONS_H))
    first = (now - timedelta(days=cfg.history.retention_days)).date()
    lists = [
        lst
        for lst in evaluate.load_archives(data_dir, first, cutoff.date())
        if lst.generated_at <= cutoff
    ]
    outcomes = evaluate.evaluate_lists(lists, snapshots, cfg.fees, cfg.history.max_gap_hours * 3600)
    return lists, outcomes


def review_summary(
    lists: list[evaluate.ArchivedList], outcomes: list[evaluate.Outcome]
) -> dict[str, Any] | None:
    if not outcomes:
        return None
    days = sorted(lst.day for lst in lists)
    return {
        "lists": len(lists),
        "from": days[0].isoformat(),
        "to": days[-1].isoformat(),
        **evaluate.summarize(outcomes).to_dict(),
    }


def write_compaction(c: history.Compaction, out_dir: Path) -> None:
    for rel, blob in c.daily_files.items():
        target = out_dir / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(blob)
    if c.removed:
        (out_dir / REMOVE_LIST).write_text("\n".join(c.removed) + "\n", encoding="utf-8")


def _snapshot_once(
    client: Gw2Client,
    cfg: config.Config,
    universe: list[int] | None,
    out_dir: Path,
    now: datetime,
) -> tuple[Path, list[int]]:
    """Ein Snapshot. Gibt den Pfad und das (ggf. neu bestimmte) Universum zurück."""
    if universe:
        prices, _ = parse_many(client.get_prices(universe), Price.parse)
        _check_failures(client, cfg)
    else:
        # Erster Lauf: Universum aus allen Preisen bestimmen (wird später von analyze gepflegt).
        log.info("Kein universe.json – Universum wird aus allen Preisen bestimmt")
        all_prices, _ = fetch_all_prices(client, cfg)
        universe = analyze.select_universe(all_prices, cfg.universe, cfg.fees)
        wanted = set(universe)
        prices = [p for p in all_prices if p.id in wanted]
    if not prices:
        raise RunError("Keine gültigen Preise für den Snapshot")
    target = out_dir / history.snapshot_relpath(now)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(history.encode_snapshot(now, prices))
    log.info("Snapshot mit %d Items: %s", len(prices), target)
    return target, universe


def take_snapshot(
    client: Gw2Client, cfg: config.Config, data_dir: Path | None, out_dir: Path, now: datetime
) -> Path:
    """Preise des Universums abrufen und als ``snapshots/YYYY-MM-DD/HHMM.json.gz`` ablegen."""
    universe = history.load_universe(data_dir / history.UNIVERSE_FILE) if data_dir else None
    return _snapshot_once(client, cfg, universe, out_dir, now)[0]


def snapshot_loop(
    client_factory: Callable[[config.Config], Gw2Client],
    cfg: config.Config,
    data_dir: Path | None,
    out_dir: Path,
    repeat_for_s: float,
    every_s: float,
    now_fn: Callable[[], datetime] = lambda: datetime.now(UTC).replace(microsecond=0),
    monotonic: Callable[[], float] = time.monotonic,
    sleep: Callable[[float], None] = time.sleep,
) -> list[Path]:
    """Snapshots im Dauerlauf: sofort einer, danach alle ``every_s`` Sekunden, solange der
    nächste Zeitpunkt höchstens ``repeat_for_s`` nach dem Start liegt.

    GitHub führt geplante Workflows unzuverlässig aus. Ein einzelner Auslöser liefert so
    trotzdem eine lückenlose Reihe. Fehlgeschlagene Durchläufe werden übersprungen."""
    universe = history.load_universe(data_dir / history.UNIVERSE_FILE) if data_dir else None
    start = monotonic()
    paths: list[Path] = []
    failures = 0
    i = 0
    while True:
        try:
            path, universe = _snapshot_once(client_factory(cfg), cfg, universe, out_dir, now_fn())
            paths.append(path)
        except (ApiError, RunError) as exc:
            failures += 1
            log.warning("Snapshot %d fehlgeschlagen: %s", i + 1, exc)
        i += 1
        offset = i * every_s
        if offset > repeat_for_s:
            break
        wait = start + offset - monotonic()
        if wait > 0:
            sleep(wait)
    log.info("%d Snapshots geschrieben, %d fehlgeschlagen", len(paths), failures)
    if not paths:
        raise RunError("Kein einziger Snapshot erfolgreich")
    return paths


def _client(cfg: config.Config) -> Gw2Client:
    return Gw2Client(
        timeout_s=cfg.api.timeout_s,
        max_retries=cfg.api.max_retries,
        min_interval_s=cfg.api.min_request_interval_s,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="gw2tp", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    parsers = {}
    for name, text in (
        ("analyze", "Einkaufsliste erzeugen, Universum aktualisieren, alte Snapshots verdichten"),
        ("snapshot", "Preis-Snapshot(s) des Universums erzeugen"),
    ):
        p = sub.add_parser(name, help=text)
        p.add_argument("--config", type=Path, default=Path("config.yaml"))
        p.add_argument("--data-dir", type=Path, default=None, help="Checkout des Branches data")
        p.add_argument("--out", type=Path, default=Path("out"))
        p.add_argument("-v", "--verbose", action="store_true")
        parsers[name] = p
    parsers["snapshot"].add_argument(
        "--repeat-for-min",
        type=int,
        default=0,
        help="Dauerlauf: so viele Minuten lang wiederholen (0 = ein einzelner Snapshot)",
    )
    parsers["snapshot"].add_argument(
        "--every-min", type=int, default=30, help="Abstand im Dauerlauf in Minuten"
    )
    args = parser.parse_args(argv)
    if args.command == "snapshot" and not (
        0 <= args.repeat_for_min <= MAX_REPEAT_MIN and MIN_EVERY_MIN <= args.every_min <= 120
    ):
        parser.error(
            f"--repeat-for-min muss 0–{MAX_REPEAT_MIN} und --every-min {MIN_EVERY_MIN}–120 sein"
        )

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )
    data_dir: Path | None = args.data_dir if args.data_dir and args.data_dir.is_dir() else None
    if args.data_dir and data_dir is None:
        log.warning("--data-dir %s fehlt – starte ohne Historie", args.data_dir)
    now = datetime.now(UTC).replace(microsecond=0)
    try:
        cfg = config.load(args.config)
        client = _client(cfg)
        if args.command == "snapshot":
            if args.repeat_for_min > 0:
                snapshot_loop(
                    _client, cfg, data_dir, args.out, args.repeat_for_min * 60, args.every_min * 60
                )
            else:
                take_snapshot(client, cfg, data_dir, args.out, now)
            return 0
        # Snapshots für die Auswertung (bis retention_days zurück) einmal laden; für die
        # Kennzahlen nur das Fenster der letzten window_days verwenden.
        all_snaps = (
            history.load_snapshots(data_dir, now, cfg.history.retention_days + 1)
            if data_dir
            else []
        )
        window_start = now - timedelta(days=cfg.history.window_days)
        snaps = [s for s in all_snaps if s.taken_at >= window_start]
        result = run(client, cfg, snaps)
        lists, outcomes = review_lists(data_dir, all_snaps, cfg, now) if data_dir else ([], [])
        write_outputs(result, args.out, cfg, now, review_summary(lists, outcomes))
        (args.out / EVALUATION_FILE).write_text(
            evaluate.to_markdown(outcomes, lists, result.funnel, now), encoding="utf-8"
        )
        if data_dir:
            write_compaction(history.compact(data_dir, now.date(), cfg.history), args.out)
    except (config.ConfigError, OSError) as exc:
        log.error("Konfiguration/Dateien: %s", exc)
        return 2
    except (ApiError, RunError) as exc:
        log.error("%s", exc)
        return 1
    log.info("%d Positionen geschrieben nach %s", len(result.positions), args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
