from bs4 import BeautifulSoup

from scrapers.base import ProductMatch, Scraper, parse_py_price


class SalemmaScraper(Scraper):
    name = "salemma"
    base_url = "https://www.salemmaonline.com.py"
    # Confirmed live via the site's own schema.org SearchAction (WebSite JSON-LD
    # on every page): target "https://www.salemmaonline.com.py//buscar?q={...}".
    # The platform does not emit Product JSON-LD anywhere (checked search
    # results and category pages) — parses the "divproduct" cards directly.
    search_path = "/buscar?q={query}"

    def search(self, query: str) -> list[ProductMatch]:
        url = self.base_url + self.search_path.format(query=query)
        resp = self.session.get(url, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        results: list[ProductMatch] = []
        for card in soup.select("div.divproduct"):
            link = card.select_one('a[href*="/producto/"]')
            price_tag = card.select_one("h6.pprice")
            name_tag = card.select_one("h6.psubtitle a.apsubtitle") or card.select_one("h6.ptitle")
            if not (link and price_tag and name_tag):
                continue
            price = parse_py_price(price_tag.get_text())
            if price is None:
                continue
            results.append(ProductMatch(name_tag.get_text(strip=True), price, link["href"]))
        return results
