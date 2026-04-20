"""Tests for market detection utility."""

import pytest
from klse_screener.market import Market, detect_market, is_klse, is_hkse


class TestDetectMarket:
    """Test market detection from ticker format."""

    def test_klse_ticker(self):
        """Detect KLSE tickers."""
        assert detect_market("5132.KL") == Market.KLSE
        assert detect_market("7152.KL") == Market.KLSE
        assert detect_market("9172.KL") == Market.KLSE
        assert detect_market("1155.KL") == Market.KLSE

    def test_klse_ticker_lowercase(self):
        """Detect KLSE tickers (lowercase)."""
        assert detect_market("5132.kl") == Market.KLSE
        assert detect_market("7152.kl") == Market.KLSE

    def test_klse_ticker_whitespace(self):
        """Detect KLSE tickers with whitespace."""
        assert detect_market("  5132.KL  ") == Market.KLSE

    def test_hkse_ticker(self):
        """Detect HKSE tickers."""
        assert detect_market("0700.HK") == Market.HKSE
        assert detect_market("9868.HK") == Market.HKSE
        assert detect_market("1066.HK") == Market.HKSE

    def test_invalid_ticker_no_suffix(self):
        """Reject tickers without suffix."""
        assert detect_market("5132") == Market.UNKNOWN
        assert detect_market("9868") == Market.UNKNOWN

    def test_invalid_ticker_prefix(self):
        """Reject tickers with prefix format."""
        assert detect_market("KL.5132") == Market.UNKNOWN
        assert detect_market("HK.9868") == Market.UNKNOWN

    def test_invalid_ticker_a_share(self):
        """Reject A-share tickers."""
        assert detect_market("600519") == Market.UNKNOWN
        assert detect_market("000001") == Market.UNKNOWN

    def test_invalid_ticker_empty(self):
        """Reject empty ticker."""
        assert detect_market("") == Market.UNKNOWN
        assert detect_market("  ") == Market.UNKNOWN


class TestIsKlse:
    """Test is_klse helper function."""

    def test_klse_true(self):
        """Return True for KLSE tickers."""
        assert is_klse("5132.KL") is True
        assert is_klse("7152.KL") is True

    def test_klse_false(self):
        """Return False for non-KLSE tickers."""
        assert is_klse("0700.HK") is False
        assert is_klse("AAPL") is False
        assert is_klse("5132") is False


class TestIsHkse:
    """Test is_hkse helper function."""

    def test_hkse_true(self):
        """Return True for HKSE tickers."""
        assert is_hkse("0700.HK") is True
        assert is_hkse("9868.HK") is True

    def test_hkse_false(self):
        """Return False for non-HKSE tickers."""
        assert is_hkse("5132.KL") is False
        assert is_hkse("AAPL") is False
