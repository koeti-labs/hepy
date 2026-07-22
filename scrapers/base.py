import json
import re
from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup

USER_AGENT = "Hepy/0.1 (+https://github.com/gsmkev/hepy; contacto: gsmkev@gmail.com)"


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


def parse_py_price(text: str) -> float | None:
    """Parse a Paraguayan Guaraní price string (e.g. "Gs. 11.400") into a
    float (11400.0). Guaraní has no cents; "." is the thousands separator,
    not a decimal point. Returns None if no digits are found.
    """
    digits = re.sub(r"[^\d]", "", text)
    return float(digits) if digits else None


class Scraper:
    name: str = "base"
    base_url: str = ""

    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.headers["User-Agent"] = USER_AGENT

    def search(self, query: str) -> list[ProductMatch]:
        raise NotImplementedError
