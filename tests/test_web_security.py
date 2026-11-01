"""Statische Sicherheitsprüfung des Dashboards (web/)."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

WEB = Path(__file__).resolve().parents[1] / "web"
JS = sorted(WEB.glob("*.js"))
HTML = WEB / "index.html"

REQUIRED_CSP = {
    "default-src": "'self'",
    "script-src": "'self'",
    "style-src": "'self'",
    "img-src": "'self' https://render.guildwars2.com",
    "connect-src": "'self' https://api.guildwars2.com",
    "object-src": "'none'",
    "base-uri": "'none'",
    "form-action": "'none'",
    "require-trusted-types-for": "'script'",
}


# Einzige erlaubte externe Verlinkung (reine Navigation, kein Laden von Ressourcen).
EXTERNAL_LINKS = {"https://account.arena.net/applications"}


def _csp() -> dict[str, str]:
    html = HTML.read_text(encoding="utf-8")
    m = re.search(r'<meta http-equiv="Content-Security-Policy" content="([^"]+)">', html)
    assert m, "CSP-Meta-Tag fehlt"
    out = {}
    for part in m.group(1).split(";"):
        name, _, value = part.strip().partition(" ")
        out[name] = value.strip()
    return out


def test_csp_is_strict():
    csp = _csp()
    for name, value in REQUIRED_CSP.items():
        assert csp.get(name) == value, name
    joined = " ".join(csp.values())
    assert "unsafe-inline" not in joined
    assert "unsafe-eval" not in joined
    assert "*" not in joined and "data:" not in joined


@pytest.mark.parametrize("path", JS, ids=lambda p: p.name)
def test_no_dangerous_dom_sinks(path):
    src = path.read_text(encoding="utf-8")
    for pattern in [
        r"\.innerHTML",
        r"\.outerHTML",
        r"insertAdjacentHTML",
        r"document\.write",
        r"\beval\s*\(",
        r"new\s+Function",
        r"setTimeout\s*\(\s*['\"`]",
        r"setInterval\s*\(\s*['\"`]",
        r"createContextualFragment",
        r"DOMParser",
    ]:
        assert not re.search(pattern, src), f"{path.name}: {pattern}"


@pytest.mark.parametrize("path", JS, ids=lambda p: p.name)
def test_only_allowed_hosts(path):
    src = path.read_text(encoding="utf-8")
    hosts = set(re.findall(r"https?://([A-Za-z0-9.-]+)", src.replace("\\.", ".")))
    assert hosts <= {"render.guildwars2.com", "api.guildwars2.com"}, hosts


def test_html_has_no_inline_code_or_external_resources():
    html = HTML.read_text(encoding="utf-8")
    assert re.findall(r"<script\b[^>]*>", html) == ['<script type="module" src="app.js">']
    assert "<style" not in html
    assert not re.search(r"\sstyle\s*=", html)
    assert not re.search(r"\son[a-z]+\s*=", html, re.IGNORECASE)
    for url in re.findall(r'(?:src|href)="([^"]+)"', html):
        if url in EXTERNAL_LINKS:
            continue
        assert not re.match(r"[a-z]+:", url), url  # sonst nur relative URLs
    # Externe Links öffnen ohne Referrer und ohne Zugriff auf window.opener.
    for tag in re.findall(r"<a\b[^>]*>", html):
        if 'href="https://' in tag:
            assert 'rel="noopener noreferrer"' in tag, tag


def test_only_static_files_are_deployed():
    allowed = {".html", ".js", ".css", ".svg", ".json"}  # .json = package.json, nicht deployt
    assert {p.suffix for p in WEB.iterdir()} <= allowed


# --- Phase 4: Umgang mit dem persönlichen API-Key -----------------------------------------


def _sources() -> dict[str, str]:
    return {p.name: p.read_text(encoding="utf-8") for p in JS}


AUTH_PATHS = {
    "/v2/tokeninfo",
    "/v2/commerce/delivery",
    "/v2/commerce/transactions/current/buys",
    "/v2/commerce/transactions/current/sells",
    "/v2/commerce/transactions/history/buys",
    "/v2/commerce/transactions/history/sells",
}


def test_access_token_only_in_api_client():
    # Die GW2-API unterstützt keinen CORS-Preflight; im Browser geht der Key daher nur als
    # access_token. Das darf ausschließlich der API-Client tun, und nur für AUTH_PATHS.
    for name, src in _sources().items():
        if name != "gw2api.js":
            assert "access_token" not in src, name
    api = (WEB / "gw2api.js").read_text(encoding="utf-8")
    assert api.count('searchParams.set("access_token"') == 1
    block = re.search(r"AUTH_PATHS = new Set\(\[(.*?)\]\)", api, re.DOTALL).group(1)
    assert set(re.findall(r'"([^"]+)"', block)) == AUTH_PATHS
    assert "if (!AUTH_PATHS.has(path))" in api


def test_requests_avoid_preflight_and_leaks():
    api = (WEB / "gw2api.js").read_text(encoding="utf-8")
    code = re.sub(r"^\s*//.*$", "", api, flags=re.MULTILINE)
    assert "Authorization" not in code  # würde einen Preflight auslösen
    assert 'headers: { Accept: "application/json" }' in api
    for snippet in [
        'redirect: "error"',
        'credentials: "omit"',
        'referrerPolicy: "no-referrer"',
        'cache: "no-store"',
    ]:
        assert snippet in api, snippet
    for name, src in _sources().items():
        c = re.sub(r"^\s*//.*$", "", src, flags=re.MULTILINE)
        assert not re.search(r"\bAuthorization\b", c), name


def test_network_access_only_via_known_modules():
    # Nur der API-Client (api.guildwars2.com) und die Einkaufsliste (gleicher Ursprung) laden Daten.
    for name, src in _sources().items():
        if re.search(r"\bfetch\s*\(", src):
            assert name in {"gw2api.js", "shopping.js"}, name
        assert "XMLHttpRequest" not in src and "sendBeacon" not in src and "WebSocket" not in src
    shopping = (WEB / "shopping.js").read_text(encoding="utf-8")
    assert re.findall(r"fetch\(([^,]+),", shopping) == ["DATA_URL"]


def test_key_storage_only_in_keystore():
    for name, src in _sources().items():
        if name in {"keystore.js"}:
            continue
        assert "sessionStorage" not in src, name
        if "localStorage" in src:
            assert name == "shopping.js", name  # nur das (unkritische) Budget
            assert "apiKey" not in src


def test_no_console_logging():
    for name, src in _sources().items():
        assert not re.search(r"\bconsole\.", src), name


def test_key_input_is_not_autocompleted():
    html = HTML.read_text(encoding="utf-8")
    tag = re.search(r'<input id="api-key"[^>]*>', html).group(0)
    assert 'type="password"' in tag
    assert 'autocomplete="off"' in tag
    assert 'spellcheck="false"' in tag
