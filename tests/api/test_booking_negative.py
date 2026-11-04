"""Negative cases: missing resources, invalid input and business rules.

Where Restful-Booker behaves differently from what a production API should do,
the test asserts the correct behaviour and is marked xfail with the reason.
With xfail_strict = true, the suite turns red if the defect is ever fixed, so
the known-defect list cannot silently go stale.
"""

from typing import Any

import pytest

from qa_portfolio.api.booking_client import BookingClient
from qa_portfolio.api.payloads import build_booking


@pytest.mark.parametrize(
    "booking_id",
    [
        pytest.param(999_999_999, id="non-existent-id"),
        pytest.param(0, id="zero"),
        pytest.param(-1, id="negative"),
        pytest.param("abc", id="non-numeric"),
    ],
)
def test_get_unknown_booking_returns_404(api_client: BookingClient, booking_id: Any) -> None:
    assert api_client.get_booking(booking_id).status_code == 404


def test_update_unknown_booking_is_rejected(auth_client: BookingClient) -> None:
    response = auth_client.update_booking(999_999_999, build_booking())
    # Restful-Booker answers 405; anything in the 2xx range would be a defect.
    assert response.status_code in (404, 405)


@pytest.mark.parametrize("missing_field", ["firstname", "lastname", "totalprice", "bookingdates"])
@pytest.mark.xfail(
    reason="KNOWN DEFECT: missing required field returns 500 Internal Server Error, not 400"
)
def test_create_booking_without_required_field_returns_400(
    auth_client: BookingClient, missing_field: str
) -> None:
    payload = build_booking()
    del payload[missing_field]

    response = auth_client.create_booking(payload)

    assert response.status_code == 400


@pytest.mark.parametrize("missing_field", ["firstname", "lastname", "totalprice", "bookingdates"])
def test_create_booking_without_required_field_is_not_accepted(
    auth_client: BookingClient, missing_field: str
) -> None:
    """Current behaviour guard: whatever the status code, the booking must not be created."""
    payload = build_booking()
    del payload[missing_field]

    response = auth_client.create_booking(payload)

    assert not response.ok
    assert "bookingid" not in response.text


@pytest.mark.xfail(reason="KNOWN DEFECT: API accepts a checkout date before the checkin date")
def test_checkout_before_checkin_is_rejected(auth_client: BookingClient) -> None:
    payload = build_booking(bookingdates={"checkin": "2030-05-10", "checkout": "2030-05-01"})

    response = auth_client.create_booking(payload)
    if response.ok:
        auth_client.delete_booking(response.json()["bookingid"])

    assert response.status_code == 400


@pytest.mark.xfail(reason="KNOWN DEFECT: API accepts a negative total price")
def test_negative_price_is_rejected(auth_client: BookingClient) -> None:
    response = auth_client.create_booking(build_booking(totalprice=-100))
    if response.ok:
        auth_client.delete_booking(response.json()["bookingid"])

    assert response.status_code == 400
