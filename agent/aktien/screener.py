"""Einfacher Aktien/ETF-Kandidaten-Screener (2026-07-19, Nutzer-Wunsch nach der
FINRA-Datenquellen-Runde: "analog Marktscan" fuer Aktien/Rohstoffe/ETF). Bewusst
KEIN Aequivalent zum vierstufigen Krypto-Marktscan (`agent/krypto/marktscan.py`,
Stufe A-D mit Regime-Gewichtung + Groq-Writeup) - der Nutzer bat ausdruecklich um
"einen einfachen Screener": manueller Trigger, keine Persistenz, kein automatischer
LLM-Call. Ergebnis ist eine reine Kandidatenliste, die der Nutzer manuell per
`config.add_watchlist_entry()` uebernehmen kann (Bewertung passiert danach ganz
regulaer ueber `agent/multi_asset_batch.py`, keine Doppelspur).

ZWEI GETRENNTE QUELLEN, bewusst asymmetrisch (siehe Docstrings der beiden
Funktionen unten) - kein Rohstoff-Screener, da das Rohstoff-Universum (WisdomTree-
ETCs) zu klein/spezialisiert fuer eine sinnvolle automatische Kandidatensuche ist.

WICHTIGER BITPANDA-FUND (2026-07-19, im Zuge dieser Implementierung entdeckt): ALLE
9 aktuell gehaltenen Rohstoff-/Themen-ETF-Positionen (OD7N/OD7H/OD7C/OD7L/VVMX/X136/
EXH3/CEBS/ISOC) sind laut `api.bitpanda.is_listed()` NICHT bei Bitpanda gelistet -
nur die beiden Aktien (VST/PLTR) sind es. Bitpanda fuehrt zwar eigene ETF/ETC-
"Themenkoerbe" (z.B. "COPPERMINE", "NATGAS"), das sind aber ANDERE, eigene
Bitpanda-Produkte, keine echten UCITS-ETFs/WisdomTree-ETCs wie in der Watchlist -
der Nutzer haelt diese Positionen also nachweislich ueber einen anderen Broker.
Das begruendet die asymmetrische Architektur unten: fuer Aktien ist Bitpanda-
Listing ein sinnvoller Zusatzfilter (VST/PLTR sind ja tatsaechlich dort gelistet),
fuer ETF/ETC ist Bitpandas eigener Themenkorb-Katalog selbst die realistischste
Kandidatenquelle (da echte UCITS-ETF-Discovery ueber yfinance ohnehin nicht zu
Bitpandas Angebot passen wuerde)."""
from __future__ import annotations

import logging
from dataclasses import dataclass

import yfinance as yf

import config
from api.bitpanda import BitpandaAsset, is_listed
from database.api_health import track_api_health

logger = logging.getLogger(__name__)

# Vordefinierte Yahoo-Finance-Screens (kein API-Key noetig, live verifiziert
# 2026-07-19) - bewusst eine Mischung aus Momentum (day_gainers) und Qualitaet/
# Value (growth_technology_stocks, undervalued_growth_stocks), damit der
# Screener nicht nur kurzfristige "Hype"-Kandidaten liefert.
_AKTIEN_SCREENS = ("day_gainers", "growth_technology_stocks", "undervalued_growth_stocks")
_AKTIEN_SCREEN_COUNT = 60

# Filter-Schwellenwerte gegen Mikro-/Pennystock-Rauschen (day_gainers ist sonst
# voller duenn gehandelter Nebenwerte) - bewusst konservativ, kein Anspruch auf
# Optimalitaet, jederzeit in config.yaml nachjustierbar falls zu eng/weit.
MIN_MARKTKAP_USD = 500_000_000
MIN_TAGESVOLUMEN = 500_000


@dataclass
class ScreenerCandidate:
    symbol: str
    name: str
    assetklasse: str  # "aktien" | "etf"
    quelle: str  # z.B. "day_gainers" oder "bitpanda_katalog"
    preis_usd: float | None
    marktkap_usd: float | None
    aenderung_pct: float | None
    bitpanda_gelistet: bool | None  # None nur wenn kein Bitpanda-Abgleich moeglich war
    hinweis: str | None = None
    hauptgruppe: str | None = None  # nur bei automatischer Klassifikation ueber kategorien.yaml
    unterkategorie: str | None = None


def _bereits_in_watchlist(symbol: str, watchlist) -> bool:
    symbol_upper = symbol.upper()
    for asset in watchlist:
        if asset.symbol.upper() == symbol_upper:
            return True
        if asset.yfinance_symbol and asset.yfinance_symbol.upper() == symbol_upper:
            return True
    return False


@track_api_health("yfinance")
def scan_aktien_candidates(
    watchlist, bitpanda_assets: list[BitpandaAsset] | None = None,
) -> list[ScreenerCandidate]:
    """Durchsucht 3 vordefinierte Yahoo-Finance-Screens nach neuen Aktien-
    Kandidaten (noch nicht in der Watchlist), filtert Mikro-Caps/Illiquides
    heraus und markiert pro Kandidat, ob er bei Bitpanda kaufbar ist (sofern
    `bitpanda_assets` mitgegeben wird - sonst bleibt `bitpanda_gelistet=None`,
    kein Fehler, siehe P-8). Dedupliziert ueber alle 3 Screens per Symbol."""
    quotes_by_symbol: dict[str, dict] = {}
    for screen_name in _AKTIEN_SCREENS:
        try:
            result = yf.screen(screen_name, count=_AKTIEN_SCREEN_COUNT)
        except Exception as exc:
            logger.warning("Yahoo-Finance-Screen %r fehlgeschlagen (wird uebersprungen): %s", screen_name, exc)
            continue
        for quote in result.get("quotes", []):
            symbol = quote.get("symbol")
            if not symbol or symbol in quotes_by_symbol:
                continue
            quotes_by_symbol[symbol] = {**quote, "_quelle": screen_name}

    candidates: list[ScreenerCandidate] = []
    for symbol, quote in quotes_by_symbol.items():
        if quote.get("quoteType") != "EQUITY":
            continue
        marktkap = quote.get("marketCap")
        volumen = quote.get("averageDailyVolume3Month")
        if marktkap is not None and marktkap < MIN_MARKTKAP_USD:
            continue
        if volumen is not None and volumen < MIN_TAGESVOLUMEN:
            continue
        if _bereits_in_watchlist(symbol, watchlist):
            continue

        name = quote.get("longName") or quote.get("shortName") or symbol
        bitpanda_gelistet = is_listed(symbol, bitpanda_assets, name=name) if bitpanda_assets is not None else None

        candidates.append(ScreenerCandidate(
            symbol=symbol,
            name=name,
            assetklasse="aktien",
            quelle=quote["_quelle"],
            preis_usd=quote.get("regularMarketPrice"),
            marktkap_usd=marktkap,
            aenderung_pct=quote.get("regularMarketChangePercent"),
            bitpanda_gelistet=bitpanda_gelistet,
        ))

    candidates.sort(key=lambda c: c.marktkap_usd or 0, reverse=True)
    return candidates


def scan_etf_candidates(watchlist, bitpanda_assets: list[BitpandaAsset]) -> list[ScreenerCandidate]:
    """Enumeriert Bitpandas EIGENEN ETF/ETC-Themenkorb-Katalog direkt (KEIN
    yfinance-Screen) - siehe Modul-Docstring fuer die Begruendung: dies IST das
    tatsaechlich bei Bitpanda kaufbare ETF/ETC-Angebot, waehrend eine echte
    UCITS-ETF-Discovery ueber yfinance an Bitpandas Sortiment vorbeigehen wuerde.
    `bitpanda_gelistet` ist hier immer True (definitionsgemaess, da direkt aus
    dem Bitpanda-Katalog stammend). KEIN `yfinance_symbol` ableitbar - Bitpandas
    Symbole (z.B. "COPPERMINE") sind eigene Produktnamen, keine Boersenticker;
    wer einen Kandidaten uebernimmt, muss das yfinance-Symbol (falls gewuenscht)
    selbst recherchieren (P-8, `agent/aktien/pipeline.py` degradiert bei
    fehlendem yfinance_symbol bereits sauber auf "keine technische Historie",
    siehe Ticket #319).

    Jeder Kandidat wird per `config.find_kategorie_fuer_bitpanda_symbol()`
    automatisch mit Hauptgruppe/Unterkategorie aus `Basisinfos/kategorien.yaml`
    getaggt (None wenn das Symbol dort nicht gelistet ist - z.B. ganz neue
    Bitpanda-Produkte, kein Fehler). BEWUSST KEIN "bessere Produkte filtern"-
    Qualitaetsvergleich hier: Bitpandas eigene ETF/ETC-Themenkoerbe haben
    keinen echten yfinance-Ticker und damit keine oeffentliche AUM/Kostenquote
    (siehe `api/asset_quality.py`-Modul-Docstring fuer die volle Begruendung)
    - ein Vergleich "welches Produkt ist besser" ist fuer diese Kandidaten
    strukturell nicht moeglich, nur fuer echte Boersen-ETFs (dort gibt es das
    neue Kompositions-/Qualitaetsmodul bereits, aufrufbar ueber die Watchlist)."""
    candidates: list[ScreenerCandidate] = []
    for asset in bitpanda_assets:
        if asset.group not in ("etf", "etc"):
            continue
        if _bereits_in_watchlist(asset.symbol, watchlist):
            continue
        kategorie = config.find_kategorie_fuer_bitpanda_symbol(asset.symbol)
        candidates.append(ScreenerCandidate(
            symbol=asset.symbol,
            name=asset.name,
            assetklasse="etf",
            quelle="bitpanda_katalog",
            preis_usd=None,
            marktkap_usd=None,
            aenderung_pct=None,
            bitpanda_gelistet=True,
            hinweis="Bitpanda-eigenes Produkt, kein yfinance-Symbol automatisch ableitbar.",
            hauptgruppe=kategorie[0] if kategorie else None,
            unterkategorie=kategorie[1] if kategorie else None,
        ))
    candidates.sort(key=lambda c: c.name)
    return candidates
