import db
import run_daily
from scrapers.base import ProductMatch, Scraper

BASKET = [
    {"product_key": "arroz", "nombre_canonico": "Arroz", "bcp_category": "cereales",
     "weight": 1.0, "queries": {"good": "arroz", "bad": "arroz"}},
]


class GoodScraper(Scraper):
    name = "good"

    def search(self, query):
        return [ProductMatch(name="Arroz", price=6500.0, url="https://good/p/1")]


class BadScraper(Scraper):
    name = "bad"

    def search(self, query):
        raise ConnectionError("site is down")


def test_run_daily_inserts_and_survives_one_site_failing(tmp_path):
    conn = db.connect(str(tmp_path / "t.db"))
    db.init_schema(conn)

    summary = run_daily.run(conn, BASKET, [GoodScraper(), BadScraper()], date="2026-07-22")

    assert summary["inserted"] == 1
    assert summary["failed_supermarkets"] == ["bad"]

    rows = db.read_prices(conn, product_key="arroz", supermarket="good")
    assert len(rows) == 1
    assert rows[0]["price"] == 6500.0


def test_run_daily_recovers_after_one_item_fails_mid_basket():
    # Regression test for a real bug: a scraper timing out on one item used
    # to abort every remaining item in its basket for that scraper (the
    # try/except wrapped the whole per-scraper loop). Confirmed live:
    # Grütter timed out on item 6 of 28, and items 7-28 were silently never
    # attempted for that entire run.
    two_item_basket = [
        {"product_key": "arroz", "nombre_canonico": "Arroz", "bcp_category": "cereales",
         "weight": 0.5, "queries": {"flaky": "arroz"}},
        {"product_key": "aceite", "nombre_canonico": "Aceite", "bcp_category": "aceites",
         "weight": 0.5, "queries": {"flaky": "aceite"}},
    ]

    class FlakyOnFirstItemScraper(Scraper):
        name = "flaky"
        calls = 0

        def search(self, query):
            self.calls += 1
            if self.calls == 1:
                raise TimeoutError("read timed out")
            return [ProductMatch(name="Aceite", price=12000.0, url="https://flaky/p/2")]

    conn = db.connect(":memory:")
    db.init_schema(conn)
    scraper = FlakyOnFirstItemScraper()

    summary = run_daily.run(conn, two_item_basket, [scraper], date="2026-07-22")

    assert scraper.calls == 2  # both items were attempted, not just the first
    assert summary["failed_supermarkets"] == ["flaky"]
    rows = db.read_prices(conn, product_key="aceite", supermarket="flaky")
    assert len(rows) == 1
    assert rows[0]["price"] == 12000.0
    # The failed item leaves no row at all (not a false "no match" delete,
    # not a fabricated insert) — its prior state, if any, is untouched.
    assert db.read_prices(conn, product_key="arroz", supermarket="flaky") == []


def test_run_daily_leaves_existing_row_untouched_when_search_errors(tmp_path):
    conn = db.connect(str(tmp_path / "t.db"))
    db.init_schema(conn)
    db.insert_price(conn, "2026-07-22", "flaky", "arroz", "Arroz (de ayer)", 6400.0, "https://flaky/p/old")

    class AlwaysFailsScraper(Scraper):
        name = "flaky"

        def search(self, query):
            raise TimeoutError("read timed out")

    run_daily.run(conn, BASKET, [AlwaysFailsScraper()], date="2026-07-22")

    rows = db.read_prices(conn, product_key="arroz", supermarket="flaky")
    assert len(rows) == 1
    assert rows[0]["price"] == 6400.0  # untouched, not deleted and not overwritten


class NoMatchScraper(Scraper):
    name = "good"

    def search(self, query):
        # A completely unrelated result — select_best_match must reject it.
        return [ProductMatch(name="Detergente lavavajilla 500ml", price=8000.0, url="https://good/p/9")]


def test_run_daily_clears_a_stale_match_when_rerun_finds_none(tmp_path):
    conn = db.connect(str(tmp_path / "t.db"))
    db.init_schema(conn)
    # Simulate an earlier run (before a matching fix landed) having wrongly
    # recorded a match for this exact date/supermarket/product_key.
    db.insert_price(conn, "2026-07-22", "good", "arroz", "Detergente lavavajilla 500ml", 8000.0, "https://good/p/9")

    summary = run_daily.run(conn, BASKET, [NoMatchScraper()], date="2026-07-22")

    assert summary["missing"] == 1
    assert db.read_prices(conn, product_key="arroz", supermarket="good") == []


def test_export_json_csv_writes_csv_header_even_with_no_rows(tmp_path):
    conn = db.connect(str(tmp_path / "t.db"))
    db.init_schema(conn)
    csv_path = tmp_path / "prices.csv"
    json_path = tmp_path / "prices.json"
    index_path = tmp_path / "index.json"
    run_daily.export_json_csv(conn, str(json_path), str(csv_path), str(index_path))
    assert csv_path.exists()
    content = csv_path.read_text(encoding="utf-8")
    assert "date" in content  # header present
    assert content.count("\n") == 1  # header only, no data rows


def test_export_latest_prices_snapshot_keeps_only_latest_date_and_excludes_outliers(tmp_path):
    import json

    conn = db.connect(str(tmp_path / "t.db"))
    db.init_schema(conn)
    db.insert_price(conn, "2026-07-21", "good", "arroz", "Arroz", 6000.0, "u1")
    db.insert_price(conn, "2026-07-22", "good", "arroz", "Arroz", 6500.0, "u2")
    db.insert_price(conn, "2026-07-22", "good", "aceite", "Aceite", 12000.0, "u3")
    db.insert_price(conn, "2026-07-22", "bad", "arroz", "Arroz", 99999.0, "u4", is_outlier=True)

    out_path = tmp_path / "latest_prices.json"
    run_daily.export_latest_prices_snapshot(conn, str(out_path))

    data = json.loads(out_path.read_text(encoding="utf-8"))
    assert data["date"] == "2026-07-22"
    product_keys = sorted(r["product_key"] for r in data["prices"])
    assert product_keys == ["aceite", "arroz"]
    assert all(r["supermarket"] != "bad" for r in data["prices"])  # outlier row excluded


def test_export_latest_prices_snapshot_handles_empty_db(tmp_path):
    import json

    conn = db.connect(str(tmp_path / "t.db"))
    db.init_schema(conn)
    out_path = tmp_path / "latest_prices.json"
    run_daily.export_latest_prices_snapshot(conn, str(out_path))
    data = json.loads(out_path.read_text(encoding="utf-8"))
    assert data == {"date": None, "prices": []}
