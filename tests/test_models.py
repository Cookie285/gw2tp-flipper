import pytest

from gw2tp.models import Item, Price, ValidationError, parse_id_list, parse_many

from .conftest import raw_item, raw_price


def test_valid_price():
    p = Price.parse(raw_price(5, bid=10, ask=20, demand=3, supply=4))
    assert (p.id, p.buys.unit_price, p.sells.unit_price, p.buys.quantity, p.sells.quantity) == (
        5,
        10,
        20,
        3,
        4,
    )


@pytest.mark.parametrize(
    "mutate",
    [
        lambda r: r.pop("id"),
        lambda r: r.update(id="5"),
        lambda r: r.update(id=True),
        lambda r: r.update(id=0),
        lambda r: r.update(id=-3),
        lambda r: r.pop("buys"),
        lambda r: r.update(sells=None),
        lambda r: r.update(sells=[1, 2]),
        lambda r: r["buys"].update(unit_price=1.5),
        lambda r: r["buys"].update(unit_price=-1),
        lambda r: r["sells"].update(quantity="7"),
        lambda r: r["sells"].update(quantity=False),
        lambda r: r["sells"].update(unit_price=10**15),
        lambda r: r["sells"].pop("unit_price"),
    ],
)
def test_invalid_prices_rejected(mutate):
    raw = raw_price()
    mutate(raw)
    with pytest.raises(ValidationError):
        Price.parse(raw)


def test_parse_many_drops_invalid_and_counts():
    records = [raw_price(1), {"id": "x"}, None, "junk", 42, raw_price(2)]
    valid, rejected = parse_many(records, Price.parse)
    assert [p.id for p in valid] == [1, 2]
    assert rejected == 4


def test_valid_item():
    item = Item.parse(raw_item(19721, flags=["NoSalvage"]))
    assert item.name == "Glob of Ectoplasm"
    assert item.chat_link == "[&AgGpTAAA]"
    assert item.flags == {"NoSalvage"}
    assert item.icon.startswith("https://render.guildwars2.com/")


def test_item_name_control_characters_removed():
    item = Item.parse(raw_item(name="Evil\nName‮\x00 Item"))
    assert item.name == "Evil Name Item"


@pytest.mark.parametrize(
    "icon",
    [
        "http://render.guildwars2.com/file/x.png",
        "https://evil.example/file/x.png",
        "https://render.guildwars2.com.evil.example/x.png",
        "https://user@render.guildwars2.com/x.png",
        "https://render.guildwars2.com:8443/x.png",
        "https://render.guildwars2.com/x.png?a=b",
        "javascript:alert(1)",
        'https://render.guildwars2.com/x".png',
        123,
    ],
)
def test_item_icon_must_be_render_host(icon):
    raw = raw_item()
    raw["icon"] = icon
    with pytest.raises(ValidationError):
        Item.parse(raw)


def test_item_without_icon_ok():
    raw = raw_item()
    del raw["icon"]
    assert Item.parse(raw).icon is None


@pytest.mark.parametrize(
    "mutate",
    [
        lambda r: r.update(name=""),
        lambda r: r.update(name="   "),
        lambda r: r.update(name=None),
        lambda r: r.update(name="x" * 500),
        lambda r: r.update(chat_link="[&AgGpTAAA]<script>"),
        lambda r: r.update(chat_link="`rm -rf`"),
        lambda r: r.pop("chat_link"),
        lambda r: r.update(flags="AccountBound"),
        lambda r: r.update(flags=[1]),
        lambda r: r.update(flags=["Account Bound"]),
        lambda r: r.update(rarity="<b>"),
    ],
)
def test_invalid_items_rejected(mutate):
    raw = raw_item()
    mutate(raw)
    with pytest.raises(ValidationError):
        Item.parse(raw)


def test_parse_id_list():
    ids, rejected = parse_id_list([1, 2, "3", 2, -1, 4])
    assert ids == [1, 2, 4]
    assert rejected == 2
    with pytest.raises(ValidationError):
        parse_id_list({"ids": [1]})
