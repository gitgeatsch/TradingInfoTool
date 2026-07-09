"""Hintergrund-Scheduler: periodischer Preis-Refresh in die SQLite-Cache (B-1)."""
from __future__ import annotations

import logging

from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_MISSED
from apscheduler.schedulers.background import BackgroundScheduler

import database.db as db
from api.history import backfill_all
from api.kraken_history import backfill_all_ohlc

logger = logging.getLogger(__name__)

REFRESH_INTERVAL_MINUTES = 15  # Verbrauchsreduzierung: 15 statt 5 Min (siehe Kap. 16/8,
# Monats-Kontingent-Rechnung 2026-07-06 - 5 Min haette zusammen mit dem taeglichen
# Historie-Refresh das 10.000/Monat-Limit ueberschritten)
HISTORY_REFRESH_INTERVAL_HOURS = 24
OHLC_REFRESH_INTERVAL_HOURS = 24  # eigener Job, oeffentliche Kraken-Endpunkte teilen sich
# kein Kontingent mit CoinGecko - unabhaengig vom Historie-Refresh getaktet


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


def refresh_history_job(client, conn_factory, watchlist) -> None:
    conn = conn_factory()
    try:
        results = backfill_all(client, conn, watchlist)
        degraded = [r for r in results if r.degraded]
        logger.info(
            "Historie-Refresh: %d/%d Assets aktualisiert (%d degradiert)",
            len(results) - len(degraded),
            len(results),
            len(degraded),
        )
    except Exception:
        logger.exception("Historie-Refresh fehlgeschlagen")
    finally:
        conn.close()


def refresh_ohlc_job(client, conn_factory, watchlist) -> None:
    conn = conn_factory()
    try:
        results = backfill_all_ohlc(client, conn, watchlist)
        degraded = [r for r in results if r.degraded]
        skipped = [r for r in results if r.skipped]
        logger.info(
            "Kraken-OHLC-Refresh: %d/%d Assets aktualisiert (%d ohne Listing, %d degradiert)",
            len(results) - len(degraded) - len(skipped),
            len(results),
            len(skipped),
            len(degraded),
        )
    except Exception:
        logger.exception("Kraken-OHLC-Refresh fehlgeschlagen")
    finally:
        conn.close()


def marktscan_job(coingecko_client, kraken_client, groq_client, conn_factory, watchlist, fred_api_key) -> None:
    """MS-3: 2x taeglich (04:00/16:00, siehe build_scheduler()) - kompletter
    Marktscan-Lauf (Stufe A-D, agent/marktscan.py). Braucht ein aktuelles Regime
    (R-5.1 + Liquiditaets-Regime + Zyklus-Risiko) fuer Stufe C/D, dafuer dieselbe
    Logik wie agent/pipeline.py::generate_signal() (compute_current_regime(), nicht
    dupliziert). `groq_client` kann None sein (P-8) - dann greift nur der manuelle
    UI-Klick-Pfad fuer P-5-Begruendungen, keine automatischen."""
    conn = conn_factory()
    try:
        import config as config_module
        from agent.marktscan import run_scan
        from agent.pipeline import compute_current_regime

        config_dict = config_module.load_config()
        if not config_dict["marktscan"].get("aktiv", True):
            logger.info("Marktscan deaktiviert (config.yaml marktscan.aktiv=false) - übersprungen")
            return

        regime_result = compute_current_regime(conn, coingecko_client, watchlist, fred_api_key, config_dict)
        candidates = run_scan(
            coingecko_client, conn, watchlist, regime_result, config_dict,
            groq_client=groq_client, kraken_client=kraken_client,
        )
        treffer = [c for c in candidates if c.einstufung in ("kaufkandidat", "watchlist_wuerdig")]
        logger.info(
            "Marktscan: %d Kandidaten bewertet (%d Treffer: watchlist_würdig/Kaufkandidat, Regime %s)",
            len(candidates), len(treffer), regime_result.regime,
        )
    except Exception:
        logger.exception("Marktscan fehlgeschlagen")
    finally:
        conn.close()


def _log_job_event(event) -> None:
    """U-12-Minimalfix (2026-07-09): jeder Job faengt seine eigenen Exceptions
    bereits selbst ab (siehe *_job()-Funktionen oben) - dieser Listener ist die
    zweite Verteidigungslinie fuer alles, was DENNOCH bis zum Scheduler durchschlaegt
    (z.B. ein Bug im Job-Wrapper selbst), UND faengt zusaetzlich verpasste Laeufe ab
    (EVENT_JOB_MISSED - z.B. wenn der Rechner zur geplanten Zeit im Standby war),
    was bisher komplett unsichtbar blieb."""
    if event.exception:
        logger.error("Scheduler-Job '%s' fehlgeschlagen (unbehandelt): %s", event.job_id, event.exception)
    else:
        logger.warning("Scheduler-Job '%s' verpasst (Misfire)", event.job_id)


def build_scheduler(
    coingecko_client, kraken_client, db_conn_factory, watchlist_provider,
    groq_client=None, fred_api_key=None,
) -> BackgroundScheduler:
    watchlist = watchlist_provider()
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        refresh_prices_job,
        "interval",
        minutes=REFRESH_INTERVAL_MINUTES,
        args=[coingecko_client, db_conn_factory, watchlist],
        id="refresh_prices",
    )
    scheduler.add_job(
        refresh_history_job,
        "interval",
        hours=HISTORY_REFRESH_INTERVAL_HOURS,
        args=[coingecko_client, db_conn_factory, watchlist],
        id="refresh_history",
    )
    scheduler.add_job(
        refresh_ohlc_job,
        "interval",
        hours=OHLC_REFRESH_INTERVAL_HOURS,
        args=[kraken_client, db_conn_factory, watchlist],
        id="refresh_ohlc",
    )
    # MS-3: erster CronTrigger im Projekt (bisherige Jobs nutzen nur "interval") -
    # feste Uhrzeiten statt Intervall, siehe config.yaml marktscan.zeiten.
    scheduler.add_job(
        marktscan_job,
        "cron",
        hour="4,16",
        minute=0,
        args=[coingecko_client, kraken_client, groq_client, db_conn_factory, watchlist, fred_api_key],
        id="marktscan",
    )
    scheduler.add_listener(_log_job_event, EVENT_JOB_ERROR | EVENT_JOB_MISSED)
    return scheduler
