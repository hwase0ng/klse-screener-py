"""
KLSE Screener entitlements data - dividends and corporate actions.

Source: https://www.klsescreener.com/v2
"""

import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from .http import fetch_url
from .parsers import clean_html

logger = logging.getLogger(__name__)


def get_klse_dividend_calendar(limit: int = 50) -> List[Dict[str, Any]]:
    """
    Fetch market-wide dividend calendar from KLSE Screener.

    Source: /v2/entitlements/dividends
    Returns recent and upcoming dividends with ex-date, amount, type, payment date.

    Args:
        limit: Maximum number of records to return (default: 50)

    Returns:
        List of dividend entries:
        [
            {
                "ticker": "5132.KL",
                "company_name": "DELEUM BERHAD",
                "ex_date": "2026-04-15",
                "amount": "2.5 sen",
                "type": "Single Tier",
                "pay_date": "2026-05-10",
                "announcement_date": "2026-04-01"
            },
            ...
        ]
    """
    try:
        url = "https://www.klsescreener.com/v2/entitlements/dividends"
        html = fetch_url(url, "dividend_calendar")

        dividends = []

        # Parse dividend table rows
        # Pattern matches table rows with dividend data
        row_pattern = r'<tr[^>]*>([\s\S]*?)</tr>'
        rows = re.findall(row_pattern, html)

        for row in rows[1:]:  # Skip header row
            try:
                cells = re.findall(r'<td[^>]*>([\s\S]*?)</td>', row)
                if len(cells) < 6:
                    continue

                # Clean cell content
                ticker = clean_html(cells[0]).strip() if len(cells) > 0 else ""
                company = clean_html(cells[1]).strip() if len(cells) > 1 else ""
                ex_date = clean_html(cells[2]).strip() if len(cells) > 2 else ""
                dividend_type = clean_html(cells[3]).strip() if len(cells) > 3 else ""
                amount = clean_html(cells[4]).strip() if len(cells) > 4 else ""
                pay_date = clean_html(cells[5]).strip() if len(cells) > 5 else ""

                if not ticker or not ex_date:
                    continue

                dividends.append({
                    "ticker": ticker + ".KL" if ticker and ".KL" not in ticker else ticker,
                    "company_name": company,
                    "ex_date": ex_date,
                    "type": dividend_type,
                    "amount": amount,
                    "pay_date": pay_date,
                })

                if len(dividends) >= limit:
                    break

            except Exception as e:
                logger.warning(f"Error parsing dividend row: {e}")
                continue

        return dividends

    except Exception as e:
        logger.error(f"get_klse_dividend_calendar failed: {e}")
        return []


def get_klse_corporate_actions(limit: int = 20) -> List[Dict[str, Any]]:
    """
    Fetch market-wide corporate actions from KLSE Screener.

    Source: /v2/entitlements/shares-issue
    Returns rights issues, bonus issues, consolidations, stock splits.

    Args:
        limit: Maximum number of records to return (default: 20)

    Returns:
        List of corporate action entries:
        [
            {
                "ticker": "5132.KL",
                "company_name": "DELEUM BERHAD",
                "action_type": "Bonus Issue",
                "ratio": "1:5",
                "ex_date": "2026-04-15",
                "announcement_date": "2026-04-01"
            },
            ...
        ]
    """
    try:
        url = "https://www.klsescreener.com/v2/entitlements/shares-issue"
        html = fetch_url(url, "corporate_actions")

        actions = []

        # Parse corporate actions table
        row_pattern = r'<tr[^>]*>([\s\S]*?)</tr>'
        rows = re.findall(row_pattern, html)

        for row in rows[1:]:  # Skip header row
            try:
                cells = re.findall(r'<td[^>]*>([\s\S]*?)</td>', row)
                if len(cells) < 5:
                    continue

                ticker = clean_html(cells[0]).strip() if len(cells) > 0 else ""
                company = clean_html(cells[1]).strip() if len(cells) > 1 else ""
                action_type = clean_html(cells[2]).strip() if len(cells) > 2 else ""
                ratio = clean_html(cells[3]).strip() if len(cells) > 3 else ""
                ex_date = clean_html(cells[4]).strip() if len(cells) > 4 else ""

                if not ticker or not ex_date:
                    continue

                actions.append({
                    "ticker": ticker + ".KL" if ticker and ".KL" not in ticker else ticker,
                    "company_name": company,
                    "action_type": action_type,
                    "ratio": ratio,
                    "ex_date": ex_date,
                })

                if len(actions) >= limit:
                    break

            except Exception as e:
                logger.warning(f"Error parsing corporate action row: {e}")
                continue

        return actions

    except Exception as e:
        logger.error(f"get_klse_corporate_actions failed: {e}")
        return []
