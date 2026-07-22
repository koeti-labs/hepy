import json
from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup

USER_AGENT = "Hepy/0.1 (+https://github.com/koeti-labs/hepy; contacto: labs@koeti.dev)"


@dataclass
class ProductMatch:
    name: str
    price: float
    url: str


def extract_jsonld_products(html: str) -> list[dict]:
    """Parse schema.org Product JSON-LD blocks embedded in a page.

    Returns a list of {"name": str, "price": float}. Malformed or non-Product
    blocks are skipped silently, never raise.
    """
    soup = BeautifulSoup(html, "html.parser")
    products: list[dict] = []
    for tag in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(tag.string or "")
        except (json.JSONDecodeError, TypeError):
            continue
        items = data if isinstance(data, list) else [data]
        for item in items:
            if not isinstance(item, dict) or item.get("@type") != "Product":
                continue
            offers = item.get("offers", {})
            if isinstance(offers, list):
                offers = offers[0] if offers else {}
            name = item.get("name")
            price = offers.get("price") if isinstance(offers, dict) else None
            if name and price is not None:
                try:
                    products.append({"name": name, "price": float(price)})
                except (TypeError, ValueError):
                    continue
    return products


class Scraper:
    name: str = "base"
    base_url: str = ""

    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.headers["User-Agent"] = USER_AGENT

    def search(self, query: str) -> list[ProductMatch]:
        raise NotImplementedError
