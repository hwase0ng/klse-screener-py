#!/usr/bin/env python3
"""KLSE OHLCV price history.

Usage:
    python price.py TICKER [30d|10y]

Examples:
    python price.py 5132.KL
    python price.py 0012.KL 10y
"""

import sys

try:
    from klse_screener import get_klse_price_history
except ImportError:
    sys.exit("klse-screener-py not installed. Run: pip install klse-screener-py")


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    ticker = sys.argv[1].upper()
    period = sys.argv[2] if len(sys.argv) > 2 else "30d"
    if period not in ("30d", "10y"):
        sys.exit("period must be '30d' or '10y'")

    result = get_klse_price_history(ticker, period)
    if not result:
        print(f"No price history for {ticker} ({period})")
        sys.exit(1)

    rows = result["data"]
    has_adj = any("adjusted_close" in r for r in rows)
    cols = ["date", "open", "high", "low", "close", "volume"]
    if has_adj:
        cols.append("adjusted_close")

    print(f"\n# {ticker} — {period} ({result['count']} bars)")
    print("  " + " ".join(f"{c:>13s}" for c in cols))
    for r in rows:
        print("  " + " ".join(f"{str(r.get(c, ''))[:13]:>13s}" for c in cols))


if __name__ == "__main__":
    main()
