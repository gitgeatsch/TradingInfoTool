"""Hintergrund-Scheduler: periodischer Preis-Refresh in die SQLite-Cache (B-1)."""
from __future__ import annotations

import logging
import threading
import time
from datetime import datetime, timedelta, timezone

from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_MISSED
from apscheduler.schedulers.background import BackgroundScheduler

import database.db as db
import staleness
from api.history import backfill_all
from api.kraken import KRAKEN_PAIR_MAP
from api.kraken_history import backfill_all_ohlc
from api.yfinance_client import YFinanceClient
from api.yfinance_history import backfill_all_aktien_ohlc

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
bitpanda_holdings_lock = threading.Lock()
# Batch-Signal-Berechnung (2026-07-13) - der urspruengliche taegliche
# 05:00-Scheduler-Job ist seit Phase 5 (2026-07-14) entfernt (der Budget-
# Allocator uebernimmt Spot-Rotation jetzt im 15-Min-Takt, siehe
# hebel_screening_job()/budget_allocator.py). Der manuelle UI-Button
# (ui/signals_view.py) bleibt bestehen (Nutzer-Entscheidung) und nutzt diesen
# Lock weiterhin selbst (verhindert einen Doppel-Lauf bei Mehrfach-Klick).
signal_batch_lock = threading.Lock()
# Hebel-Screening (2026-07-14, Phase 1, siehe docs/hebel_positionsformel.md) -
# rein deterministisches Scoring, kein Groq-Aufruf, daher (noch) kein zweiter
# Ausloeser wie bei signal_batch_lock - Lock existiert trotzdem, falls spaeter
# ein manueller "Jetzt screenen"-Button dazukommt (gleiches Muster).
hebel_screening_lock = threading.Lock()
# Multi-Asset-Batch (2026-07-18, siehe agent/multi_asset_batch.py) - eigener
# Lock analog zu hebel_screening_lock, verhindert einen Doppel-Lauf bei
# ueberlappenden Intervallen (z.B. nach einem verspaeteten Neustart).
multi_asset_batch_lock = threading.Lock()
_JOB_LOCKS = {
    "refresh_prices": refresh_prices_lock,
    "refresh_securities": refresh_securities_lock,
    "marktscan": marktscan_lock,
    "bitpanda_holdings": bitpanda_holdings_lock,
    "signal_batch": signal_batch_lock,
    "hebel_screening": hebel_screening_lock,
    "multi_asset_batch": multi_asset_batch_lock,
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
BITPANDA_HOLDINGS_REFRESH_INTERVAL_MINUTES = 30  # 2026-07-11: seltener als der
# Preis-Takt (15 Min) - authentifizierter Call, Bestaende/Cash aendern sich
# normalerweise seltener als Marktpreise. Deckte urspruenglich NUR den Fiat-Cash-
# Anteil ab (die vollen Bestaende hatten einen interaktiven Rueckgangs-
# Bestaetigungsdialog, der sich nicht sauber aus einem Hintergrund-Thread aufrufen
# liess) - seit 2026-07-16 (Staking-Verifikation, siehe importer/bitpanda_sync.py
# Modul-Docstring) deckt derselbe Takt den KOMPLETTEN Bestandsabgleich ab
# (sync_from_bitpanda() macht Cash intern automatisch mit, kein separater Job
# mehr noetig).
STALENESS_RECHECK_INTERVAL_MINUTES = 15  # 2026-07-23, echter Fund: _history_data_is_
# stale()/_ohlc_data_is_stale() liefen bisher NUR einmalig beim App-Start (siehe
# build_scheduler() unten). Landete der letzte Neustart zufaellig knapp VOR dem
# Ueberschreiten der 2-Tage-Schwelle (echter Fall: Neustart 07-22 23:26, Schwelle
# noch nicht ueberschritten) und lief die App danach durchgehend weiter (ueber
# Mitternacht hinweg), wurde das Ueberschreiten der Schwelle nie bemerkt - die
# Krypto-Kurshistorie blieb bis mind. 06:14 auf dem Stand 07-20 stehen, ALLE
# Hebel-/Spot-Kandidaten scheiterten die ganze Nacht (00:11-04:15, 390 Signale)
# am P-10-Gate, ohne dass je ein echter LLM-Call stattfand. Backtest gegen die
# echte Log-Timeline (backtest_staleness_watchdog.py): ein periodischer Recheck
# im 15-Min-Takt haette 389/390 dieser Signale gerettet (nur das allererste um
# 00:11 waere knapp vor dem ersten Tick noch verpasst worden). Gleicher Takt wie
# REFRESH_INTERVAL_MINUTES/HEBEL_SCREENING_INTERVAL_MINUTES - keine neue
# Kadenz-Klasse noetig.
HEBEL_SCREENING_INTERVAL_MINUTES = 15  # muss mit config.yaml hebel_screening.
# intervall_minuten uebereinstimmen (wie bei allen anderen Jobs ist die Taktung selbst
# ein Python-Konstante, nur der aktiv-Schalter wird dynamisch aus config.yaml gelesen,
# siehe hebel_screening_job()) - kalibriert auf die reale Ø-Haltedauer echter
# Hebel-Positionen (1,1 Tage), siehe docs/hebel_positionsformel.md.
MULTI_ASSET_BATCH_CRON_HOURS = "9,19"  # 2026-07-20, Quotrix-Handelsfenster-Fix (siehe
# Memory project_bitpanda_exchange: Bitpanda-Aktien/ETFs/ETCs laufen seit 2026 ueber
# die Quotrix-Boerse, Handelszeiten Mo-Fr 07:30-23:00 CET, NICHT 24/7 wie Krypto).
# Vorher: reines "interval" alle MULTI_ASSET_BATCH_INTERVAL_HOURS=12 Std. MIT
# next_run_time=jetzt bei jedem Neustart - das konnte zu jeder Uhrzeit (auch
# nachts) ein Signal mit Kurszonen erzeugen, die auf einem Stunden/Tage alten
# Schlusskurs basierten UND vom Nutzer erst zum naechsten Handelsstart ueberhaupt
# umsetzbar waren. 09:00/19:00 CET liegen sicher im Handelsfenster (nach
# Handelsstart, deutlich vor Handelsschluss) UND nur an Handelstagen (day_of_week=
# mon-fri) - kein next_run_time-Sofortstart mehr, ein Neustart wartet bewusst bis
# zum naechsten reguleaeren Takt. Der eigentliche Re-Bewertungs-Rhythmus je Asset
# bleibt weiterhin ueber die Cooldown-Werte in config.yaml multi_asset_batch
# gesteuert, dieser Cron-Takt gibt nur den technischen Lauf-Rahmen vor.

# Job-Ausfall-Backoff (2026-07-12, letzter offener Betriebssicherheits-Punkt): Referenz
# auf die scheduler-Instanz selbst, gesetzt am Ende von build_scheduler() - noetig, damit
# _record_job_failure_for_backoff() den naechsten Lauf per scheduler.modify_job()
# verschieben kann, obwohl die *_job()-Funktionen selbst keine Scheduler-Referenz als
# Parameter bekommen (gleiches Modul-Level-Zugriffsmuster wie die Locks oben).
_scheduler_ref = None
_consecutive_failures: dict[str, int] = {}
# Bewusst NUR die drei haeufig getakteten Jobs (15-30 Min) - bei den beiden
# 24-Stunden-Jobs (Historie/OHLC) und den Cron-getakteten Jobs (Marktscan/
# Backward-Tracking) ist der Normal-Takt bereits so gross, dass ein zusaetzliches
# Backoff keinen nennenswerten Nutzen haette (ein einzelner taeglicher Fehlschlag
# "haemmert" keine API).
_BACKOFF_BASE_INTERVAL_MINUTES = {
    "refresh_prices": REFRESH_INTERVAL_MINUTES,
    "refresh_securities_prices": SECURITIES_REFRESH_INTERVAL_MINUTES,
    "bitpanda_holdings": BITPANDA_HOLDINGS_REFRESH_INTERVAL_MINUTES,
}
_IMMEDIATE_START_MISFIRE_GRACE_SECONDS = 300  # siehe build_scheduler()-Kommentar (2026-07-19)
_BACKOFF_MAX_MINUTES = 240  # Deckel 4 Std. - auch bei einem sehr langen Ausfall soll die
# App nach spaetestens 4 Std. wieder einen Versuch starten, statt den Job faktisch
# stillzulegen.


def refresh_prices_job(client, conn_factory, watchlist_provider) -> bool:
    """Rueckgabe: True = tatsaechlich gelaufen, False = uebersprungen (Lock
    bereits belegt - laeuft schon ein anderer Aufruf desselben Jobs, egal ob
    durch den Scheduler-Takt oder einen manuellen Remote-Trigger).

    `watchlist_provider` (2026-07-23, Restart-Fix - siehe Memory project_
    watchlist_live_reload_fix): Callable statt fertiger Liste, wird HIER bei
    jedem Lauf frisch aufgerufen (config.get_watchlist() liest config.yaml
    ohne Caching) - eine neu hinzugefuegte Watchlist-Asset wird so spaetestens
    beim naechsten Takt beruecksichtigt, ohne App-Neustart."""
    if not refresh_prices_lock.acquire(blocking=False):
        logger.info("Preis-Refresh: bereits in Ausführung - übersprungen")
        return False
    watchlist = watchlist_provider()
    _job_started_at["refresh_prices"] = time.monotonic()
    conn = conn_factory()
    try:
        snapshots = client.fetch_price_snapshots(watchlist)
        for snapshot in snapshots:
            db.insert_price_snapshot(conn, snapshot)
        logger.info("Preis-Refresh: %d/%d Assets aktualisiert", len(snapshots), len(watchlist))
        _record_job_success_for_backoff("refresh_prices")
    except Exception as exc:
        logger.exception("Preis-Refresh fehlgeschlagen")
        _notify_job_failure("refresh_prices", f"Preis-Refresh fehlgeschlagen: {exc}")
        _record_job_failure_for_backoff("refresh_prices")
    finally:
        conn.close()
        refresh_prices_lock.release()
        _job_started_at.pop("refresh_prices", None)
    return True


def refresh_securities_prices_job(client, conn_factory, watchlist_provider) -> bool:
    """Multi-Asset-Tracking (Nutzer-Idee 2026-07-09): Preis-Refresh fuer Aktien/ETF/
    Rohstoffe ueber yfinance, analog zu refresh_prices_job() fuer Krypto. Assets mit
    assetklasse == 'krypto' werden von YFinanceClient.fetch_price_snapshots() selbst
    uebersprungen, kein Vorfiltern hier noetig. Rueckgabewert wie refresh_prices_job().
    `watchlist_provider` siehe refresh_prices_job()-Docstring (2026-07-23)."""
    if not refresh_securities_lock.acquire(blocking=False):
        logger.info("Wertpapier-Preis-Refresh: bereits in Ausführung - übersprungen")
        return False
    watchlist = watchlist_provider()
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
        _record_job_success_for_backoff("refresh_securities_prices")
    except Exception as exc:
        logger.exception("Wertpapier-Preis-Refresh fehlgeschlagen")
        _notify_job_failure("refresh_securities_prices", f"Wertpapier-Preis-Refresh fehlgeschlagen: {exc}")
        _record_job_failure_for_backoff("refresh_securities_prices")
    finally:
        conn.close()
        refresh_securities_lock.release()
        _job_started_at.pop("refresh_securities", None)
    return True


def refresh_history_job(client, conn_factory, watchlist_provider) -> None:
    """`watchlist_provider` siehe refresh_prices_job()-Docstring (2026-07-23)."""
    watchlist = watchlist_provider()
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
    except Exception as exc:
        logger.exception("Historie-Refresh fehlgeschlagen")
        _notify_job_failure("refresh_history", f"Historie-Refresh fehlgeschlagen: {exc}")
    finally:
        conn.close()


def refresh_ohlc_job(client, conn_factory, watchlist_provider) -> None:
    """`watchlist_provider` siehe refresh_prices_job()-Docstring (2026-07-23)."""
    watchlist = watchlist_provider()
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
    except Exception as exc:
        logger.exception("Kraken-OHLC-Refresh fehlgeschlagen")
        _notify_job_failure("refresh_ohlc", f"Kraken-OHLC-Refresh fehlgeschlagen: {exc}")
    finally:
        conn.close()


def refresh_aktien_ohlc_job(conn_factory, watchlist_provider) -> None:
    """Automatischer taeglicher OHLC-Refresh fuer Einzelaktien (2026-07-16, siehe
    api/yfinance_history.py::backfill_all_aktien_ohlc() Docstring fuer den vollen
    Kontext - schliesst eine Luecke aus dem Asset-Verwaltungs-Audit: ohne diesen Job
    haette der taegliche Backward-Tracking-Job offene Aktien-Signale zunehmend gegen
    veraltete Kursdaten geprueft, da Phase 1 der Aktien-Pipeline OHLC bisher nur bei
    manuellem Signal-Klick aktualisierte). `watchlist_provider` siehe
    refresh_prices_job()-Docstring (2026-07-23)."""
    watchlist = watchlist_provider()
    conn = conn_factory()
    try:
        results = backfill_all_aktien_ohlc(conn, watchlist)
        degraded = [r for r in results if r.degraded]
        logger.info(
            "Aktien-OHLC-Refresh: %d/%d Assets aktualisiert (%d degradiert)",
            len(results) - len(degraded), len(results), len(degraded),
        )
    except Exception as exc:
        logger.exception("Aktien-OHLC-Refresh fehlgeschlagen")
        _notify_job_failure("refresh_aktien_ohlc", f"Aktien-OHLC-Refresh fehlgeschlagen: {exc}")
    finally:
        conn.close()


def marktscan_job(coingecko_client, kraken_client, conn_factory, watchlist_provider, fred_api_key) -> bool:
    """MS-3: 2x taeglich (04:00/16:00, siehe build_scheduler()) - kompletter
    Marktscan-Lauf (Stufe A-D, agent/krypto/marktscan.py). Braucht ein aktuelles Regime
    (R-5.1 + Liquiditaets-Regime + Zyklus-Risiko) fuer Stufe C/D, dafuer dieselbe
    Logik wie agent/krypto/pipeline.py::generate_signal() (compute_current_regime(), nicht
    dupliziert). Seit Phase 5 (2026-07-14) macht `run_scan()` selbst KEINE Groq-Calls
    mehr (siehe agent/krypto/marktscan.py) - der Budget-Allocator generiert
    Kaufkandidaten-Begruendungen zentral im 15-Min-Takt. Rueckgabewert wie
    refresh_prices_job() (Lock-Status). `watchlist_provider` siehe
    refresh_prices_job()-Docstring (2026-07-23)."""
    if not marktscan_lock.acquire(blocking=False):
        logger.info("Marktscan: bereits in Ausführung - übersprungen")
        return False
    watchlist = watchlist_provider()
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
        candidates = run_scan(coingecko_client, conn, watchlist, regime_result, config_dict)
        treffer = [c for c in candidates if c.einstufung in ("kaufkandidat", "watchlist_wuerdig")]
        logger.info(
            "Marktscan: %d Kandidaten bewertet (%d Treffer: watchlist_würdig/Kaufkandidat, Regime %s)",
            len(candidates), len(treffer), regime_result.regime,
        )
        kaufkandidaten = [c for c in candidates if c.einstufung == "kaufkandidat"]
        _notify_marktscan_kaufkandidaten(kaufkandidaten)
    except Exception as exc:
        logger.exception("Marktscan fehlgeschlagen")
        _notify_job_failure("marktscan", f"Marktscan fehlgeschlagen: {exc}")
    finally:
        conn.close()
        marktscan_lock.release()
        _job_started_at.pop("marktscan", None)
    return True


def backward_tracking_job(conn_factory, watchlist_provider) -> None:
    """Selbstverifikations-Vision Schritt 2 (2026-07-10, siehe
    agent/krypto/backward_tracking.py) - taeglich, feste Uhrzeit (siehe
    build_scheduler()): prueft vergangene KAUFEN/NACHKAUFEN-Signale gegen die
    bereits vorhandene Kurshistorie (price_history/price_history_ohlc), kein
    eigener Netzwerk-Call noetig - reine Beobachtung, keine Empfehlung/kein Veto.

    2026-07-15 um Hebel-Signale erweitert (agent/krypto/hebel_backward_tracking.py) -
    derselbe taegliche Lauf, dieselbe Fehlerbehandlung, kein zweiter Scheduler-
    Eintrag noetig (identisches Timing, identische Konfiguration).
    `watchlist_provider` siehe refresh_prices_job()-Docstring (2026-07-23)."""
    watchlist = watchlist_provider()
    conn = conn_factory()
    try:
        import config as config_module
        from agent.krypto.backward_tracking import run_backward_tracking
        from agent.krypto.hebel_backward_tracking import run_hebel_backward_tracking

        config_dict = config_module.load_config()
        result = run_backward_tracking(conn, watchlist, config_dict)
        logger.info(
            "Backward-Tracking (Spot): %d geprüft, %d Take-Profit, %d Stop-Loss, %d abgelaufen, %d weiterhin offen",
            result.geprueft_count, result.resolved_take_profit, result.resolved_stop_loss,
            result.expired, result.still_open,
        )
        hebel_result = run_hebel_backward_tracking(conn, watchlist, config_dict)
        logger.info(
            "Backward-Tracking (Hebel): %d geprüft, %d Take-Profit, %d Stop-Loss, %d Liquidation, "
            "%d abgelaufen, %d weiterhin offen",
            hebel_result.geprueft_count, hebel_result.resolved_take_profit, hebel_result.resolved_stop_loss,
            hebel_result.resolved_liquidation, hebel_result.expired, hebel_result.still_open,
        )
        db.set_backward_tracking_last_run_date(conn, datetime.now().date().isoformat())
    except Exception as exc:
        logger.exception("Backward-Tracking fehlgeschlagen")
        _notify_job_failure("backward_tracking", f"Backward-Tracking fehlgeschlagen: {exc}")
    finally:
        conn.close()


def makro_analog_job(conn_factory, fred_api_key) -> None:
    """Historischer Makro-Konstellationsvergleich (2026-07-18, siehe
    agent/krypto/makro_analog.py Modul-Docstring) - taeglich: Historie
    (FRED/yfinance/blockchain.com) auffrischen, Top-Analoge neu berechnen,
    Ergebnis cachen (makro_analog_ergebnis). Baut jeden Lauf auf der bereits
    gespeicherten Historie additiv auf (COALESCE-Merge, siehe
    upsert_makro_historie_monat()) - ein einzelner Fehlschlag einer Quelle
    (z.B. FRED_API_KEY fehlt) blockiert die anderen nicht, siehe
    run_makro_analog_update()-Docstring."""
    conn = conn_factory()
    try:
        import config as config_module
        from agent.krypto.makro_analog import run_makro_analog_update

        config_dict = config_module.load_config()
        fakt = run_makro_analog_update(conn, fred_api_key, config_dict)
        if fakt is not None:
            logger.info(
                "Makro-Analog-Vergleich: %d historische Analoge gefunden (aktueller Monat %s)",
                fakt["anzahl_analoge"], fakt["aktueller_monat"],
            )
        else:
            logger.info("Makro-Analog-Vergleich: noch keine auswertbare Historie (zu fruehe Datenlage).")
    except Exception as exc:
        logger.exception("Makro-Analog-Vergleich fehlgeschlagen")
        _notify_job_failure("makro_analog", f"Makro-Analog-Vergleich fehlgeschlagen: {exc}")
    finally:
        conn.close()


def backward_tracking_catchup_if_missed(conn_factory, watchlist) -> None:
    """2026-07-17, Nutzer-Fund: der feste 06:00-Cron holt einen verpassten Termin
    NICHT automatisch nach, wenn die App zu diesem Zeitpunkt gar nicht lief (an
    zwei aufeinanderfolgenden Tagen passiert, 07-15 und 07-16 - zwei Tage lang
    keine einzige Backward-Tracking-Auswertung, obwohl laengst faellig). Beim
    App-Start einmalig geprueft: wurde der heutige Lauf bereits erledigt? Falls
    nicht, sofort synchron nachholen (kein Netzwerk-Call, reine DB-Auswertung,
    siehe backward_tracking_job()-Docstring - unbedenklich, das direkt beim
    Start zu tun). Verhindert gleichzeitig unnoetige Mehrfach-Laeufe bei
    mehreren Neustarts am selben Tag, nachdem der heutige Lauf schon glückte."""
    conn = conn_factory()
    try:
        last_run = db.get_backward_tracking_last_run_date(conn)
    finally:
        conn.close()
    heute = datetime.now().date().isoformat()
    if last_run == heute:
        return
    logger.info(
        "Backward-Tracking: heutiger 06:00-Termin noch nicht erledigt (zuletzt: %s) - hole sofort nach.",
        last_run or "nie",
    )
    backward_tracking_job(conn_factory, watchlist)


def refresh_bitpanda_holdings_job(api_key, conn_factory) -> bool:
    """Automatischer VOLLER Bestandsabgleich (2026-07-16, ersetzt den bisherigen
    reinen Cash-Sync) - moeglich geworden durch die Staking-Verifikation in
    importer/bitpanda_sync.py::sync_from_bitpanda() (siehe dortigen Modul-
    Docstring): die urspruengliche Vorsicht ("Rueckgang koennte Staking statt
    Verkauf sein, nur der Nutzer kann das unterscheiden") ist jetzt technisch
    aufgeloest, kein interaktiver Dialog mehr noetig fuer den Normalfall.

    Fallback (selten): schlaegt die Staking-Verifikation NUR in diesem einen
    Lauf fehl (z.B. Netzwerkfehler beim Transaktions-Abruf), bleiben etwaige
    Rueckgaenge unangewendet (Bestand bleibt auf dem alten, bekannten Stand -
    kein Datenverlust, nur Staleness) UND werden hier per E-Mail gemeldet
    (wiederverwendet _notify_job_failure()'s Cooldown-Mechanismus, damit ein
    laengerer Ausfall nicht taeglich x-mal eine Mail ausloest) - der Nutzer
    kann dann jederzeit manuell "Bestände von Bitpanda abgleichen" klicken,
    was den bestehenden Bestaetigungsdialog als echten Rueckfallweg zeigt."""
    if not bitpanda_holdings_lock.acquire(blocking=False):
        logger.info("Bitpanda-Bestandsabgleich: bereits in Ausführung - übersprungen")
        return False
    _job_started_at["bitpanda_holdings"] = time.monotonic()
    conn = conn_factory()
    try:
        from api.bitpanda import get_listed_assets
        from importer.bitpanda_sync import sync_from_bitpanda

        listed_assets = get_listed_assets()
        result = sync_from_bitpanda(conn, api_key, listed_assets)
        logger.info(
            "Bitpanda-Bestandsabgleich: %d aktualisiert (%d Zuwächse, %d automatisch "
            "bestätigte Rückgänge, %d Rückgänge weiterhin bestätigungspflichtig, "
            "Staking-Verifikation: %s)",
            result.synced_count, len(result.updated_holdings), len(result.auto_confirmed_decreases),
            len(result.decreased_holdings_needs_confirmation), result.staking_verified,
        )
        if result.decreased_holdings_needs_confirmation:
            symbole = ", ".join(c.symbol for c in result.decreased_holdings_needs_confirmation)
            _notify_job_failure(
                "bitpanda_holdings_decreases_pending",
                f"Staking-Verifikation in diesem Lauf nicht möglich - {len(result.decreased_holdings_needs_confirmation)} "
                f"Rückgang/-gänge bleiben unangewendet, bis manuell bestätigt: {symbole}. "
                "Bitte im Datei-Menü 'Bestände von Bitpanda abgleichen' klicken.",
            )
        _record_job_success_for_backoff("bitpanda_holdings")
    except Exception as exc:
        logger.exception("Bitpanda-Bestandsabgleich fehlgeschlagen")
        _notify_job_failure("bitpanda_holdings", f"Bitpanda-Bestandsabgleich fehlgeschlagen: {exc}")
        _record_job_failure_for_backoff("bitpanda_holdings")
    finally:
        conn.close()
        bitpanda_holdings_lock.release()
        _job_started_at.pop("bitpanda_holdings", None)
    return True


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


# E-Mail-Benachrichtigung bei Job-Ausfall (U-8, 2026-07-12) - Cooldown-Speicher
# pro Job-ID, geteilt zwischen BEIDEN Fehlerquellen unten (den eigenen
# except-Bloecken der *_job()-Funktionen UND dem globalen Listener), damit ein
# Job sich insgesamt hoechstens 1x pro Cooldown-Fenster meldet, egal ueber
# welchen der beiden Wege der Fehler bekannt wurde.
_last_failure_email_sent: dict[str, float] = {}


def _notify_job_failure(job_id: str, fehler_text: str) -> None:
    """E-Mail-Benachrichtigung bei Job-Fehlschlag, mit Cooldown (U-8, 2026-07-12).

    WICHTIGER FUND beim Bauen: der globale EVENT_JOB_ERROR-Listener (siehe
    _log_job_event() unten) feuert NUR bei unbehandelten Bugs im Job-Wrapper
    selbst - der weitaus haeufigere Realfall (z.B. Groq/CoinGecko/Bitpanda
    mehrere Stunden nicht erreichbar) wird von jedem *_job() bereits INTERN
    abgefangen (eigener try/except, siehe oben) und erreicht den Listener nie.
    Deshalb wird diese Funktion von BEIDEN Stellen aus aufgerufen - vom
    Listener UND direkt aus den bestehenden except-Bloecken der Jobs selbst.

    Cooldown (config.yaml benachrichtigung.email.job_ausfall_cooldown_minuten)
    verhindert Postfach-Spam bei einem mehrstuendigen/-taegigen Ausfall - ein
    Job meldet sich pro Fenster hoechstens einmal."""
    import config as config_module
    from api.email_notify import send_notification_email

    config_dict = config_module.load_config()
    email_cfg = config_dict.get("benachrichtigung", {}).get("email", {})
    if not email_cfg.get("aktiv", False):
        return
    empfaenger = email_cfg.get("empfaenger")
    if not empfaenger:
        return

    cooldown_minuten = email_cfg.get("job_ausfall_cooldown_minuten", 60)
    last_sent = _last_failure_email_sent.get(job_id)
    # Bugfix (2026-07-12, bei der Verifikation gefunden): time.monotonic() zaehlt
    # unter Windows ab Systemstart - ein 0.0-Default fuer "noch nie gesendet"
    # wuerde einen allerersten Job-Fehlschlag in der ersten Stunde nach einem
    # Neustart faelschlich als "kuerzlich gesendet" werten und die Mail
    # unterdruecken. None statt 0.0 als Default macht "noch nie gesendet"
    # explizit und umgeht den Cooldown-Check in diesem Fall komplett.
    if last_sent is not None and time.monotonic() - last_sent < cooldown_minuten * 60:
        return

    if send_notification_email(
        f"TradingInfoTool: Job '{job_id}' fehlgeschlagen",
        f"{fehler_text}\n\nWeitere Meldungen für denselben Job werden für "
        f"{cooldown_minuten} Minuten unterdrückt (Spam-Schutz).",
        empfaenger,
    ):
        _last_failure_email_sent[job_id] = time.monotonic()


def _record_job_failure_for_backoff(job_id: str) -> None:
    """Job-Ausfall-Backoff (2026-07-12): verdoppelt bei WIEDERHOLTEN Fehlschlägen
    desselben Jobs das Intervall bis zum nächsten Versuch (gedeckelt auf
    _BACKOFF_MAX_MINUTES), statt stur im Normal-Takt (z. B. alle 15 Min) weiter
    gegen eine erkennbar nicht erreichbare API zu laufen. Bewusst erst AB dem
    zweiten Fehlschlag in Folge aktiv (2^0 = Normal-Takt beim ersten Fehlschlag) -
    eine einzelne fehlgeschlagene Anfrage soll nicht gleich als Dauerausfall
    gewertet werden, das waere bei einem kurzen Netzwerk-Hänger unnötig träge.

    Nur für die in _BACKOFF_BASE_INTERVAL_MINUTES gelisteten Jobs aktiv - für
    alle anderen (job_id nicht im Dict, z. B. Historie/OHLC/Marktscan) ein reines
    No-Op."""
    base_minutes = _BACKOFF_BASE_INTERVAL_MINUTES.get(job_id)
    if base_minutes is None or _scheduler_ref is None:
        return
    _consecutive_failures[job_id] = _consecutive_failures.get(job_id, 0) + 1
    failures = _consecutive_failures[job_id]
    delay_minutes = min(base_minutes * (2 ** (failures - 1)), _BACKOFF_MAX_MINUTES)
    if delay_minutes <= base_minutes:
        return
    try:
        _scheduler_ref.modify_job(job_id, next_run_time=datetime.now() + timedelta(minutes=delay_minutes))
        logger.warning(
            "Job '%s': %d Fehlschläge in Folge - nächster Versuch erst in %d Min (Backoff)",
            job_id, failures, delay_minutes,
        )
    except Exception:
        logger.exception("Backoff für Job '%s' konnte nicht angewendet werden", job_id)


def _record_job_success_for_backoff(job_id: str) -> None:
    """Gegenstück zu _record_job_failure_for_backoff() - setzt den Fehlschlag-Zähler
    zurück, sobald ein Job wieder erfolgreich läuft. Kein manueller Reset des
    nächsten Laufzeitpunkts nötig: APScheduler's IntervalTrigger rechnet den
    nächsten Takt ab dem TATSÄCHLICHEN letzten Lauf weiter, der Normal-Takt stellt
    sich damit von selbst wieder ein, sobald ein Lauf erfolgreich war."""
    if _consecutive_failures.get(job_id):
        logger.info("Job '%s': wieder erfolgreich - Backoff zurückgesetzt", job_id)
    _consecutive_failures[job_id] = 0


# Cash-Veto-Warnmail (2026-07-18, Detailanalyse "Anzeige/Info bei Cash-Block") -
# EIN globaler Zeitstempel statt pro-Symbol/pro-Job wie _last_failure_email_sent,
# da RM-4 (Cash-Reserve-Minimum) ein PORTFOLIOWEITER Zustand ist, kein Zustand
# einzelner Assets - waehrend die Reserve unter dem Minimum liegt, waere
# `cash_veto` bei JEDEM bewerteten Spot-/Aktien-/Rohstoff-/Themen-ETF-Asset
# identisch True. Ohne einen gemeinsamen Cooldown wuerde das Postfach geflutet.
_last_cash_veto_email_sent: float | None = None


def _notify_cash_veto_warning(signal) -> None:
    """WARNUNG-E-Mail, wenn RM-4 (Cash-Reserve-Minimum) einen Kauf blockiert
    (Nutzer-Vorgabe 2026-07-18: "sollte eher als Warnung betrachtet werden, da
    das System beeinträchtigt ist" - bewusst NICHT als gewöhnliche
    Empfehlungs-Mail behandelt, die HALTEN nie versendet). Anders als
    risk_veto/risk_veto_reason (die nur feuern, wenn das Modell eine Regel
    missachtet hat) spiegelt signal.cash_veto den tatsächlichen RM-4-Zustand,
    auch wenn das Modell selbst schon regelkonform HALTEN gesagt hat - genau
    der bisher unsichtbare Fall (siehe risk_gate.py::RiskPreCheckResult.
    cash_veto-Docstring).

    Cooldown wie _notify_job_failure() (config.yaml benachrichtigung.email.
    cash_veto_warnung_cooldown_minuten, Default 360 Min) - siehe Kommentar bei
    _last_cash_veto_email_sent oben, warum ein einzelner globaler statt ein
    pro-Job-Zeitstempel hier richtig ist."""
    global _last_cash_veto_email_sent
    import config as config_module
    from api.email_notify import send_notification_email

    config_dict = config_module.load_config()
    email_cfg = config_dict.get("benachrichtigung", {}).get("email", {})
    if not email_cfg.get("aktiv", False):
        return
    empfaenger = email_cfg.get("empfaenger")
    if not empfaenger:
        return

    cooldown_minuten = email_cfg.get("cash_veto_warnung_cooldown_minuten", 360)
    if (
        _last_cash_veto_email_sent is not None
        and time.monotonic() - _last_cash_veto_email_sent < cooldown_minuten * 60
    ):
        return

    body = (
        f"HALTEN wurde durch Cash-Veto (fehlendes Cash) verursacht ({signal.symbol}).\n\n"
        f"{signal.cash_veto_reason or ''}\n\n"
        "Das System ist aktuell durch eine zu geringe Cash-Reserve beeinträchtigt: "
        "mögliche Kaufgelegenheiten können nicht als Empfehlung ausgesprochen werden, "
        "bis die Reserve wieder über dem RM-4-Minimum liegt (z. B. Cash aufstocken "
        "oder bestehende Positionen reduzieren). Betrifft ALLE Spot-/Aktien-/"
        "Rohstoff-/Themen-ETF-Bewertungen, nicht nur dieses Asset.\n\n"
        f"Weitere Meldungen werden für {cooldown_minuten} Minuten unterdrückt (Spam-Schutz)."
    )
    if send_notification_email(f"TradingInfoTool: WARNUNG - Cash-Veto ({signal.symbol})", body, empfaenger):
        _last_cash_veto_email_sent = time.monotonic()


def _notify_oi_abdeckung_warnung(symbol: str, konsekutive_fehlschlaege: int) -> bool:
    """WARNUNG-E-Mail, wenn ein Symbol wiederholt keine Open-Interest-Daten von
    KEINER der drei Boersen (Binance/Bybit/OKX) liefert (2026-07-19, echter
    Notebook-Fund KAS/KAIA/FLOKI/TURBO/CANTON). Anders als die Cash-Veto-Warnung
    oben (ein globaler Zeitstempel, da RM-4 portfolioweit ist) ist dieser
    Cooldown pro Symbol DB-persistiert (db.set_oi_abdeckung_gemeldet), nicht
    in-memory - der Zustand soll einen Neustart ueberleben, da es sich laut
    Nutzer-Einschaetzung um ein potenziell DAUERHAFTES Problem handelt (nicht
    nur eine kurze Stoerung wie bei Groq-Erschoepfung).

    Bewusst KEIN automatisches Abschalten der Hebel-Pruefung fuer das Symbol -
    nur Sichtbarmachung (E-Mail + GUI-Markierung in ui/app.py), die
    Entscheidung bleibt beim Nutzer ueber den bestehenden Hebel-Pruefung-Toggle.

    Gibt zurueck, ob tatsaechlich eine E-Mail verschickt wurde - der Aufrufer
    (_pruefe_oi_abdeckung_warnung()) markiert das Symbol NUR bei True als
    gemeldet (db.set_oi_abdeckung_gemeldet), sonst wuerde bei deaktivierter
    E-Mail oder einem Versandfehler der Cooldown faelschlich anlaufen und eine
    spaeter (wieder) aktivierte Benachrichtigung bis zu oi_abdeckung_warnung_
    cooldown_stunden lang unterdruecken, obwohl nie etwas verschickt wurde."""
    import config as config_module
    from api.email_notify import send_notification_email

    config_dict = config_module.load_config()
    email_cfg = config_dict.get("benachrichtigung", {}).get("email", {})
    if not email_cfg.get("aktiv", False):
        return False
    empfaenger = email_cfg.get("empfaenger")
    if not empfaenger:
        return False

    body = (
        f"Fuer {symbol} liefert seit {konsekutive_fehlschlaege} aufeinanderfolgenden "
        "Hebel-Screening-Laeufen KEINE der drei Boersen (Binance/Bybit/OKX) "
        "Open-Interest-Daten.\n\n"
        "Moegliche Ursachen: das Symbol ist auf keiner dieser Boersen als Perp/Future "
        "gelistet, oder ein dauerhaftes API-Problem. Die Hebel-Pruefung fuer dieses "
        "Symbol laeuft technisch weiter, aber ohne OI-/Long-Short-Ratio-Kontext - "
        "ein Hebel-Signal fuer dieses Symbol sollte entsprechend vorsichtiger "
        "bewertet werden.\n\n"
        "Das System schaltet die Hebel-Pruefung NICHT automatisch ab - bei Bedarf "
        "manuell ueber den Hebel-Pruefung-Schalter in der Watchlist steuern.\n\n"
        "Weitere Meldungen fuer dieses Symbol werden fuer die konfigurierte "
        "Cooldown-Dauer unterdrueckt (Spam-Schutz)."
    )
    return send_notification_email(f"TradingInfoTool: WARNUNG - keine OI-Daten fuer {symbol}", body, empfaenger)


def _pruefe_oi_abdeckung_warnung(conn_factory, config_dict: dict) -> None:
    """Nach jedem Hebel-Screening-Lauf: prueft, ob ein Symbol die konfigurierte
    Fehlschlags-Schwelle ueberschritten hat (config.yaml hebel_screening.
    oi_abdeckung_schwelle_fehlschlaege) und noch nicht innerhalb des
    Cooldowns (oi_abdeckung_warnung_cooldown_stunden) gemeldet wurde - siehe
    db.get_symbole_mit_ueberschrittener_oi_schwelle()."""
    hebel_cfg = config_dict.get("hebel_screening", {})
    schwelle = hebel_cfg.get("oi_abdeckung_schwelle_fehlschlaege", 8)
    cooldown_stunden = hebel_cfg.get("oi_abdeckung_warnung_cooldown_stunden", 24)

    conn = conn_factory()
    try:
        status = db.get_oi_abdeckung_status(conn)
        symbole = db.get_symbole_mit_ueberschrittener_oi_schwelle(conn, schwelle, cooldown_stunden)
        for symbol in symbole:
            konsekutive_fehlschlaege = status.get(symbol, {}).get("konsekutive_fehlschlaege", schwelle)
            if _notify_oi_abdeckung_warnung(symbol, konsekutive_fehlschlaege):
                db.set_oi_abdeckung_gemeldet(conn, symbol)
    finally:
        conn.close()


def _notify_marktscan_kaufkandidaten(kaufkandidaten: list) -> None:
    """MS-1b (2026-07-12): eine gebündelte E-Mail pro Scan-Lauf über alle neuen
    Kaufkandidaten, wiederverwendet dieselbe Infrastruktur wie _notify_job_failure()
    (api/email_notify.py). Bewusst OHNE Cooldown - anders als ein Job-Fehlschlag ist
    ein wiederholt gemeldeter Kaufkandidat keine Spam-Situation, sondern eine
    weiterhin gültige Kauf-Chance; der Scan selbst läuft ohnehin nur 2x täglich, und
    bereits vom Nutzer entschiedene Kandidaten (verworfen/übernommen) tauchen wegen
    marktscan.py::_duplicate_should_skip() gar nicht erst erneut auf.

    Eigener try/except (P-10): ein Fehler beim E-Mail-Versand darf einen erfolgreich
    abgeschlossenen Marktscan-Lauf nicht nachträglich als 'fehlgeschlagen' erscheinen
    lassen - deshalb hier abgefangen statt den Aufrufer (marktscan_job()) crashen zu
    lassen."""
    if not kaufkandidaten:
        return
    try:
        import config as config_module
        from api.email_notify import send_notification_email

        config_dict = config_module.load_config()
        email_cfg = config_dict.get("benachrichtigung", {}).get("email", {})
        if not email_cfg.get("aktiv", False):
            return
        empfaenger = email_cfg.get("empfaenger")
        if not empfaenger:
            return
        if not config_dict.get("marktscan", {}).get("benachrichtigung_email", False):
            return

        zeilen = []
        for c in kaufkandidaten:
            score_text = f"{c.score_gesamt:.0f}" if c.score_gesamt is not None else "?"
            zeile = f"- {c.symbol} ({c.name}), Score {score_text}, Tier {c.tier}: {c.einstufung_begruendung}"
            if c.groq_kurzbegruendung:
                zeile += f"\n  KI-Kurzbegründung: {c.groq_kurzbegruendung}"
            zeilen.append(zeile)

        body = (
            f"{len(kaufkandidaten)} neue(r) Kaufkandidat(en) beim Marktscan gefunden:\n\n"
            + "\n".join(zeilen)
            + "\n\nDetails im Marktscan-Tab der App."
        )
        send_notification_email(
            f"TradingInfoTool: {len(kaufkandidaten)} neue(r) Marktscan-Kaufkandidat(en)",
            body,
            empfaenger,
        )
    except Exception:
        logger.exception("Marktscan-Kaufkandidaten-E-Mail fehlgeschlagen")


def _ist_email_relevantes_asset(
    symbol: str, watchlist: list, bitpanda_assets: list | None, conn_factory=None,
) -> bool:
    """Bitpanda-Listing-Filter (2026-07-14, In-App-Schalter, siehe ui/app.py::
    _toggle_email_nur_bitpanda(), Standard AN) - Umsetzung erfolgt manuell ueber
    die Bitpanda-App, eine Empfehlung fuer ein dort nicht gelistetes Asset waere
    also ohnehin nicht direkt ausfuehrbar. ui/settings.py hat keine tkinter-
    Abhaengigkeit, deshalb hier ohne Probleme aus dem Hintergrund-Job lesbar.

    WatchlistAsset speichert KEIN bitpanda_gelistet-Feld (das wird bei jedem
    Signal-Lauf frisch per API abgefragt, siehe agent/krypto/pipeline.py::
    generate_signal()) - bitpanda_assets wird deshalb einmal pro Job-Lauf vom
    Aufrufer (hebel_screening_job()) geholt und hier durchgereicht, statt es
    pro Signal erneut abzufragen.

    Nachtrag (2026-07-22, echter Fund: DBPK/3QSS-Hedge-Signale bekamen trotz
    bestaetigtem manuellem Override nie eine E-Mail): der `/v3/assets`-Live-
    Check deckt Bitpandas "Bitpanda Stocks"-Fractional-ETF/ETC-Produktlinie
    nachweislich NICHT vollstaendig ab (echte Bitpanda-App-Screenshots hatten
    das am 2026-07-20 bewiesen, siehe database/db.py::asset_bitpanda_override-
    Tabellendocstring) - deshalb existiert der manuelle Override-Toggle im
    Watchlist-Tab. Alle 4 Spot-family-Pipelines (agent/krypto|aktien|rohstoff|
    themen_etf/pipeline.py) fragen db.get_bitpanda_gelistet_override() bereits
    nach einem negativen Live-Check ab - dieses E-Mail-Gate war die einzige
    Stelle, die den Override noch NICHT respektierte. `conn_factory` optional
    (Standard None) fuer Rueckwaertskompatibilitaet bestehender Aufrufer/Tests
    ohne DB-Zugriff - ohne conn_factory bleibt das alte Verhalten (nur Live-
    Check) unveraendert."""
    import ui.settings as ui_settings

    settings = ui_settings.load_settings()
    if not settings.get("email_empfehlungen_nur_bitpanda", True):
        return True
    if bitpanda_assets is None:
        # P-10: Abruf fehlgeschlagen -> nicht blockieren, lieber eine Mail zu
        # viel als eine handlungsrelevante Empfehlung zu verlieren.
        return True
    asset = next((a for a in watchlist if a.symbol == symbol), None)
    if asset is None:
        return True
    from api.bitpanda import is_listed

    if is_listed(symbol, bitpanda_assets, name=asset.name):
        return True
    if conn_factory is not None:
        try:
            conn = conn_factory()
            try:
                if db.get_bitpanda_gelistet_override(conn, symbol):
                    return True
            finally:
                conn.close()
        except Exception:
            logger.exception("Bitpanda-Override-Abfrage fuer %s fehlgeschlagen", symbol)
    return False


def _formatiere_top_gruende(signal) -> str:
    gruende = [getattr(signal, f"top_grund_{i}_text", None) for i in range(1, 6)]
    return "\n".join(f"- {g}" for g in gruende if g)


def _formatiere_zeitpunkt_lokal(iso_timestamp: str | None) -> str:
    """BUGFIX (2026-07-21, Nutzer-Fund): 'Berechnet: ...' in den Signal-E-Mails
    zeigte bisher den rohen UTC-Zeitstempel aus der DB (`signal.created_at`)
    OHNE Umrechnung auf lokale Zeit, waehrend der E-Mail-Client (Gmail) den
    Empfangszeitpunkt ganz normal lokal anzeigt - das erweckte den falschen
    Eindruck einer ~2-Stunden-Verzoegerung zwischen Berechnung und Versand
    (CEST = UTC+2), obwohl beide Zeitpunkte nur Sekunden auseinanderlagen.
    `astimezone()` ohne Argument konvertiert auf die lokale Systemzeitzone."""
    if not iso_timestamp:
        return "-"
    try:
        dt = datetime.fromisoformat(iso_timestamp)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone().strftime("%Y-%m-%d %H:%M")
    except ValueError:
        return iso_timestamp[:16].replace("T", " ")


def _formatiere_key_risks(signal) -> str:
    """Nachbesserung (2026-07-17, Nutzer-Fund: E-Mail-Inhalt unvollstaendig) -
    `key_risks` wurde bisher von der KI erzeugt, im Signale-/Hebel-Tab
    angezeigt, aber nie in die E-Mail uebernommen - genau die Information, die
    fuer eine Entscheidung von unterwegs am wichtigsten waere."""
    if not signal.key_risks_text:
        return ""
    zeilen = [f"- {z}" for z in signal.key_risks_text.split("\n") if z.strip()]
    return "Risiken:\n" + "\n".join(zeilen) if zeilen else ""


def _formatiere_halte_kriterium(signal) -> str:
    """Siehe _formatiere_key_risks()-Docstring - gleiche Nachbesserung, gleicher
    Grund. Nur Felder aufnehmen, die tatsaechlich gesetzt sind (Regel 17 im
    SYSTEM_PROMPT verlangt nur mindestens EINES der drei Detail-Felder)."""
    from ui.formatting import format_money

    if not signal.halte_kriterium_bucket:
        return ""
    teile = [f"Zeithorizont: {signal.halte_kriterium_bucket}"]
    if signal.halte_kriterium_ziel_preis_eur is not None:
        teile.append(f"Zielkurs: {format_money(signal.halte_kriterium_ziel_preis_eur)} EUR")
    if signal.halte_kriterium_ziel_datum:
        teile.append(f"Zieldatum: {signal.halte_kriterium_ziel_datum}")
    if signal.halte_kriterium_bedingung_text:
        teile.append(f"Bedingung: {signal.halte_kriterium_bedingung_text}")
    return "Halte-Kriterium: " + " | ".join(teile)


def _formatiere_positionsgroesse_und_tranchen(signal) -> str:
    """Nachbesserung (2026-07-16, Nutzer-Audit 'sind alle relevanten Infos in
    der E-Mail enthalten?'): position_size_*/tranchen_json waren im
    Signale-Tab (ui/signals_view.py) schon immer vollstaendig sichtbar, in
    der E-Mail bisher aber komplett gefehlt - ohne Kaufmenge/Tranchen-Anteile
    ist eine Empfehlung von unterwegs nicht vollstaendig umsetzbar. Gleiche
    Rundung/Darstellung wie im Signale-Tab (format_money), bewusst kompakter
    (keine Zonen-Wiederholung, die stehen bereits weiter oben in der Mail)."""
    import json

    from ui.formatting import format_money

    zeilen = []
    if signal.position_size_usd or signal.position_size_eur or signal.position_size_note:
        zeilen.append(
            f"Positionsgröße: {format_money(signal.position_size_usd)} USD / "
            f"{format_money(signal.position_size_eur)} EUR"
        )
        if signal.position_size_note:
            zeilen.append(f"  {signal.position_size_note}")

    tranchen = None
    if signal.tranchen_json:
        try:
            tranchen = sorted(json.loads(signal.tranchen_json), key=lambda t: t.get("rang", 0))
        except (ValueError, TypeError):
            tranchen = None
    if tranchen:
        zeilen.append("Tranchen (Info, keine automatische Ausführung):")
        gesamt_usd = signal.position_size_usd
        for eintrag in tranchen:
            anteil = eintrag.get("anteil_prozent")
            betrag_text = ""
            if gesamt_usd and anteil is not None:
                betrag_text = f" (~{format_money(gesamt_usd * anteil / 100)} USD)"
            zeilen.append(f"  Tranche {eintrag.get('rang')}: {anteil:g}%{betrag_text}")

    return "\n".join(zeilen)


def _formatiere_gegenargument(signal) -> str:
    """2026-07-19 (E-Mail-/App-Neustrukturierung in 3 Abschnitte) - `gegenargument`
    existiert seit 2026-07-18 als Pflichtfeld (SYSTEM_PROMPT Regel 13/22,
    staerkstes Argument GEGEN die eigene Empfehlung), fehlte bisher aber
    komplett in E-Mail und App-Detail-Panel."""
    if not signal.gegenargument:
        return ""
    return f"Gegenargument (stärkste Einwand gegen diese Empfehlung):\n{signal.gegenargument}"


def _formatiere_forecast(signal) -> str:
    """2026-07-19 - Bull/Base/Bear-Szenarien waren bisher nur in der DB, nicht
    in E-Mail/App sichtbar, obwohl sie ein zentraler Baustein der Gegenszenario-
    Deckel-Logik sind (hebel_risk_gate.py/risk_gate.py)."""
    zeilen = []
    for label, text_attr, prob_attr in (
        ("Bull", "forecast_bull_text", "forecast_bull_prob_pct"),
        ("Base", "forecast_base_text", "forecast_base_prob_pct"),
        ("Bear", "forecast_bear_text", "forecast_bear_prob_pct"),
    ):
        text = getattr(signal, text_attr, None)
        prob = getattr(signal, prob_attr, None)
        if text:
            prob_text = f" ({prob:.0f}%)" if prob is not None else ""
            zeilen.append(f"{label}{prob_text}: {text}")
    return "Forecast-Szenarien:\n" + "\n".join(zeilen) if zeilen else ""


_RISIKOFAKTOR_SYMBOL = {"positiv": "▲", "neutral": "●", "negativ": "▼"}
# 2026-07-20: urspruenglich farbige Kreis-Emoji (🟢/⚪/🔴) - Nutzer-Screenshot
# vom echten Notebook-App-Detail-Panel zeigte, dass die Farbunterscheidung dort
# komplett verloren ging (Tkinter-Fontfallback), ausserdem wurde bereits zuvor
# ⚪ in manchen E-Mail-Clients (z.B. Gmail-Web) blass-lila statt eindeutig grau
# dargestellt. Wechsel auf die bereits im Projekt etablierten Form-Marker
# ▲/●/▼ (siehe ui/app.py/portfolio.py/screener_view.py: These-Marker, gleiche
# Semantik positiv/neutral/negativ) - Form statt Farbe ist robust gegen
# Emoji-Rendering-Unterschiede, sowohl in der App als auch im E-Mail-Text.
# Eigene Kopie wie ui/formatting.py::RISIKOFAKTOREN_LEGENDE (dort fuer den
# App-Kontext), bewusst getrennt gehalten (siehe _formatiere_risikofaktoren()-
# Docstring).
_RISIKOFAKTOREN_LEGENDE = "(▲ unterstützt die Empfehlung · ● neutral · ▼ Warnsignal/Risiko)"


def _formatiere_risikofaktoren(signal) -> str:
    """2026-07-19 (Kern von Abschnitt 3 "Konklusion" - Nutzer-Wunsch nach dem
    echten AVAX-Hebel-Fund: E-Mail/App sollen zwischen 1. mathematisch
    berechneten Fakten, 2. LLM-Bewertung und 3. einer deterministischen
    Konklusion mit positiven/neutralen/negativen Risikofaktoren trennen).
    `risikofaktoren_json` wird deterministisch von agent/krypto/risk_gate.py::
    compute_risikofaktoren() bzw. hebel_risk_gate.py::
    compute_risikofaktoren_hebel() erzeugt - bewusst NICHT vom LLM, siehe
    dortige Docstrings (echter Interpretationsfehler des Modells war der
    Ausloeser)."""
    import json

    if not signal.risikofaktoren_json:
        return ""
    try:
        faktoren = json.loads(signal.risikofaktoren_json)
    except (ValueError, TypeError):
        return ""
    if not faktoren:
        return ""

    gruppen: dict[str, list[dict]] = {"negativ": [], "neutral": [], "positiv": []}
    for f in faktoren:
        gruppen.setdefault(f.get("bewertung", "neutral"), []).append(f)

    zeilen = []
    for bewertung in ("negativ", "neutral", "positiv"):
        eintraege = gruppen.get(bewertung, [])
        if not eintraege:
            continue
        for f in eintraege:
            symbol = _RISIKOFAKTOR_SYMBOL.get(bewertung, "●")
            zeilen.append(f"{symbol} {f.get('name', '')}: {f.get('begruendung', '')}")
    # 2026-07-22, Nutzer-Fund: Outlook Web entfernt einzelne "\n" beim Anzeigen
    # ("Wir haben zusätzliche Zeilenumbrüche aus dieser Nachricht entfernt") und
    # verschmilzt dadurch Legende + ersten Risikofaktor zu einem Fliesstext.
    # Andere Abschnitte dieser E-Mail trennen Bloecke bereits mit "\n\n" und
    # rendern deshalb zuverlaessig als eigene Absaetze - hier genauso: jede
    # Risikofaktor-Zeile bekommt eine echte Leerzeile als Absatztrenner.
    return "\n\n".join(zeilen)


def _notify_spot_signal(signal, watchlist: list, bitpanda_assets: list | None, conn_factory=None) -> None:
    """E-Mail bei handlungsrelevanter Spot-Empfehlung (2026-07-14, Erweiterung
    von U-8/P-7 - Empfehlungen sollen den Nutzer auch erreichen, wenn er selten
    am Notebook ist). HALTEN loest bewusst NIE eine Mail aus. Eigener try/except
    (P-10) - ein E-Mail-Fehler darf den Budget-Allocator-Lauf nicht nachtraeglich
    als fehlgeschlagen erscheinen lassen."""
    from agent.krypto.analyst import REQUIRED_ACTIONS

    if signal.cash_veto:
        try:
            _notify_cash_veto_warning(signal)
        except Exception:
            logger.exception("Cash-Veto-Warnmail für %s fehlgeschlagen", signal.symbol)

    if signal.action not in REQUIRED_ACTIONS or signal.action == "HALTEN":
        return
    if not _ist_email_relevantes_asset(signal.symbol, watchlist, bitpanda_assets, conn_factory):
        return
    try:
        import config as config_module
        from api.email_notify import send_notification_email
        from ui.formatting import format_money

        email_cfg = config_module.load_config().get("benachrichtigung", {}).get("email", {})
        if not email_cfg.get("aktiv", False) or not email_cfg.get("empfehlungen_aktiv", False):
            return
        empfaenger = email_cfg.get("empfaenger")
        if not empfaenger:
            return

        # BUGFIX (2026-07-17, Nutzer-Fund): Entry/Stop-Loss/Take-Profit wurden
        # bisher als rohe Python-Floats interpoliert statt ueber format_money()
        # (das genau dafuer da ist, siehe dessen Docstring "nie wissenschaftliche
        # Notation") - bei sehr kleinen Kursen (Micro-/Meme-Coins, z.B. 1.06e-06)
        # rutschte Python automatisch in wissenschaftliche Notation, unlesbar
        # fuer eine schnelle Entscheidung von unterwegs.
        positionsgroesse_text = _formatiere_positionsgroesse_und_tranchen(signal)
        risiken_text = _formatiere_key_risks(signal)
        halte_kriterium_text = _formatiere_halte_kriterium(signal)
        gegenargument_text = _formatiere_gegenargument(signal)
        forecast_text = _formatiere_forecast(signal)
        risikofaktoren_text = _formatiere_risikofaktoren(signal)
        zeitpunkt_text = _formatiere_zeitpunkt_lokal(signal.created_at)
        body = (
            f"Aktion: {signal.action}\n"
            f"Regime: {signal.regime or 'unbekannt'}\n"
            f"Berechnet: {zeitpunkt_text} · Anbieter: {signal.groq_model or '-'}\n\n"
            f"--- 1. MATHEMATISCH BERECHNET ---\n"
            f"Entry: {format_money(signal.entry_eur_von)}-{format_money(signal.entry_eur_bis)} EUR\n"
            f"Stop-Loss: {format_money(signal.stop_loss_eur_von)}-{format_money(signal.stop_loss_eur_bis)} EUR\n"
            f"Take-Profit: {format_money(signal.take_profit_eur_von)}-{format_money(signal.take_profit_eur_bis)} EUR\n"
            + (f"{positionsgroesse_text}\n" if positionsgroesse_text else "")
            + f"\n--- 2. LLM-BEWERTUNG (Konfidenz {signal.confidence_pct}%) ---\n"
            f"{signal.short_reasoning or ''}\n\n"
            f"Top-Gründe:\n{_formatiere_top_gruende(signal)}\n\n"
            + (f"{gegenargument_text}\n\n" if gegenargument_text else "")
            + (f"{risiken_text}\n\n" if risiken_text else "")
            + (f"{halte_kriterium_text}\n\n" if halte_kriterium_text else "")
            + (f"{forecast_text}\n" if forecast_text else "")
            + "\n--- 3. KONKLUSION (RISIKOFAKTOREN) ---\n"
            + f"{_RISIKOFAKTOREN_LEGENDE}\n\n"
            + (risikofaktoren_text if risikofaktoren_text else "Keine strukturierten Risikofaktoren verfügbar.")
            + "\n\nDetails im Signale-Tab der App. Ausführung manuell über die Bitpanda-App."
        )
        send_notification_email(f"TradingInfoTool: {signal.action} {signal.symbol}", body, empfaenger)
    except Exception:
        logger.exception("Spot-Empfehlungs-E-Mail für %s fehlgeschlagen", signal.symbol)


def _notify_hebel_signal(signal, watchlist: list, bitpanda_assets: list | None, conn_factory=None) -> None:
    """Analog _notify_spot_signal() fuer Hebel-Empfehlungen (7-Aktionen-
    Vokabular statt 5, siehe agent/krypto/hebel_analyst.REQUIRED_HEBEL_
    ACTIONS).

    `conn_factory` (2026-07-21, SLA-Redesign-Transparenz, optional damit
    bestehende Aufrufer/Tests ohne DB-Zugriff nicht brechen) erlaubt die
    Anzeige der wahren Wartezeit seit Erstkandidatur in der E-Mail - NUR
    fuer Hebel sinnvoll (Tier 3 Spot-Rotation hat keine vergleichbare
    Kandidatur-Historie, siehe database/db.py::
    get_hebel_wartezeit_stunden_je_paar())."""
    from agent.krypto.hebel_analyst import REQUIRED_HEBEL_ACTIONS

    if signal.action not in REQUIRED_HEBEL_ACTIONS or signal.action == "HALTEN":
        return
    if not _ist_email_relevantes_asset(signal.symbol, watchlist, bitpanda_assets, conn_factory):
        return
    try:
        import config as config_module
        from api.email_notify import send_notification_email
        from ui.formatting import format_money

        email_cfg = config_module.load_config().get("benachrichtigung", {}).get("email", {})
        if not email_cfg.get("aktiv", False) or not email_cfg.get("empfehlungen_aktiv", False):
            return
        empfaenger = email_cfg.get("empfaenger")
        if not empfaenger:
            return

        # BUGFIX + Nachbesserung (2026-07-17, siehe _notify_spot_signal()-
        # Kommentar): dieselben zwei Probleme (rohe Floats statt format_money(),
        # fehlende Risiken/Halte-Kriterium) galten hier identisch.
        hinweis = f"Hinweis: {signal.ausfuehrbarkeit_hinweis}\n" if signal.ausfuehrbarkeit_hinweis else ""
        eigenkapital_eur_text = (
            f" ({format_money(signal.eigenkapitalbedarf_eur)} EUR)"
            if signal.eigenkapitalbedarf_eur is not None else ""
        )
        eigenkapital_zeile = (
            f"Eigenkapitalbedarf: {format_money(signal.eigenkapitalbedarf_usd)} USD{eigenkapital_eur_text}\n"
            if signal.eigenkapitalbedarf_usd is not None else ""
        )
        senkung_zeile = (
            f"Eigenkapital-Nachschuss für Hebel-Senkung: "
            f"{format_money(signal.hebel_senkung_eigenkapital_nachschuss_eur)} EUR\n"
            if signal.hebel_senkung_eigenkapital_nachschuss_eur is not None else ""
        )
        korrektur_zeile = f"({signal.hebel_korrektur_hinweis})\n" if signal.hebel_korrektur_hinweis else ""
        risiken_text = _formatiere_key_risks(signal)
        halte_kriterium_text = _formatiere_halte_kriterium(signal)
        gegenargument_text = _formatiere_gegenargument(signal)
        forecast_text = _formatiere_forecast(signal)
        risikofaktoren_text = _formatiere_risikofaktoren(signal)
        zeitpunkt_text = _formatiere_zeitpunkt_lokal(signal.created_at)
        wartezeit_text = ""
        if conn_factory is not None:
            try:
                conn = conn_factory()
                try:
                    wartezeiten = db.get_hebel_wartezeit_stunden_je_paar(conn)
                finally:
                    conn.close()
                stunden = wartezeiten.get((signal.symbol, signal.richtung))
                if stunden is not None:
                    wartezeit_text = f" · Wartezeit seit Erstkandidatur: {stunden:.1f}h"
            except Exception:
                logger.exception("Wartezeit-Berechnung fuer Hebel-E-Mail (%s) fehlgeschlagen", signal.symbol)
        body = (
            f"Richtung: {signal.richtung}, Aktion: {signal.action}\n"
            f"Regime: {signal.regime or 'unbekannt'}\n"
            f"Berechnet: {zeitpunkt_text} · Anbieter: {signal.llm_model or '-'}{wartezeit_text}\n\n"
            f"--- 1. MATHEMATISCH BERECHNET ---\n"
            f"Hebel: {signal.hebel_final}x\n"
            f"{korrektur_zeile}"
            f"Entry: {format_money(signal.entry_eur_von)}-{format_money(signal.entry_eur_bis)} EUR\n"
            f"Stop-Loss: {format_money(signal.stop_loss_eur_von)}-{format_money(signal.stop_loss_eur_bis)} EUR\n"
            f"Take-Profit: {format_money(signal.take_profit_eur_von)}-{format_money(signal.take_profit_eur_bis)} EUR\n"
            f"Geschätzter Liquidationspreis: {format_money(signal.liquidationspreis_geschaetzt_usd)} USD"
            f"{' (' + format_money(signal.liquidationspreis_geschaetzt_eur) + ' EUR)' if signal.liquidationspreis_geschaetzt_eur is not None else ''}\n"
            f"{eigenkapital_zeile}"
            f"{senkung_zeile}"
            f"{hinweis}"
            + f"\n--- 2. LLM-BEWERTUNG (Konfidenz {signal.confidence_pct}%) ---\n"
            f"{signal.short_reasoning or ''}\n\n"
            f"Top-Gründe:\n{_formatiere_top_gruende(signal)}\n\n"
            + (f"{gegenargument_text}\n\n" if gegenargument_text else "")
            + (f"{risiken_text}\n\n" if risiken_text else "")
            + (f"{halte_kriterium_text}\n\n" if halte_kriterium_text else "")
            + (f"{forecast_text}\n" if forecast_text else "")
            + "\n--- 3. KONKLUSION (RISIKOFAKTOREN) ---\n"
            + f"{_RISIKOFAKTOREN_LEGENDE}\n\n"
            + (risikofaktoren_text if risikofaktoren_text else "Keine strukturierten Risikofaktoren verfügbar.")
            + "\n\nDetails im Hebel-Tab der App. Ausführung manuell über die Bitpanda-App."
        )
        # Liquiditätszonen-Grafik (2026-07-23, Nutzer-Wunsch: nicht nur in der
        # App, auch in der E-Mail) - derselbe Renderer wie ui/hebel_view.py,
        # baut aus dem bereits im Signal gespeicherten Fakt (facts_json) ein
        # PNG mit konkreten Zahlen/Einheiten. None, wenn keine Zone vorliegt
        # oder der aktuelle Kurs nicht ermittelt werden konnte - Mail geht
        # dann ganz normal ohne Bild raus (kein Hard-Fail wegen der Grafik).
        chart_png = None
        try:
            import json as _json
            from ui.liquidity_chart import render_liquiditaetszonen_chart

            facts = _json.loads(signal.facts_json)
            liquiditaetszonen = facts.get("liquiditaetszonen")
            if liquiditaetszonen and conn_factory is not None:
                conn = conn_factory()
                try:
                    price_snap = db.get_latest_prices(conn).get(signal.symbol)
                finally:
                    conn.close()
                if price_snap is not None and price_snap.price_eur:
                    chart_png = render_liquiditaetszonen_chart(
                        liquiditaetszonen, price_snap.price_eur, "EUR",
                    )
        except Exception:
            logger.exception("Liquiditätszonen-Grafik für %s fehlgeschlagen", signal.symbol)

        send_notification_email(
            f"TradingInfoTool: Hebel {signal.action} {signal.symbol} ({signal.richtung})", body, empfaenger,
            inline_image_png=chart_png,
        )
    except Exception:
        logger.exception("Hebel-Empfehlungs-E-Mail für %s fehlgeschlagen", signal.symbol)


def _notify_multi_asset_signal(signal, watchlist: list, bitpanda_assets: list | None, conn_factory=None) -> None:
    """Analog _notify_spot_signal() fuer Aktien/Rohstoffe/Hedge (2026-07-18,
    siehe agent/multi_asset_batch.py) - 4-Aktionen-Vokabular (KAUFEN/VERKAUFEN/
    HALTEN/NACHKAUFEN, kein TAUSCHEN, siehe REQUIRED_ACTIONS in agent/aktien|
    rohstoff|hedge/analyst.py, identisch in allen dreien). Hedge-Signale haben
    KEIN Bitpanda-Veto (agent/hedge/pipeline.py ruft risk_gate.pre_check() nicht
    auf, siehe dessen Modul-Docstring) - _ist_email_relevantes_asset() bleibt
    trotzdem unveraendert anwendbar, sie prueft nur den allgemeinen Bitpanda-
    Katalog, nicht pipelinespezifische Vetos.

    `conn_factory` (2026-07-22, echter Fund: DBPK/3QSS trotz Override nie
    gemailt) - siehe _ist_email_relevantes_asset()-Docstring fuer den vollen
    Root-Cause."""
    if signal.cash_veto:
        try:
            _notify_cash_veto_warning(signal)
        except Exception:
            logger.exception("Cash-Veto-Warnmail für %s fehlgeschlagen", signal.symbol)

    if signal.action == "HALTEN":
        return
    if not _ist_email_relevantes_asset(signal.symbol, watchlist, bitpanda_assets, conn_factory):
        return
    try:
        import config as config_module
        from api.email_notify import send_notification_email
        from ui.formatting import format_money

        email_cfg = config_module.load_config().get("benachrichtigung", {}).get("email", {})
        if not email_cfg.get("aktiv", False) or not email_cfg.get("empfehlungen_aktiv", False):
            return
        empfaenger = email_cfg.get("empfaenger")
        if not empfaenger:
            return

        positionsgroesse_text = _formatiere_positionsgroesse_und_tranchen(signal)
        risiken_text = _formatiere_key_risks(signal)
        halte_kriterium_text = _formatiere_halte_kriterium(signal)
        gegenargument_text = _formatiere_gegenargument(signal)
        forecast_text = _formatiere_forecast(signal)
        risikofaktoren_text = _formatiere_risikofaktoren(signal)
        zeitpunkt_text = _formatiere_zeitpunkt_lokal(signal.created_at)
        body = (
            f"Aktion: {signal.action}\n"
            f"Berechnet: {zeitpunkt_text} · Anbieter: {signal.groq_model or '-'}\n\n"
            f"--- 1. MATHEMATISCH BERECHNET ---\n"
            f"Entry: {format_money(signal.entry_eur_von)}-{format_money(signal.entry_eur_bis)} EUR\n"
            f"Stop-Loss: {format_money(signal.stop_loss_eur_von)}-{format_money(signal.stop_loss_eur_bis)} EUR\n"
            f"Take-Profit: {format_money(signal.take_profit_eur_von)}-{format_money(signal.take_profit_eur_bis)} EUR\n"
            + (f"{positionsgroesse_text}\n" if positionsgroesse_text else "")
            + f"\n--- 2. LLM-BEWERTUNG (Konfidenz {signal.confidence_pct}%) ---\n"
            f"{signal.short_reasoning or ''}\n\n"
            f"Top-Gründe:\n{_formatiere_top_gruende(signal)}\n\n"
            + (f"{gegenargument_text}\n\n" if gegenargument_text else "")
            + (f"{risiken_text}\n\n" if risiken_text else "")
            + (f"{halte_kriterium_text}\n\n" if halte_kriterium_text else "")
            + (f"{forecast_text}\n" if forecast_text else "")
            + "\n--- 3. KONKLUSION (RISIKOFAKTOREN) ---\n"
            + f"{_RISIKOFAKTOREN_LEGENDE}\n\n"
            + (risikofaktoren_text if risikofaktoren_text else "Keine strukturierten Risikofaktoren verfügbar.")
            + "\n\nDetails im Signale-Tab der App. Ausführung manuell über die Bitpanda-App."
        )
        send_notification_email(f"TradingInfoTool: {signal.action} {signal.symbol}", body, empfaenger)
    except Exception:
        logger.exception("Multi-Asset-Empfehlungs-E-Mail für %s fehlgeschlagen", signal.symbol)


def _refresh_hebel_position_liquidation_prices(conn) -> None:
    """Fuer jede aktuell offene Margin-Position den geschaetzten Liquidationspreis
    mit den ECHTEN verstrichenen Tagen neu berechnen (2026-07-14, Phase 3) -
    entry_preis_eur wird aus positionswert_eur/positionsmenge abgeleitet (kein
    separat gespeicherter Einstandspreis noetig, siehe database/models.py::
    HebelPosition-Docstring). Ohne positionsmenge (z.B. sehr alte/unvollstaendige
    Datensaetze) wird die Position uebersprungen statt eine falsche Schaetzung
    zu zeigen (P-10)."""
    import config as config_module
    from agent.krypto.hebel_risk_gate import estimate_liquidation_price

    sicherheitsmarge_relativ = config_module.load_config()["risiko"]["hebel"]["liquidations_sicherheitsmarge_relativ"]
    now_unix = int(time.time())
    for pos in db.get_open_hebel_positions(conn):
        if not pos.positionsmenge or not pos.positionswert_eur:
            continue
        entry_preis_eur = pos.positionswert_eur / pos.positionsmenge
        hebel = pos.hebel_effektiv or 1.0
        eroeffnet_unix = int(datetime.fromisoformat(pos.eroeffnet_am).timestamp())
        days_held = max(0.0, (now_unix - eroeffnet_unix) / 86400)
        pos.liquidationspreis_geschaetzt_eur = estimate_liquidation_price(
            entry_preis_eur, hebel, pos.richtung, days_held=days_held,
            sicherheitsmarge_relativ=sicherheitsmarge_relativ,
        )
        pos.liquidationspreis_berechnet_am = datetime.now(timezone.utc).isoformat()
        db.upsert_hebel_position(conn, pos)


def hebel_screening_job(
    coingecko_client, kraken_client, conn_factory, watchlist_provider, bitpanda_api_key=None,
    groq_client=None, gemini_client=None, fred_api_key=None,
    mistral_client=None, zai_client=None,
) -> bool:
    """`watchlist_provider` siehe refresh_prices_job()-Docstring (2026-07-23).

    Hebel-Screening (2026-07-14, Phase 1, siehe docs/hebel_positionsformel.md)
    - rein deterministisches Zwei-Zweige-Scoring, KEIN Groq-Aufruf. Ergebnis
    landet in hebel_triggers.

    Seit Phase 3 (Positions-Rekonstruktion) huckepack im selben 15-Min-Takt:
    Bitpanda-Margin-Positions-Sync + Liquidationspreis-Neuberechnung fuer
    offene Positionen (P-8: nur falls bitpanda_api_key gesetzt ist, sonst
    stillschweigend uebersprungen - kein Fehler).

    Seit Phase 5 (Budget-Allocator, siehe docs/budget_queue_design.md)
    zusaetzlich: der zentrale Allocator laeuft im selben Takt und verteilt das
    gemeinsame Tagesbudget ueber Hebel-Kandidaten (dieses Screening),
    Marktscan-Kaufkandidaten UND Spot-Rotation (P-8: nur falls mindestens
    groq_client gesetzt ist, sonst uebersprungen - Groq ist die einzige
    echte Voraussetzung, mistral_client/gemini_client sind optionale
    Fallback-Stufen).

    **2026-07-17:** Cerebras vollstaendig aus der Fallback-Kette entfernt
    (Mistral hat dessen Rolle uebernommen, siehe Memory
    project_cerebras_free_tier_aenderung_2026-08-17.md - urspruenglich war
    nur die Entfernung zum 2026-08-17 geplant, der Nutzer hat sich aber
    bewusst fuer die sofortige vollstaendige Entfernung entschieden)."""
    if not hebel_screening_lock.acquire(blocking=False):
        logger.info("Hebel-Screening: bereits in Ausführung - übersprungen")
        return False
    watchlist = watchlist_provider()
    _job_started_at["hebel_screening"] = time.monotonic()
    try:
        import config as config_module
        from agent.krypto.hebel_screening import run_hebel_screening

        config_dict = config_module.load_config()
        if not config_dict.get("hebel_screening", {}).get("aktiv", True):
            logger.info("Hebel-Screening deaktiviert (config.yaml hebel_screening.aktiv=false) - übersprungen")
            return True

        triggers = run_hebel_screening(conn_factory, watchlist, kraken_client, coingecko_client, config_dict)
        kandidaten = [t for t in triggers if t.ist_kandidat]
        logger.info(
            "Hebel-Screening: %d Assets bewertet, %d Kandidaten (Score >= Schwelle)",
            len(triggers), len(kandidaten),
        )
        _pruefe_oi_abdeckung_warnung(conn_factory, config_dict)

        if bitpanda_api_key:
            from importer.bitpanda_margin_positions import auto_add_unknown_hebel_symbols, sync_hebel_positions

            conn = conn_factory()
            try:
                sync_result = sync_hebel_positions(conn, bitpanda_api_key)
                logger.info(
                    "Hebel-Positions-Sync: %d Transaktionen geladen, %d Positionen aktualisiert, %d neu geschlossen",
                    sync_result.total_transactions_fetched, len(sync_result.positionen_aktualisiert),
                    sync_result.neu_geschlossen,
                )
                _refresh_hebel_position_liquidation_prices(conn)

                # Klassifikations-Redesign (2026-07-16): offene Positionen auf
                # bisher unbekannten Symbolen automatisch zur Watchlist
                # ergaenzen, sonst wuerden Screening/Preisversorgung/die neue
                # Positions-Prioritaet fuer sie ins Leere laufen.
                try:
                    from api.bitpanda import get_listed_assets
                    # BUGFIX (2026-07-16, live am Notebook gefunden): get_listed_assets()
                    # nimmt eine optionale requests.Session fuer Connection-Reuse entgegen,
                    # KEINEN API-Key (der Bitpanda-Asset-Katalog ist ein oeffentlicher,
                    # unauthentifizierter Endpunkt) - der urspruengliche Aufruf mit
                    # bitpanda_api_key als Positionsargument loeste bei JEDEM Lauf
                    # "AttributeError: 'str' object has no attribute 'get'" aus.
                    neue_symbole = auto_add_unknown_hebel_symbols(
                        conn, watchlist, get_listed_assets(), coingecko_client=coingecko_client,
                    )
                    if neue_symbole:
                        logger.info(
                            "Hebel-Position(en) ohne Watchlist-Eintrag automatisch ergaenzt: %s",
                            ", ".join(neue_symbole),
                        )
                except Exception:
                    logger.exception("Auto-Add unbekannter Hebel-Symbole fehlgeschlagen")
            finally:
                conn.close()

        if groq_client is not None:
            from agent.krypto.budget_allocator import run_budget_allocator

            # E-Mail-Latenz-Fix (2026-07-23, echter Fund: ein einzelner Batch mit
            # 38 Kandidaten hing 18+ Minuten an langsamen/timeoutenden externen
            # Abrufen fest - da die Benachrichtigung bisher erst NACH vollstaendigem
            # Abschluss von run_budget_allocator() ausgeloest wurde, blieben laengst
            # fertige echte Signale (NEAR/SUI/VIRTUAL) ohne jede E-Mail haengen).
            # bitpanda_assets wird bewusst NICHT vorab, sondern lazy beim ersten
            # tatsaechlichen Signal geholt (haeufigster Fall: ein ganzer Zyklus
            # erzeugt gar kein echtes Signal, dann entfaellt der API-Call komplett -
            # identisches Verhalten wie vorher, nur zeitlich vorgezogen) und dann
            # fuer den Rest DIESES Laufs wiederverwendet (kein Mehrfach-Abruf je
            # Kandidat).
            bitpanda_assets_state = {"geholt": False, "wert": None}

            def _on_signal_ready(schluessel: str, ergebnis) -> None:
                if not bitpanda_assets_state["geholt"]:
                    try:
                        from api.bitpanda import get_listed_assets

                        bitpanda_assets_state["wert"] = get_listed_assets()
                    except Exception as exc:
                        bitpanda_assets_state["wert"] = None
                        logger.info("Bitpanda-Listing-Abruf für Empfehlungs-E-Mails fehlgeschlagen: %s", exc)
                    bitpanda_assets_state["geholt"] = True
                bitpanda_assets = bitpanda_assets_state["wert"]
                if schluessel.startswith("hebel:"):
                    _notify_hebel_signal(ergebnis, watchlist, bitpanda_assets, conn_factory)
                elif schluessel.startswith("spot:"):
                    _notify_spot_signal(ergebnis, watchlist, bitpanda_assets, conn_factory)

            allocation = run_budget_allocator(
                conn_factory, watchlist, groq_client, coingecko_client, kraken_client,
                fred_api_key, config_dict, gemini_client=gemini_client, mistral_client=mistral_client,
                zai_client=zai_client, on_signal_ready=_on_signal_ready,
            )
            logger.info(
                "Budget-Allocator: Hebel %d, Marktscan %d, Spot %d verarbeitet, %d fehlgeschlagen, "
                "Groq heute erschöpft: %s, "
                "Zai-Calls %d, Zai-Budget erschöpft: %s, "
                "Mistral-Calls %d, Mistral-Budget erschöpft: %s, "
                "Gemini-Calls %d, Gemini-Budget erschöpft: %s",
                len(allocation.hebel_verarbeitet), len(allocation.marktscan_verarbeitet),
                len(allocation.spot_verarbeitet), len(allocation.fehlgeschlagen),
                allocation.groq_erschoepft_erkannt,
                allocation.zai_calls_verbraucht, allocation.zai_budget_erschoepft,
                allocation.mistral_calls_verbraucht, allocation.mistral_budget_erschoepft,
                allocation.gemini_calls_verbraucht, allocation.gemini_budget_erschoepft,
            )
        else:
            logger.info("Budget-Allocator übersprungen (kein Groq-Client konfiguriert)")
    except Exception as exc:
        logger.exception("Hebel-Screening fehlgeschlagen")
        _notify_job_failure("hebel_screening", f"Hebel-Screening fehlgeschlagen: {exc}")
    finally:
        hebel_screening_lock.release()
        _job_started_at.pop("hebel_screening", None)
    return True


def multi_asset_batch_job(
    conn_factory, watchlist_provider, coingecko_client, groq_client=None, gemini_client=None, mistral_client=None,
) -> bool:
    """Multi-Asset-Batch (2026-07-18, siehe agent/multi_asset_batch.py Modul-
    Docstring fuer die volle Architektur-Begruendung) - automatische Signal-
    Erzeugung fuer Aktien/Rohstoffe/Hedge, bisher nur manuell per Klick
    erreichbar. P-8: nur aktiv, wenn mindestens groq_client gesetzt ist
    (gleiches Muster wie hebel_screening_job()). `watchlist_provider` siehe
    refresh_prices_job()-Docstring (2026-07-23)."""
    if not multi_asset_batch_lock.acquire(blocking=False):
        logger.info("Multi-Asset-Batch: bereits in Ausführung - übersprungen")
        return False
    watchlist = watchlist_provider()
    _job_started_at["multi_asset_batch"] = time.monotonic()
    try:
        if groq_client is None:
            logger.info("Multi-Asset-Batch übersprungen (kein Groq-Client konfiguriert)")
            return True

        import config as config_module
        from agent.multi_asset_batch import run_multi_asset_batch

        config_dict = config_module.load_config()
        result = run_multi_asset_batch(
            conn_factory, watchlist, groq_client, coingecko_client, config_dict,
            gemini_client=gemini_client, mistral_client=mistral_client,
        )
        logger.info(
            "Multi-Asset-Batch: %d verarbeitet, %d fehlgeschlagen, %d Cooldown-uebersprungen, "
            "Mistral-Calls %d, Gemini-Calls %d",
            len(result.verarbeitet), len(result.fehlgeschlagen), result.uebersprungen_cooldown,
            result.mistral_calls_verbraucht, result.gemini_calls_verbraucht,
        )
        if result.ergebnis_objekt:
            try:
                from api.bitpanda import get_listed_assets

                bitpanda_assets = get_listed_assets()
            except Exception as exc:
                bitpanda_assets = None
                logger.info("Bitpanda-Listing-Abruf für Multi-Asset-Empfehlungs-E-Mails fehlgeschlagen: %s", exc)
            for signal in result.ergebnis_objekt.values():
                _notify_multi_asset_signal(signal, watchlist, bitpanda_assets, conn_factory)
    except Exception as exc:
        logger.exception("Multi-Asset-Batch fehlgeschlagen")
        _notify_job_failure("multi_asset_batch", f"Multi-Asset-Batch fehlgeschlagen: {exc}")
    finally:
        multi_asset_batch_lock.release()
        _job_started_at.pop("multi_asset_batch", None)
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
        _notify_job_failure(event.job_id, f"Unbehandelter Fehler im Job-Wrapper: {event.exception}")
    else:
        logger.warning("Scheduler-Job '%s' verpasst (Misfire)", event.job_id)
        _notify_job_failure(event.job_id, "Verpasster Lauf (Misfire) - z. B. Rechner war im Standby.")


def _history_data_is_stale(conn, watchlist) -> bool:
    """Betriebssicherheit (2026-07-12): staleness-bewusster Vorab-Check fuer den
    sofortigen ersten refresh_history-Lauf nach einem Neustart - vermeidet einen
    vollen Asset-Refresh (CoinGecko-Kontingent) bei JEDEM Neustart, holt einen
    echten Rueckstand (z.B. nach laengerer Downtime) aber trotzdem sofort nach,
    statt bis zu 24 Std. auf den naechsten Intervall-Takt zu warten. Ein einzelnes
    stalles Asset genuegt, weil der Job ohnehin alle Assets in einem Lauf
    aktualisiert. Bei einem Fehler im Check selbst (z.B. DB-Problem) sicherer
    Default False - kein unbeabsichtigter sofortiger Kontingent-Verbrauch."""
    try:
        for asset in watchlist:
            if asset.coingecko_id is None:
                continue
            if staleness.is_history_stale(db.get_last_history_date(conn, asset.coingecko_id)):
                return True
        return False
    except Exception:
        logger.exception("Staleness-Check fuer Kurs-Historie fehlgeschlagen - kein Sofort-Lauf ausgeloest")
        return False


def _ohlc_data_is_stale(conn, watchlist) -> bool:
    """Analog zu _history_data_is_stale(), fuer den Kraken-OHLC-Job. Prueft nur
    Assets/Waehrungen mit echtem Kraken-Listing (KRAKEN_PAIR_MAP) - fehlende
    Listings sind eine bekannte, dokumentierte Deckungsluecke (siehe
    api/kraken_history.py), kein Staleness-Fall."""
    try:
        for asset in watchlist:
            pair_map = KRAKEN_PAIR_MAP.get(asset.symbol)
            if pair_map is None:
                continue
            for currency in pair_map:
                if staleness.is_history_stale(db.get_last_ohlc_date(conn, asset.symbol, currency)):
                    return True
        return False
    except Exception:
        logger.exception("Staleness-Check fuer Kraken-OHLC fehlgeschlagen - kein Sofort-Lauf ausgeloest")
        return False


def staleness_watchdog_job(conn_factory, watchlist_provider) -> None:
    """Periodischer Nachhol-Check (2026-07-23, siehe STALENESS_RECHECK_INTERVAL_
    MINUTES-Kommentar oben): _history_data_is_stale()/_ohlc_data_is_stale() liefen
    bisher nur beim App-Start - lief die App danach lange genug durch, konnte die
    2-Tage-Schwelle mitten im Betrieb unbemerkt ueberschritten werden. Erzwingt bei
    Bedarf einen sofortigen Lauf des jeweiligen Jobs UEBER DEN SCHEDULER selbst
    (modify_job, gleiches Muster wie _record_job_failure_for_backoff()) statt
    eines direkten Funktionsaufrufs - damit APScheduler's eigene
    Lauf-Serialisierung je job_id weiterhin greift (kein Doppel-Lauf-Risiko, falls
    der reguläre 24h-Takt zufaellig zeitgleich feuert). `watchlist_provider` siehe
    refresh_prices_job()-Docstring (2026-07-23)."""
    if _scheduler_ref is None:
        return
    watchlist = watchlist_provider()
    conn = conn_factory()
    try:
        history_stale = _history_data_is_stale(conn, watchlist)
        ohlc_stale = _ohlc_data_is_stale(conn, watchlist)
    finally:
        conn.close()
    if history_stale:
        logger.info(
            "Staleness-Watchdog: Kurs-Historie waehrend laufendem Betrieb veraltet "
            "- sofortiger Nachhol-Lauf ausgeloest"
        )
        try:
            _scheduler_ref.modify_job("refresh_history", next_run_time=datetime.now())
        except Exception:
            logger.exception("Staleness-Watchdog: Nachhol-Lauf fuer refresh_history konnte nicht ausgeloest werden")
    if ohlc_stale:
        logger.info(
            "Staleness-Watchdog: Kraken-OHLC-Historie waehrend laufendem Betrieb veraltet "
            "- sofortiger Nachhol-Lauf ausgeloest"
        )
        try:
            _scheduler_ref.modify_job("refresh_ohlc", next_run_time=datetime.now())
        except Exception:
            logger.exception("Staleness-Watchdog: Nachhol-Lauf fuer refresh_ohlc konnte nicht ausgeloest werden")


def build_scheduler(
    coingecko_client, kraken_client, db_conn_factory, watchlist_provider,
    groq_client=None, gemini_client=None, fred_api_key=None, bitpanda_api_key=None,
    mistral_client=None, zai_client=None,
) -> BackgroundScheduler:
    watchlist = watchlist_provider()
    scheduler = BackgroundScheduler()
    # Betriebssicherheit (2026-07-12): next_run_time=jetzt, damit Preise nach
    # einem Neustart (egal wie lange die App vorher offline war) nicht erst nach
    # einem vollen Intervall aktualisiert werden - guenstiger Einzelabruf, immer
    # sinnvoll, analog zum bitpanda_holdings-Job unten.
    #
    # BUGFIX (2026-07-19, echter Notebook-Fund - siehe Screenshot-Analyse
    # "erste Nacht mit dem letzten Release"): APScheduler's misfire_grace_time
    # ist standardmaessig nur 1 Sekunde. Der Scheduler-Aufbau selbst (mehrere
    # add_job()-Aufrufe + der synchrone Backward-Tracking-Nachhol-Check davor)
    # braucht real laenger als das - dadurch war next_run_time=jetzt bereits
    # >1s "in der Vergangenheit", sobald scheduler.start() tatsaechlich lief,
    # und ALLE sechs Sofort-Start-Jobs galten faelschlich als Misfire (inkl.
    # sofortiger "Job X fehlgeschlagen"-Alarmmail) - obwohl sie Sekunden
    # spaeter beim naechsten reguleaeren Takt ohnehin fehlerfrei liefen.
    # _IMMEDIATE_START_MISFIRE_GRACE_SECONDS gibt dem Scheduler-Start genug
    # Luft, ohne echte, mehrstuendige Standby-Ausfaelle (das eigentliche
    # Misfire-Szenario, siehe _log_job_event()-Docstring) zu verschleiern.
    scheduler.add_job(
        refresh_prices_job,
        "interval",
        minutes=REFRESH_INTERVAL_MINUTES,
        args=[coingecko_client, db_conn_factory, watchlist_provider],
        id="refresh_prices",
        next_run_time=datetime.now(),
        misfire_grace_time=_IMMEDIATE_START_MISFIRE_GRACE_SECONDS,
    )
    # Betriebssicherheit (2026-07-12): anders als bei den Preisen oben KEIN
    # bedingungsloses next_run_time=jetzt - ein voller Historie-/OHLC-Refresh ist
    # teuer (CoinGecko-Kontingent), waere sonst bei JEDEM Neustart faellig, auch
    # nach einem Absturz vor 5 Minuten. Stattdessen ein staleness-bewusster Check
    # (siehe _history_data_is_stale()/_ohlc_data_is_stale() oben): nur sofort
    # laufen, wenn die Daten tatsaechlich veraltet sind (z.B. nach laengerer
    # Downtime) - sonst wie bisher der naechste reguelaere 24-Std.-Takt.
    conn = db_conn_factory()
    try:
        history_stale = _history_data_is_stale(conn, watchlist)
        ohlc_stale = _ohlc_data_is_stale(conn, watchlist)
    finally:
        conn.close()
    if history_stale:
        logger.info("Kurs-Historie veraltet (> %d Tage) - sofortiger Refresh nach Neustart ausgeloest", staleness.HISTORY_STALE_THRESHOLD_DAYS)
    if ohlc_stale:
        logger.info("Kraken-OHLC-Historie veraltet (> %d Tage) - sofortiger Refresh nach Neustart ausgeloest", staleness.HISTORY_STALE_THRESHOLD_DAYS)
    # WICHTIG: next_run_time=None ist NICHT gleichbedeutend mit "normal aus dem
    # Trigger berechnen" - APScheduler wuerde den Job dann dauerhaft ohne
    # next_run_time anlegen und er liefe NIE mehr (live geprueft). Das kwarg muss
    # bei "nicht veraltet" deshalb komplett WEGGELASSEN werden, nicht auf None
    # gesetzt werden.
    history_job_kwargs = (
        {"next_run_time": datetime.now(), "misfire_grace_time": _IMMEDIATE_START_MISFIRE_GRACE_SECONDS}
        if history_stale else {}
    )
    scheduler.add_job(
        refresh_history_job,
        "interval",
        hours=HISTORY_REFRESH_INTERVAL_HOURS,
        args=[coingecko_client, db_conn_factory, watchlist_provider],
        id="refresh_history",
        **history_job_kwargs,
    )
    ohlc_job_kwargs = (
        {"next_run_time": datetime.now(), "misfire_grace_time": _IMMEDIATE_START_MISFIRE_GRACE_SECONDS}
        if ohlc_stale else {}
    )
    scheduler.add_job(
        refresh_ohlc_job,
        "interval",
        hours=OHLC_REFRESH_INTERVAL_HOURS,
        args=[kraken_client, db_conn_factory, watchlist_provider],
        id="refresh_ohlc",
        **ohlc_job_kwargs,
    )
    # Staleness-Watchdog (2026-07-23, siehe STALENESS_RECHECK_INTERVAL_MINUTES-
    # Kommentar oben): wiederholt denselben Check waehrend des laufenden Betriebs,
    # nicht nur einmalig beim Start wie oben. Bewusst KEIN next_run_time=jetzt -
    # der Start-Fall ist durch history_stale/ohlc_stale oben bereits abgedeckt,
    # der erste Watchdog-Tick darf reguleaer nach STALENESS_RECHECK_INTERVAL_
    # MINUTES kommen.
    scheduler.add_job(
        staleness_watchdog_job,
        "interval",
        minutes=STALENESS_RECHECK_INTERVAL_MINUTES,
        args=[db_conn_factory, watchlist_provider],
        id="staleness_watchdog",
    )
    scheduler.add_job(
        refresh_securities_prices_job,
        "interval",
        minutes=SECURITIES_REFRESH_INTERVAL_MINUTES,
        args=[YFinanceClient(), db_conn_factory, watchlist_provider],
        id="refresh_securities_prices",
        next_run_time=datetime.now(),
        misfire_grace_time=_IMMEDIATE_START_MISFIRE_GRACE_SECONDS,
    )
    # Aktien-OHLC-Refresh (2026-07-16, Asset-Verwaltungs-Audit-Fund, siehe
    # refresh_aktien_ohlc_job()-Docstring) - kein Staleness-Vorab-Check wie bei
    # refresh_ohlc oben noetig: nur eine Handvoll Aktien-Assets, yfinance-Abruf
    # ist im Gegensatz zu CoinGecko/Kraken nicht kontingentiert.
    scheduler.add_job(
        refresh_aktien_ohlc_job,
        "interval",
        hours=OHLC_REFRESH_INTERVAL_HOURS,
        args=[db_conn_factory, watchlist_provider],
        id="refresh_aktien_ohlc",
        next_run_time=datetime.now(),
        misfire_grace_time=_IMMEDIATE_START_MISFIRE_GRACE_SECONDS,
    )
    # Hebel-Screening (2026-07-14, Phase 1) - eigener 15-Min-Takt, unabhaengig vom
    # Preis-Refresh oben (andere Datenquellen: Binance/Bybit/OKX/Kraken statt
    # CoinGecko/yfinance). Aktiv-Schalter wird IM Job-Body geprueft (identisches
    # Muster wie marktscan_job()), daher immer registriert. Seit Phase 5
    # traegt derselbe Takt zusaetzlich den Budget-Allocator (alle LLM-Clients
    # + fred_api_key durchgereicht, P-8-Grundprinzip: nur Groq ist echte
    # Voraussetzung, Mistral/Gemini sind optionale Fallback-Stufen,
    # siehe hebel_screening_job()-Docstring).
    scheduler.add_job(
        hebel_screening_job,
        "interval",
        minutes=HEBEL_SCREENING_INTERVAL_MINUTES,
        args=[
            coingecko_client, kraken_client, db_conn_factory, watchlist_provider, bitpanda_api_key,
            groq_client, gemini_client, fred_api_key, mistral_client, zai_client,
        ],
        id="hebel_screening",
        next_run_time=datetime.now(),
        misfire_grace_time=_IMMEDIATE_START_MISFIRE_GRACE_SECONDS,
    )
    # Multi-Asset-Batch (2026-07-18, siehe agent/multi_asset_batch.py) - eigener,
    # deutlich selterer Takt als Krypto (der Rhythmus wird ueber config.yaml
    # multi_asset_batch.cooldown_stunden_* gesteuert, nicht ueber diesen
    # Job-Takt selbst). Seit 2026-07-20 fester Cron statt Intervall, an Bitpandas
    # Quotrix-Handelsfenster gekoppelt - siehe MULTI_ASSET_BATCH_CRON_HOURS oben.
    # Bewusst KEIN next_run_time=jetzt mehr (anders als bei den Krypto-Jobs) - ein
    # sofortiger Lauf direkt nach Neustart koennte ausserhalb der Handelszeiten
    # liegen, genau das Problem, das dieser Fix beheben soll.
    scheduler.add_job(
        multi_asset_batch_job,
        "cron",
        hour=MULTI_ASSET_BATCH_CRON_HOURS,
        minute=0,
        day_of_week="mon-fri",
        args=[db_conn_factory, watchlist_provider, coingecko_client, groq_client, gemini_client, mistral_client],
        id="multi_asset_batch",
    )
    # MS-3: erster CronTrigger im Projekt (bisherige Jobs nutzen nur "interval") -
    # feste Uhrzeiten statt Intervall, siehe config.yaml marktscan.zeiten.
    scheduler.add_job(
        marktscan_job,
        "cron",
        hour="4,16",
        minute=0,
        args=[coingecko_client, kraken_client, db_conn_factory, watchlist_provider, fred_api_key],
        id="marktscan",
    )
    # Batch-Signal-Berechnung (2026-07-13): fixer 05:00-Cron entfernt (2026-07-14,
    # Phase 5) - der Budget-Allocator uebernimmt Spot-Rotation jetzt im 15-Min-Takt
    # mit (siehe hebel_screening_job()). agent/krypto/signal_batch.py::
    # run_signal_batch() bleibt bestehen, nur noch fuer den manuellen UI-Button
    # (ui/signals_view.py, Nutzer-Entscheidung) genutzt.
    # Backward-Tracking (2026-07-10): taeglich, kein eigener API-Call noetig (reine
    # Auswertung bereits vorhandener Kursdaten) - feste Uhrzeit nach dem ueblichen
    # naechtlichen Refresh-Fenster, keine harte Abhaengigkeit (holt am naechsten Tag
    # nach, falls refresh_history/refresh_ohlc an dem Tag noch nicht durch waren).
    scheduler.add_job(
        backward_tracking_job,
        "cron",
        hour=6,
        minute=0,
        args=[db_conn_factory, watchlist_provider],
        id="backward_tracking",
    )
    # Makro-Analog-Vergleich (2026-07-18) - taeglich, gestaffelt nach Backward-
    # Tracking (kein harter Grund, nur um nicht beide teureren Jobs exakt
    # gleichzeitig zu starten). next_run_time=jetzt: bootstrapt die Historie
    # sofort nach dem ersten Start dieses Features, statt bis zu 24 Std. auf den
    # ersten Cron-Takt zu warten (gleiches Muster wie refresh_prices/
    # hebel_screening oben).
    scheduler.add_job(
        makro_analog_job,
        "cron",
        hour=6,
        minute=30,
        args=[db_conn_factory, fred_api_key],
        id="makro_analog",
        next_run_time=datetime.now(),
        misfire_grace_time=_IMMEDIATE_START_MISFIRE_GRACE_SECONDS,
    )
    # 2026-07-17, Nutzer-Fund: ein fester Cron holt einen verpassten Termin NICHT
    # automatisch nach, wenn die App zu diesem Zeitpunkt gar nicht lief - an zwei
    # Tagen in Folge passiert (07-15/07-16), zwei Tage lang keine einzige
    # Backward-Tracking-Auswertung trotz laengst reifer Hebel-Positionen. Direkter
    # synchroner Nachhol-Check beim Start (kein Netzwerk-Call, siehe Docstring
    # dort) - No-Op, falls der heutige Lauf schon glückte.
    backward_tracking_catchup_if_missed(db_conn_factory, watchlist)
    # Automatischer VOLLER Bestandsabgleich (2026-07-11 als reiner Cash-Sync
    # eingefuehrt, 2026-07-16 auf den kompletten Bestandsabgleich erweitert, siehe
    # refresh_bitpanda_holdings_job()-Docstring) - P-8: nur registriert, wenn ein
    # BITPANDA_API_KEY vorhanden ist, sonst bleibt RM-4/Portfolio wie bisher auf
    # den manuellen Sync angewiesen. next_run_time=jetzt verkuerzt das Stale-
    # Fenster direkt nach dem App-Start, statt bis zu
    # BITPANDA_HOLDINGS_REFRESH_INTERVAL_MINUTES zu warten.
    if bitpanda_api_key:
        scheduler.add_job(
            refresh_bitpanda_holdings_job,
            "interval",
            minutes=BITPANDA_HOLDINGS_REFRESH_INTERVAL_MINUTES,
            args=[bitpanda_api_key, db_conn_factory],
            id="bitpanda_holdings",
            next_run_time=datetime.now(),
            misfire_grace_time=_IMMEDIATE_START_MISFIRE_GRACE_SECONDS,
        )
    else:
        logger.info("Kein BITPANDA_API_KEY - automatischer Bestandsabgleich deaktiviert (P-8)")
    scheduler.add_listener(_log_job_event, EVENT_JOB_ERROR | EVENT_JOB_MISSED)

    global _scheduler_ref
    _scheduler_ref = scheduler
    return scheduler
