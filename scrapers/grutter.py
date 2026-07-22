from scrapers.base import ProductMatch, Scraper, extract_woocommerce_products


class GrutterScraper(Scraper):
    name = "grutter"
    base_url = "https://grutteronline.casagrutter.com.py"
    # Reachability confirmed from the real execution environment (the
    # planning-sandbox connection failure did not reproduce). Standard
    # WooCommerce ("megashop" theme) — confirmed live: no Product JSON-LD,
    # search via ?s=<term>&post_type=product does filter correctly.
    search_path = "/?s={query}&post_type=product"

    def search(self, query: str) -> list[ProductMatch]:
        url = self.base_url + self.search_path.format(query=query)
        resp = self.session.get(url, timeout=10)
        resp.raise_for_status()
        products = extract_woocommerce_products(resp.text, self.base_url)
        return [ProductMatch(p["name"], p["price"], p["url"]) for p in products]
