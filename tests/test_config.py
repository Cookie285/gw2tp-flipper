from pathlib import Path

import pytest

from gw2tp import config
from gw2tp.config import ConfigError

ROOT = Path(__file__).resolve().parents[1]


def test_repo_config_loads_with_spec_defaults():
    cfg = config.load(ROOT / "config.yaml")
    assert cfg.budget_copper == 2_000_000
    assert cfg.filters.min_roi == 0.10
    assert cfg.filters.min_profit_per_unit_copper == 1_000
    assert cfg.filters.min_profit_per_position_copper == 10_000
    assert cfg.filters.min_buy_price_copper == 100
    assert cfg.sizing.max_budget_share == 0.10
    assert cfg.sizing.max_units == 250
    assert cfg.sizing.max_positions == 10
    assert cfg.fees.listing_fee + cfg.fees.exchange_fee == pytest.approx(0.15)


def test_empty_config_uses_defaults():
    assert config.from_dict(None) == config.Config()


@pytest.mark.parametrize(
    "data",
    [
        {"budget_gld": 200},
        {"filters": {"min_rio": 0.1}},
        {"filters": {"min_roi": "0.1"}},
        {"filters": {"min_roi": True}},
        {"filters": {"min_roi": -0.1}},
        {"filters": {"min_roi": 1.5}},
        {"filters": {"min_roi": 0.5, "max_roi": 0.2}},
        {"filters": {"excluded_flags": "AccountBound"}},
        {"sizing": {"max_units": 2.5}},
        {"sizing": {"max_positions": 0}},
        {"fees": {"listing_fee": 1.0}},
        {"api": {"min_request_interval_s": 0.01}},
        {"budget_gold": 0},
        {"budget_gold": "200"},
        {"filters": []},
        [],
    ],
)
def test_invalid_config_rejected(data):
    with pytest.raises(ConfigError):
        config.from_dict(data)


def test_yaml_is_loaded_safely(tmp_path):
    p = tmp_path / "c.yaml"
    p.write_text("budget_gold: !!python/object/apply:os.system ['echo pwned']\n")
    with pytest.raises(Exception, match="python/object"):
        config.load(p)


def test_phase5_tuning_in_repo_config():
    # Erste Anpassung anhand des Rückblicks vom 07.11. (siehe README „Feintuning“).
    cfg = config.load(ROOT / "config.yaml")
    assert cfg.filters.max_price_cv == 0.07
    assert cfg.sizing.max_volume_share == 0.04
    assert cfg.filters.max_price_cv <= cfg.risk.red_min_cv
