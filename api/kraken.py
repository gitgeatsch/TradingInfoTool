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

from database.api_health import track_api_health

SPOT_BASE_URL = "https://api.kraken.com/0/public"
FUTURES_BASE_URL = "https://futures.kraken.com/derivatives/api/v3"
RATE_LIMIT_PER_MINUTE = 15  # konservativ; oeffentliche Endpunkte haben kein dokumentiertes hartes Limit

# Verifiziert gegen /0/public/AssetPairs am 2026-07-07 (siehe Basisinfos/Spezifikation.md
# Kap. 8): 35 der 41 Watchlist-Assets haben ein Kraken-Spot-Paar in USD UND EUR, nicht
# nur BTC/ETH. Kraken nutzt teils eigene Symbolik (z.B. "XBT" statt "BTC").
# NICHT gelistet (Stand 2026-07-07): EURCV (Stablecoin, braucht ohnehin kein OHLC/ATR),
# KAIA, BRETT, IO, SUPRA, CANTON — fuer diese bleibt die Naeherung aus
# indicators/calculations.py der einzige Weg.
KRAKEN_PAIR_MAP = {
    "BTC": {"USD": "XBTUSD", "EUR": "XBTEUR"},
    "ETH": {"USD": "ETHUSD", "EUR": "ETHEUR"},
    "SOL": {"USD": "SOLUSD", "EUR": "SOLEUR"},
    "LINK": {"USD": "LINKUSD", "EUR": "LINKEUR"},
    "AVAX": {"USD": "AVAXUSD", "EUR": "AVAXEUR"},
    "SUI": {"USD": "SUIUSD", "EUR": "SUIEUR"},
    "TAO": {"USD": "TAOUSD", "EUR": "TAOEUR"},
    "NEAR": {"USD": "NEARUSD", "EUR": "NEAREUR"},
    "APT": {"USD": "APTUSD", "EUR": "APTEUR"},
    "ONDO": {"USD": "ONDOUSD", "EUR": "ONDOEUR"},
    "ALGO": {"USD": "ALGOUSD", "EUR": "ALGOEUR"},
    "KAS": {"USD": "KASUSD", "EUR": "KASEUR"},
    "RENDER": {"USD": "RENDERUSD", "EUR": "RENDEREUR"},
    "SEI": {"USD": "SEIUSD", "EUR": "SEIEUR"},
    "MORPHO": {"USD": "MORPHOUSD", "EUR": "MORPHOEUR"},
    "INJ": {"USD": "INJUSD", "EUR": "INJEUR"},
    "FLOKI": {"USD": "FLOKIUSD", "EUR": "FLOKIEUR"},
    "S": {"USD": "SUSD", "EUR": "SEUR"},
    "IMX": {"USD": "IMXUSD", "EUR": "IMXEUR"},
    "W": {"USD": "WUSD", "EUR": "WEUR"},
    "BEAMX": {"USD": "BEAMUSD", "EUR": "BEAMEUR"},
    "AKT": {"USD": "AKTUSD", "EUR": "AKTEUR"},
    "AIOZ": {"USD": "AIOZUSD", "EUR": "AIOZEUR"},
    "BIO": {"USD": "BIOUSD", "EUR": "BIOEUR"},
    "TURBO": {"USD": "TURBOUSD", "EUR": "TURBOEUR"},
    "PLUME": {"USD": "PLUMEUSD", "EUR": "PLUMEEUR"},
    "CAT": {"USD": "CATUSD", "EUR": "CATEUR"},
    "GRIFFAIN": {"USD": "GRIFFAINUSD", "EUR": "GRIFFAINEUR"},
    "MON": {"USD": "MONUSD", "EUR": "MONEUR"},
    "XLM": {"USD": "XLMUSD", "EUR": "XLMEUR"},
    "QNT": {"USD": "QNTUSD", "EUR": "QNTEUR"},
    "ASTER": {"USD": "ASTERUSD", "EUR": "ASTEREUR"},
    "HYPE": {"USD": "HYPEUSD", "EUR": "HYPEEUR"},
    "BNB": {"USD": "BNBUSD", "EUR": "BNBEUR"},
    "VIRTUAL": {"USD": "VIRTUALUSD", "EUR": "VIRTUALEUR"},
}

# Kraken-Futures-Symbole fuer Funding-Rates (Perpetual Futures, "PF_" Prefix).
# Waehrungsunabhaengig (relative Rate in %), daher kein separates EUR-Mapping noetig.
# 36/41 Assets abgedeckt — inkl. KAIA/BRETT/IO, die zwar KEIN Kraken-Spot-Paar haben
# (siehe KRAKEN_PAIR_MAP), aber trotzdem als Perpetual gelistet sind (getrennte Produkte).
# SUPRA/CANTON/EURCV: weder Spot noch Futures bei Kraken.
KRAKEN_FUTURES_SYMBOL_MAP = {
    "BTC": "PF_XBTUSD",
    "ETH": "PF_ETHUSD",
    "SOL": "PF_SOLUSD",
    "LINK": "PF_LINKUSD",
    "AVAX": "PF_AVAXUSD",
    "SUI": "PF_SUIUSD",
    "TAO": "PF_TAOUSD",
    "NEAR": "PF_NEARUSD",
    "APT": "PF_APTUSD",
    "ONDO": "PF_ONDOUSD",
    "ALGO": "PF_ALGOUSD",
    "KAS": "PF_KASUSD",
    "RENDER": "PF_RENDERUSD",
    "SEI": "PF_SEIUSD",
    "MORPHO": "PF_MORPHOUSD",
    "INJ": "PF_INJUSD",
    "KAIA": "PF_KAIAUSD",
    "FLOKI": "PF_FLOKIUSD",
    "S": "PF_SUSD",
    "IMX": "PF_IMXUSD",
    "W": "PF_WUSD",
    "BEAMX": "PF_BEAMUSD",
    "AKT": "PF_AKTUSD",
    "BRETT": "PF_BRETTUSD",
    "BIO": "PF_BIOUSD",
    "TURBO": "PF_TURBOUSD",
    "IO": "PF_IOUSD",
    "CAT": "PF_CATUSD",
    "GRIFFAIN": "PF_GRIFFAINUSD",
    "MON": "PF_MONUSD",
    "XLM": "PF_XLMUSD",
    "QNT": "PF_QNTUSD",
    "ASTER": "PF_ASTERUSD",
    "HYPE": "PF_HYPEUSD",
    "BNB": "PF_BNBUSD",
    "VIRTUAL": "PF_VIRTUALUSD",
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

    @track_api_health("kraken")
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

    @track_api_health("kraken")
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
