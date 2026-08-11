"""Open Interest + Long/Short-Ratio - Spezifikation Kap. 8/16, Bestandsaufnahme
"Krypto-typische Datentypen" 2026-07-08. Ergaenzt die bestehende Kraken-Funding-Rate
(`api/kraken.py`, genutzt in `agent/krypto/anticyclic.py` fuer AZ-1) um weitere
Positionierungs-/Derivate-Kontextdaten.

KEIN Liquidations-Heatmap-Ersatz: eine Heatmap braucht eine Modellierung, bei welchen
Hebelstufen wie viele Positionen bei welchem Preis liquidiert wuerden - das ist
etwas anderes als der reine Open-Interest-Bestand hier. CoinGlass (der Standard dafuer)
ist kostenpflichtig (siehe Spezifikation Kap. 16, Register verworfener Loesungen) und
wurde bewusst nicht nachgebaut, auch nicht durch Website-Scraping.

Alle drei Quellen sind oeffentliche, kostenlose Markt-Daten-Endpunkte der jeweiligen
Boersen selbst - kein Account/Key noetig, kein eigener Rate-Limiter. Urspruenglich
nur bei manuellem "Signal berechnen"-Klick aufgerufen (wenige Calls) - seit 2026-07-14
zusaetzlich alle 15 Min ueber die komplette Krypto-Watchlist vom Hebel-Screening
(agent/krypto/hebel_screening.py::fetch_and_store_oi_snapshot()), siehe
docs/hebel_positionsformel.md. Weiterhin oeffentliche Endpunkte ohne dokumentiertes
Rate-Limit, bei Bedarf spaeter nachruesten."""
from __future__ import annotations

from dataclasses import dataclass

import requests

from database.api_health import track_api_health

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


class NoOpenInterestDataError(Exception):
    """2026-07-19 (echter Notebook-Fund, mehrere Symbole - KAS/KAIA/FLOKI/TURBO/
    CANTON - scheiterten wiederholt): Bybit/OKX antworten bei einem Symbol ohne
    Daten (z.B. kein gelisteter Perp) mit HTTP 200 und einer LEEREN Liste statt
    einem Fehlerstatus - das bisherige `liste[0]` warf dafuer ein nichtssagendes
    `IndexError: list index out of range`. Diese Exception macht die eigentliche
    Ursache (keine Daten fuer dieses Symbol, keine kaputte Verbindung) im Log
    sofort erkennbar, aendert aber NICHTS am Fehlerverhalten selbst - beide
    Aufrufer (hebel_screening.py/anticyclic.py) fangen ohnehin jede Exception
    pro Boerse einzeln ab (P-10-Isolation, unveraendert)."""


def _erstes_element(liste: list, exchange: str, symbol: str):
    if not liste:
        raise NoOpenInterestDataError(f"{exchange}: keine Daten fuer Symbol '{symbol}' (leere Antwort)")
    return liste[0]


@track_api_health("binance")
def get_binance_open_interest(symbol: str = "BTCUSDT", session: requests.Session | None = None) -> OpenInterestReading:
    session = session or requests.Session()
    response = session.get(BINANCE_OI_URL, params={"symbol": symbol}, timeout=15)
    response.raise_for_status()
    data = response.json()
    return OpenInterestReading(
        exchange="binance", symbol=symbol, open_interest=float(data["openInterest"]), open_interest_usd=None
    )


@track_api_health("binance")
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
    rohdaten = response.json()
    if not rohdaten:
        raise NoOpenInterestDataError(f"binance: keine Long-Short-Ratio-Daten fuer Symbol '{symbol}' (leere Antwort)")
    data = sorted(rohdaten, key=lambda entry: entry["timestamp"])
    entry = data[-1]
    return LongShortRatioReading(
        exchange="binance",
        symbol=symbol,
        date=str(entry["timestamp"]),
        long_account_pct=float(entry["longAccount"]) * 100,
        short_account_pct=float(entry["shortAccount"]) * 100,
        long_short_ratio=float(entry["longShortRatio"]),
    )


@track_api_health("bybit")
def get_bybit_open_interest(symbol: str = "BTCUSDT", session: requests.Session | None = None) -> OpenInterestReading:
    session = session or requests.Session()
    response = session.get(
        BYBIT_OI_URL,
        params={"category": "linear", "symbol": symbol, "intervalTime": "1d", "limit": 1},
        timeout=15,
    )
    response.raise_for_status()
    data = response.json()
    entry = _erstes_element(data["result"]["list"], "bybit", symbol)
    return OpenInterestReading(
        exchange="bybit", symbol=symbol, open_interest=float(entry["openInterest"]), open_interest_usd=None
    )


@track_api_health("okx")
def get_okx_open_interest(inst_id: str = "BTC-USDT-SWAP", session: requests.Session | None = None) -> OpenInterestReading:
    session = session or requests.Session()
    response = session.get(
        OKX_OI_URL, params={"instType": "SWAP", "instId": inst_id}, timeout=15
    )
    response.raise_for_status()
    data = response.json()
    entry = _erstes_element(data["data"], "okx", inst_id)
    return OpenInterestReading(
        exchange="okx", symbol=inst_id, open_interest=float(entry["oi"]), open_interest_usd=float(entry["oiUsd"])
    )


# --- FUNDING-RATE JE SYMBOL (2026-08-11) ------------------------------------
#
# DIE LUECKE, die das schliesst. Dieses Modul holte bisher Open Interest und
# Long/Short, aber KEINE Funding-Rate - die kam ausschliesslich aus
# `api/kraken.py`. Kraken listet weniger Perpetuals als Binance und Bybit:
# an der eigenen Watchlist gemessen (11.08.) decken Binance und Bybit zusammen
# 38 von 44 Krypto-Symbolen ab, kostenlos und ohne API-Key. Beide Endpunkte
# wurden live geprueft.
#
# WARUM DIE FUNDING-RATE ZAEHLT: Sie ist einer der wenigen Fakten, die NICHT
# aus unserer Kursreihe abgeleitet sind. Nach dem Fachstandard traegt ein Setup
# drei bis vier UNABHAENGIGE Faktoren; unsere Eingabe liefert bisher zwei
# (Preis und Umsatz), weil Struktur, Bewegung und Niveaus alle aus derselben
# Kerzenreihe stammen. Die Positionierung am Terminmarkt ist eine dritte
# Quelle - siehe Fakten_Entscheidungsmappe Kapitel 12.
#
# DIE ROHE ZAHL IST KEIN FAKT. Eine Funding-Rate von 0,0001 sagt einem Modell
# nichts; erst ihr Verhaeltnis zur eigenen Historie ist eine Aussage (R-T1: das
# Fenster nennen, R-T5: relative Einheiten). Deshalb liefert
# `summarize_funding()` den Bezug mit - dasselbe Muster wie
# `finra.summarize_short_interest()`.

BINANCE_FUNDING_URL = "https://fapi.binance.com/fapi/v1/fundingRate"
BYBIT_FUNDING_URL = "https://api.bybit.com/v5/market/funding/history"


@dataclass
class FundingRateReading:
    exchange: str
    symbol: str
    zeitpunkt_ms: int
    funding_rate: float


@track_api_health("binance")
def get_binance_funding_history(symbol: str = "BTCUSDT", limit: int = 100,
                                session: requests.Session | None = None
                                ) -> list[FundingRateReading]:
    """Binance zahlt alle acht Stunden - `limit=100` sind rund 33 Tage."""
    session = session or requests.Session()
    r = session.get(BINANCE_FUNDING_URL,
                    params={"symbol": symbol, "limit": limit}, timeout=15)
    r.raise_for_status()
    daten = r.json()
    if not isinstance(daten, list) or not daten:
        raise NoOpenInterestDataError(
            f"binance: keine Funding-Daten fuer Symbol '{symbol}'")
    return [FundingRateReading("binance", symbol, int(e["fundingTime"]),
                               float(e["fundingRate"])) for e in daten]


@track_api_health("bybit")
def get_bybit_funding_history(symbol: str = "BTCUSDT", limit: int = 100,
                              session: requests.Session | None = None
                              ) -> list[FundingRateReading]:
    """Bybit liefert absteigend; hier wird aufsteigend zurueckgegeben, damit
    beide Boersen dasselbe Format haben und ein Aufrufer sie nicht
    versehentlich verwechselt."""
    session = session or requests.Session()
    r = session.get(BYBIT_FUNDING_URL,
                    params={"category": "linear", "symbol": symbol,
                            "limit": limit}, timeout=15)
    r.raise_for_status()
    liste = ((r.json().get("result") or {}).get("list")) or []
    _erstes_element(liste, "bybit", symbol)      # wirft bei leerer Antwort
    gelesen = [FundingRateReading("bybit", symbol,
                                  int(e["fundingRateTimestamp"]),
                                  float(e["fundingRate"])) for e in liste]
    return sorted(gelesen, key=lambda x: x.zeitpunkt_ms)


def get_funding_history(symbol: str = "BTCUSDT", limit: int = 100,
                        session: requests.Session | None = None
                        ) -> list[FundingRateReading]:
    """Binance zuerst, Bybit als Rueckfall - GENAU EINE Quelle je Symbol.

    Zwei Boersen zu mitteln waere falsch: die Saetze unterscheiden sich real,
    und ein Mittelwert waere eine Zahl, die es an keiner Boerse gibt. Wer die
    Quelle braucht, liest sie am Feld `exchange` ab."""
    for holen in (get_binance_funding_history, get_bybit_funding_history):
        try:
            werte = holen(symbol, limit, session)
            if werte:
                return werte
        except Exception:                                        # noqa: BLE001
            continue
    return []


def summarize_funding(readings: list[FundingRateReading]) -> dict | None:
    """Der Bezug, der aus der Zahl eine Aussage macht - keine Bewertung.

    Geliefert wird, WO die aktuelle Rate in ihrer eigenen Historie steht. Das
    Urteil darueber bleibt dem Modell (R-T3: keine Werturteile im Faktensatz).
    Das Vorzeichen ist die eigentliche Information: positiv heisst, dass Longs
    die Shorts bezahlen - der Terminmarkt ist long positioniert."""
    if not readings:
        return None
    werte = [r.funding_rate for r in readings]
    aktuell = werte[-1]
    sortiert = sorted(werte)
    rang = sum(1 for w in sortiert if w < aktuell)
    return {
        "exchange": readings[-1].exchange,
        "symbol": readings[-1].symbol,
        "aktuell": aktuell,
        "beobachtungen": len(werte),
        "perzentil": int(round(100.0 * rang / len(werte))),
        "anteil_positiv_pct": int(round(100.0 * sum(1 for w in werte if w > 0)
                                        / len(werte))),
        "mittel": sum(werte) / len(werte),
    }
