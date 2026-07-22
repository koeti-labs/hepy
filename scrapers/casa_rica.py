from scrapers.base import ProductMatch, Scraper, extract_ecommercepro_products


class CasaRicaScraper(Scraper):
    name = "casa_rica"
    base_url = "https://www.casarica.com.py"
    # Confirmed live: the "quick search" navbar form (action="catalogo") does
    # NOT filter results — a WooCommerce/EcommercePro theme quirk (verified:
    # different query terms returned byte-identical output there). The real
    # product search form (id="ecommercepro-product-search-field-0") posts to
    # "productos" with a "q" param and does filter correctly.
    search_path = "/productos?q={query}&post_type=product"

    def search(self, query: str) -> list[ProductMatch]:
        url = self.base_url + self.search_path.format(query=query)
        resp = self.session.get(url, timeout=10)
        resp.raise_for_status()
        products = extract_ecommercepro_products(resp.text, self.base_url)
        return [ProductMatch(p["name"], p["price"], p["url"]) for p in products]
