"""Thin client for the Restful-Booker API.

Methods return the raw `requests.Response` on purpose: tests decide what a
correct status code or body is, the client only knows how to send requests.
"""

from __future__ import annotations

from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def _session_with_retries() -> requests.Session:
    """Session that retries gateway errors from the free hosting tier.

    Only idempotent methods (GET, PUT, DELETE, ...) are retried, so a retry can
    never create a duplicate booking. POST is excluded by urllib3's defaults.
    """
    retry = Retry(total=3, backoff_factor=1, status_forcelist=(502, 503, 504))
    session = requests.Session()
    session.mount("https://", HTTPAdapter(max_retries=retry))
    session.mount("http://", HTTPAdapter(max_retries=retry))
    return session


class BookingClient:
    def __init__(self, base_url: str, timeout: float = 15, token: str | None = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.token = token
        self.session = _session_with_retries()
        # Restful-Booker answers 418 to anything that does not ask for JSON.
        self.session.headers.update({"Accept": "application/json"})

    def _request(self, method: str, path: str, **kwargs: Any) -> requests.Response:
        headers = kwargs.pop("headers", {})
        if self.token is not None:
            headers.setdefault("Cookie", f"token={self.token}")
        return self.session.request(
            method, f"{self.base_url}{path}", headers=headers, timeout=self.timeout, **kwargs
        )

    # Health and auth

    def ping(self) -> requests.Response:
        return self._request("GET", "/ping")

    def create_token(self, username: str, password: str) -> requests.Response:
        return self._request("POST", "/auth", json={"username": username, "password": password})

    def authenticate(self, username: str, password: str) -> str:
        """Fetch a token, store it on the client and return it."""
        response = self.create_token(username, password)
        response.raise_for_status()
        token = response.json().get("token")
        if not token:
            raise RuntimeError(f"No token in auth response: {response.text}")
        self.token = token
        return token

    # Bookings

    def get_booking_ids(self, **filters: str) -> requests.Response:
        return self._request("GET", "/booking", params=filters)

    def get_booking(self, booking_id: int | str) -> requests.Response:
        return self._request("GET", f"/booking/{booking_id}")

    def create_booking(self, payload: dict[str, Any]) -> requests.Response:
        return self._request("POST", "/booking", json=payload)

    def update_booking(
        self, booking_id: int | str, payload: dict[str, Any], **kwargs: Any
    ) -> requests.Response:
        return self._request("PUT", f"/booking/{booking_id}", json=payload, **kwargs)

    def partial_update_booking(
        self, booking_id: int | str, payload: dict[str, Any], **kwargs: Any
    ) -> requests.Response:
        return self._request("PATCH", f"/booking/{booking_id}", json=payload, **kwargs)

    def delete_booking(self, booking_id: int | str, **kwargs: Any) -> requests.Response:
        return self._request("DELETE", f"/booking/{booking_id}", **kwargs)
