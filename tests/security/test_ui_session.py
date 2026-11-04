"""Session and access-control checks on SauceDemo, done through a real browser."""

import pytest
from playwright.sync_api import Page, expect

from qa_portfolio.config import Settings
from qa_portfolio.pages import InventoryPage, LoginPage
from qa_portfolio.pages.users import STANDARD_USER

SESSION_COOKIE = "session-username"
PROTECTED_PAGES = [
    "/inventory.html",
    "/cart.html",
    "/checkout-step-one.html",
    "/checkout-step-two.html",
    "/checkout-complete.html",
]


def _login(page: Page, settings: Settings) -> InventoryPage:
    LoginPage(page).open().login(STANDARD_USER, settings.ui_password)
    inventory = InventoryPage(page)
    inventory.title.wait_for()
    return inventory


@pytest.mark.parametrize("path", PROTECTED_PAGES)
def test_protected_page_requires_login(page: Page, settings: Settings, path: str) -> None:
    page.goto(path)

    expect(page).to_have_url(f"{settings.ui_base_url}/")
    expect(LoginPage(page).error).to_contain_text("when you are logged in")


def test_protected_page_blocked_after_logout(page: Page, settings: Settings) -> None:
    _login(page, settings).logout()

    page.goto("/inventory.html")

    expect(LoginPage(page).error).to_contain_text("when you are logged in")


def test_logout_clears_session_cookie(page: Page, settings: Settings) -> None:
    _login(page, settings).logout()

    names = [cookie["name"] for cookie in page.context.cookies()]
    assert SESSION_COOKIE not in names


# Cookie attribute checks. The session cookie is written by client-side
# JavaScript (document.cookie), which explains both findings below.
# sameSite passes because Chromium treats a cookie without the attribute as Lax.
COOKIE_FINDINGS: dict[str, str] = {
    "secure": "session cookie has no Secure flag, so it could be sent over plain HTTP",
    "httpOnly": "session cookie is not HttpOnly, so any script on the page (XSS) can read it",
}


def _cookie_cases():
    for attribute in ("secure", "httpOnly", "sameSite"):
        reason = COOKIE_FINDINGS.get(attribute)
        marks = [pytest.mark.xfail(reason=f"SECURITY FINDING: {reason}")] if reason else []
        yield pytest.param(attribute, marks=marks, id=attribute)


@pytest.mark.parametrize("attribute", list(_cookie_cases()))
def test_session_cookie_flags(page: Page, settings: Settings, attribute: str) -> None:
    _login(page, settings)
    cookie = next(c for c in page.context.cookies() if c["name"] == SESSION_COOKIE)

    if attribute == "sameSite":
        assert cookie["sameSite"] in ("Strict", "Lax"), cookie
    else:
        assert cookie[attribute] is True, cookie
