# -*- coding: utf-8 -*-
"""Holt Funding-Rate und aktive Adressen in eigene Messdateien (30.08.2026).

⚠️ SCHREIBT NICHT IN DIE PRODUKTIONS-DB. Ziele:
    data/funding_historie.db   Binance Futures, 8-Stunden-Takt, ab 2019
    data/onchain_historie.db   Coin Metrics Community, taeglich, ab 2015

## Warum rueckwirkend moeglich

Im Projekt stand "Positionierung: Wirkung erst ab 22.10.2026 messbar" und
"TVL ab 18.09.2026". Beides beruhte darauf, dass die Module den
MOMENTAUFNAHME-Endpunkt abrufen. Geprueft am 30.08.:

    Funding-Rate   Binance /fapi/v1/fundingRate   ab 2019-09-10 = 7,0 Jahre
    Open Interest  Binance /futures/data/...      nur 30 Tage - NICHT holbar
    Aktive Adressen Coin Metrics Community        ETH 4.049 Punkte ab 2015

## Schonender Abruf

Funding: Pause 0,4 s (Binance-Limit ist weit hoeher, aber Nutzervorgabe
lautet "nicht zu schnell"). Coin Metrics: Limit 10 Anfragen / 6 s -> Pause
0,8 s, mit Reserve.

## Funding wird auf TAGE verdichtet

Die Rate faellt alle 8 Stunden an. Fuer die Messung zaehlt der Tageswert -
gebildet als SUMME der drei Zahlungen, denn genau das kostet ein Halten
ueber diesen Tag.
"""
import datetime as dt
import json
import sqlite3
import sys
import time
import urllib.error
import urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_eigenschaft_beitrag as B

KOPF = {"User-Agent": "TradingInfoTool/1.0 (Analyse, nicht kommerziell)"}


def hole(url, versuche=3, pause=1.0, timeout=60):
    for n in range(versuche):
        try:
            r = urllib.request.Request(url, headers=KOPF)
            with urllib.request.urlopen(r, timeout=timeout) as a:
                return json.loads(a.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
            if n == versuche - 1:
                raise
            time.sleep(pause * (n + 2))
    return None


def anlegen(conn, tabelle):
    conn.execute("""CREATE TABLE IF NOT EXISTS %s (
        symbol TEXT NOT NULL, datum TEXT NOT NULL, wert REAL NOT NULL,
        PRIMARY KEY (symbol, datum))""" % tabelle)
    conn.commit()


# ---------------------------------------------------------------------------
def funding(unsere, pause=0.4):
    print("=" * 78)
    print("A. FUNDING-RATE (Binance Futures)")
    print("=" * 78)
    info = hole("https://fapi.binance.com/fapi/v1/exchangeInfo")
    paare = {}
    # ⚠️ NUR PERPETUAL. Grosse Werte haben zusaetzlich Quartalskontrakte
    # (BTCUSDT_260925, BTCUSDT_261225) - die haben KEINE Funding-Rate. Ohne
    # diesen Filter ueberschreibt der Quartalskontrakt das Perpetual, und
    # ausgerechnet BTC und ETH fallen still aus (Fehler vom 30.08.2026,
    # gefunden erst bei der Abdeckungspruefung der Watchlist).
    for s in info.get("symbols", []):
        if (s.get("quoteAsset") == "USDT" and s.get("status") == "TRADING"
                and s.get("contractType") == "PERPETUAL"):
            basis = str(s.get("baseAsset") or "").upper()
            if basis in unsere:
                paare[basis] = s["symbol"]
    print("Unsere Symbole mit Binance-Futures-Paar: %d von %d"
          % (len(paare), len(unsere)))
    conn = sqlite3.connect("data/funding_historie.db")
    anlegen(conn, "funding")
    ok = 0
    for i, (basis, paar) in enumerate(sorted(paare.items()), 1):
        try:
            # ⚠️ MUSS bei 2019 beginnen und VORWAERTS paginieren.
            # Ohne `startTime` liefert Binance nur die letzten 500 Eintraege -
            # die Abbruchbedingung greift dann sofort, und man bekommt fuenf
            # Monate statt sieben Jahren (Fehler vom 30.08.2026, behoben).
            je_tag, runden = {}, 0
            start = int(dt.datetime(2019, 1, 1, tzinfo=dt.timezone.utc)
                        .timestamp() * 1000)
            while runden < 60:                       # Deckel gegen Endlosschleife
                url = ("https://fapi.binance.com/fapi/v1/fundingRate?symbol=%s"
                       "&limit=1000&startTime=%d" % (paar, start))
                d = hole(url, pause=pause)
                if not d:
                    break
                for e in d:
                    tag = dt.datetime.fromtimestamp(
                        e["fundingTime"] / 1000, dt.timezone.utc).date().isoformat()
                    je_tag[tag] = je_tag.get(tag, 0.0) + float(e["fundingRate"])
                if len(d) < 1000:
                    break
                start = d[-1]["fundingTime"] + 1
                runden += 1
                time.sleep(pause)
            if je_tag:
                conn.executemany("INSERT OR REPLACE INTO funding VALUES (?,?,?)",
                                 [(basis, t, v) for t, v in je_tag.items()])
                conn.commit()
                ok += 1
        except Exception as e:                       # noqa: BLE001
            print("  %-9s FEHLER: %s" % (basis, str(e)[:50]))
        if i % 20 == 0:
            print("  %3d von %d  (ok %d)" % (i, len(paare), ok))
        time.sleep(pause)
    n, s, a, b = conn.execute(
        "SELECT COUNT(*), COUNT(DISTINCT symbol), MIN(datum), MAX(datum) "
        "FROM funding").fetchone()
    print("FERTIG: %d Symbole, %d Tagespunkte, %s .. %s" % (s, n, a, b))
    conn.close()


# ---------------------------------------------------------------------------
def onchain(unsere, metrik="AdrActCnt", pause=0.8):
    print()
    print("=" * 78)
    print("B. %s (Coin Metrics Community)" % metrik)
    print("=" * 78)
    d = hole("https://community-api.coinmetrics.io/v4/catalog/asset-metrics"
             "?metrics=%s" % metrik)
    eintrag = (d.get("data") or [{}])[0]
    tages = next((f for f in (eintrag.get("frequencies") or [])
                  if f.get("frequency") == "1d"), {})
    verfuegbar = [a for a in (tages.get("assets") or []) if a.upper() in unsere]
    print("Unsere Symbole mit dieser Metrik: %d" % len(verfuegbar))
    conn = sqlite3.connect("data/onchain_historie.db")
    anlegen(conn, metrik.lower())
    ok = 0
    for i, asset in enumerate(sorted(verfuegbar), 1):
        try:
            d = hole("https://community-api.coinmetrics.io/v4/timeseries/"
                     "asset-metrics?assets=%s&metrics=%s&frequency=1d"
                     "&start_time=2013-01-01&page_size=10000" % (asset, metrik),
                     pause=pause)
            zeilen = []
            for e in (d.get("data") or []):
                v = e.get(metrik)
                if v not in (None, ""):
                    zeilen.append((asset.upper(), e["time"][:10], float(v)))
            if zeilen:
                conn.executemany("INSERT OR REPLACE INTO %s VALUES (?,?,?)"
                                 % metrik.lower(), zeilen)
                conn.commit()
                ok += 1
        except Exception as e:                       # noqa: BLE001
            print("  %-9s FEHLER: %s" % (asset, str(e)[:50]))
        if i % 20 == 0:
            print("  %3d von %d  (ok %d)" % (i, len(verfuegbar), ok))
        time.sleep(pause)
    n, s, a, b = conn.execute(
        "SELECT COUNT(*), COUNT(DISTINCT symbol), MIN(datum), MAX(datum) "
        "FROM %s" % metrik.lower()).fetchone()
    print("FERTIG: %d Symbole, %d Tagespunkte, %s .. %s" % (s, n, a, b))
    conn.close()


if __name__ == "__main__":
    unsere = {s.upper() for s in B.lade().keys()}
    was = sys.argv[1] if len(sys.argv) > 1 else "beides"
    if was in ("funding", "beides"):
        funding(unsere)
    if was in ("onchain", "beides"):
        onchain(unsere)
