"""Test configuration read from environment variables.

Every value has a safe default that points at a public practice target, so the
suites run from a clean clone with no setup. The default credentials are the
demo credentials published on the target sites themselves, not secrets.
Override any value with an environment variable, for example:

    API_BASE_URL=http://localhost:3001 pytest tests/api
"""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    api_base_url: str
    api_username: str
    api_password: str
    ui_base_url: str
    ui_password: str
    request_timeout: float


def load_settings() -> Settings:
    return Settings(
        api_base_url=os.getenv("API_BASE_URL", "https://restful-booker.herokuapp.com").rstrip("/"),
        api_username=os.getenv("API_USERNAME", "admin"),
        api_password=os.getenv("API_PASSWORD", "password123"),
        ui_base_url=os.getenv("UI_BASE_URL", "https://www.saucedemo.com").rstrip("/"),
        ui_password=os.getenv("UI_PASSWORD", "secret_sauce"),
        request_timeout=float(os.getenv("REQUEST_TIMEOUT", "15")),
    )
