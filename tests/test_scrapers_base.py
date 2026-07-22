from scrapers.base import extract_jsonld_products, Scraper, ProductMatch

def test_extract_jsonld_products_from_fixture():
    with open("fixtures/jsonld_sample.html", encoding="utf-8") as f:
        html = f.read()
    products = extract_jsonld_products(html)
    assert len(products) == 2
    assert products[0] == {"name": "Arroz Blanco 1kg", "price": 6500.0}
    assert products[1] == {"name": "Aceite de Girasol 900ml", "price": 12900.0}

def test_scraper_base_search_not_implemented():
    scraper = Scraper()
    try:
        scraper.search("arroz")
        assert False, "expected NotImplementedError"
    except NotImplementedError:
        pass

def test_product_match_dataclass():
    p = ProductMatch(name="Arroz 1kg", price=6500.0, url="https://x.com/p/1")
    assert p.name == "Arroz 1kg"
    assert p.price == 6500.0
