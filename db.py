import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS prices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    supermarket TEXT NOT NULL,
    product_key TEXT NOT NULL,
    product_name TEXT NOT NULL,
    price REAL NOT NULL,
    url TEXT NOT NULL,
    is_outlier INTEGER NOT NULL DEFAULT 0,
    UNIQUE(date, supermarket, product_key)
);

CREATE TABLE IF NOT EXISTS index_daily (
    date TEXT NOT NULL,
    supermarket TEXT NOT NULL,
    value REAL NOT NULL,
    UNIQUE(date, supermarket)
);
"""


def connect(path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()


def insert_price(
    conn: sqlite3.Connection,
    date: str,
    supermarket: str,
    product_key: str,
    product_name: str,
    price: float,
    url: str,
    is_outlier: bool = False,
) -> None:
    conn.execute(
        """INSERT OR REPLACE INTO prices
           (date, supermarket, product_key, product_name, price, url, is_outlier)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (date, supermarket, product_key, product_name, price, url, int(is_outlier)),
    )
    conn.commit()


def read_prices(
    conn: sqlite3.Connection,
    product_key: str | None = None,
    supermarket: str | None = None,
) -> list[dict]:
    query = "SELECT * FROM prices WHERE 1=1"
    params: list[str] = []
    if product_key is not None:
        query += " AND product_key = ?"
        params.append(product_key)
    if supermarket is not None:
        query += " AND supermarket = ?"
        params.append(supermarket)
    query += " ORDER BY date ASC"
    return [dict(row) for row in conn.execute(query, params)]


def write_index_daily(conn: sqlite3.Connection, date: str, supermarket: str, value: float) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO index_daily (date, supermarket, value) VALUES (?, ?, ?)",
        (date, supermarket, value),
    )
    conn.commit()


def read_index_daily(conn: sqlite3.Connection, supermarket: str | None = None) -> list[dict]:
    query = "SELECT * FROM index_daily"
    params: list[str] = []
    if supermarket is not None:
        query += " WHERE supermarket = ?"
        params.append(supermarket)
    query += " ORDER BY date ASC"
    return [dict(row) for row in conn.execute(query, params)]
