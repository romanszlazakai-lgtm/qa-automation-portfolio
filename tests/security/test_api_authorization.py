"""Authorization checks on Restful-Booker write operations.

Each test checks two things: the request is rejected, and the data really did
not change. A 403 that still modifies the record would be the worst outcome.
"""

import base64
from collections.abc import Iterator
from typing import Any

import pytest

from qa_portfolio.api.booking_client import BookingClient
from qa_portfolio.api.payloads import build_booking
from qa_portfolio.config import Settings


@pytest.fixture
def booking(auth_client: BookingClient) -> Iterator[tuple[int, dict[str, Any]]]:
    payload = build_booking()
    booking_id = auth_client.create_booking(payload).json()["bookingid"]
    yield booking_id, payload
    auth_client.delete_booking(booking_id)


@pytest.fixture
def bad_token_client(settings: Settings) -> BookingClient:
    return BookingClient(settings.api_base_url, settings.request_timeout, token="not-a-real-token")


def _basic(username: str, password: str) -> dict[str, str]:
    encoded = base64.b64encode(f"{username}:{password}".encode()).decode()
    return {"Authorization": f"Basic {encoded}"}


WRITE_OPERATIONS = ["update", "partial_update", "delete"]


def _send(client: BookingClient, operation: str, booking_id: int, **kwargs: Any):
    if operation == "update":
        return client.update_booking(booking_id, build_booking(lastname="Hacked"), **kwargs)
    if operation == "partial_update":
        return client.partial_update_booking(booking_id, {"lastname": "Hacked"}, **kwargs)
    return client.delete_booking(booking_id, **kwargs)


@pytest.mark.parametrize("operation", WRITE_OPERATIONS)
def test_write_without_token_is_forbidden(
    api_client: BookingClient, auth_client: BookingClient, booking, operation: str
) -> None:
    booking_id, original = booking

    response = _send(api_client, operation, booking_id)

    assert response.status_code == 403
    assert auth_client.get_booking(booking_id).json() == original


@pytest.mark.parametrize("operation", WRITE_OPERATIONS)
def test_write_with_invalid_token_is_forbidden(
    bad_token_client: BookingClient, auth_client: BookingClient, booking, operation: str
) -> None:
    booking_id, original = booking

    response = _send(bad_token_client, operation, booking_id)

    assert response.status_code == 403
    assert auth_client.get_booking(booking_id).json() == original


def test_wrong_basic_auth_is_forbidden(
    api_client: BookingClient, auth_client: BookingClient, booking, settings: Settings
) -> None:
    booking_id, original = booking

    response = _send(
        api_client, "update", booking_id, headers=_basic(settings.api_username, "wrong")
    )

    assert response.status_code == 403
    assert auth_client.get_booking(booking_id).json() == original


def test_valid_basic_auth_is_accepted(
    api_client: BookingClient, booking, settings: Settings
) -> None:
    """Positive control: proves the 403s above come from auth, not from a broken request."""
    booking_id, _ = booking

    response = _send(
        api_client,
        "partial_update",
        booking_id,
        headers=_basic(settings.api_username, settings.api_password),
    )

    assert response.status_code == 200


def test_malformed_json_does_not_leak_stack_trace(api_client: BookingClient) -> None:
    response = api_client.session.post(
        f"{api_client.base_url}/booking",
        data='{"firstname": "unterminated',
        headers={"Content-Type": "application/json"},
        timeout=api_client.timeout,
    )

    assert response.status_code >= 400
    for marker in ("node_modules", "SyntaxError", "    at "):
        assert marker not in response.text, f"Response leaks internals ({marker!r})"
