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
    # Mindestmengen im aktuellen Orderbuch (in jedem Modus).
    min_demand_quantity: int = 500
    min_supply_quantity: int = 500
    excluded_flags: tuple[str, ...] = ("AccountBound", "SoulbindOnAcquire")
    # Ab Phase 2 (mit Historie):
    min_volume_multiple: float = 10.0  # Tagesvolumen ≥ 10 × Stückzahl
    min_daily_volume: int = 50
    max_price_cv: float = 0.10  # Variationskoeffizient der Preise über 7 Tage
    max_negative_trend: float = 0.02  # Tagesmedian darf max. 2 %/Tag fallen


@dataclass(frozen=True, slots=True)
class Sizing:
    max_budget_share: float = 0.10
    max_depth_share: float = 0.05  # nur ohne Historie (Orderbuch-Modus)
    max_volume_share: float = 0.05  # 5 % des geschätzten Tagesvolumens
    max_units: int = 250
    max_positions: int = 10


@dataclass(frozen=True, slots=True)
class Ranking:
    # Orderbuch-Tiefe, bei der der Liquiditätsfaktor 1,0 erreicht (log-skaliert).
    liquidity_reference_quantity: int = 100_000
    # Tagesvolumen, bei dem der Liquiditätsfaktor 1,0 erreicht (Historien-Modus).
    liquidity_reference_volume: int = 10_000
    # Wie viele der besten Kandidaten für Item-Details (Name, Flags) abgefragt werden.
    max_item_lookups: int = 400
    # Pool für das Dashboard: so viele Items je Rangliste (großes / kleines Budget).
    pool_size_per_regime: int = 100


@dataclass(frozen=True, slots=True)
class Risk:
    green_min_roi: float = 0.20
    green_min_depth: int = 5_000
    red_below_roi: float = 0.12
    red_below_depth: int = 1_000
    green_max_cv: float = 0.04
    red_min_cv: float = 0.07
    red_below_trend: float = 0.01  # fällt der Median > 1 %/Tag → rot
    green_min_volume_multiple: float = 40.0
    # Grün verlangt einen Trend ≥ diesem Wert (relativ pro Tag; −0,005 = −0,5 %/Tag).
    green_min_trend: float = 0.0


@dataclass(frozen=True, slots=True)
class Universe:
    """Welche Items stündlich gespeichert werden."""

    max_items: int = 800
    min_quantity: int = 200  # Mindestmenge auf beiden Orderbuch-Seiten
    min_buy_price_copper: int = 100
    min_roi: float = 0.0  # aktueller Spread muss nach Gebühren mindestens kostendeckend sein
    whitelist_ids: tuple[int, ...] = ()


@dataclass(frozen=True, slots=True)
class History:
    window_days: int = 7
    max_gap_hours: float = 4.0  # größere Lücken zählen nicht für die Volumenschätzung
    min_history_hours: float = 24.0  # weniger → Item hat (noch) keine verwertbare Historie
    min_trend_days: int = 3
    min_samples_per_day: int = 4
    retention_days: int = 14  # ältere Stunden-Snapshots → Tageswerte


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
    universe: Universe = field(default_factory=Universe)
    history: History = field(default_factory=History)


# Werte, die negativ sein dürfen (relative Änderung pro Tag).
_SIGNED = {"green_min_trend"}

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
    "max_price_cv",
    "max_negative_trend",
    "max_volume_share",
    "green_max_cv",
    "red_min_cv",
    "red_below_trend",
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
        if isinstance(default, tuple) and name.endswith("_ids"):
            if not isinstance(value, list) or not all(
                isinstance(v, int) and not isinstance(v, bool) and 0 < v <= 10_000_000
                for v in value
            ):
                raise ConfigError(f"{key}: Liste positiver Item-IDs erwartet")
            value = tuple(dict.fromkeys(value))
        elif isinstance(default, tuple):
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
            if name in _SIGNED:
                if not -1 <= value <= 1:
                    raise ConfigError(f"{key}: muss zwischen −1 und 1 liegen")
            elif value < 0:
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
    allowed = {
        "budget_gold",
        "fees",
        "filters",
        "sizing",
        "ranking",
        "risk",
        "api",
        "universe",
        "history",
    }
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
        universe=_build(Universe, data.get("universe"), "universe"),
        history=_build(History, data.get("history"), "history"),
    )
    if cfg.filters.max_roi < cfg.filters.min_roi:
        raise ConfigError("filters.max_roi muss ≥ filters.min_roi sein")
    if not 1 <= cfg.sizing.max_positions <= 50:
        raise ConfigError("sizing.max_positions muss zwischen 1 und 50 liegen")
    if cfg.ranking.liquidity_reference_quantity < 1:
        raise ConfigError("ranking.liquidity_reference_quantity muss ≥ 1 sein")
    if cfg.api.max_retries > 10 or cfg.api.min_request_interval_s < 0.2:
        raise ConfigError("api: max_retries ≤ 10 und min_request_interval_s ≥ 0.2 erforderlich")
    if not 1 <= cfg.universe.max_items <= 2_000:
        raise ConfigError("universe.max_items muss zwischen 1 und 2000 liegen")
    if len(cfg.universe.whitelist_ids) > 500:
        raise ConfigError("universe.whitelist_ids: höchstens 500 Einträge")
    h = cfg.history
    if not 1 <= h.window_days <= 30 or h.retention_days < h.window_days:
        raise ConfigError("history: 1 ≤ window_days ≤ 30 und retention_days ≥ window_days")
    if h.max_gap_hours <= 0 or h.min_history_hours <= 0:
        raise ConfigError("history: max_gap_hours und min_history_hours müssen > 0 sein")
    if not 1 <= cfg.ranking.pool_size_per_regime <= 500:
        raise ConfigError("ranking.pool_size_per_regime muss zwischen 1 und 500 liegen")
    if cfg.ranking.liquidity_reference_volume < 1:
        raise ConfigError("ranking.liquidity_reference_volume muss ≥ 1 sein")
    return cfg


def load(path: str | Path) -> Config:
    with Path(path).open(encoding="utf-8") as fh:
        return from_dict(yaml.safe_load(fh))
