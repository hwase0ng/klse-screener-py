"""
KLSE Screener announcements data - category-based filtering.

Source: https://www.klsescreener.com/v2
"""

import logging
import re
from typing import Any, Dict, List, Literal, Optional

from .http import fetch_url
from .parsers import clean_html

logger = logging.getLogger(__name__)

# Announcement category codes
AnnouncementCategory = Literal["EA", "SH", "FA", "SB", "AL", "GM"]


def get_klse_announcements_by_category(
    category: AnnouncementCategory,
    ticker: Optional[str] = None,
    limit: int = 20
) -> List[Dict[str, Any]]:
    """
    Fetch announcements by category from KLSE Screener.

    Source: /v2/announcements?category={CODE}

    Categories:
    - EA: Entitlements (dividends, bonus/rights issues)
    - SH: Shareholdings (director/substantial shareholder changes)
    - FA: Financial Results (quarterly/annual earnings)
    - SB: Shares Buy Back (company repurchasing own shares)
    - AL: Additional Listing (new shares listed)
    - GM: General Meetings (AGM/EGM notices)

    Args:
        category: Announcement category code (EA, SH, FA, SB, AL, GM)
        ticker: Specific stock ticker (optional, e.g., "5132.KL")
        limit: Maximum number of records to return (default: 20)

    Returns:
        List of announcement entries:
        [
            {
                "ticker": "5132.KL",
                "company_name": "DELEUM BERHAD",
                "title": "Notice of Dividend",
                "date": "2026-04-01",
                "category": "EA",
                "url": "/v2/announcements/view/12345"
            },
            ...
        ]
    """
    valid_categories = ["EA", "SH", "FA", "SB", "AL", "GM"]
    if category not in valid_categories:
        logger.error(f"Invalid category: {category}. Must be one of {valid_categories}")
        return []

    try:
        # Build URL based on whether ticker is provided
        if ticker:
            # Per-stock announcements
            code = _extract_code(ticker)
            url = f"https://www.klsescreener.com/v2/announcements/stock/{code}"
            cache_key = f"ann_{category}_{code}"
        else:
            # Market-wide announcements by category
            url = f"https://www.klsescreener.com/v2/announcements?category={category}"
            cache_key = f"ann_market_{category}"

        html = fetch_url(url, cache_key)

        announcements = []

        # Parse announcement blocks
        # Pattern: href, title, date
        block_pattern = r'href="(/v2/announcements/view/\d+)"[^>]*>\s*([^<]+)\s*</a>.*?(\d{4}-\d{2}-\d{2})'
        matches = re.findall(block_pattern, html, re.DOTALL)

        for href, title, date in matches:
            if not title or not date:
                continue

            # Try to extract ticker from context if not provided
            found_ticker = ticker
            if not found_ticker:
                # Try to find ticker in surrounding HTML
                ticker_match = re.search(r'href="/v2/stocks/view/(\d+)">([^<]+)</a>', html)
                if ticker_match:
                    found_ticker = ticker_match.group(1) + ".KL"

            announcements.append({
                "ticker": found_ticker or "MARKET",
                "title": clean_html(title),
                "date": date,
                "category": category,
                "url": href,
            })

            if len(announcements) >= limit:
                break

        return announcements

    except Exception as e:
        logger.error(f"get_klse_announcements_by_category failed for {category}: {e}")
        return []


# ============= Convenience Wrapper Functions =============


def get_klse_dividend_announcements(ticker: str, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Get dividend-related announcements (EA category) for a stock.

    Convenience wrapper for EA category announcements.

    Args:
        ticker: Stock ticker (e.g., "5132.KL")
        limit: Maximum number of records

    Returns:
        List of dividend announcements
    """
    return get_klse_announcements_by_category("EA", ticker, limit)


def get_klse_insider_dealings(ticker: str, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Get insider dealings announcements (SH category) for a stock.

    Director and substantial shareholder transaction announcements.

    Args:
        ticker: Stock ticker (e.g., "5132.KL")
        limit: Maximum number of records

    Returns:
        List of insider dealing announcements
    """
    return get_klse_announcements_by_category("SH", ticker, limit)


def get_klse_financial_results(ticker: str, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Get financial results announcements (FA category) for a stock.

    Quarterly and annual earnings announcements.

    Args:
        ticker: Stock ticker (e.g., "5132.KL")
        limit: Maximum number of records

    Returns:
        List of financial results announcements
    """
    return get_klse_announcements_by_category("FA", ticker, limit)


def get_klse_share_buybacks(ticker: str, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Get share buyback announcements (SB category) for a stock.

    Company share repurchase program announcements.

    Args:
        ticker: Stock ticker (e.g., "5132.KL")
        limit: Maximum number of records

    Returns:
        List of share buyback announcements
    """
    return get_klse_announcements_by_category("SB", ticker, limit)


def get_klse_additional_listings(ticker: str, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Get additional listing announcements (AL category) for a stock.

    New share listings, bonus issue listings.

    Args:
        ticker: Stock ticker (e.g., "5132.KL")
        limit: Maximum number of records

    Returns:
        List of additional listing announcements
    """
    return get_klse_announcements_by_category("AL", ticker, limit)


def get_klse_general_meetings(ticker: str, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Get general meeting announcements (GM category) for a stock.

    AGM/EGM notices and resolutions.

    Args:
        ticker: Stock ticker (e.g., "5132.KL")
        limit: Maximum number of records

    Returns:
        List of general meeting announcements
    """
    return get_klse_announcements_by_category("GM", ticker, limit)


def _extract_code(ticker: str) -> str:
    """Extract numeric code from ticker like '5132.KL'."""
    return re.sub(r"\..*$", "", ticker.upper()).lstrip("0") or ticker
