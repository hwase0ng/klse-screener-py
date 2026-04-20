"""Tests for market-wide KLSE functions."""

import pytest
from klse_screener import (
    get_klse_dividend_calendar,
    get_klse_corporate_actions,
    get_klse_announcements_by_category,
    get_klse_dividend_announcements,
    get_klse_insider_dealings,
    get_klse_financial_results,
    get_klse_share_buybacks,
    get_klse_financial_reports,
    get_klse_market_announcements,
)


class TestDividendCalendar:
    """Test get_klse_dividend_calendar function."""

    @pytest.mark.live
    def test_dividend_calendar_returns_list(self):
        """Should return a list."""
        result = get_klse_dividend_calendar(limit=10)
        assert isinstance(result, list)

    @pytest.mark.live
    def test_dividend_calendar_has_entries(self):
        """Should have dividend entries with required fields."""
        result = get_klse_dividend_calendar(limit=10)
        if result:  # May be empty if no dividends
            entry = result[0]
            assert "ticker" in entry
            assert "ex_date" in entry
            assert "amount" in entry

    @pytest.mark.live
    def test_dividend_calendar_limit(self):
        """Should respect limit parameter."""
        result = get_klse_dividend_calendar(limit=5)
        assert len(result) <= 5


class TestCorporateActions:
    """Test get_klse_corporate_actions function."""

    @pytest.mark.live
    def test_corporate_actions_returns_list(self):
        """Should return a list."""
        result = get_klse_corporate_actions(limit=10)
        assert isinstance(result, list)

    @pytest.mark.live
    def test_corporate_actions_has_entries(self):
        """Should have entries with required fields."""
        result = get_klse_corporate_actions(limit=10)
        if result:
            entry = result[0]
            assert "ticker" in entry
            assert "action_type" in entry
            assert "ex_date" in entry


class TestAnnouncementsByCategory:
    """Test get_klse_announcements_by_category function."""

    @pytest.mark.live
    @pytest.mark.parametrize("category", ["EA", "SH", "FA", "SB"])
    def test_announcements_by_category(self, category):
        """Should return announcements for each category."""
        result = get_klse_announcements_by_category(category, limit=10)
        assert isinstance(result, list)
        # All entries should have the correct category
        for entry in result:
            assert entry.get("category") == category

    @pytest.mark.live
    def test_announcements_with_ticker(self):
        """Should filter by ticker when provided."""
        result = get_klse_announcements_by_category("EA", ticker="5132.KL", limit=10)
        assert isinstance(result, list)


class TestConvenienceWrappers:
    """Test convenience wrapper functions."""

    TICKER = "5132.KL"  # Deleum Berhad - active stock

    @pytest.mark.live
    def test_dividend_announcements(self):
        """Should return EA category announcements."""
        result = get_klse_dividend_announcements(self.TICKER, limit=10)
        assert isinstance(result, list)

    @pytest.mark.live
    def test_insider_dealings(self):
        """Should return SH category announcements."""
        result = get_klse_insider_dealings(self.TICKER, limit=10)
        assert isinstance(result, list)

    @pytest.mark.live
    def test_financial_results(self):
        """Should return FA category announcements."""
        result = get_klse_financial_results(self.TICKER, limit=10)
        assert isinstance(result, list)

    @pytest.mark.live
    def test_share_buybacks(self):
        """Should return SB category announcements."""
        result = get_klse_share_buybacks(self.TICKER, limit=10)
        assert isinstance(result, list)


class TestFinancialReports:
    """Test get_klse_financial_reports function."""

    @pytest.mark.live
    def test_financial_reports_returns_list(self):
        """Should return a list."""
        result = get_klse_financial_reports(ticker="5132.KL", limit=10)
        assert isinstance(result, list)

    @pytest.mark.live
    def test_financial_reports_has_entries(self):
        """Should have entries with required fields."""
        result = get_klse_financial_reports(ticker="5132.KL", limit=10)
        if result:
            entry = result[0]
            assert "ticker" in entry
            assert "fiscal_period" in entry
            assert "filing_date" in entry


class TestMarketAnnouncements:
    """Test get_klse_market_announcements function."""

    @pytest.mark.live
    def test_market_announcements_returns_list(self):
        """Should return a list."""
        result = get_klse_market_announcements(limit=10)
        assert isinstance(result, list)

    @pytest.mark.live
    def test_market_announcements_with_category(self):
        """Should filter by category when provided."""
        result = get_klse_market_announcements(category="EA", limit=10)
        assert isinstance(result, list)


# Non-live tests (no API access required)

class TestInvalidCategory:
    """Test invalid category handling."""

    def test_invalid_category_returns_empty(self):
        """Should return empty list for invalid category."""
        result = get_klse_announcements_by_category("INVALID", limit=10)
        assert result == []
