"""Hintergrund-Scheduler: periodischer Preis-Refresh in die SQLite-Cache (B-1)."""
from __future__ import annotations

import logging

from apscheduler.schedulers.background import BackgroundScheduler

import database.db as db

logger = logging.getLogger(__name__)

REFRESH_INTERVAL_MINUTES = 5


def refresh_prices_job(client, conn_factory, watchlist) -> None:
    conn = conn_factory()
    try:
        snapshots = client.fetch_price_snapshots(watchlist)
        for snapshot in snapshots:
            db.insert_price_snapshot(conn, snapshot)
        logger.info("Preis-Refresh: %d/%d Assets aktualisiert", len(snapshots), len(watchlist))
    except Exception:
        logger.exception("Preis-Refresh fehlgeschlagen")
    finally:
        conn.close()


def build_scheduler(coingecko_client, db_conn_factory, watchlist_provider) -> BackgroundScheduler:
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        refresh_prices_job,
        "interval",
        minutes=REFRESH_INTERVAL_MINUTES,
        args=[coingecko_client, db_conn_factory, watchlist_provider()],
        id="refresh_prices",
    )
    return scheduler
