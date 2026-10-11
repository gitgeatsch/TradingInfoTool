"""Konzeptpruefung Spot (11.10.2026), Punkt 1: WARUM fehlen 12 Bestaende im Watchlist-Universum? Nur lesend, Desktop.

    python Basisinfos/Spot_Voranalyse_04_10/kp_abdeckung_ursache.py

Das Universum der Messung (s3_stufe1 -> a2 -> as -> mk) ist: Binance-SPOT-Tagesreihe in data/messdaten.db (Krypto, USD), mit Kurs am
Stichtag und Umsatz der 90 Tage davor (min. 30 T). Je fehlendem Bestand wird festgestellt, woran es liegt:
  A  Binance fuehrt KEIN Spot-Paar (exchangeInfo, frei) - dann ist der Coin fuer diese Messung grundsaetzlich nicht da
  B  Spot-Paar unter ANDEREM Namen (symbol_zuordnung.csv, 1000er-Paare)
  C  Spot-Paar vorhanden, aber JUNG (erster Handelstag) - Reihe in messdaten fehlt oder ist kuerzer als 30 T vor dem Stichtag
  D  Spot-Paar vorhanden und alt genug, aber NICHT geladen (Messbasis-Lader)
Zusatz je Coin: Futures-Paar? Stundenreihe in stundenkurse_alle.db? erster Kurs in der Produktion (Desktop-Kopie)?
"""
import csv
import os
import sqlite3
import sys

import requests

os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
FEHLT = ["ASTER", "BRETT", "CANTON", "CAT", "HYPE", "KAS", "MON", "MORPHO", "PLUME", "SUPRA", "VSN", "XDC"]
STICHTAG = "2026-09-01"

zu = {}
with open("Basisinfos/symbol_zuordnung.csv", encoding="utf-8") as f:
    for r in csv.DictReader(f, delimiter=";"):
        zu[r["bitpanda"]] = r

ex = requests.get("https://api.binance.com/api/v3/exchangeInfo", timeout=30).json()["symbols"]
spot = {}
for s in ex:
    if s["quoteAsset"] in ("USDT", "USDC", "FDUSD"):
        spot.setdefault(s["baseAsset"], []).append((s["symbol"], s["status"]))
fx = requests.get("https://fapi.binance.com/fapi/v1/exchangeInfo", timeout=30).json()["symbols"]
fut = {}
for s in fx:
    if s["quoteAsset"] == "USDT":
        fut.setdefault(s["baseAsset"], []).append((s["symbol"], s["status"], s.get("onboardDate")))


def erster_tag_spot(paar):
    k = requests.get("https://api.binance.com/api/v3/klines", params=dict(symbol=paar, interval="1d", startTime=0, limit=1), timeout=30).json()
    if isinstance(k, list) and k:
        from datetime import datetime, timezone
        return datetime.fromtimestamp(k[0][0] / 1000, tz=timezone.utc).date().isoformat()
    return None


md = sqlite3.connect("file:data/messdaten.db?mode=ro", uri=True)
sk = sqlite3.connect("file:data/stundenkurse_alle.db?mode=ro", uri=True)
pr = sqlite3.connect("file:data/tradinginfotool.db?mode=ro", uri=True)
print("KONZEPTPRUEFUNG SPOT · Punkt 1: Ursache der Abdeckungsluecke (12 Bestaende nicht im Watchlist-Universum, Stichtag %s)\n" % STICHTAG)
urs = {}
for b in FEHLT:
    name = zu.get(b, {}).get("binance") or b
    sp = spot.get(name, [])
    ft = fut.get(name, [])
    handel = [p for p, st in sp if st == "TRADING"]
    erst = erster_tag_spot(handel[0]) if handel else None
    m = md.execute("SELECT MIN(date), MAX(date), COUNT(*) FROM price_history_ohlc WHERE symbol IN (?,?) AND currency='USD' AND assetklasse='krypto'",
                   (b, name)).fetchone()
    vor = md.execute("SELECT COUNT(*) FROM price_history_ohlc WHERE symbol IN (?,?) AND currency='USD' AND assetklasse='krypto' AND date < ?",
                     (b, name, STICHTAG)).fetchone()[0]
    st = sk.execute("SELECT markt, paar FROM _quelle WHERE symbol IN (?,?)", (b, name)).fetchone()
    p0 = pr.execute("SELECT MIN(date) FROM price_history_ohlc WHERE symbol=? AND currency='USD' AND COALESCE(quelle,'') != 'rekonstruiert'",
                    (b,)).fetchone()[0]
    if not handel:
        u = "A kein Binance-Spot"
    elif name != b and not m[2]:
        u = "B anderer Name (%s), nicht geladen" % name
    elif erst and erst > "2026-08-02":
        u = "C jung (Spot ab %s)" % erst
    elif vor < 30:
        u = "D Spot alt genug (ab %s), in messdaten %d T vor Stichtag" % (erst, vor)
    else:
        u = "? in messdaten %d T vor Stichtag - anderer Grund" % vor
    urs[b] = u
    print("  %-7s Binance %-8s Spot %-22s Futures %-26s erster Spot-Tag %-10s · messdaten %s..%s (%d) · Stunden %s · Prod ab %s" % (
        b, name, ",".join("%s:%s" % x for x in sp) or "-", ",".join("%s:%s" % x[:2] for x in ft) or "-", erst or "-",
        m[0] and m[0][:10], m[1] and m[1][:10], m[2], st and "%s/%s" % st or "-", p0 and p0[:10]))
    print("          -> %s" % u)
print()
for k in "ABCD?":
    g = [b for b, u in urs.items() if u.startswith(k)]
    if g:
        print("  %s: %d · %s" % (k, len(g), ", ".join(g)))
