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

from database.models import PriceSnapshot

logger = logging.getLogger(__name__)

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
