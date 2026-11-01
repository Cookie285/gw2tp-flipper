"""Validierte Datenmodelle für API-Antworten.

API-Antworten gelten als nicht vertrauenswürdig. Jeder Datensatz wird auf Typen, Pflichtfelder und
Wertebereiche geprüft. Ungültige Datensätze werden verworfen (und gezählt), statt das Programm
abstürzen zu lassen.
"""

from __future__ import annotations

import logging
import re
import unicodedata
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlsplit

log = logging.getLogger(__name__)

MAX_ITEM_ID = 10_000_000
MAX_PRICE_COPPER = 10_000_000_000  # 1 Mio. Gold, deutlich über jedem realen TP-Preis
MAX_QUANTITY = 1_000_000_000
MAX_NAME_LENGTH = 200
ICON_HOST = "render.guildwars2.com"
CHAT_LINK_RE = re.compile(r"^\[&[A-Za-z0-9+/]{1,64}={0,2}\]$")
FLAG_RE = re.compile(r"^[A-Za-z]{1,64}$")
MAX_FLAGS = 64


class ValidationError(ValueError):
    """Ein Datensatz entspricht nicht dem erwarteten Schema."""


def _int(value: Any, field: str, *, minimum: int = 0, maximum: int) -> int:
    # bool ist in Python ein int-Subtyp, wird hier aber explizit abgelehnt.
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValidationError(f"{field}: Ganzzahl erwartet")
    if not minimum <= value <= maximum:
        raise ValidationError(f"{field}: außerhalb des gültigen Bereichs")
    return value


def _dict(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValidationError(f"{field}: Objekt erwartet")
    return value


def item_id(value: Any, field: str = "id") -> int:
    return _int(value, field, minimum=1, maximum=MAX_ITEM_ID)


def clean_text(value: Any, field: str, *, max_length: int = MAX_NAME_LENGTH) -> str:
    """Text prüfen und Steuerzeichen entfernen (Zeilenumbrüche, Bidi-Overrides usw.)."""
    if not isinstance(value, str):
        raise ValidationError(f"{field}: Text erwartet")
    cleaned = "".join(ch if not unicodedata.category(ch).startswith("C") else " " for ch in value)
    cleaned = " ".join(cleaned.split())
    if not cleaned:
        raise ValidationError(f"{field}: leer")
    if len(cleaned) > max_length:
        raise ValidationError(f"{field}: zu lang")
    return cleaned


@dataclass(frozen=True, slots=True)
class Quote:
    unit_price: int
    quantity: int

    @classmethod
    def parse(cls, raw: Any, field: str) -> Quote:
        data = _dict(raw, field)
        return cls(
            unit_price=_int(
                data.get("unit_price"), f"{field}.unit_price", maximum=MAX_PRICE_COPPER
            ),
            quantity=_int(data.get("quantity"), f"{field}.quantity", maximum=MAX_QUANTITY),
        )


@dataclass(frozen=True, slots=True)
class Price:
    """Eintrag aus /v2/commerce/prices: höchstes Gebot (buys), niedrigstes Angebot (sells)."""

    id: int
    buys: Quote
    sells: Quote

    @classmethod
    def parse(cls, raw: Any) -> Price:
        data = _dict(raw, "price")
        return cls(
            id=item_id(data.get("id")),
            buys=Quote.parse(data.get("buys"), "buys"),
            sells=Quote.parse(data.get("sells"), "sells"),
        )


@dataclass(frozen=True, slots=True)
class Item:
    """Ausgewählte Felder aus /v2/items."""

    id: int
    name: str
    icon: str | None
    chat_link: str
    flags: frozenset[str]
    rarity: str | None = None
    type: str | None = None

    @classmethod
    def parse(cls, raw: Any) -> Item:
        data = _dict(raw, "item")
        flags_raw = data.get("flags", [])
        if not isinstance(flags_raw, list) or len(flags_raw) > MAX_FLAGS:
            raise ValidationError("flags: Liste erwartet")
        if not all(isinstance(f, str) and FLAG_RE.fullmatch(f) for f in flags_raw):
            raise ValidationError("flags: ungültiger Eintrag")

        chat_link = data.get("chat_link")
        if not isinstance(chat_link, str) or not CHAT_LINK_RE.fullmatch(chat_link):
            raise ValidationError("chat_link: ungültig")

        return cls(
            id=item_id(data.get("id")),
            name=clean_text(data.get("name"), "name"),
            icon=_icon(data.get("icon")),
            chat_link=chat_link,
            flags=frozenset(flags_raw),
            rarity=_optional_word(data.get("rarity"), "rarity"),
            type=_optional_word(data.get("type"), "type"),
        )


def _optional_word(value: Any, field: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not FLAG_RE.fullmatch(value):
        raise ValidationError(f"{field}: ungültig")
    return value


def _icon(value: Any) -> str | None:
    """Icon-URL nur akzeptieren, wenn sie per HTTPS auf render.guildwars2.com zeigt."""
    if value is None:
        return None
    if not isinstance(value, str) or len(value) > 500:
        raise ValidationError("icon: ungültig")
    parts = urlsplit(value)
    if (
        parts.scheme != "https"
        or parts.hostname != ICON_HOST
        or parts.port is not None
        or parts.username is not None
        or parts.password is not None
        or not re.fullmatch(r"[A-Za-z0-9/._-]+", parts.path or "")
        or parts.query
        or parts.fragment
    ):
        raise ValidationError("icon: unerlaubter Host oder Pfad")
    return value


def parse_many[T](records: Iterable[Any], parser: Callable[[Any], T]) -> tuple[list[T], int]:
    """Alle gültigen Datensätze parsen und die Anzahl verworfener Datensätze zurückgeben."""
    valid: list[T] = []
    rejected = 0
    for raw in records:
        try:
            valid.append(parser(raw))
        except ValidationError as exc:
            rejected += 1
            log.debug("Datensatz verworfen: %s", exc)
    if rejected:
        log.warning("%d ungültige Datensätze verworfen", rejected)
    return valid, rejected


def parse_id_list(raw: Any) -> tuple[list[int], int]:
    """Antwort einer ID-Liste (z. B. /v2/commerce/prices ohne Parameter) validieren."""
    if not isinstance(raw, list):
        raise ValidationError("ID-Liste erwartet")
    ids, rejected = parse_many(raw, item_id)
    # Duplikate entfernen, Reihenfolge beibehalten.
    return list(dict.fromkeys(ids)), rejected
