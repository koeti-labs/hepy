from scrapers.grutter import GrutterScraper


def test_search_parses_fixture(monkeypatch):
    scraper = GrutterScraper()
    with open("fixtures/grutter_search_arroz.html", encoding="utf-8") as f:
        fixture_html = f.read()

    class FakeResponse:
        text = fixture_html
        url = "https://grutteronline.casagrutter.com.py/?s=arroz&post_type=product"
        def raise_for_status(self):
            pass

    monkeypatch.setattr(scraper.session, "get", lambda *a, **k: FakeResponse())
    results = scraper.search("arroz")
    assert len(results) == 1
    assert results[0].price == 4700.0
    assert results[0].name == "ARROZ TIO NICO ROJO 1 KG."
    assert results[0].url == "https://grutteronline.casagrutter.com.py/producto/arroz-tio-nico-rojo-1-kg/"
