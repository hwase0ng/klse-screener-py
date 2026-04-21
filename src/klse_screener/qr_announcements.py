"""
KLSE Screener QR (Quarterly Results) announcements scraping.

Provides access to market-wide and ticker-specific QR announcements:
- Market-wide financial reports from /v2/financial-reports
- Ticker-specific announcements

Source: https://www.klsescreener.com/v2
"""

import logging
import re
import time
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup

from .http import fetch_url

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


def _parse_quarter_from_text(period_text: str) -> tuple:
    """
    Parse quarter number and end date from period text.
    
    Examples:
    - "Q1 2026-03-31" → ("Q1", "2026-03-31")
    - "3-MTH-ENDED31/03/26" → ("Q1", "2026-03-31")
    - "(Y.E.31/12/25)" → ("FY", "2025-12-31")
    
    Returns:
        (quarter, quarter_end_date)
    """
    period_text = period_text.upper().strip()
    
    # Pattern 1: Direct quarter format "Q1", "Q2", etc.
    quarter_match = re.search(r'Q(\d)', period_text)
    quarter = f"Q{quarter_match.group(1)}" if quarter_match else "Q4"
    
    # Pattern 2: Date in format DD/MM/YY or DD/MM/YYYY
    date_patterns = [
        r'(\d{2})/(\d{2})/(\d{2,4})',  # 31/03/26 or 31/03/2026
        r'(\d{4})-(\d{2})-(\d{2})',    # 2026-03-31
    ]
    
    quarter_end_date = None
    for pattern in date_patterns:
        date_match = re.search(pattern, period_text)
        if date_match:
            groups = date_match.groups()
            if len(groups[0]) == 4:  # YYYY-MM-DD format
                quarter_end_date = f"{groups[0]}-{groups[1]}-{groups[2]}"
            else:  # DD/MM/YY format
                day, month, year = groups
                year = f"20{year}" if len(year) == 2 else year
                quarter_end_date = f"{year}-{month}-{day}"
            break
    
    if not quarter_end_date:
        # Fallback: use today's date
        quarter_end_date = date.today().isoformat()
    
    return quarter, quarter_end_date


def _parse_formatted_number(value: str) -> Optional[float]:
    """
    Parse formatted number string to float.
    
    Handles:
    - Plain numbers: "123.45" → 123.45
    - Millions: "123.45m" → 123450000
    - Billions: "1.23b" → 1230000000
    - Negative: "(123.45)" → -123.45
    
    Returns None for invalid/empty values.
    """
    if not value or not isinstance(value, str):
        return None
    
    value = value.strip().lower()
    
    # Handle negative numbers in parentheses
    is_negative = value.startswith("(") and value.endswith(")")
    if is_negative:
        value = value[1:-1]
    
    # Remove commas
    value = value.replace(",", "")
    
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


def get_klse_daily_financial_reports(scrape_date: Optional[date] = None) -> List[Dict[str, Any]]:
    """
    Fetch market-wide financial reports from /v2/financial-reports.
    
    Scrapes the latest QR announcements across all KLSE stocks.
    
    Args:
        scrape_date: Date to scrape (default: today)
    
    Returns:
        List of QR announcement dicts:
        [
            {
                "ticker": "5132.KL",
                "company_name": "DELEUM BERHAD",
                "announced_date": "2026-04-16",
                "quarter": "Q1",
                "quarter_end_date": "2026-03-31",
                "revenue": 27453000,
                "net_profit": 384000,
                "eps": 0.08,
                "dps": 0.50
            },
            ...
        ]
    """
    if scrape_date is None:
        scrape_date = date.today()
    
    url = "https://www.klsescreener.com/v2/financial-reports"
    
    logger.info(f"Scraping KLSE financial reports from {url}")
    _rate_limit()
    
    try:
        html = fetch_url(url, "financial_reports_market")
        
        if not html:
            logger.warning("No HTML content received from klsescreener")
            return []
        
        soup = BeautifulSoup(html, 'html.parser')
        results = []
        
        # Find the financial reports table
        table = soup.find('table', id='table-financial-reports')
        if not table:
            logger.warning("Financial reports table not found")
            return []
        
        # Parse table rows
        tbody = table.find('tbody')
        if not tbody:
            return []
        
        rows = tbody.find_all('tr')
        
        for row in rows:
            cells = row.find_all('td')
            if len(cells) < 2:
                continue
            
            # Extract announced date (first column)
            announced_text = cells[0].get_text(strip=True)
            
            # Parse announced date - format: "16 Apr" or "16 Apr 2026"
            try:
                date_match = re.match(r'(\d{1,2})\s+(\w{3})(?:\s+(\d{4}))?', announced_text)
                if date_match:
                    day = int(date_match.group(1))
                    month_str = date_match.group(2)
                    year = int(date_match.group(3)) if date_match.group(3) else scrape_date.year
                    
                    months = {'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
                             'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12}
                    month = months.get(month_str, 1)
                    
                    announced_date = date(year, month, day)
                else:
                    continue
            except Exception as e:
                logger.debug(f"Failed to parse date '{announced_text}': {e}")
                continue
            
            # Only include reports from last 3 days (guard against old data)
            days_diff = (scrape_date - announced_date).days
            if days_diff < 0 or days_diff > 3:
                continue
            
            # Extract ticker (second column)
            ticker_cell = cells[1]
            ticker_link = ticker_cell.find('a', href=re.compile(r'/v2/stocks/view/'))
            if not ticker_link:
                continue
            
            # Extract code from href
            href = ticker_link.get('href', '')
            code_match = re.search(r'/view/(\d+)', href)
            if code_match:
                code = code_match.group(1).zfill(4)  # Ensure 4 digits
                ticker = f"{code}.KL"
            else:
                # Fallback to text
                ticker_text = ticker_link.get_text(strip=True)
                ticker = f"{ticker_text}.KL" if not ticker_text.endswith('.KL') else ticker_text
            
            # Extract quarter info
            quarter = "Q4"
            quarter_end_date = announced_date.isoformat()
            
            # Try to find quarter info in other cells
            for i, cell in enumerate(cells[2:], 2):
                cell_text = cell.get_text(strip=True)
                
                # Look for quarter pattern
                if re.search(r'Q\d', cell_text):
                    q, qd = _parse_quarter_from_text(cell_text)
                    quarter = q
                    quarter_end_date = qd
                    break
                
                # Look for date pattern (Q Date column)
                date_match = re.match(r'(\d{4})-(\d{2})-(\d{2})', cell_text)
                if date_match:
                    quarter_end_date = cell_text
                    # Infer quarter from month
                    month = int(date_match.group(2))
                    if month in [1, 2, 3]:
                        quarter = "Q1"
                    elif month in [4, 5, 6]:
                        quarter = "Q2"
                    elif month in [7, 8, 9]:
                        quarter = "Q3"
                    else:
                        quarter = "Q4"
            
            # Extract financial data if available
            revenue = None
            net_profit = None
            eps = None
            dps = None
            
            # Try to parse numeric cells (revenue, profit, etc.)
            for i, cell in enumerate(cells[4:], 4):
                cell_text = cell.get_text(strip=True)
                parsed = _parse_formatted_number(cell_text)
                if parsed is not None:
                    if revenue is None:
                        revenue = parsed
                    elif net_profit is None:
                        net_profit = parsed
            
            results.append({
                "ticker": ticker,
                "announced_date": announced_date.isoformat(),
                "quarter": quarter,
                "quarter_end_date": quarter_end_date,
                "revenue": revenue,
                "net_profit": net_profit,
                "eps": eps,
                "dps": dps,
            })
        
        logger.info(f"Scraped {len(results)} KLSE QR announcements for {scrape_date.isoformat()}")
        return results
        
    except Exception as e:
        logger.error(f"get_klse_daily_financial_reports failed: {e}")
        return []


def get_klse_announcements_by_ticker(ticker: str, days_back: int = 3) -> List[Dict[str, Any]]:
    """
    Fetch QR announcements for a specific ticker.
    
    Args:
        ticker: Stock ticker (e.g., "5132.KL")
        days_back: Number of days to look back (default: 3)
    
    Returns:
        List of QR announcement dicts for the ticker
    """
    try:
        # Get market-wide reports and filter by ticker
        all_reports = []
        for i in range(days_back):
            scrape_date = date.today() - timedelta(days=i)
            reports = get_klse_daily_financial_reports(scrape_date)
            all_reports.extend(reports)
        
        # Filter by ticker
        ticker_reports = [r for r in all_reports if r["ticker"] == ticker]
        
        logger.info(f"Found {len(ticker_reports)} QR announcements for {ticker}")
        return ticker_reports
        
    except Exception as e:
        logger.error(f"get_klse_announcements_by_ticker failed for {ticker}: {e}")
        return []


def get_klse_financial_reports_by_ticker(ticker: str, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Fetch financial reports for a specific ticker from stock page.
    
    This is an alternative to get_klse_daily_financial_reports() for
    ticker-specific historical data.
    
    Args:
        ticker: Stock ticker (e.g., "5132.KL")
        limit: Maximum number of records to return (default: 20)
    
    Returns:
        List of financial report dicts:
        [
            {
                "ticker": "5132.KL",
                "report_type": "Quarterly",
                "fiscal_period": "Q4 2025",
                "filing_date": "2026-02-15",
                "revenue": 125500000,
                "profit": 18200000,
                "eps": 0.08
            },
            ...
        ]
    """
    try:
        code = _extract_code(ticker)
        url = f"https://www.klsescreener.com/v2/stocks/view/{code}"
        
        logger.info(f"Fetching financial reports for {ticker} from {url}")
        _rate_limit()
        
        html = fetch_url(url, f"financial_reports_{code}")
        
        if not html:
            logger.warning(f"No HTML content for {ticker}")
            return []
        
        soup = BeautifulSoup(html, 'html.parser')
        reports = []
        
        # Find quarterly reports section
        # Look for table with quarterly data
        tables = soup.find_all('table')
        
        for table in tables:
            # Check if this is a financial reports table
            rows = table.find_all('tr')
            if len(rows) < 3:
                continue
            
            # Check header row for financial indicators
            header = rows[0].get_text().upper()
            if 'EPS' not in header and 'REVENUE' not in header:
                continue
            
            # Parse data rows
            for row in rows[1:]:
                cells = row.find_all(['td', 'th'])
                if len(cells) < 6:
                    continue
                
                try:
                    # Extract data from cells
                    fiscal_period = cells[0].get_text(strip=True) if len(cells) > 0 else ""
                    revenue_str = cells[1].get_text(strip=True) if len(cells) > 1 else ""
                    profit_str = cells[2].get_text(strip=True) if len(cells) > 2 else ""
                    eps_str = cells[3].get_text(strip=True) if len(cells) > 3 else ""
                    filing_date = cells[5].get_text(strip=True) if len(cells) > 5 else ""
                    
                    # Parse numeric values
                    revenue = _parse_formatted_number(revenue_str)
                    profit = _parse_formatted_number(profit_str)
                    eps = _parse_formatted_number(eps_str)
                    
                    # Determine report type
                    report_type = "Quarterly"
                    if "FY" in fiscal_period or "YEAR" in fiscal_period.upper():
                        report_type = "Annual"
                    
                    reports.append({
                        "ticker": ticker,
                        "report_type": report_type,
                        "fiscal_period": fiscal_period,
                        "filing_date": filing_date,
                        "revenue": revenue,
                        "profit": profit,
                        "eps": eps,
                    })
                    
                    if len(reports) >= limit:
                        break
                        
                except Exception as e:
                    logger.debug(f"Error parsing financial report row: {e}")
                    continue
            
            if len(reports) >= limit:
                break
        
        logger.info(f"Fetched {len(reports)} financial reports for {ticker}")
        return reports
        
    except Exception as e:
        logger.error(f"get_klse_financial_reports_by_ticker failed for {ticker}: {e}")
        return []
