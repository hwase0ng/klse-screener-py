"""Tests for KLSE sector stock scraping."""
import pytest
from klse_screener.sectors import KLSE_SECTOR_CODES, SECTOR_URL_BASE


class TestSectorConstants:
    def test_has_all_13_sectors(self):
        assert len(KLSE_SECTOR_CODES) == 13

    def test_sector_codes_are_strings(self):
        for code in KLSE_SECTOR_CODES:
            assert isinstance(code, str)

    def test_sector_names_are_strings(self):
        for name in KLSE_SECTOR_CODES.values():
            assert isinstance(name, str)

    def test_url_base_ends_with_bursa(self):
        assert "markets/bursa" in SECTOR_URL_BASE

    def test_known_sector_present(self):
        assert "0001I" in KLSE_SECTOR_CODES
        assert "CONSUMER" in KLSE_SECTOR_CODES["0001I"].upper()


from klse_screener.sectors import _parse_sector_stocks_html


class TestParseSectorStocksHtml:
    SAMPLE_HTML = '''
    <div class="card-body">
        <div class="row">
            <h6 class="col text-nowrap"><a target="_blank" href="/v2/stocks/view/5681">PETDAG</a></h6>
            <span class="col text-right">19.240</span>
        </div>
        <div class="row">
            <span class="col text-muted" title="Market Cap">19.1B</span>
            <span class="col text-right text-success">
                0.460 (2.4%)
            </span>
        </div>
        <div class="text-right">
            <span class="text-muted">14,731</span>
        </div>
        <small class="text-muted">Retailers</small>
    </div>
    <div class="card-body">
        <div class="row">
            <h6 class="col text-nowrap"><a target="_blank" href="/v2/stocks/view/3026">DLADY</a></h6>
            <span class="col text-right">33.000</span>
        </div>
        <div class="row">
            <span class="col text-muted" title="Market Cap">2.1B</span>
            <span class="col text-right text-success">
                0.280 (0.9%)
            </span>
        </div>
        <div class="text-right">
            <span class="text-muted">400</span>
        </div>
        <small class="text-muted">Food & Beverages</small>
    </div>
    '''

    def test_parses_stock_count(self):
        stocks = _parse_sector_stocks_html(self.SAMPLE_HTML)
        assert len(stocks) == 2

    def test_parses_stock_code(self):
        stocks = _parse_sector_stocks_html(self.SAMPLE_HTML)
        assert stocks[0]["code"] == "5681"
        assert stocks[1]["code"] == "3026"

    def test_parses_stock_symbol(self):
        stocks = _parse_sector_stocks_html(self.SAMPLE_HTML)
        assert stocks[0]["symbol"] == "5681.KL"
        assert stocks[1]["symbol"] == "3026.KL"

    def test_parses_stock_name(self):
        stocks = _parse_sector_stocks_html(self.SAMPLE_HTML)
        assert stocks[0]["name"] == "PETDAG"
        assert stocks[1]["name"] == "DLADY"

    def test_parses_price(self):
        stocks = _parse_sector_stocks_html(self.SAMPLE_HTML)
        assert stocks[0]["price"] == "19.240"
        assert stocks[1]["price"] == "33.000"

    def test_parses_change_pct(self):
        stocks = _parse_sector_stocks_html(self.SAMPLE_HTML)
        assert stocks[0]["change_pct"] == "2.4%"
        assert stocks[1]["change_pct"] == "0.9%"

    def test_parses_subsector(self):
        stocks = _parse_sector_stocks_html(self.SAMPLE_HTML)
        assert stocks[0]["subsector"] == "Retailers"
        assert stocks[1]["subsector"] == "Food & Beverages"

    def test_empty_html_returns_empty(self):
        assert _parse_sector_stocks_html("") == []

    def test_no_stocks_returns_empty(self):
        assert _parse_sector_stocks_html("<div>no stocks here</div>") == []

    def test_negative_change_parsed(self):
        html = '''
        <div class="card-body">
            <div class="row">
                <h6 class="col text-nowrap"><a target="_blank" href="/v2/stocks/view/1234">TESTCO</a></h6>
                <span class="col text-right">5.000</span>
            </div>
            <div class="row">
                <span class="col text-muted" title="Market Cap">1.0B</span>
                <span class="col text-right text-danger">
                    -0.100 (-2.0%)
                </span>
            </div>
            <div class="text-right">
                <span class="text-muted">1,000</span>
            </div>
            <small class="text-muted">Test Sector</small>
        </div>
        '''
        stocks = _parse_sector_stocks_html(html)
        assert len(stocks) == 1
        assert stocks[0]["change_pct"] == "-2.0%"


from klse_screener.sectors import (
    get_klse_sector_stocks,
    get_klse_all_sector_stocks,
    get_klse_sector_info,
)


class TestGetKlseSectorInfo:
    def test_returns_dict(self):
        info = get_klse_sector_info()
        assert isinstance(info, dict)

    def test_has_13_sectors(self):
        info = get_klse_sector_info()
        assert len(info) == 13

    def test_each_entry_has_code_and_name(self):
        info = get_klse_sector_info()
        for code, data in info.items():
            assert "code" in data
            assert "name" in data
            assert data["code"] == code


class TestGetKlseSectorStocks:
    def test_returns_list(self):
        result = get_klse_sector_stocks("0001I")
        assert isinstance(result, list)

    def test_invalid_sector_returns_empty(self):
        result = get_klse_sector_stocks("INVALID")
        assert result == []

    def test_stock_dict_structure(self):
        result = get_klse_sector_stocks("0001I")
        if result:
            stock = result[0]
            assert "code" in stock
            assert "symbol" in stock
            assert "name" in stock
            assert "price" in stock
            assert "change_pct" in stock
            assert "subsector" in stock

    def test_symbol_format(self):
        result = get_klse_sector_stocks("0001I")
        if result:
            for stock in result:
                assert stock["symbol"].endswith(".KL")


class TestGetKlseAllSectorStocks:
    def test_returns_dict(self):
        result = get_klse_all_sector_stocks()
        assert isinstance(result, dict)

    def test_has_sector_keys(self):
        result = get_klse_all_sector_stocks()
        for code in KLSE_SECTOR_CODES:
            assert code in result

    def test_values_are_lists(self):
        result = get_klse_all_sector_stocks()
        for stocks in result.values():
            assert isinstance(stocks, list)
