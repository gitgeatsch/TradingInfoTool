"""Einstiegspunkt: DB init -> Erstimport (falls noetig) -> Scheduler -> UI."""
from __future__ import annotations

import logging
import os

import config
import database.db as db
import ui.app as app
from api.coingecko import CoinGeckoClient
from api.history import backfill_all
from api.kraken import KrakenClient
from api.kraken_history import backfill_all_ohlc
from importer.excel_import import import_holdings
from scheduler.background import build_scheduler

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    config.load_env()
    coingecko_api_key = os.environ.get("COINGECKO_API_KEY")
    if coingecko_api_key:
        logger.info("CoinGecko API-Key gefunden (100 Req/Min statt 30).")
    else:
        logger.info("Kein CoinGecko API-Key gesetzt - anonymer Zugriff (30 Req/Min).")

    watchlist = config.get_watchlist()

    conn = db.get_connection()
    db.init_db(conn)

    if db.is_first_run(conn):
        result = import_holdings(conn)
        logger.info("Erstimport: %d Bestände importiert.", result.imported_count)
        for warning in result.warnings:
            logger.warning(warning)

    coingecko_client = CoinGeckoClient(api_key=coingecko_api_key)

    if db.is_history_first_run(conn):
        results = backfill_all(coingecko_client, conn, watchlist)
        degraded = [r for r in results if r.degraded]
        logger.info(
            "Historie-Erstbefüllung: %d/%d Assets, %d degradiert",
            len(results) - len(degraded),
            len(results),
            len(degraded),
        )
        for r in degraded:
            logger.warning("Historie für %s unvollständig: %s", r.coingecko_id, r.reason)
        db.mark_history_backfilled(conn)

    kraken_client = KrakenClient()

    if db.is_ohlc_first_run(conn):
        ohlc_results = backfill_all_ohlc(kraken_client, conn, watchlist)
        ohlc_skipped = [r for r in ohlc_results if r.skipped]
        ohlc_degraded = [r for r in ohlc_results if r.degraded]
        logger.info(
            "Kraken-OHLC-Erstbefüllung: %d/%d Assets, %d ohne Kraken-Listing, %d degradiert",
            len(ohlc_results) - len(ohlc_skipped) - len(ohlc_degraded),
            len(ohlc_results),
            len(ohlc_skipped),
            len(ohlc_degraded),
        )
        for r in ohlc_degraded:
            logger.warning("Kraken-OHLC für %s unvollständig: %s", r.symbol, r.reason)
        db.mark_ohlc_backfilled(conn)

    conn.close()

    bg_scheduler = build_scheduler(
        coingecko_client=coingecko_client,
        kraken_client=kraken_client,
        db_conn_factory=db.get_connection,
        watchlist_provider=lambda: watchlist,
    )
    bg_scheduler.start()

    try:
        app.run_app(
            db_conn_factory=db.get_connection,
            watchlist=watchlist,
            coingecko_client=coingecko_client,
        )
    finally:
        bg_scheduler.shutdown(wait=False)


if __name__ == "__main__":
    main()
