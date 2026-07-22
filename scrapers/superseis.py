from scrapers.base import ProductMatch, Scraper, extract_jsonld_products


class SuperseisScraper(Scraper):
    name = "superseis"
    base_url = "https://www.superseis.com.py"
    search_path = "/busqueda?q={query}"  # ponytail: verify against a live browser session — site blocked automated fetches (CloudFront 403) during planning

    def search(self, query: str) -> list[ProductMatch]:
        url = self.base_url + self.search_path.format(query=query)
        resp = self.session.get(url, timeout=10)
        resp.raise_for_status()
        products = extract_jsonld_products(resp.text)
        return [ProductMatch(p["name"], p["price"], resp.url) for p in products]
