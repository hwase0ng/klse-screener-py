"""Tests for KLSE Screener core functions."""

import pytest
from klse_screener import (
    get_klse_fundamentals,
    get_klse_news,
    get_klse_announcements,
    get_klse_trade_summary,
    get_klse_comments,
    is_klse,
)


# Test tickers
KLSE_TICKER = "5132.KL"  # Deleum Berhad - active stock
HKSE_TICKER = "0700.HK"  # Tencent - not KLSE
INVALID_TICKER = "INVALID"


class TestMarketDetection:
    """Test that non-KLSE tickers return empty results."""

    def test_fundamentals_non_klse(self):
        """Return empty dict for non-KLSE."""
        result = get_klse_fundamentals(HKSE_TICKER)
        assert result == {}

    def test_news_non_klse(self):
        """Return empty string for non-KLSE."""
        result = get_klse_news(HKSE_TICKER)
        assert result == ""

    def test_trade_summary_non_klse(self):
        """Return empty dict for non-KLSE."""
        result = get_klse_trade_summary(HKSE_TICKER)
        assert result == {}

    def test_comments_non_klse(self):
        """Return empty list for non-KLSE."""
        result = get_klse_comments(HKSE_TICKER)
        assert result == []


class TestGetKlseFundamentals:
    """Test get_klse_fundamentals function."""

    @pytest.mark.skip(reason="Requires live API access")
    def test_fundamentals_structure(self):
        """Verify response structure."""
        result = get_klse_fundamentals(KLSE_TICKER)
        assert isinstance(result, dict)
        assert "data_source" in result
        assert result["data_source"] == "klsescreener"

    @pytest.mark.skip(reason="Requires live API access")
    def test_fundamentals_has_fields(self):
        """Verify expected fields present."""
        result = get_klse_fundamentals(KLSE_TICKER)
        expected_fields = ["pe_ratio", "eps", "dividend_yield", "market_cap"]
        for field in expected_fields:
            assert field in result or "error" in result


class TestGetKlseNews:
    """Test get_klse_news function."""

    @pytest.mark.skip(reason="Requires live API access")
    def test_news_format(self):
        """Verify news format."""
        result = get_klse_news(KLSE_TICKER, limit=5)
        assert isinstance(result, str)
        if result:  # May be empty if no news
            assert "## KLSE Screener News" in result
            assert result.count("- ") <= 5


class TestGetKlseAnnouncements:
    """Test get_klse_announcements function."""

    @pytest.mark.skip(reason="Requires live API access")
    def test_announcements_format(self):
        """Verify announcements format."""
        result = get_klse_announcements(KLSE_TICKER, limit=5)
        assert isinstance(result, str)
        if result:
            assert "## Bursa Malaysia Announcements" in result


class TestGetKlseTradeSummary:
    """Test get_klse_trade_summary function."""

    @pytest.mark.skip(reason="Requires live API access")
    def test_trade_summary_structure(self):
        """Verify trade summary structure."""
        result = get_klse_trade_summary(KLSE_TICKER)
        assert isinstance(result, dict)
        if result and "error" not in result:
            assert "current_price" in result
            assert "bid_levels" in result
            assert "ask_levels" in result


class TestGetKlseComments:
    """Test get_klse_comments function."""

    @pytest.mark.skip(reason="Requires live API access")
    def test_comments_structure(self):
        """Verify comments structure."""
        result = get_klse_comments(KLSE_TICKER, limit=10)
        assert isinstance(result, list)
        if result:
            comment = result[0]
            assert "comment_id" in comment
            assert "username" in comment
            assert "comment_text" in comment


class TestFormattedWrappers:
    """Test formatted wrapper functions."""

    @pytest.mark.skip(reason="Requires live API access")
    def test_trade_summary_formatted(self):
        """Verify formatted trade summary."""
        from klse_screener import get_klse_trade_summary_formatted

        result = get_klse_trade_summary_formatted(KLSE_TICKER)
        assert isinstance(result, str)
        if result:
            assert "## KLSE Order Book Summary" in result

    @pytest.mark.skip(reason="Requires live API access")
    def test_comments_formatted(self):
        """Verify formatted comments."""
        from klse_screener import get_klse_comments_formatted

        result = get_klse_comments_formatted(KLSE_TICKER, limit=10)
        assert isinstance(result, str)
        if result:
            assert "## KLSE Stock Discussions" in result
            assert "Sentiment Overview" in result
