"""Minimaler, defensiver Client für die offizielle GW2-API.

* ruft ausschließlich https://api.guildwars2.com auf (auch Redirects werden geprüft),
* setzt Timeouts und begrenzt die Antwortgröße,
* bündelt IDs (max. 200 pro Request) und hält einen Mindestabstand zwischen Requests ein,
* wiederholt bei 429/5xx/Netzwerkfehlern mit exponentiellem Backoff (Retry-After wird beachtet).

Es werden nur öffentliche Endpunkte ohne API-Key verwendet.
"""

from __future__ import annotations

import http.client
import json
import logging
import random
import re
import time
import urllib.error
import urllib.request
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, field
from typing import Any, Protocol
from urllib.parse import urlencode, urlsplit

from . import __version__

log = logging.getLogger(__name__)

API_HOST = "api.guildwars2.com"
BASE_URL = f"https://{API_HOST}"
MAX_IDS_PER_REQUEST = 200
MAX_RESPONSE_BYTES = 20 * 1024 * 1024
SCHEMA_VERSION = "2022-03-23T19:00:00.000Z"
USER_AGENT = f"gw2tp-flipper/{__version__} (+https://github.com/cookie285/gw2tp-flipper)"
RETRY_STATUS = frozenset({429, 500, 502, 503, 504})
_PATH_RE = re.compile(r"^/v2(/[a-z]+)+$")


class ApiError(RuntimeError):
    """Nicht behebbarer Fehler beim API-Zugriff."""


class _Opener(Protocol):
    def open(self, req: urllib.request.Request, timeout: float) -> Any: ...


def check_url(url: str) -> None:
    """Nur HTTPS-URLs auf api.guildwars2.com zulassen."""
    parts = urlsplit(url)
    if (
        parts.scheme != "https"
        or parts.hostname != API_HOST
        or parts.port not in (None, 443)
        or parts.username is not None
        or parts.password is not None
    ):
        raise ApiError(f"Unerlaubtes Ziel: {parts.scheme}://{parts.hostname}")


class _AllowlistRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[override]
        check_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def default_opener() -> _Opener:
    # Jede URL wird vor dem Request per check_url geprüft (nur https://api.guildwars2.com);
    # der Redirect-Handler prüft zusätzlich jedes Redirect-Ziel.
    return urllib.request.build_opener(_AllowlistRedirectHandler())


@dataclass
class FetchStats:
    requests: int = 0
    retries: int = 0
    failed_batches: int = 0
    total_batches: int = 0
    errors: list[str] = field(default_factory=list)


@dataclass
class Gw2Client:
    opener: _Opener = field(default_factory=default_opener)
    sleep: Callable[[float], None] = time.sleep
    clock: Callable[[], float] = time.monotonic
    jitter: Callable[[], float] = random.random
    timeout_s: float = 20.0
    max_retries: int = 5
    min_interval_s: float = 0.25
    backoff_base_s: float = 1.0
    backoff_cap_s: float = 60.0
    stats: FetchStats = field(default_factory=FetchStats)
    _last_request: float | None = field(default=None, init=False, repr=False)

    # --- Low level -----------------------------------------------------------------------

    def _throttle(self) -> None:
        if self._last_request is not None:
            wait = self.min_interval_s - (self.clock() - self._last_request)
            if wait > 0:
                self.sleep(wait)
        self._last_request = self.clock()

    def _backoff(self, attempt: int, retry_after: str | None) -> float:
        if retry_after is not None and retry_after.strip().isdigit():
            return min(float(retry_after.strip()), self.backoff_cap_s)
        delay = self.backoff_base_s * (2**attempt)
        return min(delay + self.jitter() * self.backoff_base_s, self.backoff_cap_s)

    def get_json(
        self, path: str, params: dict[str, str] | None = None, *, empty_on_404: bool = False
    ) -> Any:
        if not _PATH_RE.fullmatch(path):
            raise ApiError("Ungültiger API-Pfad")
        url = BASE_URL + path
        if params:
            url += "?" + urlencode(params)
        check_url(url)

        last_error = "unbekannt"
        for attempt in range(self.max_retries + 1):
            if attempt:
                self.stats.retries += 1
            self._throttle()
            self.stats.requests += 1
            req = urllib.request.Request(  # noqa: S310 - Schema/Host per check_url geprüft
                url,
                headers={
                    "Accept": "application/json",
                    "User-Agent": USER_AGENT,
                    "X-Schema-Version": SCHEMA_VERSION,
                },
                method="GET",
            )
            retry_after: str | None = None
            try:
                with self.opener.open(req, timeout=self.timeout_s) as resp:
                    final_url = resp.geturl() if hasattr(resp, "geturl") else url
                    check_url(final_url)
                    return _decode(_read_limited(resp))
            except urllib.error.HTTPError as exc:
                status = exc.code
                if status == 404 and empty_on_404:
                    return []
                if status not in RETRY_STATUS:
                    raise ApiError(f"HTTP {status} für {path}") from None
                retry_after = exc.headers.get("Retry-After") if exc.headers else None
                last_error = f"HTTP {status}"
            except (urllib.error.URLError, http.client.HTTPException, TimeoutError, OSError) as exc:
                last_error = type(exc).__name__
            if attempt < self.max_retries:
                delay = self._backoff(attempt, retry_after)
                log.info("%s bei %s, neuer Versuch in %.1f s", last_error, path, delay)
                self.sleep(delay)
        raise ApiError(f"{path}: aufgegeben nach {self.max_retries + 1} Versuchen ({last_error})")

    # --- Endpunkte -----------------------------------------------------------------------

    def get_batched(self, path: str, ids: Iterable[int]) -> list[Any]:
        """IDs in Blöcken zu max. 200 abfragen. Fehlgeschlagene Blöcke werden gezählt und
        übersprungen; der Aufrufer entscheidet anhand von ``stats``, ob das Ergebnis reicht."""
        records: list[Any] = []
        for batch in chunked(ids, MAX_IDS_PER_REQUEST):
            self.stats.total_batches += 1
            try:
                data = self.get_json(path, {"ids": ",".join(map(str, batch))}, empty_on_404=True)
            except ApiError as exc:
                self.stats.failed_batches += 1
                self.stats.errors.append(str(exc))
                log.warning("Block übersprungen: %s", exc)
                continue
            if not isinstance(data, list):
                self.stats.failed_batches += 1
                self.stats.errors.append(f"{path}: Liste erwartet")
                continue
            records.extend(data)
        return records

    def get_price_ids(self) -> Any:
        return self.get_json("/v2/commerce/prices")

    def get_prices(self, ids: Iterable[int]) -> list[Any]:
        return self.get_batched("/v2/commerce/prices", ids)

    def get_items(self, ids: Iterable[int]) -> list[Any]:
        return self.get_batched("/v2/items", ids)


def chunked(ids: Iterable[int], size: int) -> list[Sequence[int]]:
    if not 1 <= size <= MAX_IDS_PER_REQUEST:
        raise ValueError("Blockgröße muss zwischen 1 und 200 liegen")
    values = list(ids)
    for value in values:
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            raise ValueError("IDs müssen positive Ganzzahlen sein")
    return [values[i : i + size] for i in range(0, len(values), size)]


def _read_limited(resp: Any) -> bytes:
    body = resp.read(MAX_RESPONSE_BYTES + 1)
    if len(body) > MAX_RESPONSE_BYTES:
        raise ApiError("Antwort zu groß")
    return body


def _decode(body: bytes) -> Any:
    try:
        return json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise ApiError("Antwort ist kein gültiges JSON") from None
