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
import re
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
EASTMONEY_M2_REPORT = "RPT_ECONOMY_CURRENCY_SUPPLY"  # kein Token noetig (anders als LPR)

# Globale M2-Gesamtsicht (Liquiditaetszyklus-Diskussion, 2026-07-08, siehe
# Spezifikation Kap. 8/16) - USA laeuft bereits ueber FRED (m2_geldmenge), hier die
# Ergaenzung um Eurozone/China/Japan.

# EZB-eigene SDMX-API (nicht FRED - FREDs Eurozone-M2-Kopie war seit 2017 tot, siehe
# Kap. 8) - Series-Key live ermittelt, kein API-Key noetig.
ECB_SDMX_BASE_URL = "https://data-api.ecb.europa.eu/service/data"
ECB_M2_SERIES_KEY = "BSI/M.U2.Y.V.M20.X.1.U2.2300.Z01.E"

# Japan-M2: KEINE der beiden FRED-Kopien (tot seit 2016/17) UND KEINE nutzbare
# Anbindung an die 2026 gestartete BoJ-JSON-API gefunden (zu neu/kaum dokumentiert -
# selbst die Community-Bibliothek `bojpy` scraped aus demselben Grund HTML statt die
# neue API zu nutzen). Deshalb bewusster HTML-Scraping-Fallback der oeffentlichen
# Statistik-Tabellenseite - fragiler als eine echte API (Spaltenreihenfolge koennte
# sich aendern), aber live verifiziert funktionsfaehig (2026-07-08, Update taeglich
# 15:00 JST laut Seite). Faellt bei strukturellen Aenderungen der Seite mit einem
# klaren ValueError aus, nicht mit einem stillen Falschwert.
BOJ_M2_URL = "https://www.stat-search.boj.or.jp/ssi/mtshtml/md02_m_1_en.html"


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


@dataclass
class RegionalM2Reading:
    region: str
    date: str
    value: float
    unit: str  # Rohe gemeldete Einheit je Quelle, bewusst NICHT umgerechnet/vereinheitlicht


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


def get_fred_history(
    series_id: str, api_key: str, observation_start: str, session: requests.Session | None = None
) -> list[FredObservation]:
    """Fuer Trend-/Richtungsberechnungen (Liquiditaets-Regime, agent/regime.py) reicht
    der letzte Wert allein nicht - FRED veroeffentlicht die volle Historie ueber
    denselben Endpunkt wie `get_fred_latest`, nur mit `observation_start` statt
    `limit=1`. Genutzt fuer Fed Funds Rate + US-M2, damit der Liquiditaets-Trend ab dem
    ersten Lauf verfuegbar ist statt erst nach Monaten manuell angehaeufter
    `macro_snapshot`-Zeilen (die Pipeline laeuft nur bei manuellem "Signal
    berechnen"-Klick, kein taeglicher Scheduler - siehe agent/pipeline.py)."""
    session = session or requests.Session()
    response = session.get(
        FRED_BASE_URL,
        params={
            "series_id": series_id,
            "api_key": api_key,
            "file_type": "json",
            "sort_order": "asc",
            "observation_start": observation_start,
        },
        timeout=15,
    )
    response.raise_for_status()
    data = response.json()
    return [
        FredObservation(
            series_id=series_id, date=o["date"], value=None if o["value"] == "." else float(o["value"])
        )
        for o in data["observations"]
    ]


def get_ecb_m2_history(n_observations: int = 13, session: requests.Session | None = None) -> list[RegionalM2Reading]:
    """Wie `get_fred_history`: mehrere Beobachtungen statt nur der letzten, fuer den
    Liquiditaets-Trend. `n_observations=13` deckt >1 Jahr ab (EZB-M2 ist monatlich)."""
    session = session or requests.Session()
    response = session.get(
        f"{ECB_SDMX_BASE_URL}/{ECB_M2_SERIES_KEY}",
        params={"lastNObservations": n_observations, "format": "jsondata"},
        timeout=15,
    )
    response.raise_for_status()
    data = response.json()
    times = data["structure"]["dimensions"]["observation"][0]["values"]
    series_key = next(iter(data["dataSets"][0]["series"]))
    obs = data["dataSets"][0]["series"][series_key]["observations"]
    return [
        RegionalM2Reading(region="eurozone", date=t["id"], value=float(obs[str(i)][0]), unit="Mio. EUR")
        for i, t in enumerate(times)
        if str(i) in obs
    ]


def get_china_m2_history(n_observations: int = 13, session: requests.Session | None = None) -> list[RegionalM2Reading]:
    """Wie `get_fred_history`: mehrere Beobachtungen statt nur der letzten, fuer den
    Liquiditaets-Trend. `n_observations=13` deckt >1 Jahr ab (China-M2 ist monatlich)."""
    session = session or requests.Session()
    params = {
        "columns": "REPORT_DATE,TIME,BASIC_CURRENCY,BASIC_CURRENCY_SAME,BASIC_CURRENCY_SEQUENTIAL",
        "pageNumber": "1",
        "pageSize": str(n_observations),
        "sortColumns": "REPORT_DATE",
        "sortTypes": "-1",
        "source": "WEB",
        "client": "WEB",
        "reportName": EASTMONEY_M2_REPORT,
    }
    response = session.get(EASTMONEY_URL, params=params, timeout=15)
    response.raise_for_status()
    data = response.json()
    entries = data["result"]["data"]
    return [
        RegionalM2Reading(
            region="china", date=str(e["REPORT_DATE"]).split(" ")[0], value=float(e["BASIC_CURRENCY"]),
            unit="hundert Mio. CNY",
        )
        for e in reversed(entries)  # Eastmoney liefert absteigend (neuestes zuerst) -> umdrehen fuer aufsteigend
    ]


def get_ecb_m2(session: requests.Session | None = None) -> RegionalM2Reading:
    """Eurozone-M2 (Average Amounts Outstanding) direkt von der EZB-eigenen SDMX-API,
    kein API-Key noetig. Live verifiziert 2026-07-08."""
    session = session or requests.Session()
    response = session.get(
        f"{ECB_SDMX_BASE_URL}/{ECB_M2_SERIES_KEY}",
        params={"lastNObservations": 1, "format": "jsondata"},
        timeout=15,
    )
    response.raise_for_status()
    data = response.json()
    times = data["structure"]["dimensions"]["observation"][0]["values"]
    series_key = next(iter(data["dataSets"][0]["series"]))
    obs = data["dataSets"][0]["series"][series_key]["observations"]
    date = times[-1]["id"]
    value = obs[str(len(times) - 1)][0]
    return RegionalM2Reading(region="eurozone", date=date, value=float(value), unit="Mio. EUR")


def get_china_m2(session: requests.Session | None = None) -> RegionalM2Reading:
    """China-M2 ueber denselben Eastmoney-Endpunkt wie PBoC-LPR, anderer reportName,
    kein Token noetig. Live verifiziert 2026-07-08."""
    session = session or requests.Session()
    params = {
        "columns": "REPORT_DATE,TIME,BASIC_CURRENCY,BASIC_CURRENCY_SAME,BASIC_CURRENCY_SEQUENTIAL",
        "pageNumber": "1",
        "pageSize": "1",
        "sortColumns": "REPORT_DATE",
        "sortTypes": "-1",
        "source": "WEB",
        "client": "WEB",
        "reportName": EASTMONEY_M2_REPORT,
    }
    response = session.get(EASTMONEY_URL, params=params, timeout=15)
    response.raise_for_status()
    data = response.json()
    entry = data["result"]["data"][0]
    date = str(entry["REPORT_DATE"]).split(" ")[0]
    return RegionalM2Reading(
        region="china", date=date, value=float(entry["BASIC_CURRENCY"]), unit="hundert Mio. CNY"
    )


def get_japan_m2(session: requests.Session | None = None) -> RegionalM2Reading:
    """Japan-M2 (Average Amounts Outstanding) - HTML-Scraping-Fallback, siehe
    Modul-Docstring bei BOJ_M2_URL fuer den Vorbehalt. Sucht die Spalte
    "M2/Average Amounts Outstanding/Money Stock" dynamisch (nicht per festem Index),
    damit eine Spalten-Umsortierung nicht zu einem stillen Falschwert fuehrt - schlaegt
    stattdessen mit ValueError fehl."""
    session = session or requests.Session()
    response = session.get(BOJ_M2_URL, timeout=15)
    response.raise_for_status()
    html = response.text

    header_idx = html.find("Name of <br>time-series")
    if header_idx == -1:
        raise ValueError("BoJ-Tabellenkopf nicht gefunden - Seitenstruktur hat sich vermutlich geändert")
    header_segment = html[header_idx : header_idx + 8000]
    column_names = re.findall(r"<td[^>]*>([^<]*Money Stock[^<]*)</td>", header_segment)
    m2_col_index = next(
        (i for i, name in enumerate(column_names) if name.startswith("M2/Average Amounts Outstanding")),
        None,
    )
    if m2_col_index is None:
        raise ValueError("M2-Spalte (Average Amounts Outstanding) nicht in der BoJ-Tabelle gefunden")

    row_matches = list(
        re.finditer(r"<tr nowrap align=right><th[^>]*>(\d{4}/\d{2})</th>((?:<td[^>]*>[^<]*</td>)+)", html)
    )
    if not row_matches:
        raise ValueError("Keine Datenzeile in der BoJ-Tabelle gefunden")
    last_date, last_row_html = row_matches[-1].groups()
    values = re.findall(r"<td[^>]*>([^<]*)</td>", last_row_html)
    return RegionalM2Reading(
        region="japan", date=last_date, value=float(values[m2_col_index].strip()), unit="100 Mio. JPY"
    )


def get_all_regional_m2(session: requests.Session | None = None) -> dict[str, RegionalM2Reading | None]:
    """Ergaenzt US-M2 (bereits ueber FRED/get_all_fred_rates) um Eurozone/China/Japan
    fuer eine globale M2-Gesamtsicht (Liquiditaetszyklus-Diskussion, Spezifikation
    Kap. 8/16). P-10: jede Region einzeln versucht, ein Fehlschlag blockiert nicht
    die anderen."""
    session = session or requests.Session()
    fetchers = {"eurozone": get_ecb_m2, "china": get_china_m2, "japan": get_japan_m2}
    results: dict[str, RegionalM2Reading | None] = {}
    for name, fetcher in fetchers.items():
        try:
            results[name] = fetcher(session)
        except Exception as exc:  # noqa: BLE001 - eine Region darf die anderen nicht blockieren
            logger.warning("Regionale M2-Abfrage fuer %s fehlgeschlagen: %s", name, exc)
            results[name] = None
    return results
