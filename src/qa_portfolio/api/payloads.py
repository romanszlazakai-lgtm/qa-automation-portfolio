"""Builders for booking request bodies."""

from __future__ import annotations

import uuid
from datetime import date, timedelta
from typing import Any


def unique_name(prefix: str = "QA") -> str:
    """Name that is unique per test run.

    Restful-Booker is shared by everyone on the internet, so tests must never
    rely on data they did not create themselves.
    """
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


def build_booking(**overrides: Any) -> dict[str, Any]:
    checkin = date.today() + timedelta(days=30)
    booking: dict[str, Any] = {
        "firstname": unique_name("Jan"),
        "lastname": "Kowalski",
        "totalprice": 450,
        "depositpaid": True,
        "bookingdates": {
            "checkin": checkin.isoformat(),
            "checkout": (checkin + timedelta(days=3)).isoformat(),
        },
        "additionalneeds": "Breakfast",
    }
    booking.update(overrides)
    return booking
