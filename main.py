"""Einstiegspunkt: DB init -> Erstimport (falls noetig) -> Scheduler -> UI."""
from __future__ import annotations

import logging

import config
import database.db as db
import ui.app as app
from api.coingecko import CoinGeckoClient
from importer.excel_import import import_holdings
from scheduler.background import build_scheduler

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    watchlist = config.get_watchlist()

    conn = db.get_connection()
    db.init_db(conn)

    if db.is_first_run(conn):
        result = import_holdings(conn)
        logger.info("Erstimport: %d Bestände importiert.", result.imported_count)
        for warning in result.warnings:
            logger.warning(warning)

    conn.close()

    coingecko_client = CoinGeckoClient()

    bg_scheduler = build_scheduler(
        coingecko_client=coingecko_client,
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
