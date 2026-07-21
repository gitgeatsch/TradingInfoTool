"""SQLite Verwaltung: Verbindung, automatische Initialisierung, CRUD."""
from __future__ import annotations

import json
import logging
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

from database.models import (
    HebelPosition,
    HebelSignal,
    HebelTrigger,
    Holding,
    MacroSnapshot,
    MakroAnalogErgebnis,
    MakroHistorieMonat,
    MarktscanCandidate,
    OhlcPoint,
    OpenInterestSnapshot,
    PriceHistoryPoint,
    PriceSnapshot,
    Signal,
    These,
)

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "tradinginfotool.db"

# Selektiver Desktop<->Notebook-Sync (2026-07-17, siehe Memory
# reference_usb_sync_workflow.md) - NUR fuer die manuellen Einstandspreis-
# Overrides in holdings.avg_buy_price_manual_eur, NICHT fuer die gesamte DB.
# Grund: das Notebook laeuft 24/7 und erzeugt laufend selbst Produktivdaten
# (signals/hebel_*/price_history/macro_snapshot/...) - eine volle DB-Kopie
# wuerde das jedes Mal ueberschreiben. Diese kleine JSON-Datei wird bei jeder
# manuellen Einstandspreis-Aenderung automatisch neu geschrieben (siehe
# set_holding_avg_buy_price_manual()) und bei jedem App-Start automatisch
# wieder eingelesen (siehe init_db()) - reines Copy-Merge via USB-Stick reicht,
# kein manueller Zwischenschritt noetig. NICHT in Git (siehe .gitignore),
# gleiche Sensitivitaet wie Assets.xlsx (echte Portfolio-Zahlen).
HOLDINGS_MANUAL_OVERRIDES_PATH = DB_PATH.parent / "holdings_manual_overrides.json"

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

CREATE TABLE IF NOT EXISTS asset_dca_settings (
    symbol          TEXT PRIMARY KEY,
    dca_erlaubt     INTEGER NOT NULL
);

-- Hebel-Pruefung-Toggle (2026-07-18, Budget/Asset-Optimierung) - analog
-- asset_dca_settings: per Asset umschaltbar, ob agent/krypto/hebel_screening.py
-- dieses Symbol ueberhaupt fuer neue Hebel-Trigger screent (OI-Abruf,
-- Trendfolge-/Kontra-Scoring, LLM-Call). Default true (kein Verhaltenswechsel
-- ohne explizites Abschalten durch den Nutzer), siehe get_hebel_pruefung_erlaubt().
CREATE TABLE IF NOT EXISTS asset_hebel_settings (
    symbol                  TEXT PRIMARY KEY,
    hebel_pruefung_erlaubt  INTEGER NOT NULL
);

-- Bitpanda-Gelistet-Override (2026-07-20, Nutzer-Fund: CEBS/EXH3/ISOC/VVMX/
-- X136/OD7C/OD7H/OD7L/OD7N/DBPK/3QSS werden vom /v3/assets-Endpunkt (api/
-- bitpanda.py) nicht gefunden, sind laut zwei echten Bitpanda-Screenshots
-- (S&P 500 2X Inverse=DBPK, iShares Agribusiness=ISOC) aber tatsaechlich
-- gehalten und aktiv handelbar - der Endpunkt ist fuer Bitpandas "Bitpanda
-- Stocks"-Fractional-ETF/ETC-Produktlinie offenbar keine vollstaendige
-- Quelle. Analog asset_hebel_settings: per Asset umschaltbar, ob der Live-
-- Check uebersteuert und IMMER als gelistet behandelt werden soll. Default
-- (keine Zeile): kein Override, Live-Check gilt wie bisher - siehe
-- get_bitpanda_gelistet_override().
CREATE TABLE IF NOT EXISTS asset_bitpanda_override (
    symbol                      TEXT PRIMARY KEY,
    bitpanda_gelistet_override  INTEGER NOT NULL
);

-- Groq-Erschoepfungs-Sperre, DB-persistent (2026-07-20) - ersetzt die
-- urspruengliche In-Memory-Variante in agent/krypto/budget_allocator.py
-- (dortiger Kommentar: "ein Neustart ist selten, das ist bewusst
-- akzeptabel"). Echter Notebook-Befund widerlegte das: in der aktiven
-- Entwicklungsphase (haeufige Pulls) startete die App ~8x/Tag neu, wodurch
-- die In-Memory-Sperre bei jedem Neustart zurückgesetzt wurde und Groq
-- wiederholt binnen Minuten erneut in dieselben 429-Fehlschlaege lief.
-- Einzeilige Tabelle (id=1 erzwungen) - haelt nur den aktuellen Tag,
-- siehe get/record-Funktionen fuer die Tageswechsel-Logik.
CREATE TABLE IF NOT EXISTS groq_exhaustion_status (
    id            INTEGER PRIMARY KEY CHECK (id = 1),
    datum         TEXT NOT NULL,
    fehlschlaege  INTEGER NOT NULL,
    erschoepft    INTEGER NOT NULL
);

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

CREATE TABLE IF NOT EXISTS open_interest_snapshot (
    symbol              TEXT NOT NULL,
    exchange            TEXT NOT NULL,
    open_interest       REAL,
    open_interest_usd   REAL,
    funding_rate        REAL,
    long_account_pct    REAL,
    fetched_at          TEXT NOT NULL,
    PRIMARY KEY (symbol, exchange, fetched_at)
);
CREATE INDEX IF NOT EXISTS idx_oi_snapshot_symbol_fetched ON open_interest_snapshot(symbol, exchange, fetched_at);

CREATE TABLE IF NOT EXISTS hebel_triggers (
    id                          INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol                      TEXT NOT NULL,
    richtung                    TEXT NOT NULL,
    screened_at                 TEXT NOT NULL,
    screening_run_id            TEXT NOT NULL,
    trigger_zweig               TEXT,
    score_gesamt                REAL,
    score_details_json          TEXT,
    oi_change_pct_lookback      REAL,
    kursaenderung_pct_lookback  REAL,
    funding_rate_aktuell        REAL,
    long_konten_anteil_prozent  REAL,
    ist_kandidat                INTEGER NOT NULL DEFAULT 0,
    status                      TEXT NOT NULL DEFAULT 'neu',
    status_geaendert_am         TEXT,
    -- trigger_zweig gehoert zum UNIQUE-Schluessel: Trendfolge UND Kontra koennen
    -- unabhaengig voneinander dieselbe Richtung fuer dasselbe Symbol vorschlagen
    -- (z.B. beide SHORT, aus unterschiedlichen Gruenden) - live gefunden 2026-07-14
    -- beim Test gegen die komplette Watchlist, siehe docs/hebel_positionsformel.md.
    UNIQUE(symbol, richtung, trigger_zweig, screening_run_id)
);
CREATE INDEX IF NOT EXISTS idx_hebel_triggers_kandidat ON hebel_triggers(ist_kandidat, screened_at);

CREATE TABLE IF NOT EXISTS hebel_positions (
    id                                  INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol                              TEXT NOT NULL,
    richtung                            TEXT NOT NULL DEFAULT 'LONG',
    status                              TEXT NOT NULL DEFAULT 'offen',
    eroeffnet_am                        TEXT NOT NULL,
    geschlossen_am                      TEXT,
    hebel_effektiv                      REAL,
    positionswert_eur                   REAL,
    kreditbetrag_eur                    REAL,
    eigenkapital_eur                    REAL,
    positionsmenge                      REAL,
    letzte_transaktion_unix_timestamp   INTEGER NOT NULL,
    liquidationspreis_geschaetzt_eur    REAL,
    liquidationspreis_berechnet_am      TEXT,
    quelle_tags_json                    TEXT,
    UNIQUE(symbol, eroeffnet_am)
);
CREATE INDEX IF NOT EXISTS idx_hebel_positions_status ON hebel_positions(status, symbol);

CREATE TABLE IF NOT EXISTS hebel_signals (
    id                            INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol                        TEXT NOT NULL,
    created_at                    TEXT NOT NULL,
    pipeline_version              TEXT NOT NULL DEFAULT '1',
    richtung                      TEXT NOT NULL,
    action                        TEXT NOT NULL,
    hebel_vorschlag                REAL,
    hebel_final                    REAL,
    hebel_korrektur_hinweis         TEXT,
    trade_thesis_typ                 TEXT,
    hebel_trigger_id                  INTEGER,
    trigger_zweig                      TEXT,
    trigger_score                       REAL,
    confidence_pct                       REAL,
    short_reasoning                      TEXT,
    long_reasoning_technisch              TEXT,
    long_reasoning_fundamental              TEXT,
    long_reasoning_makro                     TEXT,
    entry_usd_von                             REAL,
    entry_usd_bis                              REAL,
    entry_eur_von                               REAL,
    entry_eur_bis                                REAL,
    stop_loss_usd_von                             REAL,
    stop_loss_usd_bis                              REAL,
    stop_loss_eur_von                               REAL,
    stop_loss_eur_bis                                REAL,
    take_profit_usd_von                               REAL,
    take_profit_usd_bis                                REAL,
    take_profit_eur_von                                 REAL,
    take_profit_eur_bis                                  REAL,
    halte_kriterium_bucket                                TEXT,
    halte_kriterium_ziel_preis_usd                         REAL,
    halte_kriterium_ziel_preis_eur                          REAL,
    halte_kriterium_ziel_datum                               TEXT,
    halte_kriterium_bedingung_text                            TEXT,
    halte_kriterium_reasoning                                  TEXT,
    top_grund_1_kategorie                                       TEXT,
    top_grund_1_text                                             TEXT,
    top_grund_2_kategorie                                         TEXT,
    top_grund_2_text                                               TEXT,
    top_grund_3_kategorie                                           TEXT,
    top_grund_3_text                                                 TEXT,
    top_grund_4_kategorie                                             TEXT,
    top_grund_4_text                                                   TEXT,
    top_grund_5_kategorie                                               TEXT,
    top_grund_5_text                                                     TEXT,
    key_risks_text                                                       TEXT,
    regime                                                                TEXT,
    regime_source                                                         TEXT,
    forecast_bull_text                                                     TEXT,
    forecast_bull_prob_pct                                                  REAL,
    forecast_base_text                                                       TEXT,
    forecast_base_prob_pct                                                    REAL,
    forecast_bear_text                                                         TEXT,
    forecast_bear_prob_pct                                                      REAL,
    liquidationspreis_geschaetzt_usd                                             REAL,
    eigenkapitalbedarf_usd                                                        REAL,
    hebel_senkung_eigenkapital_nachschuss_eur                                      REAL,
    ausfuehrbarkeit_hinweis                                                        TEXT,
    gate_passed                                                                    INTEGER NOT NULL,
    gate_reason                                                                    TEXT,
    risk_veto                                                                      INTEGER NOT NULL DEFAULT 0,
    risk_veto_reason                                                               TEXT,
    facts_json                                                                     TEXT NOT NULL,
    groq_raw_response                                                              TEXT,
    llm_model                                                                      TEXT
);
CREATE INDEX IF NOT EXISTS idx_hebel_signals_symbol_created ON hebel_signals(symbol, created_at);

-- API-Gesundheits-Status (2026-07-15) - passive Erfolg/Fehler-Aufzeichnung je
-- externer Quelle, siehe database/api_health.py::track_api_health().
CREATE TABLE IF NOT EXISTS api_health_status (
    source              TEXT PRIMARY KEY,
    last_success_at     TEXT,
    last_error_at       TEXT,
    last_error_type     TEXT,
    last_error_message  TEXT
);

-- Historischer Makro-Konstellationsvergleich (2026-07-18, siehe Memory
-- project_konfidenz_kalibrierung_regelwerk.md / makro_analog.py) - monatliche
-- Zeitreihe mehrerer Makro-Faktoren + gecachtes Vergleichsergebnis.
CREATE TABLE IF NOT EXISTS makro_historie_monat (
    monat                   TEXT PRIMARY KEY,
    dxy_proxy                REAL,
    fed_funds_rate            REAL,
    rendite_10y                REAL,
    cpi_yoy_prozent              REAL,
    oel_wti                       REAL,
    spx_close                      REAL,
    spx_trend_deviation_std         REAL,
    btc_close                        REAL
);

CREATE TABLE IF NOT EXISTS makro_analog_ergebnis (
    berechnet_am    TEXT PRIMARY KEY,
    ergebnis_json   TEXT NOT NULL
);

-- Kategorie-Schwerpunkt-Thesen (2026-07-19, Release 2 der Kategorie-
-- Taxonomie) - siehe database/models.py::These fuer die volle Begruendung.
-- Bewusst append-artig ueber status statt Loeschen: 'erledigt'/'verworfen'
-- bleiben als Historie erhalten (die-Nutzer-Sorge/Begruendung von damals
-- ist spaeter noch nachvollziehbar, analog signals/hebel_signals).
CREATE TABLE IF NOT EXISTS thesen (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    hauptgruppe         TEXT NOT NULL,
    unterkategorie      TEXT,
    richtung            TEXT NOT NULL,
    staerke             INTEGER,
    begruendung         TEXT NOT NULL,
    pruef_mechanismus   TEXT,
    gesetzt_am          TEXT NOT NULL,
    review_am           TEXT,
    status              TEXT NOT NULL DEFAULT 'aktiv',
    quelle              TEXT NOT NULL DEFAULT 'manuell'
);
CREATE INDEX IF NOT EXISTS idx_thesen_status ON thesen(status);
CREATE INDEX IF NOT EXISTS idx_thesen_hauptgruppe ON thesen(hauptgruppe, unterkategorie);

-- OI-Abdeckungs-Status (2026-07-19, echter Notebook-Fund: KAS/KAIA/FLOKI/
-- TURBO/CANTON scheiterten wiederholt bei ALLEN drei Boersen) - anders als
-- api_health_status (ein Zustand je EXTERNE QUELLE) hier ein Zustand je
-- SYMBOL, weil die Frage "hat DIESES Symbol strukturell keine OI-Daten"
-- unabhaengig von der einzelnen Boerse beantwortet werden soll (alle drei
-- muessten gleichzeitig fehlschlagen, damit ein Lauf als Fehlschlag zaehlt,
-- siehe agent/krypto/hebel_screening.py::fetch_and_store_oi_snapshot()).
CREATE TABLE IF NOT EXISTS oi_abdeckung_status (
    symbol                      TEXT PRIMARY KEY,
    konsekutive_fehlschlaege    INTEGER NOT NULL DEFAULT 0,
    letzter_erfolg_at           TEXT,
    zuletzt_gemeldet_at         TEXT
);
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
    # Boden-Zielzone (AZ-4 Baustein 2, 2026-07-12) - siehe database/models.py::
    # MacroSnapshot fuer die Feld-Dokumentation. Gleiche generische Migration wie
    # oben, kein eigener Funktionsblock noetig.
    "btc_boden_zielzone_von", "btc_boden_zielzone_bis",
    "eth_boden_zielzone_von", "eth_boden_zielzone_bis",
    "equities_sp500_drawdown_pct", "equities_nasdaq_drawdown_pct",
    "eth_regression_predicted_price", "eth_regression_residual_std",
    # Regime-Status-Anzeige (2026-07-17) - siehe database/models.py::MacroSnapshot
    # fuer die Feld-Dokumentation. zyklus_risiko ist REAL, der Rest TEXT (siehe
    # _MACRO_SNAPSHOT_TEXT_COLUMNS unten).
    "zyklus_risiko", "zyklus_risiko_begruendung", "liquiditaets_regime",
    "liquiditaets_regime_begruendung", "btc_trend_label", "regime_reason",
    # VIX-Fruehindikator (2026-07-18) - siehe database/models.py::MacroSnapshot
    # fuer die Feld-Dokumentation.
    "vix_wert",
)

# Erste TEXT-Spalten in dieser bisher rein numerischen Migrationsliste (siehe
# _migrate_macro_snapshot_columns()) - explizit als Ausnahme markiert, statt
# alle neuen Spalten pauschal als REAL zu deklarieren (SQLite wuerde Text zwar
# trotzdem speichern, aber mit irrefuehrender Spaltenaffinitaet).
_MACRO_SNAPSHOT_TEXT_COLUMNS = {
    "zyklus_risiko_begruendung", "liquiditaets_regime",
    "liquiditaets_regime_begruendung", "btc_trend_label", "regime_reason",
}


def _migrate_macro_snapshot_columns(conn: sqlite3.Connection) -> None:
    """Leichtgewichtige Migration: macro_snapshot existierte bereits vor den
    FRED/PBoC-Spalten (Phase 3, 2026-07-08 Folge-Slice) - CREATE TABLE IF NOT EXISTS
    greift bei bereits existierenden Tabellen nicht, daher ALTER TABLE nachziehen.
    Alle neuen Spalten sind nullable, daher unkritisch fuer Bestandsdaten."""
    existing = {row["name"] for row in conn.execute("PRAGMA table_info(macro_snapshot)")}
    for column in _MACRO_SNAPSHOT_NEW_COLUMNS:
        if column not in existing:
            sql_type = "TEXT" if column in _MACRO_SNAPSHOT_TEXT_COLUMNS else "REAL"
            conn.execute(f"ALTER TABLE macro_snapshot ADD COLUMN {column} {sql_type}")
    conn.commit()


def _migrate_marktscan_candidates_columns(conn: sqlite3.Connection) -> None:
    """Wie _migrate_macro_snapshot_columns(): marktscan_candidates existierte bereits
    vor der bitpanda_gelistet-Spalte (2026-07-09, Nutzer-Wunsch Handelsboersen-Check)."""
    existing = {row["name"] for row in conn.execute("PRAGMA table_info(marktscan_candidates)")}
    if "bitpanda_gelistet" not in existing:
        conn.execute("ALTER TABLE marktscan_candidates ADD COLUMN bitpanda_gelistet INTEGER")
    if "llm_model" not in existing:
        # 2026-07-14: fehlte bisher als einzige der drei Signal-erzeugenden
        # Tabellen (signals.groq_model/hebel_signals.llm_model existieren schon)
        # - noetig fuer einen echten, providerspezifischen Tages-Zaehler ueber
        # alle 3 Budget-Allocator-Tiers (siehe count_real_llm_calls_today_by_provider()).
        conn.execute("ALTER TABLE marktscan_candidates ADD COLUMN llm_model TEXT")
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


_SIGNAL_OUTCOME_NEW_COLUMNS = {
    "outcome_status": "TEXT",
    "outcome_geprueft_am": "TEXT",
    "outcome_entschieden_am": "TEXT",
    "outcome_realisiertes_crv": "REAL",
    "outcome_datenquelle": "TEXT",
}


def _migrate_signal_outcome_columns(conn: sqlite3.Connection) -> None:
    """Wie _migrate_signal_range_kriterium_columns(): signals existierte bereits vor
    dem Backward-Tracking (2026-07-10, Selbstverifikations-Vision Schritt 2 - siehe
    agent/krypto/backward_tracking.py)."""
    existing = {row["name"] for row in conn.execute("PRAGMA table_info(signals)")}
    for column, sql_type in _SIGNAL_OUTCOME_NEW_COLUMNS.items():
        if column not in existing:
            conn.execute(f"ALTER TABLE signals ADD COLUMN {column} {sql_type}")
    conn.commit()


_HEBEL_SIGNAL_OUTCOME_NEW_COLUMNS = {
    "outcome_status": "TEXT",
    "outcome_geprueft_am": "TEXT",
    "outcome_entschieden_am": "TEXT",
    "outcome_realisiertes_crv": "REAL",
    "outcome_datenquelle": "TEXT",
}


def _migrate_hebel_signal_outcome_columns(conn: sqlite3.Connection) -> None:
    """Wie _migrate_signal_outcome_columns(), aber fuer hebel_signals (2026-07-15,
    Hebel-Backward-Tracking - siehe agent/krypto/hebel_backward_tracking.py).
    hebel_signals existierte bereits vor diesen Spalten (seit Hebel-Phase 4)."""
    existing = {row["name"] for row in conn.execute("PRAGMA table_info(hebel_signals)")}
    for column, sql_type in _HEBEL_SIGNAL_OUTCOME_NEW_COLUMNS.items():
        if column not in existing:
            conn.execute(f"ALTER TABLE hebel_signals ADD COLUMN {column} {sql_type}")
    conn.commit()


_HEBEL_SIGNAL_SENKUNG_NEW_COLUMNS = {"hebel_senkung_eigenkapital_nachschuss_eur": "REAL"}


def _migrate_hebel_signal_senkung_columns(conn: sqlite3.Connection) -> None:
    """Nachtrag 2026-07-17 (echter LINK-Fall, siehe Memory
    project_hebel_rahmenbedingungen.md) - konkreter EUR-Nachschussbetrag bei
    HEBEL_SENKEN, macht die Empfehlung erst praktisch umsetzbar. Gleiches
    additive Migrations-Muster wie _migrate_hebel_signal_outcome_columns()."""
    existing = {row["name"] for row in conn.execute("PRAGMA table_info(hebel_signals)")}
    for column, sql_type in _HEBEL_SIGNAL_SENKUNG_NEW_COLUMNS.items():
        if column not in existing:
            conn.execute(f"ALTER TABLE hebel_signals ADD COLUMN {column} {sql_type}")
    conn.commit()


_GEGENARGUMENT_NEW_COLUMN = {"gegenargument": "TEXT"}


def _migrate_gegenargument_columns(conn: sqlite3.Connection) -> None:
    """Nachtrag 2026-07-18 (echter CAT-Fall, siehe Memory
    project_konfidenz_kalibrierung_regelwerk.md) - Gegenargument-Pflichtfeld
    (analyst.py/hebel_analyst.py SYSTEM_PROMPT Regel 22) fuer beide Tabellen.
    Gleiches additive Migrations-Muster wie oben."""
    for table in ("signals", "hebel_signals"):
        existing = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})")}
        for column, sql_type in _GEGENARGUMENT_NEW_COLUMN.items():
            if column not in existing:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {sql_type}")
    conn.commit()


_RISIKOFAKTOREN_NEW_COLUMN = {"risikofaktoren_json": "TEXT"}


def _migrate_risikofaktoren_columns(conn: sqlite3.Connection) -> None:
    """Nachtrag 2026-07-19 (E-Mail-/App-Neustrukturierung in 3 Abschnitte -
    Mathematisch berechnet / LLM-Bewertung / Konklusion mit Risikofaktoren,
    echter AVAX-Hebel-Fund) fuer beide Tabellen. Gleiches additive
    Migrations-Muster wie _migrate_gegenargument_columns()."""
    for table in ("signals", "hebel_signals"):
        existing = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})")}
        for column, sql_type in _RISIKOFAKTOREN_NEW_COLUMN.items():
            if column not in existing:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {sql_type}")
    conn.commit()


_CASH_VETO_NEW_COLUMNS = {"cash_veto": "INTEGER", "cash_veto_reason": "TEXT"}


def _migrate_cash_veto_columns(conn: sqlite3.Connection) -> None:
    """Nachtrag 2026-07-18 (Detailanalyse "Anzeige/Info bei Cash-Block") - nur
    `signals` (RM-4 gilt fuer Spot/Aktien/Rohstoffe/Themen-ETF, nicht Hebel/
    Hedge, siehe risk_gate.py-Modul-Docstring). Gleiches additive
    Migrations-Muster wie oben."""
    existing = {row["name"] for row in conn.execute("PRAGMA table_info(signals)")}
    for column, sql_type in _CASH_VETO_NEW_COLUMNS.items():
        if column not in existing:
            conn.execute(f"ALTER TABLE signals ADD COLUMN {column} {sql_type}")
    conn.commit()


_SIGNAL_TRANCHEN_NEW_COLUMNS = {"tranchen_json": "TEXT"}


def _migrate_signal_tranchen_columns(conn: sqlite3.Connection) -> None:
    """Wie _migrate_signal_outcome_columns(): signals existierte bereits vor der
    AZ-4-Tranchen-Erweiterung (2026-07-12, gestaffelte Kauf-/Verkaufszonen). Variable
    Anzahl Tranchen (2-5) -> JSON-Blob statt fester Spalten (Muster aus
    marktscan_candidates.signale_technik_json etc.), da tranchen rein informativ ist
    (siehe agent/krypto/analyst.py) und keine feste Spaltenzahl wie top_gruende hat."""
    existing = {row["name"] for row in conn.execute("PRAGMA table_info(signals)")}
    for column, sql_type in _SIGNAL_TRANCHEN_NEW_COLUMNS.items():
        if column not in existing:
            conn.execute(f"ALTER TABLE signals ADD COLUMN {column} {sql_type}")
    conn.commit()


_SIGNAL_CASH_RESERVE_ZIEL_NEW_COLUMNS = {
    "cash_reserve_ziel_btc_usd": "REAL",
    "cash_reserve_ziel_eth_usd": "REAL",
    "cash_reserve_ziel_gesamt_usd": "REAL",
    "cash_reserve_ziel_begruendung": "TEXT",
}


def _migrate_signal_cash_reserve_ziel_columns(conn: sqlite3.Connection) -> None:
    """AZ-4 Baustein 3 (2026-07-12) - gleiches Muster wie
    _migrate_signal_tranchen_columns(). Signal-gebunden (nicht macro_snapshot-artig
    wie Boden-Zielzone), da an die konkrete BTC/ETH-Signalerzeugung gebunden."""
    existing = {row["name"] for row in conn.execute("PRAGMA table_info(signals)")}
    for column, sql_type in _SIGNAL_CASH_RESERVE_ZIEL_NEW_COLUMNS.items():
        if column not in existing:
            conn.execute(f"ALTER TABLE signals ADD COLUMN {column} {sql_type}")
    conn.commit()


_HOLDINGS_AVG_COST_NEW_COLUMNS = {
    # EUR, nicht USD - Bitpandas trade.attributes.price ist EUR-denominiert
    # (fiat_id "1" = EUR, live gegen /fiatwallets verifiziert 2026-07-11).
    "avg_buy_price_eur": "REAL",
    "avg_buy_price_tracked_qty": "REAL",
    "avg_buy_price_computed_at": "TEXT",
    "avg_buy_price_manual_eur": "REAL",
    # 2026-07-11, Nutzer-Fund: aktuell gestakte Menge, ueber Wallet-Endpunkte
    # strukturell unsichtbar (siehe importer/bitpanda_avg_cost.py::
    # compute_staked_quantities()) - ohne dieses Feld war ein signifikanter Teil
    # des Portfolios (im Live-Test ~2.400 EUR) fuer Anzeige UND Regelwerk unsichtbar.
    "staked_quantity": "REAL",
}


def _migrate_holdings_avg_cost_columns(conn: sqlite3.Connection) -> None:
    """Wie _migrate_signal_outcome_columns(): holdings existierte bereits vor dem
    Einstandspreis-Feature (2026-07-11, echter Marktpreis aus Bitpanda-Trades,
    siehe importer/bitpanda_avg_cost.py)."""
    existing = {row["name"] for row in conn.execute("PRAGMA table_info(holdings)")}
    for column, sql_type in _HOLDINGS_AVG_COST_NEW_COLUMNS.items():
        if column not in existing:
            conn.execute(f"ALTER TABLE holdings ADD COLUMN {column} {sql_type}")
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
    _migrate_signal_outcome_columns(conn)
    _migrate_holdings_avg_cost_columns(conn)
    _migrate_signal_tranchen_columns(conn)
    _migrate_signal_cash_reserve_ziel_columns(conn)
    _migrate_hebel_signal_outcome_columns(conn)
    _migrate_hebel_signal_senkung_columns(conn)
    _migrate_gegenargument_columns(conn)
    _migrate_cash_veto_columns(conn)
    _migrate_risikofaktoren_columns(conn)
    import_holdings_manual_overrides(conn)


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
        "SELECT symbol, quantity, updated_at, source, avg_buy_price_eur, "
        "avg_buy_price_tracked_qty, avg_buy_price_computed_at, avg_buy_price_manual_eur, "
        "staked_quantity FROM holdings"
    ).fetchall()
    return [Holding(**dict(row)) for row in rows]


def update_holding_staked_quantity(conn: sqlite3.Connection, symbol: str, staked_quantity: float) -> None:
    """2026-07-11: aktuell gestakte Menge (aus Wallet-Transaktions-Tags berechnet,
    siehe importer/bitpanda_avg_cost.py::compute_staked_quantities()) - additiv zu
    holdings.quantity (der normalen, ueber die Wallet-API sichtbaren Menge)."""
    conn.execute(
        "UPDATE holdings SET staked_quantity = ? WHERE symbol = ?",
        (staked_quantity, symbol),
    )
    conn.commit()


def update_holding_avg_buy_price(
    conn: sqlite3.Connection, symbol: str, avg_buy_price_eur: float | None, tracked_qty: float
) -> None:
    """Schreibt nur den automatisch berechneten Einstandspreis (Slice: Bitpanda-
    Transaktions-Auswertung, importer/bitpanda_avg_cost.py) - avg_buy_price_manual_eur
    bleibt unberuehrt (siehe Plan: manueller Override wird von keiner automatischen
    Berechnung je angefasst). Setzt nur, wenn die Zeile bereits existiert (holdings
    wird ausschliesslich ueber upsert_holding() neu angelegt)."""
    conn.execute(
        "UPDATE holdings SET avg_buy_price_eur = ?, avg_buy_price_tracked_qty = ?, "
        "avg_buy_price_computed_at = ? WHERE symbol = ?",
        (avg_buy_price_eur, tracked_qty, _now_iso(), symbol),
    )
    conn.commit()


def set_holding_avg_buy_price_manual(conn: sqlite3.Connection, symbol: str, value: float | None) -> None:
    """value=None loescht den Override explizit (faellt dann auf den automatischen
    Wert zurueck, siehe Holding.effective_avg_buy_price_eur)."""
    conn.execute(
        "UPDATE holdings SET avg_buy_price_manual_eur = ? WHERE symbol = ?",
        (value, symbol),
    )
    conn.commit()
    export_holdings_manual_overrides(conn)


def export_holdings_manual_overrides(conn: sqlite3.Connection) -> None:
    """Schreibt alle aktuellen avg_buy_price_manual_eur-Werte in eine kleine JSON-
    Datei neben der DB (siehe HOLDINGS_MANUAL_OVERRIDES_PATH) - Grundlage fuer den
    selektiven Desktop<->Notebook-Sync (nur diese Datei per USB-Stick mitnehmen,
    NICHT die ganze DB kopieren). Wird automatisch bei jeder Aenderung aufgerufen,
    kein manueller Export-Schritt noetig."""
    rows = conn.execute(
        "SELECT symbol, avg_buy_price_manual_eur FROM holdings WHERE avg_buy_price_manual_eur IS NOT NULL"
    ).fetchall()
    overrides = {row["symbol"]: row["avg_buy_price_manual_eur"] for row in rows}
    HOLDINGS_MANUAL_OVERRIDES_PATH.parent.mkdir(parents=True, exist_ok=True)
    HOLDINGS_MANUAL_OVERRIDES_PATH.write_text(json.dumps(overrides, indent=2, sort_keys=True), encoding="utf-8")


def import_holdings_manual_overrides(conn: sqlite3.Connection) -> list[str]:
    """Liest HOLDINGS_MANUAL_OVERRIDES_PATH (falls vorhanden) und uebernimmt die
    Werte in die lokale holdings-Tabelle - nur fuer Symbole, die hier bereits einen
    holdings-Eintrag haben (kein Anlegen neuer Phantom-Zeilen; die Zeile selbst
    entsteht ausschliesslich ueber upsert_holding(), also den echten Bitpanda-
    Bestandsabgleich). Wird automatisch bei jedem App-Start aufgerufen (init_db()),
    idempotent - mehrfaches Anwenden derselben Datei aendert nichts weiter."""
    if not HOLDINGS_MANUAL_OVERRIDES_PATH.exists():
        return []
    overrides: dict[str, float] = json.loads(HOLDINGS_MANUAL_OVERRIDES_PATH.read_text(encoding="utf-8"))
    existing_symbols = {row["symbol"] for row in conn.execute("SELECT symbol FROM holdings").fetchall()}
    applied: list[str] = []
    for symbol, value in overrides.items():
        if symbol not in existing_symbols:
            continue
        conn.execute(
            "UPDATE holdings SET avg_buy_price_manual_eur = ? WHERE symbol = ?",
            (value, symbol),
        )
        applied.append(symbol)
    conn.commit()
    return applied


def get_bitpanda_avg_cost_last_synced_unix(conn: sqlite3.Connection) -> int | None:
    """Globaler Wasserstand (nicht pro Symbol, ein API-Aufruf liefert Transaktionen
    ueber alle Symbole gemischt) - ermoeglicht inkrementelle Folge-Syncs, da Bitpanda
    /wallets/transactions neueste-zuerst liefert (live verifiziert 2026-07-11)."""
    row = conn.execute(
        "SELECT value FROM meta WHERE key = 'bitpanda_avg_cost_last_synced_unix'"
    ).fetchone()
    if row is None or row["value"] is None:
        return None
    try:
        return int(row["value"])
    except ValueError:
        return None


def set_bitpanda_avg_cost_last_synced_unix(conn: sqlite3.Connection, unix_timestamp: int) -> None:
    conn.execute(
        "INSERT INTO meta (key, value) VALUES ('bitpanda_avg_cost_last_synced_unix', ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (str(unix_timestamp),),
    )
    conn.commit()


def get_bitpanda_holdings_last_synced_unix(conn: sqlite3.Connection) -> int | None:
    """EIGENER Wasserstand fuer die Staking-Verifikation im Bestandsabgleich
    (2026-07-16, importer/bitpanda_sync.py::sync_from_bitpanda()) - bewusst
    NICHT derselbe Schluessel wie bitpanda_avg_cost_last_synced_unix: beide
    Features verarbeiten dieselben Rohtransaktionen fuer unterschiedliche
    Zwecke (Einstandspreis vs. Staking-Erkennung) und duerfen sich nicht
    gegenseitig Transaktionen "wegkonsumieren" - ein gemeinsamer Cursor haette
    sonst dazu gefuehrt, dass der jeweils andere Feature-Sync Transaktionen
    verpasst, die der erste Aufrufer bereits als 'bis hierhin gesehen'
    markiert hat."""
    row = conn.execute(
        "SELECT value FROM meta WHERE key = 'bitpanda_holdings_last_synced_unix'"
    ).fetchone()
    if row is None or row["value"] is None:
        return None
    try:
        return int(row["value"])
    except ValueError:
        return None


def set_bitpanda_holdings_last_synced_unix(conn: sqlite3.Connection, unix_timestamp: int) -> None:
    conn.execute(
        "INSERT INTO meta (key, value) VALUES ('bitpanda_holdings_last_synced_unix', ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (str(unix_timestamp),),
    )
    conn.commit()


def get_backward_tracking_last_run_date(conn: sqlite3.Connection) -> str | None:
    """2026-07-17, Nutzer-Fund: der taegliche 06:00-Cron fuer backward_tracking_job
    hatte am 07-15 UND 07-16 keinen einzigen Lauf, weil die App zu diesem Zeitpunkt
    schlicht nicht lief (APScheduler-Cron-Trigger holen einen verpassten festen
    Zeitpunkt NICHT automatisch nach) - zwei Tage lang wurden dadurch offene
    Hebel-Signale nie auf ein Ergebnis geprueft, obwohl die Haltedauer (~1,1 Tage
    im Schnitt) laengst reif dafuer war. Dieses ISO-Datum (Wasserstand statt
    Unix-Timestamp, da nur Tag-Genauigkeit noetig) ermoeglicht einen Nachhol-Lauf
    beim naechsten App-Start, falls der heutige 06:00-Termin verpasst wurde."""
    row = conn.execute(
        "SELECT value FROM meta WHERE key = 'backward_tracking_last_run_date'"
    ).fetchone()
    return row["value"] if row is not None else None


def set_backward_tracking_last_run_date(conn: sqlite3.Connection, iso_date: str) -> None:
    conn.execute(
        "INSERT INTO meta (key, value) VALUES ('backward_tracking_last_run_date', ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (iso_date,),
    )
    conn.commit()


def get_cash_reserve_fiat_eur(conn: sqlite3.Connection) -> float:
    """Manuell gepflegtes Fiat-Guthaben (EUR) auf der Boerse, z.B. Bitpanda - nicht
    in Stablecoins umgewandeltes Geld, das die App sonst nirgends kennt (RM-4-
    Erweiterung, 2026-07-10). 0.0 falls nie gesetzt."""
    row = conn.execute("SELECT value FROM meta WHERE key = 'cash_reserve_fiat_eur'").fetchone()
    if row is None or row["value"] is None:
        return 0.0
    try:
        return float(row["value"])
    except ValueError:
        # 2026-07-18 (Detailanalyse Punkt 4): bisher stiller Fallback auf 0.0 -
        # ein korrupter Wert wuerde RM-4 dauerhaft und ohne erkennbaren Grund
        # verschaerfen (Fiat-Guthaben faellt komplett aus der Cash-Reserve),
        # bis der naechste erfolgreiche Sync ueberschreibt. Jetzt wenigstens
        # geloggt, damit das nicht unbemerkt bleibt.
        logger.warning("cash_reserve_fiat_eur enthaelt einen ungueltigen Wert (%r) - falle auf 0.0 zurueck", row["value"])
        return 0.0


def set_cash_reserve_fiat_eur(conn: sqlite3.Connection, value_eur: float) -> None:
    conn.execute(
        "INSERT INTO meta (key, value) VALUES ('cash_reserve_fiat_eur', ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (str(value_eur),),
    )
    conn.commit()


_DCA_ERLAUBT_DEFAULT_SYMBOLS = {"BTC", "ETH", "SOL"}


def get_dca_erlaubt(conn: sqlite3.Connection, symbol: str) -> bool:
    """AZ-4-Tranchen-Toggle (2026-07-12, 2026-07-18 um SOL erweitert) - per
    Asset umschaltbar, ob der Agent gestaffelte Kauf-/Verkaufszonen
    vorschlagen darf (zusaetzlich zur Regime-Bedingung in
    agent/krypto/pipeline.py). Default: an fuer BTC/ETH/SOL, sonst aus,
    solange keine explizite Zeile existiert."""
    row = conn.execute(
        "SELECT dca_erlaubt FROM asset_dca_settings WHERE symbol = ?", (symbol,)
    ).fetchone()
    if row is None:
        return symbol in _DCA_ERLAUBT_DEFAULT_SYMBOLS
    return bool(row["dca_erlaubt"])


def set_dca_erlaubt(conn: sqlite3.Connection, symbol: str, erlaubt: bool) -> None:
    conn.execute(
        "INSERT INTO asset_dca_settings (symbol, dca_erlaubt) VALUES (?, ?) "
        "ON CONFLICT(symbol) DO UPDATE SET dca_erlaubt = excluded.dca_erlaubt",
        (symbol, int(erlaubt)),
    )
    conn.commit()


def get_hebel_pruefung_erlaubt(conn: sqlite3.Connection, symbol: str) -> bool:
    """Hebel-Pruefung-Toggle (2026-07-18) - per Asset umschaltbar, ob
    agent/krypto/hebel_screening.py dieses Symbol ueberhaupt fuer neue
    Hebel-Trigger screent. Default: an fuer ALLE Krypto-Assets (kein
    Verhaltenswechsel ohne explizites Abschalten), solange keine explizite
    Zeile existiert - anders als get_dca_erlaubt() (dort ist der Default
    NUR fuer BTC/ETH/SOL an), da bisher jedes Krypto-Asset gescreent wurde
    und dieser Toggle rein ein zusaetzliches Opt-out sein soll, keine
    Verhaltensaenderung fuer bestehende Nutzer."""
    row = conn.execute(
        "SELECT hebel_pruefung_erlaubt FROM asset_hebel_settings WHERE symbol = ?", (symbol,)
    ).fetchone()
    if row is None:
        return True
    return bool(row["hebel_pruefung_erlaubt"])


def set_hebel_pruefung_erlaubt(conn: sqlite3.Connection, symbol: str, erlaubt: bool) -> None:
    conn.execute(
        "INSERT INTO asset_hebel_settings (symbol, hebel_pruefung_erlaubt) VALUES (?, ?) "
        "ON CONFLICT(symbol) DO UPDATE SET hebel_pruefung_erlaubt = excluded.hebel_pruefung_erlaubt",
        (symbol, int(erlaubt)),
    )
    conn.commit()


def get_bitpanda_gelistet_override(conn: sqlite3.Connection, symbol: str) -> bool:
    """Bitpanda-Gelistet-Override (2026-07-20) - siehe asset_bitpanda_override-
    Tabellendocstring. Default: kein Override (False), solange keine explizite
    Zeile existiert - der normale Live-Check (api/bitpanda.py::is_listed())
    gilt dann unveraendert weiter, keine Verhaltensaenderung fuer alle
    anderen Assets."""
    row = conn.execute(
        "SELECT bitpanda_gelistet_override FROM asset_bitpanda_override WHERE symbol = ?", (symbol,)
    ).fetchone()
    if row is None:
        return False
    return bool(row["bitpanda_gelistet_override"])


def set_bitpanda_gelistet_override(conn: sqlite3.Connection, symbol: str, aktiv: bool) -> None:
    conn.execute(
        "INSERT INTO asset_bitpanda_override (symbol, bitpanda_gelistet_override) VALUES (?, ?) "
        "ON CONFLICT(symbol) DO UPDATE SET bitpanda_gelistet_override = excluded.bitpanda_gelistet_override",
        (symbol, int(aktiv)),
    )
    conn.commit()


def _heutiges_datum_utc() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def is_groq_exhausted_today(conn: sqlite3.Connection) -> bool:
    """DB-persistente Groq-Erschoepfungs-Sperre (2026-07-20) - siehe
    groq_exhaustion_status-Tabellendocstring. Default: nicht erschoepft,
    solange keine Zeile fuer den HEUTIGEN Tag existiert - eine Zeile von
    einem frueheren Tag zaehlt nicht (kein Beibehalten ueber Tagesgrenzen
    hinweg, identisch zur urspruenglichen In-Memory-Semantik)."""
    row = conn.execute(
        "SELECT datum, erschoepft FROM groq_exhaustion_status WHERE id = 1"
    ).fetchone()
    if row is None or row["datum"] != _heutiges_datum_utc():
        return False
    return bool(row["erschoepft"])


def record_groq_failure(conn: sqlite3.Connection, schwelle: int) -> None:
    """Zaehlt Groq-Fehlschlaege NUR innerhalb desselben Kalendertags (UTC) -
    ein Zaehlerstand von gestern darf nicht in den heutigen Tag durchschlagen.
    Setzt `erschoepft`, sobald `schwelle` erreicht ist - bleibt dann fuer den
    Rest des Tages gesetzt (siehe is_groq_exhausted_today()). Loggt nur beim
    UEBERGANG auf erschoepft=True (nicht bei jedem weiteren Fehlschlag
    danach), damit das Log nicht mit Wiederholungen zugespamt wird."""
    today = _heutiges_datum_utc()
    row = conn.execute(
        "SELECT datum, fehlschlaege, erschoepft FROM groq_exhaustion_status WHERE id = 1"
    ).fetchone()
    war_schon_erschoepft = row is not None and row["datum"] == today and bool(row["erschoepft"])
    fehlschlaege = row["fehlschlaege"] + 1 if row is not None and row["datum"] == today else 1
    erschoepft = fehlschlaege >= schwelle
    conn.execute(
        "INSERT INTO groq_exhaustion_status (id, datum, fehlschlaege, erschoepft) VALUES (1, ?, ?, ?) "
        "ON CONFLICT(id) DO UPDATE SET datum = excluded.datum, fehlschlaege = excluded.fehlschlaege, "
        "erschoepft = excluded.erschoepft",
        (today, fehlschlaege, int(erschoepft)),
    )
    conn.commit()
    if erschoepft and not war_schon_erschoepft:
        logger.warning(
            "Groq: %d Fehlschlaege in Folge am %s - wird fuer den Rest des Tages uebersprungen, "
            "weitere Kandidaten gehen direkt an Mistral/Gemini",
            fehlschlaege, today,
        )


def record_groq_success(conn: sqlite3.Connection) -> None:
    """Setzt den Fehlschlag-Zaehler fuer heute zurueck (ein erfolgreicher
    Call widerlegt eine vermutete Erschoepfung)."""
    today = _heutiges_datum_utc()
    conn.execute(
        "INSERT INTO groq_exhaustion_status (id, datum, fehlschlaege, erschoepft) VALUES (1, ?, 0, 0) "
        "ON CONFLICT(id) DO UPDATE SET datum = excluded.datum, fehlschlaege = 0, erschoepft = 0",
        (today,),
    )
    conn.commit()


def get_cash_reserve_synced_at(conn: sqlite3.Connection) -> str | None:
    """Zeitstempel des letzten ERFOLGREICHEN Bitpanda-Sync-Abrufs der Cash-Reserve
    (2026-07-11, Nutzer-Fund) - unabhaengig davon, ob sich der Wert dabei
    tatsaechlich geaendert hat. Grund: Bitpanda sperrt den fuer offene Fusion-
    Limit-Orders reservierten Betrag sofort aus dem Wallet-Guthaben (live
    bestaetigt) - die App bekommt davon nichts mit, bis der naechste manuelle
    Sync laeuft. Ohne diesen Zeitstempel war nicht erkennbar, ob eine angezeigte
    Cash-Reserve noch aktuell oder laengst veraltet ist. None, wenn noch nie
    per Bitpanda-Sync synchronisiert (z.B. nur manuell eingetragen)."""
    row = conn.execute("SELECT value FROM meta WHERE key = 'cash_reserve_synced_at'").fetchone()
    return row["value"] if row and row["value"] is not None else None


def set_cash_reserve_synced_at(conn: sqlite3.Connection, timestamp: str) -> None:
    conn.execute(
        "INSERT INTO meta (key, value) VALUES ('cash_reserve_synced_at', ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (timestamp,),
    )
    conn.commit()


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


_MAKRO_HISTORIE_MONAT_COLUMNS = (
    "monat", "dxy_proxy", "fed_funds_rate", "rendite_10y", "cpi_yoy_prozent",
    "oel_wti", "spx_close", "spx_trend_deviation_std", "btc_close",
)


def upsert_makro_historie_monat(conn: sqlite3.Connection, eintrag: MakroHistorieMonat) -> None:
    """Gleiches COALESCE-Merge-Muster wie upsert_macro_snapshot() - verschiedene
    Quellen (FRED/yfinance/blockchain.com) fuellen unterschiedliche Spalten
    desselben Monats in getrennten Aufrufen (siehe agent/krypto/makro_analog.py),
    ein NULL aus einer Quelle darf einen bereits gesetzten Wert einer anderen
    Quelle nicht ueberschreiben."""
    placeholders = ", ".join("?" for _ in _MAKRO_HISTORIE_MONAT_COLUMNS)
    update_clause = ", ".join(
        f"{col} = COALESCE(excluded.{col}, makro_historie_monat.{col})"
        for col in _MAKRO_HISTORIE_MONAT_COLUMNS
        if col != "monat"
    )
    values = [getattr(eintrag, col) for col in _MAKRO_HISTORIE_MONAT_COLUMNS]
    conn.execute(
        f"INSERT INTO makro_historie_monat ({', '.join(_MAKRO_HISTORIE_MONAT_COLUMNS)}) "
        f"VALUES ({placeholders}) ON CONFLICT(monat) DO UPDATE SET {update_clause}",
        values,
    )
    conn.commit()


def get_makro_historie(conn: sqlite3.Connection) -> list[MakroHistorieMonat]:
    columns = ", ".join(_MAKRO_HISTORIE_MONAT_COLUMNS)
    rows = conn.execute(f"SELECT {columns} FROM makro_historie_monat ORDER BY monat ASC").fetchall()
    return [MakroHistorieMonat(**dict(row)) for row in rows]


def upsert_makro_analog_ergebnis(conn: sqlite3.Connection, ergebnis: MakroAnalogErgebnis) -> None:
    conn.execute(
        "INSERT INTO makro_analog_ergebnis (berechnet_am, ergebnis_json) VALUES (?, ?) "
        "ON CONFLICT(berechnet_am) DO UPDATE SET ergebnis_json = excluded.ergebnis_json",
        (ergebnis.berechnet_am, ergebnis.ergebnis_json),
    )
    conn.commit()


def get_latest_makro_analog_ergebnis(conn: sqlite3.Connection) -> MakroAnalogErgebnis | None:
    row = conn.execute(
        "SELECT berechnet_am, ergebnis_json FROM makro_analog_ergebnis ORDER BY berechnet_am DESC LIMIT 1"
    ).fetchone()
    return MakroAnalogErgebnis(**dict(row)) if row else None


_THESE_COLUMNS = (
    "hauptgruppe", "unterkategorie", "richtung", "staerke", "begruendung",
    "pruef_mechanismus", "gesetzt_am", "review_am", "status", "quelle",
)


def _row_to_these(row: sqlite3.Row) -> These:
    return These(**dict(row))


def create_these(conn: sqlite3.Connection, these: These) -> int:
    placeholders = ", ".join("?" for _ in _THESE_COLUMNS)
    values = [getattr(these, col) for col in _THESE_COLUMNS]
    cursor = conn.execute(
        f"INSERT INTO thesen ({', '.join(_THESE_COLUMNS)}) VALUES ({placeholders})", values,
    )
    conn.commit()
    return cursor.lastrowid


def update_these(conn: sqlite3.Connection, these_id: int, these: These) -> None:
    set_clause = ", ".join(f"{col} = ?" for col in _THESE_COLUMNS)
    values = [getattr(these, col) for col in _THESE_COLUMNS] + [these_id]
    conn.execute(f"UPDATE thesen SET {set_clause} WHERE id = ?", values)
    conn.commit()


def set_these_status(conn: sqlite3.Connection, these_id: int, status: str) -> None:
    """Status-Uebergang (aktiv -> erledigt/verworfen) - eigene, kleinere Funktion
    statt immer die komplette These per update_these() neu zu schreiben, analog
    set_hebel_pruefung_erlaubt()."""
    conn.execute("UPDATE thesen SET status = ? WHERE id = ?", (status, these_id))
    conn.commit()


def get_these(conn: sqlite3.Connection, these_id: int) -> These | None:
    columns = ", ".join(("id",) + _THESE_COLUMNS)
    row = conn.execute(f"SELECT {columns} FROM thesen WHERE id = ?", (these_id,)).fetchone()
    return _row_to_these(row) if row else None


def get_aktive_thesen(conn: sqlite3.Connection) -> list[These]:
    columns = ", ".join(("id",) + _THESE_COLUMNS)
    rows = conn.execute(
        f"SELECT {columns} FROM thesen WHERE status = 'aktiv' ORDER BY gesetzt_am DESC"
    ).fetchall()
    return [_row_to_these(row) for row in rows]


def get_alle_thesen(conn: sqlite3.Connection) -> list[These]:
    columns = ", ".join(("id",) + _THESE_COLUMNS)
    rows = conn.execute(f"SELECT {columns} FROM thesen ORDER BY gesetzt_am DESC").fetchall()
    return [_row_to_these(row) for row in rows]


def get_aktive_these_fuer_kategorie(
    conn: sqlite3.Connection, hauptgruppe: str, unterkategorie: str | None = None,
) -> These | None:
    """Liefert die aktive These fuer ein Asset dieser Hauptgruppe/Unterkategorie -
    eine Unterkategorie-spezifische These hat Vorrang vor einer allgemeineren
    Hauptgruppen-These (z.B. eine gezielte These auf 'Halbleiter' vor einer
    allgemeinen These auf 'ganz Technologie'), falls beide gleichzeitig aktiv
    waeren. Gibt None zurueck, wenn keine passende aktive These existiert."""
    columns = ", ".join(("id",) + _THESE_COLUMNS)
    if unterkategorie is not None:
        row = conn.execute(
            f"SELECT {columns} FROM thesen WHERE status = 'aktiv' AND hauptgruppe = ? "
            "AND unterkategorie = ? ORDER BY gesetzt_am DESC LIMIT 1",
            (hauptgruppe, unterkategorie),
        ).fetchone()
        if row:
            return _row_to_these(row)
    row = conn.execute(
        f"SELECT {columns} FROM thesen WHERE status = 'aktiv' AND hauptgruppe = ? "
        "AND unterkategorie IS NULL ORDER BY gesetzt_am DESC LIMIT 1",
        (hauptgruppe,),
    ).fetchone()
    return _row_to_these(row) if row else None


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
    "tranchen_json",
    "cash_reserve_ziel_btc_usd", "cash_reserve_ziel_eth_usd", "cash_reserve_ziel_gesamt_usd",
    "cash_reserve_ziel_begruendung", "gegenargument", "cash_veto", "cash_veto_reason",
    "risikofaktoren_json",
)


def insert_signal(conn: sqlite3.Connection, signal: Signal) -> int:
    placeholders = ", ".join("?" for _ in _SIGNAL_COLUMNS)
    values = [
        int(getattr(signal, col)) if col in ("gate_passed", "risk_veto", "cash_veto") else getattr(signal, col)
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
    data["cash_veto"] = bool(data["cash_veto"]) if data.get("cash_veto") is not None else False
    if data["umgesetzt"] is not None:
        data["umgesetzt"] = bool(data["umgesetzt"])
    return Signal(**data)


def get_latest_signal(conn: sqlite3.Connection, symbol: str) -> Signal | None:
    row = conn.execute(
        "SELECT * FROM signals WHERE symbol = ? ORDER BY created_at DESC LIMIT 1",
        (symbol,),
    ).fetchone()
    return _row_to_signal(row) if row else None


def get_latest_regime_from_signals(conn: sqlite3.Connection) -> tuple[str, str, str] | None:
    """Regime/regime_source sind pro Pipeline-Lauf ueber alle Symbole identisch
    (agent/krypto/pipeline.py::compute_current_regime() wird einmal je Lauf
    aufgerufen) - das zuletzt erzeugte Signal, egal welches Symbol, traegt daher
    den zuletzt bekannten Regime-Stand. Reiner Lesezugriff fuer die passive
    Regime-Status-Anzeige (2026-07-17), kein neuer Live-Recompute."""
    row = conn.execute(
        "SELECT regime, regime_source, created_at FROM signals "
        "WHERE regime IS NOT NULL ORDER BY created_at DESC LIMIT 1"
    ).fetchone()
    if row is None:
        return None
    return row["regime"], row["regime_source"], row["created_at"]


def get_latest_real_signal_per_symbol(conn: sqlite3.Connection) -> dict[str, Signal]:
    """Neuestes Signal je Symbol MIT echter Groq-Analyse (Batch-Signal-
    Berechnung, 2026-07-13, siehe agent/krypto/signal_batch.py) -
    groq_raw_response IS NOT NULL statt gate_passed, da der
    AnalystResponseInvalid-Fallback-Pfad gate_passed=True setzt, OHNE dass
    tatsaechlich eine Groq-Antwort vorliegt (siehe analyst.py::
    call_groq_for_signal()). Ein Self-Join statt einer Schleife ueber
    get_latest_signal() pro Symbol, da hier alle Watchlist-Symbole auf
    einmal gebraucht werden."""
    rows = conn.execute(
        """
        SELECT s.* FROM signals s
        INNER JOIN (
            SELECT symbol, MAX(created_at) AS max_created_at
            FROM signals
            WHERE groq_raw_response IS NOT NULL
            GROUP BY symbol
        ) latest ON s.symbol = latest.symbol AND s.created_at = latest.max_created_at
        """
    ).fetchall()
    return {row["symbol"]: _row_to_signal(row) for row in rows}


def count_real_signals_today(conn: sqlite3.Connection, erlaubte_symbole: set[str] | None = None) -> int:
    """Fuer die gemeinsame Tagesbudget-Pruefung der Batch-Signal-Berechnung
    (2026-07-13, siehe agent/krypto/signal_batch.py) - zaehlt echte
    Groq-Analysen seit Mitternacht UTC (gleiche Zeitzone wie created_at
    ueberall in der DB). Zaehlt automatisch AUCH Einzel-Klicks ueber den
    bestehenden "Signal berechnen"-Button mit, da beide Wege in dieselbe
    signals-Tabelle schreiben - kein separater Zaehler noetig.

    `erlaubte_symbole` (2026-07-18, LLM-Budget-Konsistenzpruefung): diese
    Funktion war urspruenglich implizit Krypto-only (nur Krypto+gelegentlich
    manuell geklicktes Aktien schrieb in `signals`), wurde aber seit dem
    automatischen Multi-Asset-Batch (Aktien/Rohstoffe/Hedge/Themen-ETF, alle
    12h) STILLSCHWEIGEND durch dessen Signale mitgezaehlt - verfaelscht das
    Krypto-spezifische Tagesbudget (taegliches_budget_gesamt, kalibriert auf
    Kryptos Hebel/Marktscan/Spot-System) an allen 3 Aufrufstellen
    (signal_batch.py, remote/status.py, ui/marktscan_view.py). None (Default)
    = ungefiltert, wie bisher - fuer Aufrufer, die bewusst weiterhin alle
    Assetklassen zusammen zaehlen wollen."""
    today_utc_midnight = datetime.now(timezone.utc).strftime("%Y-%m-%dT00:00:00")
    if erlaubte_symbole is not None:
        if not erlaubte_symbole:
            return 0
        placeholders = ", ".join("?" for _ in erlaubte_symbole)
        row = conn.execute(
            f"SELECT COUNT(*) AS n FROM signals WHERE groq_raw_response IS NOT NULL "
            f"AND created_at >= ? AND symbol IN ({placeholders})",
            (today_utc_midnight, *erlaubte_symbole),
        ).fetchone()
        return row["n"]
    row = conn.execute(
        "SELECT COUNT(*) AS n FROM signals WHERE groq_raw_response IS NOT NULL AND created_at >= ?",
        (today_utc_midnight,),
    ).fetchone()
    return row["n"]


def get_signal_by_id(conn: sqlite3.Connection, signal_id: int) -> Signal | None:
    row = conn.execute("SELECT * FROM signals WHERE id = ?", (signal_id,)).fetchone()
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


def update_signal_outcome(
    conn: sqlite3.Connection,
    signal_id: int,
    status: str,
    entschieden_am: str | None = None,
    realisiertes_crv: float | None = None,
    datenquelle: str | None = None,
) -> None:
    """Backward-Tracking-Ergebnis (2026-07-10, Selbstverifikations-Vision Schritt 2,
    siehe agent/krypto/backward_tracking.py) - wie update_signal_umsetzung() ein
    gezieltes Update EINER bestehenden Zeile, signals bleibt fuer neue Pipeline-
    Laeufe weiterhin Append-only."""
    conn.execute(
        "UPDATE signals SET outcome_status = ?, outcome_geprueft_am = ?, "
        "outcome_entschieden_am = ?, outcome_realisiertes_crv = ?, "
        "outcome_datenquelle = ? WHERE id = ?",
        (status, _now_iso(), entschieden_am, realisiertes_crv, datenquelle, signal_id),
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


def get_pending_marktscan_kaufkandidaten(conn: sqlite3.Connection) -> list[MarktscanCandidate]:
    """Fuer den Budget-Allocator (agent/krypto/budget_allocator.py, 2026-07-14) -
    NICHT `get_marktscan_candidates(status=...)` verwenden, `status` ist die
    NUTZER-Lifecycle-Spalte ('neu'|'nutzer_behalten_manuell_uebernommen'|
    'nutzer_verworfen'), keine Scoring-Klassifikation. Neuester Eintrag je
    `coingecko_id` mit `einstufung='kaufkandidat' AND status='neu' AND
    groq_generiert_am IS NULL` (noch keine echte Begruendung erhalten),
    Self-Join analog get_pending_hebel_candidates(), sortiert nach
    score_gesamt DESC (Tier-2-Prioritaet)."""
    rows = conn.execute(
        """
        SELECT c.* FROM marktscan_candidates c
        INNER JOIN (
            SELECT coingecko_id, MAX(discovered_at) AS max_discovered_at
            FROM marktscan_candidates
            WHERE einstufung = 'kaufkandidat' AND status = 'neu' AND groq_generiert_am IS NULL
            GROUP BY coingecko_id
        ) latest
        ON c.coingecko_id = latest.coingecko_id AND c.discovered_at = latest.max_discovered_at
        WHERE c.einstufung = 'kaufkandidat' AND c.status = 'neu' AND c.groq_generiert_am IS NULL
        ORDER BY c.score_gesamt DESC
        """
    ).fetchall()
    return [_row_to_marktscan_candidate(row) for row in rows]


def get_latest_marktscan_writeup_at(conn: sqlite3.Connection, coingecko_id: str) -> str | None:
    """Fuer den Budget-Allocator-Cooldown (2026-07-14): `groq_generiert_am`
    IS NULL auf der neuesten Zeile (siehe get_pending_marktscan_kaufkandidaten())
    verhindert NICHT, dass ein Coin bei einem FRUEHEREN scan_run bereits eine
    Begruendung bekam - jeder neue Scan-Lauf legt eine neue Zeile an
    (UNIQUE(coingecko_id, scan_run_id)). Dieser Query sucht ueber ALLE Zeilen
    dieses Coins den zuletzt gesetzten Zeitstempel, unabhaengig vom scan_run_id."""
    row = conn.execute(
        "SELECT MAX(groq_generiert_am) AS letzter FROM marktscan_candidates "
        "WHERE coingecko_id = ? AND groq_generiert_am IS NOT NULL",
        (coingecko_id,),
    ).fetchone()
    return row["letzter"] if row else None


def count_real_llm_calls_today_by_provider(conn: sqlite3.Connection, provider_prefix: str) -> int:
    """Echter, providerspezifischer Tages-Zaehler (2026-07-14) - ersetzt den
    kaputten In-Memory-Zaehler in agent/krypto/budget_allocator.py
    (`cerebras_verbraucht` wurde bei JEDEM 15-Min-Lauf auf 0 zurueckgesetzt,
    eine echte Tagesgrenze konnte so nie greifen). Zaehlt ueber ALLE DREI
    Signal-erzeugenden Tabellen (hebel_signals/signals/marktscan_candidates),
    deren Provider-Spalte mit `provider_prefix` beginnt (z.B. "cerebras:",
    "gemini:") - Kern-Prinzip: jeder Anbieter soll so oft benutzt werden, wie
    sein ECHTES Kontingent hergibt, nicht durch einen Buchfuehrungs-Bug
    unbegrenzt zugelassen oder faelschlich blockiert werden."""
    today_utc_midnight = datetime.now(timezone.utc).strftime("%Y-%m-%dT00:00:00")
    like_pattern = f"{provider_prefix}%"
    total = 0
    for table, column in (
        ("hebel_signals", "llm_model"),
        ("signals", "groq_model"),
        ("marktscan_candidates", "llm_model"),
    ):
        row = conn.execute(
            f"SELECT COUNT(*) AS n FROM {table} WHERE {column} LIKE ? AND created_at >= ?"
            if table != "marktscan_candidates"
            else f"SELECT COUNT(*) AS n FROM {table} WHERE {column} LIKE ? AND groq_generiert_am >= ?",
            (like_pattern, today_utc_midnight),
        ).fetchone()
        total += row["n"]
    return total


def count_real_marktscan_writeups_today(conn: sqlite3.Connection) -> int:
    """Fuer den Budget-Allocator, analog count_real_signals_today()/
    count_real_hebel_signals_today() - zaehlt echte Groq/Cerebras-Begruendungen
    (`groq_generiert_am` gesetzt) seit Mitternacht UTC, unabhaengig ob durch
    den manuellen Button oder den Allocator ausgeloest (beide schreiben in
    dieselbe Spalte)."""
    today_utc_midnight = datetime.now(timezone.utc).strftime("%Y-%m-%dT00:00:00")
    row = conn.execute(
        "SELECT COUNT(*) AS n FROM marktscan_candidates WHERE groq_generiert_am IS NOT NULL AND groq_generiert_am >= ?",
        (today_utc_midnight,),
    ).fetchone()
    return row["n"]


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


def has_pending_marktscan_kaufkandidat(conn: sqlite3.Connection, coingecko_id: str) -> bool:
    """BUGFIX (2026-07-21, Nutzer-Fund "immer dieselben Coins" - APE/EIGEN
    bekamen am 2026-07-09 8 frische 'neu'-Zeilen innerhalb weniger Stunden,
    bevor der Nutzer reagierte): existenzielle Pruefung, ob fuer diesen Coin
    IRGENDWO in der Historie bereits eine unbearbeitete Kaufkandidat-Zeile
    (status='neu', einstufung='kaufkandidat') liegt - unabhaengig davon, ob
    das die zeitlich neueste Zeile ist (ein spaeterer Scan kann denselben
    Coin z.B. als 'kein_treffer' neu bewerten, waehrend die AELTERE
    Kaufkandidat-Zeile immer noch unbearbeitet wartet). Fuer
    marktscan.py::_duplicate_should_skip() - verhindert, dass derselbe,
    laengst entdeckte Coin bei jedem der zwei taeglichen Scan-Laeufe erneut
    dupliziert wird, waehrend die bestehende Zeile in Ruhe weiterwartet."""
    row = conn.execute(
        "SELECT 1 FROM marktscan_candidates WHERE coingecko_id = ? "
        "AND status = 'neu' AND einstufung = 'kaufkandidat' LIMIT 1",
        (coingecko_id,),
    ).fetchone()
    return row is not None


def get_letzter_marktscan_verfall_am(conn: sqlite3.Connection, coingecko_id: str) -> str | None:
    """Ergaenzung zum obigen Fix: der juengste Zeitpunkt, zu dem eine
    Kaufkandidat-Zeile dieses Coins verfallen ist (status='verfallen') -
    fuer eine kurze Abklingzeit (siehe marktscan.py::_duplicate_should_skip()),
    damit ein gerade erst verfallener Coin nicht sofort beim naechsten
    Scan-Lauf wieder auftaucht, aber nach Ablauf der Abklingzeit eine neue
    Chance bekommt (Marktlage kann sich geaendert haben)."""
    row = conn.execute(
        "SELECT MAX(status_geaendert_am) AS letzter FROM marktscan_candidates "
        "WHERE coingecko_id = ? AND status = 'verfallen' AND einstufung = 'kaufkandidat'",
        (coingecko_id,),
    ).fetchone()
    return row["letzter"] if row and row["letzter"] else None


def update_marktscan_candidate_status(conn: sqlite3.Connection, candidate_id: int, status: str) -> None:
    conn.execute(
        "UPDATE marktscan_candidates SET status = ?, status_geaendert_am = ? WHERE id = ?",
        (status, _now_iso(), candidate_id),
    )
    conn.commit()


def resolve_marktscan_candidate_siblings(conn: sqlite3.Connection, coingecko_id: str, status: str) -> int:
    """Echter Nutzer-Fund (2026-07-19, KAITO-Coin): eine Nutzer-Entscheidung
    (uebernommen/verworfen) im Marktscan-Tab galt bisher nur fuer die eine
    angeklickte Zeile (candidate.id) - jeder neue Scan-Lauf legt aber eine
    NEUE Zeile fuer denselben coingecko_id an (UNIQUE(coingecko_id,
    scan_run_id)). Aeltere/neuere status='neu'-Geschwisterzeilen desselben
    Coins blieben dadurch dauerhaft als 'neu' haengen, obwohl der Coin
    bereits entschieden/uebernommen war - sichtbar als scheinbar nie
    aktualisierter Kandidat trotz Neustart. Ausserdem indirekt relevant fuer
    get_latest_marktscan_status_by_coingecko_id() (Cross-Lauf-Duplikat-
    Check): die sortiert nach discovered_at DESC, nicht nach der zuletzt
    getroffenen Entscheidung - mit dieser Funktion tragen aber alle Zeilen
    desselben Coins konsistent denselben Status, wodurch die Sortierreihen-
    folge dort keine Rolle mehr spielt. Aufgerufen direkt NACH dem Setzen
    des Status auf der angeklickten Zeile selbst (update_marktscan_
    candidate_status()) - deckt hier zusaetzlich alle anderen noch
    status='neu' verbliebenen Zeilen desselben Coins ab. Gibt die Anzahl
    betroffener Geschwisterzeilen zurueck."""
    cursor = conn.execute(
        "UPDATE marktscan_candidates SET status = ?, status_geaendert_am = ? "
        "WHERE coingecko_id = ? AND status = 'neu'",
        (status, _now_iso(), coingecko_id),
    )
    conn.commit()
    return cursor.rowcount


def expire_stale_marktscan_candidates(
    conn: sqlite3.Connection,
    verfall_stunden: float,
    lookback_tage_cap: float = 14.0,
    luecken_toleranz_stunden: float = 20.0,
) -> int:
    """Marktscan-Pendant zu expire_stale_hebel_candidates() (2026-07-19,
    Konsistenz-Ausweitung desselben "Info-Leichen"-Fixes): setzt
    Kaufkandidaten (status='neu', noch keine LLM-Begruendung erhalten),
    deren WAHRE Wartezeit seit Erstkandidatur
    (get_marktscan_wartezeit_stunden_je_coin(), nicht das Alter der
    einzelnen Zeile) verfall_stunden uebersteigt, auf status='verfallen'.

    BUGFIX (2026-07-21, Nutzer-Fund Marktscan-Median 137h trotz 48h-Verfall):
    die urspruengliche Fassung (2026-07-19) prüfte nur `discovered_at` der
    jeweils EINZELNEN Zeile - da jeder der zwei taeglichen Scan-Laeufe eine
    neue Zeile pro Coin anlegt (UNIQUE(coingecko_id, scan_run_id), siehe
    upsert_marktscan_candidate()), ist die neueste Zeile eines weiterhin
    entdeckten Coins IMMER frisch und verfiel dadurch NIE. Jetzt wird die
    WAHRE durchgehende Kandidatur-Dauer geprueft und - falls ueberfaellig -
    die aktuell existierende status='neu'-Zeile fuer diesen Coin verfallen
    lassen. Ergaenzt weiterhin den bereits bestehenden manuellen "Ablehnen"-
    Button (status='nutzer_verworfen') um einen automatischen Rueckfall fuer
    Kandidaten, die der Nutzer nie zu Gesicht bekommt. Gibt die Anzahl
    verfallener Zeilen zurueck."""
    wartezeiten = get_marktscan_wartezeit_stunden_je_coin(conn, lookback_tage_cap, luecken_toleranz_stunden)
    betroffen = 0
    for coingecko_id, stunden in wartezeiten.items():
        if stunden < verfall_stunden:
            continue
        cursor = conn.execute(
            "UPDATE marktscan_candidates SET status = 'verfallen', status_geaendert_am = ? "
            "WHERE coingecko_id = ? AND einstufung = 'kaufkandidat' AND status = 'neu' "
            "AND groq_generiert_am IS NULL",
            (_now_iso(), coingecko_id),
        )
        betroffen += cursor.rowcount
    conn.commit()
    return betroffen


def update_marktscan_candidate_groq_writeup(
    conn: sqlite3.Connection, candidate_id: int, kurzbegruendung: str | None, langbegruendung_json: str,
    llm_model: str | None = None,
) -> None:
    """Ergaenzt eine per Klick oder automatisch (Budget-Allocator) generierte
    P-5-Begruendung auf einem bereits existierenden Kandidaten-Datensatz - kein
    neuer Scan-Lauf, reines Update. `llm_model` (2026-07-14, z.B. "cerebras:...")
    optional, damit auch dieser Tier fuer count_real_llm_calls_today_by_provider()
    zaehlbar ist - wie bei signals.groq_model/hebel_signals.llm_model."""
    conn.execute(
        "UPDATE marktscan_candidates SET groq_kurzbegruendung = ?, groq_langbegruendung_json = ?, "
        "groq_generiert_am = ?, llm_model = ? WHERE id = ?",
        (kurzbegruendung, langbegruendung_json, _now_iso(), llm_model, candidate_id),
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


# --- Hebel-Screening (2026-07-14, siehe docs/hebel_positionsformel.md) ---


def insert_oi_snapshot(conn: sqlite3.Connection, snap: OpenInterestSnapshot) -> None:
    """Ein Snapshot pro Aufruf (nicht executemany/Liste) - fetch_and_store_oi_snapshot()
    in agent/krypto/hebel_screening.py ruft das je Boerse einzeln auf, analog zum
    bisherigen anticyclic.py-Abrufmuster (jede Boerse einzeln try/except)."""
    conn.execute(
        "INSERT INTO open_interest_snapshot "
        "(symbol, exchange, open_interest, open_interest_usd, funding_rate, long_account_pct, fetched_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?) "
        "ON CONFLICT(symbol, exchange, fetched_at) DO UPDATE SET "
        "open_interest = excluded.open_interest, open_interest_usd = excluded.open_interest_usd, "
        "funding_rate = excluded.funding_rate, long_account_pct = excluded.long_account_pct",
        (
            snap.symbol, snap.exchange, snap.open_interest, snap.open_interest_usd,
            snap.funding_rate, snap.long_account_pct, snap.fetched_at,
        ),
    )
    conn.commit()


def get_oi_history(
    conn: sqlite3.Connection, symbol: str, exchange: str, min_fetched_at: str | None = None
) -> list[OpenInterestSnapshot]:
    if min_fetched_at is not None:
        rows = conn.execute(
            "SELECT symbol, exchange, open_interest, open_interest_usd, funding_rate, "
            "long_account_pct, fetched_at FROM open_interest_snapshot "
            "WHERE symbol = ? AND exchange = ? AND fetched_at >= ? ORDER BY fetched_at ASC",
            (symbol, exchange, min_fetched_at),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT symbol, exchange, open_interest, open_interest_usd, funding_rate, "
            "long_account_pct, fetched_at FROM open_interest_snapshot "
            "WHERE symbol = ? AND exchange = ? ORDER BY fetched_at ASC",
            (symbol, exchange),
        ).fetchall()
    return [OpenInterestSnapshot(**dict(row)) for row in rows]


_HEBEL_TRIGGER_COLUMNS = (
    "symbol", "richtung", "screened_at", "screening_run_id", "trigger_zweig",
    "score_gesamt", "score_details_json", "oi_change_pct_lookback",
    "kursaenderung_pct_lookback", "funding_rate_aktuell", "long_konten_anteil_prozent",
    "ist_kandidat", "status", "status_geaendert_am",
)


def insert_hebel_trigger(conn: sqlite3.Connection, trigger: HebelTrigger) -> int:
    """Plain INSERT (kein upsert) - jeder Screening-Tick ist eine eigene Bewertung,
    kein Merge-Bedarf wie bei marktscan_candidates (dort koennen Trending UND
    Top-Gainers denselben Coin im selben Lauf finden, hier nicht - ein Lauf bewertet
    jedes Symbol/Richtung-Paar genau einmal)."""
    placeholders = ", ".join("?" for _ in _HEBEL_TRIGGER_COLUMNS)
    values = [
        int(getattr(trigger, col)) if col == "ist_kandidat" else getattr(trigger, col)
        for col in _HEBEL_TRIGGER_COLUMNS
    ]
    cursor = conn.execute(
        f"INSERT INTO hebel_triggers ({', '.join(_HEBEL_TRIGGER_COLUMNS)}) VALUES ({placeholders})",
        values,
    )
    conn.commit()
    return cursor.lastrowid


def _row_to_hebel_trigger(row: sqlite3.Row) -> HebelTrigger:
    data = dict(row)
    data["ist_kandidat"] = bool(data["ist_kandidat"])
    return HebelTrigger(**data)


def get_pending_hebel_candidates(conn: sqlite3.Connection) -> list[HebelTrigger]:
    """Neuester Trigger je (symbol, richtung) mit ist_kandidat=1 UND status='neu' -
    fuer den kuenftigen Budget-Allocator (Tier 1). Self-Join analog
    get_latest_real_signal_per_symbol(), aber zusaetzlich nach richtung gruppiert,
    da LONG und SHORT desselben Symbols unabhaengige Kandidaten sein koennen."""
    rows = conn.execute(
        """
        SELECT t.* FROM hebel_triggers t
        INNER JOIN (
            SELECT symbol, richtung, MAX(screened_at) AS max_screened_at
            FROM hebel_triggers
            WHERE ist_kandidat = 1 AND status = 'neu'
            GROUP BY symbol, richtung
        ) latest
        ON t.symbol = latest.symbol AND t.richtung = latest.richtung
           AND t.screened_at = latest.max_screened_at
        WHERE t.ist_kandidat = 1 AND t.status = 'neu'
        ORDER BY t.score_gesamt DESC
        """
    ).fetchall()
    return [_row_to_hebel_trigger(row) for row in rows]


def get_hebel_wartezeit_stunden_je_paar(
    conn: sqlite3.Connection,
    lookback_tage_cap: float = 14.0,
    luecken_toleranz_stunden: float = 1.5,
    as_of: str | None = None,
) -> dict[tuple[str, str], float]:
    """Wahre Wartezeit seit ERSTMALIGER Kandidatur je (symbol, richtung) - NICHT
    das Alter der neuesten hebel_triggers-Zeile (die ist bei fortlaufender
    Requalifizierung IMMER frisch, da run_hebel_screening() bei jedem
    15-Min-Tick eine neue Zeile einfuegt statt zu upserten, siehe
    insert_hebel_trigger()-Docstring). Loest damit genau die Verschleierung,
    die die reine score_gesamt-DESC-Sortierung in get_pending_hebel_
    candidates() erzeugt: ein Paar kann zyklenlang von frischeren/hoeher
    gescorten Konkurrenten verdraengt werden, waehrend seine eigentliche
    Wartezeit unbemerkt weiterwaechst (2026-07-21, echter Fund: HYPE LONG
    116h, BTC LONG 101h, SUI SHORT 84h trotz taeglichem Neu-Screening -
    siehe extract_notebook_diagnose.py::_hebel_erstmalige_erkennung_delta(),
    die urspruengliche einmalige Diagnose-Fassung dieser Logik).

    Ermittelt je Paar die juengste durchgehende Kandidatur-Serie: von der
    neuesten zur aeltesten screened_at-Zeile laufen, Serie abbrechen sobald
    entweder die Luecke zwischen zwei aufeinanderfolgenden Treffern
    luecken_toleranz_stunden uebersteigt (ein kurzer Ausfall, z.B. ein
    OI-Abruf-Fehlschlag, soll die Kandidatur nicht faelschlich als neu
    begonnen zaehlen lassen - Korrektur gegenueber der Diagnose-Erstfassung,
    die noch keine Luecken-Toleranz hatte) oder die Grenze durch das letzte
    echte Signal fuer dieses Paar erreicht wird. Als "letztes echtes Signal"
    zaehlt JEDE Bewertung mit hebel_trigger_id IS NOT NULL - bewusst NICHT
    das strengere groq_raw_response IS NOT NULL aus
    get_latest_hebel_signal_per_symbol() - auch ein Gate-Fail-HALTEN hat das
    Paar tatsaechlich angeschaut und darf die Wartezeit-Uhr zuruecksetzen.
    Ohne vorheriges Signal begrenzt lookback_tage_cap den Rueckblick.

    as_of (optional, Default: jetzt) macht dieselbe Funktion fuer den
    historischen Backtest (backtest_budget_allocator_sla.py) wiederverwendbar
    - eine Quelle der Wahrheit fuer Live-Betrieb UND Backtest, kein
    Doppelcode. Gibt nur Paare zurueck, die seit der jeweiligen Grenze
    tatsaechlich (noch) kandidieren."""
    referenz = datetime.fromisoformat(as_of) if as_of else datetime.now(timezone.utc)
    referenz_iso = referenz.isoformat()

    letztes_signal_am: dict[tuple[str, str], str] = {}
    for row in conn.execute(
        "SELECT symbol, richtung, MAX(created_at) AS letzter FROM hebel_signals "
        "WHERE hebel_trigger_id IS NOT NULL AND created_at <= ? GROUP BY symbol, richtung",
        (referenz_iso,),
    ):
        letztes_signal_am[(row["symbol"], row["richtung"])] = row["letzter"]

    zeiten_je_paar: dict[tuple[str, str], list[datetime]] = {}
    for row in conn.execute(
        "SELECT symbol, richtung, screened_at FROM hebel_triggers "
        "WHERE ist_kandidat = 1 AND screened_at <= ? ORDER BY symbol, richtung, screened_at DESC",
        (referenz_iso,),
    ):
        paar = (row["symbol"], row["richtung"])
        zeiten_je_paar.setdefault(paar, []).append(datetime.fromisoformat(row["screened_at"]))

    ergebnis: dict[tuple[str, str], float] = {}
    for paar, zeiten in zeiten_je_paar.items():
        grenze_str = letztes_signal_am.get(paar)
        grenze = (
            datetime.fromisoformat(grenze_str) if grenze_str
            else referenz - timedelta(days=lookback_tage_cap)
        )
        if zeiten[0] <= grenze:
            continue
        streak_start = zeiten[0]
        vorheriger = zeiten[0]
        for zeitpunkt in zeiten[1:]:
            if zeitpunkt <= grenze:
                break
            luecke_stunden = (vorheriger - zeitpunkt).total_seconds() / 3600
            if luecke_stunden > luecken_toleranz_stunden:
                break
            streak_start = zeitpunkt
            vorheriger = zeitpunkt
        ergebnis[paar] = (referenz - streak_start).total_seconds() / 3600
    return ergebnis


def get_marktscan_wartezeit_stunden_je_coin(
    conn: sqlite3.Connection,
    lookback_tage_cap: float = 14.0,
    luecken_toleranz_stunden: float = 20.0,
    as_of: str | None = None,
) -> dict[str, float]:
    """Marktscan-Pendant zu get_hebel_wartezeit_stunden_je_paar() - siehe
    dortige Docstring fuer die volle Begruendung. Unterschied: marktscan_
    candidates bekommt nur 2x/Tag (04:00/16:00) eine neue Zeile pro Coin
    (statt alle 15 Min), daher die groebere Standard-Luecken-Toleranz (20h
    statt 1.5h - uebersteht das Fehlen EINES der beiden taeglichen Scans,
    nicht zweier). Gruppiert nach coingecko_id statt (symbol, richtung), da
    Marktscan-Kandidaten keine Long/Short-Richtung kennen."""
    referenz = datetime.fromisoformat(as_of) if as_of else datetime.now(timezone.utc)
    referenz_iso = referenz.isoformat()

    letzte_bewertung_am: dict[str, str] = {}
    for row in conn.execute(
        "SELECT coingecko_id, MAX(groq_generiert_am) AS letzter FROM marktscan_candidates "
        "WHERE groq_generiert_am IS NOT NULL AND groq_generiert_am <= ? GROUP BY coingecko_id",
        (referenz_iso,),
    ):
        letzte_bewertung_am[row["coingecko_id"]] = row["letzter"]

    zeiten_je_coin: dict[str, list[datetime]] = {}
    for row in conn.execute(
        "SELECT coingecko_id, discovered_at FROM marktscan_candidates "
        "WHERE einstufung = 'kaufkandidat' AND discovered_at <= ? "
        "ORDER BY coingecko_id, discovered_at DESC",
        (referenz_iso,),
    ):
        zeiten_je_coin.setdefault(row["coingecko_id"], []).append(
            datetime.fromisoformat(row["discovered_at"])
        )

    ergebnis: dict[str, float] = {}
    for coin, zeiten in zeiten_je_coin.items():
        grenze_str = letzte_bewertung_am.get(coin)
        grenze = (
            datetime.fromisoformat(grenze_str) if grenze_str
            else referenz - timedelta(days=lookback_tage_cap)
        )
        if zeiten[0] <= grenze:
            continue
        streak_start = zeiten[0]
        vorheriger = zeiten[0]
        for zeitpunkt in zeiten[1:]:
            if zeitpunkt <= grenze:
                break
            luecke_stunden = (vorheriger - zeitpunkt).total_seconds() / 3600
            if luecke_stunden > luecken_toleranz_stunden:
                break
            streak_start = zeitpunkt
            vorheriger = zeitpunkt
        ergebnis[coin] = (referenz - streak_start).total_seconds() / 3600
    return ergebnis


def get_portfolio_prioritaets_bonus_je_symbol(
    conn: sqlite3.Connection,
    watchlist: list,
    bonus_gehalten_stunden: float = 12.0,
    bonus_kern_rolle_stunden: float = 6.0,
) -> dict[str, float]:
    """Portfolio-Bezug fuer die SLA-Priorisierung im Budget-Allocator
    (2026-07-21, Nutzer-Vorgabe "Gesamtportfolio statt punktuell
    optimieren"): reduziert die effektive SLA-Schwelle eines Kandidaten, je
    relevanter das Symbol fuer das bestehende Portfolio ist - macht das
    NICHT zu einer weiteren unabhaengigen Sortierdimension (ein reiner
    Score-Boost war vom Nutzer explizit abgelehnt worden: "Prio erhoeht aber
    Delta kann weiterhin massiv sein").

    Zwei Boni, je Symbol addiert:
    - bonus_gehalten_stunden: Symbol wird bereits gehalten (Spot-Holding
      ODER offene Hebel-Position) - Wiederbewertung von bestehendem Risiko
      ist dringlicher als eine neue, noch nicht eingegangene Chance.
      Identisches Muster wie remote/status.py::build_status() (dortige
      gehaltene_symbole/offene_hebel_symbole-Sets).
    - bonus_kern_rolle_stunden: WatchlistAsset.rolle == 'core' - rein
      manuelles, strategisches Signal, UNABHAENGIG vom aktuellen Bestand
      (siehe config.py::WatchlistAsset-Docstring: "ein core-Asset kann z.B.
      noch nie gehalten worden sein - bewusster Erstkauf-Kandidat").
      Urspruenglich war hier eine These-basierte Diversifikations-Kopplung
      geplant, die aber fuer Krypto (Hebel/Marktscan sind reine Krypto-
      Tiers) NIE gegriffen haette - Basisinfos/kategorien.yaml schliesst
      Krypto bewusst aus (siehe Kopfkommentar), database/models.py::
      These-Docstring haelt das explizit fest."""
    gehaltene_symbole = {
        h.symbol for h in get_all_holdings(conn)
        if (h.quantity or 0.0) + (h.staked_quantity or 0.0) > 0.0
    }
    offene_hebel_symbole = {p.symbol for p in get_open_hebel_positions(conn)}

    ergebnis: dict[str, float] = {}
    for asset in watchlist:
        bonus = 0.0
        if asset.symbol in gehaltene_symbole or asset.symbol in offene_hebel_symbole:
            bonus += bonus_gehalten_stunden
        if getattr(asset, "rolle", None) == "core":
            bonus += bonus_kern_rolle_stunden
        if bonus:
            ergebnis[asset.symbol] = bonus
    return ergebnis


def update_hebel_trigger_status(conn: sqlite3.Connection, trigger_id: int, status: str) -> None:
    conn.execute(
        "UPDATE hebel_triggers SET status = ?, status_geaendert_am = ? WHERE id = ?",
        (status, _now_iso(), trigger_id),
    )
    conn.commit()


def expire_stale_hebel_candidates(
    conn: sqlite3.Connection,
    verfall_stunden: float,
    lookback_tage_cap: float = 14.0,
    luecken_toleranz_stunden: float = 1.5,
) -> int:
    """Setzt Trigger-Kandidaten (status='neu'), deren WAHRE Wartezeit seit
    Erstkandidatur (get_hebel_wartezeit_stunden_je_paar(), nicht das Alter
    der einzelnen Zeile) verfall_stunden uebersteigt, auf status='verfallen'
    - verhindert, dass laengst ueberholte Marktbedingungen dauerhaft in
    get_pending_hebel_candidates() (UI-Warteliste UND Budget-Allocator-
    Auswahlpool, beide filtern nur auf status='neu') haengen bleiben.

    BUGFIX (2026-07-21, Nutzer-Fund HYPE LONG 116h/BTC LONG 101h trotz 48h-
    Verfall): die urspruengliche Fassung (2026-07-19) prüfte nur
    `screened_at` der jeweils EINZELNEN Zeile - bei fortlaufender
    Requalifizierung (jeder 15-Min-Tick legt eine neue Zeile an, siehe
    insert_hebel_trigger()) ist die neueste Zeile IMMER frisch und verfiel
    dadurch NIE, egal wie lange das Paar tatsaechlich schon wartete. Jetzt
    wird die WAHRE durchgehende Kandidatur-Dauer geprueft und - falls
    ueberfaellig - die aktuell existierende status='neu'-Zeile fuer dieses
    Paar verfallen lassen (nicht mehr zeilenweise per WHERE-Vergleich).
    Gibt die Anzahl der soeben verfallenen Zeilen zurueck."""
    wartezeiten = get_hebel_wartezeit_stunden_je_paar(conn, lookback_tage_cap, luecken_toleranz_stunden)
    betroffen = 0
    for (symbol, richtung), stunden in wartezeiten.items():
        if stunden < verfall_stunden:
            continue
        cursor = conn.execute(
            "UPDATE hebel_triggers SET status = 'verfallen', status_geaendert_am = ? "
            "WHERE symbol = ? AND richtung = ? AND status = 'neu' AND ist_kandidat = 1",
            (_now_iso(), symbol, richtung),
        )
        betroffen += cursor.rowcount
    conn.commit()
    return betroffen


_HEBEL_POSITION_COLUMNS = (
    "symbol", "richtung", "status", "eroeffnet_am", "geschlossen_am",
    "hebel_effektiv", "positionswert_eur", "kreditbetrag_eur", "eigenkapital_eur",
    "positionsmenge", "letzte_transaktion_unix_timestamp", "liquidationspreis_geschaetzt_eur",
    "liquidationspreis_berechnet_am", "quelle_tags_json",
)


def upsert_hebel_position(conn: sqlite3.Connection, pos: HebelPosition) -> int:
    """`(symbol, eroeffnet_am)` identifiziert eine Position eindeutig - ein erneuter
    Sync derselben (noch offenen oder inzwischen geschlossenen) Position aktualisiert
    dieselbe Zeile, analog upsert_marktscan_candidate()."""
    placeholders = ", ".join("?" for _ in _HEBEL_POSITION_COLUMNS)
    update_clause = ", ".join(
        f"{col} = excluded.{col}"
        for col in _HEBEL_POSITION_COLUMNS
        if col not in ("symbol", "eroeffnet_am")
    )
    values = [getattr(pos, col) for col in _HEBEL_POSITION_COLUMNS]
    cursor = conn.execute(
        f"INSERT INTO hebel_positions ({', '.join(_HEBEL_POSITION_COLUMNS)}) "
        f"VALUES ({placeholders}) "
        f"ON CONFLICT(symbol, eroeffnet_am) DO UPDATE SET {update_clause}",
        values,
    )
    conn.commit()
    return cursor.lastrowid


def _row_to_hebel_position(row: sqlite3.Row) -> HebelPosition:
    return HebelPosition(**dict(row))


def get_open_hebel_positions(conn: sqlite3.Connection, symbol: str | None = None) -> list[HebelPosition]:
    if symbol is not None:
        rows = conn.execute(
            "SELECT * FROM hebel_positions WHERE status = 'offen' AND symbol = ? ORDER BY eroeffnet_am ASC",
            (symbol,),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM hebel_positions WHERE status = 'offen' ORDER BY eroeffnet_am ASC"
        ).fetchall()
    return [_row_to_hebel_position(row) for row in rows]


def get_hebel_position_last_synced_unix(conn: sqlite3.Connection) -> int | None:
    """Globaler Wasserstand, analog get_bitpanda_avg_cost_last_synced_unix() -
    Bitpanda liefert Transaktionen ueber alle Symbole gemischt, neueste zuerst."""
    row = conn.execute(
        "SELECT value FROM meta WHERE key = 'hebel_position_last_synced_unix'"
    ).fetchone()
    if row is None or row["value"] is None:
        return None
    try:
        return int(row["value"])
    except ValueError:
        return None


def set_hebel_position_last_synced_unix(conn: sqlite3.Connection, unix_timestamp: int) -> None:
    conn.execute(
        "INSERT INTO meta (key, value) VALUES ('hebel_position_last_synced_unix', ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (str(unix_timestamp),),
    )
    conn.commit()


_HEBEL_SIGNAL_COLUMNS = (
    "symbol", "created_at", "pipeline_version", "richtung", "action",
    "hebel_vorschlag", "hebel_final", "hebel_korrektur_hinweis", "trade_thesis_typ",
    "hebel_trigger_id", "trigger_zweig", "trigger_score",
    "confidence_pct", "short_reasoning", "long_reasoning_technisch",
    "long_reasoning_fundamental", "long_reasoning_makro",
    "entry_usd_von", "entry_usd_bis", "entry_eur_von", "entry_eur_bis",
    "stop_loss_usd_von", "stop_loss_usd_bis", "stop_loss_eur_von", "stop_loss_eur_bis",
    "take_profit_usd_von", "take_profit_usd_bis", "take_profit_eur_von", "take_profit_eur_bis",
    "halte_kriterium_bucket", "halte_kriterium_ziel_preis_usd", "halte_kriterium_ziel_preis_eur",
    "halte_kriterium_ziel_datum", "halte_kriterium_bedingung_text", "halte_kriterium_reasoning",
    "top_grund_1_kategorie", "top_grund_1_text", "top_grund_2_kategorie", "top_grund_2_text",
    "top_grund_3_kategorie", "top_grund_3_text", "top_grund_4_kategorie", "top_grund_4_text",
    "top_grund_5_kategorie", "top_grund_5_text",
    "key_risks_text", "regime", "regime_source", "forecast_bull_text", "forecast_bull_prob_pct",
    "forecast_base_text", "forecast_base_prob_pct", "forecast_bear_text", "forecast_bear_prob_pct",
    "liquidationspreis_geschaetzt_usd", "eigenkapitalbedarf_usd",
    "hebel_senkung_eigenkapital_nachschuss_eur", "ausfuehrbarkeit_hinweis",
    "gate_passed", "gate_reason", "risk_veto", "risk_veto_reason", "facts_json",
    "groq_raw_response", "llm_model", "gegenargument", "risikofaktoren_json",
)


def insert_hebel_signal(conn: sqlite3.Connection, signal: HebelSignal) -> int:
    """Append-only wie insert_signal() - jeder Hebel-Analyst-Lauf ist eine eigene
    Zeile, kein Upsert."""
    placeholders = ", ".join("?" for _ in _HEBEL_SIGNAL_COLUMNS)
    values = [
        int(getattr(signal, col)) if col in ("gate_passed", "risk_veto") else getattr(signal, col)
        for col in _HEBEL_SIGNAL_COLUMNS
    ]
    cursor = conn.execute(
        f"INSERT INTO hebel_signals ({', '.join(_HEBEL_SIGNAL_COLUMNS)}) VALUES ({placeholders})",
        values,
    )
    conn.commit()
    return cursor.lastrowid


def _row_to_hebel_signal(row: sqlite3.Row) -> HebelSignal:
    data = dict(row)
    data["gate_passed"] = bool(data["gate_passed"])
    data["risk_veto"] = bool(data["risk_veto"])
    return HebelSignal(**data)


def get_latest_hebel_signal_per_symbol(conn: sqlite3.Connection) -> dict[str, HebelSignal]:
    """Neuestes Hebel-Signal je Symbol MIT echter LLM-Analyse, analog
    get_latest_real_signal_per_symbol() - groq_raw_response IS NOT NULL statt
    gate_passed, aus demselben Grund (AnalystResponseInvalid-Fallback setzt
    gate_passed=True ohne echte Antwort)."""
    rows = conn.execute(
        """
        SELECT s.* FROM hebel_signals s
        INNER JOIN (
            SELECT symbol, MAX(created_at) AS max_created_at
            FROM hebel_signals
            WHERE groq_raw_response IS NOT NULL
            GROUP BY symbol
        ) latest ON s.symbol = latest.symbol AND s.created_at = latest.max_created_at
        """
    ).fetchall()
    return {row["symbol"]: _row_to_hebel_signal(row) for row in rows}


def get_hebel_signal_history(
    conn: sqlite3.Connection, symbol: str, richtung: str, limit: int = 20,
) -> list[HebelSignal]:
    """Wie get_signal_history(), aber fuer hebel_signals - nach (symbol,
    richtung) gefiltert (2026-07-16, ui/hebel_view.py::HebelSignalHistoryDialog):
    LONG/SHORT sind unabhaengige Thesen (siehe hebel_backward_tracking.py::
    _is_superseded()), eine gemeinsame Historie waere irrefuehrend."""
    rows = conn.execute(
        "SELECT * FROM hebel_signals WHERE symbol = ? AND richtung = ? ORDER BY created_at DESC LIMIT ?",
        (symbol, richtung, limit),
    ).fetchall()
    return [_row_to_hebel_signal(row) for row in rows]


def get_latest_hebel_signal_per_symbol_and_richtung(conn: sqlite3.Connection) -> dict[tuple[str, str], HebelSignal]:
    """Wie get_latest_hebel_signal_per_symbol(), aber zusaetzlich nach `richtung`
    gruppiert (2026-07-16, Ueberholt-Erkennung in hebel_backward_tracking.py::
    _is_superseded()) - ein LONG- und ein SHORT-Signal fuer denselben Coin sind
    zwei unabhaengige Thesen, eines macht das andere nicht ueberholt."""
    rows = conn.execute(
        """
        SELECT s.* FROM hebel_signals s
        INNER JOIN (
            SELECT symbol, richtung, MAX(created_at) AS max_created_at
            FROM hebel_signals
            WHERE groq_raw_response IS NOT NULL
            GROUP BY symbol, richtung
        ) latest ON s.symbol = latest.symbol AND s.richtung = latest.richtung
            AND s.created_at = latest.max_created_at
        """
    ).fetchall()
    return {(row["symbol"], row["richtung"]): _row_to_hebel_signal(row) for row in rows}


def count_real_hebel_signals_today(conn: sqlite3.Connection) -> int:
    """Fuer den kuenftigen Budget-Allocator (docs/budget_queue_design.md), analog
    count_real_signals_today() - zaehlt echte LLM-Analysen (Groq ODER Cerebras)
    seit Mitternacht UTC."""
    today_utc_midnight = datetime.now(timezone.utc).strftime("%Y-%m-%dT00:00:00")
    row = conn.execute(
        "SELECT COUNT(*) AS n FROM hebel_signals WHERE groq_raw_response IS NOT NULL AND created_at >= ?",
        (today_utc_midnight,),
    ).fetchone()
    return row["n"]


def get_hebel_signal_by_id(conn: sqlite3.Connection, hebel_signal_id: int) -> HebelSignal | None:
    row = conn.execute("SELECT * FROM hebel_signals WHERE id = ?", (hebel_signal_id,)).fetchone()
    return _row_to_hebel_signal(row) if row else None


def update_hebel_signal_outcome(
    conn: sqlite3.Connection,
    hebel_signal_id: int,
    status: str,
    entschieden_am: str | None = None,
    realisiertes_crv: float | None = None,
    datenquelle: str | None = None,
) -> None:
    """Wie update_signal_outcome(), aber fuer hebel_signals (2026-07-15, Hebel-
    Backward-Tracking - siehe agent/krypto/hebel_backward_tracking.py)."""
    conn.execute(
        "UPDATE hebel_signals SET outcome_status = ?, outcome_geprueft_am = ?, "
        "outcome_entschieden_am = ?, outcome_realisiertes_crv = ?, "
        "outcome_datenquelle = ? WHERE id = ?",
        (status, _now_iso(), entschieden_am, realisiertes_crv, datenquelle, hebel_signal_id),
    )
    conn.commit()


def record_api_health_success(conn: sqlite3.Connection, source: str) -> None:
    """Passives API-Gesundheits-Tracking (2026-07-15, siehe database/api_health.py::
    track_api_health()) - Upsert, laesst etwaige Fehler-Felder unangetastet (ein
    Erfolg loescht nicht die Erinnerung an den letzten Fehler, get_api_health_status()
    vergleicht beide Zeitstempel)."""
    conn.execute(
        "INSERT INTO api_health_status (source, last_success_at) VALUES (?, ?) "
        "ON CONFLICT(source) DO UPDATE SET last_success_at = excluded.last_success_at",
        (source, _now_iso()),
    )
    conn.commit()


def record_api_health_error(conn: sqlite3.Connection, source: str, error_type: str, error_message: str) -> None:
    """Wie record_api_health_success(), aber fuer einen Fehlschlag - laesst
    last_success_at unangetastet."""
    conn.execute(
        "INSERT INTO api_health_status (source, last_error_at, last_error_type, last_error_message) "
        "VALUES (?, ?, ?, ?) "
        "ON CONFLICT(source) DO UPDATE SET last_error_at = excluded.last_error_at, "
        "last_error_type = excluded.last_error_type, last_error_message = excluded.last_error_message",
        (source, _now_iso(), error_type, error_message),
    )
    conn.commit()


def get_api_health_status(conn: sqlite3.Connection) -> dict[str, dict]:
    """Liest alle bekannten Quellen mit einem abgeleiteten 'status'-Feld:
    'ok' (letzter Erfolg ist juenger als/gleichauf mit dem letzten Fehler, oder es
    gab noch nie einen Fehler), 'fehler' (letzter Fehler ist juenger als der letzte
    Erfolg, oder es gab noch nie einen Erfolg), 'unbekannt' (weder Erfolg noch
    Fehler bisher aufgezeichnet - sollte praktisch nicht vorkommen, da ein Upsert
    immer mindestens ein Feld setzt)."""
    rows = conn.execute("SELECT * FROM api_health_status").fetchall()
    ergebnis: dict[str, dict] = {}
    for row in rows:
        last_success_at = row["last_success_at"]
        last_error_at = row["last_error_at"]
        if last_success_at is None and last_error_at is None:
            status = "unbekannt"
        elif last_error_at is None:
            status = "ok"
        elif last_success_at is None:
            status = "fehler"
        else:
            status = "ok" if last_success_at >= last_error_at else "fehler"
        ergebnis[row["source"]] = {
            "status": status,
            "last_success_at": last_success_at,
            "last_error_at": last_error_at,
            "last_error_type": row["last_error_type"],
            "last_error_message": row["last_error_message"],
        }
    return ergebnis


def record_oi_abdeckung_ergebnis(conn: sqlite3.Connection, symbol: str, erfolg: bool) -> int:
    """OI-Abdeckungs-Status je Symbol (2026-07-19, siehe Schema-Kommentar) -
    bei Erfolg wird der Fehlschlag-Zaehler zurueckgesetzt und letzter_erfolg_at
    aktualisiert; bei Fehlschlag nur der Zaehler erhoeht (letzter_erfolg_at
    bleibt als "wann zuletzt ok" stehen). Gibt den NEUEN Zaehlerstand zurueck,
    damit der Aufrufer (hebel_screening.py) ohne zweite Abfrage weiss, ob
    gerade eine Schwelle ueberschritten wurde."""
    if erfolg:
        conn.execute(
            "INSERT INTO oi_abdeckung_status (symbol, konsekutive_fehlschlaege, letzter_erfolg_at) "
            "VALUES (?, 0, ?) "
            "ON CONFLICT(symbol) DO UPDATE SET konsekutive_fehlschlaege = 0, letzter_erfolg_at = excluded.letzter_erfolg_at",
            (symbol, _now_iso()),
        )
        conn.commit()
        return 0
    conn.execute(
        "INSERT INTO oi_abdeckung_status (symbol, konsekutive_fehlschlaege) VALUES (?, 1) "
        "ON CONFLICT(symbol) DO UPDATE SET konsekutive_fehlschlaege = konsekutive_fehlschlaege + 1",
        (symbol,),
    )
    conn.commit()
    row = conn.execute(
        "SELECT konsekutive_fehlschlaege FROM oi_abdeckung_status WHERE symbol = ?", (symbol,)
    ).fetchone()
    return row["konsekutive_fehlschlaege"]


def get_oi_abdeckung_status(conn: sqlite3.Connection) -> dict[str, dict]:
    """Fuer die GUI (Watchlist-Tab-Markierung) - kompletter Status aller
    jemals gescreenten Symbole, keine Filterung nach Schwelle (das entscheidet
    der Aufrufer/die UI selbst anhand von config.yaml)."""
    rows = conn.execute("SELECT * FROM oi_abdeckung_status").fetchall()
    return {row["symbol"]: dict(row) for row in rows}


def get_symbole_mit_ueberschrittener_oi_schwelle(
    conn: sqlite3.Connection, schwelle: int, cooldown_stunden: float,
) -> list[str]:
    """Symbole, die die Fehlschlag-Schwelle erreicht/ueberschritten haben UND
    entweder noch nie gemeldet wurden oder deren letzte Meldung laenger als
    der Cooldown zurueckliegt (verhindert taegliche Wiederholungs-Mails fuer
    ein bereits bekanntes, weiterhin ungeloestes Problem, gleiches Prinzip wie
    scheduler/background.py::_notify_cash_veto_warning()).

    BUGFIX (2026-07-20, echter Nutzer-Fund: CANTON wurde ueber den Hebel-
    Pruefung-Toggle abgeschaltet, meldete aber weiter per E-Mail). Grund:
    `oi_abdeckung_status.konsekutive_fehlschlaege` wird ausschliesslich in
    hebel_screening.py::run_hebel_screening() erhoeht/zurueckgesetzt - sobald
    ein Symbol per Toggle aus der Neuentdeckung ausgeschlossen ist (siehe
    dortiger Docstring), laeuft fuer dieses Symbol schlicht kein Lauf mehr,
    der Zaehler bleibt fuer immer auf dem letzten Stand eingefroren. Ohne
    diesen JOIN blieb ein einmal ueber der Schwelle liegender, dann
    abgeschalteter Zaehler trotzdem dauerhaft >= schwelle und loeste nach
    jedem Cooldown-Ablauf eine neue, inhaltlich falsche "seit N Laeufen"-
    Warnmail aus, obwohl laengst keine neuen Laeufe mehr stattfanden.
    COALESCE-Default 1 (erlaubt), da fehlende asset_hebel_settings-Zeile
    laut get_hebel_pruefung_erlaubt() ebenfalls "erlaubt" bedeutet."""
    grenze = (datetime.now(timezone.utc) - timedelta(hours=cooldown_stunden)).isoformat()
    rows = conn.execute(
        "SELECT o.symbol FROM oi_abdeckung_status o "
        "LEFT JOIN asset_hebel_settings s ON s.symbol = o.symbol "
        "WHERE o.konsekutive_fehlschlaege >= ? "
        "AND (o.zuletzt_gemeldet_at IS NULL OR o.zuletzt_gemeldet_at < ?) "
        "AND COALESCE(s.hebel_pruefung_erlaubt, 1) = 1",
        (schwelle, grenze),
    ).fetchall()
    return [row["symbol"] for row in rows]


def set_oi_abdeckung_gemeldet(conn: sqlite3.Connection, symbol: str) -> None:
    conn.execute(
        "UPDATE oi_abdeckung_status SET zuletzt_gemeldet_at = ? WHERE symbol = ?",
        (_now_iso(), symbol),
    )
    conn.commit()
