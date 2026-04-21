"""Tests for core.py *_raw() functions and deprecation warnings."""

import warnings
import pytest
from klse_screener import (
    get_klse_news_raw,
    get_klse_announcements_raw,
    get_klse_dividends_raw,
    get_klse_capital_changes_raw,
    get_klse_warrants_raw,
    get_klse_shareholding_changes_raw,
    get_klse_market_sentiment_raw,
    get_klse_news,
    get_klse_announcements,
    get_klse_dividends,
    get_klse_capital_changes,
    get_klse_warrants,
    get_klse_shareholding_changes,
    get_klse_market_sentiment,
)


class TestGetKlseNewsRaw:
    """Tests for get_klse_news_raw()."""

    def test_valid_ticker_returns_list(self):
        """Test with valid KLSE ticker returns list."""
        result = get_klse_news_raw("5132.KL", limit=5)
        assert isinstance(result, list)

    def test_valid_ticker_items_have_required_keys(self):
        """Test that news items have required keys."""
        result = get_klse_news_raw("5132.KL", limit=3)
        if result:
            for item in result:
                assert "title" in item
                assert "url" in item

    def test_invalid_ticker_returns_empty_list(self):
        """Test with non-KLSE ticker returns empty list."""
        result = get_klse_news_raw("AAPL", limit=5)
        assert result == []

    def test_limit_parameter(self):
        """Test that limit parameter works."""
        result = get_klse_news_raw("5132.KL", limit=2)
        assert len(result) <= 2

    def test_return_type(self):
        """Test return type is List[Dict]."""
        result = get_klse_news_raw("5132.KL", limit=5)
        assert isinstance(result, list)
        if result:
            assert isinstance(result[0], dict)


class TestGetKlseAnnouncementsRaw:
    """Tests for get_klse_announcements_raw()."""

    def test_valid_ticker_returns_list(self):
        """Test with valid KLSE ticker returns list."""
        result = get_klse_announcements_raw("5132.KL", limit=5)
        assert isinstance(result, list)

    def test_valid_ticker_items_have_required_keys(self):
        """Test that announcement items have required keys."""
        result = get_klse_announcements_raw("5132.KL", limit=3)
        if result:
            for item in result:
                assert "title" in item
                assert "url" in item
                assert "date" in item

    def test_invalid_ticker_returns_empty_list(self):
        """Test with non-KLSE ticker returns empty list."""
        result = get_klse_announcements_raw("AAPL", limit=5)
        assert result == []

    def test_limit_parameter(self):
        """Test that limit parameter works."""
        result = get_klse_announcements_raw("5132.KL", limit=2)
        assert len(result) <= 2

    def test_return_type(self):
        """Test return type is List[Dict]."""
        result = get_klse_announcements_raw("5132.KL", limit=5)
        assert isinstance(result, list)
        if result:
            assert isinstance(result[0], dict)


class TestGetKlseDividendsRaw:
    """Tests for get_klse_dividends_raw()."""

    def test_valid_ticker_returns_list(self):
        """Test with valid KLSE ticker returns list."""
        result = get_klse_dividends_raw("5132.KL", limit=5)
        assert isinstance(result, list)

    def test_valid_ticker_items_have_required_keys(self):
        """Test that dividend items have required keys."""
        result = get_klse_dividends_raw("5132.KL", limit=3)
        if result:
            for item in result:
                assert "ex_date" in item
                assert "payment_date" in item
                assert "dividend_amount" in item

    def test_invalid_ticker_returns_empty_list(self):
        """Test with non-KLSE ticker returns empty list."""
        result = get_klse_dividends_raw("AAPL", limit=5)
        assert result == []

    def test_limit_parameter(self):
        """Test that limit parameter works."""
        result = get_klse_dividends_raw("5132.KL", limit=2)
        assert len(result) <= 2

    def test_return_type(self):
        """Test return type is List[Dict]."""
        result = get_klse_dividends_raw("5132.KL", limit=5)
        assert isinstance(result, list)
        if result:
            assert isinstance(result[0], dict)


class TestGetKlseCapitalChangesRaw:
    """Tests for get_klse_capital_changes_raw()."""

    def test_valid_ticker_returns_list(self):
        """Test with valid KLSE ticker returns list."""
        result = get_klse_capital_changes_raw("5132.KL", limit=5)
        assert isinstance(result, list)

    def test_valid_ticker_items_have_required_keys(self):
        """Test that capital change items have required keys."""
        result = get_klse_capital_changes_raw("5132.KL", limit=3)
        if result:
            for item in result:
                assert "ex_date" in item
                assert "description" in item

    def test_invalid_ticker_returns_empty_list(self):
        """Test with non-KLSE ticker returns empty list."""
        result = get_klse_capital_changes_raw("AAPL", limit=5)
        assert result == []

    def test_limit_parameter(self):
        """Test that limit parameter works."""
        result = get_klse_capital_changes_raw("5132.KL", limit=2)
        assert len(result) <= 2

    def test_return_type(self):
        """Test return type is List[Dict]."""
        result = get_klse_capital_changes_raw("5132.KL", limit=5)
        assert isinstance(result, list)
        if result:
            assert isinstance(result[0], dict)


class TestGetKlseWarrantsRaw:
    """Tests for get_klse_warrants_raw()."""

    def test_valid_ticker_returns_list(self):
        """Test with valid KLSE ticker returns list."""
        result = get_klse_warrants_raw("5132.KL", limit=5)
        assert isinstance(result, list)

    def test_valid_ticker_items_have_required_keys(self):
        """Test that warrant items have required keys."""
        result = get_klse_warrants_raw("5132.KL", limit=3)
        if result:
            for item in result:
                assert "name" in item
                assert "last_price" in item
                assert "volume" in item

    def test_invalid_ticker_returns_empty_list(self):
        """Test with non-KLSE ticker returns empty list."""
        result = get_klse_warrants_raw("AAPL", limit=5)
        assert result == []

    def test_limit_parameter(self):
        """Test that limit parameter works."""
        result = get_klse_warrants_raw("5132.KL", limit=2)
        assert len(result) <= 2

    def test_return_type(self):
        """Test return type is List[Dict]."""
        result = get_klse_warrants_raw("5132.KL", limit=5)
        assert isinstance(result, list)
        if result:
            assert isinstance(result[0], dict)


class TestGetKlseShareholdingChangesRaw:
    """Tests for get_klse_shareholding_changes_raw()."""

    def test_valid_ticker_returns_list(self):
        """Test with valid KLSE ticker returns list."""
        result = get_klse_shareholding_changes_raw("5132.KL", limit=10)
        assert isinstance(result, list)

    def test_valid_ticker_items_have_required_keys(self):
        """Test that shareholding change items have required keys."""
        result = get_klse_shareholding_changes_raw("5132.KL", limit=5)
        if result:
            for item in result:
                assert "name" in item
                assert "shares" in item
                assert "transaction_type" in item

    def test_invalid_ticker_returns_empty_list(self):
        """Test with non-KLSE ticker returns empty list."""
        result = get_klse_shareholding_changes_raw("AAPL", limit=10)
        assert result == []

    def test_limit_parameter(self):
        """Test that limit parameter works."""
        result = get_klse_shareholding_changes_raw("5132.KL", limit=5)
        assert len(result) <= 5

    def test_return_type(self):
        """Test return type is List[Dict]."""
        result = get_klse_shareholding_changes_raw("5132.KL", limit=10)
        assert isinstance(result, list)
        if result:
            assert isinstance(result[0], dict)


class TestGetKlseMarketSentimentRaw:
    """Tests for get_klse_market_sentiment_raw()."""

    def test_returns_dict(self):
        """Test that market sentiment returns dict."""
        result = get_klse_market_sentiment_raw()
        assert isinstance(result, dict)

    def test_dict_has_required_keys(self):
        """Test that result has required keys."""
        result = get_klse_market_sentiment_raw()
        assert "market_updates" in result or "note" in result or "error" in result

    def test_return_type(self):
        """Test return type is Dict."""
        result = get_klse_market_sentiment_raw()
        assert isinstance(result, dict)


class TestDeprecationWarnings:
    """Tests for deprecation warnings on wrapper functions."""

    def test_get_klse_news_deprecation_warning(self):
        """Test that get_klse_news() raises DeprecationWarning."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            get_klse_news("5132.KL", limit=5)
            assert len(w) >= 1
            assert any(issubclass(warning.category, DeprecationWarning) for warning in w)
            assert any("deprecated" in str(warning.message).lower() for warning in w)

    def test_get_klse_announcements_deprecation_warning(self):
        """Test that get_klse_announcements() raises DeprecationWarning."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            get_klse_announcements("5132.KL", limit=5)
            assert len(w) >= 1
            assert any(issubclass(warning.category, DeprecationWarning) for warning in w)
            assert any("deprecated" in str(warning.message).lower() for warning in w)

    def test_get_klse_dividends_deprecation_warning(self):
        """Test that get_klse_dividends() raises DeprecationWarning."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            get_klse_dividends("5132.KL", limit=5)
            assert len(w) >= 1
            assert any(issubclass(warning.category, DeprecationWarning) for warning in w)
            assert any("deprecated" in str(warning.message).lower() for warning in w)

    def test_get_klse_capital_changes_deprecation_warning(self):
        """Test that get_klse_capital_changes() raises DeprecationWarning."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            get_klse_capital_changes("5132.KL", limit=5)
            assert len(w) >= 1
            assert any(issubclass(warning.category, DeprecationWarning) for warning in w)
            assert any("deprecated" in str(warning.message).lower() for warning in w)

    def test_get_klse_warrants_deprecation_warning(self):
        """Test that get_klse_warrants() raises DeprecationWarning."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            get_klse_warrants("5132.KL", limit=5)
            assert len(w) >= 1
            assert any(issubclass(warning.category, DeprecationWarning) for warning in w)
            assert any("deprecated" in str(warning.message).lower() for warning in w)

    def test_get_klse_shareholding_changes_deprecation_warning(self):
        """Test that get_klse_shareholding_changes() raises DeprecationWarning."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            get_klse_shareholding_changes("5132.KL", limit=5)
            assert len(w) >= 1
            assert any(issubclass(warning.category, DeprecationWarning) for warning in w)
            assert any("deprecated" in str(warning.message).lower() for warning in w)

    def test_get_klse_market_sentiment_deprecation_warning(self):
        """Test that get_klse_market_sentiment() raises DeprecationWarning."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            get_klse_market_sentiment()
            assert len(w) >= 1
            assert any(issubclass(warning.category, DeprecationWarning) for warning in w)
            assert any("deprecated" in str(warning.message).lower() for warning in w)


class TestInvalidTicker:
    """Tests for invalid ticker handling."""

    def test_news_invalid_ticker(self):
        """Test news with invalid ticker."""
        result = get_klse_news_raw("INVALID", limit=5)
        assert result == []

    def test_announcements_invalid_ticker(self):
        """Test announcements with invalid ticker."""
        result = get_klse_announcements_raw("INVALID", limit=5)
        assert result == []

    def test_dividends_invalid_ticker(self):
        """Test dividends with invalid ticker."""
        result = get_klse_dividends_raw("INVALID", limit=5)
        assert result == []

    def test_capital_changes_invalid_ticker(self):
        """Test capital changes with invalid ticker."""
        result = get_klse_capital_changes_raw("INVALID", limit=5)
        assert result == []

    def test_warrants_invalid_ticker(self):
        """Test warrants with invalid ticker."""
        result = get_klse_warrants_raw("INVALID", limit=5)
        assert result == []

    def test_shareholding_changes_invalid_ticker(self):
        """Test shareholding changes with invalid ticker."""
        result = get_klse_shareholding_changes_raw("INVALID", limit=5)
        assert result == []
