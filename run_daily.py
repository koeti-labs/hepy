import json
import logging

import db
import index
import outliers
from scrapers.base import Scraper

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("run_daily")


def run(conn, basket: list[dict], scrapers: list[Scraper], date: str) -> dict:
    inserted = 0
    missing = 0
    failed_supermarkets: list[str] = []

    for scraper in scrapers:
        try:
            for item in basket:
                query = item["queries"].get(scraper.name, item["nombre_canonico"])
                matches = scraper.search(query)
                if not matches:
                    missing += 1
                    log.info("no match for %s on %s", item["product_key"], scraper.name)
                    continue

                best = matches[0]
                history = [
                    r["price"]
                    for r in db.read_prices(conn, product_key=item["product_key"], supermarket=scraper.name)
                ]
                flagged = outliers.is_outlier(history, best.price)
                db.insert_price(
                    conn, date, scraper.name, item["product_key"], best.name, best.price, best.url,
                    is_outlier=flagged,
                )
                inserted += 1
        except Exception as exc:  # a whole supermarket failing must not abort the run
            log.warning("supermarket %s failed: %s", scraper.name, exc)
            failed_supermarkets.append(scraper.name)

    return {"inserted": inserted, "missing": missing, "failed_supermarkets": failed_supermarkets}


def export_json_csv(conn, prices_json_path: str, prices_csv_path: str, index_json_path: str) -> None:
    rows = db.read_prices(conn)
    with open(prices_json_path, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)

    import csv

    fieldnames = list(rows[0].keys()) if rows else [
        "id", "date", "supermarket", "product_key", "product_name", "price", "url", "is_outlier",
    ]
    with open(prices_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    # Separate from prices.json (raw price rows, the dataset proper) because
    # the dashboard (Task 21) only needs the much smaller index_daily series —
    # fetching the full price history client-side would be wasteful.
    index_rows = db.read_index_daily(conn)
    with open(index_json_path, "w", encoding="utf-8") as f:
        json.dump({"index_daily": index_rows}, f, ensure_ascii=False, indent=2)


def export_latest_prices_snapshot(conn, path: str) -> None:
    """Write a small snapshot of only the most recent date's prices — bounded
    size forever (unlike prices.json, which grows with the full history), so
    it's safe to commit to git for the dashboard's price-dispersion chart to
    read directly (GitHub Release assets don't send CORS headers; committed
    files served via raw.githubusercontent.com do).
    """
    rows = db.read_prices(conn)
    if not rows:
        latest_date = None
        snapshot = []
    else:
        latest_date = max(r["date"] for r in rows)
        snapshot = [r for r in rows if r["date"] == latest_date and not r["is_outlier"]]

    with open(path, "w", encoding="utf-8") as f:
        json.dump({"date": latest_date, "prices": snapshot}, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    import datetime

    from scrapers.arete import AreteScraper
    from scrapers.biggie import BiggieScraper
    from scrapers.casa_rica import CasaRicaScraper
    from scrapers.grutter import GrutterScraper
    from scrapers.los_jardines import LosJardinesScraper
    from scrapers.real import RealScraper
    from scrapers.salemma import SalemmaScraper
    from scrapers.stock import StockScraper
    from scrapers.superseis import SuperseisScraper

    with open("basket.json", encoding="utf-8") as f:
        basket_data = json.load(f)

    all_scrapers = [
        SuperseisScraper(), StockScraper(), CasaRicaScraper(), SalemmaScraper(),
        BiggieScraper(), AreteScraper(), GrutterScraper(), LosJardinesScraper(), RealScraper(),
    ]

    conn = db.connect("prices.db")
    db.init_schema(conn)
    today = datetime.date.today().isoformat()

    summary = run(conn, basket_data, all_scrapers, today)
    log.info("run summary: %s", summary)

    index.compute_aggregate_index(conn, basket_data, [s.name for s in all_scrapers])
    export_json_csv(conn, "prices.json", "prices.csv", "index.json")
    export_latest_prices_snapshot(conn, "latest_prices.json")
