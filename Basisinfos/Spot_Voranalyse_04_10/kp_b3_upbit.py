"""Konzeptpruefung Spot (11.10.2026), Punkt B3 Upbit-Verkaufsanlass - zwei Fragen, nur lesend, Desktop.

    python Basisinfos/Spot_Voranalyse_04_10/kp_b3_upbit.py

  U1 WIE OFT kann B3 ueberhaupt ausloesen? Ein Upbit-Listing (KRW) trifft nur Coins, die Upbit noch NICHT in KRW fuehrt.
     Freie Marktliste api.upbit.com/v1/market/all gegen die 28 Krypto-Bestaende ohne Kern (frei + gestakt, Spot §39.9).
  U2 Was heisst *verkaufen* fuer den HALTER? §38.4 misst gegen BTC (Kaeufersicht). Wer verkauft, haelt danach Dollar (wie B1, §39.5).
     Dieselben 32 Ereignisse ab 2024 (data/_spot/c2_ereignisse.csv, gleiche Stunden he/hx): Ertrag des Coins in DOLLAR ueber die 7 T
     nach +4 h, dazu BTC in Dollar. Halten schlaegt Verkaufen, wenn der Coin in Dollar steigt. Keine neue Hypothese, nur die Zielgroesse
     des Halters auf denselben Faellen; Urteilsregel wie §38.2 (Monatskorb, Block-Bootstrap) als Auskunft.
"""
import os
import sys

import numpy as np
import pandas as pd
import requests

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
import c2_messung as C  # noqa: E402  (main() laeuft nur ueber __main__)

BESTAND = ["ALGO", "ASTER", "AVAX", "BEAMX", "BIO", "BNB", "BRETT", "CANTON", "CAT", "HYPE", "INJ", "KAIA", "KAS", "LINK", "MON", "MORPHO",
           "NEAR", "PLUME", "QNT", "SEI", "SUI", "SUPRA", "TAO", "TURBO", "VSN", "W", "XDC", "XLM"]
UPBIT_NAME = {"CANTON": "CC"}

m = requests.get("https://api.upbit.com/v1/market/all", timeout=30).json()
krw = {x["market"].split("-")[1] for x in m if x["market"].startswith("KRW-")}
alle = {x["market"].split("-")[1] for x in m}
print("KONZEPTPRUEFUNG SPOT · B3 Upbit-Verkaufsanlass\n")
print("U1 Upbit fuehrt %d Coins in KRW. Bestand ohne Kern: %d" % (len(krw), len(BESTAND)))
schon = [s for s in BESTAND if UPBIT_NAME.get(s, s) in krw]
offen = [s for s in BESTAND if UPBIT_NAME.get(s, s) not in krw]
print("   schon in KRW (B3 kann NICHT mehr ausloesen): %d · %s" % (len(schon), ", ".join(schon)))
print("   noch nicht in KRW (B3 moeglich): %d · %s%s\n" % (len(offen), ", ".join(offen),
      "" if not [s for s in offen if UPBIT_NAME.get(s, s) in alle] else " (davon nur BTC/USDT-Markt: %s)" % ", ".join(
          s for s in offen if UPBIT_NAME.get(s, s) in alle)))

D = pd.read_csv(os.path.join("data", "_spot", "c2_ereignisse.csv"), sep=";", parse_dates=["zeit"])
Du = D[(D.art == "C2-b Upbit-Listing") & (D.zeit >= "2024-01-01")].reset_index(drop=True)
P = C.stundenreihen(sorted(set(Du.sym) | {"BTC"}))
usd, btc = [], []
for r in Du.itertuples():
    a, b = P[r.sym], P["BTC"]
    usd.append(C.letzter(a, r.he, r.hx) / a[r.he] - 1)
    btc.append(b[r.hx] / b[r.he] - 1)
Du["usd"], Du["btc_usd"] = usd, btc
Du["mon"] = Du.zeit.dt.to_period("M")
korb = Du.groupby("mon")[["ex", "usd", "btc_usd"]].mean()
print("U2 dieselben %d Upbit-Listings ab 2024 (%d Monate), Kauf/Bezug +4 h, 7 T:" % (len(Du), len(korb)))
print("   gegen BTC (wie §38.4, Kontrolle): Korb %+.2f Pp" % (100 * korb.ex.mean()))
print("   Coin in DOLLAR (Halter: Halten statt Verkaufen): Korb %+.2f %% · Median der Ereignisse %+.2f %% · steigt in %d von %d · Bootstrap(>0) %.3f" % (
    100 * korb.usd.mean(), 100 * Du.usd.median(), int((Du.usd > 0).sum()), len(Du), C.boot(korb.usd.values)))
print("   BTC in Dollar ueber dieselben Stunden: Korb %+.2f %%" % (100 * korb.btc_usd.mean()))
print("   je Jahr (Dollar): %s" % " · ".join("%d %+.1f %% (n %d)" % (j, 100 * g.usd.mean(), len(g)) for j, g in Du.groupby(Du.zeit.dt.year)))
print("\n   Ereignisse: %s" % " · ".join("%s %s %+.0f%%/%+.0f%%" % (r.zeit.strftime("%y-%m"), r.sym, 100 * r.usd, 100 * r.ex) for r in Du.itertuples()))
