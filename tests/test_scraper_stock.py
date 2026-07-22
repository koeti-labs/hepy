from scrapers.stock import StockScraper


def test_search_parses_fixture(monkeypatch):
    scraper = StockScraper()
    with open("fixtures/stock_search_arroz.html", encoding="utf-8") as f:
        fixture_html = f.read()

    class FakeResponse:
        text = fixture_html
        url = "https://www.stock.com.py/search.aspx?searchterms=arroz"
        def raise_for_status(self):
            pass

    monkeypatch.setattr(scraper.session, "get", lambda *a, **k: FakeResponse())
    results = scraper.search("arroz")
    assert len(results) == 1
    assert results[0].price == 21000.0
    assert results[0].name == "ARROZ CHINES INTEGRAL BOLSA 1KG"
    assert results[0].url == "https://www.stock.com.py/products/10070-arroz-chines-integral-bsa-1kg.aspx"
