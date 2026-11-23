"""
klse-screener-py: Malaysian (KLSE/Bursa) stock data scraper.

Fetch fundamentals, trading data, news, and announcements from KLSE Screener.
"""

from ._version import __version__
from .announcements import (
    get_klse_additional_listings,
    get_klse_announcements_by_category,
    get_klse_dividend_announcements,
    get_klse_financial_results,
    get_klse_general_meetings,
    get_klse_insider_dealings,
    get_klse_share_buybacks,
)
from .core import (
    get_klse_announcements_raw,
    get_klse_capital_changes_raw,
    get_klse_comments,
    get_klse_comments_formatted,
    get_klse_dividends_raw,
    get_klse_enhanced_fundamentals,
    get_klse_full_report,
    get_klse_fundamentals,
    get_klse_intraday_stats,
    # Raw functions (KLSE-only)
    get_klse_news_raw,
    get_klse_quarterly_history,
    get_klse_shareholding_changes_raw,
    get_klse_trade_details,
    get_klse_trade_details_formatted,
    get_klse_trade_summary,
    # Formatted wrappers
    get_klse_trade_summary_formatted,
    get_klse_warrants_raw,
)

# Market-wide data
from .entitlements import (
    get_klse_corporate_actions,
    get_klse_dividend_calendar,
)
from .financial_reports import (
    get_klse_financial_reports,
    get_klse_market_announcements,
)

# NEW: Structured financial data (pandas-free)
from .financials import (
    get_klse_annual_financials_dict,
    get_klse_financial_report_figures,
    get_klse_fundamentals_mf_enhanced,
    get_klse_key_ratios,
    get_klse_quarterly_financials_dict,
)
from .http import clear_cache, fetch_url, reset_rate_limit

# NEW: Bursa market data
from .market_data import get_bursa_market_data

# NEW: Price history (pandas-free)
from .price_history import (
    get_klse_price_history,
    scrape_ohlcv_raw,
)

# NEW: QR announcements
from .qr_announcements import (
    get_klse_announcements_by_ticker,
    get_klse_daily_financial_reports,
    get_klse_financial_reports_by_ticker,
)

# NEW: Sector mapping
from .sectors import (
    get_klse_all_sector_stocks,
    get_klse_sector_info,
    get_klse_sector_stocks,
)

__all__ = [
    # Version
    "__version__",
    "clear_cache",
    # HTTP utilities
    "fetch_url",
    # Bursa market data (NEW)
    "get_bursa_market_data",
    "get_klse_additional_listings",
    "get_klse_all_sector_stocks",
    # Market-wide: Announcements
    "get_klse_announcements_by_category",
    "get_klse_announcements_by_ticker",
    "get_klse_announcements_raw",
    "get_klse_annual_financials_dict",
    "get_klse_capital_changes_raw",
    "get_klse_comments",
    "get_klse_comments_formatted",
    "get_klse_corporate_actions",
    # QR announcements (NEW)
    "get_klse_daily_financial_reports",
    "get_klse_dividend_announcements",
    # Market-wide: Entitlements
    "get_klse_dividend_calendar",
    "get_klse_dividends_raw",
    "get_klse_enhanced_fundamentals",
    # Structured financial report figures (NEW)
    "get_klse_financial_report_figures",
    # Market-wide: Financial Reports
    "get_klse_financial_reports",
    "get_klse_financial_reports_by_ticker",
    "get_klse_financial_results",
    "get_klse_full_report",
    # Core individual stock functions (KLSE-only)
    "get_klse_fundamentals",
    "get_klse_fundamentals_mf_enhanced",
    "get_klse_general_meetings",
    "get_klse_insider_dealings",
    "get_klse_intraday_stats",
    # Structured financials (NEW)
    "get_klse_key_ratios",
    "get_klse_market_announcements",
    # Raw functions (KLSE-only - recommended for programmatic use)
    "get_klse_news_raw",
    "get_klse_price_history",
    "get_klse_quarterly_financials_dict",
    "get_klse_quarterly_history",
    "get_klse_sector_info",
    # Sector mapping (NEW)
    "get_klse_sector_stocks",
    "get_klse_share_buybacks",
    "get_klse_shareholding_changes_raw",
    "get_klse_trade_details",
    "get_klse_trade_details_formatted",
    "get_klse_trade_summary",
    # Formatted wrappers (LLM-friendly)
    "get_klse_trade_summary_formatted",
    "get_klse_warrants_raw",
    "reset_rate_limit",
    # Price history (NEW)
    "scrape_ohlcv_raw",
]
