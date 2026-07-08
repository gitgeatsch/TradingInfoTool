"""Open Interest + Long/Short-Ratio - Spezifikation Kap. 8/16, Bestandsaufnahme
"Krypto-typische Datentypen" 2026-07-08. Ergaenzt die bestehende Kraken-Funding-Rate
(`api/kraken.py`, genutzt in `agent/anticyclic.py` fuer AZ-1) um weitere
Positionierungs-/Derivate-Kontextdaten.

KEIN Liquidations-Heatmap-Ersatz: eine Heatmap braucht eine Modellierung, bei welchen
Hebelstufen wie viele Positionen bei welchem Preis liquidiert wuerden - das ist
etwas anderes als der reine Open-Interest-Bestand hier. CoinGlass (der Standard dafuer)
ist kostenpflichtig (siehe Spezifikation Kap. 16, Register verworfener Loesungen) und
wurde bewusst nicht nachgebaut, auch nicht durch Website-Scraping.

Alle drei Quellen sind oeffentliche, kostenlose Markt-Daten-Endpunkte der jeweiligen
Boersen selbst - kein Account/Key noetig, kein eigener Rate-Limiter (wird nur bei
manuellem "Signal berechnen"-Klick aufgerufen, wenige Calls)."""
from __future__ import annotations

from dataclasses import dataclass

import requests

BINANCE_OI_URL = "https://fapi.binance.com/fapi/v1/openInterest"
BINANCE_LSR_URL = "https://fapi.binance.com/futures/data/globalLongShortAccountRatio"
BYBIT_OI_URL = "https://api.bybit.com/v5/market/open-interest"
OKX_OI_URL = "https://www.okx.com/api/v5/public/open-interest"


@dataclass
class OpenInterestReading:
    exchange: str
    symbol: str
    open_interest: float  # Einheit variiert je Boerse (Kontrakte/Coin), siehe Feld unten
    open_interest_usd: float | None  # nur OKX liefert das direkt mit


@dataclass
class LongShortRatioReading:
    exchange: str
    symbol: str
    date: str
    long_account_pct: float
    short_account_pct: float
    long_short_ratio: float


def get_binance_open_interest(symbol: str = "BTCUSDT", session: requests.Session | None = None) -> OpenInterestReading:
    session = session or requests.Session()
    response = session.get(BINANCE_OI_URL, params={"symbol": symbol}, timeout=15)
    response.raise_for_status()
    data = response.json()
    return OpenInterestReading(
        exchange="binance", symbol=symbol, open_interest=float(data["openInterest"]), open_interest_usd=None
    )


def get_binance_long_short_ratio(
    symbol: str = "BTCUSDT", period: str = "1d", session: requests.Session | None = None
) -> LongShortRatioReading:
    """`period` ist das Aggregations-Fenster der Binance-API (z.B. "1d", "4h"), nicht
    ein Datumsfilter. Fragt bewusst mehrere Punkte ab und nimmt den letzten statt
    limit=1 zu vertrauen - Binance dokumentiert die Sortierreihenfolge nicht
    explizit genug, um sich blind auf "erster Eintrag = neuester" zu verlassen."""
    session = session or requests.Session()
    response = session.get(
        BINANCE_LSR_URL, params={"symbol": symbol, "period": period, "limit": 5}, timeout=15
    )
    response.raise_for_status()
    data = sorted(response.json(), key=lambda entry: entry["timestamp"])
    entry = data[-1]
    return LongShortRatioReading(
        exchange="binance",
        symbol=symbol,
        date=str(entry["timestamp"]),
        long_account_pct=float(entry["longAccount"]) * 100,
        short_account_pct=float(entry["shortAccount"]) * 100,
        long_short_ratio=float(entry["longShortRatio"]),
    )


def get_bybit_open_interest(symbol: str = "BTCUSDT", session: requests.Session | None = None) -> OpenInterestReading:
    session = session or requests.Session()
    response = session.get(
        BYBIT_OI_URL,
        params={"category": "linear", "symbol": symbol, "intervalTime": "1d", "limit": 1},
        timeout=15,
    )
    response.raise_for_status()
    data = response.json()
    entry = data["result"]["list"][0]
    return OpenInterestReading(
        exchange="bybit", symbol=symbol, open_interest=float(entry["openInterest"]), open_interest_usd=None
    )


def get_okx_open_interest(inst_id: str = "BTC-USDT-SWAP", session: requests.Session | None = None) -> OpenInterestReading:
    session = session or requests.Session()
    response = session.get(
        OKX_OI_URL, params={"instType": "SWAP", "instId": inst_id}, timeout=15
    )
    response.raise_for_status()
    data = response.json()
    entry = data["data"][0]
    return OpenInterestReading(
        exchange="okx", symbol=inst_id, open_interest=float(entry["oi"]), open_interest_usd=float(entry["oiUsd"])
    )
