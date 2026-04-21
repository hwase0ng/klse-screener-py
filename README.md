# klse-screener-py

Malaysian (KLSE/Bursa Malaysia) stock data scraper. Fetch fundamentals, trading data, news, and announcements from [KLSE Screener](https://www.klsescreener.com/v2).

## Features

- **17 data functions** covering fundamentals, trading data, news, and announcements
- **Rate-limited HTTP client** (2-second intervals, respectful scraping)
- **Market detection** for KLSE tickers (*.KL format)
- **No caching** - host application controls caching strategy
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
    get_klse_news,
    get_klse_trade_summary,
    get_klse_comments,
)

# Get fundamentals
data = get_klse_fundamentals("5132.KL")
print(f"P/E: {data.get('pe_ratio')}")
print(f"Dividend Yield: {data.get('dividend_yield')}")

# Get news
news = get_klse_news("5132.KL", limit=10)
print(news)

# Get order book depth
summary = get_klse_trade_summary("5132.KL")
print(f"Bid Volume: {summary.get('total_bid_volume'):,}")
print(f"Ask Volume: {summary.get('total_ask_volume'):,}")
```

## API Reference

### Fundamentals

| Function | Description | Returns |
|----------|-------------|---------|
| `get_klse_fundamentals(ticker)` | P/E, EPS, DY, NTA, P/B, ROE, RSI | `Dict[str, Any]` |
| `get_klse_enhanced_fundamentals(ticker)` | + debt ratios, stochastic, volume | `Dict[str, Any]` |
| `get_klse_annual(ticker, limit=3)` | Annual revenue, profit, EPS | `str` |
| `get_klse_quarterly_history(ticker, limit=20)` | Multi-quarter history | `str` |
| `get_klse_dividends(ticker, limit=5)` | Dividend history with dates | `str` |
| `get_klse_capital_changes(ticker, limit=5)` | Splits, bonus issues | `str` |

### Trading Data

| Function | Description | Returns |
|----------|-------------|---------|
| `get_klse_intraday_stats(ticker)` | High/Low/Open/Volume, Bid/Ask | `Dict[str, Any]` |
| `get_klse_trade_summary(ticker)` | Order book depth (15-min delayed) | `Dict[str, Any]` |
| `get_klse_trade_details(ticker, limit=50)` | Time-stamped trades | `List[Dict]` |
| `get_klse_warrants(ticker, limit=5)` | Warrant prices, volumes | `str` |

### Sentiment & News

| Function | Description | Returns |
|----------|-------------|---------|
| `get_klse_news(ticker, limit=10)` | Stock-specific news | `str` |
| `get_klse_announcements(ticker, limit=10)` | Bursa Malaysia announcements | `str` |
| `get_klse_comments(ticker, limit=30)` | Forum discussions | `List[Dict]` |
| `get_klse_shareholding_changes(ticker, limit=20)` | Institutional transactions | `str` |

### Market Data

| Function | Description | Returns |
|----------|-------------|---------|
| `get_klse_market_sentiment()` | Market overview | `str` |
| `get_klse_full_report(ticker)` | All data consolidated | `Dict[str, Any]` |

### Formatted Wrappers

| Function | Description | Returns |
|----------|-------------|---------|
| `get_klse_comments_formatted(ticker, limit=30)` | Sentiment analysis + samples | `str` |
| `get_klse_trade_details_formatted(ticker, limit=50)` | Volume breakdown | `str` |
| `get_klse_trade_summary_formatted(ticker)` | Bid/ask pressure | `str` |

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

Non-KLSE tickers return empty results (no-op).

## Limitations

- **15-minute delayed** trading data (per Bursa Malaysia regulations)
- **Market sentiment** function has limited data (KLSE Screener removed some widgets)
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

### 0.1.0 (2026-04-21)
- Initial release
- 17 data functions extracted from FinGenius
- Rate-limited HTTP client
- Market detection utility
