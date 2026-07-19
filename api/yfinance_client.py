"""Kursquelle fuer Aktien/ETF/Rohstoffe (Multi-Asset-Tracking, Nutzer-Idee 2026-07-09).

Bitpanda selbst liefert fuer diese Assetklassen KEINE freien Marktdaten (live geprueft:
`/v1/ticker` deckt nur Krypto + die separate Edelmetall-Wallet ab, keine Aktien/ETC-
Preise; die eigentliche Markt-/Preis-API fuer Wertpapiere ist ein B2B-Enterprise-Produkt,
nicht frei zugaenglich). yfinance (kostenlos, kein API-Key, inoffizielle Yahoo-Finance-
Anbindung) ist die Kursquelle - Bitpanda bleibt fuer diese Assetklassen nur die
Handelsplattform des Nutzers, wie Kraken/CoinGecko es fuer Krypto sind.

`Ticker.fast_info` statt `.history()`: dieser Slice ist bewusst auf reines Tracking
(aktueller Kurs, kein Chart/keine Historie) beschraenkt (siehe Spezifikation Kap. 11,
Zielarchitektur Multi-Asset-Erweiterbarkeit). Wichtig: manche duenn gehandelten
Instrumente (z.B. WisdomTree-ETNs ueber die ISIN+".SG"-Form) liefern nur ueber
fast_info einen Kurs, `.history()` schlaegt dort fehl ("possibly delisted") - live
verifiziert 2026-07-09."""
from __future__ import annotations

import concurrent.futures
import logging
import queue
import threading
import time
from datetime import datetime, timezone

import yfinance as yf

from database.api_health import track_api_health
from database.models import FundamentalsSnapshot, PriceSnapshot

logger = logging.getLogger(__name__)

# Bekannte, bereits live bestaetigte "nur fast_info"-Ticker (2026-07-16, aus
# Notebook-Log-Analyse: 2.637 ERROR-Zeilen ueber 4 Tage, ausgangs 5 Tickern;
# 2026-07-19 um X136.BE/IS0C.DE ergaenzt - Notebook-Nacht-Analyse zeigte 272
# weitere ERROR-Zeilen je Ticker ueber 72 Std., identisches Muster, Job lief
# jedes Mal trotzdem erfolgreich durch: "Wertpapier-Preis-Refresh: 13 Assets
# aktualisiert"). yfinance's EIGENER interner Logger meldet bei jedem fast_info-
# Zugriff auf diese Ticker "possibly delisted; no price data found" (probiert
# intern period=1y/5d, beides schlaegt hier erwartungsgemaess fehl - kein
# Fehler in unserem Code, fast_info liefert trotzdem einen Kurs). Wird in
# main.py per Logging-Filter genutzt, um GENAU diese bekannten, erwarteten
# Faelle zu unterdruecken - ein bisher unbekanntes/neu betroffenes Symbol mit
# demselben yfinance-Fehler bleibt weiterhin sichtbar (P-10: nicht blind alle
# "possibly delisted"-Meldungen unterdruecken, nur die bereits bestaetigten).
YFINANCE_HISTORY_UNRELIABLE_TICKERS = frozenset({
    "GB00B15KY328.SG",  # OD7N
    "IE00BLRPRJ20.SG",  # 3QSS
    "JE00BN7KB334.SG",  # OD7L
    "OD7H.SG",
    "OD7C.SG",
    "X136.BE",  # X136, 2026-07-19 ergaenzt
    "IS0C.DE",  # ISOC, 2026-07-19 ergaenzt
})

# 2026-07-11 (Remote-Steuer-Seite-Planung): anders als requests-basierte Clients
# im Projekt (alle mit explizitem timeout=) bietet yfinance keinen von uns
# kontrollierten Netzwerk-Timeout - ein haengender Yahoo-Finance-Call wuerde
# refresh_securities_prices_job() unbegrenzt blockieren und dessen Lock (siehe
# scheduler/background.py) dauerhaft besetzt halten. Timeout ueber Daemon-Threads
# erzwungen (siehe run_with_daemon_timeout() sowie fetch_price_snapshots()' eigene
# Parallel-Variante mit gemeinsamer Deadline, 2026-07-15-Bugfix).
_YFINANCE_TIMEOUT_SECONDS = 15


def run_with_daemon_timeout(fn, timeout_seconds: float):
    """Notebook-Crash-Fix (2026-07-15): urspruenglich per
    concurrent.futures.ThreadPoolExecutor(max_workers=1) + shutdown(wait=False)
    umgesetzt - das sah nach einem sauberen Timeout aus, hatte aber einen echten
    Bug: ThreadPoolExecutor-Worker sind NICHT daemonisch, und Python registriert
    GLOBAL (unabhaengig vom shutdown() der einzelnen Executor-Instanz!) einen
    atexit-Hook (concurrent.futures.thread._python_exit), der beim Beenden des
    Interpreters ALLE jemals von IRGENDEINEM ThreadPoolExecutor im Prozess
    erzeugten Threads joint. Ein einzelner haengender yfinance-Call (Yahoo
    antwortet nie, kein eigener Netzwerk-Timeout) blockierte dadurch das gesamte
    Prozess-Beenden/Neustarten - live auf dem Notebook beobachtet (App blieb beim
    Start haengen, "yfinance-Threadpool"-Fehler beim Herunterfahren).

    Ein echter threading.Thread(daemon=True) umgeht das: Daemon-Threads werden
    beim Interpreter-Exit NICHT gejoint, sondern abrupt beendet - ein haengender
    yfinance-Call kann den Prozess dann nicht mehr blockieren. Ergebnisuebergabe
    ueber eine Queue statt eines Future-Objekts (kein ThreadPoolExecutor mehr im
    Spiel). Wird von api/yfinance_history.py wiederverwendet (identisches
    Problem dort, siehe dessen Modul-Docstring)."""
    result_queue: queue.Queue = queue.Queue(maxsize=1)

    def _worker():
        try:
            result_queue.put(("ok", fn()))
        except Exception as exc:
            result_queue.put(("error", exc))

    thread = threading.Thread(target=_worker, daemon=True)
    thread.start()
    thread.join(timeout=timeout_seconds)
    if not thread.is_alive():
        kind, payload = result_queue.get()
        if kind == "error":
            raise payload
        return payload

    # Thread laeuft im Hintergrund weiter (Daemon - blockiert den Interpreter-Exit
    # NICHT), aber wir warten hier nicht laenger - das ist das eigentliche Ziel.
    raise concurrent.futures.TimeoutError(
        f"Aufruf nach {timeout_seconds}s abgebrochen (haengender Daemon-Thread laeuft im Hintergrund weiter)"
    )


class YFinanceClient:
    def fetch_price_snapshots(self, assets: list, eur_usd_fx_rate: float | None = None) -> list[PriceSnapshot]:
        """Nur Assets mit assetklasse != 'krypto' und gesetztem yfinance_symbol.
        P-10: ein fehlgeschlagenes/delistetes Symbol darf die anderen nicht blockieren -
        yfinance bietet (anders als CoinGecko) keinen Bulk-Endpunkt mit eingebauter
        Fehlerisolierung, daher try/except je Einzelsymbol.

        eur_usd_fx_rate (2026-07-11, Nutzer-Fund): US-Aktien wie PLTR/VST liefern von
        yfinance nur einen USD-Preis - ohne Umrechnung blieb price_eur fuer diese
        bisher dauerhaft None, wodurch sie in JEDER EUR-basierten Summe (Portfolio-
        Gesamtwert, RM-1/RM-2) unsichtbar waren. Optionaler, vom Aufrufer per echtem
        Marktkurs (EURCV-Peg, siehe scheduler/background.py) ermittelter Umrechnungs-
        kurs - KEINE geratene/fixe Zahl. Bleibt der Kurs unbekannt (None), bleibt
        price_eur weiterhin None statt eines falsch geratenen Werts (P-10).

        2026-07-15-Bugfix (Notebook): frueher wurden alle Assets NACHEINANDER
        abgerufen, jedes mit eigenem bis zu 15s-Timeout - bei mehreren gleichzeitig
        unerreichbaren Symbolen (z.B. Yahoo Finance vom Notebook-Netzwerk aus nicht
        erreichbar) summierte sich das auf N x 15s und liess den Scheduler-Start
        wie haengengeblieben wirken. Jetzt laufen alle Abrufe PARALLEL (eigener
        Daemon-Thread je Asset), mit einer GEMEINSAMEN Gesamt-Deadline von
        _YFINANCE_TIMEOUT_SECONDS - Gesamtlaufzeit bleibt dadurch auf ca. 15s
        begrenzt, unabhaengig von der Anzahl betroffener Assets."""
        fetched_at = datetime.now(timezone.utc).isoformat()
        targets = [a for a in assets if a.assetklasse != "krypto" and a.yfinance_symbol]
        if not targets:
            return []

        result_queue: queue.Queue = queue.Queue()
        for asset in targets:
            threading.Thread(
                target=self._fetch_one_guarded,
                args=(asset, fetched_at, eur_usd_fx_rate, result_queue),
                daemon=True,
            ).start()

        deadline = time.monotonic() + _YFINANCE_TIMEOUT_SECONDS
        snapshots: list[PriceSnapshot] = []
        for _ in targets:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            try:
                asset, kind, payload = result_queue.get(timeout=remaining)
            except queue.Empty:
                break
            if kind == "error":
                logger.error("yfinance-Kursabruf fehlgeschlagen fuer %s (%s): %s", asset.symbol, asset.yfinance_symbol, payload)
            elif payload is not None:
                snapshots.append(payload)

        fertig_count = len(snapshots)
        if fertig_count < len(targets):
            logger.error(
                "yfinance-Kursabruf: nur %d von %d Assets nach %ds abgeschlossen (uebrige haengen als "
                "Hintergrund-Daemon-Threads weiter oder sind fehlgeschlagen) - naechster Scheduler-Lauf versucht es erneut",
                fertig_count, len(targets), _YFINANCE_TIMEOUT_SECONDS,
            )

        return snapshots

    def _fetch_one_guarded(self, asset, fetched_at: str, eur_usd_fx_rate, result_queue: queue.Queue) -> None:
        """Laeuft in einem eigenen Daemon-Thread (siehe fetch_price_snapshots()) -
        faengt JEDE Exception ab und meldet sie ueber die Queue zurueck, statt den
        Thread stillschweigend sterben zu lassen (P-10: ein Symbol darf die anderen
        nicht blockieren, aber Fehler muessen sichtbar bleiben)."""
        try:
            snapshot = self._fetch_one(asset, fetched_at, eur_usd_fx_rate)
            result_queue.put((asset, "ok", snapshot))
        except Exception as exc:
            result_queue.put((asset, "error", exc))

    @track_api_health("yfinance")
    def _fetch_one(self, asset, fetched_at: str, eur_usd_fx_rate: float | None = None) -> PriceSnapshot | None:
        info = yf.Ticker(asset.yfinance_symbol).fast_info
        last_price = info.get("lastPrice")
        currency = info.get("currency")
        if last_price is None:
            return None

        # Nur die tatsaechlich gemeldete Waehrung direkt befuellen, nie raten. Die
        # jeweils ANDERE Waehrung wird NUR umgerechnet, wenn ein echter, aktuell
        # beobachteter Marktkurs vorliegt (eur_usd_fx_rate) - sonst bleibt sie None
        # statt eines falsch geratenen Werts (P-10).
        price_usd = last_price if currency == "USD" else None
        price_eur = last_price if currency == "EUR" else None
        if price_usd is None and price_eur is None:
            logger.warning(
                "yfinance liefert fuer %s eine nicht unterstuetzte Waehrung (%s) - Preis wird nicht angezeigt",
                asset.symbol, currency,
            )
        elif eur_usd_fx_rate:
            if price_eur is None and price_usd is not None:
                price_eur = price_usd / eur_usd_fx_rate
            elif price_usd is None and price_eur is not None:
                price_usd = price_eur * eur_usd_fx_rate

        return PriceSnapshot(
            symbol=asset.symbol,
            coingecko_id=None,
            price_usd=price_usd,
            price_eur=price_eur,
            market_cap_usd=None,
            volume_24h_usd=None,
            change_24h_pct=None,
            fetched_at=fetched_at,
        )


def fetch_fundamentals(symbol: str, yfinance_symbol: str) -> FundamentalsSnapshot:
    """Aktien-Fundamentaldaten (2026-07-15, Non-Krypto-Agent-Pipeline Phase 1, siehe
    agent/aktien/pipeline.py) - komplett neue Datenkategorie ueber die bereits
    vorhandene yfinance-Abhaengigkeit (Ticker.info/.calendar), bisher nirgends im
    Projekt genutzt. P-10: einzelne fehlende Felder bleiben None statt geraten -
    nur ein echter Netzwerk-/Timeout-Fehler wirft (wie bei _fetch_one()), ein
    fehlendes EINZELNES Feld in einer sonst erfolgreichen Antwort nicht."""
    return run_with_daemon_timeout(
        lambda: _fetch_fundamentals(symbol, yfinance_symbol), _YFINANCE_TIMEOUT_SECONDS
    )


@track_api_health("yfinance")
def _fetch_fundamentals(symbol: str, yfinance_symbol: str) -> FundamentalsSnapshot:
    ticker = yf.Ticker(yfinance_symbol)
    info = ticker.info or {}

    naechstes_earnings_datum = None
    try:
        calendar = ticker.calendar
        # yfinance liefert je nach Version entweder ein dict ({"Earnings Date": [...]})
        # oder ein pandas.DataFrame - beide Formen abfangen, P-10: bei unbekannter
        # Struktur bleibt das Feld None statt eines geratenen Werts.
        if isinstance(calendar, dict):
            dates = calendar.get("Earnings Date")
            if dates:
                naechstes_earnings_datum = str(dates[0])
        elif calendar is not None and not calendar.empty and "Earnings Date" in calendar.index:
            naechstes_earnings_datum = str(calendar.loc["Earnings Date"].iloc[0])
    except Exception:
        logger.warning("yfinance-Earnings-Datum fuer %s (%s) nicht lesbar - Feld bleibt None", symbol, yfinance_symbol)

    # Live geprueft (2026-07-15, PLTR/VST): earningsGrowth/revenueGrowth kommen als
    # Faktor (3.25 = +325%), *100 fuer Prozent. dividendYield kommt dagegen bereits
    # in Prozentpunkten (0.58 = 0,58%, NICHT 58%) - bestaetigt durch Abgleich mit
    # trailingAnnualDividendYield (0,0057 = 0,57%, konsistent mit obigem 0,58) -
    # bekannte yfinance-Inkonsistenz zwischen Feldern, deshalb hier explizit
    # dokumentiert statt blind *100 auf alle Felder anzuwenden.
    earnings_growth = info.get("earningsGrowth")
    revenue_growth = info.get("revenueGrowth")

    return FundamentalsSnapshot(
        symbol=symbol,
        kgv=info.get("trailingPE"),
        forward_kgv=info.get("forwardPE"),
        gewinnwachstum_pct=earnings_growth * 100 if earnings_growth is not None else None,
        umsatzwachstum_pct=revenue_growth * 100 if revenue_growth is not None else None,
        dividendenrendite_pct=info.get("dividendYield"),
        analysten_konsens=info.get("recommendationKey"),
        analysten_kursziel_usd=info.get("targetMeanPrice"),
        market_cap_usd=info.get("marketCap"),
        sektor=info.get("sector"),
        naechstes_earnings_datum=naechstes_earnings_datum,
        fetched_at=datetime.now(timezone.utc).isoformat(),
    )
