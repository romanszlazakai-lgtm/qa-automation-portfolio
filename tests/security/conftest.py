from typing import Any

import pytest

from qa_portfolio.config import Settings


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args: dict[str, Any], settings: Settings) -> dict:
    return {**browser_context_args, "base_url": settings.ui_base_url}
