"""Regression: QoQ%/YoY% direction is carried only by the cell's CSS class.

KLSE Screener prints QoQ% and YoY% as unsigned magnitudes ("29.1%") and encodes
direction solely in the inner span's ``btn-success`` / ``btn-danger`` class.
``cell.get_text()`` discards class attributes, so before this fix every earnings
*decline* was published as a growth number. In the BeatIt cache that produced
75,056 ``yoy`` values with zero negatives across 1,119 KLSE files, and 45.2% of
0012.KL's comparable quarters (19 of 42) carried the wrong sign.

These tests pin the fixed behaviour against a captured page so the defect cannot
return silently. The 2025-06-30 row is the canonical case: QoQ 14.2% and
YoY 29.1%, both ``btn-danger``, previously stored as +14.2 / +29.1.
"""

from pathlib import Path

import pytest

from klse_screener import financials
from klse_screener.financials import (
    _apply_percent_sign,
    _parse_formatted_number,
    _percent_sign_class,
    get_klse_quarterly_financials_dict,
)

FIXTURE = (
    Path(__file__).parent / "fixtures" / "financial_report_0012_quarterly.html"
)


@pytest.fixture
def quarterly(monkeypatch):
    """Parse the captured page offline instead of hitting klsescreener.com."""
    html = FIXTURE.read_text(encoding="utf-8", errors="replace")
    monkeypatch.setattr(financials, "fetch_url", lambda *a, **k: html)
    result = get_klse_quarterly_financials_dict("0012.KL")
    assert result.get("quarterly_data"), "fixture produced no quarterly rows"
    return {row["q_date"]: row for row in result["quarterly_data"]}


def test_danger_class_becomes_negative(quarterly):
    """A btn-danger decline must not be published as a gain."""
    row = quarterly["2025-06-30"]
    assert row["qoq"] == pytest.approx(-14.2)
    assert row["yoy"] == pytest.approx(-29.1)


def test_success_class_stays_positive(quarterly):
    row = quarterly["2026-06-30"]
    assert row["qoq"] == pytest.approx(41.0)
    assert row["yoy"] == pytest.approx(91.3)


def test_opposite_signs_within_one_row(quarterly):
    """Strongest case: one row where QoQ fell and YoY rose.

    Guards against a fix that applies a single blanket sign per row, or that
    assumes both percentage columns always agree.
    """
    row = quarterly["2026-03-31"]
    assert row["qoq"] == pytest.approx(-13.1)   # btn-danger
    assert row["yoy"] == pytest.approx(16.5)    # btn-success


def test_near_zero_magnitude_keeps_its_class_sign(quarterly):
    """2025-12-31 YoY is 0.9% btn-danger: a real decline that reads as +0.9%."""
    row = quarterly["2025-12-31"]
    assert row["yoy"] == pytest.approx(-0.9)


def test_roe_is_unclassed_and_unaffected(quarterly):
    """ROE carries no sign class, so it must pass through untouched."""
    assert quarterly["2025-06-30"]["roe"] == pytest.approx(1.7)


def test_non_percentage_columns_unchanged(quarterly):
    """Only columns 10/11 may change; the rest of the row must be untouched."""
    row = quarterly["2026-06-30"]
    assert row["qoq"] == pytest.approx(41.0)
    assert row["q_date"] == "2026-06-30"
    assert row["financial_year"] == "31 Dec, 2026"
    # Monetary columns are magnitudes, not signed percentages.
    assert row["revenue"] > 0
    assert row["net_profit"] > 0


class TestHelpers:
    def test_class_is_authoritative_for_direction(self):
        """A classed cell's magnitude is unsigned, so the class decides the sign.

        Verified against the fixture: classed QoQ%/YoY% cells never carry a
        literal minus ('41%', '14.2%', '0.9%'). So ``abs()`` is correct rather
        than a normalisation -- and it also prevents a double negation when the
        class already says "decline".
        """
        assert _apply_percent_sign(-5.0, -1) == -5.0   # danger: not flipped twice
        assert _apply_percent_sign(5.0, -1) == -5.0
        assert _apply_percent_sign(5.0, 1) == 5.0
        assert _apply_percent_sign(-5.0, 1) == 5.0     # class overrides magnitude

    def test_zero_ignores_class(self):
        assert _apply_percent_sign(0.0, -1) == 0.0

    def test_missing_values_pass_through(self):
        assert _apply_percent_sign(None, -1) is None

    def test_unclassed_cell_yields_no_sign(self):
        from bs4 import BeautifulSoup

        soup = BeautifulSoup("<td>1.7%</td>", "html.parser")
        assert _percent_sign_class(soup.find("td")) is None

    def test_paren_negative_still_parses(self):
        """Parenthesised-negative handling must be left intact."""
        assert _parse_formatted_number("(1,234)") == pytest.approx(-1234.0)
