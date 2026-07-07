"""Makro-Kontext fuer R-5.1 (Marktregime): BTC-Dominanz + Fear & Greed Index. Deckt
NICHT die vollstaendige Makro-Anbindung aus Spezifikation Kap. 8 ab (Leitzinsen,
ISM, M2, CPI, Trueflation bleiben `[OFFEN]`, eigene Recherche noetig) - nur die zwei
Kennzahlen, die fuer die Regime-Bestimmung in dieser Phase-3-Slice gebraucht werden.

Kein eigener Rate-Limiter: wird nur bei manuellem "Signal berechnen"-Klick aufgerufen
(wenige Calls), alternative.me dokumentiert kein strenges Limit, CoinGecko /global
laeuft ueber den bereits gedrosselten CoinGeckoClient. Falls das spaeter in den
Scheduler wandert, dann Drosselung nachruesten.
"""
from __future__ import annotations

from dataclasses import dataclass

import requests

FEAR_GREED_URL = "https://api.alternative.me/fng/"


@dataclass
class FearGreedReading:
    value: int
    classification: str


def get_btc_dominance(coingecko_client) -> float:
    data = coingecko_client.get_global_data()
    return data["data"]["market_cap_percentage"]["btc"]


def get_fear_greed_index(session: requests.Session | None = None) -> FearGreedReading:
    session = session or requests.Session()
    response = session.get(FEAR_GREED_URL, params={"limit": 1}, timeout=15)
    response.raise_for_status()
    data = response.json()
    entry = data["data"][0]
    # "value" kommt als String aus der API (live verifiziert 2026-07-07), nicht als Zahl.
    return FearGreedReading(value=int(entry["value"]), classification=entry["value_classification"])
