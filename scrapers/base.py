import json
import re
import unicodedata
from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup

USER_AGENT = "Hepy/0.1 (+https://github.com/koeti-labs/hepy; contacto: gsmkev@gmail.com)"


@dataclass
class ProductMatch:
    name: str
    price: float
    url: str


# Basket categories where a search engine matching on a bare ingredient name
# (e.g. "banana", "papa", "queso") routinely surfaces a processed product
# using that ingredient as a flavor/component instead of the ingredient
# itself — confirmed live: banana-flavored whey protein for "banana",
# potato gnocchi for "papa", tomato purée for "tomate". _PROCESSED_INDICATOR_WORDS
# below is only applied for these categories/keys.
_RAW_INGREDIENT_CATEGORIES = {
    "alimentacion_frutas",
    "alimentacion_hortalizas_y_tuberculos",
    "alimentacion_carnes",
    "alimentacion_legumbres",
}
_RAW_INGREDIENT_PRODUCT_KEYS = {"queso_paraguay_1kg", "huevos_docena"}

_UNITS_AND_STOPWORDS = {
    "kg", "g", "gr", "grs", "l", "lt", "litro", "litros", "ml", "docena",
    "unidad", "un", "de", "del", "la", "el", "los", "las",
}

_PROCESSED_INDICATOR_WORDS = {
    "agua", "jugo", "gaseosa", "colorante", "saborizada", "saborizado",
    "noqui", "noquis", "pure", "salsa", "sopa", "aderezo", "empanada",
    "tratamiento", "shampoo", "champu", "proteina", "whey", "suplemento",
    "relleno", "helado", "yogur", "yogurt", "galletita", "galletitas",
    "barra", "bebida", "postre", "torta", "budin", "nugget", "nuggets",
    "milanesa", "empanado",
    # Confirmed live in a second pass: frozen/prepared potato snacks
    # ("papa frita"/"pre frita"/"p/freír") dominate every site's "papa"
    # results; egg-adjacent products that aren't a dozen chicken eggs
    # (Easter chocolate eggs, quail eggs, egg salad); onion/orange sold as
    # a dehydrated seasoning or jam rather than the fresh ingredient.
    "frita", "frito", "freir", "mermelada", "deshidratada", "deshidratado",
    "triturada", "triturado", "pascua", "ensalada", "codorniz",
    # Third pass: a misspelled variant seen live ("desidratada", missing the
    # "h"), pickled onion, a hairbrush that happens to be orange-colored
    # (not the fruit), egg noodles/pasta (contains egg, isn't a dozen eggs).
    "desidratada", "desidratado", "granulada", "granulado", "macerado",
    "macerada", "vinagre", "peine", "fideo", "fideos",
    # Fourth pass: a flavoring extract, not the fruit itself.
    "esencia",
    # Fifth pass: flour milled from a raw root, not the root itself
    # ("harina de mandioca" matched for canonical "Mandioca 1kg").
    "harina",
}


def _normalize(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in decomposed if not unicodedata.combining(c))


def _stem(word: str) -> str:
    return word[:-1] if len(word) > 3 and word.endswith("s") else word


def _tokenize(name: str) -> set[str]:
    words = re.findall(r"[a-z]+", _normalize(name))
    return {_stem(w) for w in words if w not in _UNITS_AND_STOPWORDS}


_WEIGHT_VOL_UNIT_TO_BASE = {
    "kg": ("g", 1000.0), "g": ("g", 1.0), "gr": ("g", 1.0), "grs": ("g", 1.0),
    "l": ("ml", 1000.0), "lt": ("ml", 1000.0), "litro": ("ml", 1000.0), "litros": ("ml", 1000.0),
    "ml": ("ml", 1.0),
}
_QUANTITY_RE = re.compile(r"(\d+(?:[.,]\d+)?)\s*(kg|grs?|g|litros?|lt|l|ml)\b")

# "docena"/"unidad"/"un" need a separate pattern with an *optional* leading
# number: "Huevos docena" states no digit at all (a bare "docena" implies
# 12), unlike weight/volume units which are never written without one.
_COUNT_UNIT_TO_BASE = {"docena": 12.0, "unidad": 1.0, "un": 1.0}
_COUNT_RE = re.compile(r"(?:(\d+(?:[.,]\d+)?)\s*)?(docena|unidad|un)\b")


def _extract_quantity(text: str) -> tuple[float, str] | None:
    # ponytail: only the first quantity found is used — good enough for
    # single-pack basket items, would need a rewrite for multipacks ("3x500g").
    norm = _normalize(text)
    match = _QUANTITY_RE.search(norm)
    if match:
        unit, factor = _WEIGHT_VOL_UNIT_TO_BASE[match.group(2)]
        return (round(float(match.group(1).replace(",", ".")) * factor, 3), unit)

    match = _COUNT_RE.search(norm)
    if match:
        if match.group(1) is None:
            # A bare "unidad"/"un" (no digit) just means "priced per piece",
            # not a specific count to verify — real case: "Jabón de tocador
            # unidad" is sold by the bar, and real bars describe their
            # weight in grams (a different axis), not a unit count. Only a
            # bare "docena" is an actual quantity claim (implies 12).
            if match.group(2) != "docena":
                return None
            count = 1.0
        else:
            count = float(match.group(1).replace(",", "."))
        return (round(count * _COUNT_UNIT_TO_BASE[match.group(2)], 3), "un")

    return None


def select_best_match(
    canonical_name: str,
    candidates: list[ProductMatch],
    bcp_category: str | None = None,
    product_key: str | None = None,
) -> ProductMatch | None:
    """Pick the first candidate that plausibly refers to canonical_name,
    instead of blindly trusting the search engine's top result.

    Real supermarket search engines routinely surface unrelated products
    that merely mention the query term — a banana-flavored whey protein for
    "banana", potato gnocchi for "papa", or (confirmed live) "sopa
    paraguaya" (a corn-cake dish) for "queso paraguay" (a cheese) on shared
    words alone. A candidate must contain every significant word of
    canonical_name (accent/case/simple-plural insensitive); for basket items
    in a raw-ingredient category (fruit, vegetable, meat, legumes) or
    explicitly flagged via product_key, it must additionally contain none of
    a fixed list of processed-food indicator words. Returns None (treated as
    "no match", not a wrong one) if nothing qualifies.
    """
    canon_tokens = _tokenize(canonical_name)
    if not canon_tokens:
        return candidates[0] if candidates else None
    canon_norm = _normalize(canonical_name)
    canon_qty = _extract_quantity(canonical_name)

    strict = bcp_category in _RAW_INGREDIENT_CATEGORIES or product_key in _RAW_INGREDIENT_PRODUCT_KEYS

    for candidate in candidates:
        cand_tokens = _tokenize(candidate.name)
        if not canon_tokens.issubset(cand_tokens):
            continue
        # A candidate in a completely different pack size isn't the same
        # product for price-comparison purposes — confirmed live: "Aceite de
        # girasol 900ml" matched a 1,5 LT bottle, since quantities were never
        # compared (digits are dropped by _tokenize, unit words are
        # stopwords). Only enforced when the canonical name actually states
        # a quantity.
        if canon_qty is not None and _extract_quantity(candidate.name) != canon_qty:
            continue
        if strict:
            cand_norm = _normalize(candidate.name)
            # Substring (not exact-token) check: catches glued compounds
            # like "PREFRITAS" containing "frita", which a token-set
            # intersection would miss. A denylist word already present in
            # the canonical name itself never disqualifies (defensive: no
            # current basket item hits this, but it's a real correctness
            # trap for future denylist additions).
            if any(word in cand_norm and word not in canon_norm for word in _PROCESSED_INDICATOR_WORDS):
                continue
        return candidate
    return None


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


def extract_nextjs_rsc_products(text: str) -> list[dict]:
    """Parse product records out of a Next.js React Server Components (RSC)
    payload — the "Flight" wire format Next.js sends when a request carries
    an `RSC: 1` header, requesting the raw server-rendered data instead of
    HTML. Real (realonline.com.py) renders its search results this way with
    no client-callable product-search API; the payload is a stream of
    `<id>:<json-or-primitive>` lines, one per server-component data chunk.

    Returns [{"name", "price", "sku"}, ...] for every line whose JSON object
    has all three fields; every other line (categories, UI state, etc.) is
    skipped silently.
    """
    products: list[dict] = []
    for line in text.splitlines():
        m = re.match(r"^[0-9a-f]+:(\{.*\})$", line)
        if not m:
            continue
        try:
            obj = json.loads(m.group(1))
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict) and "name" in obj and "price" in obj and "sku" in obj:
            products.append({"name": obj["name"], "price": float(obj["price"]), "sku": obj["sku"]})
    return products


def extract_woocommerce_products(html: str, base_url: str) -> list[dict]:
    """Parse product cards from a plain WooCommerce theme (confirmed live on
    Grütter's "megashop" theme) — no schema.org Product JSON-LD present, so
    this parses the standard `.woocommerce-loop-product__title` /
    `.woocommerce-Price-amount` markup directly.

    Takes the primary `span.price` amount (ignores any bulk-discount price
    shown separately, e.g. Grütter's "3 o más" tier). Returns
    [{"name", "price", "url"}, ...]; cards with no parseable price skipped.
    """
    soup = BeautifulSoup(html, "html.parser")
    products: list[dict] = []
    for card in soup.select("li.product"):
        title = card.select_one(".woocommerce-loop-product__title")
        link = card.select_one("a.woocommerce-loop-product__link")
        price_amount = card.select_one("span.price .woocommerce-Price-amount")
        if not (title and link and price_amount):
            continue

        price = parse_py_price(price_amount.get_text())
        if price is None:
            continue

        href = link.get("href", "")
        url = href if href.startswith("http") else base_url.rstrip("/") + "/" + href.lstrip("/")
        products.append({"name": title.get_text(strip=True), "price": price, "url": url})
    return products


def extract_stock_products(html: str) -> list[dict]:
    """Parse product cards from Stock's custom ASP.NET WebForms storefront
    (confirmed live: NOT nopCommerce despite the original planning guess —
    just carries an old nopCommerce copyright comment; no Product JSON-LD).
    Product URLs are absolute already, so no base_url join is needed.

    Returns [{"name", "price", "url"}, ...]; cards with no parseable price
    skipped.
    """
    soup = BeautifulSoup(html, "html.parser")
    products: list[dict] = []
    for card in soup.select("div.product-item"):
        link = card.select_one("h2.product-title a.product-title-link")
        price_span = card.select_one("span.productPrice")
        if not (link and price_span):
            continue

        price = parse_py_price(price_span.get_text())
        if price is None:
            continue

        products.append({"name": link.get_text(strip=True), "price": price, "url": link.get("href", "")})
    return products


class Scraper:
    name: str = "base"
    base_url: str = ""

    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.headers["User-Agent"] = USER_AGENT

    def search(self, query: str) -> list[ProductMatch]:
        raise NotImplementedError
