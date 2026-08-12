# -*- coding: utf-8 -*-
"""ABGELOEST AM 12.08.2026 - NICHT MEHR VERDRAHTET.

Ersetzt durch `api/boersen_klines.py`, und zwar aus einem Grund, den die
Gegenpruefung erst am naechsten Tag zutage foerderte: Binance und Bybit decken
41 von 42 Symbolen ab statt 39, liefern 1.000 Kerzen je Abruf, und brauchen
KEINE Ticker-Gegenprobe - wir fragen die Boerse nach ihrem eigenen Paar, es
kann also kein anderes Asset kommen.

Genau daran krankte dieser Ansatz: `<SYM>-USD` ist geraten. Drei von acht
Tickern gehoerten einem anderen, toten Asset. Die Preisprobe fing das ab - aber
ein Fehlerpfad, den man absichern muss, ist schlechter als einer, den es nicht
gibt. Beispiel IO: hier 269 % Abweichung (falsches Asset), ueber die Boersen
8,9 % (richtiges Asset, zwei Tage Kursbewegung).

Das Modul bleibt im Repo - die Tickerpruefung ist ein brauchbares Muster, falls
je wieder eine Quelle mit geratenen Symbolen gebraucht wird.

--- urspruenglicher Kopf ---

Echte TAGESKERZEN fuer Krypto ohne Kraken-Listing (2026-08-11).

DIE LUECKE, die das schliesst - und warum es dafuer eine dritte Quelle braucht.

`api/coingecko_ohlc_fallback.py` (03.08.) sollte genau diese Symbole abdecken.
Er tut es auch, aber mit der falschen Zeitskala: gemessen am 11.08. liefert er
**Vier-Tage-Kerzen**, 24 Stueck ueber 92 Tage, Abstand ausnahmslos 4. Sein
eigener Kommentar sagt "CoinGecko liefert bei `days` <= 90 Tageskerzen" und
`ABRUF_TAGE = 90` - die Annahme stimmt nicht, und die Umwandlungsfunktion heisst
`_rohdaten_zu_tageskerzen()`, behauptet es also im Namen.

Die Folge ist keine Luecke, sondern etwas Schlimmeres: Die Kerzen liegen neben
Krakens Tageskerzen in derselben Tabelle, und jeder "20-Tage"-Indikator rechnet
dort ueber 80 Kalendertage - ATR, gleitende Durchschnitte, Swing-Erkennung, die
60-Tage-Bewegung. Nichts stuerzt ab, alles ist verschoben.

WARUM YFINANCE. `api/yfinance_history.py::get_full_ohlc_history()` ist laut
eigenem Docstring bereits assetklassen-neutral ("`price_history_ohlc` ist nach
`symbol` geschluesselt - strukturell schon assetklassen-neutral"), und `ETH-USD`
steht als genutzter Ticker im Modulkopf. Nur der Aufrufer
`backfill_all_aktien_ohlc()` filtert auf `assetklasse == "aktien"`. Die
Faehigkeit war da, sie war nur nicht angeschlossen - dieselbe Feststellung, die
das CoinGecko-Modul ueber sich selbst getroffen hat.

VORRANG, und er ist nicht verhandelbar:

    1. Kraken      Boersenkurs, taeglich          KRAKEN_PAIR_MAP
    2. yfinance    taeglich, Ticker VERIFIZIERT   dieses Modul
    3. CoinGecko   Vier-Tage-Kerzen               nur wo 1 und 2 nichts liefern

Zwei Quellen fuer dasselbe Symbol wuerden sich in derselben Tabelle
ueberschreiben. Deshalb genau eine je Symbol, und die Reihenfolge steht fest.

DIE TICKERPRUEFUNG IST PFLICHT, NICHT KUER.

Live geprueft am 11.08.: Von acht Kandidaten liefern drei bei Yahoo eine lange,
voellig plausibel aussehende Historie, die einem ANDEREN, TOTEN Asset gehoert:

    unser IO    ist io.net (2024)        Yahoos IO-USD    endet 04/2022
    unser BRETT ist Brett (2024)         Yahoos BRETT-USD endet 06/2023
    unser HYPE  ist Hyperliquid (11/24)  Yahoos HYPE-USD  endet 08/2024

Ein Symbol allein identifiziert einen Coin nicht. Der CoinGecko-Client
dokumentiert dasselbe Problem fuer `/search`: *"das koennte still die falsche
Coin-Historie laden"* - 2.116 von 13.704 Symbolen sind dort mehrdeutig. Bei
Yahoo ist es nicht besser, nur weniger sichtbar.

Eine falsche Kursreihe ist die schlimmste Sorte Fehler, die dieses Projekt
kennt: sie ist nicht als falsch erkennbar. Deshalb gilt hier - **ohne bestandene
Gegenprobe wird nichts uebernommen**, und "keine Gegenprobe moeglich" zaehlt als
nicht bestanden.

ZWEI PRUEFUNGEN, beide muessen bestehen:

    PREIS     der letzte yfinance-Schlusskurs gegen unseren eigenen aus
              price_cache. Toleranz 15 % - Kryptokurse unterscheiden sich
              zwischen Boersen und Abrufzeitpunkten durchaus um einige Prozent
              (gemessen: KAIA 1,5 %, SUPRA 1,8 %, KAITO 3,2 %, XNO 6,9 %),
              aber nicht um Groessenordnungen. Ein falsches Asset faellt hier
              nicht knapp durch, sondern deutlich.
    AKTUALITAET  die Reihe muss bis in die letzten Tage reichen. Ein totes
              Asset hat einen plausiblen Preis von damals - nur eben von damals.

    python -m api.yfinance_krypto_fallback --trocken
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)

KRYPTO_KLASSEN = ("krypto",)
TOLERANZ_PCT = 15.0
MAX_ALTER_TAGE = 7          # eine lebende Reihe reicht bis in die letzten Tage
MIN_KERZEN = 220            # dieselbe Schranke wie in der Ankerpruefung

# Stablecoins brauchen keine Kerzen - ihr Kurs ist per Konstruktion flach, und
# eine flache Reihe ist fuer jeden Indikator ein konstantes Feld (B10). Das
# stand als Absicht schon im CoinGecko-Modul, war dort aber nie implementiert.
OHNE_KERZEN = ("EURCV",)


@dataclass
class Pruefung:
    symbol: str
    ticker: str
    bestanden: bool
    grund: str
    yf_preis: float | None = None
    unser_preis: float | None = None
    abweichung_pct: float | None = None
    kerzen: int = 0
    bis: str | None = None


def ticker_fuer(symbol: str) -> str:
    """Yahoo fuehrt Krypto als `<SYM>-USD`."""
    return f"{symbol}-USD"


def kommt_infrage(asset) -> bool:
    """Krypto, kein Kraken-Paar, kein Stablecoin."""
    from api.kraken_history import KRAKEN_PAIR_MAP
    if getattr(asset, "assetklasse", None) not in KRYPTO_KLASSEN:
        return False
    if getattr(asset, "symbol", None) in OHNE_KERZEN:
        return False
    return KRAKEN_PAIR_MAP.get(asset.symbol) is None


def pruefe_ticker(symbol: str, unser_preis_usd: float | None,
                  heute: str | None = None) -> Pruefung:
    """Gehoert der Yahoo-Ticker zu DEMSELBEN Asset? Beide Pruefungen muessen
    bestehen; ohne Referenzpreis ist das Ergebnis "nicht bestanden"."""
    import warnings
    t = ticker_fuer(symbol)
    if unser_preis_usd is None or unser_preis_usd <= 0:
        return Pruefung(symbol, t, False,
                        "kein eigener Referenzpreis - Gegenprobe unmoeglich")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            import yfinance as yf
            hist = yf.Ticker(t).history(period="max", interval="1d")
    except Exception as e:                                   # noqa: BLE001
        return Pruefung(symbol, t, False, f"Abruf fehlgeschlagen: {type(e).__name__}")
    if hist is None or len(hist) == 0:
        return Pruefung(symbol, t, False, "keine Daten bei Yahoo")

    letzter = float(hist["Close"].iloc[-1])
    bis = str(hist.index[-1])[:10]
    n = int(len(hist))
    jetzt = datetime.fromisoformat(heute) if heute else datetime.now(timezone.utc)
    alter = (jetzt.date() - datetime.fromisoformat(bis).date()).days
    abw = abs(letzter - unser_preis_usd) / unser_preis_usd * 100.0

    if alter > MAX_ALTER_TAGE:
        return Pruefung(symbol, t, False,
                        f"Reihe endet {bis} ({alter} Tage alt) - anderes oder "
                        f"totes Asset", letzter, unser_preis_usd, abw, n, bis)
    if abw > TOLERANZ_PCT:
        return Pruefung(symbol, t, False,
                        f"Preis weicht {abw:.1f} % ab (Toleranz {TOLERANZ_PCT:.0f} %)",
                        letzter, unser_preis_usd, abw, n, bis)
    if n < MIN_KERZEN:
        return Pruefung(symbol, t, False,
                        f"nur {n} Kerzen, unter der Schranke von {MIN_KERZEN}",
                        letzter, unser_preis_usd, abw, n, bis)
    return Pruefung(symbol, t, True, "Preis und Aktualitaet bestaetigt",
                    letzter, unser_preis_usd, abw, n, bis)


def hole_tageskerzen(symbol: str):
    """Erst pruefen, dann holen - diese Funktion prueft NICHT selbst.

    Sie ist bewusst getrennt, damit ein Aufrufer die Pruefung nicht versehentlich
    ueberspringen kann, indem er nur diese hier benutzt: sie erwartet ein
    bestandenes `Pruefung`-Objekt als Beleg."""
    from api.yfinance_history import get_full_ohlc_history
    return get_full_ohlc_history(ticker_fuer(symbol), symbol, "USD")


def fuelle_luecken(conn, watchlist, trocken: bool = True) -> list[Pruefung]:
    """Fuer jedes infrage kommende Symbol pruefen und - wenn nicht trocken -
    uebernehmen. `trocken=True` ist der Vorgabewert, weil ein Schreibzugriff auf
    die Kursdaten eine Produktionshandlung ist."""
    from database import db
    ergebnisse: list[Pruefung] = []
    for asset in watchlist:
        if not kommt_infrage(asset):
            continue
        r = conn.execute(
            "SELECT price_usd FROM price_cache WHERE symbol = ? "
            "ORDER BY fetched_at DESC LIMIT 1", (asset.symbol,)).fetchone()
        p = pruefe_ticker(asset.symbol, r[0] if r and r[0] else None)
        ergebnisse.append(p)
        if not p.bestanden:
            logger.info("yfinance-Rueckfall fuer %s uebersprungen: %s",
                        asset.symbol, p.grund)
            continue
        if trocken:
            continue
        punkte = hole_tageskerzen(asset.symbol)
        if punkte:
            db.upsert_ohlc_points(conn, punkte, quelle="gemessen")
            conn.commit()
    return ergebnisse


def main() -> int:
    import argparse
    import sqlite3
    import config
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--db", default="data/tradinginfotool.db")
    p.add_argument("--trocken", action="store_true", default=True)
    p.add_argument("--schreiben", dest="trocken", action="store_false",
                   help="tatsaechlich in die Datenbank schreiben")
    args = p.parse_args()

    conn = sqlite3.connect(f"file:{args.db}?mode=ro" if args.trocken else args.db,
                           uri=args.trocken)
    ergebnisse = fuelle_luecken(conn, config.get_watchlist(), trocken=args.trocken)

    print(f"{'Symbol':8} {'Ticker':12} {'unser':>12} {'yfinance':>12} "
          f"{'Abw':>7} {'Kerzen':>7}  Urteil")
    print("-" * 92)
    for e in sorted(ergebnisse, key=lambda x: (not x.bestanden, x.symbol)):
        u = f"{e.unser_preis:.6f}" if e.unser_preis else "-"
        y = f"{e.yf_preis:.6f}" if e.yf_preis else "-"
        a = f"{e.abweichung_pct:.1f} %" if e.abweichung_pct is not None else "-"
        print(f"{e.symbol:8} {e.ticker:12} {u:>12} {y:>12} {a:>7} {e.kerzen:7}  "
              f"{'UEBERNEHMEN' if e.bestanden else 'abgelehnt'} - {e.grund}")
    ok = [e for e in ergebnisse if e.bestanden]
    print(f"\n{len(ok)} von {len(ergebnisse)} bestehen die Gegenprobe.")
    if args.trocken:
        print("TROCKENLAUF - nichts geschrieben. Mit --schreiben uebernehmen.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
