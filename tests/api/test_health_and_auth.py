import pytest

from qa_portfolio.api.booking_client import BookingClient
from qa_portfolio.api.schemas import TOKEN
from qa_portfolio.api.validation import assert_matches_schema
from qa_portfolio.config import Settings


@pytest.mark.smoke
def test_ping_reports_service_up(api_client: BookingClient) -> None:
    # Restful-Booker documents 201 for a healthy ping.
    assert api_client.ping().status_code == 201


@pytest.mark.smoke
def test_valid_credentials_return_token(api_client: BookingClient, settings: Settings) -> None:
    response = api_client.create_token(settings.api_username, settings.api_password)

    assert response.status_code == 200
    assert_matches_schema(response.json(), TOKEN)


@pytest.mark.parametrize(
    ("username", "password"),
    [
        pytest.param("admin", "wrong-password", id="wrong-password"),
        pytest.param("not-a-user", "password123", id="unknown-user"),
        pytest.param("", "", id="empty-credentials"),
        pytest.param("ADMIN", "password123", id="username-is-case-sensitive"),
    ],
)
def test_invalid_credentials_do_not_return_token(
    api_client: BookingClient, username: str, password: str
) -> None:
    response = api_client.create_token(username, password)

    body = response.json()
    assert "token" not in body
    assert body.get("reason") == "Bad credentials"


@pytest.mark.xfail(
    reason="KNOWN DEFECT: failed login returns 200 OK instead of 401 Unauthorized",
)
def test_invalid_credentials_return_401(api_client: BookingClient) -> None:
    response = api_client.create_token("admin", "wrong-password")
    assert response.status_code == 401
