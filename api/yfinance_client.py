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
from datetime import datetime, timezone

import yfinance as yf

from database.models import PriceSnapshot

logger = logging.getLogger(__name__)

# 2026-07-11 (Remote-Steuer-Seite-Planung): anders als requests-basierte Clients
# im Projekt (alle mit explizitem timeout=) bietet yfinance keinen von uns
# kontrollierten Netzwerk-Timeout - ein haengender Yahoo-Finance-Call wuerde
# refresh_securities_prices_job() unbegrenzt blockieren und dessen Lock (siehe
# scheduler/background.py) dauerhaft besetzt halten. Timeout ueber einen
# separaten Worker-Thread erzwungen (siehe _fetch_one_with_timeout()).
_YFINANCE_TIMEOUT_SECONDS = 15


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
        price_eur weiterhin None statt eines falsch geratenen Werts (P-10)."""
        fetched_at = datetime.now(timezone.utc).isoformat()
        snapshots: list[PriceSnapshot] = []

        for asset in assets:
            if asset.assetklasse == "krypto" or not asset.yfinance_symbol:
                continue
            try:
                snapshot = self._fetch_one_with_timeout(asset, fetched_at, eur_usd_fx_rate)
            except concurrent.futures.TimeoutError:
                logger.error(
                    "yfinance-Kursabruf fuer %s (%s) nach %ds abgebrochen (haengender Aufruf) - "
                    "naechster Scheduler-Lauf versucht es erneut",
                    asset.symbol, asset.yfinance_symbol, _YFINANCE_TIMEOUT_SECONDS,
                )
                continue
            except Exception:
                logger.exception("yfinance-Kursabruf fehlgeschlagen fuer %s (%s)", asset.symbol, asset.yfinance_symbol)
                continue
            if snapshot is not None:
                snapshots.append(snapshot)

        return snapshots

    def _fetch_one_with_timeout(
        self, asset, fetched_at: str, eur_usd_fx_rate: float | None = None
    ) -> PriceSnapshot | None:
        """Python kann einen haengenden Thread nicht erzwungen beenden - selbst nach
        Ablauf des Timeouts koennte der Worker-Thread im Hintergrund weiterlaufen (bis
        Yahoo irgendwann doch antwortet oder der Prozess endet). Das begrenzt aber
        unsere WARTEZEIT zuverlaessig, was hier das eigentliche Ziel ist (Job/Lock darf
        nicht unbegrenzt blockieren). shutdown(wait=False) ist bewusst noetig - der
        Default (wait=True) wuerde sonst selbst beim Timeout-Fall auf den haengenden
        Thread warten und den ganzen Sinn der Massnahme zunichtemachen."""
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        future = executor.submit(self._fetch_one, asset, fetched_at, eur_usd_fx_rate)
        try:
            return future.result(timeout=_YFINANCE_TIMEOUT_SECONDS)
        finally:
            executor.shutdown(wait=False)

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
