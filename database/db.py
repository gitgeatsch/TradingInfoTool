"""SQLite Verwaltung: Verbindung, automatische Initialisierung, CRUD."""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from database.models import Holding, PriceSnapshot

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "tradinginfotool.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS holdings (
    symbol          TEXT PRIMARY KEY,
    quantity        REAL NOT NULL DEFAULT 0,
    updated_at      TEXT NOT NULL,
    source          TEXT NOT NULL DEFAULT 'import'
);

CREATE TABLE IF NOT EXISTS price_cache (
    symbol          TEXT NOT NULL,
    coingecko_id    TEXT NOT NULL,
    price_usd       REAL,
    price_eur       REAL,
    market_cap_usd  REAL,
    volume_24h_usd  REAL,
    change_24h_pct  REAL,
    fetched_at      TEXT NOT NULL,
    PRIMARY KEY (symbol, fetched_at)
);

CREATE TABLE IF NOT EXISTS meta (
    key             TEXT PRIMARY KEY,
    value           TEXT
);
"""


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(_SCHEMA)
    conn.commit()


def is_first_run(conn: sqlite3.Connection) -> bool:
    row = conn.execute(
        "SELECT value FROM meta WHERE key = 'holdings_imported_at'"
    ).fetchone()
    return row is None or row["value"] is None


def mark_holdings_imported(conn: sqlite3.Connection) -> None:
    conn.execute(
        "INSERT INTO meta (key, value) VALUES ('holdings_imported_at', ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (_now_iso(),),
    )
    conn.commit()


def upsert_holding(
    conn: sqlite3.Connection, symbol: str, quantity: float, source: str = "import"
) -> None:
    conn.execute(
        "INSERT INTO holdings (symbol, quantity, updated_at, source) VALUES (?, ?, ?, ?) "
        "ON CONFLICT(symbol) DO UPDATE SET "
        "quantity = excluded.quantity, updated_at = excluded.updated_at, source = excluded.source",
        (symbol, quantity, _now_iso(), source),
    )
    conn.commit()


def get_all_holdings(conn: sqlite3.Connection) -> list[Holding]:
    rows = conn.execute(
        "SELECT symbol, quantity, updated_at, source FROM holdings"
    ).fetchall()
    return [Holding(**dict(row)) for row in rows]


def insert_price_snapshot(conn: sqlite3.Connection, snap: PriceSnapshot) -> None:
    conn.execute(
        "INSERT INTO price_cache "
        "(symbol, coingecko_id, price_usd, price_eur, market_cap_usd, volume_24h_usd, "
        "change_24h_pct, fetched_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (
            snap.symbol,
            snap.coingecko_id,
            snap.price_usd,
            snap.price_eur,
            snap.market_cap_usd,
            snap.volume_24h_usd,
            snap.change_24h_pct,
            snap.fetched_at,
        ),
    )
    conn.commit()


def get_latest_prices(conn: sqlite3.Connection) -> dict[str, PriceSnapshot]:
    rows = conn.execute(
        """
        SELECT p.symbol, p.coingecko_id, p.price_usd, p.price_eur, p.market_cap_usd,
               p.volume_24h_usd, p.change_24h_pct, p.fetched_at
        FROM price_cache p
        INNER JOIN (
            SELECT symbol, MAX(fetched_at) AS max_fetched_at
            FROM price_cache
            GROUP BY symbol
        ) latest
        ON p.symbol = latest.symbol AND p.fetched_at = latest.max_fetched_at
        """
    ).fetchall()
    return {row["symbol"]: PriceSnapshot(**dict(row)) for row in rows}
