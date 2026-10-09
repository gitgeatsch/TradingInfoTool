"""KORREKTUR Abdeckung Bestand (Spot §39.9, 09.10.2026) - Bestand = FREI + GESTAKT (Prod-Sicherung 09.10. 12:35 UTC), nur lesend.

    python Basisinfos/Spot_Voranalyse_04_10/d4_abdeckung_bestand.py

Die erste Liste stammte aus der Teilexport-Zeile *BESTAND (Menge > 0)*, die nur `holdings.quantity` zaehlt: vollstaendig gestakte Werte
fehlten (BNB, HYPE, SEI, TAO, VSN). Rechnung wie d4_wirkung.py (letzter Monatsstichtag, Watchlist-Universum, F1/F2/F8/F9, Fuenftel).
"""
import os
import sys

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
os.chdir(os.path.dirname(os.path.dirname(HIER)))
import d4_wirkung as D4  # noqa: E402

MK, M, W, K, POS = D4.MK, D4.M, D4.W, D4.K, D4.POS
# Krypto ohne Kern (BTC, ETH, SOL) und ohne Cash (EURCV); frei + gestakt > 0 am 09.10. 12:35 UTC; CT inzwischen verkauft
BESTAND = ["ALGO", "ASTER", "AVAX", "BEAMX", "BIO", "BNB", "BRETT", "CANTON", "CAT", "HYPE", "INJ", "KAIA", "KAS", "LINK", "MON", "MORPHO",
           "NEAR", "PLUME", "QNT", "SEI", "SUI", "SUPRA", "TAO", "TURBO", "VSN", "W", "XDC", "XLM"]
GESTAKT = {"ALGO", "AVAX", "BNB", "HYPE", "NEAR", "SEI", "SUI", "TAO", "VSN"}

t = max(x for x in POS if x.day == 1)
out, _, _ = MK.klassen_mw(t)
Dt = pd.DataFrame([dict(t=t, sym=s, kl=k) for s, k in out.items() if not np.isnan(K[s].values[POS[t]])])
Ft = M.merkmale(Dt)
Zl = W.Leicht(Dt)
pt, pt9 = M.pct_in_zelle(Zl, W.wert(Zl, Ft)), M.pct_in_zelle(Zl, W.wert(Zl, Ft, wahl=D4.OHNE_F9))
print("ABDECKUNG BESTAND (frei + gestakt) am Stichtag %s · Universum %d Coins · %d Bestaende ohne Kern\n" % (t.date(), len(Dt), len(BESTAND)))
z = {"voll": [], "ohne_tvl": [], "nicht": []}
unten = []
for s in BESTAND:
    j = np.where(Dt.sym.values == s)[0]
    g = " (gestakt)" if s in GESTAKT else ""
    if not len(j):
        z["nicht"].append(s)
        print("  %-7s NICHT im Watchlist-Universum%s · Kurs B1: %s" % (s, g, "Binance" if s in K.columns and not np.isnan(K[s].values[POS[t]]) else "nur Prod (D5)"))
        continue
    j = j[0]
    bek = [k for k, _ in W.WAHL if not np.isnan(Ft[k][j])]
    z["voll" if len(bek) == 4 else "ohne_tvl"].append(s)
    f = int(D4.fuenftel(pt[j:j + 1])[0]) if pt[j] == pt[j] else None
    f9 = int(D4.fuenftel(pt9[j:j + 1])[0]) if pt9[j] == pt9[j] else None
    if f9 == 1:
        unten.append(s)
    print("  %-7s Klasse %s · Merkmale %s · Fuenftel %s (ohne F9 %s)%s" % (s, Dt.kl.values[j], ",".join(bek), f, f9, g))
print("\n-> im Universum %d von %d (alle vier Merkmale %d, ohne TVL %d) · NICHT im Universum %d: %s" % (
    len(z["voll"]) + len(z["ohne_tvl"]), len(BESTAND), len(z["voll"]), len(z["ohne_tvl"]), len(z["nicht"]), ", ".join(z["nicht"])))
print("-> unteres Fuenftel (ohne F9, wie B4 vorlaeufig): %s" % (", ".join(unten) or "-"))
