from collections.abc import Iterator
from typing import Any

import pytest

from qa_portfolio.api.booking_client import BookingClient
from qa_portfolio.api.payloads import build_booking


@pytest.fixture
def booking_payload() -> dict[str, Any]:
    return build_booking()


@pytest.fixture
def created_booking(
    auth_client: BookingClient, booking_payload: dict[str, Any]
) -> Iterator[tuple[int, dict[str, Any]]]:
    """Create a booking for the test and delete it afterwards.

    Teardown runs even when the test fails, so the shared API is left clean.
    A test that already deleted the booking is fine: we only clean up if needed.
    """
    response = auth_client.create_booking(booking_payload)
    assert response.status_code == 200, f"Setup failed: {response.status_code} {response.text}"
    booking_id = response.json()["bookingid"]

    yield booking_id, booking_payload

    if auth_client.get_booking(booking_id).status_code == 200:
        auth_client.delete_booking(booking_id)
