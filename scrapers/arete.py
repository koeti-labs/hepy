from scrapers.base import ProductMatch, Scraper, extract_ecommercepro_products


class AreteScraper(Scraper):
    name = "arete"
    base_url = "https://www.arete.com.py"
    # Confirmed live: same EcommercePro WooCommerce theme as Casa Rica and
    # Los Jardines. Real search form posts to "productos" with a "q" param.
    search_path = "/productos?q={query}&post_type=product"

    def search(self, query: str) -> list[ProductMatch]:
        url = self.base_url + self.search_path.format(query=query)
        resp = self.session.get(url, timeout=10)
        resp.raise_for_status()
        products = extract_ecommercepro_products(resp.text, self.base_url)
        return [ProductMatch(p["name"], p["price"], p["url"]) for p in products]
