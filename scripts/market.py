#!/usr/bin/env python3
"""Bursa Malaysia market overview.

Usage:
    python market.py

Prints KLSE indices, Bursa sector indices, and top active/turnover/
gainers/losers lists from klsescreener.com/v2/markets (15-min delayed).
"""

import sys

try:
    from klse_screener import get_bursa_market_data
except ImportError:
    sys.exit("klse-screener-py not installed. Run: pip install klse-screener-py")

_LIST_KEYS = (
    "klse_indices",
    "sector_indices",
    "top_active",
    "top_turnover",
    "top_gainers",
    "top_gainers_pct",
    "top_losers",
    "top_losers_pct",
)


def _pct(v) -> str:
    if v is None:
        return ""
    return f"{'+' if v > 0 else ''}{v}%"


def _arrow(trend) -> str:
    return {"up": "^", "down": "v"}.get(trend, "")


def _print_indices(rows: list, title: str) -> None:
    print(f"\n## {title}")
    if not rows:
        print("  (no data)")
    for r in rows:
        price = r.get("price")
        print(
            f"  {r.get('name', '?')!s:40s} "
            f"{price if price is not None else 'N/A':>10}  "
            f"{_pct(r.get('change_pct')):>8}  {_arrow(r.get('trend'))}"
        )


def _print_top(rows: list, title: str) -> None:
    print(f"\n## {title}")
    if not rows:
        print("  (no data)")
    for r in rows:
        extra = r.get("turnover") or r.get("volume") or ""
        price = r.get("price")
        print(
            f"  {r.get('rank', '?')!s:>2}. {r.get('code', '?')} "
            f"{str(r.get('name', '?'))[:30]:30s} "
            f"{price if price is not None else 'N/A':>8}  "
            f"{_pct(r.get('change_pct')):>8}  {extra}"
        )


def main() -> None:
    data = get_bursa_market_data()
    if not any(data.get(k) for k in _LIST_KEYS):
        print(f"Failed to fetch market data: {data.get('error', 'all sections empty')}")
        sys.exit(1)

    print(f"# Bursa Malaysia market — {data.get('scraped_at', 'n/a')}")
    _print_indices(data.get("klse_indices", []), "KLSE Indices")
    _print_indices(data.get("sector_indices", []), "Sector Indices")
    _print_top(data.get("top_active", []), "Top Active (volume)")
    _print_top(data.get("top_turnover", []), "Top Turnover")
    _print_top(data.get("top_gainers_pct", []), "Top Gainers %")
    _print_top(data.get("top_losers_pct", []), "Top Losers %")
    _print_top(data.get("top_gainers", []), "Top Gainers (absolute)")
    _print_top(data.get("top_losers", []), "Top Losers (absolute)")


if __name__ == "__main__":
    main()
