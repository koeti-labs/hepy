from scrapers.base import ProductMatch, Scraper, extract_ecommercepro_products


class LosJardinesScraper(Scraper):
    name = "los_jardines"
    base_url = "https://www.losjardinesonline.com.py"
    # Confirmed live: same EcommercePro WooCommerce theme as Casa Rica and
    # Areté. Unlike Casa Rica, this site's search form correctly posts to
    # "catalogo" with a "q" param and does filter results.
    search_path = "/catalogo?q={query}"

    def search(self, query: str) -> list[ProductMatch]:
        url = self.base_url + self.search_path.format(query=query)
        resp = self.session.get(url, timeout=10)
        resp.raise_for_status()
        products = extract_ecommercepro_products(resp.text, self.base_url)
        return [ProductMatch(p["name"], p["price"], p["url"]) for p in products]
