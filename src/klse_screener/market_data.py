"""
KLSE Screener - Bursa Malaysia Market Data

Fetches comprehensive market overview from klsescreener.com/v2/markets including:
- KLSE indices (FBM KLCI, CPO)
- Sector indices (12 Bursa sector indices)
- Top lists (Active, Turnover, Gainers, Losers)

All data is real-time scraped - no caching in library.
Host applications should implement their own caching strategy.

Source: https://www.klsescreener.com/v2/markets
"""

import re
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from bs4 import BeautifulSoup

from .http import fetch_url


# ============================================================================
# KLSE-SPECIFIC INDICES TO SCRAPE
# ============================================================================
KLSE_INDICES_CODES = {
    "200": "FTSE Bursa Malaysia KLCI",
    "CPO": "Crude Palm Oil",
}

# Top lists default limit
DEFAULT_TOP_LIMIT = 15


def get_bursa_market_data() -> Dict[str, Any]:
    """
    Fetch Bursa Malaysia market data from klsescreener.com/v2/markets.
    
    Returns comprehensive market overview including:
    - KLSE indices (FBM KLCI, CPO)
    - Sector indices (12 Bursa sector indices)
    - Top Active stocks (by volume)
    - Top Turnover stocks (by value)
    - Top Gainers (absolute)
    - Top Gainers (percentage)
    - Top Losers (absolute)
    - Top Losers (percentage)
    
    Returns:
        Dict with market data structure. Returns partial data if some sections
        fail to parse. Only includes "error" key if ALL sections fail.
        
    Example:
        >>> data = get_bursa_market_data()
        >>> print(f"KLCI: {data['klse_indices'][0]['price']}")
        1710.39
    """
    try:
        html = fetch_url("https://www.klsescreener.com/v2/markets", "market_data")
        soup = BeautifulSoup(html, "html.parser")
        
        result = {
            "scraped_at": datetime.now(timezone.utc).isoformat(),
            "source": "klsescreener.com/v2/markets",
        }
        
        errors = []
        
        # Extract each section independently
        try:
            result["klse_indices"] = _extract_klse_indices(soup)
        except Exception as e:
            errors.append(f"klse_indices: {str(e)}")
            result["klse_indices"] = []
        
        try:
            result["sector_indices"] = _extract_sector_indices(soup)
        except Exception as e:
            errors.append(f"sector_indices: {str(e)}")
            result["sector_indices"] = []
        
        try:
            result["top_active"] = _extract_top_list(soup, "Top Active", limit=DEFAULT_TOP_LIMIT)
        except Exception as e:
            errors.append(f"top_active: {str(e)}")
            result["top_active"] = []
        
        try:
            result["top_turnover"] = _extract_top_list(soup, "Top Turnover", limit=DEFAULT_TOP_LIMIT)
        except Exception as e:
            errors.append(f"top_turnover: {str(e)}")
            result["top_turnover"] = []
        
        try:
            result["top_gainers"] = _extract_top_list(soup, "Top Gainers", limit=DEFAULT_TOP_LIMIT)
        except Exception as e:
            errors.append(f"top_gainers: {str(e)}")
            result["top_gainers"] = []
        
        try:
            result["top_gainers_pct"] = _extract_top_list(soup, "Top Gainers %", limit=DEFAULT_TOP_LIMIT)
        except Exception as e:
            errors.append(f"top_gainers_pct: {str(e)}")
            result["top_gainers_pct"] = []
        
        try:
            result["top_losers"] = _extract_top_list(soup, "Top Losers", limit=DEFAULT_TOP_LIMIT)
        except Exception as e:
            errors.append(f"top_losers: {str(e)}")
            result["top_losers"] = []
        
        try:
            result["top_losers_pct"] = _extract_top_list(soup, "Top Losers %", limit=DEFAULT_TOP_LIMIT)
        except Exception as e:
            errors.append(f"top_losers_pct: {str(e)}")
            result["top_losers_pct"] = []
        
        # Only add error key if everything failed
        if len(errors) == 8:  # All sections failed
            result["error"] = "; ".join(errors)
        
        return result
        
    except Exception as e:
        return {
            "error": str(e),
            "scraped_at": datetime.now(timezone.utc).isoformat(),
            "source": "klsescreener.com/v2/markets",
        }


def _extract_klse_indices(soup: BeautifulSoup) -> List[Dict[str, Any]]:
    """Extract KLSE-specific indices from Market Index section."""
    indices = []
    
    # Find Market Index section
    h2 = soup.find("h2", string="Market Index")
    if not h2:
        return indices
    
    section = h2.find_next("div", class_="indices-section")
    if not section:
        return indices
    
    for entry in section.find_all("div", class_="col-md-4", attrs={"data-code": True}):
        code = entry.get("data-code", "")
        
        # Filter: Only KLSE indices (exclude currency pairs and international indices)
        if code not in KLSE_INDICES_CODES:
            continue
        
        name = KLSE_INDICES_CODES.get(code, code)
        price = _parse_float(entry.get("data-price"))
        ref_price = _parse_float(entry.get("data-ref-price"))
        change_abs = price - ref_price if price and ref_price else None
        change_pct = _extract_change_pct(entry)
        
        trend_div = entry.select_one("div[data-class='class']")
        trend = _extract_trend(trend_div)
        
        indices.append({
            "code": code,
            "name": name,
            "price": round(price, 2) if price else None,
            "change_abs": round(change_abs, 2) if change_abs else None,
            "change_pct": round(change_pct, 3) if change_pct else None,
            "trend": trend,
        })
    
    return indices


def _extract_sector_indices(soup: BeautifulSoup) -> List[Dict[str, Any]]:
    """Extract Bursa sector indices from Bursa Index section."""
    indices = []
    
    h2 = soup.find("h2", string="Bursa Index")
    if not h2:
        return indices
    
    section = h2.find_next("div", class_="row equal")
    if not section:
        return indices
    
    for entry in section.find_all("div", class_="col-md-4", attrs={"data-code": True}):
        code = entry.get("data-code", "")
        
        # Sector indices have data-code 1-50
        if not code.isdigit() or int(code) > 50:
            continue
        
        name_elem = entry.select_one(".stock-name-col .text-primary a")
        name = name_elem.text.strip() if name_elem else ""
        
        # Extract index code from href (e.g., /v2/stocks/view/0001I)
        index_code = ""
        if name_elem:
            href = name_elem.get("href", "")
            match = re.search(r"/view/(\w+)", href)
            if match:
                index_code = match.group(1)
        
        price = _parse_float(entry.get("data-price"))
        change_pct = _extract_change_pct(entry)
        
        trend_div = entry.select_one("div[data-class='class']")
        trend = _extract_trend(trend_div)
        
        indices.append({
            "code": code,
            "index_code": index_code,
            "name": name,
            "price": round(price, 2) if price else None,
            "change_pct": round(change_pct, 3) if change_pct else None,
            "trend": trend,
        })
    
    return indices


def _extract_top_list(soup: BeautifulSoup, section_name: str, limit: int = 15) -> List[Dict[str, Any]]:
    """
    Extract a top list section (Top Active, Top Gainers, etc.).
    
    Args:
        soup: BeautifulSoup object
        section_name: Section header text (e.g., "Top Active")
        limit: Maximum number of entries to return (default: 15)
    
    Returns:
        List of stock data dicts
    """
    stocks = []
    
    # Find section header
    h2 = soup.find("h2", string=section_name)
    if not h2:
        return stocks
    
    # Find the row after header
    section = h2.find_next("div", class_="row equal")
    if not section:
        return stocks
    
    rank = 0
    for entry in section.find_all("div", class_="col-md-4", attrs={"data-code": True}):
        if rank >= limit:
            break
        
        rank += 1
        code = entry.get("data-code", "")
        
        # Extract name (remove rank prefix like "1. ")
        name_elem = entry.select_one(".stock-name-col .text-primary a")
        name = name_elem.text.strip() if name_elem else ""
        name = re.sub(r"^\d+\.\s*", "", name)
        
        price = _parse_float(entry.get("data-price"))
        
        # Get volume or turnover
        volume_elem = entry.select_one(".stock-price-col .volume")
        volume_text = volume_elem.text.strip() if volume_elem else ""
        
        change_pct = _extract_change_pct(entry)
        
        trend_div = entry.select_one(".stock-price-col div[data-class='class']")
        trend = _extract_trend(trend_div)
        
        stock_data = {
            "rank": rank,
            "code": code,
            "name": name,
            "price": round(price, 3) if price else None,
            "change_pct": round(change_pct, 2) if change_pct else None,
            "trend": trend,
        }
        
        # Distinguish volume vs turnover
        if "m" in volume_text.lower():
            stock_data["turnover"] = volume_text
        else:
            stock_data["volume"] = volume_text
        
        stocks.append(stock_data)
    
    return stocks


def _extract_trend(trend_div: Optional[Any]) -> str:
    """Extract trend direction from CSS class."""
    if not trend_div:
        return "unchanged"
    
    classes = trend_div.get("class", [])
    if isinstance(classes, str):
        classes = [classes]
    
    if "increasing" in classes:
        return "up"
    elif "decreasing" in classes:
        return "down"
    return "unchanged"


def _extract_change_pct(entry: Any) -> Optional[float]:
    """Extract percentage change from price_change span."""
    change_elem = entry.select_one("span[data-value='price_change']")
    if not change_elem:
        return None
    
    text = change_elem.text.strip()
    # Pattern: "+0.035 -3.9%" or "0.035 -3.9%"
    match = re.search(r"([+-]?\d+\.\d+)%", text)
    if match:
        return float(match.group(1))
    return None


def _parse_float(value: Any) -> Optional[float]:
    """Safely parse float from string or attribute."""
    if value is None:
        return None
    try:
        return float(str(value).replace(",", ""))
    except (ValueError, TypeError):
        return None
