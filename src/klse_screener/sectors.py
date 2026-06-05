"""KLSE sector-to-stock mapping scraping.

Scrapes sector pages from klsescreener.com to map sector codes to
constituent stocks. Used for sector rotation analysis.

Source: https://www.klsescreener.com/v2/markets/bursa/{sector_code}
"""

import logging
import re
from typing import Dict, List

from bs4 import BeautifulSoup

from .http import fetch_url

logger = logging.getLogger(__name__)

KLSE_SECTOR_CODES: Dict[str, str] = {
    "0001I": "CONSUMER PRODUCTS & SERVICES",
    "0002I": "INDUSTRIAL PRODUCTS & SERVICES",
    "0003I": "CONSTRUCTION",
    "0005I": "TECHNOLOGY",
    "0010I": "FINANCIAL SERVICES",
    "0020I": "PROPERTY",
    "0025I": "PLANTATION",
    "0050I": "REAL ESTATE INVESTMENT TRUSTS",
    "0061I": "ENERGY",
    "0062I": "HEALTH CARE",
    "0063I": "TELECOMMUNICATIONS & MEDIA",
    "0064I": "TRANSPORTATION & LOGISTICS",
    "0065I": "UTILITIES",
}

SECTOR_URL_BASE = "https://www.klsescreener.com/v2/markets/bursa"


def _parse_sector_stocks_html(html: str) -> List[Dict[str, str]]:
    """Parse stock cards from sector page HTML.

    Each card contains: stock link, price, market cap, change %, subsector.

    Args:
        html: Raw HTML from klsescreener.com/v2/markets/bursa/{code}

    Returns:
        List of stock dicts with keys: code, symbol, name, price, change_pct, subsector
    """
    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")
    stocks = []

    for card in soup.find_all("div", class_="card-body"):
        link = card.find("a", href=re.compile(r"/v2/stocks/view/"))
        if not link:
            continue

        href = link.get("href", "")
        code_match = re.search(r"/view/(\w+)", href)
        if not code_match:
            continue

        code = code_match.group(1)
        name = link.get_text(strip=True)

        first_row = card.find("div", class_="row")
        price = ""
        if first_row:
            price_span = first_row.find("span", class_="col", string=re.compile(r"\d"))
            if price_span:
                price = price_span.get_text(strip=True)

        change_pct = ""
        change_span = card.find("span", class_=re.compile(r"text-(success|danger)"))
        if change_span:
            change_text = change_span.get_text(strip=True)
            pct_match = re.search(r"\(([+-]?\d+\.?\d*%)\)", change_text)
            if pct_match:
                change_pct = pct_match.group(1)

        subsector = ""
        small_tag = card.find("small", class_="text-muted")
        if small_tag:
            subsector = small_tag.get_text(strip=True)

        stocks.append({
            "code": code,
            "symbol": f"{code}.KL",
            "name": name,
            "price": price,
            "change_pct": change_pct,
            "subsector": subsector,
        })

    return stocks


def get_klse_sector_info() -> Dict[str, Dict[str, str]]:
    """Get KLSE sector code-to-name mapping.

    Returns:
        Dict mapping sector code to info dict with 'code' and 'name' keys.
    """
    return {
        code: {"code": code, "name": name}
        for code, name in KLSE_SECTOR_CODES.items()
    }


def get_klse_sector_stocks(sector_code: str) -> List[Dict[str, str]]:
    """Scrape stocks belonging to a KLSE sector.

    Args:
        sector_code: Sector index code (e.g., "0001I")

    Returns:
        List of stock dicts with keys: code, symbol, name, price, change_pct, subsector
    """
    if sector_code not in KLSE_SECTOR_CODES:
        logger.warning("Unknown sector code: %s", sector_code)
        return []

    url = f"{SECTOR_URL_BASE}/{sector_code}"
    cache_key = f"sector_{sector_code}"

    try:
        logger.info("Fetching sector %s from %s", sector_code, url)
        html = fetch_url(url, cache_key)
        stocks = _parse_sector_stocks_html(html)
        logger.info("Parsed %d stocks for sector %s", len(stocks), sector_code)
        return stocks
    except Exception as e:
        logger.error("Failed to fetch sector %s: %s: %s", sector_code, type(e).__name__, e)
        return []


def get_klse_all_sector_stocks() -> Dict[str, List[Dict[str, str]]]:
    """Scrape stocks for all 13 KLSE sectors.

    Returns:
        Dict mapping sector code to list of stock dicts.

    Note:
        Rate limiting is handled by fetch_url (2s interval between requests).
    """
    result = {}
    for code in KLSE_SECTOR_CODES:
        result[code] = get_klse_sector_stocks(code)
    return result
