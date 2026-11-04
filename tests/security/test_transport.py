"""TLS and HTTPS checks using only a normal client handshake (no protocol fuzzing)."""

import socket
import ssl
from datetime import UTC, datetime
from urllib.parse import urlparse

import pytest
import requests

from qa_portfolio.config import load_settings

_settings = load_settings()
HOSTS = {
    "saucedemo": urlparse(_settings.ui_base_url).hostname,
    "restful-booker": urlparse(_settings.api_base_url).hostname,
}
MIN_CERT_DAYS_LEFT = 14

# target -> reason, same idea as KNOWN_FINDINGS in test_security_headers.py
NO_HTTPS_REDIRECT: dict[str, str] = {}


def _handshake(host: str) -> tuple[str, dict]:
    """Connect with the default (verifying) context: trusted CA and hostname match are required."""
    context = ssl.create_default_context()
    with (
        socket.create_connection((host, 443), timeout=_settings.request_timeout) as sock,
        context.wrap_socket(sock, server_hostname=host) as tls,
    ):
        return tls.version() or "", tls.getpeercert() or {}


@pytest.mark.smoke
@pytest.mark.parametrize("target", HOSTS)
def test_certificate_is_trusted_and_matches_host(target: str) -> None:
    # Raises ssl.SSLCertVerificationError if the chain or hostname is wrong.
    _handshake(HOSTS[target])


@pytest.mark.parametrize("target", HOSTS)
def test_negotiates_modern_tls(target: str) -> None:
    version, _ = _handshake(HOSTS[target])
    assert version in ("TLSv1.2", "TLSv1.3")


@pytest.mark.parametrize("target", HOSTS)
def test_certificate_not_close_to_expiry(target: str) -> None:
    _, cert = _handshake(HOSTS[target])
    expires = datetime.fromtimestamp(ssl.cert_time_to_seconds(cert["notAfter"]), tz=UTC)
    days_left = (expires - datetime.now(UTC)).days
    assert days_left >= MIN_CERT_DAYS_LEFT, f"Certificate expires in {days_left} days"


def _redirect_cases():
    for target in HOSTS:
        reason = NO_HTTPS_REDIRECT.get(target)
        marks = [pytest.mark.xfail(reason=f"SECURITY FINDING: {reason}")] if reason else []
        yield pytest.param(target, marks=marks, id=target)


@pytest.mark.parametrize("target", list(_redirect_cases()))
def test_plain_http_redirects_to_https(target: str) -> None:
    response = requests.get(
        f"http://{HOSTS[target]}/", allow_redirects=False, timeout=_settings.request_timeout
    )
    assert response.status_code in (301, 302, 307, 308)
    assert response.headers["Location"].startswith("https://")
