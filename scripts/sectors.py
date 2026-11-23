#!/usr/bin/env python3
"""KLSE sector mapping and sector constituents.

Usage:
    python sectors.py              # list all sector codes
    python sectors.py 0001I        # stocks in one sector

Sector codes: 0001I 0002I 0003I 0005I 0010I 0020I 0025I 0050I
              0061I 0062I 0063I 0064I 0065I
"""

import sys

try:
    from klse_screener import get_klse_sector_info, get_klse_sector_stocks
except ImportError:
    sys.exit("klse-screener-py not installed. Run: pip install klse-screener-py")


def main() -> None:
    if len(sys.argv) < 2:
        print("KLSE sectors:")
        for code, info in get_klse_sector_info().items():
            print(f"  {code}  {info['name']}")
        print("\nUsage: sectors.py <sector_code>")
        return

    code = sys.argv[1].upper()
    stocks = get_klse_sector_stocks(code)
    if not stocks:
        print(f"No stocks found for sector {code} (check the code, or sector page layout)")
        sys.exit(1)

    name = get_klse_sector_info().get(code, {}).get("name", code)
    print(f"\n# {name} ({code}) — {len(stocks)} stocks")
    print(f"  {'code':>7s} {'symbol':>8s} {'price':>8s} {'chg%':>8s}  name")
    for s in stocks:
        chg = s.get("change_pct")
        chg_s = ""
        if chg is not None:
            try:
                chg_s = f"{float(chg):+.2f}"
            except (TypeError, ValueError):
                chg_s = str(chg)
        sub = f"  [{s['subsector']}]" if s.get("subsector") else ""
        print(
            f"  {s.get('code', '?'):>7s} {s.get('symbol', '?'):>8s} "
            f"{s.get('price') or 'N/A'!s:>8s} {chg_s:>8s}  {s.get('name', '?')}{sub}"
        )


if __name__ == "__main__":
    main()
