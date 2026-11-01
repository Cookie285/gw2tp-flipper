"""Konfiguration aus config.yaml laden und streng prüfen.

Unbekannte Schlüssel führen zu einem Fehler, damit Tippfehler nicht unbemerkt Standardwerte
aktivieren.
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import Any

import yaml

from .fees import COPPER_PER_GOLD, FeeSchedule


class ConfigError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class Filters:
    min_roi: float = 0.10
    max_roi: float = 2.0
    min_profit_per_unit_copper: int = 1_000  # 10 Silber
    min_profit_per_position_copper: int = 10_000  # 1 Gold
    min_buy_price_copper: int = 100  # 1 Silber
    # Phase 1: Orderbuch-Tiefe als Ersatz für das (noch unbekannte) Tagesvolumen.
    min_demand_quantity: int = 500
    min_supply_quantity: int = 500
    excluded_flags: tuple[str, ...] = ("AccountBound", "SoulbindOnAcquire")


@dataclass(frozen=True, slots=True)
class Sizing:
    max_budget_share: float = 0.10
    max_depth_share: float = 0.05
    max_units: int = 250
    max_positions: int = 10


@dataclass(frozen=True, slots=True)
class Ranking:
    # Orderbuch-Tiefe, bei der der Liquiditätsfaktor 1,0 erreicht (log-skaliert).
    liquidity_reference_quantity: int = 100_000
    # Wie viele der besten Kandidaten für Item-Details (Name, Flags) abgefragt werden.
    max_item_lookups: int = 400


@dataclass(frozen=True, slots=True)
class Risk:
    green_min_roi: float = 0.20
    green_min_depth: int = 5_000
    red_below_roi: float = 0.12
    red_below_depth: int = 1_000


@dataclass(frozen=True, slots=True)
class Api:
    timeout_s: float = 20.0
    max_retries: int = 5
    min_request_interval_s: float = 0.25
    # Anteil fehlgeschlagener Blöcke, ab dem der Lauf abbricht (statt lückenhafter Liste).
    max_failed_batch_share: float = 0.2


@dataclass(frozen=True, slots=True)
class Config:
    budget_copper: int = 200 * COPPER_PER_GOLD
    fees: FeeSchedule = field(default_factory=FeeSchedule)
    filters: Filters = field(default_factory=Filters)
    sizing: Sizing = field(default_factory=Sizing)
    ranking: Ranking = field(default_factory=Ranking)
    risk: Risk = field(default_factory=Risk)
    api: Api = field(default_factory=Api)


_RATIOS = {
    "min_roi",
    "max_roi",
    "max_budget_share",
    "max_depth_share",
    "green_min_roi",
    "red_below_roi",
    "max_failed_batch_share",
    "listing_fee",
    "exchange_fee",
}


def _build(cls: type, data: Any, section: str) -> Any:
    if data is None:
        return cls()
    if not isinstance(data, dict):
        raise ConfigError(f"{section}: Abschnitt muss ein Mapping sein")
    known = {f.name: f for f in fields(cls)}
    unknown = set(data) - set(known)
    if unknown:
        raise ConfigError(f"{section}: unbekannte Schlüssel {sorted(unknown)}")
    defaults = cls()
    values: dict[str, Any] = {}
    for name, value in data.items():
        default = getattr(defaults, name)
        key = f"{section}.{name}"
        if isinstance(default, tuple):
            if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
                raise ConfigError(f"{key}: Liste von Texten erwartet")
            value = tuple(value)
        elif isinstance(default, bool) or isinstance(value, bool):
            raise ConfigError(f"{key}: Zahl erwartet")
        elif isinstance(default, int):
            if not isinstance(value, int):
                raise ConfigError(f"{key}: Ganzzahl erwartet")
            if value < 0:
                raise ConfigError(f"{key}: darf nicht negativ sein")
        elif isinstance(default, float):
            if not isinstance(value, int | float):
                raise ConfigError(f"{key}: Zahl erwartet")
            value = float(value)
            if value < 0:
                raise ConfigError(f"{key}: darf nicht negativ sein")
            if name in _RATIOS and name != "max_roi" and value > 1:
                raise ConfigError(f"{key}: Anteil muss zwischen 0 und 1 liegen")
        values[name] = value
    try:
        return cls(**values)
    except (TypeError, ValueError) as exc:
        raise ConfigError(f"{section}: {exc}") from None


def from_dict(data: Any) -> Config:
    if data is None:
        data = {}
    if not isinstance(data, dict):
        raise ConfigError("Konfiguration muss ein Mapping sein")
    allowed = {"budget_gold", "fees", "filters", "sizing", "ranking", "risk", "api"}
    unknown = set(data) - allowed
    if unknown:
        raise ConfigError(f"unbekannte Schlüssel {sorted(unknown)}")

    budget_gold = data.get("budget_gold", 200)
    if (
        isinstance(budget_gold, bool)
        or not isinstance(budget_gold, int | float)
        or budget_gold <= 0
    ):
        raise ConfigError("budget_gold muss eine positive Zahl sein")

    cfg = Config(
        budget_copper=round(budget_gold * COPPER_PER_GOLD),
        fees=_build(FeeSchedule, data.get("fees"), "fees"),
        filters=_build(Filters, data.get("filters"), "filters"),
        sizing=_build(Sizing, data.get("sizing"), "sizing"),
        ranking=_build(Ranking, data.get("ranking"), "ranking"),
        risk=_build(Risk, data.get("risk"), "risk"),
        api=_build(Api, data.get("api"), "api"),
    )
    if cfg.filters.max_roi < cfg.filters.min_roi:
        raise ConfigError("filters.max_roi muss ≥ filters.min_roi sein")
    if not 1 <= cfg.sizing.max_positions <= 50:
        raise ConfigError("sizing.max_positions muss zwischen 1 und 50 liegen")
    if cfg.ranking.liquidity_reference_quantity < 1:
        raise ConfigError("ranking.liquidity_reference_quantity muss ≥ 1 sein")
    if cfg.api.max_retries > 10 or cfg.api.min_request_interval_s < 0.2:
        raise ConfigError("api: max_retries ≤ 10 und min_request_interval_s ≥ 0.2 erforderlich")
    return cfg


def load(path: str | Path) -> Config:
    with Path(path).open(encoding="utf-8") as fh:
        return from_dict(yaml.safe_load(fh))
