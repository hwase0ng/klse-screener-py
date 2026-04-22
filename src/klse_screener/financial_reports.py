"""
KLSE Screener financial reports data.

Source: https://www.klsescreener.com/v2
"""

import logging
import re
from typing import Any, Dict, List, Optional

from .http import fetch_url
from .parsers import clean_html

logger = logging.getLogger(__name__)


def get_klse_financial_reports(
    ticker: Optional[str] = None,
    limit: int = 20
) -> List[Dict[str, Any]]:
    """
    Fetch financial reports from KLSE Screener.

    Source: /v2/financial-reports
    Returns market-wide or ticker-specific quarterly/annual report filings.

    Args:
        ticker: Stock ticker (e.g., "5132.KL") or None for market-wide
        limit: Maximum number of records to return (default: 20)

    Returns:
        List of financial report entries:
        [
            {
                "ticker": "5132.KL",
                "company_name": "DELEUM BERHAD",
                "report_type": "Quarterly",
                "fiscal_period": "Q4 2025",
                "filing_date": "2026-02-15",
                "revenue": "125.5M",
                "profit": "18.2M",
                "url": "/v2/financial-reports/view/12345"
            },
            ...
        ]
    """
    try:
        if ticker:
            # Ticker-specific reports
            code = _extract_code(ticker)
            url = f"https://www.klsescreener.com/v2/stocks/view/{code}"
            cache_key = f"financial_reports_{code}"
        else:
            # Market-wide reports
            url = "https://www.klsescreener.com/v2/financial-reports"
            cache_key = "financial_reports_market"

        html = fetch_url(url, cache_key)

        reports = []

        if ticker:
            # Parse from individual stock page
            # Find financial reports section
            match = re.search(r'id="quarter_reports".*?</div>\s*</div>', html, re.DOTALL)
            if not match:
                return []

            content = match.group(0)
            rows = re.findall(r"<tr[^>]*>(.*?)</tr>", content, re.DOTALL)

            for row in rows[1:]:  # Skip header
                cells = re.findall(r"<td[^>]*>([\s\S]*?)</td>", row)
                if len(cells) < 6:
                    continue

                fiscal_period = clean_html(cells[0])
                revenue = clean_html(cells[1])
                profit = clean_html(cells[2])
                eps = clean_html(cells[3])
                filing_date = clean_html(cells[5]) if len(cells) > 5 else ""

                if not fiscal_period:
                    continue

                reports.append({
                    "ticker": ticker,
                    "report_type": "Quarterly",
                    "fiscal_period": fiscal_period,
                    "revenue": revenue,
                    "profit": profit,
                    "eps": eps,
                    "filing_date": filing_date,
                })

                if len(reports) >= limit:
                    break
        else:
            # Parse market-wide financial reports
            row_pattern = r'<tr[^>]*>([\s\S]*?)</tr>'
            rows = re.findall(row_pattern, html)

            for row in rows[1:]:  # Skip header
                cells = re.findall(r'<td[^>]*>([\s\S]*?)</td>', row)
                if len(cells) < 5:
                    continue

                ticker_found = clean_html(cells[0])
                company = clean_html(cells[1])
                report_type = clean_html(cells[2])
                fiscal_period = clean_html(cells[3])
                filing_date = clean_html(cells[4])

                if not ticker_found or not filing_date:
                    continue

                reports.append({
                    "ticker": ticker_found + ".KL" if ".KL" not in ticker_found else ticker_found,
                    "company_name": company,
                    "report_type": report_type,
                    "fiscal_period": fiscal_period,
                    "filing_date": filing_date,
                })

                if len(reports) >= limit:
                    break

        return reports

    except Exception as e:
        logger.error(f"get_klse_financial_reports failed: {e}")
        return []


def get_klse_market_announcements(
    category: Optional[str] = None,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """
    Fetch market-wide announcements from KLSE Screener.

    Source: /v2/announcements (market-wide, not per-stock)
    Returns all Bursa Malaysia announcements, optionally filtered by category.

    Args:
        category: Optional category filter (EA, SH, FA, SB, AL, GM)
        limit: Maximum number of records to return (default: 50)

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
    try:
        url = "https://www.klsescreener.com/v2/announcements"
        if category:
            url += f"?category={category}"

        cache_key = f"market_announcements_{category or 'all'}"
        html = fetch_url(url, cache_key)

        announcements = []

        # Parse announcement blocks
        block_pattern = r'href="(/v2/announcements/view/\d+)"[^>]*>\s*([^<]+)\s*</a>.*?(\d{4}-\d{2}-\d{2})'
        matches = re.findall(block_pattern, html, re.DOTALL)

        for href, title, date in matches:
            if not title or not date:
                continue

            announcements.append({
                "title": clean_html(title),
                "date": date,
                "category": category or "All",
                "url": href,
            })

            if len(announcements) >= limit:
                break

        return announcements

    except Exception as e:
        logger.error(f"get_klse_market_announcements failed: {e}")
        return []


def _extract_code(ticker: str) -> str:
    """Extract numeric code from ticker like '5132.KL'."""
    code = re.sub(r"\..*$", "", ticker.upper())
    return code or ticker
