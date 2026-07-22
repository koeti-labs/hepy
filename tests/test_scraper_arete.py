from scrapers.arete import AreteScraper


def test_search_parses_fixture(monkeypatch):
    scraper = AreteScraper()
    with open("fixtures/arete_search_arroz.html", encoding="utf-8") as f:
        fixture_html = f.read()

    class FakeResponse:
        text = fixture_html
        url = "https://www.arete.com.py/productos?q=arroz&post_type=product"
        def raise_for_status(self):
            pass

    monkeypatch.setattr(scraper.session, "get", lambda *a, **k: FakeResponse())
    results = scraper.search("arroz")
    assert len(results) == 1
    assert results[0].price == 4700.0
    assert results[0].name == "ARROZ AZUL TIPO II 1 KG  EL PAIS"
    assert results[0].url == "https://www.arete.com.py/arroz-azul-tipo-ii-1-kg-el-pais-p152778"
