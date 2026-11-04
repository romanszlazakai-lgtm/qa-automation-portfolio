"""Money parsing. Decimal, never float: 0.1 + 0.2 must equal 0.3."""

import re
from decimal import Decimal

_AMOUNT = re.compile(r"\$\s*(\d+(?:\.\d{1,2})?)")


def parse_price(text: str) -> Decimal:
    """Extract the amount from labels like '$29.99' or 'Item total: $39.98'."""
    match = _AMOUNT.search(text)
    if not match:
        raise ValueError(f"No price found in {text!r}")
    return Decimal(match.group(1))
