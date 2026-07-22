from scrapers.casa_rica import CasaRicaScraper


def test_search_parses_fixture(monkeypatch):
    scraper = CasaRicaScraper()
    with open("fixtures/casa_rica_search_arroz.html", encoding="utf-8") as f:
        fixture_html = f.read()

    class FakeResponse:
        text = fixture_html
        url = "https://www.casarica.com.py/productos?q=arroz&post_type=product"
        def raise_for_status(self):
            pass

    monkeypatch.setattr(scraper.session, "get", lambda *a, **k: FakeResponse())
    results = scraper.search("arroz")
    assert len(results) == 1
    assert results[0].price == 14000.0
    assert results[0].name == "ARROZ DON ARROZ INTEGRAL 1KG"
    assert results[0].url == "https://www.casarica.com.py/arroz-don-arroz-integral-1kg-p23506"
