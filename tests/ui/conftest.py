import base64
from typing import Any

import pytest
from playwright.sync_api import Page

from qa_portfolio.config import Settings
from qa_portfolio.pages import InventoryPage, LoginPage
from qa_portfolio.pages.users import STANDARD_USER


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args: dict[str, Any], settings: Settings) -> dict:
    """Extend pytest-playwright's defaults: relative page.goto() paths use the UI base URL."""
    return {**browser_context_args, "base_url": settings.ui_base_url}


@pytest.fixture
def login_page(page: Page) -> LoginPage:
    return LoginPage(page).open()


@pytest.fixture
def inventory(login_page: LoginPage, settings: Settings) -> InventoryPage:
    """Start the test already logged in as the standard user."""
    login_page.login(STANDARD_USER, settings.ui_password)
    inventory = InventoryPage(login_page.page)
    inventory.title.wait_for()
    return inventory


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo):
    """Embed a screenshot of the failing page into the pytest-html report.

    pytest-playwright also saves a screenshot and a trace under test-results/,
    which CI uploads as an artifact. Embedding one in the report makes the
    failure visible without downloading anything.
    """
    outcome = yield
    report = outcome.get_result()
    page = item.funcargs.get("page") if hasattr(item, "funcargs") else None
    if report.when == "call" and report.failed and page is not None:
        pytest_html = item.config.pluginmanager.getplugin("html")
        if pytest_html is None:
            return
        try:
            png = page.screenshot(full_page=True)
        except Exception:  # the page may already be closed or crashed
            return
        extras = getattr(report, "extras", [])
        extras.append(pytest_html.extras.png(base64.b64encode(png).decode()))
        report.extras = extras
