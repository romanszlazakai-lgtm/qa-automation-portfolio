"""Passive HTTP response header checks (OWASP Secure Headers Project baseline).

One request per target, then each header is checked separately so the report
shows exactly which control is missing. Headers that a target is known to lack
are listed in KNOWN_FINDINGS and marked xfail: they are findings on someone
else's demo site, reported here rather than hidden. Strict xfail means the test
goes red if the target fixes the header, so the list stays accurate.
"""

import re
from collections.abc import Callable

import pytest
import requests

from qa_portfolio.config import load_settings

_settings = load_settings()
TARGETS = {
    "saucedemo": f"{_settings.ui_base_url}/",
    "restful-booker": f"{_settings.api_base_url}/ping",
}

ONE_YEAR = 31_536_000


def check_hsts(h: requests.structures.CaseInsensitiveDict) -> bool:
    match = re.search(r"max-age=(\d+)", h.get("Strict-Transport-Security", ""))
    return bool(match) and int(match.group(1)) >= ONE_YEAR


def check_nosniff(h) -> bool:
    return h.get("X-Content-Type-Options", "").lower() == "nosniff"


def check_clickjacking(h) -> bool:
    csp = h.get("Content-Security-Policy", "")
    xfo = h.get("X-Frame-Options", "").upper()
    return "frame-ancestors" in csp or xfo in ("DENY", "SAMEORIGIN")


def check_csp(h) -> bool:
    return bool(h.get("Content-Security-Policy"))


def check_referrer_policy(h) -> bool:
    return bool(h.get("Referrer-Policy"))


def check_no_powered_by(h) -> bool:
    return "X-Powered-By" not in h


def check_server_hides_version(h) -> bool:
    return not re.search(r"\d+\.\d+", h.get("Server", ""))


CHECKS: dict[str, Callable] = {
    "hsts-at-least-1-year": check_hsts,
    "x-content-type-options-nosniff": check_nosniff,
    "clickjacking-protection": check_clickjacking,
    "content-security-policy": check_csp,
    "referrer-policy": check_referrer_policy,
    "no-x-powered-by": check_no_powered_by,
    "server-header-hides-version": check_server_hides_version,
}

# (target, check) -> finding text. Confirmed from real responses in CI.
_GH_PAGES = "SauceDemo is served by GitHub Pages, which does not allow custom headers"
_EXPRESS = "Restful-Booker is a plain Express app with no security middleware (e.g. helmet)"
KNOWN_FINDINGS: dict[tuple[str, str], str] = {
    ("saucedemo", "hsts-at-least-1-year"): f"no Strict-Transport-Security. {_GH_PAGES}",
    ("saucedemo", "x-content-type-options-nosniff"): f"no X-Content-Type-Options. {_GH_PAGES}",
    ("saucedemo", "clickjacking-protection"): f"page can be framed. {_GH_PAGES}",
    ("saucedemo", "content-security-policy"): f"no Content-Security-Policy. {_GH_PAGES}",
    ("saucedemo", "referrer-policy"): f"no Referrer-Policy. {_GH_PAGES}",
    ("restful-booker", "hsts-at-least-1-year"): f"no Strict-Transport-Security. {_EXPRESS}",
    ("restful-booker", "x-content-type-options-nosniff"): f"no X-Content-Type-Options. {_EXPRESS}",
    ("restful-booker", "clickjacking-protection"): f"no frame protection. {_EXPRESS}",
    ("restful-booker", "content-security-policy"): f"no Content-Security-Policy. {_EXPRESS}",
    ("restful-booker", "referrer-policy"): f"no Referrer-Policy. {_EXPRESS}",
    ("restful-booker", "no-x-powered-by"): "X-Powered-By: Express reveals the framework",
}


def _cases():
    for target in TARGETS:
        for check in CHECKS:
            reason = KNOWN_FINDINGS.get((target, check))
            marks = [pytest.mark.xfail(reason=f"SECURITY FINDING: {reason}")] if reason else []
            yield pytest.param(target, check, id=f"{target}-{check}", marks=marks)


@pytest.fixture(scope="module")
def response_headers() -> dict[str, requests.structures.CaseInsensitiveDict]:
    cache: dict[str, requests.structures.CaseInsensitiveDict] = {}

    def get(target: str) -> requests.structures.CaseInsensitiveDict:
        if target not in cache:
            response = requests.get(TARGETS[target], timeout=_settings.request_timeout)
            cache[target] = response.headers
        return cache[target]

    return get


@pytest.mark.parametrize(("target", "check"), list(_cases()))
def test_security_header(response_headers, target: str, check: str) -> None:
    headers = response_headers(target)
    assert CHECKS[check](headers), f"{check} failed for {target}. Headers: {dict(headers)}"
