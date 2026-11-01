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
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from . import analyze, config, history, report
from .fetch import ApiError, Gw2Client
from .models import Item, Price, ValidationError, parse_id_list, parse_many

log = logging.getLogger("gw2tp")

REMOVE_LIST = "remove.txt"


class RunError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class RunResult:
    positions: list[analyze.Position]
    stats: report.RunStats
    universe: list[int]
    pool: list[analyze.PoolEntry]


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

    pool = analyze.build_pool(prices, cfg, usable if usable else None)
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
    return RunResult(positions=positions, stats=stats, universe=universe, pool=pool)


def write_outputs(result: RunResult, out_dir: Path, cfg: config.Config, now: datetime) -> None:
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
        report.to_json(result.positions, pool=result.pool, cfg=cfg, **kwargs), encoding="utf-8"
    )
    (out_dir / history.UNIVERSE_FILE).write_text(
        history.encode_universe(result.universe, now), encoding="utf-8"
    )


def write_compaction(c: history.Compaction, out_dir: Path) -> None:
    for rel, blob in c.daily_files.items():
        target = out_dir / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(blob)
    if c.removed:
        (out_dir / REMOVE_LIST).write_text("\n".join(c.removed) + "\n", encoding="utf-8")


def take_snapshot(
    client: Gw2Client, cfg: config.Config, data_dir: Path | None, out_dir: Path, now: datetime
) -> Path:
    """Preise des Universums abrufen und als ``snapshots/YYYY-MM-DD/HHMM.json.gz`` ablegen."""
    universe = history.load_universe(data_dir / history.UNIVERSE_FILE) if data_dir else None
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
    return target


def _client(cfg: config.Config) -> Gw2Client:
    return Gw2Client(
        timeout_s=cfg.api.timeout_s,
        max_retries=cfg.api.max_retries,
        min_interval_s=cfg.api.min_request_interval_s,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="gw2tp", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name, text in (
        ("analyze", "Einkaufsliste erzeugen, Universum aktualisieren, alte Snapshots verdichten"),
        ("snapshot", "Stündlichen Preis-Snapshot des Universums erzeugen"),
    ):
        p = sub.add_parser(name, help=text)
        p.add_argument("--config", type=Path, default=Path("config.yaml"))
        p.add_argument("--data-dir", type=Path, default=None, help="Checkout des Branches data")
        p.add_argument("--out", type=Path, default=Path("out"))
        p.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

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
            take_snapshot(client, cfg, data_dir, args.out, now)
            return 0
        snaps = history.load_snapshots(data_dir, now, cfg.history.window_days) if data_dir else []
        result = run(client, cfg, snaps)
        write_outputs(result, args.out, cfg, now)
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
