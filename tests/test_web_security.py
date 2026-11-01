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
        assert not re.match(r"[a-z]+:", url), url  # nur relative URLs


def test_only_static_files_are_deployed():
    allowed = {".html", ".js", ".css", ".svg", ".json"}
    assert {p.suffix for p in WEB.iterdir()} <= allowed
