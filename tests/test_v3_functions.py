"""
Test suite for klse-screener-py v3.0.0

Tests only the non-deprecated functions.
All deprecated functions have been removed.
"""

import pytest
from klse_screener import (
    get_klse_news_raw,
    get_klse_announcements_raw,
    get_klse_dividends_raw,
    get_klse_capital_changes_raw,
    get_klse_warrants_raw,
    get_klse_shareholding_changes_raw,
)


class TestV3CoreFunctions:
    """Test all core functions available in v3.0.0"""
    
    def test_news_raw_returns_list(self):
        """get_klse_news_raw returns list of dicts"""
        result = get_klse_news_raw("5132.KL", limit=5)
        assert isinstance(result, list)
        assert len(result) <= 5
        if result:
            assert "title" in result[0]
            assert "url" in result[0]
    
    def test_announcements_raw_returns_list(self):
        """get_klse_announcements_raw returns list of dicts"""
        result = get_klse_announcements_raw("5132.KL", limit=5)
        assert isinstance(result, list)
        if result:
            assert "title" in result[0] or "announcement_type" in result[0]
    
    def test_dividends_raw_returns_list(self):
        """get_klse_dividends_raw returns list of dicts"""
        result = get_klse_dividends_raw("5132.KL", limit=5)
        assert isinstance(result, list)
        if result:
            assert "dividend_amount" in result[0] or "amount" in result[0]
    
    def test_capital_changes_raw_returns_list(self):
        """get_klse_capital_changes_raw returns list of dicts"""
        result = get_klse_capital_changes_raw("5132.KL", limit=5)
        assert isinstance(result, list)
    
    def test_warrants_raw_returns_list(self):
        """get_klse_warrants_raw returns list of dicts"""
        result = get_klse_warrants_raw("5132.KL", limit=5)
        assert isinstance(result, list)
    
    def test_shareholding_changes_raw_returns_list(self):
        """get_klse_shareholding_changes_raw returns list of dicts"""
        result = get_klse_shareholding_changes_raw("5132.KL", limit=5)
        assert isinstance(result, list)
    
    def test_invalid_ticker_returns_empty(self):
        """Invalid ticker returns empty list"""
        result = get_klse_news_raw("INVALID")
        assert result == []
