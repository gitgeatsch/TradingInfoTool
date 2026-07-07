"""SQLite Verwaltung: Verbindung, automatische Initialisierung, CRUD."""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from database.models import Holding, MacroSnapshot, OhlcPoint, PriceHistoryPoint, PriceSnapshot, Signal

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

CREATE TABLE IF NOT EXISTS price_history (
    coingecko_id    TEXT NOT NULL,
    date            TEXT NOT NULL,
    price_usd       REAL,
    price_eur       REAL,
    fetched_at      TEXT NOT NULL,
    PRIMARY KEY (coingecko_id, date)
);

CREATE TABLE IF NOT EXISTS price_history_ohlc (
    symbol          TEXT NOT NULL,
    currency        TEXT NOT NULL,
    date            TEXT NOT NULL,
    open            REAL NOT NULL,
    high            REAL NOT NULL,
    low             REAL NOT NULL,
    close           REAL NOT NULL,
    volume          REAL NOT NULL,
    fetched_at      TEXT NOT NULL,
    PRIMARY KEY (symbol, currency, date)
);

CREATE TABLE IF NOT EXISTS macro_snapshot (
    date                TEXT PRIMARY KEY,
    btc_dominance_pct   REAL,
    fear_greed_value    INTEGER,
    fear_greed_label    TEXT,
    fetched_at          TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS signals (
    id                          INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol                      TEXT NOT NULL,
    created_at                  TEXT NOT NULL,
    pipeline_version            TEXT NOT NULL DEFAULT '1',
    action                      TEXT NOT NULL,
    confidence_pct              REAL,
    short_reasoning             TEXT,
    long_reasoning_technisch    TEXT,
    long_reasoning_fundamental  TEXT,
    long_reasoning_makro        TEXT,
    position_size_usd           REAL,
    position_size_eur           REAL,
    position_size_note          TEXT,
    entry_usd                   REAL,
    entry_eur                   REAL,
    stop_loss_usd                REAL,
    stop_loss_eur                REAL,
    take_profit_usd              REAL,
    take_profit_eur              REAL,
    holding_duration              TEXT,
    holding_duration_reason       TEXT,
    key_risks_text                 TEXT,
    regime                          TEXT,
    regime_source                   TEXT,
    forecast_bull_text              TEXT,
    forecast_bull_prob_pct          REAL,
    forecast_base_text              TEXT,
    forecast_base_prob_pct          REAL,
    forecast_bear_text              TEXT,
    forecast_bear_prob_pct          REAL,
    tauschen_target_symbol           TEXT,
    gate_passed                       INTEGER NOT NULL,
    gate_reason                       TEXT,
    risk_veto                          INTEGER NOT NULL DEFAULT 0,
    risk_veto_reason                   TEXT,
    facts_json                          TEXT NOT NULL,
    groq_raw_response                   TEXT,
    groq_model                          TEXT
);
CREATE INDEX IF NOT EXISTS idx_signals_symbol_created ON signals(symbol, created_at);
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


def is_history_first_run(conn: sqlite3.Connection) -> bool:
    row = conn.execute(
        "SELECT value FROM meta WHERE key = 'history_backfilled_at'"
    ).fetchone()
    return row is None or row["value"] is None


def mark_history_backfilled(conn: sqlite3.Connection) -> None:
    conn.execute(
        "INSERT INTO meta (key, value) VALUES ('history_backfilled_at', ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (_now_iso(),),
    )
    conn.commit()


def upsert_price_history_points(
    conn: sqlite3.Connection, points: list[PriceHistoryPoint]
) -> None:
    conn.executemany(
        "INSERT INTO price_history (coingecko_id, date, price_usd, price_eur, fetched_at) "
        "VALUES (?, ?, ?, ?, ?) "
        "ON CONFLICT(coingecko_id, date) DO UPDATE SET "
        "price_usd = excluded.price_usd, price_eur = excluded.price_eur, "
        "fetched_at = excluded.fetched_at",
        [
            (p.coingecko_id, p.date, p.price_usd, p.price_eur, p.fetched_at)
            for p in points
        ],
    )
    conn.commit()


def get_price_history(
    conn: sqlite3.Connection, coingecko_id: str, min_date: str | None = None
) -> list[PriceHistoryPoint]:
    if min_date is not None:
        rows = conn.execute(
            "SELECT coingecko_id, date, price_usd, price_eur, fetched_at "
            "FROM price_history WHERE coingecko_id = ? AND date >= ? ORDER BY date ASC",
            (coingecko_id, min_date),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT coingecko_id, date, price_usd, price_eur, fetched_at "
            "FROM price_history WHERE coingecko_id = ? ORDER BY date ASC",
            (coingecko_id,),
        ).fetchall()
    return [PriceHistoryPoint(**dict(row)) for row in rows]


def get_last_history_date(conn: sqlite3.Connection, coingecko_id: str) -> str | None:
    row = conn.execute(
        "SELECT MAX(date) AS max_date FROM price_history WHERE coingecko_id = ?",
        (coingecko_id,),
    ).fetchone()
    return row["max_date"] if row else None


def is_ohlc_first_run(conn: sqlite3.Connection) -> bool:
    row = conn.execute(
        "SELECT value FROM meta WHERE key = 'ohlc_backfilled_at'"
    ).fetchone()
    return row is None or row["value"] is None


def mark_ohlc_backfilled(conn: sqlite3.Connection) -> None:
    conn.execute(
        "INSERT INTO meta (key, value) VALUES ('ohlc_backfilled_at', ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (_now_iso(),),
    )
    conn.commit()


def upsert_ohlc_points(conn: sqlite3.Connection, points: list[OhlcPoint]) -> None:
    conn.executemany(
        "INSERT INTO price_history_ohlc "
        "(symbol, currency, date, open, high, low, close, volume, fetched_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?) "
        "ON CONFLICT(symbol, currency, date) DO UPDATE SET "
        "open = excluded.open, high = excluded.high, low = excluded.low, "
        "close = excluded.close, volume = excluded.volume, fetched_at = excluded.fetched_at",
        [
            (p.symbol, p.currency, p.date, p.open, p.high, p.low, p.close, p.volume, p.fetched_at)
            for p in points
        ],
    )
    conn.commit()


def get_ohlc_history(
    conn: sqlite3.Connection, symbol: str, currency: str, min_date: str | None = None
) -> list[OhlcPoint]:
    if min_date is not None:
        rows = conn.execute(
            "SELECT symbol, currency, date, open, high, low, close, volume, fetched_at "
            "FROM price_history_ohlc WHERE symbol = ? AND currency = ? AND date >= ? "
            "ORDER BY date ASC",
            (symbol, currency, min_date),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT symbol, currency, date, open, high, low, close, volume, fetched_at "
            "FROM price_history_ohlc WHERE symbol = ? AND currency = ? ORDER BY date ASC",
            (symbol, currency),
        ).fetchall()
    return [OhlcPoint(**dict(row)) for row in rows]


def get_last_ohlc_date(conn: sqlite3.Connection, symbol: str, currency: str) -> str | None:
    row = conn.execute(
        "SELECT MAX(date) AS max_date FROM price_history_ohlc WHERE symbol = ? AND currency = ?",
        (symbol, currency),
    ).fetchone()
    return row["max_date"] if row else None


def upsert_macro_snapshot(conn: sqlite3.Connection, snap: MacroSnapshot) -> None:
    conn.execute(
        "INSERT INTO macro_snapshot (date, btc_dominance_pct, fear_greed_value, "
        "fear_greed_label, fetched_at) VALUES (?, ?, ?, ?, ?) "
        "ON CONFLICT(date) DO UPDATE SET "
        "btc_dominance_pct = excluded.btc_dominance_pct, "
        "fear_greed_value = excluded.fear_greed_value, "
        "fear_greed_label = excluded.fear_greed_label, fetched_at = excluded.fetched_at",
        (snap.date, snap.btc_dominance_pct, snap.fear_greed_value, snap.fear_greed_label, snap.fetched_at),
    )
    conn.commit()


def get_macro_snapshot_history(conn: sqlite3.Connection, min_date: str | None = None) -> list[MacroSnapshot]:
    if min_date is not None:
        rows = conn.execute(
            "SELECT date, btc_dominance_pct, fear_greed_value, fear_greed_label, fetched_at "
            "FROM macro_snapshot WHERE date >= ? ORDER BY date ASC",
            (min_date,),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT date, btc_dominance_pct, fear_greed_value, fear_greed_label, fetched_at "
            "FROM macro_snapshot ORDER BY date ASC"
        ).fetchall()
    return [MacroSnapshot(**dict(row)) for row in rows]


def get_latest_macro_snapshot(conn: sqlite3.Connection) -> MacroSnapshot | None:
    row = conn.execute(
        "SELECT date, btc_dominance_pct, fear_greed_value, fear_greed_label, fetched_at "
        "FROM macro_snapshot ORDER BY date DESC LIMIT 1"
    ).fetchone()
    return MacroSnapshot(**dict(row)) if row else None


_SIGNAL_COLUMNS = (
    "symbol", "created_at", "pipeline_version", "action", "confidence_pct",
    "short_reasoning", "long_reasoning_technisch", "long_reasoning_fundamental",
    "long_reasoning_makro", "position_size_usd", "position_size_eur", "position_size_note",
    "entry_usd", "entry_eur", "stop_loss_usd", "stop_loss_eur", "take_profit_usd",
    "take_profit_eur", "holding_duration", "holding_duration_reason", "key_risks_text",
    "regime", "regime_source", "forecast_bull_text", "forecast_bull_prob_pct",
    "forecast_base_text", "forecast_base_prob_pct", "forecast_bear_text",
    "forecast_bear_prob_pct", "tauschen_target_symbol", "gate_passed", "gate_reason",
    "risk_veto", "risk_veto_reason", "facts_json", "groq_raw_response", "groq_model",
)


def insert_signal(conn: sqlite3.Connection, signal: Signal) -> int:
    placeholders = ", ".join("?" for _ in _SIGNAL_COLUMNS)
    values = [
        int(getattr(signal, col)) if col in ("gate_passed", "risk_veto") else getattr(signal, col)
        for col in _SIGNAL_COLUMNS
    ]
    cursor = conn.execute(
        f"INSERT INTO signals ({', '.join(_SIGNAL_COLUMNS)}) VALUES ({placeholders})",
        values,
    )
    conn.commit()
    return cursor.lastrowid


def _row_to_signal(row: sqlite3.Row) -> Signal:
    data = dict(row)
    data["gate_passed"] = bool(data["gate_passed"])
    data["risk_veto"] = bool(data["risk_veto"])
    return Signal(**data)


def get_latest_signal(conn: sqlite3.Connection, symbol: str) -> Signal | None:
    row = conn.execute(
        "SELECT * FROM signals WHERE symbol = ? ORDER BY created_at DESC LIMIT 1",
        (symbol,),
    ).fetchone()
    return _row_to_signal(row) if row else None


def get_signal_history(conn: sqlite3.Connection, symbol: str, limit: int = 20) -> list[Signal]:
    rows = conn.execute(
        "SELECT * FROM signals WHERE symbol = ? ORDER BY created_at DESC LIMIT ?",
        (symbol, limit),
    ).fetchall()
    return [_row_to_signal(row) for row in rows]


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
