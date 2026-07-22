from scrapers.base import ProductMatch, Scraper


class BiggieScraper(Scraper):
    name = "biggie"
    base_url = "https://www.biggie.com.py"
    # Confirmed live via browser network inspection: the frontend (a Vue SPA,
    # not server-rendered HTML — no JSON-LD anywhere) calls this JSON API
    # directly. The search page itself (biggie.com.py/search?q=...) is only
    # useful as a human-facing reference URL; the real data comes from here.
    api_url = "https://api.app.biggie.com.py/api/articles"
    reference_url = "https://www.biggie.com.py/search?q={query}"

    def search(self, query: str) -> list[ProductMatch]:
        resp = self.session.get(
            self.api_url,
            params={"query": query, "take": 24, "skip": 0, "classificationId": 0},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        reference = self.reference_url.format(query=query)

        results: list[ProductMatch] = []
        for item in data.get("items", []):
            price = item["priceSaleOffer"] if item.get("isOnOffer") else item["price"]
            if price is None:
                continue
            results.append(ProductMatch(item["name"], float(price), reference))
        return results
