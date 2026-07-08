"""Makro-Kontext fuer R-5.1 (Marktregime): BTC-Dominanz + Fear & Greed Index + FRED-
Leitzinsen/CPI/M2 + PBoC-LPR (Eastmoney). Deckt NICHT die vollstaendige Makro-
Anbindung aus Spezifikation Kap. 8 ab (Sentiment bleibt `[OFFEN]`) - die Quellen hier
sind alle live recherchiert und verifiziert (2026-07-08), siehe Kap. 8 fuer Details.

Kein eigener Rate-Limiter: wird nur bei manuellem "Signal berechnen"-Klick aufgerufen
(wenige Calls). FRED erlaubt 120 Req/Min (siehe unten), alternative.me dokumentiert
kein strenges Limit, CoinGecko /global laeuft ueber den bereits gedrosselten
CoinGeckoClient. Falls das spaeter in den Scheduler wandert, dann Drosselung
nachruesten.

WICHTIG (P-10): Noch NICHT an agent/pipeline.py oder database/models.py::MacroSnapshot
angebunden - dieser Commit liefert nur die Fetcher-Funktionen, live gegen echte
Endpunkte getestet. Verdrahtung in MacroSnapshot/regime.py ist ein separater
Folgeschritt.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

import requests

logger = logging.getLogger(__name__)

FEAR_GREED_URL = "https://api.alternative.me/fng/"

# FRED (St. Louis Fed): kostenlos, Key sofort bei Registrierung
# (fredaccount.stlouisfed.org/apikeys), 120 Requests/Minute, live verifiziert 2026-07-08
# (siehe Spezifikation Kap. 8). Deckt ueberraschend auch EZB-Saetze ab - keine
# separate ECB-SDW-Integration noetig.
FRED_BASE_URL = "https://api.stlouisfed.org/fred/series/observations"

FRED_SERIES = {
    "fed_funds_rate": "FEDFUNDS",
    "m2_geldmenge": "M2SL",
    "cpi_headline": "CPIAUCSL",
    "cpi_core": "CPILFESL",
    "ezb_einlagensatz": "ECBDFR",
    "ezb_hauptrefinanzierung": "ECBMRRFR",
    "ezb_spitzenrefinanzierung": "ECBMLFR",
    # ISM Manufacturing PMI ist seit 2016 nicht mehr ueber FRED verfuegbar
    # (Lizenzrechte) - Philadelphia Fed Index als live verifizierter Ersatz-Proxy.
    "ism_ersatz_philly_fed": "GACDFSA066MSFRBPHI",
    "boj_tagesgeldsatz": "IRSTCI01JPM156N",  # OECD-Quelle, ~2 Monate Verzug
    "bok_diskontsatz": "INTDSRKRM193N",  # OECD-Quelle, ~2 Monate Verzug
}

# PBoC: keine offiziell dokumentierte API (der amtliche LPR-Herausgeber
# chinamoney.com.cn veroeffentlicht nur ein Bild). Eastmoney (einer der groessten
# chinesischen Finanzdatenanbieter) hat einen strukturierten JSON-Endpunkt, aufgedeckt
# ueber die Open-Source-Bibliothek `akshare` (macro_china_lpr()) - NICHT offiziell
# dokumentiert/versioniert, kann sich ohne Vorankuendigung aendern (siehe Kap. 8).
EASTMONEY_URL = "https://datacenter-web.eastmoney.com/api/data/v1/get"
EASTMONEY_LPR_TOKEN = "894050c76af8597a853f5b408b759f5d"


@dataclass
class FearGreedReading:
    value: int
    classification: str


@dataclass
class FredObservation:
    series_id: str
    date: str
    value: float | None  # None, falls FRED "." liefert (kein Wert fuer diesen Zeitpunkt)


@dataclass
class PbocLprReading:
    date: str
    lpr_1y: float
    lpr_5y: float


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


def get_fred_latest(series_id: str, api_key: str, session: requests.Session | None = None) -> FredObservation:
    session = session or requests.Session()
    response = session.get(
        FRED_BASE_URL,
        params={
            "series_id": series_id,
            "api_key": api_key,
            "file_type": "json",
            "sort_order": "desc",
            "limit": 1,
        },
        timeout=15,
    )
    response.raise_for_status()
    data = response.json()
    obs = data["observations"][0]
    value = None if obs["value"] == "." else float(obs["value"])
    return FredObservation(series_id=series_id, date=obs["date"], value=value)


def get_all_fred_rates(
    api_key: str, session: requests.Session | None = None
) -> dict[str, FredObservation | None]:
    """P-10: ein fehlgeschlagener Einzel-Call blockiert nicht die anderen Series -
    jede wird separat versucht, Fehler geloggt, Ergebnis fuer diese Series ist dann
    None statt die gesamte Makro-Abfrage abzubrechen."""
    session = session or requests.Session()
    results: dict[str, FredObservation | None] = {}
    for name, series_id in FRED_SERIES.items():
        try:
            results[name] = get_fred_latest(series_id, api_key, session)
        except Exception as exc:  # noqa: BLE001 - eine Series darf die anderen nicht blockieren
            logger.warning("FRED-Abruf fuer %s (%s) fehlgeschlagen: %s", name, series_id, exc)
            results[name] = None
    return results


def get_pboc_lpr(session: requests.Session | None = None) -> PbocLprReading:
    """PBoC-Leitzins (Loan Prime Rate) ueber Eastmoney, siehe Modul-Docstring/Kap. 8
    fuer den Vorbehalt (inoffizieller Endpunkt). Aendert sich nur ca. 1x/Monat -
    Aufrufer sollte bei Fehlschlag den letzten bekannten Wert behalten (P-10), nicht
    wiederholt aggressiv retryen."""
    session = session or requests.Session()
    params = {
        "reportName": "RPTA_WEB_RATE",
        "columns": "ALL",
        "sortColumns": "TRADE_DATE",
        "sortTypes": "-1",
        "token": EASTMONEY_LPR_TOKEN,
        "pageNumber": "1",
        "pageSize": "1",
    }
    response = session.get(EASTMONEY_URL, params=params, timeout=15)
    response.raise_for_status()
    data = response.json()
    entry = data["result"]["data"][0]
    date = str(entry["TRADE_DATE"]).split(" ")[0]
    return PbocLprReading(date=date, lpr_1y=float(entry["LPR1Y"]), lpr_5y=float(entry["LPR5Y"]))
