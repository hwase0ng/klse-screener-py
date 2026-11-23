# Data Quirks & Gotchas

Read before writing code against this library or interpreting its output.

## Tickers

- Format: `{code}.KL` — e.g. `5132.KL` (Deleum Berhad), `0012.KL` (Public Bank).
- **Leading zeros are significant.** `0012.KL` is valid; `12.KL` is not.
  (v3.1.1 fixed a bug that stripped them.)
- `_extract_code()` strips the `.KL` suffix for URLs; it does not touch
  leading zeros.
- Non-KLSE tickers (e.g. `AAPL`, `0700.HK`) are a no-op in core functions —
  they return `{}` / `[]` / `None` without raising.
- Cross-market formats (yfinance `0700.HK`/`7088.KL`, Moomoo `MY.07088`,
  akshare `hk01282`) must be converted to `{code}.KL` before calling this
  library.

## Rate limits & caching

- 2.0s minimum interval between HTTP requests, enforced **globally** per
  process (module-level state in `http.py`).
- In-memory cache with 10-minute TTL, keyed by `cache_key` — a process
  running a long batch reuses pages for 10 min; a fresh `uv run`/`python`
  process refetches.
- Practical budget: ~10 requests/minute. `get_klse_all_sector_stocks()`
  alone costs 13 requests.
- `reset_rate_limit()` / `clear_cache()` reset the global state.
- 15s request timeout; a dead network raises, the calling function usually
  converts that to its error convention.

## Data freshness

- Trading data (order book, intraday stats) is **15-min delayed** per Bursa
  Malaysia regulation.
- Market overview (`get_bursa_market_data`) is a single snapshot page —
  re-call for a fresh scrape.
- `get_klse_daily_financial_reports()` defaults to today; pass
  `scrape_date=date(...)` for backfills.

## Error conventions (do not assume exceptions)

| Function shape | On failure |
|---|---|
| dict-returning (`get_klse_fundamentals`, `get_klse_trade_summary`, `get_bursa_market_data`, `get_klse_financial_report_figures`, …) | `{}` (core) or `{"error": "<msg>"}` (others). Check `"error" in result` or empty-dict. |
| list-returning (raw, formatted-list, market-wide) | `[]` |
| `get_klse_price_history` | `None` |
| string-returning (formatted wrappers, `get_klse_quarterly_history`) | `""` |

`get_bursa_market_data` is partial-tolerant: sections parse independently,
`error` key only when **all** sections fail.

## Unit scaling

- `get_klse_financial_report_figures`: the source page prints monetary rows
  in **MYR'000**; the function multiplies PBT / attributable / revenue by
  1000 → **raw RM**. `eps`, `dps` (sen) and `nta` (RM) are returned as
  printed.
- `get_klse_fundamentals` returns mostly **strings** (e.g. market cap
  `"1.5b"`, dividend yield `"3.5%"`, RSI `"Oversold (28.5)"`) — convert
  before arithmetic. `get_klse_key_ratios` is the numeric alternative.
- QoQ%/YoY% in quarterly financials are recovered from the cell's sign CSS
  class; negative values are signed floats.

## Parser fragility

- Everything is HTML/regex (BeautifulSoup where tables, regex where not).
  KLSE Screener layout changes silently break parsing → empty results.
- Financial-report P&L parsing is label-anchored (robust against injected
  "AI insight" rows that shift positional indices).
- Empty ≠ error. Before rewriting a parser: run `pytest tests/`, check
  `git log --oneline` for recent parser fixes, and diff the live HTML
  (`fetch_url`) against what the parser expects.
- No retry/backoff beyond the rate limiter; a 403 surfaces as an error
  dict/empty list.

## Caching is per-process only

The library has **no disk cache** by design — the host application owns
caching. If you need repeat access across process invocations, wrap calls in
your own cache (e.g. 15–60 min TTL for fundamentals, shorter for prices).
