# API Reference

All functions from `klse_screener` (v3.3.x). Ticker format `{code}.KL` (e.g.
`5132.KL`); some functions also accept the bare numeric code (`"0012"`).
All functions are synchronous.

## Per-stock — core (`core.py`)

| Function | Returns | Notes |
|---|---|---|
| `get_klse_fundamentals(ticker)` | `Dict` | `name`, `sector`, `pe_ratio`, `eps`, `dividend_yield`, `nta`, `pb_ratio`, `roe`, `market_cap`, `dps`, `psr`, `fifty_two_week_range`, `rsi_14`, latest-quarter fields. `{}` for non-KLSE. |
| `get_klse_enhanced_fundamentals(ticker)` | `Dict` | Fundamentals + debt ratios, stochastic, volume. |
| `get_klse_quarterly_history(ticker, limit=20)` | `str` | Multi-quarter history, formatted text. |
| `get_klse_intraday_stats(ticker)` | `Dict` | `high`, `low`, `open`, `volume`, `volume_buy`, `volume_sell`, `bid_price`, `ask_price`, `last_updated`. |
| `get_klse_trade_summary(ticker)` | `Dict` | Order-book depth: `current_price`, `total_bid_volume`, `total_ask_volume`, … 15-min delayed. |
| `get_klse_trade_details(ticker, limit=50)` | `List[Dict]` | Time-stamped trades. |
| `get_klse_comments(ticker, limit=30)` | `List[Dict]` | Forum comments: `username`, `comment_text`, `likes`, `timestamp`, `is_reply`. |
| `get_klse_full_report(ticker)` | `Dict` | Everything above consolidated. |

Raw (list of dicts, recommended for programmatic use):

| Function | Default limit |
|---|---|
| `get_klse_news_raw(ticker, limit=10)` | 10 — items carry `title`, `date`, excerpt, url |
| `get_klse_announcements_raw(ticker, limit=10)` | 10 |
| `get_klse_dividends_raw(ticker, limit=5)` | 5 |
| `get_klse_capital_changes_raw(ticker, limit=5)` | 5 — splits, bonus issues |
| `get_klse_warrants_raw(ticker, limit=5)` | 5 |
| `get_klse_shareholding_changes_raw(ticker, limit=20)` | 20 — institutional transactions |

Formatted wrappers (LLM-friendly strings): `get_klse_trade_summary_formatted(ticker)`,
`get_klse_trade_details_formatted(ticker, limit=50)`,
`get_klse_comments_formatted(ticker, limit=30)`.

## Per-stock — structured financials (`financials.py`, pandas-free)

| Function | Returns |
|---|---|
| `get_klse_key_ratios(ticker)` | `Dict` — `pe_ratio`, `eps`, `dividend_yield`, `nta_per_share`, `pb_ratio`, `roe`, `market_cap`, `dps`, `psr`, `fifty_two_week_range`, `rsi_14` (numeric where possible) |
| `get_klse_quarterly_financials_dict(ticker)` | `Dict` — `ttm_revenue`, `ttm_net_profit`, `ttm_eps`, `quarterly_data[]` |
| `get_klse_annual_financials_dict(ticker)` | `Dict` — `annual_data[]` |
| `get_klse_fundamentals_mf_enhanced(ticker)` | `Dict` — consolidated for Magic Formula: market cap, P/E, P/B, ROE, TSM figures, approximations |
| `get_klse_financial_report_figures(code, quarter_end_date, return_html=False)` | `Dict` — P&L for one quarter: `profit_before_tax`, `profit_attributable_parent`, `nta_parent`, `eps`, `dps`, `revenue`. `quarter_end_date` is `"YYYY-MM-DD"`. Monetary values in raw RM (page's MYR'000 ×1000); EPS/DPS/NAPS as printed. Error → `{"error": …}`. |

## Per-stock — price history (`price_history.py`)

| Function | Returns |
|---|---|
| `scrape_ohlcv_raw(symbol, period="30d")` | `List[Dict]` — `date`, `timestamp`, `open`, `high`, `low`, `close`, `volume` (+ `adjusted_close` for `10y`). `period`: `"30d"` (daily) or `"10y"` (chart data). |
| `get_klse_price_history(symbol, period="30d")` | `Optional[Dict]` — `symbol`, `period`, `data_source`, `count`, `last_updated`, `data`. `None` on failure. |

## Per-stock — QR announcements (`qr_announcements.py`)

| Function | Returns |
|---|---|
| `get_klse_daily_financial_reports(scrape_date=None)` | `List[Dict]` — market-wide QR filings for a date (default today): `ticker`, `company_name`, `announced_date`, `quarter`, `quarter_end_date`, `revenue`, `net_profit`, `eps`, `dps` |
| `get_klse_announcements_by_ticker(ticker, days_back=3)` | `List[Dict]` |
| `get_klse_financial_reports_by_ticker(ticker, limit=20)` | `List[Dict]` |

## Market-wide — entitlements (`entitlements.py`)

- `get_klse_dividend_calendar(limit=50) -> List[Dict]`
- `get_klse_corporate_actions(limit=20) -> List[Dict]`

## Market-wide — announcements (`announcements.py`)

Category codes: `EA` entitlements, `SH` shareholdings, `FA` financial results,
`SB` share buyback, `AL` additional listing, `GM` general meetings.

- `get_klse_announcements_by_category(category, ticker=None, limit=20) -> List[Dict]`
  — items: `ticker`, `company_name`, `title`, `date`, `category`, `url`
- Per-category convenience (all `(ticker, limit=20) -> List[Dict]`):
  `get_klse_dividend_announcements`, `get_klse_insider_dealings`,
  `get_klse_financial_results`, `get_klse_share_buybacks`,
  `get_klse_additional_listings`, `get_klse_general_meetings`

## Market-wide — reports & announcements (`financial_reports.py`)

- `get_klse_financial_reports(ticker=None, limit=20) -> List[Dict]`
  — `ticker`, `company_name`, `report_type`, `fiscal_period`, `filing_date`,
  `revenue`, `profit`, `url`. `ticker=None` → market-wide.
- `get_klse_market_announcements(category=None, limit=50) -> List[Dict]`
  — all Bursa announcements; `category` optional (EA/SH/FA/SB/AL/GM).

## Market-wide — Bursa market overview (`market_data.py`)

`get_bursa_market_data() -> Dict`:

- `scraped_at`, `source`
- `klse_indices[]` — `code`, `name` (FBM KLCI, etc.), `price`, `change_abs`,
  `change_pct`, `trend` (`up`/`down`/`unchanged`)
- `sector_indices[]` — Bursa's 12 sector indices, same shape
- `top_active[]`, `top_turnover[]`, `top_gainers[]`, `top_gainers_pct[]`,
  `top_losers[]`, `top_losers_pct[]` — `rank`, `code`, `name`, `price`,
  `change_pct`, `trend`, `volume` or `turnover`

Sections parse independently; partial data is returned. `error` key only if
all sections fail.

## Sectors (`sectors.py`)

- `get_klse_sector_info() -> Dict[str, Dict]` — 13 Bursa sector
  code→`{code, name}` mappings
- `get_klse_sector_stocks(sector_code) -> List[Dict]` — `code`, `symbol`,
  `name`, `price`, `change_pct`, `subsector`
- `get_klse_all_sector_stocks() -> Dict[str, List[Dict]]` — all 13 sectors
  (13 requests, rate-limited)

## HTTP utilities (`http.py`)

- `fetch_url(url, cache_key) -> str` — rate-limited (2s min interval),
  cached 10 min in-process, 15s timeout
- `reset_rate_limit() -> None`
- `clear_cache() -> None`
