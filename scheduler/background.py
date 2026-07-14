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
bitpanda_cash_lock = threading.Lock()
# Batch-Signal-Berechnung (2026-07-13) - geteilt zwischen dem taeglichen
# Scheduler-Job (Wochen-Sicherheitsnetz) UND dem manuellen UI-Button
# (ui/signals_view.py), verhindert einen gleichzeitigen Doppel-Lauf egal
# wodurch ausgeloest.
signal_batch_lock = threading.Lock()
# Hebel-Screening (2026-07-14, Phase 1, siehe docs/hebel_positionsformel.md) -
# rein deterministisches Scoring, kein Groq-Aufruf, daher (noch) kein zweiter
# Ausloeser wie bei signal_batch_lock - Lock existiert trotzdem, falls spaeter
# ein manueller "Jetzt screenen"-Button dazukommt (gleiches Muster).
hebel_screening_lock = threading.Lock()
_JOB_LOCKS = {
    "refresh_prices": refresh_prices_lock,
    "refresh_securities": refresh_securities_lock,
    "marktscan": marktscan_lock,
    "bitpanda_cash": bitpanda_cash_lock,
    "signal_batch": signal_batch_lock,
    "hebel_screening": hebel_screening_lock,
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
BITPANDA_CASH_REFRESH_INTERVAL_MINUTES = 30  # 2026-07-11: seltener als der Preis-Takt
# (15 Min) - authentifizierter Call, Fiat-Cash aendert sich normalerweise seltener als
# Marktpreise. Nur der Fiat-Cash-Anteil, NICHT die vollen Bestaende (die haben einen
# interaktiven Rueckgangs-Bestaetigungsdialog, siehe importer/bitpanda_sync.py::
# sync_fiat_cash_from_bitpanda()-Docstring).
HEBEL_SCREENING_INTERVAL_MINUTES = 15  # muss mit config.yaml hebel_screening.
# intervall_minuten uebereinstimmen (wie bei allen anderen Jobs ist die Taktung selbst
# ein Python-Konstante, nur der aktiv-Schalter wird dynamisch aus config.yaml gelesen,
# siehe hebel_screening_job()) - kalibriert auf die reale Ø-Haltedauer echter
# Hebel-Positionen (1,1 Tage), siehe docs/hebel_positionsformel.md.

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
    "bitpanda_cash": BITPANDA_CASH_REFRESH_INTERVAL_MINUTES,
}
_BACKOFF_MAX_MINUTES = 240  # Deckel 4 Std. - auch bei einem sehr langen Ausfall soll die
# App nach spaetestens 4 Std. wieder einen Versuch starten, statt den Job faktisch
# stillzulegen.


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
    except Exception as exc:
        logger.exception("Historie-Refresh fehlgeschlagen")
        _notify_job_failure("refresh_history", f"Historie-Refresh fehlgeschlagen: {exc}")
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
    except Exception as exc:
        logger.exception("Kraken-OHLC-Refresh fehlgeschlagen")
        _notify_job_failure("refresh_ohlc", f"Kraken-OHLC-Refresh fehlgeschlagen: {exc}")
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
    except Exception as exc:
        logger.exception("Backward-Tracking fehlgeschlagen")
        _notify_job_failure("backward_tracking", f"Backward-Tracking fehlgeschlagen: {exc}")
    finally:
        conn.close()


def refresh_bitpanda_cash_job(api_key, conn_factory) -> bool:
    """Automatischer Fiat-Cash-Sync (2026-07-11) - haelt agent/krypto/risk_gate.py's
    RM-4-Cash-Reserve-Pruefung aktuell, ohne auf den manuellen "Bestaende von Bitpanda
    abgleichen"-Klick angewiesen zu sein. Nur der Fiat-Cash-Anteil (siehe
    importer/bitpanda_sync.py::sync_fiat_cash_from_bitpanda()-Docstring, warum die
    vollen Bestaende bewusst NICHT automatisch mitlaufen). Rueckgabewert wie
    refresh_prices_job() (Lock-Status)."""
    if not bitpanda_cash_lock.acquire(blocking=False):
        logger.info("Bitpanda-Cash-Sync: bereits in Ausführung - übersprungen")
        return False
    _job_started_at["bitpanda_cash"] = time.monotonic()
    conn = conn_factory()
    try:
        from importer.bitpanda_sync import sync_fiat_cash_from_bitpanda

        result = sync_fiat_cash_from_bitpanda(conn, api_key)
        if result.updated:
            logger.info("Bitpanda-Cash-Sync: %.2f -> %.2f EUR", result.old_eur, result.new_eur)
        else:
            logger.info("Bitpanda-Cash-Sync: unverändert")
        _record_job_success_for_backoff("bitpanda_cash")
    except Exception as exc:
        logger.exception("Bitpanda-Cash-Sync fehlgeschlagen")
        _notify_job_failure("bitpanda_cash", f"Bitpanda-Cash-Sync fehlgeschlagen: {exc}")
        _record_job_failure_for_backoff("bitpanda_cash")
    finally:
        conn.close()
        bitpanda_cash_lock.release()
        _job_started_at.pop("bitpanda_cash", None)
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


def _notify_signal_batch_ergebnis(berechnet: list, verbleibend_ueberfaellig: int) -> None:
    """Batch-Signal-Berechnung (2026-07-13) - analog zu
    _notify_marktscan_kaufkandidaten(): eigener try/except (P-10, ein
    Mail-Fehler darf den Batch-Lauf nicht nachtraeglich als 'fehlgeschlagen'
    erscheinen lassen), nur bei mind. einem AKTIONABLEN Ergebnis (nicht
    HALTEN) - ein reiner HALTEN-Batch ist kein Grund fuer eine taegliche
    E-Mail (matcht das 'kein Cooldown, aber nur bei echtem Anlass'-Prinzip
    von Marktscan, nur andersherum: dort kein Cooldown noetig weil selten,
    hier waere taeglich HALTEN-Spam sonst der Normalfall)."""
    aktionabel = [s for s in berechnet if s.action != "HALTEN"]
    if not aktionabel:
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
        if not config_dict.get("signale_batch", {}).get("benachrichtigung_email", True):
            return

        zeilen = [
            f"- {s.symbol}: {s.action} (Konfidenz {s.confidence_pct:.0f}%): {s.short_reasoning}"
            for s in aktionabel
        ]
        body = (
            f"{len(berechnet)} Signal(e) automatisch berechnet, davon {len(aktionabel)} "
            f"nicht HALTEN:\n\n" + "\n".join(zeilen)
            + f"\n\n{verbleibend_ueberfaellig} Asset(s) sind aktuell länger als "
            "7 Tage ohne echte Analyse (werden in den nächsten Läufen priorisiert)."
            "\n\nDetails im Signale-Tab der App."
        )
        send_notification_email(
            f"TradingInfoTool: {len(aktionabel)} neue Signal-Empfehlung(en)",
            body,
            empfaenger,
        )
    except Exception:
        logger.exception("Signal-Batch-E-Mail fehlgeschlagen")


def signal_batch_job(coingecko_client, kraken_client, groq_client, conn_factory, watchlist, fred_api_key) -> bool:
    """Wochen-Sicherheitsnetz fuer die Batch-Signal-Berechnung (2026-07-13,
    siehe agent/krypto/signal_batch.py Modul-Docstring fuer die volle
    Token-Budget-Herleitung). Taeglich (siehe build_scheduler()), respektiert
    dasselbe geteilte Tagesbudget wie der manuelle UI-Button - `run_signal_batch()`
    prueft selbst, wie viele echte Analysen heute schon (ueber IRGENDEINEN
    Ausloeser) gelaufen sind. `groq_client` kann None sein (P-8) - dann
    schlaegt jeder generate_signal()-Aufruf beim eigentlichen Groq-Call fehl,
    wird aber pro Asset einzeln abgefangen (siehe run_signal_batch())."""
    if not signal_batch_lock.acquire(blocking=False):
        logger.info("Signal-Batch: bereits in Ausführung - übersprungen")
        return False
    _job_started_at["signal_batch"] = time.monotonic()
    try:
        import config as config_module
        from agent.krypto.signal_batch import run_signal_batch

        config_dict = config_module.load_config()
        batch_cfg = config_dict.get("signale_batch", {})
        if not batch_cfg.get("aktiv", True):
            logger.info("Signal-Batch deaktiviert (config.yaml signale_batch.aktiv=false) - übersprungen")
            return True

        result = run_signal_batch(
            conn_factory, watchlist, groq_client, coingecko_client, kraken_client, fred_api_key,
            daily_budget=batch_cfg.get("taegliches_budget", 15),
        )
        logger.info(
            "Signal-Batch: %d berechnet, %d fehlgeschlagen, %d weiterhin >7 Tage überfällig, Budget erschöpft: %s",
            len(result.berechnet), len(result.fehlgeschlagen), result.verbleibend_ueberfaellig,
            result.budget_erschoepft,
        )
        _notify_signal_batch_ergebnis(result.berechnet, result.verbleibend_ueberfaellig)
    except Exception as exc:
        logger.exception("Signal-Batch fehlgeschlagen")
        _notify_job_failure("signal_batch", f"Signal-Batch fehlgeschlagen: {exc}")
    finally:
        signal_batch_lock.release()
        _job_started_at.pop("signal_batch", None)
    return True


def _refresh_hebel_position_liquidation_prices(conn) -> None:
    """Fuer jede aktuell offene Margin-Position den geschaetzten Liquidationspreis
    mit den ECHTEN verstrichenen Tagen neu berechnen (2026-07-14, Phase 3) -
    entry_preis_eur wird aus positionswert_eur/positionsmenge abgeleitet (kein
    separat gespeicherter Einstandspreis noetig, siehe database/models.py::
    HebelPosition-Docstring). Ohne positionsmenge (z.B. sehr alte/unvollstaendige
    Datensaetze) wird die Position uebersprungen statt eine falsche Schaetzung
    zu zeigen (P-10)."""
    from agent.krypto.hebel_risk_gate import estimate_liquidation_price

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
        )
        pos.liquidationspreis_berechnet_am = datetime.now(timezone.utc).isoformat()
        db.upsert_hebel_position(conn, pos)


def hebel_screening_job(coingecko_client, kraken_client, conn_factory, watchlist, bitpanda_api_key=None) -> bool:
    """Hebel-Screening (2026-07-14, Phase 1, siehe docs/hebel_positionsformel.md)
    - rein deterministisches Zwei-Zweige-Scoring, KEIN Groq-Aufruf. Ergebnis
    landet in hebel_triggers, ein kuenftiger Budget-Allocator (spaetere Phase)
    entscheidet, welche Kandidaten eine echte LLM-Empfehlung bekommen - das ist
    NICHT Teil dieses Jobs.

    Seit Phase 3 (Positions-Rekonstruktion) huckepack im selben 15-Min-Takt:
    Bitpanda-Margin-Positions-Sync + Liquidationspreis-Neuberechnung fuer
    offene Positionen (P-8: nur falls bitpanda_api_key gesetzt ist, sonst
    stillschweigend uebersprungen - kein Fehler)."""
    if not hebel_screening_lock.acquire(blocking=False):
        logger.info("Hebel-Screening: bereits in Ausführung - übersprungen")
        return False
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

        if bitpanda_api_key:
            from importer.bitpanda_margin_positions import sync_hebel_positions

            conn = conn_factory()
            try:
                sync_result = sync_hebel_positions(conn, bitpanda_api_key)
                logger.info(
                    "Hebel-Positions-Sync: %d Transaktionen geladen, %d Positionen aktualisiert, %d neu geschlossen",
                    sync_result.total_transactions_fetched, len(sync_result.positionen_aktualisiert),
                    sync_result.neu_geschlossen,
                )
                _refresh_hebel_position_liquidation_prices(conn)
            finally:
                conn.close()
    except Exception as exc:
        logger.exception("Hebel-Screening fehlgeschlagen")
        _notify_job_failure("hebel_screening", f"Hebel-Screening fehlgeschlagen: {exc}")
    finally:
        hebel_screening_lock.release()
        _job_started_at.pop("hebel_screening", None)
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


def build_scheduler(
    coingecko_client, kraken_client, db_conn_factory, watchlist_provider,
    groq_client=None, fred_api_key=None, bitpanda_api_key=None,
) -> BackgroundScheduler:
    watchlist = watchlist_provider()
    scheduler = BackgroundScheduler()
    # Betriebssicherheit (2026-07-12): next_run_time=jetzt, damit Preise nach
    # einem Neustart (egal wie lange die App vorher offline war) nicht erst nach
    # einem vollen Intervall aktualisiert werden - guenstiger Einzelabruf, immer
    # sinnvoll, analog zum bitpanda_cash-Job unten.
    scheduler.add_job(
        refresh_prices_job,
        "interval",
        minutes=REFRESH_INTERVAL_MINUTES,
        args=[coingecko_client, db_conn_factory, watchlist],
        id="refresh_prices",
        next_run_time=datetime.now(),
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
    history_job_kwargs = {"next_run_time": datetime.now()} if history_stale else {}
    scheduler.add_job(
        refresh_history_job,
        "interval",
        hours=HISTORY_REFRESH_INTERVAL_HOURS,
        args=[coingecko_client, db_conn_factory, watchlist],
        id="refresh_history",
        **history_job_kwargs,
    )
    ohlc_job_kwargs = {"next_run_time": datetime.now()} if ohlc_stale else {}
    scheduler.add_job(
        refresh_ohlc_job,
        "interval",
        hours=OHLC_REFRESH_INTERVAL_HOURS,
        args=[kraken_client, db_conn_factory, watchlist],
        id="refresh_ohlc",
        **ohlc_job_kwargs,
    )
    scheduler.add_job(
        refresh_securities_prices_job,
        "interval",
        minutes=SECURITIES_REFRESH_INTERVAL_MINUTES,
        args=[YFinanceClient(), db_conn_factory, watchlist],
        id="refresh_securities_prices",
        next_run_time=datetime.now(),
    )
    # Hebel-Screening (2026-07-14, Phase 1) - eigener 15-Min-Takt, unabhaengig vom
    # Preis-Refresh oben (andere Datenquellen: Binance/Bybit/OKX/Kraken statt
    # CoinGecko/yfinance). Aktiv-Schalter wird IM Job-Body geprueft (identisches
    # Muster wie marktscan_job()/signal_batch_job()), daher immer registriert.
    scheduler.add_job(
        hebel_screening_job,
        "interval",
        minutes=HEBEL_SCREENING_INTERVAL_MINUTES,
        args=[coingecko_client, kraken_client, db_conn_factory, watchlist, bitpanda_api_key],
        id="hebel_screening",
        next_run_time=datetime.now(),
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
    # Batch-Signal-Berechnung (2026-07-13) - Luecke zwischen Marktscan (4/16 Uhr)
    # und Backward-Tracking (6 Uhr). Immer registriert, der Aktiv-Schalter wird
    # IM Job-Body geprueft (identisches Muster wie marktscan_job() oben), nicht
    # bei der Registrierung.
    scheduler.add_job(
        signal_batch_job,
        "cron",
        hour=5,
        minute=0,
        args=[coingecko_client, kraken_client, groq_client, db_conn_factory, watchlist, fred_api_key],
        id="signal_batch",
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
    # Automatischer Fiat-Cash-Sync (2026-07-11) - P-8: nur registriert, wenn ein
    # BITPANDA_API_KEY vorhanden ist, sonst bleibt RM-4 wie bisher auf den manuellen
    # Sync angewiesen. next_run_time=jetzt verkuerzt das Stale-Fenster direkt nach dem
    # App-Start, statt bis zu BITPANDA_CASH_REFRESH_INTERVAL_MINUTES zu warten.
    if bitpanda_api_key:
        scheduler.add_job(
            refresh_bitpanda_cash_job,
            "interval",
            minutes=BITPANDA_CASH_REFRESH_INTERVAL_MINUTES,
            args=[bitpanda_api_key, db_conn_factory],
            id="bitpanda_cash",
            next_run_time=datetime.now(),
        )
    else:
        logger.info("Kein BITPANDA_API_KEY - automatischer Cash-Sync deaktiviert (P-8)")
    scheduler.add_listener(_log_job_event, EVENT_JOB_ERROR | EVENT_JOB_MISSED)

    global _scheduler_ref
    _scheduler_ref = scheduler
    return scheduler
