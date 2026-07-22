from scrapers.base import ProductMatch, Scraper, extract_stock_products


class StockScraper(Scraper):
    name = "stock"
    base_url = "https://www.stock.com.py"
    # Confirmed live: NOT nopCommerce (only carries an old nopCommerce
    # copyright comment) — a custom ASP.NET WebForms storefront. The real
    # search path (found via a live promo link) is search.aspx?searchterms=,
    # not /search?q= as originally guessed; confirmed it filters correctly
    # and does not require the WebForms postback/viewstate flow.
    search_path = "/search.aspx?searchterms={query}"

    def search(self, query: str) -> list[ProductMatch]:
        url = self.base_url + self.search_path.format(query=query)
        resp = self.session.get(url, timeout=10)
        resp.raise_for_status()
        products = extract_stock_products(resp.text)
        return [ProductMatch(p["name"], p["price"], p["url"]) for p in products]
