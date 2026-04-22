"""
Tests for new financial data functions.

These tests verify the new structured dict-based functions
that will replace the string-returning functions in v2.0.
"""

import pytest
from datetime import datetime

from klse_screener.financials import (
    get_klse_key_ratios,
    get_klse_quarterly_financials_dict,
    get_klse_annual_financials_dict,
    get_klse_fundamentals_mf_enhanced,
)
from klse_screener.price_history import (
    scrape_ohlcv_raw,
    get_klse_price_history,
)
from klse_screener.qr_announcements import (
    get_klse_daily_financial_reports,
    get_klse_announcements_by_ticker,
)


class TestGetKlseKeyRatios:
    """Test get_klse_key_ratios() function"""
    
    def test_valid_ticker(self):
        """Test with valid KLSE ticker"""
        result = get_klse_key_ratios("5132.KL")
        
        # Should return a dict
        assert isinstance(result, dict)
        
        # Should have data_source
        assert result.get("data_source") == "klsescreener_key_ratios"
        
        # Should have at least some ratios
        assert "pe_ratio" in result or "market_cap" in result
    
    def test_invalid_ticker(self):
        """Test with invalid ticker"""
        result = get_klse_key_ratios("INVALID")
        assert isinstance(result, dict)
        assert len(result) == 0
    
    def test_non_klse_ticker(self):
        """Test with non-KLSE ticker"""
        result = get_klse_key_ratios("0700.HK")
        assert isinstance(result, dict)
        assert len(result) == 0
    
    def test_returns_dict_not_string(self):
        """Verify return type is dict (not string like legacy functions)"""
        result = get_klse_key_ratios("5132.KL")
        assert isinstance(result, dict)
        # Dict should be structured data, not formatted text
        for key, value in result.items():
            # Values should be raw data, not formatted strings with newlines
            if isinstance(value, str):
                assert "\n" not in value


class TestGetKlseQuarterlyFinancialsDict:
    """Test get_klse_quarterly_financials_dict() function"""
    
    def test_valid_ticker(self):
        """Test with valid KLSE ticker"""
        result = get_klse_quarterly_financials_dict("5132.KL")
        
        assert isinstance(result, dict)
        assert result.get("data_source") == "klsescreener_quarterly"
        
        # Should have quarterly_data list
        assert "quarterly_data" in result
        assert isinstance(result["quarterly_data"], list)
        
        # Should have TTM fields
        assert "ttm_revenue" in result
        assert "ttm_net_profit" in result
        assert "ttm_eps" in result
    
    def test_ttm_calculation(self):
        """Verify TTM is calculated from quarterly data"""
        result = get_klse_quarterly_financials_dict("5132.KL")
        
        quarterly_data = result.get("quarterly_data", [])
        
        if len(quarterly_data) >= 4:
            # TTM should be calculated
            assert result["ttm_revenue"] is not None
            assert result["ttm_net_profit"] is not None
            assert result["ttm_eps"] is not None
    
    def test_returns_dict_not_string(self):
        """Verify return type is dict (not string like get_klse_quarterly_history)"""
        result = get_klse_quarterly_financials_dict("5132.KL")
        assert isinstance(result, dict)
        
        # Quarterly data should be list of dicts
        assert isinstance(result["quarterly_data"], list)
        if len(result["quarterly_data"]) > 0:
            assert isinstance(result["quarterly_data"][0], dict)


class TestGetKlseAnnualFinancialsDict:
    """Test get_klse_annual_financials_dict() function"""
    
    def test_valid_ticker(self):
        """Test with valid KLSE ticker"""
        result = get_klse_annual_financials_dict("5132.KL")
        
        assert isinstance(result, dict)
        assert result.get("data_source") == "klsescreener_annual"
        
        # Should have annual_data list
        assert "annual_data" in result
        assert isinstance(result["annual_data"], list)
    
    def test_returns_dict_not_string(self):
        """Verify return type is dict (not string like get_klse_annual)"""
        result = get_klse_annual_financials_dict("5132.KL")
        assert isinstance(result, dict)
        
        # Annual data should be list of dicts
        assert isinstance(result["annual_data"], list)
        if len(result["annual_data"]) > 0:
            assert isinstance(result["annual_data"][0], dict)


class TestGetKlseFundamentalsCombined:
    """Test get_klse_fundamentals_mf_enhanced() function"""
    
    def test_valid_ticker(self):
        """Test with valid KLSE ticker"""
        result = get_klse_fundamentals_mf_enhanced("5132.KL")
        
        assert isinstance(result, dict)
        assert result.get("data_source") == "klsescreener_mf_enhanced"
        
        # Should have key ratios
        assert "market_cap" in result
        assert "pe_ratio" in result
        assert "roe" in result
        
        # Should have TTM data
        assert "ttm_revenue" in result
        assert "ttm_net_profit" in result
        
        # Should have quarterly and annual data
        assert "quarterly_data" in result
        assert "annual_data" in result
        
        # Should have MF approximations
        assert "approx_ebit_ttm" in result
        assert "approx_fixed_assets" in result
    
    def test_combines_all_data(self):
        """Verify combined function returns data from all sources"""
        result_mf = get_klse_fundamentals_mf_enhanced("5132.KL")
        key_ratios = get_klse_key_ratios("5132.KL")
        quarterly = get_klse_quarterly_financials_dict("5132.KL")
        
        # Combined should have key ratios fields
        assert result_mf.get("pe_ratio") == key_ratios.get("pe_ratio")
        
        # Combined should have quarterly TTM fields
        assert result_mf.get("ttm_revenue") == quarterly.get("ttm_revenue")
    
    def test_alias_function(self):
        """Test get_klse_fundamentals() alias"""
        from klse_screener.financials import get_klse_fundamentals
        
        result = get_klse_fundamentals("5132.KL")
        result_mf = get_klse_fundamentals_mf_enhanced("5132.KL")
        
        # Should be identical
        assert result == result_mf


class TestScrapeOhlcvRaw:
    """Test scrape_ohlcv_raw() function"""
    
    def test_30day_history(self):
        """Test 30-day OHLCV data"""
        result = scrape_ohlcv_raw("5132.KL", period="30d")
        
        assert isinstance(result, list)
        
        if len(result) > 0:
            # Each item should be a dict with OHLCV fields
            item = result[0]
            assert isinstance(item, dict)
            assert "date" in item
            assert "open" in item
            assert "high" in item
            assert "low" in item
            assert "close" in item
            assert "volume" in item
    
    def test_10year_chart(self):
        """Test 10-year chart data"""
        result = scrape_ohlcv_raw("5132.KL", period="10y")
        
        assert isinstance(result, list)
        
        if len(result) > 0:
            # Each item should be a dict with OHLCV fields
            item = result[0]
            assert isinstance(item, dict)
            assert "date" in item
            assert "timestamp" in item
    
    def test_returns_list_not_dataframe(self):
        """Verify return type is list of dicts (not pandas DataFrame)"""
        result = scrape_ohlcv_raw("5132.KL", period="30d")
        
        assert isinstance(result, list)
        # Should NOT be a DataFrame
        try:
            import pandas as pd
            assert not isinstance(result, pd.DataFrame)
        except ImportError:
            pass  # pandas not installed, that's fine


class TestGetKlsePriceHistory:
    """Test get_klse_price_history() wrapper"""
    
    def test_with_metadata(self):
        """Test price history with metadata"""
        result = get_klse_price_history("5132.KL", period="30d")
        
        if result is not None:
            assert isinstance(result, dict)
            assert "symbol" in result
            assert "period" in result
            assert "data_source" in result
            assert "count" in result
            assert "data" in result
            assert isinstance(result["data"], list)


class TestGetKlseDailyFinancialReports:
    """Test get_klse_daily_financial_reports() function"""
    
    def test_market_wide_reports(self):
        """Test market-wide QR announcements"""
        result = get_klse_daily_financial_reports()
        
        assert isinstance(result, list)
        
        if len(result) > 0:
            # Each item should have required fields
            item = result[0]
            assert isinstance(item, dict)
            assert "ticker" in item
            assert "announced_date" in item
            assert "quarter" in item
            assert "quarter_end_date" in item
    
    def test_ticker_format(self):
        """Verify ticker format includes .KL suffix"""
        result = get_klse_daily_financial_reports()
        
        for item in result:
            ticker = item.get("ticker", "")
            assert ticker.endswith(".KL")


class TestGetKlseAnnouncementsByTicker:
    """Test get_klse_announcements_by_ticker() function"""
    
    def test_ticker_specific(self):
        """Test ticker-specific announcements"""
        result = get_klse_announcements_by_ticker("5132.KL", days_back=3)
        
        assert isinstance(result, list)
        
        # All results should be for the specified ticker
        for item in result:
            assert item.get("ticker") == "5132.KL"


class TestBackwardCompatibility:
    """Test that new dict functions are compatible with project usage"""
    
    def test_quarterly_has_ttm(self):
        """Verify quarterly function has TTM calculations (project requirement)"""
        result = get_klse_quarterly_financials_dict("5132.KL")
        
        # TTM fields must exist for project Magic Formula
        assert "ttm_revenue" in result
        assert "ttm_net_profit" in result
        assert "ttm_eps" in result
    
    def test_combined_has_mf_approximations(self):
        """Verify combined function has MF approximations (project requirement)"""
        result = get_klse_fundamentals_mf_enhanced("5132.KL")
        
        # MF approximation fields
        assert "approx_ebit_ttm" in result
        assert "approx_fixed_assets" in result
    
    def test_no_pandas_dependency(self):
        """Verify functions don't require pandas (library is pandas-free)"""
        try:
            import pandas as pd
            pandas_installed = True
        except ImportError:
            pandas_installed = False
        
        # Functions should work regardless
        result = get_klse_fundamentals_mf_enhanced("5132.KL")
        assert isinstance(result, dict)
        
        # Return type should be dict, not DataFrame
        assert not (pandas_installed and isinstance(result, pd.DataFrame))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
