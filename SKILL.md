---
name: klse-screener-py
description: >
  Malaysian (KLSE/Bursa Malaysia) stock data via the klse-screener-py Python library:
  fundamentals, key ratios, financial reports, OHLCV price history, dividends, corporate
  actions, news, announcements, retail sentiment, sector mapping, Bursa market overview.
  Use when the user asks about *.KL tickers, Bursa Malaysia or KLSE Screener data,
  Malaysian stocks, KLSE sectors, or market-wide KLSE announcements/reports.
license: MIT
---

# KLSE Screener

Scraper for KLSE Screener (klsescreener.com/v2) — Malaysian stock data.
Sync-only. Returns dicts / lists of dicts / formatted strings.
Global 2-second rate limit between HTTP requests, 10-minute in-memory cache.

## When to use

- Any question about Bursa Malaysia / KLSE tickers (`*.KL`)
- Market-wide KLSE data: indices, top movers, dividend calendar, announcements, financial reports
- When other sources (yfinance, akshare) lack Malaysian fundamentals/announcements

## Setup

Python >= 3.10. Only dependency: `beautifulsoup4`.

```bash
pip install klse-screener-py        # PyPI
# or, in this repo:
uv sync                             # or: pip install -e ".[dev]"
```

## Scripts (fastest path)

Run from the repo root with `uv run`, or with `python` in any env where the
package is installed.

| Script | Usage | Gets you |
|---|---|---|
| `scripts/stock.py` | `uv run scripts/stock.py 5132.KL [fundamentals ratios financials news announcements dividends shareholding reports sentiment]` | Stock profile (all sections if none given) |
| `scripts/market.py` | `uv run scripts/market.py` | Bursa market overview: KLSE + sector indices, top active/turnover/gainers/losers |
| `scripts/price.py` | `uv run scripts/price.py 5132.KL [30d\|10y]` | OHLCV history table |
| `scripts/sectors.py` | `uv run scripts/sectors.py [sector_code]` | Sector list, or a sector's constituents (`0001I`…`0065I`) |

## Python API

```python
from klse_screener import (
    get_klse_fundamentals,       # P/E, EPS, DY, NTA, P/B, ROE, RSI, market cap
    get_klse_key_ratios,         # same ratios as floats
    get_klse_full_report,        # everything consolidated in one dict
    get_bursa_market_data,       # market overview
    get_klse_price_history,      # 30d / 10y OHLCV
)

data = get_klse_fundamentals("5132.KL")
```

Full catalog of all ~30 exported functions with signatures and return shapes:
[`references/api-reference.md`](references/api-reference.md).

Data gotchas (rate limits, 15-min delay, ticker format, error conventions,
unit scaling): [`references/data-quirks.md`](references/data-quirks.md).

## Rules of thumb

- Ticker = `{code}.KL`. Preserve leading zeros (`0012.KL`, never `12.KL`).
- Budget ~1 request/2s; one process reuses its 10-min cache.
- Trading data is 15-min delayed (Bursa regulation).
- Failure conventions: dict gains an `"error"` key, lists return `[]`,
  `get_klse_price_history` returns `None`. Non-KLSE tickers are a no-op.
- Parsing is HTML/regex — empty results can mean a site layout change, not
  missing data. Check `tests/` before rewriting parsers.
- Async: `await asyncio.to_thread(get_klse_fundamentals, "5132.KL")`.

## Development

```bash
uv sync --extra dev
uv run pytest tests/ -v
uv run ruff check src/ tests/
```
