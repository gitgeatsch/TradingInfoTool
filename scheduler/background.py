"""Hintergrund-Scheduler: periodischer Preis-Refresh in die SQLite-Cache (B-1)."""
from __future__ import annotations

import logging
import threading
import time

from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_MISSED
from apscheduler.schedulers.background import BackgroundScheduler

import database.db as db
from api.history import backfill_all
from api.kraken_history import backfill_all_ohlc
from api.yfinance_client import YFinanceClient

logger = logging.getLogger(__name__)

# Remote-Steuer-Seite (2026-07-11): ein Lock pro Job, geteilt zwischen dem
# normalen Scheduler-Takt UND einem kuenftigen manuellen Remote-Trigger (siehe
# remote/server.py) - verhindert, dass derselbe Job doppelt gleichzeitig
# laeuft, egal wodurch die Kollision ausgeloest wird. _job_started_at haelt
# fest, seit wann ein Job laeuft (fuer eine "laeuft seit X Min"-Anzeige +
# Grundlage fuer den Not-Reset, siehe get_lock_status()/force_release_lock()).
refresh_prices_lock = threading.Lock()
refresh_securities_lock = threading.Lock()
marktscan_lock = threading.Lock()
_JOB_LOCKS = {
    "refresh_prices": refresh_prices_lock,
    "refresh_securities": refresh_securities_lock,
    "marktscan": marktscan_lock,
}
_job_started_at: dict[str, float] = {}

REFRESH_INTERVAL_MINUTES = 15  # Verbrauchsreduzierung: 15 statt 5 Min (siehe Kap. 16/8,
# Monats-Kontingent-Rechnung 2026-07-06 - 5 Min haette zusammen mit dem taeglichen
# Historie-Refresh das 10.000/Monat-Limit ueberschritten)
HISTORY_REFRESH_INTERVAL_HOURS = 24
OHLC_REFRESH_INTERVAL_HOURS = 24  # eigener Job, oeffentliche Kraken-Endpunkte teilen sich
# kein Kontingent mit CoinGecko - unabhaengig vom Historie-Refresh getaktet
SECURITIES_REFRESH_INTERVAL_MINUTES = 15  # eigener Job (Multi-Asset-Tracking,
# Nutzer-Idee 2026-07-09) - yfinance hat keine offizielle Rate-Limit-Dokumentation,
# defensiv aehnlich wie der Krypto-Preis-Takt gewaehlt. Bewusst ein SEPARATER Job statt
# in refresh_prices_job() mit hineingemischt, damit ein yfinance-Ausfall den Krypto-
# Preis-Takt nicht blockiert (P-10-Isolation, gleiches Prinzip wie der Kraken-OHLC-Job).


def refresh_prices_job(client, conn_factory, watchlist) -> bool:
    """Rueckgabe: True = tatsaechlich gelaufen, False = uebersprungen (Lock
    bereits belegt - laeuft schon ein anderer Aufruf desselben Jobs, egal ob
    durch den Scheduler-Takt oder einen manuellen Remote-Trigger)."""
    if not refresh_prices_lock.acquire(blocking=False):
        logger.info("Preis-Refresh: bereits in Ausführung - übersprungen")
        return False
    _job_started_at["refresh_prices"] = time.monotonic()
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
        refresh_prices_lock.release()
        _job_started_at.pop("refresh_prices", None)
    return True


def refresh_securities_prices_job(client, conn_factory, watchlist) -> bool:
    """Multi-Asset-Tracking (Nutzer-Idee 2026-07-09): Preis-Refresh fuer Aktien/ETF/
    Rohstoffe ueber yfinance, analog zu refresh_prices_job() fuer Krypto. Assets mit
    assetklasse == 'krypto' werden von YFinanceClient.fetch_price_snapshots() selbst
    uebersprungen, kein Vorfiltern hier noetig. Rueckgabewert wie refresh_prices_job()."""
    if not refresh_securities_lock.acquire(blocking=False):
        logger.info("Wertpapier-Preis-Refresh: bereits in Ausführung - übersprungen")
        return False
    _job_started_at["refresh_securities"] = time.monotonic()
    conn = conn_factory()
    try:
        # 2026-07-11, Nutzer-Fund: US-Aktien (z.B. PLTR/VST) liefern von yfinance nur
        # USD - ohne EUR-Umrechnung blieben sie in jeder EUR-Summe unsichtbar. Gleicher
        # EURCV-Peg-Trick wie agent/krypto/risk_gate.py::pre_check() (1 EURCV ~= 1 EUR,
        # A-5) - kein zusaetzlicher Wechselkurs-Call noetig, echter Marktkurs statt
        # geratener Zahl. Fehlt der EURCV-Snapshot, bleibt eur_usd_fx_rate None (P-10).
        eurcv_snap = db.get_latest_prices(conn).get("EURCV")
        eur_usd_fx_rate = (
            eurcv_snap.price_usd / eurcv_snap.price_eur
            if eurcv_snap and eurcv_snap.price_usd and eurcv_snap.price_eur
            else None
        )
        snapshots = client.fetch_price_snapshots(watchlist, eur_usd_fx_rate=eur_usd_fx_rate)
        for snapshot in snapshots:
            db.insert_price_snapshot(conn, snapshot)
        logger.info("Wertpapier-Preis-Refresh: %d Assets aktualisiert", len(snapshots))
    except Exception:
        logger.exception("Wertpapier-Preis-Refresh fehlgeschlagen")
    finally:
        conn.close()
        refresh_securities_lock.release()
        _job_started_at.pop("refresh_securities", None)
    return True


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


def marktscan_job(coingecko_client, kraken_client, groq_client, conn_factory, watchlist, fred_api_key) -> bool:
    """MS-3: 2x taeglich (04:00/16:00, siehe build_scheduler()) - kompletter
    Marktscan-Lauf (Stufe A-D, agent/krypto/marktscan.py). Braucht ein aktuelles Regime
    (R-5.1 + Liquiditaets-Regime + Zyklus-Risiko) fuer Stufe C/D, dafuer dieselbe
    Logik wie agent/krypto/pipeline.py::generate_signal() (compute_current_regime(), nicht
    dupliziert). `groq_client` kann None sein (P-8) - dann greift nur der manuelle
    UI-Klick-Pfad fuer P-5-Begruendungen, keine automatischen. Rueckgabewert wie
    refresh_prices_job() (Lock-Status)."""
    if not marktscan_lock.acquire(blocking=False):
        logger.info("Marktscan: bereits in Ausführung - übersprungen")
        return False
    _job_started_at["marktscan"] = time.monotonic()
    conn = conn_factory()
    try:
        import config as config_module
        from agent.krypto.marktscan import run_scan
        from agent.krypto.pipeline import compute_current_regime

        config_dict = config_module.load_config()
        if not config_dict["marktscan"].get("aktiv", True):
            logger.info("Marktscan deaktiviert (config.yaml marktscan.aktiv=false) - übersprungen")
            return True

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
        marktscan_lock.release()
        _job_started_at.pop("marktscan", None)
    return True


def backward_tracking_job(conn_factory, watchlist) -> None:
    """Selbstverifikations-Vision Schritt 2 (2026-07-10, siehe
    agent/krypto/backward_tracking.py) - taeglich, feste Uhrzeit (siehe
    build_scheduler()): prueft vergangene KAUFEN/NACHKAUFEN-Signale gegen die
    bereits vorhandene Kurshistorie (price_history/price_history_ohlc), kein
    eigener Netzwerk-Call noetig - reine Beobachtung, keine Empfehlung/kein Veto."""
    conn = conn_factory()
    try:
        import config as config_module
        from agent.krypto.backward_tracking import run_backward_tracking

        config_dict = config_module.load_config()
        result = run_backward_tracking(conn, watchlist, config_dict)
        logger.info(
            "Backward-Tracking: %d geprüft, %d Take-Profit, %d Stop-Loss, %d abgelaufen, %d weiterhin offen",
            result.geprueft_count, result.resolved_take_profit, result.resolved_stop_loss,
            result.expired, result.still_open,
        )
    except Exception:
        logger.exception("Backward-Tracking fehlgeschlagen")
    finally:
        conn.close()


def get_lock_status() -> dict[str, dict]:
    """Fuer die Remote-Steuer-Seite (remote/status.py) - liest den aktuellen
    Sperr-/Laufzeit-Status der ueberwachten Jobs, ohne selbst einen Lock zu
    beanspruchen. running_since_seconds ist None, wenn der Job nicht laeuft."""
    now = time.monotonic()
    status = {}
    for name, lock in _JOB_LOCKS.items():
        locked = lock.locked()
        started = _job_started_at.get(name)
        running_since_seconds = (now - started) if (locked and started is not None) else None
        status[name] = {"locked": locked, "running_since_seconds": running_since_seconds}
    return status


def force_release_lock(job_name: str) -> bool:
    """Not-Reset (remote/server.py::POST /api/reset-lock) - gibt einen haengen
    gebliebenen Lock zwangsweise frei, damit ein neuer Versuch moeglich ist.
    WICHTIG: das setzt NUR den Lock zurueck - ein urspruenglich haengender
    Hintergrund-Thread laeuft dabei ggf. als Daemon-Thread weiter (Python kann
    Threads nicht erzwungen beenden), das ist reine Not-Funktion, keine echte
    Prozess-Kontrolle. Rueckgabe False, falls der Job unbekannt ist oder gar
    nicht lief (nichts zu tun)."""
    lock = _JOB_LOCKS.get(job_name)
    if lock is None:
        return False
    if not lock.locked():
        return False
    try:
        lock.release()
    except RuntimeError:
        return False
    _job_started_at.pop(job_name, None)
    logger.warning("Lock fuer Job '%s' manuell zurueckgesetzt (Not-Reset ueber Remote-Steuer-Seite)", job_name)
    return True


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
    scheduler.add_job(
        refresh_securities_prices_job,
        "interval",
        minutes=SECURITIES_REFRESH_INTERVAL_MINUTES,
        args=[YFinanceClient(), db_conn_factory, watchlist],
        id="refresh_securities_prices",
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
    # Backward-Tracking (2026-07-10): taeglich, kein eigener API-Call noetig (reine
    # Auswertung bereits vorhandener Kursdaten) - feste Uhrzeit nach dem ueblichen
    # naechtlichen Refresh-Fenster, keine harte Abhaengigkeit (holt am naechsten Tag
    # nach, falls refresh_history/refresh_ohlc an dem Tag noch nicht durch waren).
    scheduler.add_job(
        backward_tracking_job,
        "cron",
        hour=6,
        minute=0,
        args=[db_conn_factory, watchlist],
        id="backward_tracking",
    )
    scheduler.add_listener(_log_job_event, EVENT_JOB_ERROR | EVENT_JOB_MISSED)
    return scheduler
