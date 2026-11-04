"""Create, read, update and delete happy paths, plus data-driven create cases."""

from typing import Any

import pytest

from qa_portfolio.api.booking_client import BookingClient
from qa_portfolio.api.payloads import build_booking, unique_name
from qa_portfolio.api.schemas import BOOKING, BOOKING_ID_LIST, CREATED_BOOKING
from qa_portfolio.api.validation import assert_matches_schema


@pytest.mark.smoke
def test_create_booking_returns_id_and_echoes_body(
    auth_client: BookingClient, booking_payload: dict[str, Any]
) -> None:
    response = auth_client.create_booking(booking_payload)
    body = response.json()

    try:
        assert response.status_code == 200
        assert_matches_schema(body, CREATED_BOOKING)
        assert body["booking"] == booking_payload
    finally:
        auth_client.delete_booking(body["bookingid"])


def test_get_booking_returns_stored_data(
    api_client: BookingClient, created_booking: tuple[int, dict[str, Any]]
) -> None:
    booking_id, payload = created_booking

    response = api_client.get_booking(booking_id)

    assert response.status_code == 200
    assert_matches_schema(response.json(), BOOKING)
    assert response.json() == payload


def test_booking_list_matches_schema(api_client: BookingClient) -> None:
    response = api_client.get_booking_ids()

    assert response.status_code == 200
    assert_matches_schema(response.json(), BOOKING_ID_LIST)


def test_filter_by_name_finds_created_booking(
    api_client: BookingClient, created_booking: tuple[int, dict[str, Any]]
) -> None:
    booking_id, payload = created_booking

    response = api_client.get_booking_ids(
        firstname=payload["firstname"], lastname=payload["lastname"]
    )

    assert response.status_code == 200
    assert {"bookingid": booking_id} in response.json()


def test_full_update_replaces_booking(
    auth_client: BookingClient, created_booking: tuple[int, dict[str, Any]]
) -> None:
    booking_id, _ = created_booking
    new_data = build_booking(lastname="Nowak", totalprice=999, depositpaid=False)

    response = auth_client.update_booking(booking_id, new_data)

    assert response.status_code == 200
    assert response.json() == new_data
    assert auth_client.get_booking(booking_id).json() == new_data


def test_partial_update_changes_only_given_fields(
    auth_client: BookingClient, created_booking: tuple[int, dict[str, Any]]
) -> None:
    booking_id, original = created_booking
    changes = {"firstname": unique_name("Anna"), "totalprice": 120}

    response = auth_client.partial_update_booking(booking_id, changes)

    assert response.status_code == 200
    assert response.json() == {**original, **changes}


def test_deleted_booking_is_gone(
    auth_client: BookingClient, created_booking: tuple[int, dict[str, Any]]
) -> None:
    booking_id, _ = created_booking

    delete_response = auth_client.delete_booking(booking_id)

    # Restful-Booker documents 201 Created for a successful delete (sic).
    assert delete_response.status_code == 201
    assert auth_client.get_booking(booking_id).status_code == 404


@pytest.mark.parametrize(
    "overrides",
    [
        pytest.param({"totalprice": 0}, id="zero-price"),
        pytest.param({"totalprice": 1_000_000}, id="large-price"),
        pytest.param({"depositpaid": False}, id="no-deposit"),
        pytest.param({"firstname": "Zażółć", "lastname": "Gęślą-Jaźń"}, id="polish-diacritics"),
        pytest.param({"lastname": "O'Brien"}, id="apostrophe-in-name"),
        pytest.param(
            {"bookingdates": {"checkin": "2030-02-28", "checkout": "2030-03-01"}},
            id="month-boundary",
        ),
        pytest.param(
            {"bookingdates": {"checkin": "2028-02-28", "checkout": "2028-02-29"}},
            id="leap-day",
        ),
    ],
)
def test_create_booking_with_valid_variants(
    auth_client: BookingClient, overrides: dict[str, Any]
) -> None:
    payload = build_booking(**overrides)

    response = auth_client.create_booking(payload)
    body = response.json()

    try:
        assert response.status_code == 200
        assert body["booking"] == payload
    finally:
        auth_client.delete_booking(body["bookingid"])


def test_create_booking_without_optional_field(auth_client: BookingClient) -> None:
    payload = build_booking()
    del payload["additionalneeds"]

    response = auth_client.create_booking(payload)
    body = response.json()

    try:
        assert response.status_code == 200
        assert_matches_schema(body, CREATED_BOOKING)
        assert "additionalneeds" not in body["booking"]
    finally:
        auth_client.delete_booking(body["bookingid"])
