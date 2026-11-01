"""Kommandozeile: ``python -m gw2tp analyze --config config.yaml --out out``."""

from __future__ import annotations

import argparse
import logging
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from . import analyze, config, report
from .fetch import ApiError, Gw2Client
from .models import Item, Price, ValidationError, parse_id_list, parse_many

log = logging.getLogger("gw2tp")


class RunError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class RunResult:
    positions: list[analyze.Position]
    stats: report.RunStats


def _check_failures(client: Gw2Client, cfg: config.Config) -> None:
    s = client.stats
    if s.total_batches and s.failed_batches / s.total_batches > cfg.api.max_failed_batch_share:
        raise RunError(
            f"{s.failed_batches} von {s.total_batches} API-Blöcken fehlgeschlagen – Abbruch"
        )


def run(client: Gw2Client, cfg: config.Config) -> RunResult:
    try:
        ids, _ = parse_id_list(client.get_price_ids())
    except ValidationError as exc:
        raise RunError(f"Ungültige ID-Liste: {exc}") from None
    if not ids:
        raise RunError("API lieferte keine Item-IDs")
    log.info("%d handelbare Items", len(ids))

    prices, prices_rejected = parse_many(client.get_prices(ids), Price.parse)
    _check_failures(client, cfg)
    if not prices:
        raise RunError("Keine gültigen Preise erhalten")

    ranked = analyze.preselect(prices, cfg)
    log.info("%d Kandidaten nach Markt-, Größen- und Gewinnfiltern", len(ranked))
    shortlist = ranked[: cfg.ranking.max_item_lookups]

    items_raw = client.get_items([p.candidate.item_id for p in shortlist]) if shortlist else []
    items, items_rejected = parse_many(items_raw, Item.parse)
    _check_failures(client, cfg)

    positions = analyze.finalize(shortlist, {i.id: i for i in items}, cfg)
    stats = report.RunStats(
        prices_total=len(prices),
        prices_rejected=prices_rejected,
        items_rejected=items_rejected,
        candidates=len(ranked),
        failed_batches=client.stats.failed_batches,
    )
    return RunResult(positions=positions, stats=stats)


def write_outputs(result: RunResult, out_dir: Path, cfg: config.Config, now: datetime) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    kwargs = {"generated_at": now, "budget_copper": cfg.budget_copper, "stats": result.stats}
    (out_dir / "shopping-list.md").write_text(
        report.to_markdown(result.positions, **kwargs), encoding="utf-8"
    )
    (out_dir / "shopping-list.json").write_text(
        report.to_json(result.positions, **kwargs), encoding="utf-8"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="gw2tp", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p_an = sub.add_parser("analyze", help="Einkaufsliste aus aktuellen Preisen erzeugen")
    p_an.add_argument("--config", type=Path, default=Path("config.yaml"))
    p_an.add_argument("--out", type=Path, default=Path("out"))
    p_an.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )
    try:
        cfg = config.load(args.config)
        client = Gw2Client(
            timeout_s=cfg.api.timeout_s,
            max_retries=cfg.api.max_retries,
            min_interval_s=cfg.api.min_request_interval_s,
        )
        result = run(client, cfg)
        write_outputs(result, args.out, cfg, datetime.now(UTC))
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
