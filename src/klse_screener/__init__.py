"""
klse-screener-py: Malaysian (KLSE/Bursa) stock data scraper.

Fetch fundamentals, trading data, news, and announcements from KLSE Screener.
"""

from ._version import __version__
from .core import (
    get_klse_fundamentals,
    get_klse_enhanced_fundamentals,
    get_klse_quarterly_history,
    get_klse_intraday_stats,
    get_klse_trade_summary,
    get_klse_trade_details,
    get_klse_comments,
    get_klse_full_report,
    # Raw functions (KLSE-only)
    get_klse_news_raw,
    get_klse_announcements_raw,
    get_klse_dividends_raw,
    get_klse_capital_changes_raw,
    get_klse_warrants_raw,
    get_klse_shareholding_changes_raw,
    # Formatted wrappers
    get_klse_trade_summary_formatted,
    get_klse_trade_details_formatted,
    get_klse_comments_formatted,
)
from .http import fetch_url, reset_rate_limit, clear_cache

# Market-wide data
from .entitlements import (
    get_klse_dividend_calendar,
    get_klse_corporate_actions,
)
from .announcements import (
    get_klse_announcements_by_category,
    get_klse_dividend_announcements,
    get_klse_insider_dealings,
    get_klse_financial_results,
    get_klse_share_buybacks,
    get_klse_additional_listings,
    get_klse_general_meetings,
)
from .financial_reports import (
    get_klse_financial_reports,
    get_klse_market_announcements,
)

# NEW: Structured financial data (pandas-free)
from .financials import (
    get_klse_key_ratios,
    get_klse_quarterly_financials_dict,
    get_klse_annual_financials_dict,
    get_klse_fundamentals_mf_enhanced,
)

# NEW: Price history (pandas-free)
from .price_history import (
    scrape_ohlcv_raw,
    get_klse_price_history,
)

# NEW: QR announcements
from .qr_announcements import (
    get_klse_daily_financial_reports,
    get_klse_announcements_by_ticker,
    get_klse_financial_reports_by_ticker,
)

__all__ = [
    # Version
    "__version__",
    # Core individual stock functions (KLSE-only)
    "get_klse_fundamentals",
    "get_klse_enhanced_fundamentals",
    "get_klse_quarterly_history",
    "get_klse_intraday_stats",
    "get_klse_trade_summary",
    "get_klse_trade_details",
    "get_klse_comments",
    "get_klse_full_report",
    # Raw functions (KLSE-only - recommended for programmatic use)
    "get_klse_news_raw",
    "get_klse_announcements_raw",
    "get_klse_dividends_raw",
    "get_klse_capital_changes_raw",
    "get_klse_warrants_raw",
    "get_klse_shareholding_changes_raw",
    # Formatted wrappers (LLM-friendly)
    "get_klse_trade_summary_formatted",
    "get_klse_trade_details_formatted",
    "get_klse_comments_formatted",
    # Market-wide: Entitlements
    "get_klse_dividend_calendar",
    "get_klse_corporate_actions",
    # Market-wide: Announcements
    "get_klse_announcements_by_category",
    "get_klse_dividend_announcements",
    "get_klse_insider_dealings",
    "get_klse_financial_results",
    "get_klse_share_buybacks",
    "get_klse_additional_listings",
    "get_klse_general_meetings",
    # Market-wide: Financial Reports
    "get_klse_financial_reports",
    "get_klse_market_announcements",
    # HTTP utilities
    "fetch_url",
    "reset_rate_limit",
    "clear_cache",
    # Structured financial data (pandas-free)
    "get_klse_key_ratios",
    "get_klse_quarterly_financials_dict",
    "get_klse_annual_financials_dict",
    "get_klse_fundamentals_mf_enhanced",  # Recommended for Magic Formula
    # Price history (pandas-free)
    "scrape_ohlcv_raw",
    "get_klse_price_history",
    # QR announcements
    "get_klse_daily_financial_reports",
    "get_klse_announcements_by_ticker",
    "get_klse_financial_reports_by_ticker",
]
