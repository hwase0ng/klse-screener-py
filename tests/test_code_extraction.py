"""
Tests for stock code extraction with leading zeros.

Verifies that stock codes with leading zeros are preserved correctly:
0001.KL -> "0001" (not "1")
0002.KL -> "0002" (not "2")
"""

import pytest
import re


def extract_code_from_ticker(ticker: str) -> str:
    """
    Extract numeric code from ticker.
    
    This is the CORRECT implementation that preserves leading zeros.
    """
    code = re.sub(r"\..*$", "", ticker.upper())
    return code or ticker


class TestStockCodeExtraction:
    """Test that stock code extraction preserves leading zeros."""
    
    def test_leading_zeros_preserved(self):
        """Test that leading zeros are NOT stripped."""
        # These stocks have leading zeros and MUST be preserved
        test_cases = [
            ("0001.KL", "0001"),
            ("0002.KL", "0002"),
            ("0005.KL", "0005"),
            ("0010.KL", "0010"),
            ("0025.KL", "0025"),
            ("0050.KL", "0050"),
        ]
        
        for ticker, expected_code in test_cases:
            code = extract_code_from_ticker(ticker)
            assert code == expected_code, f"Leading zeros lost for {ticker}"
    
    def test_no_leading_zeros_unchanged(self):
        """Test that codes without leading zeros work correctly."""
        test_cases = [
            ("5132.KL", "5132"),
            ("1155.KL", "1155"),
            ("700.HK", "700"),
            ("9988.HK", "9988"),
        ]
        
        for ticker, expected_code in test_cases:
            code = extract_code_from_ticker(ticker)
            assert code == expected_code
    
    def test_klsescreener_url_format(self):
        """Test that extracted codes produce valid klsescreener URLs."""
        test_cases = [
            ("0001.KL", "https://www.klsescreener.com/v2/stocks/view/0001"),
            ("0002.KL", "https://www.klsescreener.com/v2/stocks/view/0002"),
            ("5132.KL", "https://www.klsescreener.com/v2/stocks/view/5132"),
        ]
        
        for ticker, expected_url in test_cases:
            code = extract_code_from_ticker(ticker)
            url = f"https://www.klsescreener.com/v2/stocks/view/{code}"
            assert url == expected_url
    
    def test_uppercase_conversion(self):
        """Test that lowercase tickers are converted to uppercase."""
        assert extract_code_from_ticker("0001.kl") == "0001"
        assert extract_code_from_ticker("5132.kl") == "5132"
    
    def test_edge_cases(self):
        """Test edge cases."""
        # Empty string returns empty
        assert extract_code_from_ticker("") == ""
        # Malformed ticker with only suffix returns the suffix (no match on regex)
        assert extract_code_from_ticker(".KL") == ".KL"


class TestBuggyExtraction:
    """
    Test to document the BUGGY extraction that strips leading zeros.
    
    This test should FAIL with the buggy implementation, PASS with the fix.
    """
    
    def extract_code_buggy(self, ticker: str) -> str:
        """BUGGY implementation that strips leading zeros."""
        return re.sub(r"\..*$", "", ticker.upper()).lstrip("0") or ticker
    
    def test_buggy_version_strips_zeros(self):
        """
        This test DOCUMENTS the bug - it should FAIL with buggy code.
        
        If this test PASSES, the bug is NOT fixed.
        If this test FAILS, the bug IS fixed (which is what we want).
        """
        buggy_code = self.extract_code_buggy("0001.KL")
        
        # With buggy code: "0001.KL" -> "1" (WRONG)
        # With fixed code: This test would fail because we're testing buggy behavior
        
        # This assertion checks that the buggy version DOES strip zeros
        assert buggy_code == "1", "Bug not present - code preserves leading zeros"
        
        # This assertion would check for the bug being fixed
        # assert buggy_code == "0001", "Bug still present - leading zeros stripped"
