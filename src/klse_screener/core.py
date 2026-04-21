"""
KLSE Screener fundamentals scraper for Malaysian (Bursa) stocks.

Provides:
  - Key ratios (P/E, EPS, DY, NTA, P/B, ROE, etc.)
  - Quarterly financials (Revenue, Profit, EPS, QoQ, YoY)
  - Annual financials
  - Dividend history (with ex-date and pay date)
  - Capital changes (splits, bonus issues)
  - Stock-specific news
  - Bursa Malaysia announcements
  - Trading data (order book, trade details)
  - Forum comments (retail sentiment)

Source: https://www.klsescreener.com/v2
"""

import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup

from .http import fetch_url
from .market import is_klse

logger = logging.getLogger(__name__)


def _extract_code(ticker: str) -> str:
    """Extract numeric code from ticker like '5132.KL'."""
    return re.sub(r"\..*$", "", ticker.upper()).lstrip("0") or ticker


def get_klse_fundamentals(ticker: str) -> Dict[str, Any]:
    """Fetch fundamentals for a KLSE stock from KLSE Screener.

    Returns a structured dict with key ratios and latest quarter data.
    Returns empty dict for non-KLSE tickers.

    Args:
        ticker: Stock ticker (e.g., "5132.KL")

    Returns:
        Dict with fundamentals data, or empty dict if not KLSE
    """
    if not is_klse(ticker):
        return {}

    try:
        code = _extract_code(ticker)
        url = f"https://www.klsescreener.com/v2/stocks/view/{code}"
        html = fetch_url(url, f"stock_{code}")

        result: Dict[str, Any] = {"data_source": "klsescreener"}

        # Company name
        name_match = re.search(r"<h5[^>]*>\s*(\w[\w\s&.()-]+?)(?:</h5>|<)", html)
        if name_match:
            result["name"] = name_match.group(1).strip()

        # Sector
        sector_match = re.search(r"(?:Main Market|ACE Market)\s*:\s*([^<]+)", html)
        if sector_match:
            result["sector"] = sector_match.group(1).strip()

        # Key ratios
        patterns = {
            "pe_ratio": r"P/E[^<]*</[^>]+>\s*<[^>]+>\s*([\d.]+)",
            "eps": r"EPS[^<]*</[^>]+>\s*<[^>]+>\s*([\d.]+)",
            "dividend_yield": r"DY[^<]*</[^>]+>\s*<[^>]+>\s*([\d.]+%)",
            "nta": r"NTA[^<]*</[^>]+>\s*<[^>]+>\s*([\d.]+)",
            "pb_ratio": r"P/B[^<]*</[^>]+>\s*<[^>]+>\s*([\d.]+)",
            "roe": r"ROE[^<]*</[^>]+>\s*<[^>]+>\s*([\d.]+)",
            "market_cap": r"Market Cap[^<]*</[^>]+>\s*<[^>]+>\s*([\d.]+[MBK])",
            "dps": r"DPS[^<]*</[^>]+>\s*<[^>]+>\s*([\d.]+)",
            "psr": r"PSR[^<]*</[^>]+>\s*<[^>]+>\s*([\d.]+)",
            "fifty_two_week_range": r"52w[^<]*</[^>]+>\s*<[^>]+>\s*([\d.]+ - [\d.]+)",
        }

        for label, pattern in patterns.items():
            m = re.search(pattern, html)
            if m:
                result[label] = m.group(1)

        # RSI
        rsi_match = re.search(
            r"RSI\(14\)[^<]*</[^>]+>\s*<[^>]+>\s*(\w+)\s*([\d.]+)", html
        )
        if rsi_match:
            result["rsi_14"] = f"{rsi_match.group(1)} ({rsi_match.group(2)})"

        # Latest quarter
        q_rows = re.findall(
            r"<tr[^>]*>(\s*<td[^>]*class='number[^']*'>.*?</td>\s*</tr>)",
            html,
            re.DOTALL,
        )
        if not q_rows:
            rev_match = re.search(r"class='number'>[\d.]+m</td>", html)
            if rev_match:
                tr_start = html.rfind("<tr", 0, rev_match.start())
                tr_end = html.find("</tr>", rev_match.start()) + 5
                q_rows = [html[tr_start:tr_end]]

        if q_rows:
            cells = re.findall(r"<td[^>]*>\s*(.*?)\s*</td>", q_rows[0], re.DOTALL)
            clean = [re.sub(r"<[^>]+>", "", c).strip() for c in cells]
            if len(clean) >= 10:
                result["latest_quarter"] = {
                    "eps": clean[0],
                    "dps": clean[1],
                    "nta": clean[2],
                    "revenue": clean[3],
                    "profit_loss": clean[4],
                    "quarter": clean[5],
                    "fiscal_year": clean[6],
                    "roe": clean[9],
                }
                if len(clean) > 10:
                    result["latest_quarter"]["qoq"] = clean[10]
                if len(clean) > 11:
                    result["latest_quarter"]["yoy"] = clean[11]

        return result

    except Exception as e:
        logger.error(f"get_klse_fundamentals failed for {ticker}: {e}")
        return {"error": str(e)}


def get_klse_news(ticker: str, limit: int = 10) -> str:
    """Fetch stock-specific news from KLSE Screener.

    Returns formatted string. Empty for non-KLSE.

    Args:
        ticker: Stock ticker
        limit: Maximum number of news items

    Returns:
        Formatted news string, or empty string
    """
    if not is_klse(ticker):
        return ""

    try:
        code = _extract_code(ticker)
        url = f"https://www.klsescreener.com/v2/news/stock/{code}"
        html = fetch_url(url, f"news_{code}")

        items = re.findall(
            r'<a[^>]*href="(/v2/news/view/[^"]+)"[^>]*>\s*(.*?)\s*</a>',
            html,
            re.DOTALL,
        )

        seen = set()
        results: List[str] = []
        for _, title in items:
            clean = re.sub(r"<[^>]+>", "", title).strip()
            if clean and clean not in seen:
                seen.add(clean)
                results.append(f"- {clean}")
                if len(results) >= limit:
                    break

        if not results:
            return ""

        return "## KLSE Screener News\n\n" + "\n".join(results)

    except Exception as e:
        logger.error(f"get_klse_news failed for {ticker}: {e}")
        return ""


def get_klse_announcements(ticker: str, limit: int = 10) -> str:
    """Fetch Bursa Malaysia announcements from KLSE Screener.

    Returns formatted string. Empty for non-KLSE.

    Args:
        ticker: Stock ticker
        limit: Maximum number of announcements

    Returns:
        Formatted announcements string, or empty string
    """
    if not is_klse(ticker):
        return ""

    try:
        code = _extract_code(ticker)
        url = f"https://www.klsescreener.com/v2/announcements/stock/{code}"
        html = fetch_url(url, f"ann_{code}")

        blocks = re.findall(
            r'href="(/v2/announcements/view/\d+)".*?'
            r"(\d{4}-\d{2}-\d{2}\s*-\s*\d+:\d+\s*[ap]m)",
            html,
            re.DOTALL,
        )

        seen = set()
        results: List[str] = []
        for _, date_str in blocks:
            date_str = date_str.strip()
            if date_str and date_str not in seen:
                seen.add(date_str)
                results.append(f"- Bursa announcement ({date_str})")
                if len(results) >= limit:
                    break

        if not results:
            return ""

        return "## Bursa Malaysia Announcements\n\n" + "\n".join(results)

    except Exception as e:
        logger.error(f"get_klse_announcements failed for {ticker}: {e}")
        return ""


def get_klse_annual(ticker: str, limit: int = 3) -> str:
    """Fetch annual financials from KLSE Screener.
    
    DEPRECATED: This function returns formatted string for LLM consumption.
    For programmatic use, use get_klse_annual_financials_dict() instead.

    Args:
        ticker: Stock ticker
        limit: Maximum number of years

    Returns:
        Formatted annual data string, or empty string
    
    Deprecated:
        Will be removed in v2.0. Use get_klse_annual_financials_dict() for structured dict data.
    """
    import warnings
    warnings.warn(
        "get_klse_annual() is deprecated and will be removed in v2.0. "
        "Use get_klse_annual_financials_dict() for structured dict data.",
        DeprecationWarning,
        stacklevel=2
    )
    
    if not is_klse(ticker):
        return ""

    try:
        code = _extract_code(ticker)
        html = fetch_url(
            f"https://www.klsescreener.com/v2/stocks/view/{code}", f"stock_{code}"
        )

        match = re.search(r'id="annual".*?</div>\s*</div>', html, re.DOTALL)
        if not match:
            return ""

        content = match.group(0)
        rows = re.findall(r"<tr[^>]*>(.*?)</tr>", content, re.DOTALL)
        if not rows:
            return ""

        results: List[str] = []
        count = 0
        for row in rows:
            cells = re.findall(r"<td[^>]*>\s*(.*?)\s*</td>", row, re.DOTALL)
            clean = [re.sub(r"<[^>]+>", "", c).strip() for c in cells]
            if len(clean) >= 4 and clean[0]:
                results.append(
                    f"**{clean[0]}:** Revenue: {clean[1]}, Profit: {clean[2]}, EPS: {clean[3]}"
                )
                count += 1
                if count >= limit:
                    break

        if count == 0:
            return ""

        return "## KLSE Annual Financials\n\n" + "\n".join(results)

    except Exception as e:
        logger.error(f"get_klse_annual failed for {ticker}: {e}")
        return ""


def get_klse_dividends(ticker: str, limit: int = 5) -> str:
    """Fetch dividend history from KLSE Screener.

    Returns formatted string. Empty for non-KLSE.

    Args:
        ticker: Stock ticker
        limit: Maximum number of dividends

    Returns:
        Formatted dividend history string, or empty string
    """
    if not is_klse(ticker):
        return ""

    try:
        code = _extract_code(ticker)
        html = fetch_url(
            f"https://www.klsescreener.com/v2/stocks/view/{code}", f"stock_{code}"
        )

        match = re.search(r'id="dividends".*?</div>\s*</div>', html, re.DOTALL)
        if not match:
            return ""

        content = match.group(0)
        rows = re.findall(r"<tr[^>]*>(.*?)</tr>", content, re.DOTALL)
        if not rows:
            return ""

        results: List[str] = []
        count = 0
        for row in rows:
            cells = re.findall(r"<td[^>]*>\s*(.*?)\s*</td>", row, re.DOTALL)
            clean = [re.sub(r"<[^>]+>", "", c).strip() for c in cells]
            if len(clean) >= 7 and clean[3]:
                results.append(
                    f"- {clean[3]}: {clean[5]} (Ex: {clean[2]}, Pay: {clean[4]})"
                )
                count += 1
                if count >= limit:
                    break

        if count == 0:
            return ""

        return "## KLSE Dividend History\n\n" + "\n".join(results)

    except Exception as e:
        logger.error(f"get_klse_dividends failed for {ticker}: {e}")
        return ""


def get_klse_capital_changes(ticker: str, limit: int = 5) -> str:
    """Fetch capital changes (splits, bonus issues) from KLSE Screener.

    Returns formatted string. Empty for non-KLSE.

    Args:
        ticker: Stock ticker
        limit: Maximum number of changes

    Returns:
        Formatted capital changes string, or empty string
    """
    if not is_klse(ticker):
        return ""

    try:
        code = _extract_code(ticker)
        html = fetch_url(
            f"https://www.klsescreener.com/v2/stocks/view/{code}", f"stock_{code}"
        )

        match = re.search(r'id="capital_changes".*?</div>\s*</div>', html, re.DOTALL)
        if not match:
            return ""

        content = match.group(0)
        rows = re.findall(r"<tr[^>]*>(.*?)</tr>", content, re.DOTALL)
        if not rows:
            return ""

        results: List[str] = []
        count = 0
        for row in rows:
            cells = re.findall(r"<td[^>]*>\s*(.*?)\s*</td>", row, re.DOTALL)
            clean = [re.sub(r"<[^>]+>", "", c).strip() for c in cells]
            if len(clean) >= 4 and clean[2]:
                results.append(f"- {clean[2]}: {clean[3]} ({clean[0]})")
                count += 1
                if count >= limit:
                    break

        if count == 0:
            return ""

        return "## KLSE Capital Changes\n\n" + "\n".join(results)

    except Exception as e:
        logger.error(f"get_klse_capital_changes failed for {ticker}: {e}")
        return ""


def get_klse_warrants(ticker: str, limit: int = 5) -> str:
    """Fetch warrants from KLSE Screener.

    Returns formatted string. Empty for non-KLSE.

    Args:
        ticker: Stock ticker
        limit: Maximum number of warrants

    Returns:
        Formatted warrants string, or empty string
    """
    if not is_klse(ticker):
        return ""

    try:
        code = _extract_code(ticker)
        html = fetch_url(
            f"https://www.klsescreener.com/v2/stocks/view/{code}", f"stock_{code}"
        )

        match = re.search(r'id="warrants"(.*?)</div>\s*</div>', html, re.DOTALL)
        if not match:
            return ""

        content = match.group(0)
        rows = re.findall(r"<tr[^>]*>(.*?)</tr>", content, re.DOTALL)
        if not rows:
            return ""

        results: List[str] = []
        count = 0
        for row in rows:
            cells = re.findall(r"<td[^>]*>\s*(.*?)\s*</td>", row, re.DOTALL)
            clean = [re.sub(r"<[^>]+>", "", c).strip() for c in cells]
            if len(clean) >= 4 and clean[0]:
                results.append(
                    f"- {clean[0]}: Last={clean[1]}, Chg={clean[2]}, Vol={clean[3]}"
                )
                count += 1
                if count >= limit:
                    break

        if count == 0:
            return ""

        return "## KLSE Warrants\n\n" + "\n".join(results)

    except Exception as e:
        logger.error(f"get_klse_warrants failed for {ticker}: {e}")
        return ""


def get_klse_shareholding_changes(ticker: str, limit: int = 20) -> str:
    """Fetch institutional shareholding TRANSACTIONS from KLSE Screener.

    Returns formatted string showing recent institutional buying/selling activity.

    Args:
        ticker: Stock ticker
        limit: Maximum number of transactions

    Returns:
        Formatted shareholding changes string, or empty string
    """
    if not is_klse(ticker):
        return ""

    try:
        code = _extract_code(ticker)
        html = fetch_url(
            f"https://www.klsescreener.com/v2/stocks/view/{code}",
            f"shareholding_{code}",
        )

        match = re.search(
            r'id="shareholding_changes"(.*?)</div>\s*</div>', html, re.DOTALL
        )
        if not match:
            return ""

        content = match.group(0)
        rows = re.findall(r"<tr[^>]*>(.*?)</tr>", content, re.DOTALL)
        if not rows:
            return ""

        results: List[str] = []
        count = 0
        for row in rows:
            cells = re.findall(r"<td[^>]*>\s*(.*?)\s*</td>", row, re.DOTALL)
            clean = [re.sub(r"<[^>]+>", "", c).strip() for c in cells]
            if len(clean) >= 5 and clean[0]:
                results.append(
                    f"- {clean[0]}: {clean[3]} shares ({clean[2]}) by {clean[4]}"
                )
                count += 1
                if count >= limit:
                    break

        if count == 0:
            return ""

        return "## KLSE Shareholding Changes\n\n" + "\n".join(results)

    except Exception as e:
        logger.error(f"get_klse_shareholding_changes failed for {ticker}: {e}")
        return ""


def get_klse_intraday_stats(ticker: str) -> Dict[str, Any]:
    """Fetch intraday statistics from KLSE Screener.

    Returns:
        {
            "high": 0.290,
            "low": 0.280,
            "open": 0.285,
            "volume": 33094,
            "volume_buy": 5100,
            "volume_sell": 2349400,
            "bid_price": 0.280,
            "ask_price": 0.285,
            "last_updated": "2026-04-18T16:00:00+08:00"
        }

    Empty dict for non-KLSE stocks.

    Args:
        ticker: Stock ticker

    Returns:
        Dict with intraday stats, or empty dict
    """
    if not is_klse(ticker):
        return {}

    try:
        code = _extract_code(ticker)
        html = fetch_url(
            f"https://www.klsescreener.com/v2/stocks/view/{code}", f"intraday_{code}"
        )

        result = {
            "high": None,
            "low": None,
            "open": None,
            "volume": None,
            "volume_buy": None,
            "volume_sell": None,
            "bid_price": None,
            "ask_price": None,
            "last_updated": datetime.now().isoformat(),
        }

        # Parse High/Low/Open/Volume
        patterns = {
            "high": r"<td>High</td>\s*<td[^>]*>([\d.]+)</td>",
            "low": r"<td>Low</td>\s*<td[^>]*>([\d.]+)</td>",
            "open": r"<td>Open</td>\s*<td[^>]*>([\d.]+)</td>",
            "volume": r"<td>Volume</td>\s*<td[^>]*>([\d,]+)</td>",
        }

        for key, pattern in patterns.items():
            match = re.search(pattern, html)
            if match:
                value = match.group(1).replace(",", "")
                result[key] = float(value) if "." in value else int(value)

        # Volume (B/S)
        volume_bs_match = re.search(
            r"<td>Volume \(B/S\)</td>\s*<td[^>]*>([\d,]+)\s*/\s*([\d,]+)</td>", html
        )
        if volume_bs_match:
            result["volume_buy"] = int(volume_bs_match.group(1).replace(",", ""))
            result["volume_sell"] = int(volume_bs_match.group(2).replace(",", ""))

        # Price Bid/Ask
        bid_ask_match = re.search(
            r"<td>Price Bid/Ask</td>\s*<td[^>]*>([\d.]+)\s*/\s*([\d.]+)</td>", html
        )
        if bid_ask_match:
            result["bid_price"] = float(bid_ask_match.group(1))
            result["ask_price"] = float(bid_ask_match.group(2))

        return result

    except Exception as e:
        logger.error(f"get_klse_intraday_stats failed for {ticker}: {e}")
        return {}


def get_klse_full_report(ticker: str) -> Dict[str, Any]:
    """Fetch all available KLSE Screener data for a stock.

    Returns a consolidated dict suitable for risk control / sentiment analysis.

    Args:
        ticker: Stock ticker

    Returns:
        Dict with all data, or empty dict
    """
    if not is_klse(ticker):
        return {}

    return {
        "fundamentals": get_klse_fundamentals(ticker),
        "annual": get_klse_annual(ticker),
        "dividends": get_klse_dividends(ticker),
        "capital_changes": get_klse_capital_changes(ticker),
        "warrants": get_klse_warrants(ticker, limit=5),
        "shareholding_changes": get_klse_shareholding_changes(ticker, limit=5),
        "news": get_klse_news(ticker, limit=5),
        "announcements": get_klse_announcements(ticker, limit=5),
    }


def get_klse_quarterly_history(ticker: str, limit: int = 20) -> str:
    """Fetch multi-quarter history for a KLSE stock.
    
    DEPRECATED: This function returns formatted string for LLM consumption.
    For programmatic use, use get_klse_quarterly_financials_dict() instead.
    
    Args:
        ticker: Stock ticker
        limit: Maximum number of quarters
    
    Returns:
        Formatted quarterly history string, or empty string
    
    Deprecated:
        Will be removed in v2.0. Use get_klse_quarterly_financials_dict() for structured data.
    """
    import warnings
    warnings.warn(
        "get_klse_quarterly_history() is deprecated and will be removed in v2.0. "
        "Use get_klse_quarterly_financials_dict() for structured dict data.",
        DeprecationWarning,
        stacklevel=2
    )
    
    if not is_klse(ticker):
        return ""

    try:
        code = _extract_code(ticker)
        html = fetch_url(
            f"https://www.klsescreener.com/v2/stocks/view/{code}", f"stock_{code}"
        )

        soup = BeautifulSoup(html, "html.parser")
        quarter_div = soup.find("div", id="quarter_reports")
        if not quarter_div:
            return ""

        table = quarter_div.find("table")
        if not table:
            return ""

        rows = table.find_all("tr")
        if len(rows) < 2:
            return ""

        # Parse header
        header_row = rows[0]
        headers = [th.get_text().strip() for th in header_row.find_all(["th", "td"])]

        # Map columns
        header_map = {}
        for i, h in enumerate(headers):
            h_lower = h.lower()
            if "revenue" in h_lower:
                header_map["revenue"] = i
            elif h_lower in ["eps", "earning per share"]:
                header_map["eps"] = i
            elif h_lower == "dps":
                header_map["dps"] = i
            elif "quarter" in h_lower or "q date" in h_lower:
                header_map["quarter"] = i
            elif "financial year" in h_lower or "fy" in h_lower:
                header_map["fy"] = i
            elif h_lower in ["p/l", "profit", "net profit"]:
                header_map["profit"] = i
            elif "nta" in h_lower:
                header_map["nta"] = i

        # Parse data rows
        quarter_entries = []
        count = 0

        for row in rows[1:]:
            if count >= limit:
                break

            cells = row.find_all(["td", "th"])
            if len(cells) < len(headers):
                continue

            fy = cells[header_map["fy"]].get_text().strip() if "fy" in header_map else ""
            quarter = (
                cells[header_map["quarter"]].get_text().strip()
                if "quarter" in header_map
                else ""
            )
            revenue = (
                cells[header_map["revenue"]].get_text().strip()
                if "revenue" in header_map
                else ""
            )
            profit = (
                cells[header_map["profit"]].get_text().strip()
                if "profit" in header_map
                else ""
            )
            eps = (
                cells[header_map["eps"]].get_text().strip()
                if "eps" in header_map
                else ""
            )
            dps = (
                cells[header_map["dps"]].get_text().strip()
                if "dps" in header_map
                else ""
            )

            fiscal_period = f"{fy} {quarter}".strip()
            entry = f"**{fiscal_period}:**"

            parts = []
            if revenue:
                parts.append(f"Revenue: {revenue}")
            if profit:
                parts.append(f"Profit: {profit}")
            if eps:
                parts.append(f"EPS: {eps}")
            if dps:
                parts.append(f"DPS: {dps}")

            if parts:
                entry += " " + ", ".join(parts)
                quarter_entries.append(entry)
                count += 1

        if quarter_entries:
            return "## KLSE Quarterly Financial History\n\n" + "\n".join(
                quarter_entries
            )
        return ""

    except Exception as e:
        logger.error(f"get_klse_quarterly_history failed for {ticker}: {e}")
        return ""


def get_klse_enhanced_fundamentals(ticker: str) -> Dict[str, Any]:
    """Fetch enhanced fundamentals with advanced metrics.

    Args:
        ticker: Stock ticker

    Returns:
        Dict with basic + enhanced fundamentals
    """
    if not is_klse(ticker):
        return {}

    try:
        basic = get_klse_fundamentals(ticker)
        code = _extract_code(ticker)
        url = f"https://www.klsescreener.com/v2/stocks/view/{code}"
        html = fetch_url(url, f"stock_{code}_enhanced")

        def _extract_metric(pattern: str) -> Optional[str]:
            match = re.search(pattern, html, re.IGNORECASE)
            return match.group(1) if match else None

        advanced_metrics: Dict[str, Any] = {
            "debt_to_equity_ratio": _extract_metric(
                r"(?:debt to equity|gearing ratio|debt/equity)[^<]*</[^>]+>\s*<[^>]+>\s*([0-9,.]+)"
            ),
            "net_gearing_ratio": _extract_metric(
                r"(?:net gearing|gearing)[^<]*</[^>]+>\s*<[^>]+>\s*([0-9,.]+)"
            ),
            "current_ratio": _extract_metric(
                r"(?:current ratio|liquidity)[^<]*</[^>]+>\s*<[^>]+>\s*([0-9,.]+)"
            ),
            "stochastic_14": _extract_metric(
                r"(?:stochastic|stoch)\s*\(?14\)?[^<]*</[^>]+>\s*<[^>]+>\s*([0-9,.]+)"
            ),
        }

        volume_metrics: Dict[str, Any] = {
            "avg_volume_30d": _extract_metric(
                r"(?:avg vol 30|average volume)[^<]*</[^>]+>\s*<[^>]+>\s*([0-9,.MKb]+)"
            ),
            "volume_today": _extract_metric(
                r"(?:vol today|volume)[^<]*</[^>]+>\s*<[^>]+>\s*([0-9,.MKb]+)"
            ),
        }

        enhanced_data = {**basic}
        for key, value in advanced_metrics.items():
            if value:
                enhanced_data[key] = value
        for key, value in volume_metrics.items():
            if value:
                enhanced_data[key] = value

        return enhanced_data

    except Exception as e:
        logger.error(f"get_klse_enhanced_fundamentals failed for {ticker}: {e}")
        return basic if basic else {"error": str(e)}


def get_klse_market_sentiment() -> str:
    """Fetch overall market sentiment from KLSE Screener.

    Note: KLSE Screener removed Top Gainers/Losers from homepage.

    Returns:
        Formatted market sentiment string
    """
    try:
        html = fetch_url("https://www.klsescreener.com/v2/", "market_overview")
        soup = BeautifulSoup(html, "html.parser")

        ann_section = soup.find("section")
        if ann_section:
            ann_text = ann_section.get_text()[:500].strip()
            if ann_text:
                return f"## KLSE Market Updates\n\n{ann_text}"

        return (
            "## KLSE Market Sentiment\n\n"
            "**Note:** KLSE Screener has removed Top Gainers/Losers from homepage.\n\n"
            "Alternative: Check KLCI via yfinance or individual stock data."
        )

    except Exception as e:
        logger.error(f"get_klse_market_sentiment failed: {e}")
        return f"## KLSE Market Sentiment\n\nUnable to fetch: {str(e)}"


def get_klse_trade_summary(ticker: str) -> Dict[str, Any]:
    """Fetch order book depth for a KLSE stock.

    Returns dict with bid/ask volumes at each price level.
    Empty dict for non-KLSE tickers.

    Args:
        ticker: Stock ticker

    Returns:
        Dict with order book data
    """
    if not is_klse(ticker):
        return {}

    try:
        code = _extract_code(ticker)
        url = f"https://www.klsescreener.com/v2/stocks/trade_summary/{code}"
        html = fetch_url(url, f"trade_summary_{code}")

        price_match = re.search(r'<span class="price">([^<]+)</span>', html)
        current_price = float(price_match.group(1)) if price_match else 0.0

        change_match = re.search(
            r'<span class="price-change[^"]*">([^<]+)</span>', html
        )
        price_change = 0.0
        change_percent = 0.0
        if change_match:
            parts = change_match.group(1).strip().split()
            if parts:
                try:
                    price_change = float(parts[0])
                except ValueError:
                    pass
            if len(parts) > 1:
                try:
                    change_percent = float(
                        parts[1].replace("(", "").replace(")", "").replace("%", "")
                    )
                except ValueError:
                    pass

        bid_levels: List[Dict[str, Any]] = []
        ask_levels: List[Dict[str, Any]] = []

        row_pattern = r'<tr class="row-price"[^>]*data-value="([^"]+)".*?</tr>'
        row_matches = re.findall(row_pattern, html, re.DOTALL)

        for row_data in row_matches:
            try:
                row_match = re.search(
                    rf'<tr class="row-price"[^>]*data-value="{re.escape(row_data)}".*?</tr>',
                    html,
                    re.DOTALL,
                )
                if not row_match:
                    continue

                row_html = row_match.group(0)
                price_data_match = re.search(r'data-value="([^"]+)"', row_html)
                if not price_data_match:
                    continue

                try:
                    price = float(price_data_match.group(1))
                except ValueError:
                    continue

                buy_vol_match = re.search(
                    r'<span class="buy-volume"[^>]*data-value="(\d+)"', row_html
                )
                buy_volume = int(buy_vol_match.group(1)) if buy_vol_match else 0

                sell_vol_match = re.search(
                    r'<span class="sell-volume"[^>]*data-value="(\d+)"', row_html
                )
                sell_volume = int(sell_vol_match.group(1)) if sell_vol_match else 0

                counts = re.findall(
                    r'<div class="small text-secondary d-none">(\d+)</div>', row_html
                )
                buy_count = int(counts[0]) if len(counts) > 0 else 0
                sell_count = int(counts[1]) if len(counts) > 1 else 0

                if buy_volume > 0:
                    bid_levels.append(
                        {"price": price, "volume": buy_volume, "count": buy_count}
                    )
                if sell_volume > 0:
                    ask_levels.append(
                        {"price": price, "volume": sell_volume, "count": sell_count}
                    )

            except Exception as e:
                logger.warning(f"Error parsing order book row: {e}")
                continue

        bid_levels.sort(key=lambda x: x["price"], reverse=True)
        ask_levels.sort(key=lambda x: x["price"])

        total_bid_volume = sum(level["volume"] for level in bid_levels)
        total_ask_volume = sum(level["volume"] for level in ask_levels)

        best_bid = bid_levels[0]["price"] if bid_levels else 0
        best_ask = ask_levels[0]["price"] if ask_levels else 0
        bid_ask_spread = best_ask - best_bid if best_bid and best_ask else 0

        return {
            "current_price": current_price,
            "price_change": price_change,
            "price_change_percent": change_percent,
            "total_bid_volume": total_bid_volume,
            "total_ask_volume": total_ask_volume,
            "bid_ask_spread": bid_ask_spread,
            "bid_levels": bid_levels,
            "ask_levels": ask_levels,
        }

    except Exception as e:
        logger.error(f"get_klse_trade_summary failed for {ticker}: {e}")
        return {}


def get_klse_trade_details(ticker: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Fetch intraday trade details for a KLSE stock.

    Returns list of trades with time, price, change, volume.
    Empty list for non-KLSE tickers.

    Args:
        ticker: Stock ticker
        limit: Maximum number of trades

    Returns:
        List of trade dicts
    """
    if not is_klse(ticker):
        return []

    try:
        code = _extract_code(ticker)
        url = f"https://www.klsescreener.com/v2/stocks/trade_details/{code}"
        html = fetch_url(url, f"trade_details_{code}")

        trades: List[Dict[str, Any]] = []
        row_pattern = (
            r'<tr>\s*<td class="">([^<]+)</td>\s*'
            r'<td class="text-right pr-3">([^<]+)</td>\s*'
            r'<td class="text-right"[^>]*>([^<]*)</td>\s*'
            r'<td class="text-right[^>]*>([^<]+)</td>\s*</tr>'
        )
        row_matches = re.findall(row_pattern, html, re.DOTALL)

        for time_str, price_str, change_str, volume_str in row_matches[:limit]:
            try:
                time_str = time_str.strip()
                price_str = price_str.strip()
                change_str = change_str.strip()

                change = 0.0
                if change_str:
                    change_clean = re.sub(r"<[^>]+>", "", change_str).strip()
                    try:
                        change = float(change_clean) if change_clean else 0.0
                    except ValueError:
                        change = 0.0

                volume = int(volume_str.strip().replace(",", ""))
                price = float(price_str)

                trades.append(
                    {
                        "time": time_str,
                        "price": price,
                        "change": change,
                        "volume": volume,
                    }
                )
            except Exception as e:
                logger.warning(f"Error parsing trade row: {e}")
                continue

        return trades

    except Exception as e:
        logger.error(f"get_klse_trade_details failed for {ticker}: {e}")
        return []


def get_klse_comments(ticker: str, limit: int = 30) -> List[Dict[str, Any]]:
    """Fetch user comments/discussions for a KLSE stock.

    Returns list of comment dicts with metadata.
    Empty list for non-KLSE tickers.

    Args:
        ticker: Stock ticker
        limit: Maximum number of comments

    Returns:
        List of comment dicts
    """
    if not is_klse(ticker):
        return []

    try:
        code = _extract_code(ticker)
        url = f"https://www.klsescreener.com/v2/comments/all/stock/{code}"
        html = fetch_url(url, f"comments_{code}")

        comments: List[Dict[str, Any]] = []
        comment_starts = list(re.finditer(r'id="comment-(\d+)"', html))

        for i, match in enumerate(comment_starts[:limit]):
            comment_id = match.group(1)
            start_pos = match.start()
            end_pos = (
                comment_starts[i + 1].start()
                if i + 1 < len(comment_starts)
                else len(html)
            )
            comment_html = html[start_pos:end_pos]

            try:
                username_match = re.search(
                    r'<strong class="text-primary">(.*?)</strong>',
                    comment_html,
                    re.DOTALL,
                )
                username = (
                    username_match.group(1).strip() if username_match else "Anonymous"
                )

                text_match = re.search(
                    r'<div class="message-container[^"]*">(.*?)</div>',
                    comment_html,
                    re.DOTALL,
                )
                if not text_match:
                    continue

                comment_text = re.sub(r"<[^>]+>", "", text_match.group(1)).strip()
                if not comment_text:
                    continue

                likes = 0
                likes_match = re.search(
                    r'<span class="align-right text-muted"[^>]*>\s*(\d+)?\s*Like',
                    comment_html,
                )
                if likes_match and likes_match.group(1):
                    likes = int(likes_match.group(1))
                else:
                    likes_plural = re.search(r">(\d+)\s+Likes<", comment_html)
                    if likes_plural:
                        likes = int(likes_plural.group(1))

                timestamp_str = ""
                ts_match = re.search(r'data-datetime="([^"]+)"', comment_html)
                if ts_match:
                    timestamp_str = ts_match.group(1)
                else:
                    ts_nested = re.search(
                        r'<span class="text-muted"[^>]*>.*?<a[^>]*data-datetime="([^"]+)"',
                        comment_html,
                        re.DOTALL,
                    )
                    if ts_nested:
                        timestamp_str = ts_nested.group(1)

                is_reply = "comment-reply" in comment_html

                comments.append(
                    {
                        "comment_id": comment_id,
                        "username": username,
                        "comment_text": comment_text,
                        "likes": likes,
                        "timestamp": timestamp_str,
                        "is_reply": is_reply,
                        "parent_comment_id": None,
                    }
                )

            except Exception as e:
                logger.warning(f"Error parsing comment {comment_id}: {e}")
                continue

        return comments

    except Exception as e:
        logger.error(f"get_klse_comments failed for {ticker}: {e}")
        return []


# ============= Formatted Wrappers =============


def get_klse_trade_summary_formatted(ticker: str) -> str:
    """Format trade summary for agent consumption.

    Args:
        ticker: Stock ticker

    Returns:
        Formatted string summary
    """
    summary = get_klse_trade_summary(ticker)
    if not summary:
        return ""

    total_bid = summary["total_bid_volume"]
    total_ask = summary["total_ask_volume"]
    total_volume = total_bid + total_ask

    buy_ratio = total_bid * 100 // total_volume if total_volume else 0
    sell_ratio = total_ask * 100 // total_volume if total_volume else 0

    result = (
        f"## KLSE Order Book Summary (15-min delayed)\n\n"
        f"**Current Price:** RM{summary['current_price']:.3f}\n"
        f"**Change:** {summary['price_change']:+.3f} ({summary['price_change_percent']:+.1f}%)\n"
        f"**Spread:** {summary['bid_ask_spread']:.3f}\n\n"
        f"**Total Volume:**\n"
        f"- 🟢 Bid (Buy): {total_bid:,} ({buy_ratio}%)\n"
        f"- 🔴 Ask (Sell): {total_ask:,} ({sell_ratio}%)\n"
    )

    if total_bid > total_ask * 1.5:
        result += "\n⚠️ **Buy Pressure:** Bid volume significantly higher\n"
    elif total_ask > total_bid * 1.5:
        result += "\n⚠️ **Sell Pressure:** Ask volume significantly higher\n"

    result += "\n**Top Bid Levels:**\n"
    for level in summary["bid_levels"][:5]:
        result += (
            f"- RM{level['price']:.3f}: {level['volume']:,} shares ({level['count']} orders)\n"
        )

    result += "\n**Top Ask Levels:**\n"
    for level in summary["ask_levels"][:5]:
        result += (
            f"- RM{level['price']:.3f}: {level['volume']:,} shares ({level['count']} orders)\n"
        )

    return result


def get_klse_trade_details_formatted(ticker: str, limit: int = 50) -> str:
    """Format trade details for agent consumption.

    Args:
        ticker: Stock ticker
        limit: Maximum trades

    Returns:
        Formatted string summary
    """
    trades = get_klse_trade_details(ticker, limit)
    if not trades:
        return ""

    total_volume = sum(t["volume"] for t in trades)
    prices = [t["price"] for t in trades]
    avg_price = sum(prices) / len(prices) if prices else 0

    buy_volume = sum(t["volume"] for t in trades if t["change"] > 0)
    sell_volume = sum(t["volume"] for t in trades if t["change"] < 0)
    neutral_volume = total_volume - buy_volume - sell_volume

    result = (
        f"## KLSE Intraday Trade Details (15-min delayed)\n\n"
        f"**Total Trades:** {len(trades)}\n"
        f"**Total Volume:** {total_volume:,}\n"
        f"**Average Price:** RM{avg_price:.4f}\n\n"
        f"**Volume Breakdown:**\n"
        f"- 🟢 Buy Volume: {buy_volume:,} ({buy_volume * 100 // total_volume if total_volume else 0}%)\n"
        f"- 🔴 Sell Volume: {sell_volume:,} ({sell_volume * 100 // total_volume if total_volume else 0}%)\n"
        f"- ⚪ Neutral: {neutral_volume:,} ({neutral_volume * 100 // total_volume if total_volume else 0}%)\n\n"
        f"**Recent Trades:**\n"
    )

    for trade in trades[: min(10, len(trades))]:
        change_indicator = ""
        if trade["change"] > 0:
            change_indicator = f"+{trade['change']:.3f} 🟢"
        elif trade["change"] < 0:
            change_indicator = f"{trade['change']:.3f} 🔴"
        else:
            change_indicator = "0.000 ⚪"

        result += (
            f"- {trade['time']} | RM{trade['price']:.3f} | {change_indicator} | {trade['volume']:,}\n"
        )

    return result


def get_klse_comments_formatted(ticker: str, limit: int = 30) -> str:
    """Format comments for agent consumption with sentiment analysis.

    Args:
        ticker: Stock ticker
        limit: Maximum comments

    Returns:
        Formatted string with sentiment breakdown
    """
    comments = get_klse_comments(ticker, limit)
    if not comments:
        return ""

    positive_keywords = [
        "good",
        "great",
        "buy",
        "bullish",
        "strong",
        "upside",
        "positive",
        "dividend",
        "profit",
        "growth",
        "undervalued",
        "recommend",
    ]
    negative_keywords = [
        "bad",
        "sell",
        "bearish",
        "weak",
        "downside",
        "negative",
        "loss",
        "overvalued",
        "avoid",
        "risk",
        "fall",
        "drop",
    ]

    positive_count = 0
    negative_count = 0
    neutral_count = 0
    sample_comments = []

    for comment in comments[: min(10, len(comments))]:
        text_lower = comment["comment_text"].lower()
        has_positive = any(kw in text_lower for kw in positive_keywords)
        has_negative = any(kw in text_lower for kw in negative_keywords)

        if has_positive and not has_negative:
            positive_count += 1
        elif has_negative and not has_positive:
            negative_count += 1
        else:
            neutral_count += 1

        sample_comments.append(
            f"- [{comment['likes']}👍] {comment['comment_text'][:200]}"
        )

    total = len(comments)
    result = (
        f"## KLSE Stock Discussions\n\n"
        f"**Total Comments:** {total}\n"
        f"**Sentiment Overview:**\n"
        f"- 👍 Positive: {positive_count} ({positive_count * 100 // total if total else 0}%)\n"
        f"- 👎 Negative: {negative_count} ({negative_count * 100 // total if total else 0}%)\n"
        f"- ➖ Neutral: {neutral_count} ({neutral_count * 100 // total if total else 0}%)\n\n"
        f"**Sample Comments:**\n" + "\n".join(sample_comments)
    )

    return result
