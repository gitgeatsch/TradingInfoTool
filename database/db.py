"""SQLite Verwaltung: Verbindung, automatische Initialisierung, CRUD."""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from database.models import (
    Holding,
    MacroSnapshot,
    MarktscanCandidate,
    OhlcPoint,
    PriceHistoryPoint,
    PriceSnapshot,
    Signal,
)

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
    coingecko_id    TEXT,
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
-- FRED/PBoC-Spalten (fed_funds_rate etc.) werden per ALTER TABLE in
-- _migrate_macro_snapshot_columns() nachgezogen, nicht hier - macro_snapshot
-- existiert bereits in bestehenden Installationen, CREATE TABLE IF NOT EXISTS greift
-- dort nicht mehr (siehe init_db()).

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
    groq_model                          TEXT,
    umgesetzt                            INTEGER,
    umgesetzt_am                          TEXT,
    umgesetzt_menge                        REAL,
    umgesetzt_preis_usd                     REAL
);
CREATE INDEX IF NOT EXISTS idx_signals_symbol_created ON signals(symbol, created_at);

CREATE TABLE IF NOT EXISTS marktscan_candidates (
    id                          INTEGER PRIMARY KEY AUTOINCREMENT,
    coingecko_id                TEXT NOT NULL,
    symbol                      TEXT NOT NULL,
    name                        TEXT NOT NULL,
    discovered_at                TEXT NOT NULL,
    discovery_source              TEXT NOT NULL,
    scan_run_id                    TEXT NOT NULL,
    filter_a_bestanden              INTEGER NOT NULL,
    tier                             TEXT,
    market_cap_usd                   REAL,
    volume_24h_usd                    REAL,
    vol_marktkap_ratio                 REAL,
    alter_tage_geschaetzt               INTEGER,
    alter_tage_quelle                    TEXT,
    filter_a_begruendung                  TEXT,
    bitpanda_gelistet                      INTEGER,
    price_usd                              REAL,
    price_eur                               REAL,
    change_24h_pct                           REAL,
    score_technik                             REAL,
    score_fundamental                          REAL,
    score_momentum                              REAL,
    score_kontext_makro                          REAL,
    signale_technik_json                          TEXT,
    signale_fundamental_json                       TEXT,
    signale_momentum_json                           TEXT,
    signale_kontext_json                             TEXT,
    score_gesamt                                      REAL,
    gewichte_json                                      TEXT,
    regime_bei_scan                                     TEXT,
    einstufung                                           TEXT,
    einstufung_begruendung                                TEXT,
    small_cap_budget_hinweis                               TEXT,
    groq_kurzbegruendung                                    TEXT,
    groq_langbegruendung_json                                TEXT,
    groq_generiert_am                                         TEXT,
    status                                                     TEXT NOT NULL DEFAULT 'neu',
    status_geaendert_am                                         TEXT,
    UNIQUE(coingecko_id, scan_run_id)
);
CREATE INDEX IF NOT EXISTS idx_marktscan_status ON marktscan_candidates(status, discovered_at);
"""


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


_MACRO_SNAPSHOT_NEW_COLUMNS = (
    "fed_funds_rate", "m2_geldmenge", "cpi_headline", "cpi_core", "ezb_einlagensatz",
    "ezb_hauptrefinanzierung", "ezb_spitzenrefinanzierung", "ism_ersatz_philly_fed",
    "boj_tagesgeldsatz", "bok_diskontsatz", "pboc_lpr_1y", "pboc_lpr_5y",
    "m2_eurozone", "m2_china", "m2_japan",
)


def _migrate_macro_snapshot_columns(conn: sqlite3.Connection) -> None:
    """Leichtgewichtige Migration: macro_snapshot existierte bereits vor den
    FRED/PBoC-Spalten (Phase 3, 2026-07-08 Folge-Slice) - CREATE TABLE IF NOT EXISTS
    greift bei bereits existierenden Tabellen nicht, daher ALTER TABLE nachziehen.
    Alle neuen Spalten sind nullable REAL, daher unkritisch fuer Bestandsdaten."""
    existing = {row["name"] for row in conn.execute("PRAGMA table_info(macro_snapshot)")}
    for column in _MACRO_SNAPSHOT_NEW_COLUMNS:
        if column not in existing:
            conn.execute(f"ALTER TABLE macro_snapshot ADD COLUMN {column} REAL")
    conn.commit()


def _migrate_marktscan_candidates_columns(conn: sqlite3.Connection) -> None:
    """Wie _migrate_macro_snapshot_columns(): marktscan_candidates existierte bereits
    vor der bitpanda_gelistet-Spalte (2026-07-09, Nutzer-Wunsch Handelsboersen-Check)."""
    existing = {row["name"] for row in conn.execute("PRAGMA table_info(marktscan_candidates)")}
    if "bitpanda_gelistet" not in existing:
        conn.execute("ALTER TABLE marktscan_candidates ADD COLUMN bitpanda_gelistet INTEGER")
    conn.commit()


_SIGNAL_UMSETZUNG_NEW_COLUMNS = {
    "umgesetzt": "INTEGER", "umgesetzt_am": "TEXT", "umgesetzt_menge": "REAL",
    "umgesetzt_preis_usd": "REAL",
}


def _migrate_signal_umsetzung_columns(conn: sqlite3.Connection) -> None:
    """Wie _migrate_macro_snapshot_columns(): signals existierte bereits vor den
    Umsetzungs-Rueckmeldung-Spalten (2026-07-09, Nutzer-Idee vom 2026-07-07)."""
    existing = {row["name"] for row in conn.execute("PRAGMA table_info(signals)")}
    for column, sql_type in _SIGNAL_UMSETZUNG_NEW_COLUMNS.items():
        if column not in existing:
            conn.execute(f"ALTER TABLE signals ADD COLUMN {column} {sql_type}")
    conn.commit()


_SIGNAL_RANGE_KRITERIUM_NEW_COLUMNS = {
    "entry_usd_von": "REAL", "entry_usd_bis": "REAL",
    "entry_eur_von": "REAL", "entry_eur_bis": "REAL",
    "stop_loss_usd_von": "REAL", "stop_loss_usd_bis": "REAL",
    "stop_loss_eur_von": "REAL", "stop_loss_eur_bis": "REAL",
    "take_profit_usd_von": "REAL", "take_profit_usd_bis": "REAL",
    "take_profit_eur_von": "REAL", "take_profit_eur_bis": "REAL",
    "top_grund_1_kategorie": "TEXT", "top_grund_1_text": "TEXT",
    "top_grund_2_kategorie": "TEXT", "top_grund_2_text": "TEXT",
    "top_grund_3_kategorie": "TEXT", "top_grund_3_text": "TEXT",
    "top_grund_4_kategorie": "TEXT", "top_grund_4_text": "TEXT",
    "top_grund_5_kategorie": "TEXT", "top_grund_5_text": "TEXT",
    "halte_kriterium_bucket": "TEXT",
    "halte_kriterium_ziel_preis_usd": "REAL",
    "halte_kriterium_ziel_preis_eur": "REAL",
    "halte_kriterium_ziel_datum": "TEXT",
    "halte_kriterium_bedingung_text": "TEXT",
    "halte_kriterium_reasoning": "TEXT",
}


def _migrate_signal_range_kriterium_columns(conn: sqlite3.Connection) -> None:
    """Wie _migrate_signal_umsetzung_columns(): signals existierte bereits vor den
    Entry/Stop/Take-Kurszonen- und Halte-Kriterium-Spalten (2026-07-10, Nutzer-Wunsch
    von/bis-Ranges statt Einzelwerte + strukturiertes Halte-Kriterium)."""
    existing = {row["name"] for row in conn.execute("PRAGMA table_info(signals)")}
    for column, sql_type in _SIGNAL_RANGE_KRITERIUM_NEW_COLUMNS.items():
        if column not in existing:
            conn.execute(f"ALTER TABLE signals ADD COLUMN {column} {sql_type}")
    conn.commit()


def _migrate_price_cache_nullable_coingecko_id(conn: sqlite3.Connection) -> None:
    """price_cache.coingecko_id war urspruenglich NOT NULL (reines Krypto-Schema) -
    fuer Multi-Asset-Tracking (Nutzer-Idee 2026-07-09, Aktien/ETF/Rohstoffe ohne
    CoinGecko-ID) muss die Spalte NULL erlauben. SQLite kennt kein ALTER COLUMN,
    daher Tabellen-Neubau (Standard-SQLite-Migrationsmuster): neue Tabelle mit
    korrigiertem Schema anlegen, Daten kopieren, alte Tabelle ersetzen. Idempotent -
    ueberspringt, wenn die Spalte bereits NULL erlaubt (z.B. frische DB, _SCHEMA
    liefert das direkt)."""
    columns = conn.execute("PRAGMA table_info(price_cache)").fetchall()
    coingecko_id_col = next(c for c in columns if c["name"] == "coingecko_id")
    if coingecko_id_col["notnull"] == 0:
        return

    conn.execute(
        """
        CREATE TABLE price_cache_new (
            symbol          TEXT NOT NULL,
            coingecko_id    TEXT,
            price_usd       REAL,
            price_eur       REAL,
            market_cap_usd  REAL,
            volume_24h_usd  REAL,
            change_24h_pct  REAL,
            fetched_at      TEXT NOT NULL,
            PRIMARY KEY (symbol, fetched_at)
        )
        """
    )
    conn.execute("INSERT INTO price_cache_new SELECT * FROM price_cache")
    conn.execute("DROP TABLE price_cache")
    conn.execute("ALTER TABLE price_cache_new RENAME TO price_cache")
    conn.commit()


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(_SCHEMA)
    conn.commit()
    _migrate_macro_snapshot_columns(conn)
    _migrate_marktscan_candidates_columns(conn)
    _migrate_signal_umsetzung_columns(conn)
    _migrate_signal_range_kriterium_columns(conn)
    _migrate_price_cache_nullable_coingecko_id(conn)


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


_MACRO_SNAPSHOT_COLUMNS = (
    "date", "btc_dominance_pct", "fear_greed_value", "fear_greed_label", "fetched_at",
) + _MACRO_SNAPSHOT_NEW_COLUMNS


def upsert_macro_snapshot(conn: sqlite3.Connection, snap: MacroSnapshot) -> None:
    """P-10: mehrere Pipeline-Laeufe am selben Tag duerfen sich nicht gegenseitig
    Werte loeschen, nur weil ein einzelner Fetch an diesem Lauf fehlgeschlagen ist
    (z.B. FRED_API_KEY erst spaeter gesetzt, oder ein einzelner Provider kurzzeitig
    down) - COALESCE behaelt den zuletzt bekannten Wert, wenn der neue NULL ist.
    `fetched_at` wird immer aktualisiert (Zeitpunkt des letzten Schreibversuchs)."""
    placeholders = ", ".join("?" for _ in _MACRO_SNAPSHOT_COLUMNS)
    update_clause = ", ".join(
        f"{col} = excluded.{col}" if col == "fetched_at"
        else f"{col} = COALESCE(excluded.{col}, macro_snapshot.{col})"
        for col in _MACRO_SNAPSHOT_COLUMNS
        if col != "date"
    )
    values = [getattr(snap, col) for col in _MACRO_SNAPSHOT_COLUMNS]
    conn.execute(
        f"INSERT INTO macro_snapshot ({', '.join(_MACRO_SNAPSHOT_COLUMNS)}) "
        f"VALUES ({placeholders}) ON CONFLICT(date) DO UPDATE SET {update_clause}",
        values,
    )
    conn.commit()


def get_macro_snapshot_history(conn: sqlite3.Connection, min_date: str | None = None) -> list[MacroSnapshot]:
    columns = ", ".join(_MACRO_SNAPSHOT_COLUMNS)
    if min_date is not None:
        rows = conn.execute(
            f"SELECT {columns} FROM macro_snapshot WHERE date >= ? ORDER BY date ASC",
            (min_date,),
        ).fetchall()
    else:
        rows = conn.execute(f"SELECT {columns} FROM macro_snapshot ORDER BY date ASC").fetchall()
    return [MacroSnapshot(**dict(row)) for row in rows]


def get_latest_macro_snapshot(conn: sqlite3.Connection) -> MacroSnapshot | None:
    columns = ", ".join(_MACRO_SNAPSHOT_COLUMNS)
    row = conn.execute(
        f"SELECT {columns} FROM macro_snapshot ORDER BY date DESC LIMIT 1"
    ).fetchone()
    return MacroSnapshot(**dict(row)) if row else None


_SIGNAL_COLUMNS = (
    "symbol", "created_at", "pipeline_version", "action", "confidence_pct",
    "short_reasoning", "long_reasoning_technisch", "long_reasoning_fundamental",
    "long_reasoning_makro", "position_size_usd", "position_size_eur", "position_size_note",
    "entry_usd", "entry_eur", "stop_loss_usd", "stop_loss_eur", "take_profit_usd",
    "take_profit_eur", "entry_usd_von", "entry_usd_bis", "entry_eur_von", "entry_eur_bis",
    "stop_loss_usd_von", "stop_loss_usd_bis", "stop_loss_eur_von", "stop_loss_eur_bis",
    "take_profit_usd_von", "take_profit_usd_bis", "take_profit_eur_von", "take_profit_eur_bis",
    "holding_duration", "holding_duration_reason",
    "halte_kriterium_bucket", "halte_kriterium_ziel_preis_usd", "halte_kriterium_ziel_preis_eur",
    "halte_kriterium_ziel_datum", "halte_kriterium_bedingung_text", "halte_kriterium_reasoning",
    "top_grund_1_kategorie", "top_grund_1_text", "top_grund_2_kategorie", "top_grund_2_text",
    "top_grund_3_kategorie", "top_grund_3_text", "top_grund_4_kategorie", "top_grund_4_text",
    "top_grund_5_kategorie", "top_grund_5_text",
    "key_risks_text", "regime", "regime_source", "forecast_bull_text", "forecast_bull_prob_pct",
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
    if data["umgesetzt"] is not None:
        data["umgesetzt"] = bool(data["umgesetzt"])
    return Signal(**data)


def get_latest_signal(conn: sqlite3.Connection, symbol: str) -> Signal | None:
    row = conn.execute(
        "SELECT * FROM signals WHERE symbol = ? ORDER BY created_at DESC LIMIT 1",
        (symbol,),
    ).fetchone()
    return _row_to_signal(row) if row else None


def update_signal_umsetzung(
    conn: sqlite3.Connection,
    signal_id: int,
    umgesetzt: bool,
    umgesetzt_menge: float | None = None,
    umgesetzt_preis_usd: float | None = None,
) -> None:
    """Nachtraegliche Umsetzungs-Rueckmeldung (Nutzer-Idee 2026-07-07, umgesetzt
    2026-07-09) - signals bleibt Append-only fuer neue Pipeline-Laeufe, dies ist ein
    gezieltes Update EINER bestehenden Zeile, kein neuer Insert. Menge/Preis bleiben
    optional (koennen None bleiben, auch wenn umgesetzt=True)."""
    conn.execute(
        "UPDATE signals SET umgesetzt = ?, umgesetzt_am = ?, umgesetzt_menge = ?, "
        "umgesetzt_preis_usd = ? WHERE id = ?",
        (int(umgesetzt), _now_iso(), umgesetzt_menge, umgesetzt_preis_usd, signal_id),
    )
    conn.commit()


def get_signal_history(conn: sqlite3.Connection, symbol: str, limit: int = 20) -> list[Signal]:
    rows = conn.execute(
        "SELECT * FROM signals WHERE symbol = ? ORDER BY created_at DESC LIMIT ?",
        (symbol, limit),
    ).fetchall()
    return [_row_to_signal(row) for row in rows]


_MARKTSCAN_COLUMNS = (
    "coingecko_id", "symbol", "name", "discovered_at", "discovery_source", "scan_run_id",
    "filter_a_bestanden", "tier", "market_cap_usd", "volume_24h_usd", "vol_marktkap_ratio",
    "alter_tage_geschaetzt", "alter_tage_quelle", "filter_a_begruendung", "bitpanda_gelistet",
    "price_usd", "price_eur", "change_24h_pct", "score_technik", "score_fundamental",
    "score_momentum", "score_kontext_makro", "signale_technik_json", "signale_fundamental_json",
    "signale_momentum_json", "signale_kontext_json", "score_gesamt", "gewichte_json",
    "regime_bei_scan", "einstufung", "einstufung_begruendung", "small_cap_budget_hinweis",
    "groq_kurzbegruendung", "groq_langbegruendung_json", "groq_generiert_am", "status",
    "status_geaendert_am",
)


def upsert_marktscan_candidate(conn: sqlite3.Connection, candidate: MarktscanCandidate) -> int:
    """Ein Kandidat kann innerhalb EINES Scan-Laufs ueber mehrere Quellen (Trending
    UND Top-Gainers) gefunden werden - `ON CONFLICT` merged das dann, statt einen
    Fehler zu werfen. `status`/`status_geaendert_am` werden hier NICHT ueberschrieben
    (siehe `update_marktscan_candidate_status()`) - ein zweiter Scoring-Durchlauf
    innerhalb desselben Laufs darf einen bereits gesetzten Nutzer-Status nicht
    zuruecksetzen. Cross-Lauf-Duplikat-Unterdrueckung (bereits abgelehnte/uebernommene
    Coins nicht erneut anzeigen) ist bewusst NICHT hier, sondern Aufgabe von
    agent/krypto/marktscan.py (andere scan_run_id = andere Zeile, kein UNIQUE-Konflikt)."""
    placeholders = ", ".join("?" for _ in _MARKTSCAN_COLUMNS)
    update_clause = ", ".join(
        f"{col} = excluded.{col}"
        for col in _MARKTSCAN_COLUMNS
        if col not in ("coingecko_id", "scan_run_id", "status", "status_geaendert_am")
    )
    values = []
    for col in _MARKTSCAN_COLUMNS:
        value = getattr(candidate, col)
        if col == "filter_a_bestanden":
            value = int(value)
        elif col == "bitpanda_gelistet" and value is not None:
            value = int(value)
        values.append(value)
    cursor = conn.execute(
        f"INSERT INTO marktscan_candidates ({', '.join(_MARKTSCAN_COLUMNS)}) "
        f"VALUES ({placeholders}) "
        f"ON CONFLICT(coingecko_id, scan_run_id) DO UPDATE SET {update_clause}",
        values,
    )
    conn.commit()
    return cursor.lastrowid


def _row_to_marktscan_candidate(row: sqlite3.Row) -> MarktscanCandidate:
    data = dict(row)
    data["filter_a_bestanden"] = bool(data["filter_a_bestanden"])
    if data.get("bitpanda_gelistet") is not None:
        data["bitpanda_gelistet"] = bool(data["bitpanda_gelistet"])
    return MarktscanCandidate(**data)


def get_marktscan_candidates(
    conn: sqlite3.Connection, status: str | None = None, limit: int = 200
) -> list[MarktscanCandidate]:
    if status is not None:
        rows = conn.execute(
            "SELECT * FROM marktscan_candidates WHERE status = ? ORDER BY discovered_at DESC LIMIT ?",
            (status, limit),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM marktscan_candidates ORDER BY discovered_at DESC LIMIT ?", (limit,)
        ).fetchall()
    return [_row_to_marktscan_candidate(row) for row in rows]


def get_latest_marktscan_status_by_coingecko_id(conn: sqlite3.Connection, coingecko_id: str) -> str | None:
    """Fuer den Cross-Lauf-Duplikat-Check (agent/krypto/marktscan.py): letzter bekannter
    Status dieses Coins ueber ALLE frueheren Scan-Laeufe hinweg, nicht auf den
    aktuellen scan_run_id beschraenkt."""
    row = conn.execute(
        "SELECT status FROM marktscan_candidates WHERE coingecko_id = ? "
        "ORDER BY discovered_at DESC LIMIT 1",
        (coingecko_id,),
    ).fetchone()
    return row["status"] if row else None


def update_marktscan_candidate_status(conn: sqlite3.Connection, candidate_id: int, status: str) -> None:
    conn.execute(
        "UPDATE marktscan_candidates SET status = ?, status_geaendert_am = ? WHERE id = ?",
        (status, _now_iso(), candidate_id),
    )
    conn.commit()


def update_marktscan_candidate_groq_writeup(
    conn: sqlite3.Connection, candidate_id: int, kurzbegruendung: str | None, langbegruendung_json: str
) -> None:
    """Ergaenzt eine per Klick oder automatisch (config.yaml
    marktscan.groq_automatisch_kaufkandidaten) generierte P-5-Begruendung auf einem
    bereits existierenden Kandidaten-Datensatz - kein neuer Scan-Lauf, reines Update."""
    conn.execute(
        "UPDATE marktscan_candidates SET groq_kurzbegruendung = ?, groq_langbegruendung_json = ?, "
        "groq_generiert_am = ? WHERE id = ?",
        (kurzbegruendung, langbegruendung_json, _now_iso(), candidate_id),
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
