import json

from scrapers.biggie import BiggieScraper


def test_search_parses_fixture(monkeypatch):
    scraper = BiggieScraper()
    with open("fixtures/biggie_search_arroz.json", encoding="utf-8") as f:
        fixture_data = json.load(f)

    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return fixture_data

    monkeypatch.setattr(scraper.session, "get", lambda *a, **k: FakeResponse())
    results = scraper.search("arroz")
    assert len(results) == 2
    # first item is on offer: uses priceSaleOffer, not the crossed-out price
    assert results[0].name == "Arroz Primicia Parborizado Tipo I de 1.000 gr."
    assert results[0].price == 8450.0
    # second item is not on offer: uses the plain price
    assert results[1].name == "Arroz Doña Juana 1kg"
    assert results[1].price == 7200.0
    assert results[0].url == "https://www.biggie.com.py/search?q=arroz"
