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


def extract_ecommercepro_products(html: str, base_url: str) -> list[dict]:
    """Parse product cards from the "EcommercePro" WooCommerce theme, shared
    by several Paraguayan supermarket sites (Casa Rica, Areté, Los Jardines
    confirmed live) — none of which emit schema.org Product JSON-LD, so this
    is the real extraction path for that theme.

    Handles both card shapes seen live: a sale price inside <ins> with the
    original crossed out in <del>, and a plain single price with an empty
    <ins> placeholder. Returns [{"name", "price", "url"}, ...]; cards with no
    parseable price are skipped.
    """
    soup = BeautifulSoup(html, "html.parser")
    products: list[dict] = []
    for card in soup.select("div.product"):
        title = card.select_one(".ecommercepro-loop-product__title")
        link = card.select_one("a.ecommercepro-LoopProduct-link")
        price_container = card.select_one("span.price")
        if not (title and link and price_container):
            continue

        price = None
        ins_amount = price_container.select_one("ins .amount")
        if ins_amount and ins_amount.get_text(strip=True):
            price = parse_py_price(ins_amount.get_text())
        else:
            for amount in price_container.select(".amount"):
                if amount.find_parent("del"):
                    continue
                text = amount.get_text(strip=True)
                if text:
                    price = parse_py_price(text)
                    break

        if price is None:
            continue

        href = link.get("href", "")
        url = href if href.startswith("http") else base_url.rstrip("/") + "/" + href.lstrip("/")
        products.append({"name": title.get_text(strip=True), "price": price, "url": url})
    return products


class Scraper:
    name: str = "base"
    base_url: str = ""

    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.headers["User-Agent"] = USER_AGENT

    def search(self, query: str) -> list[ProductMatch]:
        raise NotImplementedError
