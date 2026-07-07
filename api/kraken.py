"""Kraken API Anbindung — komplett oeffentliche Endpunkte, kein Account/Key/KYC noetig.

Liefert echte OHLC-Kerzendaten (Open/High/Low/Close) und Funding-Rate-Historie.
Ersetzt fuer bei Kraken gelistete Assets die Naeherungen aus
indicators/calculations.py (atr_close_to_close_proxy, swing_highs_lows_close_proxy) -
siehe Basisinfos/Spezifikation.md Kap. 8.
"""
from __future__ import annotations

import time
from collections import deque
from datetime import datetime, timezone

import requests

SPOT_BASE_URL = "https://api.kraken.com/0/public"
FUTURES_BASE_URL = "https://futures.kraken.com/derivatives/api/v3"
RATE_LIMIT_PER_MINUTE = 15  # konservativ; oeffentliche Endpunkte haben kein dokumentiertes hartes Limit

# Bekannte Kraken-Spot-Paare fuer die Anker-Assets (Kraken nutzt eigene Symbolik, z.B.
# "XBT" statt "BTC"). Wird bei Bedarf erweitert, sobald weitere Assets angebunden werden.
KRAKEN_PAIR_MAP = {
    "BTC": "XBTUSD",
    "ETH": "ETHUSD",
}

# Kraken-Futures-Symbole fuer Funding-Rates (Perpetual Futures, "PF_" Prefix).
KRAKEN_FUTURES_SYMBOL_MAP = {
    "BTC": "PF_XBTUSD",
    "ETH": "PF_ETHUSD",
}


class KrakenClient:
    def __init__(self, session: requests.Session | None = None):
        self._session = session or requests.Session()
        self._call_timestamps: deque[float] = deque()

    def _respect_rate_limit(self) -> None:
        now = time.monotonic()
        while self._call_timestamps and now - self._call_timestamps[0] > 60:
            self._call_timestamps.popleft()
        if len(self._call_timestamps) >= RATE_LIMIT_PER_MINUTE:
            sleep_for = 60 - (now - self._call_timestamps[0])
            if sleep_for > 0:
                time.sleep(sleep_for)
        self._call_timestamps.append(time.monotonic())

    def get_ohlc(self, pair: str, interval: int = 1440, since: int | None = None) -> list[dict]:
        """interval in Minuten (1440 = 1 Tag). Liefert bis zu 720 Kerzen."""
        self._respect_rate_limit()
        params = {"pair": pair, "interval": interval}
        if since is not None:
            params["since"] = since
        response = self._session.get(f"{SPOT_BASE_URL}/OHLC", params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        if data.get("error"):
            raise RuntimeError(f"Kraken OHLC Fehler fuer {pair}: {data['error']}")

        result = data["result"]
        # Der Pair-Key in der Antwort entspricht nicht immer exakt dem Anfrage-Pair
        # (z.B. interne Kraken-Normalisierung) - das erste Nicht-"last"-Feld nehmen.
        pair_key = next(k for k in result if k != "last")
        candles = result[pair_key]

        return [
            {
                "time": row[0],
                "date": datetime.fromtimestamp(row[0], tz=timezone.utc).date().isoformat(),
                "open": float(row[1]),
                "high": float(row[2]),
                "low": float(row[3]),
                "close": float(row[4]),
                "vwap": float(row[5]),
                "volume": float(row[6]),
                "count": row[7],
            }
            for row in candles
        ]

    def get_funding_rates(self, futures_symbol: str) -> list[dict]:
        self._respect_rate_limit()
        params = {"symbol": futures_symbol}
        response = self._session.get(
            f"{FUTURES_BASE_URL}/historical-funding-rates", params=params, timeout=15
        )
        response.raise_for_status()
        data = response.json()
        if data.get("result") != "success":
            raise RuntimeError(f"Kraken Funding-Rate Fehler fuer {futures_symbol}: {data}")

        return [
            {
                "timestamp": entry["timestamp"],
                "funding_rate": entry["fundingRate"],
                "relative_funding_rate": entry["relativeFundingRate"],
            }
            for entry in data["rates"]
        ]
