import pytest
from playwright.sync_api import expect

from qa_portfolio.config import Settings
from qa_portfolio.pages import InventoryPage, LoginPage
from qa_portfolio.pages.users import LOCKED_OUT_USER, STANDARD_USER


@pytest.mark.smoke
def test_valid_login_opens_inventory(login_page: LoginPage, settings: Settings) -> None:
    login_page.login(STANDARD_USER, settings.ui_password)

    inventory = InventoryPage(login_page.page)
    expect(login_page.page).to_have_url(f"{settings.ui_base_url}/inventory.html")
    expect(inventory.title).to_have_text("Products")
    expect(inventory.items).to_have_count(6)


def test_locked_out_user_cannot_log_in(login_page: LoginPage, settings: Settings) -> None:
    login_page.login(LOCKED_OUT_USER, settings.ui_password)

    expect(login_page.error).to_have_text("Epic sadface: Sorry, this user has been locked out.")
    expect(login_page.page).to_have_url(f"{settings.ui_base_url}/")


@pytest.mark.parametrize(
    ("username", "password", "expected_error"),
    [
        pytest.param(
            STANDARD_USER,
            "wrong-password",
            "Epic sadface: Username and password do not match any user in this service",
            id="wrong-password",
        ),
        pytest.param(
            "unknown_user",
            "secret_sauce",
            "Epic sadface: Username and password do not match any user in this service",
            id="unknown-user",
        ),
        pytest.param("", "secret_sauce", "Epic sadface: Username is required", id="empty-username"),
        pytest.param(STANDARD_USER, "", "Epic sadface: Password is required", id="empty-password"),
    ],
)
def test_invalid_login_shows_error(
    login_page: LoginPage, username: str, password: str, expected_error: str
) -> None:
    login_page.login(username, password)

    expect(login_page.error).to_have_text(expected_error)


def test_error_message_does_not_reveal_which_field_was_wrong(login_page: LoginPage) -> None:
    """Same message for unknown user and wrong password, so usernames cannot be enumerated."""
    login_page.login("unknown_user", "secret_sauce")
    unknown_user_error = login_page.error.inner_text()

    login_page.open()
    login_page.login(STANDARD_USER, "wrong-password")
    wrong_password_error = login_page.error.inner_text()

    assert unknown_user_error == wrong_password_error


def test_logout_returns_to_login(inventory: InventoryPage, settings: Settings) -> None:
    inventory.logout()

    expect(inventory.page).to_have_url(f"{settings.ui_base_url}/")
    expect(LoginPage(inventory.page).login_button).to_be_visible()
