"""
Market detection utility for KLSE tickers.

Determines if a ticker is listed on Bursa Malaysia (KLSE).

Ticker conventions:
  - KLSE:     Ends with ".KL", e.g. "5132.KL", "1155.KL"
  - HKSE:     Ends with ".HK", e.g. "0700.HK", "9868.HK"
"""

import re
from enum import Enum


class Market(str, Enum):
    """Supported markets."""

    HKSE = "HKSE"
    KLSE = "KLSE"
    UNKNOWN = "UNKNOWN"


# Strict suffix patterns
_HK_PATTERN = re.compile(r"^(\d{1,5})\.HK$", re.IGNORECASE)
_KL_PATTERN = re.compile(r"^(\d{1,5})\.KL$", re.IGNORECASE)


def detect_market(ticker: str) -> Market:
    """
    Return the Market for a given ticker string.

    Only suffix format is valid:
    - "5132.KL" → KLSE ✓
    - "9868.HK" → HKSE ✓
    - "5132" → UNKNOWN ✗ (no suffix)

    Args:
        ticker: Stock ticker string

    Returns:
        Market enum value
    """
    t = ticker.strip()

    if _HK_PATTERN.match(t):
        return Market.HKSE

    if _KL_PATTERN.match(t):
        return Market.KLSE

    return Market.UNKNOWN


def is_klse(ticker: str) -> bool:
    """Return True if ticker is listed on Bursa Malaysia (KLSE)."""
    return detect_market(ticker) == Market.KLSE


def is_hkse(ticker: str) -> bool:
    """Return True if ticker is listed on HKSE."""
    return detect_market(ticker) == Market.HKSE
