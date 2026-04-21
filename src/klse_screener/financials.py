"""
KLSE Screener financial data extraction.

Provides structured dict-based access to:
- Key ratios (P/E, ROE, NTA, etc.)
- Quarterly financials with TTM calculations
- Annual financials
- Combined fundamentals for Magic Formula

Source: https://www.klsescreener.com/v2
"""

import logging
import re
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from bs4 import BeautifulSoup

from .http import fetch_url
from .market import is_klse

logger = logging.getLogger(__name__)

# Rate limiting and caching (shared with http module)
_MIN_INTERVAL = 2.0  # seconds between requests
_CACHE_TTL = 600  # 10 minutes


def _extract_code(ticker: str) -> str:
    """Extract numeric code from ticker like '5132.KL'."""
    code = re.sub(r"\..*$", "", ticker.upper())
    return code or ticker


def _parse_formatted_number(value: str) -> Optional[float]:
    """
    Parse formatted number string to float.
    
    Handles:
    - Plain numbers: "123.45" → 123.45
    - Millions: "123.45m" → 123450000
    - Billions: "1.23b" → 1230000000
    - Thousands: "1.23k" → 1230
    - Negative: "(123.45)" → -123.45
    - Percentage: "12.34%" → 12.34
    
    Returns None for invalid/empty values.
    """
    if not value or not isinstance(value, str):
        return None
    
    value = value.strip().lower()
    
    # Handle negative numbers in parentheses
    is_negative = value.startswith("(") and value.endswith(")")
    if is_negative:
        value = value[1:-1]
    
    # Remove commas and percentage signs
    value = value.replace(",", "").replace("%", "")
    
    # Handle multipliers
    multiplier = 1.0
    if value.endswith("m"):
        multiplier = 1_000_000
        value = value[:-1]
    elif value.endswith("b"):
        multiplier = 1_000_000_000
        value = value[:-1]
    elif value.endswith("k"):
        multiplier = 1_000
        value = value[:-1]
    
    try:
        result = float(value) * multiplier
        return -result if is_negative else result
    except (ValueError, TypeError):
        return None


def _clean_html_text(text: str) -> str:
    """Clean HTML text by removing tags and extra whitespace."""
    if not text:
        return ""
    # Remove HTML tags
    clean = re.sub(r"<[^>]+>", "", text)
    # Normalize whitespace
    clean = " ".join(clean.split())
    return clean.strip()


def get_klse_key_ratios(ticker: str) -> Dict[str, Any]:
    """
    Fetch key ratios for a KLSE stock from KLSE Screener.
    
    Returns a structured dict with all key ratios.
    Returns empty dict for non-KLSE tickers.
    
    Args:
        ticker: Stock ticker (e.g., "5132.KL")
    
    Returns:
        Dict with key ratios:
        {
            "pe_ratio": 15.2,
            "eps": 0.52,
            "dividend_yield": "3.5%",
            "nta_per_share": 2.45,
            "pb_ratio": 1.2,
            "roe": 8.5,
            "market_cap": "1.5b",
            "dps": 0.10,
            "psr": 0.8,
            "fifty_two_week_range": "1.20 - 1.80",
            "rsi_14": "Oversold (28.5)"
        }
    """
    if not is_klse(ticker):
        return {}
    
    try:
        code = _extract_code(ticker)
        url = f"https://www.klsescreener.com/v2/stocks/view/{code}"
        html = fetch_url(url, f"stock_{code}")
        
        if not html:
            logger.warning(f"No HTML content for {ticker}")
            return {}
        
        result: Dict[str, Any] = {"data_source": "klsescreener_key_ratios"}
        
        # Company name
        name_match = re.search(r"<h5[^>]*>\s*(\w[\w\s&.()-]+?)(?:</h5>|<)", html)
        if name_match:
            result["company_name"] = name_match.group(1).strip()
        
        # Sector
        sector_match = re.search(r"(?:Main Market|ACE Market)\s*:\s*([^<]+)", html)
        if sector_match:
            result["sector"] = sector_match.group(1).strip()
        
        # Key ratios patterns
        patterns = {
            "pe_ratio": r"P/E[^<]*</[^>]+>\s*<[^>]+>\s*([\d.]+)",
            "eps": r"EPS[^<]*</[^>]+>\s*<[^>]+>\s*([\d.]+)",
            "dividend_yield": r"DY[^<]*</[^>]+>\s*<[^>]+>\s*([\d.]+%)",
            "nta_per_share": r"NTA[^<]*</[^>]+>\s*<[^>]+>\s*([\d.]+)",
            "pb_ratio": r"P/B[^<]*</[^>]+>\s*<[^>]+>\s*([\d.]+)",
            "roe": r"ROE[^<]*</[^>]+>\s*<[^>]+>\s*([\d.]+)",
            "market_cap": r"Market Cap[^<]*</[^>]+>\s*<[^>]+>\s*([\d.]+[MBK])",
            "dps": r"DPS[^<]*</[^>]+>\s*<[^>]+>\s*([\d.]+)",
            "psr": r"PSR[^<]*</[^>]+>\s*<[^>]+>\s*([\d.]+)",
            "fifty_two_week_range": r"52w[^<]*</[^>]+>\s*<[^>]+>\s*([\d.]+ - [\d.]+)",
        }
        
        for label, pattern in patterns.items():
            match = re.search(pattern, html)
            if match:
                value = match.group(1)
                # Try to parse numeric values
                if label not in ["dividend_yield", "market_cap", "fifty_two_week_range"]:
                    parsed = _parse_formatted_number(value)
                    if parsed is not None:
                        value = parsed
                result[label] = value
        
        # RSI (special format: "Oversold (28.5)")
        rsi_match = re.search(
            r"RSI\(14\)[^<]*</[^>]+>\s*<[^>]+>\s*(\w+)\s*\(([\d.]+)\)", html
        )
        if rsi_match:
            result["rsi_14"] = f"{rsi_match.group(1)} ({rsi_match.group(2)})"
            result["rsi_14_value"] = float(rsi_match.group(2))
            result["rsi_14_signal"] = rsi_match.group(1)
        
        logger.info(f"Key ratios fetched for {ticker}")
        return result
        
    except Exception as e:
        logger.error(f"get_klse_key_ratios failed for {ticker}: {e}")
        return {}


def get_klse_quarterly_financials_dict(ticker: str) -> Dict[str, Any]:
    """
    Fetch quarterly financials with TTM calculations.
    
    Returns a structured dict with quarterly data and TTM metrics.
    Returns empty dict for non-KLSE tickers.
    
    Args:
        ticker: Stock ticker (e.g., "5132.KL")
    
    Returns:
        Dict with quarterly data:
        {
            "data_source": "klsescreener_quarterly",
            "quarterly_data": [
                {
                    "eps": 0.15,
                    "dps": 0.05,
                    "nta": 2.45,
                    "revenue": 125000000,
                    "net_profit": 18000000,
                    "quarter": "Q4",
                    "q_date": "2024-12-31",
                    "financial_year": 2024,
                    "announced": "2025-02-15",
                    "roe": 8.5,
                    "qoq": 5.2,
                    "yoy": 12.3
                },
                ...
            ],
            "ttm_revenue": 480000000,
            "ttm_net_profit": 72000000,
            "ttm_eps": 0.58
        }
    """
    if not is_klse(ticker):
        return {}
    
    try:
        code = _extract_code(ticker)
        url = f"https://www.klsescreener.com/v2/stocks/view/{code}"
        html = fetch_url(url, f"stock_{code}_quarterly")
        
        if not html:
            logger.warning(f"No HTML content for {ticker}")
            return {}
        
        result: Dict[str, Any] = {
            "data_source": "klsescreener_quarterly",
            "quarterly_data": [],
            "ttm_revenue": None,
            "ttm_net_profit": None,
            "ttm_eps": None,
        }
        
        # Use BeautifulSoup for reliable parsing
        soup = BeautifulSoup(html, "html.parser")
        tables = soup.find_all("table")
        
        target_table = None
        for table in tables:
            rows = table.find_all("tr")
            if len(rows) < 5:
                continue
            
            # Check first row for quarterly indicators
            first_row = rows[0]
            cells = first_row.find_all(["td", "th"])
            cell_texts = [
                c.get_text(strip=True).upper() for c in cells if c.get_text(strip=True)
            ]
            
            if any("EPS" in t or "REVENUE" in t or "P/L" in t for t in cell_texts):
                target_table = table
                break
        
        if not target_table:
            logger.warning(f"No quarterly table found for {ticker}")
            return result
        
        rows = target_table.find_all("tr")
        if not rows:
            return result
        
        # Parse quarterly data rows
        quarterly_data = []
        for row in rows[1:]:  # Skip header row
            cells = row.find_all(["td", "th"])
            cell_texts = [
                _clean_html_text(c.get_text()) for c in cells if c.get_text(strip=True)
            ]
            
            # Skip year header rows (single cell with date)
            if len(cell_texts) == 1 and "," in cell_texts[0]:
                continue
            
            # Skip empty rows
            if len(cell_texts) < 4:
                continue
            
            # Expected format: EPS, DPS, NTA, Revenue, P/L, Quarter, Q Date, Financial Year, Announced, ROE, QoQ%, YoY%, Report
            if len(cell_texts) >= 9:
                try:
                    eps = _parse_formatted_number(cell_texts[0])
                    dps = _parse_formatted_number(cell_texts[1]) if len(cell_texts) > 1 else None
                    nta = _parse_formatted_number(cell_texts[2]) if len(cell_texts) > 2 else None
                    revenue = _parse_formatted_number(cell_texts[3]) if len(cell_texts) > 3 else None
                    net_profit = _parse_formatted_number(cell_texts[4]) if len(cell_texts) > 4 else None
                    quarter = cell_texts[5] if len(cell_texts) > 5 else None
                    q_date = cell_texts[6] if len(cell_texts) > 6 else None
                    financial_year = cell_texts[7] if len(cell_texts) > 7 else None
                    announced = cell_texts[8] if len(cell_texts) > 8 else None
                    roe = _parse_formatted_number(cell_texts[9]) if len(cell_texts) > 9 else None
                    qoq = _parse_formatted_number(cell_texts[10]) if len(cell_texts) > 10 else None
                    yoy = _parse_formatted_number(cell_texts[11]) if len(cell_texts) > 11 else None
                    
                    quarterly_data.append({
                        "eps": eps,
                        "dps": dps,
                        "nta": nta,
                        "revenue": revenue,
                        "net_profit": net_profit,
                        "quarter": quarter,
                        "q_date": q_date,
                        "financial_year": financial_year,
                        "announced": announced,
                        "roe": roe,
                        "qoq": qoq,
                        "yoy": yoy,
                    })
                except Exception as e:
                    logger.debug(f"Error parsing quarterly row for {ticker}: {e}")
                    continue
        
        result["quarterly_data"] = quarterly_data
        
        # Calculate TTM (Trailing Twelve Months) - sum of last 4 quarters
        if len(quarterly_data) >= 4:
            last_4 = quarterly_data[:4]  # Most recent 4 quarters
            ttm_revenue = sum(q["revenue"] or 0 for q in last_4 if q["revenue"] is not None)
            ttm_net_profit = sum(q["net_profit"] or 0 for q in last_4 if q["net_profit"] is not None)
            ttm_eps = sum(q["eps"] or 0 for q in last_4 if q["eps"] is not None)
            
            result["ttm_revenue"] = ttm_revenue if ttm_revenue > 0 else None
            result["ttm_net_profit"] = ttm_net_profit if ttm_net_profit > 0 else None
            result["ttm_eps"] = ttm_eps if ttm_eps > 0 else None
            
            logger.info(
                f"TTM calculated for {ticker}: Revenue={ttm_revenue}, Net Profit={ttm_net_profit}"
            )
        
        return result
        
    except Exception as e:
        logger.error(f"get_klse_quarterly_financials_dict failed for {ticker}: {e}")
        return {}


def get_klse_annual_financials_dict(ticker: str) -> Dict[str, Any]:
    """
    Fetch annual financials for a KLSE stock.
    
    Returns a structured dict with annual data.
    Returns empty dict for non-KLSE tickers.
    
    Args:
        ticker: Stock ticker (e.g., "5132.KL")
    
    Returns:
        Dict with annual data:
        {
            "data_source": "klsescreener_annual",
            "annual_data": [
                {
                    "eps": 0.52,
                    "dps": 0.20,
                    "nta": 2.45,
                    "revenue": 500000000,
                    "net_profit": 75000000,
                    "financial_year_end": "2024-12-31",
                    "roe": 8.5
                },
                ...
            ]
        }
    """
    if not is_klse(ticker):
        return {}
    
    try:
        code = _extract_code(ticker)
        url = f"https://www.klsescreener.com/v2/stocks/view/{code}"
        html = fetch_url(url, f"stock_{code}_annual")
        
        if not html:
            logger.warning(f"No HTML content for {ticker}")
            return {}
        
        result: Dict[str, Any] = {
            "data_source": "klsescreener_annual",
            "annual_data": [],
        }
        
        # Use BeautifulSoup for reliable parsing
        soup = BeautifulSoup(html, "html.parser")
        tables = soup.find_all("table")
        
        target_table = None
        for table in tables:
            rows = table.find_all("tr")
            if len(rows) < 5:
                continue
            
            # Check first row for annual indicators
            first_row = rows[0]
            cells = first_row.find_all(["td", "th"])
            cell_texts = [
                c.get_text(strip=True).upper() for c in cells if c.get_text(strip=True)
            ]
            
            if any("EPS" in t or "REVENUE" in t for t in cell_texts):
                target_table = table
                break
        
        if not target_table:
            logger.warning(f"No annual table found for {ticker}")
            return result
        
        rows = target_table.find_all("tr")
        if not rows:
            return result
        
        # Parse annual data rows
        annual_data = []
        for row in rows[1:]:  # Skip header row
            cells = row.find_all(["td", "th"])
            cell_texts = [
                _clean_html_text(c.get_text()) for c in cells if c.get_text(strip=True)
            ]
            
            # Skip empty rows
            if len(cell_texts) < 4:
                continue
            
            # Expected format: EPS, DPS, NTA, Revenue, P/L, FYE, ROE
            if len(cell_texts) >= 6:
                try:
                    eps = _parse_formatted_number(cell_texts[0])
                    dps = _parse_formatted_number(cell_texts[1]) if len(cell_texts) > 1 else None
                    nta = _parse_formatted_number(cell_texts[2]) if len(cell_texts) > 2 else None
                    revenue = _parse_formatted_number(cell_texts[3]) if len(cell_texts) > 3 else None
                    net_profit = _parse_formatted_number(cell_texts[4]) if len(cell_texts) > 4 else None
                    fye = cell_texts[5] if len(cell_texts) > 5 else None
                    roe = _parse_formatted_number(cell_texts[6]) if len(cell_texts) > 6 else None
                    
                    annual_data.append({
                        "eps": eps,
                        "dps": dps,
                        "nta": nta,
                        "revenue": revenue,
                        "net_profit": net_profit,
                        "financial_year_end": fye,
                        "roe": roe,
                    })
                except Exception as e:
                    logger.debug(f"Error parsing annual row for {ticker}: {e}")
                    continue
        
        result["annual_data"] = annual_data
        logger.info(f"Annual data fetched for {ticker} ({len(annual_data)} years)")
        return result
        
    except Exception as e:
        logger.error(f"get_klse_annual_financials_dict failed for {ticker}: {e}")
        return {}


def get_klse_fundamentals_mf_enhanced(ticker: str) -> Dict[str, Any]:
    """
    Fetch all available fundamental data for a KLSE stock.
    
    Combines:
    - Key ratios (P/E, Market Cap, ROE, NTA, etc.)
    - Quarterly financials (with TTM calculations)
    - Annual financials
    - Magic Formula approximations
    
    Returns:
        Consolidated dict suitable for Magic Formula calculations.
        Returns empty dict for non-KLSE tickers.
    """
    if not is_klse(ticker):
        return {}
    
    try:
        # Fetch all data
        key_ratios = get_klse_key_ratios(ticker)
        quarterly = get_klse_quarterly_financials_dict(ticker)
        annual = get_klse_annual_financials_dict(ticker)
        
        # Consolidate
        result: Dict[str, Any] = {
            "data_source": "klsescreener_mf_enhanced",
            "ticker": ticker,
            "market_cap": key_ratios.get("market_cap"),
            "pe_ratio": key_ratios.get("pe_ratio"),
            "pb_ratio": key_ratios.get("pb_ratio"),
            "roe": key_ratios.get("roe"),
            "eps_current": key_ratios.get("eps"),
            "dps": key_ratios.get("dps"),
            "dividend_yield": key_ratios.get("dividend_yield"),
            "nta_per_share": key_ratios.get("nta_per_share"),
            "psr": key_ratios.get("psr"),
            # Quarterly/TTM data
            "ttm_revenue": quarterly.get("ttm_revenue"),
            "ttm_net_profit": quarterly.get("ttm_net_profit"),
            "ttm_eps": quarterly.get("ttm_eps"),
            "quarterly_data": quarterly.get("quarterly_data", []),
            # Annual data
            "annual_data": annual.get("annual_data", []),
            # Magic Formula approximations
            # Note: These are approximations - use hybrid mode for full accuracy
            "approx_ebit_ttm": quarterly.get("ttm_net_profit"),  # Simplified: Use Net Profit as EBIT proxy
            "approx_fixed_assets": key_ratios.get("nta_per_share"),  # NTA as fixed assets proxy
        }
        
        logger.info(f"MF-enhanced fundamentals fetched for {ticker}")
        return result
        
    except Exception as e:
        logger.error(f"get_klse_fundamentals_mf_enhanced failed for {ticker}: {e}")
        return {}


# Convenience alias for backward compatibility with beatit
def get_klse_fundamentals(ticker: str) -> Dict[str, Any]:
    """
    Alias for get_klse_fundamentals_mf_enhanced().
    
    This function exists for backward compatibility with beatit.
    New code should use get_klse_fundamentals_mf_enhanced() directly.
    """
    return get_klse_fundamentals_mf_enhanced(ticker)
