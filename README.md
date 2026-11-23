# klse-screener-py

Malaysian (KLSE/Bursa Malaysia) stock data scraper. Fetch fundamentals, trading data, news, and announcements from [KLSE Screener](https://www.klsescreener.com/v2).

## Features

- **42 data functions** covering fundamentals, trading data, news, announcements, price history, and sectors
- **Rate-limited HTTP client** (2-second intervals, respectful scraping)
- **Market detection** for KLSE tickers (*.KL format)
- **In-process cache** (10-min TTL) to stay inside the rate limit; no disk cache - host application controls longer-term caching
- **Dict-only responses** - lightweight, no Pydantic dependency
- **Sync-only** - use with `asyncio.to_thread()` or executor for async

## Installation

```bash
pip install klse-screener-py
```

## Quick Start

```python
from klse_screener import (
    get_klse_fundamentals,
    get_klse_news_raw,
    get_klse_trade_summary,
)

# Get fundamentals
data = get_klse_fundamentals("5132.KL")
print(f"P/E: {data.get('pe_ratio')}")
print(f"Dividend Yield: {data.get('dividend_yield')}")

# Get news
for item in get_klse_news_raw("5132.KL", limit=10):
    print(item["date"], item["title"])

# Get order book depth
summary = get_klse_trade_summary("5132.KL")
print(f"Bid Volume: {summary.get('total_bid_volume'):,}")
print(f"Ask Volume: {summary.get('total_ask_volume'):,}")
```

## API Reference

### Per-Stock: Fundamentals

| Function | Description | Returns |
|----------|-------------|---------|
| `get_klse_fundamentals(ticker)` | P/E, EPS, DY, NTA, P/B, ROE, RSI, market cap | `Dict[str, Any]` |
| `get_klse_enhanced_fundamentals(ticker)` | + debt ratios, stochastic, volume | `Dict[str, Any]` |
| `get_klse_key_ratios(ticker)` | Key ratios as numeric floats | `Dict[str, Any]` |
| `get_klse_quarterly_financials_dict(ticker)` | Quarterly figures + TTM totals | `Dict[str, Any]` |
| `get_klse_annual_financials_dict(ticker)` | Annual revenue, profit, EPS | `Dict[str, Any]` |
| `get_klse_fundamentals_mf_enhanced(ticker)` | Consolidated for Magic Formula scoring | `Dict[str, Any]` |
| `get_klse_financial_report_figures(code, quarter_end_date)` | PBT, attributable, NAPS, EPS, DPS, revenue for one quarter | `Dict[str, Any]` |
| `get_klse_quarterly_history(ticker, limit=20)` | Multi-quarter history (text) | `str` |
| `get_klse_dividends_raw(ticker, limit=5)` | Dividend history with dates | `List[Dict]` |
| `get_klse_capital_changes_raw(ticker, limit=5)` | Splits, bonus issues | `List[Dict]` |

### Per-Stock: Trading Data

| Function | Description | Returns |
|----------|-------------|---------|
| `get_klse_intraday_stats(ticker)` | High/Low/Open/Volume, Bid/Ask | `Dict[str, Any]` |
| `get_klse_trade_summary(ticker)` | Order book depth (15-min delayed) | `Dict[str, Any]` |
| `get_klse_trade_details(ticker, limit=50)` | Time-stamped trades | `List[Dict]` |
| `get_klse_warrants_raw(ticker, limit=5)` | Warrant prices, volumes | `List[Dict]` |
| `get_klse_full_report(ticker)` | All of the above consolidated | `Dict[str, Any]` |

### Per-Stock: Sentiment & News

| Function | Description | Returns |
|----------|-------------|---------|
| `get_klse_news_raw(ticker, limit=10)` | Stock-specific news (title, date, excerpt, url) | `List[Dict]` |
| `get_klse_announcements_raw(ticker, limit=10)` | Bursa Malaysia announcements | `List[Dict]` |
| `get_klse_comments(ticker, limit=30)` | Forum discussions | `List[Dict]` |
| `get_klse_shareholding_changes_raw(ticker, limit=20)` | Institutional transactions | `List[Dict]` |
| `get_klse_comments_formatted(ticker, limit=30)` | Sentiment analysis + samples | `str` |
| `get_klse_trade_details_formatted(ticker, limit=50)` | Volume breakdown | `str` |
| `get_klse_trade_summary_formatted(ticker)` | Bid/ask pressure | `str` |

### Per-Stock: Price History & QR Announcements

| Function | Description | Returns |
|----------|-------------|---------|
| `get_klse_price_history(symbol, period='30d')` | OHLCV bars; `period`: `'30d'` or `'10y'` | `Optional[Dict]` |
| `scrape_ohlcv_raw(symbol, period='30d')` | Same, raw list without metadata | `List[Dict]` |
| `get_klse_daily_financial_reports(scrape_date=None)` | Market-wide QR filings for a date | `List[Dict]` |
| `get_klse_announcements_by_ticker(ticker, days_back=3)` | QR announcements for one stock | `List[Dict]` |
| `get_klse_financial_reports_by_ticker(ticker, limit=20)` | Financial report filings for one stock | `List[Dict]` |

### Market-Wide

| Function | Description | Returns |
|----------|-------------|---------|
| `get_bursa_market_data()` | Bursa Malaysia overview: KLSE + sector indices, top active/turnover/gainers/losers | `Dict[str, Any]` |
| `get_klse_dividend_calendar(limit=50)` | Upcoming dividend entitlements | `List[Dict]` |
| `get_klse_corporate_actions(limit=20)` | Recent corporate actions | `List[Dict]` |
| `get_klse_announcements_by_category(category, ticker=None, limit=20)` | Category: `EA` `SH` `FA` `SB` `AL` `GM` | `List[Dict]` |
| `get_klse_dividend_announcements(ticker, limit=20)` | Entitlements (EA) | `List[Dict]` |
| `get_klse_insider_dealings(ticker, limit=20)` | Shareholdings (SH) | `List[Dict]` |
| `get_klse_financial_results(ticker, limit=20)` | Financial results (FA) | `List[Dict]` |
| `get_klse_share_buybacks(ticker, limit=20)` | Buybacks (SB) | `List[Dict]` |
| `get_klse_additional_listings(ticker, limit=20)` | Additional listings (AL) | `List[Dict]` |
| `get_klse_general_meetings(ticker, limit=20)` | AGM/EGM notices (GM) | `List[Dict]` |
| `get_klse_financial_reports(ticker=None, limit=20)` | Report filings (market-wide or per-stock) | `List[Dict]` |
| `get_klse_market_announcements(category=None, limit=50)` | All Bursa announcements, optional category filter | `List[Dict]` |

### Sectors

| Function | Description | Returns |
|----------|-------------|---------|
| `get_klse_sector_info()` | Bursa sector code → name mapping (13 sectors) | `Dict[str, Dict]` |
| `get_klse_sector_stocks(sector_code)` | Constituents of one sector (e.g. `0001I`) | `List[Dict]` |
| `get_klse_all_sector_stocks()` | Constituents of all 13 sectors (13 rate-limited requests) | `Dict[str, List[Dict]]` |

## Usage Examples

### Async Usage

```python
import asyncio
from klse_screener import get_klse_fundamentals

async def get_data():
    # Run sync function in thread pool
    data = await asyncio.to_thread(get_klse_fundamentals, "5132.KL")
    return data

asyncio.run(get_data())
```

### Batch Processing

```python
from concurrent.futures import ThreadPoolExecutor
from klse_screener import get_klse_fundamentals

stocks = ["5132.KL", "7152.KL", "9172.KL"]

with ThreadPoolExecutor(max_workers=5) as executor:
    results = list(executor.map(get_klse_fundamentals, stocks))

for stock, data in zip(stocks, results):
    print(f"{stock}: P/E={data.get('pe_ratio')}")
```

### Error Handling

```python
from klse_screener import get_klse_fundamentals

data = get_klse_fundamentals("5132.KL")
if "error" in data:
    print(f"Error: {data['error']}")
else:
    print(f"Success: {data}")
```

## Rate Limiting

- **2-second interval** between requests (enforced globally)
- **10 requests/minute** maximum
- Automatic backoff on errors

## Ticker Format

KLSE tickers use the format `{code}.KL`:
- `5132.KL` - Deleum Berhad
- `7152.KL` - Yinson Holdings
- `9172.KL` - FPI Corporation
- `0012.KL` - Public Bank Berhad

**Leading zeros are significant** - `0012.KL` is valid, `12.KL` is not.
Non-KLSE tickers return empty results (no-op).

## Limitations

- **15-minute delayed** trading data (per Bursa Malaysia regulations)
- `get_bursa_market_data()` parses sections independently - partial data is returned if some widgets fail; `error` key only if all fail
- **HTML parsing** - may break if KLSE Screener changes layout

## License

MIT License - see [LICENSE](LICENSE) file.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `pytest tests/`
5. Submit a pull request

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Run linting
ruff check src/ tests/
```

## Changelog

### 3.4.1 (2026-11-23)
- Fixed `project.urls` (Homepage/Repository) pointing at the wrong GitHub org
- Fixed the same wrong URLs in `docs/MIGRATION_TO_V2.md` and `docs/INTEGRATION_COMPLETE.md`

### 3.4.0 (2026-11-23)
- Fixed `get_klse_full_report` crash (missing import + removed call to a non-existent market-sentiment function)
- Fixed `get_klse_enhanced_fundamentals` masking errors via an unbound variable in its exception path
- Fixed `get_bursa_market_data` Top Turnover parsing (page now renders `.turnover`; value key derived from section)
- Fixed `qr_announcements` href type error
- Restored 9 missing public exports in `__all__` (financials, price history, QR announcements)
- Synced `_version.py` with the package version
- README: refreshed quickstart, full API reference (42 functions), caching and ticker notes
- Modernized typing (PEP 585/604), sorted imports, and made `ruff check` clean

### 0.1.0 (2026-04-21)
- Initial release
- 17 data functions extracted from FinGenius
- Rate-limited HTTP client
- Market detection utility
