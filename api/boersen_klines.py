# -*- coding: utf-8 -*-
"""Echte Tageskerzen von Binance und Bybit - die Rueckfallquelle fuer Krypto.

WARUM DIESE DATEI DREI ANDERE ERSETZT (12.08.2026).

Fuer Krypto ohne Kraken-Listing gab es nacheinander zwei Rueckfaelle, und beide
waren die schlechtere Wahl:

  * `api/coingecko_ohlc_fallback.py` (03.08.) liefert ueber `/ohlc` gar KEINE
    Tageskerzen. Gemessen: Vier-Tage-Kerzen, abgelegt neben Krakens
    Tageskerzen, ohne Vermerk. Jeder "20-Tage"-Indikator rechnete dort ueber
    80 Kalendertage.
  * `api/yfinance_krypto_fallback.py` (11.08.) liefert Tageskerzen, aber ueber
    einen geratenen Ticker: `<SYM>-USD`. Von acht geprueften gehoerten DREI
    einem anderen, toten Asset - VSN mit 972 Kerzen haette jede Laengenpruefung
    bestanden. Nur die Preis-Gegenprobe fing das ab.

Die Boersen-Klines haben beide Probleme nicht:

    Deckung          41 von 42 Symbolen, die Kerzen brauchen (yfinance: 39)
    Granularitaet    Median-Abstand 1 Tag, geprueft
    Tiefe            1.000 Kerzen je Abruf, rund 2,7 Jahre
    Eindeutigkeit    das Boersensymbol selbst - keine Verwechslung moeglich
    Aufwand          DIESELBE API, die wir fuer Funding, Open Interest und
                     Long/Short ohnehin rufen. Kostenlos, ohne Schluessel

KEINE PREIS-GEGENPROBE NOETIG, und das ist der eigentliche Gewinn. Bei yfinance
war sie Pflicht, weil "KAIA-USD" ein beliebiges Yahoo-Papier sein kann. Hier
fragen wir die Boerse nach ihrem eigenen Paar `KAIAUSDT` - was sie liefert, IST
dieses Paar. Ein ganzer Fehlerpfad entfaellt, statt abgesichert zu werden.

VORRANG: Kraken bleibt erste Quelle (unsere Handelsboerse fuer die gelisteten
Paare). Diese hier bedient nur, was dort fehlt. Genau EINE Quelle je Symbol -
zwei zu mischen ergaebe Kerzen, die es an keiner Boerse gab.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

import requests

from database.api_health import track_api_health
from database.models import OhlcPoint

logger = logging.getLogger(__name__)

BINANCE_KLINES_URL = "https://api.binance.com/api/v3/klines"
BYBIT_KLINES_URL = "https://api.bybit.com/v5/market/kline"
MAX_KERZEN = 1000

# Symbole, die keine Kerzen brauchen - Begruendung je Eintrag:
#   EURCV  Stablecoin, per Konstruktion flach. Eine flache Reihe ist fuer jeden
#          Indikator ein konstantes Feld (B10).
#   VSN    Wertpapier, laeuft ueber yfinance_history (nicht ueber Krypto).
OHNE_KERZEN = ("EURCV", "VSN")


def _tag(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).date().isoformat()


def _ist_taeglich(punkte: list[OhlcPoint]) -> bool:
    """Median-Abstand genau ein Tag? Dieselbe Pruefung wie an jeder anderen
    Quelle - eine Quelle, die sich nicht selbst prueft, verlaesst sich darauf,
    dass eine spaetere Stufe ihren Fehler faengt."""
    from datetime import date
    if len(punkte) < 3:
        return True
    tage = [date.fromisoformat(p.date) for p in punkte]
    ab = sorted((tage[i + 1] - tage[i]).days for i in range(len(tage) - 1))
    median = ab[len(ab) // 2]
    if median != 1:
        logger.warning("Klines im Median-Abstand von %d Tagen - keine "
                       "Tageskerzen, werden nicht gespeichert.", median)
        return False
    return True


@track_api_health("binance")
def hole_binance(symbol: str, currency: str = "USD",
                 session: requests.Session | None = None) -> list[OhlcPoint]:
    session = session or requests.Session()
    r = session.get(BINANCE_KLINES_URL,
                    params={"symbol": f"{symbol}USDT", "interval": "1d",
                            "limit": MAX_KERZEN}, timeout=20)
    r.raise_for_status()
    jetzt = datetime.now(timezone.utc).isoformat()
    # [oeffnungszeit, open, high, low, close, volume, ...]
    return [OhlcPoint(symbol=symbol, currency=currency, date=_tag(int(z[0])),
                      open=float(z[1]), high=float(z[2]), low=float(z[3]),
                      close=float(z[4]), volume=float(z[5]), fetched_at=jetzt)
            for z in r.json() or []]


@track_api_health("bybit")
def hole_bybit(symbol: str, currency: str = "USD",
               session: requests.Session | None = None) -> list[OhlcPoint]:
    """Bybit liefert absteigend; hier aufsteigend zurueck, damit beide Quellen
    dasselbe Format haben und ein Aufrufer sie nicht verwechseln kann."""
    session = session or requests.Session()
    r = session.get(BYBIT_KLINES_URL,
                    params={"category": "spot", "symbol": f"{symbol}USDT",
                            "interval": "D", "limit": MAX_KERZEN}, timeout=20)
    r.raise_for_status()
    liste = ((r.json().get("result") or {}).get("list")) or []
    jetzt = datetime.now(timezone.utc).isoformat()
    punkte = [OhlcPoint(symbol=symbol, currency=currency, date=_tag(int(z[0])),
                        open=float(z[1]), high=float(z[2]), low=float(z[3]),
                        close=float(z[4]), volume=float(z[5]), fetched_at=jetzt)
              for z in liste]
    return sorted(punkte, key=lambda p: p.date)


def braucht_rueckfall(asset) -> bool:
    """Krypto, kein Kraken-Paar, kein Sonderfall."""
    from api.kraken import KRAKEN_PAIR_MAP
    if getattr(asset, "assetklasse", None) != "krypto":
        return False
    if getattr(asset, "symbol", None) in OHNE_KERZEN:
        return False
    return KRAKEN_PAIR_MAP.get(asset.symbol) is None


def hole_tageskerzen(symbol: str, currency: str = "USD",
                     session: requests.Session | None = None) -> list[OhlcPoint]:
    """Binance zuerst, Bybit als Rueckfall. GENAU EINE Quelle je Symbol."""
    for holen in (hole_binance, hole_bybit):
        try:
            punkte = holen(symbol, currency, session)
        except Exception as e:                                   # noqa: BLE001
            logger.info("Klines fuer %s bei %s fehlgeschlagen: %s", symbol,
                        holen.__name__, type(e).__name__)
            continue
        if punkte and _ist_taeglich(punkte):
            return punkte
    return []


def fuelle_luecken(conn, watchlist, trocken: bool = True) -> list[dict]:
    """Alle Krypto-Assets ohne Kraken-Listing.

    `trocken=True` ist die Vorgabe: ein Schreibzugriff auf die Kursdaten ist
    eine Produktionshandlung."""
    import database.db as db
    ergebnisse = []
    for asset in watchlist or []:
        if not braucht_rueckfall(asset):
            continue
        punkte = hole_tageskerzen(asset.symbol, "USD")
        zeile = {"symbol": asset.symbol, "kerzen": len(punkte),
                 "von": punkte[0].date if punkte else None,
                 "bis": punkte[-1].date if punkte else None}
        if punkte and not trocken:
            db.upsert_ohlc_points(conn, punkte, quelle="gemessen")
            conn.commit()
        elif not punkte:
            logger.info("Keine Tageskerzen fuer %s an beiden Boersen",
                        asset.symbol)
        ergebnisse.append(zeile)
    return ergebnisse
