"""
Tests for get_klse_financial_report_figures().

Verifies the library-owned P&L figure scraper parses PBT / attributable / NAPS
from a saved financial-report fixture (scale-correct) and that return_html=True
includes the raw page HTML.
"""

from pathlib import Path
from unittest import mock

from klse_screener.financials import get_klse_financial_report_figures

FIX = Path(__file__).parent / "fixtures" / "financial_report_0012_2026-06-30.html"
HTML = FIX.read_text()


class TestGetKlseFinancialReportFigures:
    """Test get_klse_financial_report_figures() against a saved fixture."""

    def test_parses_scaled_figures(self):
        """PBT / attributable are MYR'000 on the page -> scaled x1000 to raw RM."""
        with mock.patch(
            "klse_screener.financials.fetch_url", return_value=HTML
        ) as m_fetch:
            r = get_klse_financial_report_figures("0012.KL", "2026-06-30")

        # fetch_url called with the correct financial-report URL + cache key.
        m_fetch.assert_called_once()
        args = m_fetch.call_args.args
        assert args[0] == (
            "https://www.klsescreener.com/v2/stock/financial-report/0012/2026-06-30"
        )

        assert r.get("data_source") == "klsescreener_financial_report"
        # Revenue 33,900 (MYR'000) -> 33,900,000 raw ringgit
        assert r["revenue"] == 33_900_000
        # PBT 5,200 (MYR'000) -> 5,200,000
        assert r["profit_before_tax"] == 5_200_000
        # Attributable 4,100 (MYR'000) -> 4,100,000
        assert r["profit_attributable_parent"] == 4_100_000
        # NAPS 0.51 RM stays as-is
        assert r["nta_parent"] == 0.51
        # EPS/DPS sen stay as-is
        assert r["eps"] == 0.84
        assert r["dps"] == 1.0

    def test_ignores_cumulative_column(self):
        """Must target the Individual Period - Current Year Quarter column (idx 1)."""
        with mock.patch("klse_screener.financials.fetch_url", return_value=HTML):
            r = get_klse_financial_report_figures("0012.KL", "2026-06-30")

        # If it grabbed the cumulative (YTD) column, revenue would be 65,000,000.
        assert r["revenue"] != 65_000_000
        assert r["profit_before_tax"] != 9_500_000

    def test_return_html_includes_raw_page(self):
        """return_html=True includes the raw page under '_html' (Plan 2 hook)."""
        with mock.patch("klse_screener.financials.fetch_url", return_value=HTML):
            r = get_klse_financial_report_figures(
                "0012.KL", "2026-06-30", return_html=True
            )

        assert "_html" in r
        assert "33,900" in r["_html"]
        assert "download?id=239272" in r["_html"]

    def test_error_on_empty_response(self):
        """Empty page -> {'error': ...}, never raises."""
        with mock.patch("klse_screener.financials.fetch_url", return_value=""):
            r = get_klse_financial_report_figures("0012.KL", "2026-06-30")

        assert "error" in r

    def test_error_on_403_page(self):
        """403 page -> {'error': ...}."""
        with mock.patch(
            "klse_screener.financials.fetch_url",
            return_value="<html>403 Forbidden</html>",
        ):
            r = get_klse_financial_report_figures("0012.KL", "2026-06-30")

        assert "error" in r


if __name__ == "__main__":
    import pytest

    pytest.main([__file__, "-v"])
