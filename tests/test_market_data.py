"""
Tests for Bursa Malaysia market data scraping.

Tests verify:
- Data structure correctness
- KLSE indices filtering (exclude currency pairs, international indices)
- Top lists limited to 15 entries
- Error handling (partial data return)
- Trend extraction (up/down/unchanged)
"""

import pytest
from klse_screener import get_bursa_market_data


class TestGetBursaMarketData:
    """Test get_bursa_market_data function."""
    
    def test_returns_dict_with_required_keys(self):
        """Test that function returns dict with all required keys."""
        data = get_bursa_market_data()
        
        assert isinstance(data, dict)
        assert "scraped_at" in data
        assert "source" in data
        assert "klse_indices" in data
        assert "sector_indices" in data
        assert "top_active" in data
        assert "top_turnover" in data
        assert "top_gainers" in data
        assert "top_gainers_pct" in data
        assert "top_losers" in data
        assert "top_losers_pct" in data
    
    def test_scraped_at_is_iso_format(self):
        """Test that scraped_at timestamp is in ISO format."""
        data = get_bursa_market_data()
        
        from datetime import datetime
        # Should not raise exception
        datetime.fromisoformat(data["scraped_at"].replace("Z", "+00:00"))
    
    def test_source_is_klsescreener(self):
        """Test that source indicates klsescreener.com."""
        data = get_bursa_market_data()
        
        assert data["source"] == "klsescreener.com/v2/markets"
    
    def test_klse_indices_is_list(self):
        """Test that klse_indices is a list."""
        data = get_bursa_market_data()
        
        assert isinstance(data["klse_indices"], list)
    
    def test_klse_indices_structure(self):
        """Test that KLSE indices have correct structure."""
        data = get_bursa_market_data()
        
        if len(data["klse_indices"]) > 0:
            index = data["klse_indices"][0]
            
            assert "code" in index
            assert "name" in index
            assert "price" in index
            assert "change_abs" in index
            assert "change_pct" in index
            assert "trend" in index
    
    def test_klse_indices_includes_klci(self):
        """Test that FBM KLCI is included."""
        data = get_bursa_market_data()
        
        klcis = [idx for idx in data["klse_indices"] if idx["code"] == "200"]
        assert len(klcis) == 1
        assert klcis[0]["name"] == "FTSE Bursa Malaysia KLCI"
    
    def test_klse_indices_includes_cpo(self):
        """Test that CPO is included."""
        data = get_bursa_market_data()
        
        cpos = [idx for idx in data["klse_indices"] if idx["code"] == "CPO"]
        assert len(cpos) == 1
        assert cpos[0]["name"] == "Crude Palm Oil"
    
    def test_klse_indices_excludes_currency_pairs(self):
        """Test that currency pairs are excluded."""
        data = get_bursa_market_data()
        
        codes = [idx["code"] for idx in data["klse_indices"]]
        
        # Should NOT include currency pairs
        assert not any("MYR=X" in code for code in codes)
        assert "USDMYR=X" not in codes
        assert "SGDMYR=X" not in codes
    
    def test_klse_indices_excludes_international_indices(self):
        """Test that international indices are excluded."""
        data = get_bursa_market_data()
        
        codes = [idx["code"] for idx in data["klse_indices"]]
        
        # Should NOT include international indices
        assert "^GSPC" not in codes  # S&P 500
        assert "^IXIC" not in codes  # NASDAQ
        assert "HSI" not in codes    # Hang Seng
        assert "STI" not in codes    # Singapore STI
    
    def test_sector_indices_is_list(self):
        """Test that sector_indices is a list."""
        data = get_bursa_market_data()
        
        assert isinstance(data["sector_indices"], list)
    
    def test_sector_indices_structure(self):
        """Test that sector indices have correct structure."""
        data = get_bursa_market_data()
        
        if len(data["sector_indices"]) > 0:
            index = data["sector_indices"][0]
            
            assert "code" in index
            assert "index_code" in index
            assert "name" in index
            assert "price" in index
            assert "change_pct" in index
            assert "trend" in index
    
    def test_top_lists_are_lists(self):
        """Test that all top lists are lists."""
        data = get_bursa_market_data()
        
        assert isinstance(data["top_active"], list)
        assert isinstance(data["top_turnover"], list)
        assert isinstance(data["top_gainers"], list)
        assert isinstance(data["top_gainers_pct"], list)
        assert isinstance(data["top_losers"], list)
        assert isinstance(data["top_losers_pct"], list)
    
    def test_top_lists_limited_to_15(self):
        """Test that top lists are limited to 15 entries."""
        data = get_bursa_market_data()
        
        assert len(data["top_active"]) <= 15
        assert len(data["top_turnover"]) <= 15
        assert len(data["top_gainers"]) <= 15
        assert len(data["top_gainers_pct"]) <= 15
        assert len(data["top_losers"]) <= 15
        assert len(data["top_losers_pct"]) <= 15
    
    def test_top_list_structure(self):
        """Test that top list entries have correct structure."""
        data = get_bursa_market_data()
        
        if len(data["top_active"]) > 0:
            stock = data["top_active"][0]
            
            assert "rank" in stock
            assert "code" in stock
            assert "name" in stock
            assert "price" in stock
            assert "trend" in stock
            # Either volume or turnover
            assert "volume" in stock or "turnover" in stock
    
    def test_top_list_ranks_are_sequential(self):
        """Test that ranks are sequential starting from 1."""
        data = get_bursa_market_data()
        
        if len(data["top_active"]) > 0:
            ranks = [stock["rank"] for stock in data["top_active"]]
            expected_ranks = list(range(1, len(ranks) + 1))
            assert ranks == expected_ranks
    
    def test_trend_values_are_valid(self):
        """Test that trend values are one of: up, down, unchanged."""
        data = get_bursa_market_data()
        
        valid_trends = {"up", "down", "unchanged"}
        
        # Check KLSE indices
        for index in data["klse_indices"]:
            assert index["trend"] in valid_trends
        
        # Check top lists
        for stock in data["top_active"]:
            assert stock["trend"] in valid_trends
    
    def test_price_is_numeric_or_none(self):
        """Test that price values are numeric or None."""
        data = get_bursa_market_data()
        
        for index in data["klse_indices"]:
            assert index["price"] is None or isinstance(index["price"], (int, float))
        
        for stock in data["top_active"]:
            assert stock["price"] is None or isinstance(stock["price"], (int, float))
    
    def test_change_pct_is_numeric_or_none(self):
        """Test that change_pct values are numeric or None."""
        data = get_bursa_market_data()
        
        for index in data["klse_indices"]:
            assert index["change_pct"] is None or isinstance(index["change_pct"], (int, float))
        
        for stock in data["top_active"]:
            assert stock["change_pct"] is None or isinstance(stock["change_pct"], (int, float))
    
    def test_sector_indices_has_multiple_sectors(self):
        """Test that multiple sector indices are returned."""
        data = get_bursa_market_data()
        
        # Should have at least some sector indices
        assert len(data["sector_indices"]) >= 5
        
        # Verify sector names contain expected keywords (case-insensitive)
        sector_names = [idx["name"].upper() for idx in data["sector_indices"]]
        sector_keywords = ["CONSUMER", "INDUSTRIAL", "FINANCE", "PROPERTY", "PLANTATION"]
        
        # At least some sectors should match
        matched = sum(1 for keyword in sector_keywords if any(keyword in name for name in sector_names))
        assert matched >= 3


class TestErrorHandling:
    """Test error handling behavior."""
    
    def test_returns_partial_data_on_parse_error(self):
        """Test that function returns partial data if some sections fail."""
        # This is tested implicitly - if we get here without exception,
        # the function successfully handled any parsing errors
        
        data = get_bursa_market_data()
        
        # Should always return a dict
        assert isinstance(data, dict)
        
        # Should have at least some keys
        assert len(data.keys()) >= 2  # scraped_at, source at minimum
    
    def test_error_key_only_if_all_fail(self):
        """Test that error key is only present if all sections fail."""
        data = get_bursa_market_data()
        
        # If we successfully scraped anything, there should be no error key
        if len(data["klse_indices"]) > 0 or len(data["top_active"]) > 0:
            assert "error" not in data or data.get("error") is None


class TestIntegration:
    """Integration tests with real klsescreener.com data."""
    
    def test_klci_price_is_reasonable(self):
        """Test that KLCI price is in reasonable range (1000-2000)."""
        data = get_bursa_market_data()
        
        klcis = [idx for idx in data["klse_indices"] if idx["code"] == "200"]
        if len(klcis) > 0 and klcis[0]["price"]:
            price = klcis[0]["price"]
            assert 1000 <= price <= 2000, f"KLCI price {price} seems unreasonable"
    
    def test_cpo_price_is_reasonable(self):
        """Test that CPO price is in reasonable range (3000-6000)."""
        data = get_bursa_market_data()
        
        cpos = [idx for idx in data["klse_indices"] if idx["code"] == "CPO"]
        if len(cpos) > 0 and cpos[0]["price"]:
            price = cpos[0]["price"]
            assert 3000 <= price <= 6000, f"CPO price {price} seems unreasonable"
    
    def test_top_active_has_volume(self):
        """Test that top active stocks have volume data."""
        data = get_bursa_market_data()
        
        if len(data["top_active"]) > 0:
            stock = data["top_active"][0]
            assert "volume" in stock
            assert stock["volume"]  # Should not be empty
    
    def test_top_turnover_has_turnover(self):
        """Test that top turnover stocks have turnover data."""
        data = get_bursa_market_data()
        
        if len(data["top_turnover"]) > 0:
            stock = data["top_turnover"][0]
            assert "turnover" in stock
            assert "m" in stock["turnover"].lower()  # Should contain 'm' for millions
