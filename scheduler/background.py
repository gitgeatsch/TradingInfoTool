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
COINGECKO_QUOTA_CHECK_INTERVAL_MINUTES = 60  # 2026-07-31, echte CoinGecko-80%-
# Warnmail ausgeloest (siehe Memory project_bug_runde_31_07_notebook_export) -
# reiner Lese-Check (siehe coingecko_quota_check_job() unten), der Zaehler
# selbst aendert sich pro Call in api/coingecko.py::CoinGeckoClient.
# _track_quota() - stuendlich reicht voellig, das Kontingent aendert sich
# langsam ueber Stunden/Tage, kein Grund fuer einen engeren Takt.
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
_STARTUP_STAGGER_SECONDS = 5  # siehe _staggered_start()-Docstring (2026-07-31)


def _staggered_start(index: int) -> datetime:
    """Verteilt die Sofort-Start-Jobs auf ein paar Sekunden Abstand statt alle
    exakt gleichzeitig zu starten (2026-07-31, Bug-Runde-Fund, siehe Memory
    project_bug_runde_31_07_notebook_export): mehrere Jobs trafen bei jedem
    Neustart gleichzeitig auf yfinance (refresh_securities_prices +
    refresh_aktien_ohlc) bzw. schrieben gleichzeitig in die SQLite-DB (ein
    "database is locked" bei hebel_screening beobachtet, 24s nach einem
    Neustart). Aendert NUR den Startzeitpunkt, nicht die Job-Logik selbst -
    jeder Job hat bereits sein eigenes Lock gegen Doppelausfuehrung (siehe
    Lock-Definitionen oben), die Staffelung interagiert damit nicht.
    index=0 startet weiterhin sofort (identisches Verhalten wie vor dieser
    Aenderung fuer den ersten Job)."""
    return datetime.now() + timedelta(seconds=index * _STARTUP_STAGGER_SECONDS)
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


def refresh_ohlc_job(client, conn_factory, watchlist_provider,
                     coingecko_client=None) -> None:
    """`watchlist_provider` siehe refresh_prices_job()-Docstring (2026-07-23).

    DIE LUECKE, die eine zweite Quelle noetig macht: Krypto-Assets ohne
    Kraken-Listing bekamen GAR KEINE Kerzen - stillschweigend, weil
    backfill_ohlc() sie als "kein Kraken-Listing" ueberspringt. Betroffen waren
    elf Symbole, darunter KAIA mit 17,2 % aller Hebel-Screening-Kandidaten.

    RUECKFALL SEIT 12.08.: BOERSEN-KLINES (`api/boersen_klines.py`). Er laeuft
    NACH Kraken und ruehrt nur Symbole ohne Kraken-Paar an.

    Der Parameter `coingecko_client` wird NICHT MEHR VERWENDET. Er steht noch in
    der Signatur, damit bestehende Aufrufer nicht brechen; der Job ignoriert
    ihn. Wer ihn entfernt, muss `build_scheduler()` mit anfassen.

    Beide Vorgaenger waren die schlechtere Wahl. CoinGecko liefert ueber /ohlc
    GAR KEINE Tageskerzen (gemessen: Vier-Tage-Abstand, abgelegt neben Krakens
    Tageskerzen ohne Vermerk). yfinance liefert Tageskerzen, aber ueber einen
    GERATENEN Ticker `<SYM>-USD` - drei von acht gehoerten einem anderen, toten
    Asset.

    `api/boersen_klines.py` fragt Binance und Bybit nach IHREM eigenen Paar.
    Deckung 41 von 42 statt 39, Median-Abstand geprueft 1 Tag, 1.000 Kerzen je
    Abruf, dieselbe API wie fuer Funding und Open Interest - und keine
    Ticker-Gegenprobe noetig, weil keine Verwechslung moeglich ist.

    DAMIT GILT DIE RANGFOLGE:  Kraken -> Binance/Bybit.
    Genau EINE Quelle je Symbol."""
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
    else:
        # Bewusst im else-Zweig und mit eigenem try: ein Fehler in der
        # Rueckfallquelle darf den erfolgreichen Kraken-Lauf nicht als
        # fehlgeschlagen melden.
        # RUECKFALL: Boersen-Klines. Ersetzt CoinGecko (liefert keine
        # Tageskerzen) und yfinance (geratener Ticker, drei von acht falsch).
        # Beide Module bleiben im Repo, sind aber nicht mehr verdrahtet - ihre
        # Docstrings halten fest, WARUM sie ungeeignet sind.
        try:
            from api.boersen_klines import fuelle_luecken

            rf = fuelle_luecken(conn, watchlist, trocken=False)
            bedient = [z for z in rf if z["kerzen"] > 0]
            if rf:
                logger.info(
                    "Boersen-Klines-Rueckfall: %d/%d Symbole befuellt, "
                    "%d Kerzen (Symbole ohne Kraken-Listing)",
                    len(bedient), len(rf), sum(z["kerzen"] for z in rf))
                for z in rf:
                    if not z["kerzen"]:
                        logger.info("  %s: an keiner Boerse gelistet",
                                    z["symbol"])
        except Exception as exc:
            logger.exception("Boersen-Klines-Rueckfall fehlgeschlagen")
            _notify_job_failure(
                "refresh_ohlc_fallback",
                f"Boersen-Klines-Rueckfall fehlgeschlagen: {exc}")
    finally:
        conn.close()


def _refresh_nicht_aktien_ohlc(conn, watchlist) -> None:
    """Kursreihen der uebrigen Nicht-Krypto-Klassen taeglich mitziehen (2026-08-06).

    WARUM DAS FEHLTE. backfill_all_aktien_ohlc() filtert auf
    assetklasse == "aktien". Fuer Rohstoffe, Themen-ETF und Hedge entstand eine
    Reihe deshalb nur, wenn die jeweilige PIPELINE lief - und die laeuft im
    Multi-Asset-Batch um 9 und 19 Uhr, Mo-Fr. Der Portfolio-Wert-Job laeuft um
    6:30, TAEGLICH. Damit haengt die Bewertung dieser Positionen daran, ob am
    Vortag ein Signal erzeugt wurde; am Wochenende gar nicht.

    Mit der Rekonstruktion (2026-08-06) wiegt das schwerer als vorher: die
    rekonstruierte Reihe haengt an einem Ankerpreis, der sich taeglich bewegt.
    Ohne eigenen Refresh waere sie am Montagmorgen drei Tage alt verankert.

    Aufgerufen wird bewusst die PIPELINE-eigene Funktion je Klasse, nicht eine
    Kopie davon - Staleness-Wache, Symboltrennung und Rekonstruktion sind dort
    schon richtig entschieden, und zwei Implementierungen derselben Logik laufen
    garantiert auseinander (Lehre vom 03.08.).

    Fail-soft je Asset: ein Fehlschlag darf die uebrigen nicht mitreissen.
    """
    # ASSETKLASSE REICHT NICHT ZUR AUSWAHL - und genau daran ist der erste
    # Entwurf gescheitert (06.08., im Betriebslog: "4 Assets aktualisiert",
    # erwartet waren 11). Die Watchlist kennt nur `aktien`, `rohstoffe`,
    # `krypto` und `etf`. Es gibt KEINE Assetklasse "hedge" und keine
    # "themen_etf": Hedge-Instrumente werden ueber die Mitgliedschaft in
    # SYMBOL_ZU_HEBEL_FAKTOR erkannt, Themen-ETFs sind die uebrigen `etf`.
    # Der erste Entwurf filterte auf Klassennamen, die es nicht gibt - er hat
    # deshalb nur die Rohstoffe erwischt, und die 3QSS-Rekonstruktion lief nie.
    #
    # DIE AUSWAHLREGEL WIRD DESHALB NICHT NOCHMAL FORMULIERT, sondern aus
    # agent/multi_asset_batch.py uebernommen: _kandidaten() bestimmt, welche
    # Assets eine Nicht-Krypto-Pipeline haben, _pipeline_fuer() ordnet die
    # Pipeline zu. Eine zweite Fassung derselben Regel waere genau die Dublette,
    # die am 03.08. schon einmal auseinandergelaufen ist.
    from agent.hedge.pipeline import (
        ist_hedge_instrument, _ensure_ohlc_backfilled as _hedge_ohlc,
    )
    from agent.multi_asset_batch import _kandidaten
    from agent.rohstoff.pipeline import _ensure_ohlc_backfilled as _rohstoff_ohlc
    from agent.themen_etf.pipeline import (
        _ensure_ohlc_backfilled as _etf_ohlc, _resolve_asset_currency as _etf_currency,
    )

    erledigt, fehlgeschlagen = 0, 0
    je_art: dict[str, int] = {}
    for asset in _kandidaten(watchlist):
        if asset.assetklasse == "aktien":
            continue                      # deckt backfill_all_aktien_ohlc() ab
        try:
            if asset.assetklasse == "rohstoffe":
                _rohstoff_ohlc(conn, asset)
                art = "rohstoffe"
            elif ist_hedge_instrument(asset):
                _hedge_ohlc(conn, asset)
                art = "hedge"
            elif asset.assetklasse == "etf":
                _etf_ohlc(conn, asset, _etf_currency(asset))
                art = "themen_etf"
            else:
                continue
            erledigt += 1
            je_art[art] = je_art.get(art, 0) + 1
        except Exception:
            fehlgeschlagen += 1
            logger.exception("OHLC-Refresh fuer %s fehlgeschlagen", asset.symbol)
    # Aufschluesselung je Art mitloggen: "4 Assets aktualisiert" sah unauffaellig
    # aus, obwohl zwei Arten komplett fehlten. Eine Summe verbirgt genau das.
    logger.info("Nicht-Aktien-OHLC-Refresh: %d Assets aktualisiert (%d fehlgeschlagen) - %s",
                erledigt, fehlgeschlagen,
                ", ".join(f"{k}: {v}" for k, v in sorted(je_art.items())) or "keine")


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
        _refresh_nicht_aktien_ohlc(conn, watchlist)
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

        # Mail 2 (2026-07-30, Watchlist-"heiss"): GENAU beim Uebergang zu
        # sichtung_position==3 (nicht bei jeder weiteren Sichtung) UND nur, wenn
        # die 3 Sichtungen ungewoehnlich schnell aufeinander folgten (Nutzer-
        # bestaetigtes Fenster, ~2x Median 24h, n=172 - siehe config.yaml
        # marktscan.erfolgsmessung.watchlist_heiss_fenster_stunden).
        import json as json_module

        fenster_stunden = config_dict["marktscan"]["erfolgsmessung"]["watchlist_heiss_fenster_stunden"]
        watchlist_heiss = []
        for c in candidates:
            if c.einstufung != "watchlist_wuerdig":
                continue
            try:
                signale = json_module.loads(c.signale_momentum_json or "{}")
            except (TypeError, ValueError):
                signale = {}
            if signale.get("sichtung_position") != 3:
                continue
            zeitspanne = db.get_marktscan_sichtungs_zeitspanne_bis_n(conn, c.coingecko_id, n=3)
            if zeitspanne is not None and zeitspanne <= fenster_stunden:
                watchlist_heiss.append(c)
        _notify_marktscan_watchlist_heiss(watchlist_heiss)
    except Exception as exc:
        logger.exception("Marktscan fehlgeschlagen")
        _notify_job_failure("marktscan", f"Marktscan fehlgeschlagen: {exc}")
    finally:
        conn.close()
        marktscan_lock.release()
        _job_started_at.pop("marktscan", None)
    return True


def ausstiegs_job(conn_factory, watchlist_provider) -> None:
    """Taegliche Ausstiegs-Empfehlungen (2026-08-05, Punkt 3 scharfgeschaltet).

    DER BEFUND DAHINTER: 50 % der Signale standen einmal bei +1R, aber nur
    17,6 % kamen am Ziel an. Positionen geben Gewinne regelmaessig zurueck -
    der groesste gemessene Hebel des Systems.

    GEBAUT WAR DIE REGEL SEIT DEM 04.08., aber nur PASSIV: sie rechnete im
    Export und auf der Remote-Seite. Beides muss man aufrufen. Beim Export vom
    05.08. standen 15 von 28 offenen Signalen ueber der Schwelle, darunter SOL
    mit 10,63 R ungesichertem Buchgewinn - gesehen wurde das nur, weil zufaellig
    jemand hineinschaute. Dieser Job macht daraus eine Bringschuld.

    EINE MAIL PRO TAG, HOECHSTENS. Bewusst ein Sammel-Ueberblick statt einer
    Mail je Signal: bei 15 offenen Empfehlungen waeren 15 Mails Rauschen, und
    Rauschen wird ignoriert - dann waere nichts gewonnen. Sortiert nach
    ungesichertem Buchgewinn, damit die dringendste Zeile oben steht.

    KEINE MAIL, WENN NICHTS ANLIEGT. Eine taegliche "nichts zu tun"-Mail
    erzieht dazu, die Mail nicht mehr zu oeffnen.

    ADVISORY-ONLY (P-7): der Job rechnet und meldet. Er aendert keine Position,
    setzt keinen Stop und ruft keine Handels-API auf - es gibt keine.

    Abschaltbar ueber config.yaml risiko.ausstieg_trailing_ausloese_r = 0,
    ohne Codeaenderung. Der Grund steht dort: alle Kalibrierungszahlen stammen
    aus EINER Marktphase."""
    import config as config_module
    from agent.krypto.ausstiegsregel import parameter_aus_config
    from agent.krypto.backward_tracking import compute_ausstiegs_empfehlungen

    cfg = config_module.load_config()
    # DEN LAUF VERMERKEN, UND ZWAR BEI JEDEM AUSGANG (16.08.2026).
    #
    # Der Nachholer in `build_scheduler()` fragt "lief er heute schon?". Wuerde
    # nur der Erfolgsfall vermerkt, holte er bei jedem Neustart erneut nach -
    # bei elf Neustalten am Tag waeren das elf Mails. Der Job hatte seine
    # Gelegenheit, auch wenn er nichts zu melden fand.
    _c0 = conn_factory()
    try:
        db.merke_joblauf(_c0, "ausstiegs_empfehlungen")
    finally:
        _c0.close()

    _ausloese, _abstand, aktiv = parameter_aus_config(cfg)
    if not aktiv:
        logger.info("Ausstiegsregel deaktiviert (ausstieg_trailing_ausloese_r <= 0)")
        return

    conn = conn_factory()
    try:
        ergebnis = compute_ausstiegs_empfehlungen(conn, watchlist_provider(), cfg)
    except Exception:
        logger.exception("Ausstiegs-Empfehlungen fehlgeschlagen")
        return
    finally:
        conn.close()

    empfehlungen = (ergebnis or {}).get("empfehlungen") or []
    geprueft = (ergebnis or {}).get("geprueft")
    if not empfehlungen:
        logger.info("Ausstiegsregel: keine Empfehlung offen (%s Signale geprueft)", geprueft)
        return

    logger.info("Ausstiegsregel: %d von %s offenen Signalen ueber der Schwelle",
                len(empfehlungen), geprueft)
    try:
        _sende_ausstiegs_email(empfehlungen, geprueft)
    except Exception:
        logger.exception("Ausstiegs-E-Mail fehlgeschlagen")


def _sende_ausstiegs_email(empfehlungen: list, geprueft) -> None:
    """Sammel-Mail der offenen Stop-Nachzieh-Empfehlungen.

    Der Leer-Guard steht ABSICHTLICH hier und nicht nur im Aufrufer: eine
    "0 Empfehlungen"-Mail erzieht dazu, die Mail nicht mehr zu oeffnen - und
    dann ist auch die eine wichtige nichts mehr wert. Beim Test fiel auf, dass
    ein Direktaufruf diese Mail sonst verschickt haette.

    KEIN RICHTUNGS-FILTER, UND ZWAR BEWUSST (bestaetigt 2026-08-06, nachdem der
    erste Lauf SHORT-Empfehlungen enthielt). `_ist_email_relevante_richtung()`
    gilt nur fuer SIGNAL-Mails, also fuer Vorschlaege, ETWAS NEUES ZU
    EROEFFNEN - dort blendet der BP-Schalter SHORT aus, weil es nicht
    ausfuehrbar waere. Diese Mail betrifft dagegen BEREITS OFFENE Positionen.
    Eine offene SHORT-Position muss gemanagt werden, egal wie der Schalter
    steht; sie zu verschweigen hiesse, den Nutzer genau ueber den Teil seines
    Portfolios im Dunkeln zu lassen, der gerade Gewinn absichern koennte (beim
    ersten Lauf: SOL SHORT mit 10,63 R). Der Schalter regelt, was NEU
    vorgeschlagen wird - nicht, was bereits laeuft."""
    import config as config_module
    from api.email_notify import send_notification_email

    if not empfehlungen:
        return

    email_cfg = config_module.load_config().get("benachrichtigung", {}).get("email", {})
    if not email_cfg.get("aktiv", False):
        return
    empfaenger = email_cfg.get("empfaenger")
    if not empfaenger:
        return

    zeilen = [
        f"{len(empfehlungen)} von {geprueft} offenen Signalen haben ihren "
        f"Buchgewinn nicht abgesichert.",
        "",
        "Sortiert nach hoechstem erreichten Buchgewinn. Die Regel ist eine "
        "EMPFEHLUNG - sie fuehrt nichts aus.",
        "",
    ]
    for e in empfehlungen:
        stop = e.get("stop_empfohlen")
        zeilen.append(
            f"{e.get('symbol'):<10} {e.get('richtung','?'):<5} "
            f"({e.get('tier','?')}, seit {e.get('seit','?')})"
        )
        zeilen.append(
            f"    stand bei {e.get('mfe_r')} R - Stop von {e.get('stop_bisher')} "
            f"auf {round(stop, 8) if isinstance(stop, (int, float)) else stop} "
            f"nachziehen, sichert {e.get('sichert_r')} R"
        )
    zeilen += [
        "",
        "Warum das zaehlt: 50 % der Signale standen einmal bei +1R, nur 17,6 % "
        "kamen am Ziel an.",
        "Abschalten: config.yaml risiko.ausstieg_trailing_ausloese_r auf 0.",
    ]
    send_notification_email(
        f"TradingInfoTool: {len(empfehlungen)} Stop-Nachzieh-Empfehlung(en)",
        "\n".join(zeilen),
        empfaenger,
    )


def kanarienvogel_job(mistral_client) -> None:
    """Taegliche LLM-Drift-Pruefung (2026-08-05, siehe agent/krypto/kanarienvogel.py).

    ANLASS war der 31.07.: das Hebel-Verhalten kippte binnen einer Stunde
    (selbst gewaehltes HALTEN von 35-51 auf 2-6 taeglich, Konfidenz 54,1 ->
    68,3 %), und wir haben TAGE im eigenen Regelwerk gesucht - drei
    Prompt-Regeln einzeln gegen einen Backtest, Gate, Markt, Messmethodik.
    Der Nachweis kam erst durch ein Replay derselben Faktensaetze mit dem
    bitgleichen Juli-Prompt: +12,6 Punkte Konfidenz bei unveraendertem
    Modellnamen. Dieser Job macht daraus eine laufende Messung.

    Fuenf eingefrorene Faktensaetze x 2 Wiederholungen = 10 Aufrufe taeglich.
    Bewusst klein: die Messung soll das Kontingent nicht spuerbar belasten,
    und fuer eine Verschiebung von der Groessenordnung des 31.07. reicht das
    bei weitem (Eigenrauschen rund ein halber Punkt, Bruch 12,6 Punkte).

    Faellt der Provider aus, meldet der Befund das ausdruecklich statt still
    Entwarnung zu geben - ein stummer Kanarienvogel ist kein gesunder.

    NICHT IM SCHEDULER REGISTRIERT (bewusst, 05.08.). Der Nutzer hat beim Bau
    gefragt, ob das Feature ueberhaupt Wert bringt - zu Recht: es erzeugt kein
    einziges zusaetzliches Signal, und der Drift, gegen den es schuetzt, ist
    inzwischen bekannt. Es ist eine Versicherung gegen eine WIEDERHOLUNG, kein
    Beitrag zum Ziel "mehr und bessere Signale". Der Baustein bleibt fertig und
    getestet liegen; die Grundlinie ist aufgenommen, damit ein spaeterer
    Vergleich ueberhaupt moeglich ist. Aktivieren heisst: einen add_job()-Aufruf
    in start_scheduler() ergaenzen (taeglich, vor dem Backward-Tracking).

    REVISIT-BEDINGUNG: sobald ein zweiter unerklaerter Verhaltenssprung
    auftritt - dann ist die Wiederholungswahrscheinlichkeit belegt statt
    vermutet."""
    from agent.krypto.hebel_analyst import SYSTEM_PROMPT
    from agent.krypto.kanarienvogel import pruefe_llm_drift

    if mistral_client is None:
        logger.info("Kanarienvogel uebersprungen - kein Mistral-Client")
        return

    def frage(client, fakten, prompt):
        # `json` WAR IN DIESEM MODUL NIRGENDS IMPORTIERT (gefunden 15.08.2026
        # mit der Suche nach freien Namen). Aufgefallen ist es nie, weil der
        # Kanarienvogel einen Mistral-Client braucht und Mistral seit dem
        # 07.08. nicht mehr im Betrieb ist - die Zeile darueber kehrt vorher
        # zurueck. Beim ersten echten Lauf waere es ein NameError gewesen.
        import json

        roh = client.chat(
            [{"role": "system", "content": prompt},
             {"role": "user", "content": json.dumps(fakten, ensure_ascii=False)}],
            temperature=0.2,
            response_format={"type": "json_object"},
        )
        return json.loads(roh)

    try:
        befund = pruefe_llm_drift(mistral_client, SYSTEM_PROMPT, frage)
    except Exception:
        logger.exception("Kanarienvogel-Lauf fehlgeschlagen")
        return

    if befund.abweichung:
        logger.warning("KANARIENVOGEL: %s", befund.meldung)
    else:
        logger.info("Kanarienvogel: %s (%d Aufrufe, %d Fehler)",
                    befund.meldung, befund.n_aufrufe, befund.n_fehler)


def portfolio_wert_job(conn_factory, watchlist_provider) -> None:
    """Taeglicher Portfoliowert + Z-3/RM-7-Pruefung (2026-08-04, Task #612).

    Schreibt den heutigen Wert fort und prueft die Drawdown-Notbremse. Kein
    eigener Netzwerk-Call - Bestaende und Kurse liegen bereits in der DB, wie
    beim Backward-Tracking. Deshalb auch dieselbe Uhrzeit-Logik: nach dem
    naechtlichen Kurs-Refresh.

    Z-3 ist ein ALERT, keine Automatik (Spezifikation Zeile 58) - das System
    hat ohnehin keine Handels-API. Die Mail sagt "melden und Kapitalschutz S-5
    erwaegen", nicht "verkaufen".

    BEWUSST OHNE COOLDOWN, anders als die Cash-Veto-Warnung: ein anhaltender
    Drawdown IST die Meldung wert, und zwar jeden Tag, an dem er anhaelt. Ein
    Spam-Schutz wuerde hier genau die Wiederholung unterdruecken, die die
    Dringlichkeit ausmacht. Solange der Rueckschlag unter der Schwelle bleibt,
    kommt ohnehin keine Mail."""
    import config as config_module
    from agent.portfolio_historie import pruefe_z3, schreibe_tageswert
    from api.email_notify import send_notification_email

    conn = conn_factory()
    try:
        watchlist = watchlist_provider()
        ergebnis = schreibe_tageswert(conn, watchlist=watchlist)
        logger.info(
            "Portfolio-Wert %s: %.2f EUR, Index %.3f, %d Symbole ohne Kurs",
            ergebnis["datum"], ergebnis["wert_eur"], ergebnis["index"],
            ergebnis["symbole_ohne_kurs"],
        )

        config_dict = config_module.load_config()
        schwelle = config_dict.get("ziele", {}).get("max_drawdown_prozent", 15)
        z3 = pruefe_z3(conn, schwelle_prozent=schwelle)
        if not z3["ausgeloest"]:
            logger.info(
                "Z-3: Rueckschlag %.1f%% (Schwelle %.0f%%, %d Tage Historie)",
                z3["aktuell_prozent"], schwelle, z3["tage_historie"],
            )
            return

        logger.warning(
            "Z-3 AUSGELOEST: Rueckschlag %.1f%% >= Schwelle %.0f%%",
            z3["aktuell_prozent"], schwelle,
        )
        email_cfg = config_dict.get("benachrichtigung", {}).get("email", {})
        empfaenger = email_cfg.get("empfaenger")
        if not (email_cfg.get("aktiv", False) and empfaenger):
            return

        hinweis = ""
        if z3["datenbasis_duenn"]:
            hinweis = (
                f"\n\nACHTUNG zur Einordnung: die Wertreihe umfasst erst "
                f"{z3['tage_historie']} Tage. Ein Hoechststand aus so kurzer Historie "
                "ist wenig aussagekraeftig - dieser Alarm sagt derzeit mehr ueber die "
                "Datenlage als ueber den Markt."
            )
        body = (
            f"Z-3 / RM-7 (Drawdown-Notbremse) ausgeloest.\n\n"
            f"Rueckschlag vom Hoechststand: {z3['aktuell_prozent']:.1f} %\n"
            f"Schwelle (ziele.max_drawdown_prozent): {schwelle} %\n"
            f"Groesster Rueckschlag im Zeitraum: {z3['max_prozent']:.1f} % "
            f"({z3['hoch_am']} bis {z3['tief_am']})\n"
            f"Datenbasis: {z3['tage_historie']} Tage\n\n"
            "Gerechnet wird auf einer mengenkonstanten Wertreihe - Zukaeufe und "
            "Verkaeufe sind herausgerechnet, der Rueckschlag ist also reine "
            "Marktbewegung, kein Effekt eigener Handelsaktivitaet.\n\n"
            "Z-3 ist ein hartes Limit und laut RG-6 weder durch den Nutzer noch "
            "durch die KI ueberschreibbar. Es wirkt als dringender Hinweis, nicht "
            "als automatische Aktion - zu pruefen ist der Kapitalschutz-Modus S-5."
            f"{hinweis}"
        )
        send_notification_email("TradingInfoTool: Z-3 AUSGELOEST - Drawdown-Notbremse", body, empfaenger)
    except Exception:
        logger.exception("portfolio_wert_job fehlgeschlagen")
        _notify_job_failure("portfolio_wert_job")
    finally:
        # Siehe `merke_joblauf()` - der Nachholer beim Start fragt danach.
        db.merke_joblauf(conn, "portfolio_wert")
        conn.close()


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
        # EIGENER SCHLUESSEL neben `set_backward_tracking_last_run_date`. Jene
        # Zeile steuert die FACHLICHE Fortschreibung; diese hier nur, ob der
        # Nachholer beim naechsten Start feuern muss. Zwei Fragen, zwei
        # Zeilen - sonst haengt die eine an der Semantik der anderen.
        db.merke_joblauf(conn, "backward_tracking")
        conn.close()


def marktscan_backward_tracking_job(
    coingecko_client, kraken_client, conn_factory, watchlist_provider, fred_api_key,
    mistral_client=None, gemini_client=None,
) -> None:
    """Erfolgsmessung fuer Marktscan-Kandidaten (2026-07-30, Teil 2 der Reifegrad-/
    Erfolgsmessung-Runde, siehe agent/krypto/marktscan_backward_tracking.py
    Modul-Docstring). Taeglich, feste Uhrzeit (siehe build_scheduler()) - startet
    neue Messungen (Kaufkandidaten + "heisse" Watchlist-Kandidaten) und prueft
    laufende Messungen gebuendelt gegen aktuelle CoinGecko-Preise. P-8: ohne
    mindestens einen LLM-Client (Mistral/Gemini) wird die synchrone LLM-
    Kurzbegruendung bei Erfolg uebersprungen (kein Fehler, siehe
    run_marktscan_backward_tracking()-Docstring), die Erfolgsmessung selbst
    laeuft trotzdem."""
    watchlist = watchlist_provider()
    try:
        import config as config_module
        from agent.krypto.marktscan_backward_tracking import run_marktscan_backward_tracking

        config_dict = config_module.load_config()
        if not config_dict.get("marktscan", {}).get("aktiv", True):
            logger.info("Marktscan-Erfolgsmessung: Marktscan deaktiviert - übersprungen")
            return
        llm_client = mistral_client or gemini_client
        result = run_marktscan_backward_tracking(
            conn_factory, coingecko_client, kraken_client, llm_client, watchlist, fred_api_key, config_dict,
        )
        logger.info(
            "Marktscan-Erfolgsmessung: %d neue Messung(en) gestartet, %d geprüft, %d Erfolg(e), "
            "%d kein Erfolg, %d Schnellerfolg(e)%s",
            result["neue_messungen"], result["geprueft"], result["erfolge"], result["kein_erfolg"],
            len(result["schnellerfolge"]),
            # Seit 2026-08-09: der Preisabruf ist fail-soft (ein 504 hat vorher
            # den ganzen Lauf beendet). Ohne diesen Zusatz sähe ein Lauf mit
            # gescheitertem Abruf aus wie ein ruhiger Lauf mit 0 Prüfungen.
            f" - ACHTUNG Preisabruf fehlgeschlagen: {result['preis_abruf_fehler']}"
            if result.get("preis_abruf_fehler") else "",
        )
        _notify_marktscan_schnellerfolg(result["schnellerfolge"], config_dict)
    except Exception as exc:
        logger.exception("Marktscan-Erfolgsmessung fehlgeschlagen")
        _notify_job_failure("marktscan_backward_tracking", f"Marktscan-Erfolgsmessung fehlgeschlagen: {exc}")


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


# Welcher physisch hinterlegte ETF steht fuer welchen Rohstoff.
# MANUELL GEPFLEGT wie `SYMBOL_ZU_COT_ROHSTOFF` - eine Heuristik ueber
# Namen waere fragiler, und es sind drei Zeilen.
#
# Kupfer fehlt absichtlich: CPER liefert keine `sharesOutstanding`
# (live geprueft 17.08.).
ROHSTOFF_ZU_ETF = {
    "gold": "GLD",
    "silber": "SLV",
    "erdgas": "UNG",
}


def _aktien_symbole() -> list:
    """Die Aktien der Watchlist - aus der Konfiguration, nicht aus einer Liste.

    Eine zweite, hier gepflegte Aufzaehlung waere die naechste Stelle, an der
    ein neuer Wert vergessen wird."""
    import config as config_module

    raus = []

    def geh(o):
        if isinstance(o, dict):
            if o.get("symbol") and str(o.get("assetklasse", "")).lower() in (
                    "aktien", "aktie"):
                raus.append(str(o["symbol"]).upper())
            for v in o.values():
                geh(v)
        elif isinstance(o, list):
            for v in o:
                geh(v)

    geh(config_module.load_config())
    return sorted(set(raus))


def _aktien_reihen(conn) -> int:
    """Leerverkaufsposition und Insiderzaehlung je Aktie - beide persistiert.

    ⚠️ DIE INSIDERZAHLEN GEHOEREN ZWINGEND HIERHER und nicht in die Rolle.
    Ein Form-4-Abruf sind mehrere Anfragen je Symbol; die SEC drosselt bei
    zehn je Sekunde, und `get_recent_insider_transactions` faengt jeden
    Filing-Fehler einzeln ab. Eine Sperre erschiene damit als "keine
    Insider-Aktivitaet" - eine Aussage ueber das Unternehmen, die niemand
    geprueft hat. Am 16.08. ist genau das passiert, deshalb gibt es jetzt
    `SecGesperrtError`: hier wird sie GEMELDET statt verschluckt."""
    from api.finra import get_days_to_cover_history
    from api.sec_edgar import (
        SecGesperrtError,
        get_recent_insider_transactions,
        summarize_insider_activity,
    )
    from database import db as DB

    heute = datetime.now(timezone.utc).date().isoformat()
    geschrieben = 0
    for sym in _aktien_symbole():
        try:
            geschrieben += DB.schreibe_externe_reihe(
                conn, "finra", f"{sym}_days_to_cover",
                get_days_to_cover_history(sym))
        except Exception as exc:                             # noqa: BLE001
            logger.info("Leerverkaufsposition %s nicht auffrischbar: %s", sym, exc)
        # FUNDAMENTALDATEN (17.08.2026). Sie gehen an Rolle BC, nicht an G -
        # der erste Fakt der entscheidenden Rolle, der nicht aus der
        # Kerzenreihe stammt. Als ZEITREIHE abgelegt, obwohl heute nur der
        # letzte Wert gelesen wird: damit baut sich nebenbei die Historie
        # auf, die ein spaeteres Perzentil braucht - und ein Wachstum gegen
        # die eigene Vergangenheit ist eine bessere Aussage als eines gegen
        # nichts.
        try:
            from api.yfinance_client import fetch_fundamentals

            f = fetch_fundamentals(sym, sym)
            for feld in ("gewinnwachstum_pct", "umsatzwachstum_pct"):
                wert = getattr(f, feld, None)
                if wert is not None:
                    geschrieben += DB.schreibe_externe_reihe(
                        conn, "yfinance", f"{sym}_{feld}",
                        [(heute, float(wert))])
        except Exception as exc:                             # noqa: BLE001
            logger.info("Fundamentaldaten %s nicht auffrischbar: %s", sym, exc)
        try:
            tr = get_recent_insider_transactions(sym, max_filings=40,
                                                 lookback_tage=90)
            z = summarize_insider_activity(tr) or {}
            # AUCH NULL WIRD GESCHRIEBEN. "Niemand hat gekauft" ist ein Fakt;
            # ohne die Zeile waere er von "wir haben nicht nachgesehen" nicht
            # zu unterscheiden - und ueber die Zeit entsteht so nebenbei die
            # Reihe, die ein spaeteres Perzentil braucht.
            geschrieben += DB.schreibe_externe_reihe(
                conn, "sec_edgar", f"{sym}_insider_kaeufe",
                [(heute, float(z.get("anzahl_kaeufe") or 0))])
            geschrieben += DB.schreibe_externe_reihe(
                conn, "sec_edgar", f"{sym}_insider_verkaeufe",
                [(heute, float(z.get("anzahl_verkaeufe") or 0))])
        except SecGesperrtError as exc:
            # LAUT, NICHT LEISE: eine Sperre ist ein Betriebsvorfall. Nichts
            # wird geschrieben - der gestrige Stand bleibt stehen und ist
            # ehrlicher als eine frisch datierte Null.
            logger.warning("SEC gesperrt, Insiderzahlen fuer %s NICHT "
                           "aufgefrischt: %s", sym, exc)
        except Exception as exc:                             # noqa: BLE001
            logger.info("Insiderzahlen %s nicht auffrischbar: %s", sym, exc)
    return geschrieben


def externe_reihen_job(conn_factory) -> None:
    """Die Fremdquellen der Rolle G auffrischen (2026-08-16, Schritt 3).

    WARUM ES DIESEN JOB GIBT. `zweite_meinung.rolle_g` oeffnet die Datenbank
    mit `mode=ro` - sie kann nicht schreiben. Ohne einen Job haenge jedes
    Urteil unmittelbar am Netz: faellt CoinMetrics oder die CFTC aus, faellt
    der Fakt aus, und ein Signal ohne Gegenpruefung sieht aus wie eines, das
    sie bestanden hat ("fail-soft ist fail-silent").

    Dieselbe Arbeitsteilung wie beim Terminmarkt: `hebel_screening` schreibt
    `open_interest_snapshot`, `positionierung` liest nur.

    JEDE QUELLE EINZELN GEFANGEN. Faellt die CFTC aus, soll der Boersenfluss
    trotzdem aktuell werden - dasselbe Muster wie in `run_makro_analog_update`.

    ZAEHLT NICHT ALS FEHLSCHLAG, wenn eine Reihe leer bleibt: die CFTC
    veroeffentlicht freitags, an sechs von sieben Tagen aendert sich nichts.
    Gemeldet wird nur, was gar nicht erreichbar war."""
    conn = conn_factory()
    geschrieben = 0
    # ⚠️ HIER, NICHT IN `_aktien_reihen`. Mein erster Entwurf benutzte
    # `heute` im Deribit-Block, wo es nicht definiert ist - ein
    # NameError, den der breite Fang als "nicht auffrischbar"
    # verschluckt haette. `finde_freie_namen.py` hat ihn gefangen,
    # bevor er lief; genau dafuer gibt es das Werkzeug (viermal in
    # zwei Tagen, zuletzt `assetklasse` mit zwei Vormittagen).
    heute = datetime.now(timezone.utc).date().isoformat()
    try:
        from agent.rohstoff.pipeline import SYMBOL_ZU_COT_ROHSTOFF
        from api.cftc_cot import get_cot_long_anteil_history
        from api.onchain import get_btc_exchange_flow_history
        from database import db as DB

        try:
            reihe = get_btc_exchange_flow_history(tage=800)
            geschrieben += DB.schreibe_externe_reihe(
                conn, "coinmetrics", "btc_netto_boersenfluss", reihe)
        except Exception as exc:                             # noqa: BLE001
            logger.info("Boersenfluesse nicht auffrischbar: %s", exc)

        # DAS STABLECOIN-ANGEBOT (17.08.2026) - heute OHNE Wirkung, und
        # genau deshalb jetzt.
        #
        # `get_stablecoin_supply()` liefert nur den Momentanwert; DefiLlama
        # hat keinen Historienendpunkt, den wir kostenlos lesen koennten.
        # Ohne Historie kein Perzentil, ohne Perzentil kein Satz (R-T5) -
        # deshalb entsteht heute KEINE Aussage daraus.
        #
        # WARUM SIE TROTZDEM AB HEUTE LAEUFT: die Reihe muss irgendwann
        # anfangen zu wachsen, und jeder Tag Verzoegerung ist ein Tag
        # spaeter, an dem sie brauchbar wird. Bei taeglichem Takt ist ein
        # 90-Tage-Perzentil in drei Monaten da. Kostet einen Abruf.
        #
        # WOFUER: das Gesamtangebot aller Stablecoins ist das
        # "Trockenpulver" - Kapital, das im Kryptomarkt liegt, aber nicht
        # investiert ist. Es ist WEDER aus einer Kursreihe abgeleitet NOCH
        # eine Positionierung am Terminmarkt, also eine dritte
        # Informationsart fuer Krypto.
        try:
            from api.onchain import get_stablecoin_supply

            s = get_stablecoin_supply()
            geschrieben += DB.schreibe_externe_reihe(
                conn, "defillama", "stablecoin_angebot_usd",
                [(s.date, float(s.total_usd))])
        except Exception as exc:                             # noqa: BLE001
            logger.info("Stablecoin-Angebot nicht auffrischbar: %s", exc)

        # DER OPTIONSMARKT (17.08.2026) - wie das Stablecoin-Angebot:
        # heute ohne Satz, ab dem ersten Perzentil mit.
        #
        # WAS IHN BESONDERS MACHT: DVOL ist die IMPLIZITE Volatilitaet -
        # was der Markt fuer die naechsten Wochen ERWARTET, nicht was war.
        # Als einzige unserer Quellen ist er vorausschauend und
        # marktgepreist. Der Skew sagt dazu, ob Absicherung nach unten
        # teurer ist als Spekulation nach oben.
        #
        # ⚠️ NUR BTC UND ETH. Live geprueft: SOL liefert nichts, und das
        # gilt fuer die uebrigen 41 Kryptowerte genauso - Deribit fuehrt
        # nur fuer diese beiden einen liquiden Optionsmarkt.
        try:
            from api.deribit import (get_options_skew,
                                     get_volatility_index)

            for waehrung in ("BTC", "ETH"):
                dvol = get_volatility_index(waehrung)
                if dvol is not None:
                    geschrieben += DB.schreibe_externe_reihe(
                        conn, "deribit", f"{waehrung}_dvol",
                        [(heute, float(dvol))])
                skew = get_options_skew(waehrung) or {}
                if skew.get("skew_prozentpunkte") is not None:
                    geschrieben += DB.schreibe_externe_reihe(
                        conn, "deribit", f"{waehrung}_skew",
                        [(heute, float(skew["skew_prozentpunkte"]))])
        except Exception as exc:                             # noqa: BLE001
            logger.info("Optionsmarkt nicht auffrischbar: %s", exc)

        # `set()` - vier Symbole, aber je Rohstoff nur ein Bericht. Ohne das
        # waeren es vier identische Abrufe, sobald zwei ETCs denselben
        # Basiswert haetten.
        for stoff in sorted(set(SYMBOL_ZU_COT_ROHSTOFF.values())):
            try:
                geschrieben += DB.schreibe_externe_reihe(
                    conn, "cftc_cot", stoff,
                    get_cot_long_anteil_history(stoff))
            except Exception as exc:                         # noqa: BLE001
                logger.info("COT %s nicht auffrischbar: %s", stoff, exc)

        # DIE HINTERLEGTE METALLMENGE (17.08.2026). Rohstoffe hatten in
        # Rolle G genau EINE Quelle (COT) - G1 verlangt zwei.
        #
        # WARUM DIE STUECKZAHL UND NICHT DAS FONDSVOLUMEN: das Volumen ist
        # Stueck x Preis und damit eine Kursgroesse. Die STUECKZAHL eines
        # physisch hinterlegten ETF aendert sich nur, wenn Metall
        # tatsaechlich ein- oder ausgelagert wird - eine echte
        # Nachfragegroesse, unabhaengig vom Preis. Derselbe Gedanke wie
        # beim Krypto-Umschlag.
        #
        # ⚠️ KUPFER FEHLT. Live geprueft: CPER liefert keine
        # `sharesOutstanding`. Drei von vier ist trotzdem deutlich mehr
        # als EIA, das nur Erdgas deckt und einen Schluessel braucht.
        try:
            import yfinance as _yf

            for stoff, etf in ROHSTOFF_ZU_ETF.items():
                stueck = (_yf.Ticker(etf).info or {}).get("sharesOutstanding")
                if stueck:
                    geschrieben += DB.schreibe_externe_reihe(
                        conn, "etf_bestand", f"{stoff}_stueckzahl",
                        [(heute, float(stueck))])
        except Exception as exc:                             # noqa: BLE001
            logger.info("ETF-Bestaende nicht auffrischbar: %s", exc)

        geschrieben += _aktien_reihen(conn)
        # SICH SELBST BUCHEN. Ohne diese Zeile fehlte der Job im
        # `joblaeufe`-Abschnitt des Exports - gebaut, aber unsichtbar.
        # Aufgefallen im ersten Export, der den Abschnitt trug.
        DB.merke_joblauf(conn, "externe_reihen")
        logger.info("Externe Reihen aufgefrischt: %d Punkte geschrieben.",
                    geschrieben)
    except Exception as exc:
        logger.exception("Auffrischen der externen Reihen fehlgeschlagen")
        _notify_job_failure("externe_reihen",
                            f"Externe Reihen fehlgeschlagen: {exc}")
    finally:
        conn.close()


def kategorie_vorschlaege_job(conn_factory) -> None:
    """#333 KI-Vorschlaege-Job fuer Kategorie-Schwerpunkte (2026-07-24, siehe
    agent/kategorie_vorschlaege.py Modul-Docstring) - taeglich: prueft alle
    Hauptgruppe/Unterkategorie-Schluessel aus config.PRUEF_MECHANISMUS_MAPPING,
    legt bei anhaltendem Signal automatisch neue Thesen an (Fall A) oder hebt
    Aenderungsaufforderungen gegen bestehende Thesen auf 'offen' (Fall B).
    Rein deterministisch, kein LLM-Call (Schicht 2 - ein taeglicher LLM-
    Synthese-Call ueber alle Kategorien - ist noch nicht gebaut, siehe Punkt 2
    der #333-Statustabelle in Kategorie_Basisinformationen_Release2.md)."""
    conn = conn_factory()
    try:
        from agent.kategorie_vorschlaege import run_kategorie_vorschlaege_job

        run_kategorie_vorschlaege_job(conn)
        logger.info("Kategorie-Vorschlaege-Job (#333) durchgelaufen.")
    except Exception as exc:
        logger.exception("Kategorie-Vorschlaege-Job (#333) fehlgeschlagen")
        _notify_job_failure("kategorie_vorschlaege", f"Kategorie-Vorschlaege-Job fehlgeschlagen: {exc}")
    finally:
        conn.close()


def kategorie_synthese_job(conn_factory, mistral_client=None, groq_client=None, gemini_client=None) -> None:
    """#333 Schicht 2 (2026-07-25) - kategorienuebergreifender LLM-Synthese-
    Call, siehe agent/kategorie_synthese.py Modul-Docstring. Laeuft 15 Min VOR
    kategorie_vorschlaege_job (06:15 vs. 06:30) - Schicht 1 liest das
    Tagesergebnis fuer die Gleichzeitigkeits-Moderation, das muss deshalb VOR
    Schicht 1 vorliegen (siehe build_scheduler()-Kommentar an der
    Registrierungsstelle fuer die volle Begruendung). P-8: ohne mindestens
    einen gesetzten Client wird der Lauf uebersprungen (kein Fehler) - ebenso,
    wenn alle Provider fehlschlagen (run_kategorie_synthese() gibt dann None
    zurueck, alle Konsumenten (Fall-A/B-Moderation, Screener-Score-Bonus)
    degradieren auf ihr Vor-Schicht-2-Verhalten)."""
    # MISTRAL IST RAUS (14.08.2026). Sein Free-Plan wurde am 07.08.
    # kostenpflichtig; seitdem beantwortet er jeden Aufruf mit
    # "402 Payment Required". Im Log des Nutzers vom 14.08.:
    #
    #     agent.kategorie_synthese: mistral-Call fuer Kategorie-Synthese
    #     fehlgeschlagen: 402 Client Error: Payment Required
    #     ...
    #     Kategorie-Synthese: 19 Kategorien eingeordnet (gemini)
    #
    # Der Rueckfall auf Gemini funktionierte also jedes Mal - der Mistral-Ruf
    # war reine Verzoegerung plus eine Fehlerzeile je Durchlauf. Ein Fehler,
    # der bei JEDEM Lauf auftritt und nichts bedeutet, ist schlimmer als
    # keiner: er trainiert das Auge, Fehlerzeilen zu ueberlesen.
    #
    # DER PARAMETER BLEIBT in der Signatur - der Scheduler uebergibt ihn, und
    # ihn dort zu entfernen waere eine Aenderung an sechs Aufrufstellen fuer
    # nichts. Wer Mistral wieder bezahlt, traegt ihn hier wieder ein.
    llm_clients = [("gemini", gemini_client)]
    if not any(client is not None for _, client in llm_clients):
        logger.info("Kategorie-Synthese: kein LLM-Client konfiguriert, uebersprungen.")
        return
    conn = conn_factory()
    try:
        import json

        from agent.kategorie_synthese import run_kategorie_synthese

        ergebnis = run_kategorie_synthese(conn, llm_clients)
        if ergebnis is not None:
            logger.info("Kategorie-Synthese-Job (#333 Schicht 2) durchgelaufen.")
            _notify_schneller_wechsel(json.loads(ergebnis.kategorie_ergebnisse_json))
    except Exception as exc:
        logger.exception("Kategorie-Synthese-Job (#333 Schicht 2) fehlgeschlagen")
        _notify_job_failure("kategorie_synthese", f"Kategorie-Synthese-Job fehlgeschlagen: {exc}")
    finally:
        conn.close()


def backward_tracking_catchup_if_missed(conn_factory, watchlist_provider) -> None:
    """2026-07-17, Nutzer-Fund: der feste 06:00-Cron holt einen verpassten Termin
    NICHT automatisch nach, wenn die App zu diesem Zeitpunkt gar nicht lief (an
    zwei aufeinanderfolgenden Tagen passiert, 07-15 und 07-16 - zwei Tage lang
    keine einzige Backward-Tracking-Auswertung, obwohl laengst faellig). Beim
    App-Start einmalig geprueft: wurde der heutige Lauf bereits erledigt? Falls
    nicht, sofort synchron nachholen (kein Netzwerk-Call, reine DB-Auswertung,
    siehe backward_tracking_job()-Docstring - unbedenklich, das direkt beim
    Start zu tun). Verhindert gleichzeitig unnoetige Mehrfach-Laeufe bei
    mehreren Neustarts am selben Tag, nachdem der heutige Lauf schon glückte.

    `watchlist_provider` siehe refresh_prices_job()-Docstring (2026-07-23) -
    MUSS der Provider sein, nicht eine bereits aufgeloeste Liste (BUGFIX
    2026-07-25: der Call in build_scheduler() gab hier faelschlich die lokal
    aufgeloeste `watchlist`-Liste weiter, backward_tracking_job() ruft ihren
    zweiten Parameter aber als Funktion auf - Absturz direkt beim App-Start,
    TypeError: 'list' object is not callable)."""
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
    backward_tracking_job(conn_factory, watchlist_provider)


def _letzter_faelliger_multi_asset_termin(now: datetime) -> datetime:
    """Ermittelt den letzten Slot aus MULTI_ASSET_BATCH_CRON_HOURS (Mo-Fr,
    9:00/19:00 lokal), der bereits erreicht wurde. Geht noetigenfalls mehrere
    Tage zurueck (Wochenende, laengerer Ausfall). Reine Datumsarithmetik, kein
    Bezug zu APScheduler - siehe multi_asset_batch_catchup_if_missed()."""
    kandidat_tag = now
    for _ in range(10):
        for stunde in (19, 9):
            slot = kandidat_tag.replace(hour=stunde, minute=0, second=0, microsecond=0)
            if slot <= now and slot.weekday() < 5:
                return slot
        kandidat_tag -= timedelta(days=1)
    return now


def multi_asset_batch_catchup_if_missed(
    conn_factory, watchlist_provider, coingecko_client, gemini_client=None, mistral_client=None,
    zai_client=None, openrouter_client=None,
) -> None:
    """2026-07-30, Nutzer-Fund: waehrend intensiver Entwicklungsarbeit startete
    die App an 27./28./29.07. auffaellig oft neu (11/11/4x) - der 2x/Tag-Cron
    von multi_asset_batch_job() (Mo-Fr 9/19 Uhr, siehe MULTI_ASSET_BATCH_CRON_
    HOURS) hat dabei GENAU wie der 06:00-Backward-Tracking-Cron vor diesem Fix
    (siehe backward_tracking_catchup_if_missed() oben) keinen automatischen
    Nachhol-Mechanismus: fiel ein Neustart in eines der beiden schmalen
    Zeitfenster, wurde der Termin fuer den Tag ersatzlos uebersprungen (28.07.
    19:00 komplett ausgefallen; 29.07. 09:00 durch einen Neustart mitten im
    Lauf abgebrochen, PLTR/Aktien nie erreicht) - waehrend die haeufiger
    getakteten Krypto-Jobs (15-Min-Intervall) einen kurzen Ausfall praktisch
    nie bemerken. Betrifft alle 4 ueber diesen Batch abgedeckten Assetklassen
    (Aktien/Rohstoffe/Themen-ETF/Hedge), inkl. der Hedge-Absicherungspositionen
    (DBPK/3QSS).

    Analog zum Backward-Tracking-Fix: beim App-Start einmalig geprueft, ob der
    letzte bereits FAELLIGE Slot (`_letzter_faelliger_multi_asset_termin()`)
    tatsaechlich beendet wurde. Bewusst NICHT einfach next_run_time=jetzt beim
    Job selbst (siehe Kommentar an dessen add_job()-Aufruf: das wuerde bei
    JEDEM Neustart ausserhalb der Handelszeiten feuern) - nur ein GENUIN
    verpasster Slot loest den Nachhol-Lauf aus, kein Neustart innerhalb eines
    bereits erledigten Zeitfensters."""
    letzter_faelliger_termin = _letzter_faelliger_multi_asset_termin(datetime.now())
    conn = conn_factory()
    try:
        last_run_iso = db.get_multi_asset_batch_last_run_iso(conn)
    finally:
        conn.close()
    if last_run_iso is not None:
        try:
            last_run = datetime.fromisoformat(last_run_iso)
        except ValueError:
            last_run = None
    else:
        last_run = None
    if last_run is not None and last_run >= letzter_faelliger_termin:
        return
    logger.info(
        "Multi-Asset-Batch: faelliger Termin %s noch nicht erledigt (zuletzt: %s) - hole sofort nach.",
        letzter_faelliger_termin.isoformat(timespec="minutes"), last_run_iso or "nie",
    )
    multi_asset_batch_job(
        conn_factory, watchlist_provider, coingecko_client,
        gemini_client=gemini_client, mistral_client=mistral_client, zai_client=zai_client,
        openrouter_client=openrouter_client,
    )


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


def _notify_coingecko_quota_warning(anzahl: int, limit: int, schwelle_prozent: int, prozent: float) -> None:
    """WARNUNG-E-Mail bei ueberschrittener CoinGecko-Kontingent-Schwelle
    (2026-07-31, echte CoinGecko-80%-Warnmail ausgeloest, siehe Memory
    project_bug_runde_31_07_notebook_export). Anders als die anderen Warn-
    mails hier bewusst KEIN Zeit-Cooldown (Aufrufer coingecko_quota_check_job
    prueft bereits ueber database.db::has_quota_warnung_been_sent(), ob diese
    Schwelle in diesem Monat schon gemeldet wurde - ein DB-Flag statt eines
    In-Memory-Zeitstempels, der bei jedem Neustart verloren ginge)."""
    import config as config_module
    from api.email_notify import send_notification_email

    config_dict = config_module.load_config()
    email_cfg = config_dict.get("benachrichtigung", {}).get("email", {})
    if not email_cfg.get("aktiv", False):
        return
    empfaenger = email_cfg.get("empfaenger")
    if not empfaenger:
        return

    body = (
        f"CoinGecko-Monats-Kontingent hat {schwelle_prozent}% erreicht "
        f"({anzahl:,} von {limit:,} Calls, {prozent:.1f}%).\n\n"
        "Bei 100% wird das Kontingent laut CoinGecko hart gedeckelt - Preis-/"
        "Historie-/Marktscan-Abrufe wuerden dann fehlschlagen, bis der naechste "
        "Kalendermonat beginnt (oder auf einen bezahlten Plan umgestellt wird).\n\n"
        f"Diese Warnung wird fuer die {schwelle_prozent}%-Schwelle nur einmal "
        "pro Kalendermonat versendet."
    )
    send_notification_email(
        f"TradingInfoTool: CoinGecko-Kontingent {schwelle_prozent}% erreicht", body, empfaenger,
    )


def coingecko_quota_check_job(db_conn_factory) -> None:
    """Prueft periodisch (COINGECKO_QUOTA_CHECK_INTERVAL_MINUTES), ob das
    CoinGecko-Monats-Kontingent eine in config.yaml (coingecko_quota.
    warnschwellen_prozent) definierte Warnschwelle ueberschritten hat
    (2026-07-31, echte CoinGecko-80%-Warnmail ausgeloest). BEWUSST komplett
    von der eigentlichen Zaehlung entkoppelt (siehe api/coingecko.py::
    CoinGeckoClient._track_quota()) - dieser Job liest den Zaehler nur,
    schreibt ihn nie selbst. Ein Fehler hier kann daher NIE einen echten
    CoinGecko-API-Call beeintraechtigen, selbst wenn diese Funktion komplett
    fehlschlaegt."""
    import config as config_module

    config_dict = config_module.load_config()
    cfg = config_dict.get("coingecko_quota", {})
    limit = cfg.get("monatslimit")
    if not limit:
        return
    schwellen = sorted(cfg.get("warnschwellen_prozent", [80, 90]))

    conn = db_conn_factory()
    try:
        monat = db.aktueller_monat_utc()
        anzahl = db.get_api_call_counter(conn, "coingecko", monat)
        prozent = (anzahl / limit) * 100
        for schwelle in schwellen:
            if prozent >= schwelle and not db.has_quota_warnung_been_sent(conn, "coingecko", monat, schwelle):
                db.record_quota_warnung_sent(conn, "coingecko", monat, schwelle)
                _notify_coingecko_quota_warning(anzahl, limit, schwelle, prozent)
    finally:
        conn.close()


# Schnelle-Wechsel-Warnmail (#333 Schicht 2, 2026-07-25) - EIN globaler
# Zeitstempel, gleiches Prinzip wie _last_cash_veto_email_sent: der Job selbst
# laeuft nur 1x/Tag (06:15), der eigentliche Spam-Risiko-Fall ist ein Neustart
# waehrend des Tages (next_run_time=jetzt bootstrappt den Job bei JEDEM
# App-Start sofort erneut, siehe build_scheduler()).
_last_schneller_wechsel_email_sent: float | None = None


def _notify_schneller_wechsel(kategorien: list[dict]) -> None:
    """WARNUNG-E-Mail fuer Kategorien, die #333 Schicht 2 heute als
    'schneller_wechsel' (akuter Regime-Umschwung) eingestuft hat - Nutzer-
    Entscheidung 2026-07-25 ("bei schnellen Wechseln rasch reagieren"), im
    Gegensatz zu 'sanfter_uebergang'/'stabil', die rein passiv im
    Schwerpunkte-Tab sichtbar bleiben (kein E-Mail-Spam bei jedem gewoehnlichen
    Trend)."""
    global _last_schneller_wechsel_email_sent
    import config as config_module
    from api.email_notify import send_notification_email

    schnelle = [k for k in kategorien if k.get("phase_charakter") == "schneller_wechsel"]
    if not schnelle:
        return

    config_dict = config_module.load_config()
    email_cfg = config_dict.get("benachrichtigung", {}).get("email", {})
    if not email_cfg.get("aktiv", False):
        return
    empfaenger = email_cfg.get("empfaenger")
    if not empfaenger:
        return

    cooldown_minuten = email_cfg.get("schneller_wechsel_email_cooldown_minuten", 360)
    if (
        _last_schneller_wechsel_email_sent is not None
        and time.monotonic() - _last_schneller_wechsel_email_sent < cooldown_minuten * 60
    ):
        logger.info(
            "Kategorie-Synthese: %d 'schneller_wechsel'-Kategorie(n) erkannt, E-Mail wegen "
            "Cooldown unterdrueckt (%s).",
            len(schnelle), [k.get("hauptgruppe") for k in schnelle],
        )
        return

    logger.info(
        "Kategorie-Synthese: 'schneller_wechsel' erkannt, sende Warnmail (%s).",
        [k.get("hauptgruppe") for k in schnelle],
    )
    zeilen = []
    for eintrag in schnelle:
        hauptgruppe, unterkategorie = eintrag.get("hauptgruppe"), eintrag.get("unterkategorie")
        kategorie_text = hauptgruppe if not unterkategorie else f"{hauptgruppe}: {unterkategorie}"
        zeilen.append(f"- {kategorie_text}: {eintrag.get('kurzbegruendung', '')}")

    body = (
        f"#333 Schicht 2 hat heute {len(schnelle)} Kategorie(n) als akuten, schnellen Wechsel "
        "eingestuft (siehe Schwerpunkte-Tab, Tages-Synthese):\n\n"
        + "\n".join(zeilen)
        + f"\n\nWeitere Meldungen werden fuer {cooldown_minuten} Minuten unterdrueckt (Spam-Schutz)."
    )
    if send_notification_email("TradingInfoTool: Schneller Kategorie-Wechsel erkannt", body, empfaenger):
        _last_schneller_wechsel_email_sent = time.monotonic()


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


def _notify_marktscan_writeup(candidate, config_dict: dict) -> None:
    """Mail 1 (2026-07-30, siehe hebel_screening_job()::_on_signal_ready() -
    "marktscan:"-Zweig): E-Mail sobald ein Marktscan-Kaufkandidat sein LLM-
    Kurzgutachten (Tier-2-Dispatch im Budget-Allocator) erhalten hat. Feuert fuer
    JEDEN Tier-2-Writeup (keine Potential-Schwelle als Trigger noetig), enthaelt
    aber einen zusaetzlichen Hinweis-Satz, falls der Kandidat das "hohes
    Potential"-Kriterium erfuellt (dieselbe Definition wie budget_allocator.py::
    effektive_sla_marktscan, siehe marktscan.py::ist_hohes_potential_kandidat()).
    Kein Cooldown noetig (ein Writeup pro Kandidat, kein Wiederholungsrisiko)."""
    try:
        from agent.krypto.marktscan import ist_hohes_potential_kandidat
        from api.email_notify import send_notification_email

        email_cfg = config_dict.get("benachrichtigung", {}).get("email", {})
        if not email_cfg.get("aktiv", False):
            return
        empfaenger = email_cfg.get("empfaenger")
        if not empfaenger:
            return
        if not config_dict.get("marktscan", {}).get("benachrichtigung_email", False):
            return

        score_text = f"{candidate.score_gesamt:.0f}" if candidate.score_gesamt is not None else "?"
        body = (
            f"KI-Kurzgutachten fuer Marktscan-Kaufkandidat {candidate.symbol} ({candidate.name}) "
            f"ist da:\n\nScore {score_text}, Tier {candidate.tier}: {candidate.einstufung_begruendung}\n\n"
            f"KI-Kurzbegründung: {candidate.groq_kurzbegruendung or '(keine)'}"
        )
        if ist_hohes_potential_kandidat(candidate, config_dict):
            body += (
                "\n\n⚠ Hohes Potential: frisch entdeckt (noch kein Streak-Malus) und Score "
                "deutlich ueber der Kaufkandidat-Schwelle."
            )
        body += "\n\nDetails im Marktscan-Tab der App."
        send_notification_email(
            f"TradingInfoTool: KI-Kurzgutachten für Marktscan-Kaufkandidat {candidate.symbol}",
            body,
            empfaenger,
        )
    except Exception:
        logger.exception("Marktscan-Tier2-Writeup-E-Mail fehlgeschlagen")


def _notify_marktscan_watchlist_heiss(kandidaten: list) -> None:
    """Mail 2 (2026-07-30, siehe marktscan_job() - Watchlist-"heiss"): analog
    _notify_marktscan_kaufkandidaten(), aber fuer Watchlist-würdig-Kandidaten, die
    innerhalb kurzer Zeit (config.yaml marktscan.erfolgsmessung.watchlist_heiss_
    fenster_stunden) bereits 3x gesichtet wurden - ein staerkeres Signal als eine
    einzelne watchlist_wuerdig-Einstufung. Bewusst OHNE Cooldown (feuert nur
    EINMAL pro Coin, siehe Uebergangs-Guard sichtung_position==3 an der
    Aufrufstelle)."""
    if not kandidaten:
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
        for c in kandidaten:
            score_text = f"{c.score_gesamt:.0f}" if c.score_gesamt is not None else "?"
            zeilen.append(f"- {c.symbol} ({c.name}), Score {score_text}: {c.einstufung_begruendung}")

        body = (
            f"{len(kandidaten)} Watchlist-würdige Kandidat(en) wurden innerhalb kurzer Zeit "
            "bereits 3x gesichtet (\"heiß\"):\n\n"
            + "\n".join(zeilen)
            + "\n\nDetails im Marktscan-Tab der App."
        )
        send_notification_email(
            f"TradingInfoTool: {len(kandidaten)} 'heiße(r)' Marktscan-Watchlist-Kandidat(en)",
            body,
            empfaenger,
        )
    except Exception:
        logger.exception("Marktscan-Watchlist-heiss-E-Mail fehlgeschlagen")


def _notify_marktscan_schnellerfolg(erfolge: list, config_dict: dict) -> None:
    """Mail 3 (2026-07-30, siehe marktscan_backward_tracking_job()): NUR fuer
    Kandidaten, deren Erfolgsmessung ungewoehnlich schnell abgeschlossen wurde
    (tatsaechliche Dauer <= config.yaml marktscan.erfolgsmessung.
    schnellerfolg_anteil_max * geschaetzter Dauer) - siehe agent/krypto/
    marktscan_backward_tracking.py::run_marktscan_backward_tracking() fuer das
    Gate selbst. JEDER Erfolg wird unabhaengig davon vollstaendig in der DB
    erfasst (Abschnitt 1) - nur die E-Mail ist auf die schnellen Faelle
    beschraenkt (Nutzer-bestaetigt: kein Interesse an einer Mail fuer JEDEN
    CRV-Treffer, nur an den "hohes Potential bestaetigt"-Sonderfaellen)."""
    if not erfolge:
        return
    try:
        from api.email_notify import send_notification_email

        email_cfg = config_dict.get("benachrichtigung", {}).get("email", {})
        if not email_cfg.get("aktiv", False):
            return
        empfaenger = email_cfg.get("empfaenger")
        if not empfaenger:
            return
        if not config_dict.get("marktscan", {}).get("benachrichtigung_email", False):
            return

        zeilen = []
        for e in erfolge:
            c = e["candidate"]
            anteil_pct = (e["tatsaechliche_dauer_tage"] / e["geschaetzte_dauer_tage"]) * 100
            zeile = (
                f"- {c.symbol} ({c.name}): {e['outcome_return_pct']:+.1f}% erreicht in "
                f"{e['tatsaechliche_dauer_tage']:.1f} Tagen (geschätzt: {e['geschaetzte_dauer_tage']:.1f} Tage, "
                f"{anteil_pct:.0f}% der Schätzung) - Hinweis auf bestätigtes hohes Potential."
            )
            if c.groq_kurzbegruendung:
                zeile += f"\n  KI-Kurzbegründung: {c.groq_kurzbegruendung}"
            zeilen.append(zeile)

        body = (
            f"{len(erfolge)} Marktscan-Kandidat(en) haben ihr Mindestziel ungewöhnlich schnell erreicht:\n\n"
            + "\n".join(zeilen)
            + "\n\nDetails im Marktscan-Tab der App."
        )
        send_notification_email(
            f"TradingInfoTool: {len(erfolge)} Marktscan-Schnellerfolg(e)",
            body,
            empfaenger,
        )
    except Exception:
        logger.exception("Marktscan-Schnellerfolg-E-Mail fehlgeschlagen")


def _ist_email_relevante_richtung(richtung: str | None) -> bool:
    """Richtungs-Filter fuer Hebel-E-Mails (2026-08-05, Schritt 1 des
    Nur-Long-Umbaus).

    ZIEL DES UMBAUS. Der `hebel_richtung_modus`-Schalter soll AUSSCHLIESSLICH
    steuern, was per E-Mail rausgeht und was die GUI zeigt - und sonst gar
    nichts. Bisher greift er an drei Stellen TIEF in die Verarbeitung ein:
    zwei Vorfilter im Budget-Allocator werfen SHORT-Kandidaten schon vor dem
    LLM-Aufruf weg, und ein Veto im Risk-Gate dreht `action` nachtraeglich auf
    HALTEN. Beides verfaelscht die Messung: 313 SHORT-Vorschlaege liegen
    seither als "HALTEN" in der Datenbank und haben bei der Ursachensuche zum
    31.07.-Bruch wiederholt Populationen vermischt.

    WARUM DIESER SCHRITT ZUERST KOMMT. Solange die beiden Vorfilter und der
    Veto noch greifen, erreicht diese Funktion gar keinen SHORT-Vorschlag -
    sie aendert also zunaechst NICHTS und laesst sich trotzdem vollstaendig
    testen. Erst wenn das Netz haelt, werden die drei Eingriffe entfernt.

    WARUM NICHT IN _ist_email_relevantes_asset(): jene Funktion filtert nach
    SYMBOL und wird von Spot, Hebel und Multi-Asset gemeinsam genutzt. Eine
    Richtungspruefung gehoert dort nicht hinein - Spot-Signale haben keine
    Hebel-Richtung, und eine gemeinsame Funktion mit zwei unabhaengigen
    Zustaendigkeiten waere genau die Vermischung, die wir gerade aufloesen.

    KEIN VETO, KEINE ZUSTANDSAENDERUNG. Diese Funktion entscheidet nur ueber
    den Versand. Das Signal bleibt in der Datenbank vollstaendig erhalten -
    mit seiner echten `richtung` und seiner echten `action` - und wird
    normal weiterverfolgt und gemessen.

    DIE RECHNUNG STEHT SEIT DEM 15.08.2026 IN `agent/asset_schalter.py`, bei
    den uebrigen Nutzerschaltern. Grund: die Rollen-Kette verschickt ueber ihr
    eigenes `versand` und lief hier vorbei - ein SHORT der neuen Kette waere
    trotz `nur_long` hinausgegangen. Sie dort nachzubauen waere die
    Kopierfalle gewesen; jetzt fragen beide Ketten dieselbe Stelle. Dieser
    Name bleibt, weil ein Dutzend Kommentare im Projekt auf ihn verweist."""
    from agent.asset_schalter import mail_richtung_erlaubt

    return mail_richtung_erlaubt(richtung)


def _ist_email_relevantes_asset(
    symbol: str, watchlist: list, bitpanda_assets: list | None, conn_factory=None,
) -> bool:
    """Bitpanda-Listing-Filter (2026-07-14, In-App-Schalter, siehe ui/app.py::
    _toggle_email_nur_bitpanda(), Standard AN) - Umsetzung erfolgt manuell ueber
    die Bitpanda-App, eine Empfehlung fuer ein dort nicht gelistetes Asset waere
    also ohnehin nicht direkt ausfuehrbar. Nachtrag 2026-07-28: Schalter-Wert
    liegt jetzt in config.yaml statt data/settings.json (siehe Regelwerksmanual-
    Nachtrag "Nur-Long-Deckel") - config.py hat wie ui/settings.py vorher keine
    tkinter-Abhaengigkeit, deshalb weiterhin ohne Probleme aus dem Hintergrund-
    Job lesbar.

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
    import config as config_module

    # Aus config.yaml (nicht mehr data/settings.json, 2026-07-28 Migration -
    # siehe Regelwerksmanual-Nachtrag "Nur-Long-Deckel").
    nur_bitpanda_gelistet = config_module.load_config().get("benachrichtigung", {}).get(
        "email", {}
    ).get("nur_bitpanda_gelistet", True)
    if not nur_bitpanda_gelistet:
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


# 2026-07-26 (echter Folge-Fund, Nutzer-Screenshot GUI vs. E-Mail): nach
# ui/formatting.py::format_zeitpunkt_lokal() verschoben - der 2026-07-21-Fix
# lebte nur hier und wurde nie von der App-GUI verwendet, wodurch dieselbe
# optische 2-Stunden-Luecke dort weiterhin auftrat. Re-Export unter dem alten
# Namen, damit die 3 bestehenden Aufrufstellen unten unveraendert bleiben.
from ui.formatting import (
    format_zeitpunkt_lokal as _formatiere_zeitpunkt_lokal,
    risikofaktoren_hinweis as _risikofaktoren_hinweis,
)


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
    Ausloeser).

    Regelwerk-Audit Stufe 3, Punkt 3 (2026-07-29): Eintraege mit `ist_kontext`
    (aktuell nur Regime-Konflikt/-Ausrichtung) erscheinen VOR den gezaehlten
    Warnungen als eigene Kontext-Zeile ohne ▲/▼/●-Symbol - siehe
    ui/formatting.py::format_risikofaktoren_lines()-Docstring fuer die volle
    Begruendung (spiegelt dieselbe Logik fuer den E-Mail-Textkontext)."""
    import json

    if not signal.risikofaktoren_json:
        return ""
    try:
        faktoren = json.loads(signal.risikofaktoren_json)
    except (ValueError, TypeError):
        return ""
    if not faktoren:
        return ""

    zeilen = [
        f"--- {f.get('name', '')}: {f.get('begruendung', '')} ---"
        for f in faktoren if f.get("ist_kontext", False)
    ]

    gruppen: dict[str, list[dict]] = {"negativ": [], "neutral": [], "positiv": []}
    for f in faktoren:
        if f.get("ist_kontext", False):
            continue
        gruppen.setdefault(f.get("bewertung", "neutral"), []).append(f)

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


_FAZIT_SYMBOL = {"ja": "▲", "mit_vorbehalt": "●", "nein": "▼"}


def _formatiere_fazit(signal) -> str:
    """Signal-Fazit (2026-07-25, abschliessendes LLM-Synthese-Verdikt, siehe
    Signal.fazit_folgen-Docstring und Memory feedback_llm_synthese_kein_
    deterministischer_override.md) - eigene Kopie wie _formatiere_risiko-
    faktoren() (E-Mail-Textkontext, getrennt von ui/formatting.py::
    format_fazit_lines() fuer die App). Wiederverwendet dieselben ▲/●/▼-
    Symbole wie die Risikofaktoren-Liste, damit dieselbe classify_detail_
    line()/render_detail_html()-Faerbung automatisch greift."""
    if not signal.fazit_folgen:
        return ""
    symbol = _FAZIT_SYMBOL.get(signal.fazit_folgen, "●")
    zeile = f"{symbol} Fazit: {signal.fazit_folgen.replace('_', ' ')} - {signal.fazit_kurzfazit or ''}"
    if signal.fazit_konsistenz_hinweis:
        zeile += f"\n\n⚠ {signal.fazit_konsistenz_hinweis}"
    return zeile


def _formatiere_mindestziel(signal) -> str:
    """Mindestziel-Kurs/Zeitschaetzung (2026-07-27, Performance-Messung-
    Expertenanalyse, Nutzer-Wunsch "das hätte ich gerne im eMail") - Min-Ziel-
    Gegenstueck zur bereits vorhandenen Take-Profit-Zeile (Max-Ziel), plus eine
    rechnerisch angenommene Zeitschaetzung (siehe agent/krypto/backward_
    tracking.py::schaetze_mindestziel_zeitraum_tage() Docstring - kein
    Versprechen, kann verfehlt werden)."""
    from ui.formatting import format_money

    if signal.mindestziel_usd is None:
        return ""
    mindestziel_eur_text = (
        f" ({format_money(signal.mindestziel_eur)} EUR)" if signal.mindestziel_eur is not None else ""
    )
    zeile = (
        f"Mindestziel: {format_money(signal.mindestziel_usd)} USD{mindestziel_eur_text} "
        "(Min-Ziel Richtungstreffer, Take-Profit oben = Max-Ziel)\n"
    )
    if signal.mindestziel_zeitraum_tage_geschaetzt is not None:
        zeile += (
            f"Zeitraum bis Mindestziel: ~{signal.mindestziel_zeitraum_tage_geschaetzt:.1f} Tage "
            "(rechnerisch angenommen aus bisheriger Volatilität, kein Versprechen)\n"
        )
    return zeile


_ZAI_KONSISTENZ_SYMBOL = {"konsistent": "▲", "widerspruch": "▼"}
_ZAI_UEBEREINSTIMMUNG_SYMBOL = {"ja": "▲", "nein": "▼"}


def _formatiere_zai_gegenpruefung(signal) -> str:
    """Z.ai-Gegenpruefung (2026-07-26, siehe agent/krypto/gegenpruefung.py) -
    eigene Kopie wie _formatiere_fazit() (E-Mail-Textkontext, getrennt von
    ui/formatting.py::format_zai_gegenpruefung_lines() fuer die App). Zwei
    unabhaengige Zeilen (Konsistenz-Check der Begruendung gegen Abschnitt 2,
    NICHT gegen das Fazit + eigene, unabhaengig hergeleitete Richtungs-
    einschaetzung im Vergleich zur primaeren Richtung).

    Erweitert (2026-07-27): der Konsistenz-Teil laeuft jetzt auch fuer Signal
    (Spot), siehe agent/krypto/gegenpruefung.py Modul-Docstring "Erweiterung" -
    Signal hat ABER kein zai_eigene_richtung/zai_uebereinstimmung/
    zai_richtung_kurzbegruendung (kein richtung-Konzept bei Spot), deshalb
    hier bewusst getattr() mit Default None statt direktem Attributzugriff -
    funktioniert dadurch unveraendert fuer HebelSignal UND Signal, ohne dass
    Signal diese drei ungenutzten Felder tragen muesste."""
    zeilen = []
    if signal.zai_gegenpruefung_urteil:
        symbol = _ZAI_KONSISTENZ_SYMBOL.get(signal.zai_gegenpruefung_urteil, "●")
        zeilen.append(
            f"{symbol} Z.ai-Gegenprüfung der Begründung: {signal.zai_gegenpruefung_urteil} - "
            f"{signal.zai_gegenpruefung_kurzbegruendung or ''}"
        )
    zai_eigene_richtung = getattr(signal, "zai_eigene_richtung", None)
    if zai_eigene_richtung:
        zai_uebereinstimmung = getattr(signal, "zai_uebereinstimmung", None)
        symbol = _ZAI_UEBEREINSTIMMUNG_SYMBOL.get(zai_uebereinstimmung, "●")
        abgleich_text = (
            "stimmt überein" if zai_uebereinstimmung == "ja"
            else "weicht ab" if zai_uebereinstimmung == "nein"
            else "unklar"
        )
        zeilen.append(
            f"{symbol} Z.ai eigene Richtungseinschätzung: {zai_eigene_richtung} ({abgleich_text}) - "
            f"{getattr(signal, 'zai_richtung_kurzbegruendung', None) or ''}"
        )
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
        fazit_text = _formatiere_fazit(signal)
        zai_text = _formatiere_zai_gegenpruefung(signal)
        mindestziel_text = _formatiere_mindestziel(signal)
        zeitpunkt_text = _formatiere_zeitpunkt_lokal(signal.created_at)
        body = (
            f"Aktion: {signal.action}\n"
            f"Regime: {signal.regime or 'unbekannt'}\n"
            f"Berechnet: {zeitpunkt_text} · Anbieter: {signal.groq_model or '-'}\n\n"
            f"--- 1. MATHEMATISCH BERECHNET ---\n"
            f"Entry: {format_money(signal.entry_eur_von)}-{format_money(signal.entry_eur_bis)} EUR\n"
            f"Stop-Loss: {format_money(signal.stop_loss_eur_von)}-{format_money(signal.stop_loss_eur_bis)} EUR\n"
            f"Take-Profit: {format_money(signal.take_profit_eur_von)}-{format_money(signal.take_profit_eur_bis)} EUR\n"
            f"{mindestziel_text}"
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
            + _risikofaktoren_hinweis(signal, risikofaktoren_text)
            + (f"\n\n{fazit_text}" if fazit_text else "")
            + (f"\n\n{zai_text}" if zai_text else "")
            + "\n\nDetails im Signale-Tab der App. Ausführung manuell über die Bitpanda-App."
        )
        # Liquiditätszonen-Grafik (2026-07-25, von Hebel nachgezogen - siehe
        # _notify_hebel_signal() fuer das Original vom 2026-07-23): derselbe
        # Renderer, baut aus dem bereits im Signal gespeicherten Fakt
        # (facts_json) ein PNG mit konkreten Zahlen/Einheiten. None, wenn keine
        # Zone vorliegt oder der aktuelle Kurs nicht ermittelt werden konnte -
        # Mail geht dann ganz normal ohne Bild raus (kein Hard-Fail wegen der
        # Grafik).
        chart_png = None
        try:
            import json as _json

            from ui.liquidity_chart import render_liquiditaetszonen_chart

            facts = _json.loads(signal.facts_json)
            liquiditaetszonen = facts.get("liquiditaetszonen")
            # BUGFIX (2026-07-25, echter Nutzer-Fund am BTC-Hebel-Signal, gilt
            # identisch fuer Spot): Zonen-/Kursverlauf-Preise im Fakt sind USD-
            # denominiert (liquiditaetszonen_fakt() bekommt price_snap.price_usd/
            # closes-USD), wurden hier aber mit einem EUR-Referenzpreis gemischt
            # und als "EUR" beschriftet - falsche Einheit UND verzerrte Skalierung.
            preis_usd = (facts.get("preis") or {}).get("usd")
            if liquiditaetszonen and preis_usd:
                live_preis_usd = None
                if conn_factory is not None:
                    try:
                        conn = conn_factory()
                        try:
                            live_snap = db.get_latest_prices(conn).get(signal.symbol)
                        finally:
                            conn.close()
                        if live_snap is not None:
                            live_preis_usd = live_snap.price_usd
                    except Exception:
                        logger.exception("Live-Kurs-Nachladung für Kombianzeige (%s) fehlgeschlagen", signal.symbol)
                chart_png = render_liquiditaetszonen_chart(
                    liquiditaetszonen, preis_usd, "USD", live_preis=live_preis_usd,
                )
        except Exception:
            logger.exception("Liquiditätszonen-Grafik für %s fehlgeschlagen", signal.symbol)

        # Signal-Stabilitaets-Grafik (2026-07-25, echter NEAR/LINK-Fund) -
        # gleiches Muster wie die Liquiditaetszonen-Grafik oben, eigenstaendiger
        # zweiter Fakt/Renderer. None, wenn keine ausreichende Historie vorlag.
        stabilitaet_png = None
        try:
            import json as _json

            from ui.signal_stabilitaet_chart import render_signal_stabilitaet_chart

            facts = _json.loads(signal.facts_json)
            signal_stabilitaet = facts.get("signal_stabilitaet")
            if signal_stabilitaet:
                stabilitaet_png = render_signal_stabilitaet_chart(signal_stabilitaet)
        except Exception:
            logger.exception("Signal-Stabilitaets-Grafik für %s fehlgeschlagen", signal.symbol)

        inline_images = []
        if chart_png:
            inline_images.append({"png": chart_png, "alt": "Liquiditätszonen-Grafik", "filename": "liquiditaetszonen.png"})
        if stabilitaet_png:
            inline_images.append({"png": stabilitaet_png, "alt": "Signal-Stabilitäts-Grafik", "filename": "signal_stabilitaet.png"})

        send_notification_email(
            f"TradingInfoTool: {signal.action} {signal.symbol}", body, empfaenger,
            inline_images=inline_images or None,
        )
    except Exception:
        logger.exception("Spot-Empfehlungs-E-Mail für %s fehlgeschlagen", signal.symbol)


_ZAI_EMAIL_WARTE_MAX_SEKUNDEN = 240  # NEUKALIBRIERT (2026-08-05) an echten
# Log-Daten, wie es der vorherige Kommentar selbst gefordert hatte ("bis genug
# echte 3-Call-Faelle fuer eine erneute Log-Auswertung vorliegen").
#
# GEMESSEN, 17 Faelle vom 02.-05.08.:
#     abgeschlossen        14 (82 %)   Median 49,5s   Maximum 105s
#     Zeitlimit gerissen    3          BIO, MON, TAO
#
# HERLEITUNG statt Schaetzung (Methodik 2.8): ein Signal loest DREI
# sequenzielle Z.ai-Calls aus. Reisst EINER davon sein eigenes Limit
# (api/zai.py::REQUEST_TIMEOUT_SECONDS = 150s), brauchen die beiden anderen im
# beobachteten oberen Bereich je rund 45s - macht 150 + 2*45 = 240s. Das deckt
# den haeufigsten Ausfallgrund ab, ohne den strukturellen Extremfall (3*150 =
# 450s) abzuwarten, bei dem Z.ai ohnehin nichts liefern wird.
#
# WARUM DAS NICHTS KOSTET: die Wartefunktion laeuft je Signal in einem EIGENEN
# Thread (_on_signal_ready startet ihn und kehrt sofort zurueck) und das
# Polling steigt aus, SOBALD das Ergebnis da ist. Fuer die 82 %, die
# rechtzeitig fertig werden, aendert sich also gar nichts - verlaengert wird
# nur dort, wo Warten sich lohnt.
#
# ANLASS war ein konkreter Vorfall: am 05.08. ging die TAO-Empfehlung ohne
# Z.ai-Zeilen raus, waehrend Z.ai kurz darauf "widerspruch / eigene Richtung
# SHORT" schrieb - bei einem LONG-Signal. Die vier frueheren Vorfaelle
# kosteten eine Bestaetigung, dieser einen WIDERSPRUCH.
#
# Vorheriger Wert und seine Begruendung, zur Nachvollziehbarkeit: 135 = seit dem
# Positions-Bias-Fix (siehe gegenpruefung.py::leite_eigene_richtung_
# positionsrobust()) macht der Richtungs-Call intern 2 statt 1 sequenzielle
# Z.ai-Calls (Original- + umgekehrte Reihenfolge) - macht 3 statt 2
# sequenzielle Z.ai-Calls pro Signal insgesamt (pruefe_konsistenz() +
# 2x leite_eigene_richtung()). Vorheriger Wert 90s war fuer 2 sequenzielle
# Calls kalibriert (Log-Auswertung 2026-07-28: 8 echte Faelle, 2 Zeitlimit-
# Ueberschreitungen, mehrere knapp am alten 60s-Limit) - proportional
# hochskaliert (90s * 3/2 = 135s) statt neu zu raten, bis genug echte
# 3-Call-Faelle fuer eine erneute Log-Auswertung vorliegen.
_ZAI_EMAIL_POLL_INTERVALL_SEKUNDEN = 3


def _sende_signal_email_mit_zai_wartezeit(
    ergebnis, watchlist: list, bitpanda_assets: list | None, conn_factory,
    required_actions: tuple, get_signal_by_id_fn, notify_fn,
) -> None:
    """Generische Fassung (2026-07-28, Nachtrag zum Z.ai-429-Sturm-Hotfix -
    siehe api/zai.py Modul-Docstring) von urspruenglich `_sende_hebel_email_
    mit_zai_wartezeit()` (Nutzer-Entscheidung 2026-07-26, ausgeloest durch
    einen Screenshot-Fund: die BTC-SHORT-E-Mail zeigte keine Z.ai-Zeilen,
    obwohl die DB zum Versandzeitpunkt bereits ein Urteil hatte). Bewusst
    parametrisiert (`required_actions`/`get_signal_by_id_fn`/`notify_fn`)
    statt dupliziert, da die Logik selbst asset-neutral ist (reine
    Wartemechanik, keine inhaltliche Spot/Hebel-Unterscheidung wie bei den
    Fakten/Regeln) - Krypto-Spot hatte bislang GAR KEINEN Warte- oder
    Re-Fetch-Mechanismus (echter Nutzer-Fund, 2026-07-28): `_notify_spot_
    signal()` bekam das In-Memory-Signal direkt, dessen Z.ai-Felder
    strukturell nie gesetzt sein konnten, da der Z.ai-Hintergrund-Thread
    erst zeitgleich mit dem Callback startet.

    Root Cause des urspruenglichen Funds: `generate_hebel_signal()`/
    `generate_signal()` geben das `signal`-Objekt bewusst zurueck, BEVOR der
    Z.ai-Hintergrund-Thread ueberhaupt fertig ist (siehe dortiger Docstring) -
    das In-Memory-Objekt traegt die Z.ai-Felder also nie, unabhaengig davon,
    wie schnell Z.ai tatsaechlich antwortet.

    Laeuft in einem EIGENEN Hintergrund-Thread (siehe Aufrufstelle in
    _on_signal_ready() unten) - NICHT im Haupt-Callback-Pfad von
    run_budget_allocator(), sonst wuerde genau die Batch-Blockade
    zurueckkehren, die der urspruengliche E-Mail-Latenz-Fix behoben hat
    (project_email_latenz_fix_batch_notification.md: ein einzelner Kandidat
    mit langsamem externen Call durfte NIE nachfolgende, laengst fertige
    Signale in derselben Charge blockieren). Diese Funktion wartet NUR auf
    das EINE Signal, dessen E-Mail sie selbst verschickt - andere
    Kandidaten im selben Lauf sind davon vollstaendig unberuehrt, da
    _on_signal_ready() diesen Thread startet und sofort zurueckkehrt.

    Fruehausstieg vor der Wartezeit fuer HALTEN/nicht-benachrichtigungs-
    relevante Aktionen (Duplikat der Pruefung im jeweiligen `notify_fn`,
    hier VOR der Wartezeit noetig - sonst wuerde fuer den haeufigsten Fall
    ueberhaupt, ein HALTEN-Signal ohne jede E-Mail, unnoetig bis zu 60s in
    einem Thread verbraucht).

    Begrenztes Polling (max. `_ZAI_EMAIL_WARTE_MAX_SEKUNDEN`, alle
    `_ZAI_EMAIL_POLL_INTERVALL_SEKUNDEN`) statt festem Sleep - beendet die
    Wartezeit sofort, sobald beide Z.ai-Calls fertig sind (typische
    Antwortzeit 12-25s je Call, siehe agent/krypto/gegenpruefung.py), statt
    immer das volle Zeitbudget zu verbrauchen. Wird das Limit erreicht (z.B.
    bei einem Z.ai-Timeout von bis zu 150s je Call), geht die E-Mail trotzdem
    OHNE Z.ai-Zeilen raus (P-8, kein Hard-Fail wegen einer optionalen
    Zusatzinfo).

    Fruehausstieg ruft `notify_fn` bewusst TROTZDEM auf (nur OHNE Wartezeit),
    statt komplett zu returnen (2026-07-28, echter Fund beim Verallgemeinern
    auf Spot): `_notify_spot_signal()` prueft `cash_veto` UNABHAENGIG von der
    Aktion (auch bei HALTEN) - ein blanker Return haette diese Warnmail fuer
    Spot-HALTEN-Signale mit `cash_veto` verschluckt. Fuer Hebel aendert das
    nichts (dort hat `_notify_hebel_signal()` denselben HALTEN-Guard ohnehin
    schon selbst, der Aufruf ist ein sicherer No-Op)."""
    if ergebnis.action not in required_actions or ergebnis.action == "HALTEN":
        notify_fn(ergebnis, watchlist, bitpanda_assets, conn_factory)
        return

    angereichertes_signal = ergebnis
    if conn_factory is not None and ergebnis.id is not None:
        gewartet = 0.0
        while gewartet < _ZAI_EMAIL_WARTE_MAX_SEKUNDEN:
            time.sleep(_ZAI_EMAIL_POLL_INTERVALL_SEKUNDEN)
            gewartet += _ZAI_EMAIL_POLL_INTERVALL_SEKUNDEN
            try:
                conn = conn_factory()
                try:
                    frisch = get_signal_by_id_fn(conn, ergebnis.id)
                finally:
                    conn.close()
            except Exception:
                logger.exception(
                    "Nachladen des Signals fuer Z.ai-Wartezeit (%s) fehlgeschlagen", ergebnis.symbol,
                )
                break
            if frisch is not None:
                angereichertes_signal = frisch
                if frisch.zai_gegenpruefung_urteil is not None or frisch.zai_eigene_richtung is not None:
                    logger.info(
                        "Z.ai-Gegenpruefung fuer %s nach %.0fs abgeschlossen (vor E-Mail-Versand)",
                        ergebnis.symbol, gewartet,
                    )
                    break
        else:
            # while-Schleife ohne break durchgelaufen = Zeitlimit erreicht,
            # ohne dass Z.ai fertig wurde (misst genau die Nutzer-Frage nach
            # der realen Pipeline-Dauer LLM Pruefung 1 -> LLM Pruefung 2 fuer
            # kuenftige Signale - bisher gab es dafuer keine Log-Zeile).
            logger.info(
                "Z.ai-Gegenpruefung fuer %s nach %.0fs (Zeitlimit) noch nicht abgeschlossen - "
                "E-Mail geht ohne Z.ai-Zeilen raus", ergebnis.symbol, gewartet,
            )
    notify_fn(angereichertes_signal, watchlist, bitpanda_assets, conn_factory)


def _sende_hebel_email_mit_zai_wartezeit(
    ergebnis, watchlist: list, bitpanda_assets: list | None, conn_factory,
) -> None:
    """Hebel-Fassung von `_sende_signal_email_mit_zai_wartezeit()` - siehe
    dortigen Docstring fuer die volle Begruendung."""
    from agent.krypto.hebel_analyst import REQUIRED_HEBEL_ACTIONS

    _sende_signal_email_mit_zai_wartezeit(
        ergebnis, watchlist, bitpanda_assets, conn_factory,
        required_actions=REQUIRED_HEBEL_ACTIONS,
        get_signal_by_id_fn=db.get_hebel_signal_by_id,
        notify_fn=_notify_hebel_signal,
    )


def _sende_spot_email_mit_zai_wartezeit(
    ergebnis, watchlist: list, bitpanda_assets: list | None, conn_factory,
) -> None:
    """Spot-Fassung von `_sende_signal_email_mit_zai_wartezeit()` (2026-07-28,
    echter Nutzer-Fund: Krypto-Spot hatte bislang WEDER Wartemechanismus
    (wie Hebel) NOCH Re-Fetch (wie Multi-Asset-Batch) - `_notify_spot_
    signal()` bekam das In-Memory-Signal direkt und konnte dessen Z.ai-Felder
    strukturell nie tragen). Siehe Haupt-Docstring fuer die volle
    Begruendung."""
    from agent.krypto.analyst import REQUIRED_ACTIONS

    _sende_signal_email_mit_zai_wartezeit(
        ergebnis, watchlist, bitpanda_assets, conn_factory,
        required_actions=REQUIRED_ACTIONS,
        get_signal_by_id_fn=db.get_signal_by_id,
        notify_fn=_notify_spot_signal,
    )


def _sende_multi_asset_email_mit_zai_wartezeit(
    ergebnis, watchlist: list, bitpanda_assets: list | None, conn_factory,
) -> None:
    """Multi-Asset-Fassung (Aktien/Rohstoffe/Themen-ETF/Hedge) von
    `_sende_signal_email_mit_zai_wartezeit()` - siehe dortigen Docstring fuer
    die volle Begruendung. Ersetzt den bisherigen einmaligen Re-Fetch in
    `multi_asset_batch_job()` (2026-07-27, Nachtrag "E-Mail: Re-Fetch statt
    Hebel-artigem Wartemechanismus"): jener Ansatz nahm bewusst in Kauf, dass
    NUR "die meisten" (nicht alle) Signale rechtzeitig fertig sind, weil die
    Restlaufzeit des restlichen Batches als Puffer diente. Echter Fund
    (2026-07-31, Nutzer-Screenshot: S&P-Hedge-VERKAUFEN-E-Mail komplett ohne
    Z.ai-Zeilen) zeigte den Fall, in dem der Puffer nicht ausreichte.
    `REQUIRED_ACTIONS` ist bei allen 4 Multi-Asset-Analysten identisch
    (`agent.aktien/rohstoff/themen_etf/hedge.analyst`, jeweils ("KAUFEN",
    "VERKAUFEN", "HALTEN", "NACHKAUFEN")) - hier direkt inline statt eines
    beliebig wirkenden Imports aus nur einem der vier Module."""
    _sende_signal_email_mit_zai_wartezeit(
        ergebnis, watchlist, bitpanda_assets, conn_factory,
        required_actions=("KAUFEN", "VERKAUFEN", "HALTEN", "NACHKAUFEN"),
        get_signal_by_id_fn=db.get_signal_by_id,
        notify_fn=_notify_multi_asset_signal,
    )


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
    # Richtungs-Filter (2026-08-05, siehe _ist_email_relevante_richtung()).
    # Solange die Vorfilter im Budget-Allocator und der Veto im Risk-Gate noch
    # greifen, kommt hier nie ein SHORT-Vorschlag an - die Zeile ist bis dahin
    # wirkungslos und bewusst so gebaut: erst das Netz, dann der Sprung.
    if not _ist_email_relevante_richtung(getattr(signal, "richtung", None)):
        logger.info(
            "Hebel-E-Mail fuer %s (%s) unterdrueckt - hebel_richtung_modus=nur_long. "
            "Das Signal bleibt vollstaendig erhalten und wird weiter gemessen.",
            signal.symbol, getattr(signal, "richtung", "?"),
        )
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
        eigenkapital_deckel_zeile = (
            f"  ({signal.eigenkapital_deckel_hinweis})\n" if signal.eigenkapital_deckel_hinweis else ""
        )
        eigenkapital_zeile = (
            f"Eigenkapitalbedarf: {format_money(signal.eigenkapitalbedarf_usd)} USD{eigenkapital_eur_text}\n"
            f"{eigenkapital_deckel_zeile}"
            if signal.eigenkapitalbedarf_usd is not None else ""
        )
        senkung_zeile = (
            f"Eigenkapital-Nachschuss für Hebel-Senkung: "
            f"{format_money(signal.hebel_senkung_eigenkapital_nachschuss_eur)} EUR\n"
            if signal.hebel_senkung_eigenkapital_nachschuss_eur is not None else ""
        )
        korrektur_zeile = f"({signal.hebel_korrektur_hinweis})\n" if signal.hebel_korrektur_hinweis else ""
        # BUGFIX (2026-07-24, aufgefallen bei der Kontrathese-Uebersetzung, aber
        # unabhaengig davon bestehend): hebel_final ist None bei SCHLIESSEN/
        # TEILVERKAUF/HALTEN - ohne Schutz stand hier woertlich "Hebel: Nonex".
        hebel_zeile = f"{signal.hebel_final:.2f}x" if signal.hebel_final is not None else "-"
        # Kontrathese-Uebersetzung (2026-07-24): Zonen bleiben unveraendert aus
        # dem Original-LLM-Vorschlag (siehe HebelSignal.kontrathese_zu_position-
        # Docstring), aber anders beschriftet - kein neuer Einstieg auf die
        # bestehende Position, sondern der nie ausgefuehrte Gegenrichtungs-
        # Vorschlag, der zur Uebersetzung fuehrte.
        zonen_titel = (
            f"Referenzzonen der Kontrathese (ursprünglicher {signal.kontrathese_llm_richtung}-Vorschlag, "
            "kein neuer Einstieg):"
            if signal.kontrathese_zu_position else "Entry/Stop-Loss/Take-Profit:"
        )
        risiken_text = _formatiere_key_risks(signal)
        halte_kriterium_text = _formatiere_halte_kriterium(signal)
        gegenargument_text = _formatiere_gegenargument(signal)
        forecast_text = _formatiere_forecast(signal)
        risikofaktoren_text = _formatiere_risikofaktoren(signal)
        fazit_text = _formatiere_fazit(signal)
        zai_text = _formatiere_zai_gegenpruefung(signal)
        mindestziel_text = _formatiere_mindestziel(signal)
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
            f"Hebel: {hebel_zeile}\n"
            f"{korrektur_zeile}"
            f"{zonen_titel}\n"
            f"Entry: {format_money(signal.entry_eur_von)}-{format_money(signal.entry_eur_bis)} EUR\n"
            f"Stop-Loss: {format_money(signal.stop_loss_eur_von)}-{format_money(signal.stop_loss_eur_bis)} EUR\n"
            f"Take-Profit: {format_money(signal.take_profit_eur_von)}-{format_money(signal.take_profit_eur_bis)} EUR\n"
            f"{mindestziel_text}"
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
            + _risikofaktoren_hinweis(signal, risikofaktoren_text)
            + (f"\n\n{fazit_text}" if fazit_text else "")
            + (f"\n\n{zai_text}" if zai_text else "")
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
            # BUGFIX (2026-07-24, siehe ui/hebel_view.py::_render_liquiditaetszonen_
            # chart()-Kommentar fuer den vollen Root-Cause): denselben Preis wie
            # `kursverlauf` verwenden (zum Erstellungszeitpunkt dieses Signals
            # eingebettet) statt einer separat nachgeladenen Live-Notierung -
            # verhindert eine "Aktueller Kurs"-Linie, die nicht zum Ende der
            # Kursverlauf-Linie passt, spart ausserdem den DB-Zugriff hier
            # komplett ein.
            # BUGFIX (2026-07-25, echter Nutzer-Fund am BTC-Hebel-Signal): die
            # Zonen-/Kursverlauf-Preise im Fakt sind USD-denominiert
            # (liquiditaetszonen_fakt() bekommt price_usd/closes-USD, siehe
            # hebel_pipeline.py), wurden hier aber mit einem EUR-Referenzpreis
            # gemischt und als "EUR" beschriftet - falsche Einheit UND
            # verzerrte Chart-Skalierung. USD durchgaengig statt EUR.
            preis_usd = (facts.get("preis") or {}).get("usd")
            if liquiditaetszonen and preis_usd:
                # Kombianzeige (2026-07-24, Nutzer-Wunsch): zusaetzlich zum
                # Analysezeitpunkt-Preis den LIVE-Preis nachladen (macht bei
                # der E-Mail meist keinen grossen Unterschied, da sie kurz
                # nach der Signal-Erstellung verschickt wird - aber dieselbe
                # Grafik-Funktion wie die App nutzt, daher konsistent
                # mitgegeben). Schlaegt der Abruf fehl, bleibt live_preis_usd
                # None - Chart faellt automatisch auf die reine
                # Analysezeitpunkt-Ansicht zurueck.
                live_preis_usd = None
                if conn_factory is not None:
                    try:
                        conn = conn_factory()
                        try:
                            live_snap = db.get_latest_prices(conn).get(signal.symbol)
                        finally:
                            conn.close()
                        if live_snap is not None:
                            live_preis_usd = live_snap.price_usd
                    except Exception:
                        logger.exception("Live-Kurs-Nachladung für Kombianzeige (%s) fehlgeschlagen", signal.symbol)
                chart_png = render_liquiditaetszonen_chart(
                    liquiditaetszonen, preis_usd, "USD", live_preis=live_preis_usd,
                )
        except Exception:
            logger.exception("Liquiditätszonen-Grafik für %s fehlgeschlagen", signal.symbol)

        # Signal-Stabilitaets-Grafik (2026-07-25, echter NEAR/LINK-Fund) -
        # gleiches Muster wie die Liquiditaetszonen-Grafik oben, eigenstaendiger
        # zweiter Fakt/Renderer. None, wenn keine ausreichende Historie vorlag.
        stabilitaet_png = None
        try:
            import json as _json

            from ui.signal_stabilitaet_chart import render_signal_stabilitaet_chart

            facts = _json.loads(signal.facts_json)
            signal_stabilitaet = facts.get("signal_stabilitaet")
            if signal_stabilitaet:
                stabilitaet_png = render_signal_stabilitaet_chart(signal_stabilitaet)
        except Exception:
            logger.exception("Signal-Stabilitaets-Grafik für %s fehlgeschlagen", signal.symbol)

        inline_images = []
        if chart_png:
            inline_images.append({"png": chart_png, "alt": "Liquiditätszonen-Grafik", "filename": "liquiditaetszonen.png"})
        if stabilitaet_png:
            inline_images.append({"png": stabilitaet_png, "alt": "Signal-Stabilitäts-Grafik", "filename": "signal_stabilitaet.png"})

        send_notification_email(
            f"TradingInfoTool: Hebel {signal.action} {signal.symbol} ({signal.richtung})", body, empfaenger,
            inline_images=inline_images or None,
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
        fazit_text = _formatiere_fazit(signal)
        # BUGFIX (2026-07-30, Nutzer-Fund am echten 3QSS-Fall): _notify_spot_
        # signal() ruft _formatiere_zai_gegenpruefung() bereits seit dessen
        # Einfuehrung auf - hier fehlte der Aufruf schlicht, obwohl die
        # Z.ai-Ausweitung auf alle 4 Multi-Asset-Batch-Pipelines (Aktien/
        # Rohstoffe/Themen-ETF/Hedge, 2026-07-27) die Daten laengst berechnet
        # und per Re-Fetch (Commit 10) korrekt in `signal` nachlaedt - nur die
        # E-Mail-Vorlage selbst hat den Text nie angehaengt. Betraf alle 4
        # Pipelines, nicht nur Hedge (dort nur zuerst bemerkt).
        zai_text = _formatiere_zai_gegenpruefung(signal)
        mindestziel_text = _formatiere_mindestziel(signal)
        zeitpunkt_text = _formatiere_zeitpunkt_lokal(signal.created_at)
        body = (
            f"Aktion: {signal.action}\n"
            f"Regime: {signal.regime or 'unbekannt'}\n"
            f"Berechnet: {zeitpunkt_text} · Anbieter: {signal.groq_model or '-'}\n\n"
            f"--- 1. MATHEMATISCH BERECHNET ---\n"
            f"Entry: {format_money(signal.entry_eur_von)}-{format_money(signal.entry_eur_bis)} EUR\n"
            f"Stop-Loss: {format_money(signal.stop_loss_eur_von)}-{format_money(signal.stop_loss_eur_bis)} EUR\n"
            f"Take-Profit: {format_money(signal.take_profit_eur_von)}-{format_money(signal.take_profit_eur_bis)} EUR\n"
            f"{mindestziel_text}"
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
            + _risikofaktoren_hinweis(signal, risikofaktoren_text)
            + (f"\n\n{fazit_text}" if fazit_text else "")
            + (f"\n\n{zai_text}" if zai_text else "")
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
    mistral_client=None, zai_client=None, openrouter_client=None,
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
    einer von mistral_client/gemini_client/zai_client gesetzt ist, sonst
    uebersprungen).

    **2026-07-17:** Cerebras vollstaendig aus der Fallback-Kette entfernt
    (Mistral hat dessen Rolle uebernommen, siehe Memory
    project_cerebras_free_tier_aenderung_2026-08-16.md - urspruenglich war
    nur die Entfernung zum 2026-08-16 geplant, der Nutzer hat sich aber
    bewusst fuer die sofortige vollstaendige Entfernung entschieden).

    **2026-07-26:** Groq ebenfalls vollstaendig entfernt (reproduzierter Test
    zeigte "413 Payload Too Large" bei 2/3 echten Signal-Payloads - Free-Tier-
    Kontextlimit reicht fuer den inzwischen stark gewachsenen Fakten-Umfang
    pro Signal nicht mehr aus, zudem 0 jemals aufgeloeste Signale in
    provider_performance seit Mistral Prio-1 ist). Mistral/Gemini/Z.ai decken
    die Kette jetzt allein ab."""
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

        # 2026-07-26 (Groq-Entfernung): frueher an "groq_client is not None"
        # gegated, weil Groq urspruenglich die einzige zwingende Voraussetzung
        # war. Jetzt gilt Mistral/Gemini/Zai als Basis (mind. einer muss
        # gesetzt sein) - Groq ist komplett aus der Kette entfernt.
        # 2026-08-09 (C4): openrouter_client gehoert mit ins Gate. Ohne ihn
        # bliebe der Allocator stehen, wenn OpenRouter der EINZIGE konfigurierte
        # Analyst ist - ein Zustand, den der Hard Switch moeglich macht.
        # DER SCHNITT (14.08.2026). Ist Krypto auf die Rollen-Kette umgestellt,
        # laeuft der Allocator fuer diese Klasse NICHT MEHR - sonst gaebe es
        # fuer dasselbe Asset zwei Empfehlungen, und der Nutzer muesste
        # entscheiden, welcher er glaubt. Genau das war der Grund fuer den
        # glatten Schnitt.
        #
        # Der Schalter steht in `config.yaml` unter `rollen_kette.aktiv_fuer`.
        # Vorgabe ist LEER: das blosse Einspielen dieses Codes stellt nichts um.
        from scheduler.rollen_job import bedient_neue_kette
        # `config_dict` heisst die Variable in diesem Gueltigkeitsbereich -
        # nachgesehen, nicht geraten.
        # IRGENDEINE GRUPPE GENUEGT (15.08.2026) - vorher stand hier fest
        # "krypto". Solange nur Krypto umgestellt war, machte das keinen
        # Unterschied; ab dem Vollumstieg schon: waere Krypto eines Tages
        # abgeschaltet und Aktien nicht, liefe der Umlauf gar nicht mehr an -
        # lautlos, denn der Allocator uebernaehme wieder.
        #
        # WELCHE GRUPPE DANN WIRKLICH LAEUFT, entscheidet `fuehre_umlauf`
        # ohnehin je Gruppe. Diese Zeile ist nur die Frage, ob ueberhaupt
        # etwas umgestellt ist.
        from agent import assetklassen as _AK2

        if any(bedient_neue_kette(g, config_dict)
               for g in {g for g, _, _ in _AK2.laeufe()}):
            # UND SIE LAEUFT AUCH WIRKLICH. Die erste Fassung hat den alten Weg
            # nur UEBERSPRUNGEN - der Schalter haette damit gar nichts laufen
            # lassen, und zwar lautlos: kein Fehler, keine Signale, kein Grund.
            # Gefunden beim Umlegen selbst.
            from scheduler.rollen_job import betriebsart_aus_config, fuehre_umlauf
            art = betriebsart_aus_config(config_dict)
            logger.info(
                "Budget-Allocator uebersprungen - die umgestellten Bereiche "
                "laufen ueber die Rollen-Kette (%s). Eine Klasse, eine Kette.",
                art)
            # EIN UMLAUF UEBER ALLE UMGESTELLTEN BEREICHE, nicht eine feste
            # Liste ("spot", "hebel"). Welche Bereiche es gibt, steht in
            # `assetklassen.laeufe()`; welche umgestellt sind, in der
            # Konfiguration. Jede Gruppe ist einzeln geschuetzt.
            #
            # ALLE TOEPFE UEBERGEBEN, nicht einen Client: welcher dran ist,
            # entscheidet das Restkontingent, und diese Entscheidung gehoert an
            # EINE Stelle (`rollen_job.waehle_client`).
            fuehre_umlauf(
                conn_factory=conn_factory, config=config_dict,
                clients={"gemini": gemini_client,
                         "openrouter": openrouter_client,
                         # Ein Topf, den niemand uebergibt, wird uebersprungen
                         # (`waehle_client` prueft auf None). Die Kette zu
                         # erweitern und den Client zu vergessen waere eine
                         # Reaktivierung, die nur auf dem Papier stattfindet.
                         "groq": groq_client},
                zai_client=zai_client, betriebsart=art)
        elif any(c is not None for c in (mistral_client, gemini_client, zai_client, openrouter_client)):
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
                    if zai_client is not None:
                        # Begrenzte Wartezeit auf die Z.ai-Gegenpruefung in
                        # einem EIGENEN Thread (2026-07-26, Nutzer-Entscheidung
                        # gegen die Standard-Empfehlung "nur GUI") - siehe
                        # _sende_hebel_email_mit_zai_wartezeit()-Docstring.
                        # Blockiert NICHT diesen Callback/den Allocator-Loop,
                        # andere Kandidaten im selben Batch werden weiterhin
                        # sofort benachrichtigt (E-Mail-Latenz-Fix bleibt intakt).
                        threading.Thread(
                            target=_sende_hebel_email_mit_zai_wartezeit,
                            args=(ergebnis, watchlist, bitpanda_assets, conn_factory),
                            daemon=True,
                        ).start()
                    else:
                        _notify_hebel_signal(ergebnis, watchlist, bitpanda_assets, conn_factory)
                elif schluessel.startswith("spot:"):
                    if zai_client is not None:
                        # Analog zum Hebel-Zweig oben (2026-07-28, Nachtrag -
                        # echter Nutzer-Fund: Spot hatte bislang KEINEN Warte-
                        # oder Re-Fetch-Mechanismus, siehe _sende_spot_email_
                        # mit_zai_wartezeit()-Docstring). Eigener Hintergrund-
                        # Thread, blockiert andere Kandidaten im selben Batch
                        # nicht.
                        threading.Thread(
                            target=_sende_spot_email_mit_zai_wartezeit,
                            args=(ergebnis, watchlist, bitpanda_assets, conn_factory),
                            daemon=True,
                        ).start()
                    else:
                        _notify_spot_signal(ergebnis, watchlist, bitpanda_assets, conn_factory)
                elif schluessel.startswith("marktscan:"):
                    # Mail 1 (2026-07-30, schliesst eine bisher bestehende Luecke):
                    # dieser Zweig fehlte bisher komplett - `on_signal_ready()`
                    # feuerte fuer Marktscan-Tier2-Writeups schon seit dem E-Mail-
                    # Latenz-Fix (2026-07-23), landete aber nie in einem Dispatcher-
                    # Zweig. Kein Z.ai-Wartemechanismus noetig (Marktscan-Writeups
                    # nutzen Z.ai nicht in der Fallback-Kette, siehe budget_
                    # allocator.py Tier-2-Kommentar).
                    _notify_marktscan_writeup(ergebnis, config_dict)

            allocation = run_budget_allocator(
                conn_factory, watchlist, coingecko_client, kraken_client,
                fred_api_key, config_dict, gemini_client=gemini_client, mistral_client=mistral_client,
                zai_client=zai_client, on_signal_ready=_on_signal_ready,
                openrouter_client=openrouter_client,
            )
            logger.info(
                "Budget-Allocator: Hebel %d, Marktscan %d, Spot %d verarbeitet, %d fehlgeschlagen, "
                "Calls je Anbieter %s, Budget erschöpft: %s",
                len(allocation.hebel_verarbeitet), len(allocation.marktscan_verarbeitet),
                len(allocation.spot_verarbeitet), len(allocation.fehlgeschlagen),
                dict(allocation.calls_verbraucht) or "keine",
                dict(allocation.budget_erschoepft) or "keiner",
            )
        else:
            logger.info(
                "Budget-Allocator übersprungen (kein Mistral-/Gemini-/OpenRouter-/Z.ai-Client konfiguriert)")
    except Exception as exc:
        logger.exception("Hebel-Screening fehlgeschlagen")
        _notify_job_failure("hebel_screening", f"Hebel-Screening fehlgeschlagen: {exc}")
    finally:
        hebel_screening_lock.release()
        _job_started_at.pop("hebel_screening", None)
    return True


def multi_asset_batch_job(
    conn_factory, watchlist_provider, coingecko_client, gemini_client=None, mistral_client=None,
    zai_client=None, openrouter_client=None,
) -> bool:
    """Multi-Asset-Batch (2026-07-18, siehe agent/multi_asset_batch.py Modul-
    Docstring fuer die volle Architektur-Begruendung) - automatische Signal-
    Erzeugung fuer Aktien/Rohstoffe/Hedge, bisher nur manuell per Klick
    erreichbar. P-8: nur aktiv, wenn mindestens einer von mistral_client/
    gemini_client gesetzt ist (gleiches Muster wie hebel_screening_job();
    Groq 2026-07-26 vollstaendig entfernt, siehe dortige Begruendung).
    `zai_client` (Nachtrag, Ausweitung der Z.ai-Gegenpruefung auf alle
    Assetklassen) allein aktiviert den Batch NICHT - ohne Mistral/Gemini
    gaebe es keine primaere Analyse und damit keine Fakten fuer Z.ai.
    `watchlist_provider` siehe refresh_prices_job()-Docstring (2026-07-23)."""
    if not multi_asset_batch_lock.acquire(blocking=False):
        logger.info("Multi-Asset-Batch: bereits in Ausführung - übersprungen")
        return False
    watchlist = watchlist_provider()
    _job_started_at["multi_asset_batch"] = time.monotonic()
    try:
        # DER SCHNITT GILT AUCH HIER (15.08.2026) - er tat es bis heute NICHT.
        #
        # GEFUNDEN BEI DER GEGENPRUEFUNG ZUM VOLLUMSTIEG. `bedient_neue_kette`
        # stand an genau EINER Stelle, in `hebel_screening_job`, und dort fest
        # auf "krypto". Dieser Job hier - der Aktien, Rohstoffe, Themen-ETF und
        # die Absicherung bedient - kannte den Schnitt gar nicht.
        #
        # `aktiv_fuer` auf alle sechs zu setzen haette damit nicht umgestellt,
        # sondern VERDOPPELT: die Rollen-Kette im 15-Minuten-Takt und dieser
        # Batch um 9 und 19 Uhr, beide auf dieselben Symbole, beide mit
        # Modellaufrufen und beide mit Mail. Genau der Parallelbetrieb, den der
        # Nutzer am 13.08. ausgeschlossen hat: "das aktuelle System ist tot und
        # wir stellen in einem Zug und mit glattem Schnitt um."
        #
        # GEPRUEFT WIRD JE GRUPPE, nicht pauschal: solange EINE der vier noch
        # auf der alten Kette steht, laeuft der Batch fuer sie weiter.
        import config as _cfgm
        from agent import assetklassen as _AK
        from scheduler.rollen_job import bedient_neue_kette as _neu

        _cfg = _cfgm.load_config()
        _meine = {"aktien", "rohstoffe", "themen_etf", "hedge"}
        _offen = sorted(g for g in _meine if not _neu(g, _cfg))
        if not _offen:
            logger.info(
                "Multi-Asset-Batch uebersprungen - alle vier Bereiche laufen "
                "ueber die Rollen-Kette. Eine Klasse, eine Kette.")
            return True
        if len(_offen) < len(_meine):
            logger.info(
                "Multi-Asset-Batch laeuft nur noch fuer %s - die uebrigen "
                "sind auf die Rollen-Kette umgestellt.", ", ".join(_offen))
        # 2026-08-09 (C4): openrouter_client gehoert mit ins Gate - sonst
        # stuende der Batch still, wenn OpenRouter der einzige konfigurierte
        # Analyst ist.
        if mistral_client is None and gemini_client is None and openrouter_client is None:
            logger.info(
                "Multi-Asset-Batch übersprungen (kein Mistral-/Gemini-/OpenRouter-Client konfiguriert)")
            return True

        import config as config_module
        from agent.multi_asset_batch import run_multi_asset_batch

        config_dict = config_module.load_config()
        result = run_multi_asset_batch(
            conn_factory, watchlist, coingecko_client, config_dict,
            gemini_client=gemini_client, mistral_client=mistral_client, zai_client=zai_client,
            openrouter_client=openrouter_client,
        )
        # Nachhol-Mechanismus (2026-07-30, siehe multi_asset_batch_catchup_if_missed()):
        # erst NACH erfolgreichem Abschluss von run_multi_asset_batch() gesetzt - bricht
        # der Prozess vorher ab (z.B. Neustart mitten im Batch, echter Fall 29.07.),
        # bleibt der alte Zeitstempel stehen und der naechste Start holt den Termin nach.
        last_run_conn = conn_factory()
        try:
            db.set_multi_asset_batch_last_run_iso(last_run_conn, datetime.now().isoformat())
        finally:
            last_run_conn.close()
        # `budget_erschoepft` steht seit 2026-08-09 (C3) mit in der Zeile - der
        # Krypto-Allocator loggt es laengst, hier fehlte es. Ein Feld zu fuellen,
        # das niemand liest, waere eine stille Attrappe; und eine UEBERSPRUNGENE
        # Stufe ist von aussen sonst nicht von einer GESCHEITERTEN zu
        # unterscheiden.
        logger.info(
            "Multi-Asset-Batch: %d verarbeitet, %d fehlgeschlagen, %d Cooldown-uebersprungen, "
            "%d wegen Schwerpunkt vorgezogen, Calls je Anbieter %s, Budget erschöpft: %s",
            len(result.verarbeitet), len(result.fehlgeschlagen), result.uebersprungen_cooldown,
            result.vorgezogen_schwerpunkt,
            dict(result.calls_verbraucht) or "keine",
            dict(result.budget_erschoepft) or "keiner",
        )
        if result.ergebnis_objekt:
            try:
                from api.bitpanda import get_listed_assets

                bitpanda_assets = get_listed_assets()
            except Exception as exc:
                bitpanda_assets = None
                logger.info("Bitpanda-Listing-Abruf für Multi-Asset-Empfehlungs-E-Mails fehlgeschlagen: %s", exc)
            for signal in result.ergebnis_objekt.values():
                # Wartemechanismus statt reinem Re-Fetch (2026-07-31, Nachtrag -
                # echter Fund: eine S&P-Hedge-VERKAUFEN-E-Mail hatte trotz
                # unbedingtem Z.ai-Aufruf gar keine Z.ai-Zeilen, siehe
                # _sende_multi_asset_email_mit_zai_wartezeit()-Docstring fuer
                # die volle Begruendung. Eigener Hintergrund-Thread pro Signal
                # (wie bei Hebel/Spot in _on_signal_ready()) blockiert die
                # anderen Signale in dieser Schleife NICHT - sie startet nur
                # Threads und kehrt sofort zurueck, der E-Mail-Latenz-Fix
                # bleibt dadurch unberuehrt.
                if zai_client is not None:
                    threading.Thread(
                        target=_sende_multi_asset_email_mit_zai_wartezeit,
                        args=(signal, watchlist, bitpanda_assets, conn_factory),
                        daemon=True,
                    ).start()
                else:
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


def _preis_daten_veraltet(conn, watchlist) -> tuple[int, int]:
    """(veraltete Preise, geprueft) - PUNKT 1 der Untersuchung vom 12.08.

    WARUM ES DAS BISHER NICHT GAB. Der Staleness-Watchdog prueft seit 23.07.
    die Kurs-Historie und die Kraken-OHLC-Reihen. Den PREIS-CACHE prueft er
    nicht - und genau der ist am 19.07. stehengeblieben. Am 21.07. wurden
    daraufhin 42 von 42 Assets am P-10-Gate abgewiesen, kein einziger
    LLM-Aufruf fand statt, und niemand hat es gemerkt.

    Das ist derselbe Vorfall wie der, der den Watchdog ueberhaupt ausgeloest
    hat (siehe STALENESS_RECHECK_INTERVAL_MINUTES: 390 Signale in einer Nacht).
    Damals wurde die Historie abgesichert - der Preis-Cache blieb offen.

    Anders als bei Historie und OHLC wird hier GEZAEHLT statt beim ersten
    Treffer abgebrochen: ob ein Asset veraltet ist oder alle, ist der
    Unterschied zwischen einem Einzelausfall und einem Totalausfall, und nur
    der zweite rechtfertigt eine Nachricht."""
    try:
        preise = db.get_latest_prices(conn)
        veraltet = gesamt = 0
        for asset in watchlist:
            schnappschuss = preise.get(asset.symbol)
            gesamt += 1
            if schnappschuss is None or staleness.is_price_stale(schnappschuss.fetched_at):
                veraltet += 1
        return veraltet, gesamt
    except Exception:
        logger.exception("Staleness-Check fuer den Preis-Cache fehlgeschlagen")
        return 0, 0


# PUNKT 2: ein Lauf, der ALLES abweist, ist eine Meldung wert.
#
# Bisher war ein Lauf ohne Signale von einem Lauf ohne Gelegenheiten nicht zu
# unterscheiden - beides ist Stille. Genau deshalb blieb der 21.07. unsichtbar.
# Gemeldet wird NUR der Totalausfall, und nur einmal je Sperrfrist: eine
# Nachricht, die bei jedem einzelnen veralteten Asset feuert, wird nach drei
# Tagen weggeklickt und ist dann auch still.
DATENAUSFALL_SPERRE_MINUTEN = 180
_datenausfall_zuletzt: float | None = None


def _melde_datenausfall(veraltet: int, gesamt: int) -> bool:
    """True, wenn eine Nachricht rausging."""
    global _datenausfall_zuletzt
    if gesamt < 3 or veraltet < gesamt:
        return False
    if (_datenausfall_zuletzt is not None
            and time.monotonic() - _datenausfall_zuletzt < DATENAUSFALL_SPERRE_MINUTEN * 60):
        return False
    from api.email_notify import send_notification_email
    import config as config_module

    text = chr(10).join([
        f"Fuer ALLE {gesamt} beobachteten Werte ist der zuletzt gespeicherte "
        f"Preis aelter als {staleness.PRICE_STALE_THRESHOLD_MINUTES} Minuten.",
        "",
        "Was das heisst: die Analyse laeuft nicht. Das Datenqualitaets-Gate "
        "weist jeden Wert ab, bevor ein Modell ueberhaupt gefragt wird - "
        "richtig so, aber es entstehen keine Signale.",
        "",
        "Ohne diese Nachricht waere das nicht zu erkennen: ein Lauf ohne "
        "Signale sieht aus wie ein Lauf ohne Gelegenheiten.",
        "",
        "Ein Nachhol-Lauf fuer die Kursabfrage ist automatisch angestossen. "
        "Kommt diese Nachricht erneut, hakt die Quelle selbst (CoinGecko-"
        "Kontingent, Netz, API-Schluessel).",
    ])
    try:
        empfaenger = config_module.get_config().get("benachrichtigung", {}).get("email")
    except Exception:
        empfaenger = None
    try:
        send_notification_email(
            "TradingInfoTool: KEINE ANALYSE - alle Kurse veraltet", text, empfaenger)
        _datenausfall_zuletzt = time.monotonic()
        return True
    except Exception:
        logger.exception("Datenausfall-Meldung konnte nicht gesendet werden")
        return False


def _ohlc_data_is_stale(conn, watchlist) -> bool:
    """Analog zu _history_data_is_stale(), fuer den Kraken-OHLC-Job. Prueft nur
    Assets/Waehrungen mit echtem Kraken-Listing (KRAKEN_PAIR_MAP) - fehlende
    Listings sind eine bekannte, dokumentierte Deckungsluecke (siehe
    api/kraken_history.py), kein Staleness-Fall.

    ⚠️ EIGENE, ENGERE SCHWELLE SEIT DEM 16.08.2026 - wegen eines Ausfalls, der
    zwei Tage lang niemandem auffiel.

    GEMESSEN AM NB-EXPORT vom 16.08. 09:41: **alle 61 Kursreihen endeten am
    Freitag, 14.08.** Der letzte Kraken-Refresh lief am 14.08. um 20:57, und
    zwar nur, weil ein Neustart ihn ausloeste. Die Rollen-Kette urteilte damit
    am Sonntag auf Charts vom Freitag - fuer Krypto, also 77 % aller Aufrufe -
    und die Signalmail nannte einen zwei Tage alten Kurs als "Kurs".

    DREI DINGE MUSSTEN ZUSAMMENKOMMEN:
      * der Takt ist 24 Stunden und beginnt bei JEDEM Neustart neu. Am 16.08.
        wurde dreimal neu gestartet (00:14, 06:40, 07:55) - der regulaere Lauf
        kam nie dran
      * der Sofortlauf beim Start greift erst bei MEHR als zwei Tagen
        Rueckstand. Freitag -> Sonntag sind genau zwei
      * der Watchdog benutzt dieselbe Schwelle und griff deshalb ebenfalls nicht

    HIER LIEGT DIE RICHTIGE STELLE. Diese Funktion sieht ausschliesslich
    Kraken-gelistete Assets an, also Krypto - und Krypto handelt rund um die
    Uhr. Ein Rueckstand von zwei Tagen ist dort kein Wochenende, sondern ein
    Ausfall. Die Schwelle in `staleness.py` bleibt unangetastet: an ihr haengen
    die Anzeige (`ui/formatting`) und das Datenqualitaets-Gate R-5.0 der alten
    Kette. Wer sie dort senkt, aendert beides mit."""
    try:
        for asset in watchlist:
            pair_map = KRAKEN_PAIR_MAP.get(asset.symbol)
            if pair_map is None:
                continue
            for currency in pair_map:
                if staleness.is_history_stale(
                        db.get_last_ohlc_date(conn, asset.symbol, currency),
                        schwelle_tage=staleness.KRYPTO_OHLC_STALE_THRESHOLD_DAYS):
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
        preise_veraltet, preise_gesamt = _preis_daten_veraltet(conn, watchlist)
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
    if preise_veraltet:
        logger.info(
            "Staleness-Watchdog: %d von %d Preisen veraltet - sofortiger "
            "Nachhol-Lauf ausgeloest", preise_veraltet, preise_gesamt)
        try:
            _scheduler_ref.modify_job("refresh_prices", next_run_time=datetime.now())
        except Exception:
            logger.exception("Staleness-Watchdog: Nachhol-Lauf fuer refresh_prices "
                             "konnte nicht ausgeloest werden")
        if _melde_datenausfall(preise_veraltet, preise_gesamt):
            logger.warning("Datenausfall gemeldet: %d von %d Preisen veraltet",
                           preise_veraltet, preise_gesamt)
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
    mistral_client=None, zai_client=None, openrouter_client=None,
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
        next_run_time=_staggered_start(0),
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
        # coingecko_client als viertes Argument: Rueckfallquelle fuer
        # Krypto-Assets ohne Kraken-Listing (03.08.), siehe refresh_ohlc_job().
        args=[kraken_client, db_conn_factory, watchlist_provider, coingecko_client],
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
    # KEIN next_run_time=jetzt (2026-07-31, Nutzer-Vorgabe "nichts extra
    # anfassen") - reiner Lese-Check, kein Grund, ihn den bereits gestaffelten
    # Sofort-Start-Jobs hinzuzufuegen (siehe _staggered_start()-Docstring),
    # erster Lauf einfach nach dem regulaeren Takt.
    scheduler.add_job(
        coingecko_quota_check_job,
        "interval",
        minutes=COINGECKO_QUOTA_CHECK_INTERVAL_MINUTES,
        args=[db_conn_factory],
        id="coingecko_quota_check",
    )
    scheduler.add_job(
        refresh_securities_prices_job,
        "interval",
        minutes=SECURITIES_REFRESH_INTERVAL_MINUTES,
        args=[YFinanceClient(), db_conn_factory, watchlist_provider],
        id="refresh_securities_prices",
        next_run_time=_staggered_start(1),
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
        next_run_time=_staggered_start(2),
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
            openrouter_client,
        ],
        id="hebel_screening",
        next_run_time=_staggered_start(3),
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
        args=[db_conn_factory, watchlist_provider, coingecko_client, gemini_client, mistral_client,
              zai_client, openrouter_client],
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
    # --- NACHHOLEN, WAS HEUTE NOCH NICHT LIEF (16.08.2026) ----------------
    #
    # Begruendung und Messwerte stehen bei `database.db.merke_joblauf()`.
    # Kurz: fuenf taegliche Cron-Jobs zwischen 06:00 und 07:15 liefen in 48
    # Stunden zusammen viermal, der Ausstiegs-Job gar nicht - weil die App zur
    # Uhrzeit nicht lief und APScheduler nichts nachholt.
    #
    # DIE REIHENFOLGE BLEIBT ERHALTEN, und das ist kein Schmuck: der Kommentar
    # am Ausstiegs-Job sagt ausdruecklich "Die Reihenfolge ist noetig, nicht
    # kosmetisch" - die Regel rechnet auf Werten, die das Backward-Tracking
    # vorher fortschreibt. Wuerden alle fuenf gleichzeitig nachgeholt, liefe
    # sie auf dem Stand von gestern. Deshalb der Versatz.
    def _nachholen(job_id: str, versatz_sekunden: int) -> dict:
        """kwargs fuer `add_job` - sofort, wenn heute noch nicht gelaufen.

        IM ZWEIFEL NICHT NACHHOLEN. Faellt die Abfrage aus, kommt ein leeres
        dict und der Job laeuft wie bisher zur Uhrzeit. Ein Nachholer, der bei
        einer Luecke feuert, macht aus einem Lesefehler einen Modellaufruf."""
        try:
            c = db_conn_factory()
            try:
                zuletzt = db.letzter_joblauf(c, job_id)
            finally:
                c.close()
            if zuletzt is not None:
                dann = datetime.fromisoformat(str(zuletzt))
                if dann.tzinfo is not None:
                    dann = dann.astimezone().replace(tzinfo=None)
                if dann.date() >= datetime.now().date():
                    return {}          # heute schon gelaufen
            logger.info("Job %s heute noch nicht gelaufen (zuletzt %s) - "
                        "wird in %d s nachgeholt", job_id, zuletzt or "nie",
                        versatz_sekunden)
            return {"next_run_time": datetime.now() + timedelta(
                        seconds=versatz_sekunden),
                    "misfire_grace_time": _IMMEDIATE_START_MISFIRE_GRACE_SECONDS}
        except Exception:                                    # noqa: BLE001
            logger.exception("Nachhol-Pruefung fuer %s fehlgeschlagen - "
                             "Job laeuft wie bisher zur Uhrzeit", job_id)
            return {}

    # Ausstiegs-Empfehlungen (2026-08-05) - taeglich 7:15, also NACH dem
    # Backward-Tracking (6:00) und dem Portfoliowert (6:30). Die Reihenfolge
    # ist noetig, nicht kosmetisch: die Regel rechnet auf
    # outcome_max_realisiertes_crv, und genau das schreibt das Backward-
    # Tracking fort. Vorher gestartet arbeitete sie auf dem Stand von gestern.
    scheduler.add_job(
        ausstiegs_job,
        "cron",
        hour=7,
        minute=15,
        args=[db_conn_factory, watchlist_provider],
        id="ausstiegs_empfehlungen",
        **_nachholen("ausstiegs_empfehlungen", 240),
    )
    scheduler.add_job(
        backward_tracking_job,
        "cron",
        hour=6,
        minute=0,
        args=[db_conn_factory, watchlist_provider],
        id="backward_tracking",
        **_nachholen("backward_tracking", 30),
    )
    # Portfolio-Wert + Z-3/RM-7 (2026-08-04, Task #612) - taeglich 6:30, aus
    # demselben Grund wie das Backward-Tracking darueber nach dem naechtlichen
    # Kurs-Refresh: der Job liest nur DB-Stand, macht keinen eigenen
    # Netzwerk-Call, braucht aber aktuelle Kurse. Eine halbe Stunde Versatz,
    # damit sich die beiden nicht ueberlappen.
    scheduler.add_job(
        portfolio_wert_job,
        "cron",
        hour=6,
        minute=30,
        args=[db_conn_factory, watchlist_provider],
        id="portfolio_wert",
        **_nachholen("portfolio_wert", 120),
    )
    # Marktscan-Erfolgsmessung (2026-07-30, Teil 2 der Reifegrad-/Erfolgsmessung-
    # Runde) - taeglich, 1 Std. nach dem Spot/Hebel-Backward-Tracking (analoges
    # Timing-Muster, kein harter Grund fuer genau diesen Abstand). Kein eigener
    # Aktiv-Schalter noetig - marktscan.aktiv wird im Job-Body geprueft (gleiches
    # Muster wie marktscan_job()).
    scheduler.add_job(
        marktscan_backward_tracking_job,
        "cron",
        hour=7,
        minute=0,
        args=[
            coingecko_client, kraken_client, db_conn_factory, watchlist_provider, fred_api_key,
            mistral_client, gemini_client,
        ],
        id="marktscan_backward_tracking",
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
        next_run_time=_staggered_start(4),
        misfire_grace_time=_IMMEDIATE_START_MISFIRE_GRACE_SECONDS,
    )
    # Fremdquellen der Rolle G (2026-08-16) - taeglich um 06:35, also VOR den
    # Signallaeufen. Der Zeitpunkt ist nicht beliebig: die Rollen-Kette liest
    # diese Reihen, und was sie nicht findet, holt sie im Urteil selbst aus dem
    # Netz. `next_run_time` bootstrapt sie sofort nach dem Einspielen, sonst
    # stuende die Tabelle bis zum naechsten Morgen leer.
    scheduler.add_job(
        externe_reihen_job,
        "cron",
        hour=6,
        minute=35,
        args=[db_conn_factory],
        id="externe_reihen",
        next_run_time=_staggered_start(5),
        misfire_grace_time=_IMMEDIATE_START_MISFIRE_GRACE_SECONDS,
    )
    # #333 KI-Vorschlaege-Job (2026-07-24) - gleiches Muster wie makro_analog
    # (taeglich 06:30, rein deterministisch, sofortiger Erststart).
    scheduler.add_job(
        kategorie_vorschlaege_job,
        "cron",
        hour=6,
        minute=30,
        args=[db_conn_factory],
        id="kategorie_vorschlaege",
        next_run_time=_staggered_start(5),
        misfire_grace_time=_IMMEDIATE_START_MISFIRE_GRACE_SECONDS,
    )
    # #333 Schicht 2 (2026-07-25) - BEWUSST VOR kategorie_vorschlaege_job
    # (06:15, 15 Min VOR Schicht 1 um 06:30): Schicht 2 liefert je Kategorie
    # eine Prioritaets-Rangfolge unter den heute Fall-A-reifen Kandidaten, die
    # Schicht 1 direkt im selben Lauf fuer die Gleichzeitigkeits-Moderation
    # braucht (agent/kategorie_vorschlaege.py) - dafuer muss das Ergebnis VOR
    # Schicht 1 vorliegen. Die Tracker-/These-Sicht, die Schicht 2 dabei
    # verwendet, ist automatisch "Stand von gestern Abend" (Schicht 1 hat
    # heute noch nicht gelaufen) - das ist fuer die Prognose "was wird HEUTE
    # reif" korrekt, nicht veraltet. Gleiche P-8-Fallback-Kette wie
    # hebel_screening (Mistral->Groq->Gemini), aber ohne bitpanda_api_key/
    # kraken_client/zai_client - reiner Text-Synthese-Call.
    scheduler.add_job(
        kategorie_synthese_job,
        "cron",
        hour=6,
        minute=15,
        args=[db_conn_factory, mistral_client, groq_client, gemini_client],
        id="kategorie_synthese",
        next_run_time=_staggered_start(6),
        misfire_grace_time=_IMMEDIATE_START_MISFIRE_GRACE_SECONDS,
    )
    # 2026-07-17, Nutzer-Fund: ein fester Cron holt einen verpassten Termin NICHT
    # automatisch nach, wenn die App zu diesem Zeitpunkt gar nicht lief - an zwei
    # Tagen in Folge passiert (07-15/07-16), zwei Tage lang keine einzige
    # Backward-Tracking-Auswertung trotz laengst reifer Hebel-Positionen. Direkter
    # synchroner Nachhol-Check beim Start (kein Netzwerk-Call, siehe Docstring
    # dort) - No-Op, falls der heutige Lauf schon glückte.
    backward_tracking_catchup_if_missed(db_conn_factory, watchlist_provider)
    # Multi-Asset-Batch-Nachhol-Check (2026-07-30, siehe multi_asset_batch_
    # catchup_if_missed()-Docstring) - gleiches Muster wie Backward-Tracking
    # oben, angewendet auf den 2x/Tag-Cron fuer Aktien/Rohstoffe/Themen-ETF/
    # Hedge. Reine DB-Abfrage + ggf. ein synchroner Batch-Lauf, kein
    # zusaetzliches Risiko fuer den Scheduler-Start selbst.
    multi_asset_batch_catchup_if_missed(
        db_conn_factory, watchlist_provider, coingecko_client,
        gemini_client=gemini_client, mistral_client=mistral_client, zai_client=zai_client,
        openrouter_client=openrouter_client,
    )
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
            next_run_time=_staggered_start(7),
            misfire_grace_time=_IMMEDIATE_START_MISFIRE_GRACE_SECONDS,
        )
    else:
        logger.info("Kein BITPANDA_API_KEY - automatischer Bestandsabgleich deaktiviert (P-8)")
    scheduler.add_listener(_log_job_event, EVENT_JOB_ERROR | EVENT_JOB_MISSED)

    global _scheduler_ref
    _scheduler_ref = scheduler
    return scheduler
