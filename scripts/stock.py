#!/usr/bin/env python3
"""KLSE stock profile.

Usage:
    python stock.py TICKER [SECTIONS...]

Sections (all run if none given):
    fundamentals ratios financials news announcements dividends
    shareholding reports sentiment

Examples:
    python stock.py 5132.KL
    python stock.py 0012.KL fundamentals news
"""

import json
import sys

try:
    from klse_screener import (
        get_klse_announcements_raw,
        get_klse_annual_financials_dict,
        get_klse_comments_formatted,
        get_klse_dividends_raw,
        get_klse_financial_reports_by_ticker,
        get_klse_fundamentals,
        get_klse_key_ratios,
        get_klse_news_raw,
        get_klse_quarterly_financials_dict,
        get_klse_shareholding_changes_raw,
    )
except ImportError:
    sys.exit("klse-screener-py not installed. Run: pip install klse-screener-py")

SECTIONS = {
    "fundamentals": lambda t: [get_klse_fundamentals(t)],
    "ratios": lambda t: [get_klse_key_ratios(t)],
    "financials": lambda t: [
        get_klse_quarterly_financials_dict(t),
        get_klse_annual_financials_dict(t),
    ],
    "news": lambda t: [get_klse_news_raw(t, limit=10)],
    "announcements": lambda t: [get_klse_announcements_raw(t, limit=10)],
    "dividends": lambda t: [get_klse_dividends_raw(t, limit=5)],
    "shareholding": lambda t: [get_klse_shareholding_changes_raw(t, limit=10)],
    "reports": lambda t: [get_klse_financial_reports_by_ticker(t, limit=10)],
    "sentiment": lambda t: [get_klse_comments_formatted(t, limit=30)],
}


def _print_results(results: list) -> None:
    for r in results:
        if r is None or (isinstance(r, dict) and not r):
            print("  (no data)")
        elif isinstance(r, str):
            print(r or "  (no data)")
        else:
            print(json.dumps(r, indent=2, ensure_ascii=False, default=str))


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    ticker = sys.argv[1].upper()
    requested = sys.argv[2:]
    sections = [s for s in requested if s in SECTIONS]
    if requested and not sections:
        sys.exit(f"Unknown section(s): {', '.join(requested)}. Valid: {', '.join(SECTIONS)}")
    sections = sections or list(SECTIONS)

    for name in sections:
        print(f"\n## {name} — {ticker}")
        _print_results(SECTIONS[name](ticker))


if __name__ == "__main__":
    main()
