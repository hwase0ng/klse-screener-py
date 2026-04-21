"""
KLSE Screener price history scraping.

Provides pandas-free access to historical OHLCV data:
- 30-day historical prices (from /v2/stocks/historical_prices)
- 10-year chart data (from embedded chart endpoint)

Source: https://www.klsescreener.com/v2
"""

import json
import logging
import re
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from .http import fetch_url
from .market import detect_market

logger = logging.getLogger(__name__)

# Rate limiting
_MIN_INTERVAL = 2.0  # seconds between requests
_LAST_REQUEST_TIME: float = 0.0


def _rate_limit():
    """Apply rate limiting between requests"""
    global _LAST_REQUEST_TIME
    now = time.time()
    elapsed = now - _LAST_REQUEST_TIME
    if elapsed < _MIN_INTERVAL:
        time.sleep(_MIN_INTERVAL - elapsed)
    _LAST_REQUEST_TIME = time.time()


def _extract_code(ticker: str) -> str:
    """Extract numeric code from ticker like '5132.KL'."""
    code = re.sub(r"\..*$", "", ticker.upper())
    return code or ticker


def _parse_chart_number(value: str) -> float:
    """
    Parse number from chart data format.
    
    Handles: "1.23", "1,234.56", etc.
    """
    if not value:
        return 0.0
    try:
        # Remove commas
        value = value.replace(",", "")
        return float(value)
    except (ValueError, TypeError):
        return 0.0


def scrape_ohlcv_raw(symbol: str, period: str = '30d') -> List[Dict[str, Any]]:
    """
    Fetch historical OHLCV data as list of dicts (pandas-free).
    
    Supports:
    - 30-day historical prices (default)
    - 10-year chart data
    
    Args:
        symbol: Stock ticker (e.g., "5132.KL") or index code (e.g., "^0001I")
        period: '30d' for 30-day history, '10y' for 10-year chart
    
    Returns:
        List of OHLCV dicts:
        [
            {
                "date": "2024-01-15",
                "timestamp": 1705276800000,
                "open": 1.23,
                "high": 1.25,
                "low": 1.22,
                "close": 1.24,
                "volume": 1234567,
                "adjusted_close": 1.24  # For 10y data only
            },
            ...
        ]
    """
    market = detect_market(symbol)
    
    if period == '30d':
        return _scrape_30day_history(symbol, market)
    elif period == '10y':
        return _scrape_10year_chart(symbol, market)
    else:
        logger.error(f"Unknown period: {period}. Use '30d' or '10y'")
        return []


def _scrape_30day_history(symbol: str, market: str = 'KLSE') -> List[Dict[str, Any]]:
    """
    Fetch 30-day historical price data.
    
    Source: /v2/stocks/historical_prices/{code}
    """
    try:
        code = _extract_code(symbol)
        url = f"https://www.klsescreener.com/v2/stocks/historical_prices/{code}"
        
        logger.info(f"Fetching 30-day history for {symbol} from {url}")
        _rate_limit()
        
        html = fetch_url(url, f"historical_{code}")
        
        if not html:
            logger.warning(f"No HTML content for {symbol}")
            return []
        
        # Parse table data
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        table = soup.find("table")
        
        if not table:
            logger.warning(f"No historical price table found for {symbol}")
            return []
        
        rows = table.find_all("tr")[1:]  # Skip header
        data = []
        
        for row in rows:
            cells = row.find_all("td")
            if len(cells) < 6:
                continue
            
            try:
                date_str = cells[0].get_text(strip=True)
                open_price = _parse_chart_number(cells[1].get_text(strip=True))
                high_price = _parse_chart_number(cells[2].get_text(strip=True))
                low_price = _parse_chart_number(cells[3].get_text(strip=True))
                close_price = _parse_chart_number(cells[4].get_text(strip=True))
                volume_str = cells[5].get_text(strip=True).replace(",", "")
                volume = int(volume_str) if volume_str.isdigit() else 0
                
                # Parse date (format: "2024-01-15")
                try:
                    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                    timestamp = int(date_obj.timestamp() * 1000)
                except ValueError:
                    timestamp = 0
                
                data.append({
                    "date": date_str,
                    "timestamp": timestamp,
                    "open": open_price,
                    "high": high_price,
                    "low": low_price,
                    "close": close_price,
                    "volume": volume,
                })
            except Exception as e:
                logger.debug(f"Error parsing historical row: {e}")
                continue
        
        logger.info(f"Fetched {len(data)} rows for {symbol}")
        return data
        
    except Exception as e:
        logger.error(f"_scrape_30day_history failed for {symbol}: {e}")
        return []


def _scrape_10year_chart(symbol: str, market: str = 'KLSE') -> List[Dict[str, Any]]:
    """
    Fetch 10-year chart data from embedded chart endpoint.
    
    Source: /v2/stocks/chart/{code}/embedded/10y
    
    Returns chart data in same format as 30-day history.
    """
    try:
        code = _extract_code(symbol)
        url = f"https://www.klsescreener.com/v2/stocks/chart/{code}/embedded/10y"
        
        logger.info(f"Fetching 10-year chart for {symbol} from {url}")
        _rate_limit()
        
        html = fetch_url(url, f"chart_{code}_10y")
        
        if not html:
            logger.warning(f"No HTML content for {symbol} chart")
            return []
        
        # Extract JSON data from embedded chart
        # Look for data-points attribute or chartData variable
        match = re.search(r'data-points\s*=\s*"([^"]+)"', html)
        if not match:
            # Try alternative format
            match = re.search(r'chartData\s*=\s*\[([^\]]+)\]', html)
        
        if not match:
            logger.warning(f"No chart data found for {symbol}")
            return []
        
        try:
            # Parse the embedded data
            data_str = match.group(1)
            # Decode HTML entities
            data_str = data_str.replace("&quot;", '"')
            
            # Parse as JSON or custom format
            if data_str.startswith("["):
                chart_data = json.loads(data_str)
            else:
                # Custom format: split by semicolon
                chart_data = []
                points = data_str.split(";")
                for point in points:
                    parts = point.split(",")
                    if len(parts) >= 6:
                        chart_data.append({
                            "timestamp": int(parts[0]),
                            "open": float(parts[1]),
                            "high": float(parts[2]),
                            "low": float(parts[3]),
                            "close": float(parts[4]),
                            "volume": int(parts[5]),
                        })
            
            # Convert to standard format
            data = []
            for point in chart_data:
                try:
                    # Convert timestamp to date string
                    ts = point.get("timestamp", 0)
                    date_obj = datetime.fromtimestamp(ts / 1000)
                    date_str = date_obj.strftime("%Y-%m-%d")
                    
                    data.append({
                        "date": date_str,
                        "timestamp": ts,
                        "open": point.get("open", 0),
                        "high": point.get("high", 0),
                        "low": point.get("low", 0),
                        "close": point.get("close", 0),
                        "volume": point.get("volume", 0),
                        "adjusted_close": point.get("adjusted_close"),
                    })
                except Exception as e:
                    logger.debug(f"Error converting chart point: {e}")
                    continue
            
            logger.info(f"Fetched {len(data)} rows for {symbol} 10-year chart")
            return data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse chart JSON for {symbol}: {e}")
            return []
        
    except Exception as e:
        logger.error(f"_scrape_10year_chart failed for {symbol}: {e}")
        return []


def get_klse_price_history(symbol: str, period: str = '30d') -> Optional[Dict[str, Any]]:
    """
    Fetch price history with metadata.
    
    Wrapper around scrape_ohlcv_raw() that adds metadata.
    
    Args:
        symbol: Stock ticker
        period: '30d' or '10y'
    
    Returns:
        Dict with metadata and data:
        {
            "symbol": "5132.KL",
            "period": "30d",
            "data_source": "klsescreener",
            "count": 20,
            "data": [...]
        }
    """
    data = scrape_ohlcv_raw(symbol, period)
    
    if not data:
        return None
    
    return {
        "symbol": symbol,
        "period": period,
        "data_source": "klsescreener",
        "count": len(data),
        "last_updated": datetime.now().isoformat(),
        "data": data,
    }
