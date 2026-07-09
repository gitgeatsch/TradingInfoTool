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

import logging
from datetime import datetime, timezone

import yfinance as yf

from database.models import PriceSnapshot

logger = logging.getLogger(__name__)


class YFinanceClient:
    def fetch_price_snapshots(self, assets: list) -> list[PriceSnapshot]:
        """Nur Assets mit assetklasse != 'krypto' und gesetztem yfinance_symbol.
        P-10: ein fehlgeschlagenes/delistetes Symbol darf die anderen nicht blockieren -
        yfinance bietet (anders als CoinGecko) keinen Bulk-Endpunkt mit eingebauter
        Fehlerisolierung, daher try/except je Einzelsymbol."""
        fetched_at = datetime.now(timezone.utc).isoformat()
        snapshots: list[PriceSnapshot] = []

        for asset in assets:
            if asset.assetklasse == "krypto" or not asset.yfinance_symbol:
                continue
            try:
                snapshot = self._fetch_one(asset, fetched_at)
            except Exception:
                logger.exception("yfinance-Kursabruf fehlgeschlagen fuer %s (%s)", asset.symbol, asset.yfinance_symbol)
                continue
            if snapshot is not None:
                snapshots.append(snapshot)

        return snapshots

    def _fetch_one(self, asset, fetched_at: str) -> PriceSnapshot | None:
        info = yf.Ticker(asset.yfinance_symbol).fast_info
        last_price = info.get("lastPrice")
        currency = info.get("currency")
        if last_price is None:
            return None

        # P-10: nur die tatsaechlich gemeldete Waehrung befuellen, nie umrechnen/raten -
        # ein leeres Feld ist besser als ein falsch beschrifteter Wert.
        price_usd = last_price if currency == "USD" else None
        price_eur = last_price if currency == "EUR" else None
        if price_usd is None and price_eur is None:
            logger.warning(
                "yfinance liefert fuer %s eine nicht unterstuetzte Waehrung (%s) - Preis wird nicht angezeigt",
                asset.symbol, currency,
            )

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
