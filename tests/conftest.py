"""Fixtures and hooks shared by all suites."""

from pathlib import Path

import pytest

from qa_portfolio.api.booking_client import BookingClient
from qa_portfolio.config import Settings, load_settings

SUITE_MARKERS = ("api", "ui", "security")


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Tag each test with its suite marker based on its folder, e.g. tests/api -> api."""
    for item in items:
        parts = Path(str(item.fspath)).parts
        for marker in SUITE_MARKERS:
            if marker in parts:
                item.add_marker(getattr(pytest.mark, marker))


def pytest_html_report_title(report) -> None:
    report.title = "QA Automation Portfolio - Test Report"


@pytest.fixture(scope="session")
def settings() -> Settings:
    return load_settings()


@pytest.fixture(scope="session")
def api_client(settings: Settings) -> BookingClient:
    """Unauthenticated client."""
    return BookingClient(settings.api_base_url, timeout=settings.request_timeout)


@pytest.fixture(scope="session")
def auth_token(settings: Settings) -> str:
    client = BookingClient(settings.api_base_url, timeout=settings.request_timeout)
    return client.authenticate(settings.api_username, settings.api_password)


@pytest.fixture(scope="session")
def auth_client(settings: Settings, auth_token: str) -> BookingClient:
    """Client that sends a valid token cookie with every request."""
    return BookingClient(settings.api_base_url, timeout=settings.request_timeout, token=auth_token)
