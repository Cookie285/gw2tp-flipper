import pytest

from gw2tp.fees import (
    FeeSchedule,
    buy_price_from_bid,
    exchange_fee,
    listing_fee,
    net_profit,
    roi,
    sell_price_from_ask,
    total_fees,
)


def test_bid_plus_one_ask_minus_one():
    assert buy_price_from_bid(1000) == 1001
    assert sell_price_from_ask(1500) == 1499


@pytest.mark.parametrize(
    ("price", "listing", "exchange"),
    [
        (1, 1, 1),  # Mindestgebühr 1 Kupfer je Gebühr
        (10, 1, 1),  # 0,5 → 1 (half-up), 1,0 → 1
        (29, 1, 3),  # 1,45 → 1; 2,9 → 3
        (30, 2, 3),  # 1,5 → 2 (half-up)
        (100, 5, 10),
        (1_500, 75, 150),
        (10_000_000, 500_000, 1_000_000),
    ],
)
def test_fee_rounding_and_minimum(price, listing, exchange):
    assert listing_fee(price) == listing
    assert exchange_fee(price) == exchange
    assert total_fees(price) == listing + exchange


def test_no_fee_on_zero_price():
    assert total_fees(0) == 0


def test_net_profit_matches_spec_formula_for_round_prices():
    # Verkaufspreis × 0,85 − Kaufpreis
    assert net_profit(1000, 1500) == int(1500 * 0.85) - 1000 == 275
    assert net_profit(1000, 1000) == -150


def test_net_profit_small_prices_respect_minimum_fee():
    # 10c Verkauf: 1c + 1c Gebühren → 8c Erlös
    assert net_profit(5, 10) == 3


def test_roi():
    assert roi(1000, 275) == pytest.approx(0.275)
    assert roi(1000, -150) == pytest.approx(-0.15)
    with pytest.raises(ValueError, match="positiv"):
        roi(0, 10)


def test_custom_fee_schedule():
    fees = FeeSchedule(listing_fee=0.0, exchange_fee=0.10)
    assert total_fees(1000, fees) == 100
    assert net_profit(800, 1000, fees) == 100


@pytest.mark.parametrize("bad", [-0.1, 1.0, 2])
def test_fee_schedule_rejects_invalid_rates(bad):
    with pytest.raises(ValueError):
        FeeSchedule(listing_fee=bad)


def test_fee_schedule_rejects_bool():
    with pytest.raises(TypeError):
        FeeSchedule(listing_fee=True)
