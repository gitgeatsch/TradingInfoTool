"""Preispruefung der Zuordnung Bitpanda -> Binance (O11, Voranalyse_Datenbasis_alle_Assets_01_10.md Frage 2) - nur lesen.

Fuer jedes Krypto-Asset aus Watchlist, Bestand und Hebel-Liste (Quelle wie ``messe_signalbilanz_je_asset.listen``):
    1. Binance-Kuerzel bestimmen: ``Basisinfos/symbol_zuordnung.csv`` (Ausnahmen), sonst dasselbe Kuerzel
    2. wo liegen die Stundenkurse: Messbasis ``stundenkurse.db`` oder ``stundenkurse_alle.db`` (Markt spot/futures)
    3. Binance-Kurs JETZT (oeffentlicher Ticker) / Faktor gegen den CoinGecko-Kurs (ID aus der Watchlist) - Abweichung > 5 % -> GESPERRT

Eine Zuordnung, die hier nicht OK ist, darf kein Signal erzeugen: genau so faengt sie gleiche Kuerzel fuer verschiedene Coins ab.

    python pruefe_symbol_zuordnung.py
"""
from __future__ import annotations

import csv
import os
import sqlite3
import sys

import requests

HIER = os.path.dirname(os.path.abspath(__file__))
GRENZE = 0.05


def zuordnung():
    z = {}
    with open(os.path.join(HIER, "Basisinfos", "symbol_zuordnung.csv"), encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter=";"):
            z[r["bitpanda"]] = (r["binance"], r["markt"], float(r["faktor"]))   # markt 'gesperrt' = anderer Coin
    return z


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:                                         # noqa: BLE001
        pass
    sys.path.insert(0, HIER)
    import messe_signalbilanz_je_asset as SB
    import config as C
    quelle, L = SB.listen()
    cg = {a.symbol: a.coingecko_id for a in C.get_watchlist() if a.coingecko_id}
    # Krypto oder nicht: der Bitpanda-Krypto-Ticker entscheidet (nicht die Watchlist - ein gehaltener Coin ausserhalb der Watchlist waere sonst "kein Krypto")
    kr = {a.symbol for a in C.get_watchlist() if a.assetklasse == "krypto"} | set(requests.get("https://api.bitpanda.com/v1/ticker", timeout=30).json())
    alle = sorted((set(L["Watchlist"]) | set(L["Bestand"]) | set(L["Hebel"])))
    zu = zuordnung()
    mb = {r[0] for r in sqlite3.connect("file:%s?mode=ro" % os.path.join(HIER, "data", "stundenkurse.db").replace("\\", "/"), uri=True)
          .execute("SELECT DISTINCT symbol FROM stundenkurse")}
    za = {r[0]: r[1] for r in sqlite3.connect("file:%s?mode=ro" % os.path.join(HIER, "data", "stundenkurse_alle.db").replace("\\", "/"), uri=True)
          .execute("SELECT symbol, markt FROM _quelle")}
    tick_s = {x["symbol"]: float(x["price"]) for x in requests.get("https://api.binance.com/api/v3/ticker/price", timeout=30).json()}
    tick_f = {x["symbol"]: float(x["price"]) for x in requests.get("https://fapi.binance.com/fapi/v1/ticker/price", timeout=30).json()}
    ids = sorted({cg[s] for s in alle if s in cg})
    pr = requests.get("https://api.coingecko.com/api/v3/simple/price", params={"ids": ",".join(ids), "vs_currencies": "usd"}, timeout=30).json()
    print("=" * 110)
    print("PREISPRUEFUNG ZUORDNUNG Bitpanda -> Binance · Listen: %s · Grenze ±%.0f %%" % (quelle, 100 * GRENZE))
    print("=" * 110)
    zahl = {"OK": 0, "GESPERRT": 0, "ohne Binance": 0, "ohne Vergleich": 0, "kein Krypto": 0}
    for s in alle:
        bn, markt, fak = zu.get(s, (s, None, 1.0))
        if markt == "gesperrt":
            zahl["GESPERRT"] += 1
            print("  %-9s -> %-9s  GESPERRT (Tabelle: anderer Coin unter gleichem Kuerzel)" % (s, bn))
            continue
        if s in mb or bn in mb:
            wo, markt = "Messbasis", markt or "spot"
        elif bn in za:
            wo, markt = "alle", markt or za[bn]
        else:
            wo = None
        if wo is None:
            st = "kein Krypto" if s not in kr and s not in L["Hebel"] else "ohne Binance"
            zahl[st] += 1
            print("  %-9s -> %-9s  %s" % (s, "–", st))
            continue
        paar = bn + "USDT"
        bpx = (tick_s if markt == "spot" else tick_f).get(paar)
        g = pr.get(cg.get(s, ""), {}).get("usd")
        if bpx is None or g is None:
            zahl["ohne Vergleich"] += 1
            print("  %-9s -> %-9s %-8s %-9s Binance %s · CoinGecko %s -> ohne Vergleich" % (s, bn, markt, wo, bpx, g))
            continue
        abw = (bpx / fak) / g - 1.0
        st = "OK" if abs(abw) <= GRENZE else "GESPERRT"
        zahl[st] += 1
        print("  %-9s -> %-9s %-8s %-9s Binance %.6g / %g · CoinGecko %.6g · Abweichung %+.2f %% -> %s" % (s, bn, markt, wo, bpx, fak, g, 100 * abw, st))
    print("  ZUSAMMEN: " + " · ".join("%s %d" % kv for kv in zahl.items()))
    print("SCHLUSS: vollstaendig")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
