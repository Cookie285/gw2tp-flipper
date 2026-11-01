"""Gebühren- und Gewinnberechnung. Alle Beträge sind ganze Kupfermünzen (1 g = 100 s = 10 000 c).

Handelsposten-Gebühren:
* Einstellgebühr 5 % des Verkaufspreises (wird beim Einstellen fällig, nicht erstattbar),
* Verkaufssteuer 10 % des Verkaufspreises (wird beim Verkauf einbehalten).

Beide Gebühren betragen im Spiel mindestens 1 Kupfer. Wir runden jeweils kaufmännisch auf ganze
Kupfer. Ergebnis: Netto ≈ Verkaufspreis × 0,85 − Kaufpreis (siehe SPEC.md).
"""

from __future__ import annotations

from dataclasses import dataclass

COPPER_PER_SILVER = 100
COPPER_PER_GOLD = 10_000
_BASIS_POINTS = 10_000


@dataclass(frozen=True, slots=True)
class FeeSchedule:
    """Gebührensätze als Anteil (0,05 = 5 %)."""

    listing_fee: float = 0.05
    exchange_fee: float = 0.10

    def __post_init__(self) -> None:
        for name in ("listing_fee", "exchange_fee"):
            value = getattr(self, name)
            if not isinstance(value, int | float) or isinstance(value, bool):
                raise TypeError(f"{name} muss eine Zahl sein")
            if not 0 <= value < 1:
                raise ValueError(f"{name} muss im Bereich [0, 1) liegen")


DEFAULT_FEES = FeeSchedule()


def _fee(price: int, rate: float) -> int:
    """Gebühr in Kupfer: kaufmännisch gerundet, mindestens 1 Kupfer (bei Preis > 0)."""
    if price <= 0:
        return 0
    bp = round(rate * _BASIS_POINTS)
    if bp == 0:
        return 0
    # Ganzzahlige Rundung half-up, um Float-Fehler bei großen Preisen zu vermeiden.
    return max(1, (price * bp + _BASIS_POINTS // 2) // _BASIS_POINTS)


def listing_fee(sell_price: int, fees: FeeSchedule = DEFAULT_FEES) -> int:
    return _fee(sell_price, fees.listing_fee)


def exchange_fee(sell_price: int, fees: FeeSchedule = DEFAULT_FEES) -> int:
    return _fee(sell_price, fees.exchange_fee)


def total_fees(sell_price: int, fees: FeeSchedule = DEFAULT_FEES) -> int:
    return listing_fee(sell_price, fees) + exchange_fee(sell_price, fees)


def buy_price_from_bid(highest_bid: int) -> int:
    """Eigenes Kaufgebot: höchstes Kaufgebot + 1 Kupfer."""
    return highest_bid + 1


def sell_price_from_ask(lowest_ask: int) -> int:
    """Eigenes Verkaufsangebot: niedrigstes Verkaufsangebot − 1 Kupfer."""
    return lowest_ask - 1


def net_profit(buy_price: int, sell_price: int, fees: FeeSchedule = DEFAULT_FEES) -> int:
    """Netto-Gewinn pro Stück nach Einstellgebühr und Verkaufssteuer."""
    return sell_price - total_fees(sell_price, fees) - buy_price


def roi(buy_price: int, profit: int) -> float:
    """Return on Investment = Netto-Gewinn ÷ Kaufpreis."""
    if buy_price <= 0:
        raise ValueError("Kaufpreis muss positiv sein")
    return profit / buy_price
