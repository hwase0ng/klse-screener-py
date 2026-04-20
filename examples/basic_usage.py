"""Example: Basic usage of klse-screener-py."""

from klse_screener import (
    get_klse_fundamentals,
    get_klse_news,
    get_klse_trade_summary,
    get_klse_comments_formatted,
)


def main():
    """Demonstrate basic usage."""
    ticker = "5132.KL"  # Deleum Berhad

    print(f"=== {ticker} ===\n")

    # Fundamentals
    print("## Fundamentals")
    fundamentals = get_klse_fundamentals(ticker)
    if fundamentals and "error" not in fundamentals:
        print(f"  Name: {fundamentals.get('name', 'N/A')}")
        print(f"  Sector: {fundamentals.get('sector', 'N/A')}")
        print(f"  P/E: {fundamentals.get('pe_ratio', 'N/A')}")
        print(f"  Dividend Yield: {fundamentals.get('dividend_yield', 'N/A')}")
        print(f"  Market Cap: {fundamentals.get('market_cap', 'N/A')}")
    else:
        print("  No data available")
    print()

    # News
    print("## News")
    news = get_klse_news(ticker, limit=5)
    print(news if news else "  No recent news")
    print()

    # Order Book
    print("## Order Book")
    summary = get_klse_trade_summary(ticker)
    if summary and "error" not in summary:
        print(f"  Current Price: RM{summary.get('current_price', 0):.3f}")
        print(f"  Bid Volume: {summary.get('total_bid_volume', 0):,}")
        print(f"  Ask Volume: {summary.get('total_ask_volume', 0):,}")
    else:
        print("  No order book data available")
    print()

    # Comments Sentiment
    print("## Retail Sentiment")
    comments = get_klse_comments_formatted(ticker, limit=30)
    print(comments if comments else "  No comments available")


if __name__ == "__main__":
    main()
