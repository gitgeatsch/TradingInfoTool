"""Gegenprobe Machbarkeit §40 K-3 - zweite Umsetzung (eigene Perzentile je Tag, Tagesschleife), nur lesend, nur Anzahlen.

    python Basisinfos/Spot_Voranalyse_04_10/k3_gegenprobe.py

  G1 Einstiege je Klasse und Epoche mit eigener Rechnung = Ablage (gleiche Paare Signal/Coin)
  G2 keine ueberlappenden Haltezeiten je Coin - UEBER ALLE KLASSEN (die Gegenprobe fand am 09.10. die Sperre nur je Klasse)
  G3 am Signaltag: Schwankung 90 T UND Tiefe je im unteren Fuenftel des Tagesquerschnitts (eigene Rangrechnung) und Klasse stimmt
"""
import os
import sys

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
os.chdir(os.path.dirname(os.path.dirname(HIER)))
import tc_vorpruefung as T  # noqa: E402

IDX = T.IDX
ok = n = 0


def pruefe(name, gut, info):
    global ok, n
    n += 1; ok += bool(gut)
    print("%-3s %s  %s" % (name, "gleich" if gut else "ABWEICHUNG", info), flush=True)


rel, F = T.merkmale()
up, down, end, fertig = T.ziele(rel)
m, kl = T.maske()
m = m & fertig
S90, TI = F["schwankung90"].where(m), F["tiefe"].where(m)
for ep, ab, bis in (("W", "2023-01-01", "2023-12-01"), ("U", "2024-01-01", str(T.M.ENDE.date()))):
    frei, neu = {}, {"H": [], "M": [], "S": []}
    for i, d in enumerate(IDX):
        if d < pd.Timestamp(ab) or d > pd.Timestamp(bis) or i + 31 > len(IDX) - 1:
            continue
        a, b = S90.iloc[i].dropna(), TI.iloc[i].dropna()
        if len(a) < 30 or len(b) < 30:
            continue
        ra = a.rank(pct=True)
        rb = b.rank(pct=True)
        gem = [s for s in ra.index if s in rb.index and ra[s] <= 0.2 and rb[s] <= 0.2]
        for s in gem:
            k = kl.iat[i, kl.columns.get_loc(s)]
            if k not in neu or frei.get(s, -1) >= i:
                continue
            neu[k].append((d, s))
            frei[s] = i + 31
    for k in ("H", "M", "S"):
        A = pd.read_csv(os.path.join("data", "_spot", "k3_einstiege_%s_%s.csv" % (k, ep)), sep=";", parse_dates=["signal"])
        a = set(zip(A.signal, A.sym))
        pruefe("G1", set(neu[k]) == a, "%s %s: eigene %d · Ablage %d · nur eigene %d · nur Ablage %d" % (k, ep, len(neu[k]), len(a), len(set(neu[k]) - a), len(a - set(neu[k]))))
        ALL = pd.concat([pd.read_csv(os.path.join("data", "_spot", "k3_einstiege_%s_%s.csv" % (kk, ep)), sep=";") for kk in "HMS"])
        ueber = sum(int((g.i_kauf.values[1:] <= g.i_aus.values[:-1]).sum()) for _, g in ALL.sort_values("i_kauf").groupby("sym"))
        pruefe("G2", ueber == 0, "%s %s: ueberlappende Haltezeiten %d" % (k, ep, ueber))
        fx = 0
        for r in A.itertuples():
            i = IDX.get_loc(r.signal)
            a_, b_ = S90.iloc[i].dropna().rank(pct=True), TI.iloc[i].dropna().rank(pct=True)
            fx += not (a_.get(r.sym, 1) <= 0.2 and b_.get(r.sym, 1) <= 0.2 and kl.at[r.signal, r.sym] == k)
        pruefe("G3", fx == 0, "%s %s: Bedingung am Signaltag verletzt %d" % (k, ep, fx))
print("\n%d von %d gleich" % (ok, n))
