import http.client
import urllib.error
import urllib.request
from urllib.parse import parse_qs, urlsplit

import pytest

from gw2tp.fetch import (
    MAX_IDS_PER_REQUEST,
    ApiError,
    _AllowlistRedirectHandler,
    check_url,
    chunked,
)

from .conftest import FakeOpener


def ids_of(req):
    return [int(x) for x in parse_qs(urlsplit(req.full_url).query)["ids"][0].split(",")]


def test_batches_at_most_200_ids(make_client):
    def handler(req):
        return (200, [{"id": i} for i in ids_of(req)])

    opener = FakeOpener(handler=handler)
    client = make_client(opener)
    records = client.get_prices(range(1, 451))
    assert [len(ids_of(r)) for r in opener.requests] == [200, 200, 50]
    assert len(records) == 450
    assert client.stats.total_batches == 3
    assert client.stats.failed_batches == 0


def test_requests_only_go_to_official_api(make_client):
    opener = FakeOpener([(200, [1, 2])])
    make_client(opener).get_price_ids()
    req = opener.requests[0]
    assert req.full_url == "https://api.guildwars2.com/v2/commerce/prices"
    assert req.get_method() == "GET"
    assert req.get_header("User-agent").startswith("gw2tp-flipper/")
    assert req.get_header("Authorization") is None


def test_retry_on_429_honours_retry_after(make_client, fake_time):
    opener = FakeOpener([(429, {"text": "too many"}, {"Retry-After": "7"}), (200, [1])])
    client = make_client(opener)
    assert client.get_price_ids() == [1]
    assert 7 in fake_time.sleeps
    assert client.stats.retries == 1


def test_exponential_backoff_on_5xx(make_client, fake_time):
    opener = FakeOpener([(503, {}), (502, {}), (500, {}), (200, [1])])
    client = make_client(opener, min_interval_s=0)
    assert client.get_price_ids() == [1]
    assert fake_time.sleeps == [1.0, 2.0, 4.0]


def test_backoff_is_capped(make_client, fake_time):
    opener = FakeOpener([(429, {}, {"Retry-After": "9999"}), (200, [1])])
    make_client(opener, min_interval_s=0, backoff_cap_s=30).get_price_ids()
    assert fake_time.sleeps == [30]


def test_gives_up_after_max_retries(make_client):
    opener = FakeOpener(handler=lambda req: (503, {}))
    client = make_client(opener, max_retries=3)
    with pytest.raises(ApiError, match="aufgegeben"):
        client.get_price_ids()
    assert len(opener.requests) == 4


def test_network_errors_are_retried(make_client):
    opener = FakeOpener(
        [
            urllib.error.URLError("down"),
            TimeoutError(),
            ConnectionResetError(),
            http.client.IncompleteRead(b""),
            (200, [1]),
        ]
    )
    assert make_client(opener).get_price_ids() == [1]


def test_client_errors_not_retried(make_client):
    opener = FakeOpener([(400, {"text": "bad"})])
    with pytest.raises(ApiError, match="HTTP 400"):
        make_client(opener).get_price_ids()
    assert len(opener.requests) == 1


def test_404_on_id_batch_means_empty(make_client):
    opener = FakeOpener([(404, {"text": "all ids provided are invalid"})])
    assert make_client(opener).get_prices([999_999]) == []


def test_206_partial_content_is_success(make_client):
    opener = FakeOpener([(206, [{"id": 1}])])
    assert make_client(opener).get_prices([1, 999_999]) == [{"id": 1}]


def test_failed_batch_is_skipped_and_counted(make_client):
    def handler(req):
        return (503, {}) if ids_of(req)[0] == 201 else (200, [{"id": 1}])

    client = make_client(FakeOpener(handler=handler), max_retries=1)
    records = client.get_prices(range(1, 401))
    assert records == [{"id": 1}]
    assert (client.stats.failed_batches, client.stats.total_batches) == (1, 2)


def test_non_list_batch_counted_as_failure(make_client):
    client = make_client(FakeOpener([(200, {"oops": True})]))
    assert client.get_prices([1]) == []
    assert client.stats.failed_batches == 1


def test_invalid_json_raises(make_client):
    with pytest.raises(ApiError, match="JSON"):
        make_client(FakeOpener([(200, b"<html>")])).get_price_ids()


def test_response_size_limited(make_client, monkeypatch):
    monkeypatch.setattr("gw2tp.fetch.MAX_RESPONSE_BYTES", 10)
    with pytest.raises(ApiError, match="zu groß"):
        make_client(FakeOpener([(200, b"[" + b"1," * 20 + b"1]")])).get_price_ids()


def test_redirect_to_foreign_host_rejected_after_open(make_client):
    opener = FakeOpener([(200, [1], {"_url": "https://evil.example/v2/commerce/prices"})])
    with pytest.raises(ApiError, match="Unerlaubtes Ziel"):
        make_client(opener).get_price_ids()


def test_redirect_handler_blocks_foreign_hosts():
    handler = _AllowlistRedirectHandler()
    req = urllib.request.Request("https://api.guildwars2.com/v2/items")
    with pytest.raises(ApiError):
        handler.redirect_request(req, None, 302, "Found", {}, "https://evil.example/")
    ok = handler.redirect_request(
        req, None, 302, "Found", {}, "https://api.guildwars2.com/v2/items?x=1"
    )
    assert ok.full_url.startswith("https://api.guildwars2.com/")


@pytest.mark.parametrize(
    "url",
    [
        "http://api.guildwars2.com/v2/items",
        "https://api.guildwars2.com.evil.example/v2",
        "https://evil.example/?h=api.guildwars2.com",
        "https://user:pw@api.guildwars2.com/v2",
        "https://api.guildwars2.com:8080/v2",
        "file:///etc/passwd",
    ],
)
def test_check_url_rejects(url):
    with pytest.raises(ApiError):
        check_url(url)


@pytest.mark.parametrize("path", ["/v2/../v1", "//evil.example/v2", "/v2/items?x=1", "v2/items"])
def test_invalid_paths_rejected(make_client, path):
    opener = FakeOpener([])
    with pytest.raises(ApiError, match="Pfad"):
        make_client(opener).get_json(path)
    assert opener.requests == []


def test_rate_limit_spacing(make_client, fake_time):
    opener = FakeOpener(handler=lambda req: (200, []))
    client = make_client(opener, min_interval_s=0.25)
    client.get_prices(range(1, 1001))  # 5 Requests
    assert fake_time.sleeps == [0.25] * 4


@pytest.mark.parametrize("bad", [[0], [-1], ["1"], [True], [1.5]])
def test_chunked_rejects_invalid_ids(bad):
    with pytest.raises(ValueError):
        chunked(bad, MAX_IDS_PER_REQUEST)


def test_chunked_rejects_oversized_batches():
    with pytest.raises(ValueError):
        chunked([1], 201)
