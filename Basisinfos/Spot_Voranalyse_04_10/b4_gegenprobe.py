"""B4-Vormessung (Spot §43) - GEGENPROBE mit eigenem Rechenweg. Nur lesend.

    python Basisinfos/Spot_Voranalyse_04_10/b4_gegenprobe.py

  G1 Dollar-Ertrag je Anker aus ROHKURSEN (messdaten, eigene Schleife): Kurs am Folgetag, Ende nach 365 T oder letzter Kurs vor der ersten Luecke
     - gegen die Spalte `ende` der Messung
  G2 unteres Fuenftel aus eigenem Rang des Perzentils je Zelle (Zellen >= 10) - Anzahl gegen die Messung (E3 1.474)
  G3 Abstand E3 als eigene Rechnung (Zelle, Stichtag gewichtet, Mittel) - gegen -12,51 Pp
  G4 bestaendige Nullwelt mit eigenem Zufall und eigener Auswahl (200): Rang <= 0,02 wie die Messung (0,000), 2,5. Perzentil nahe -6,5 Pp
"""
import os
import sqlite3

import numpy as np
import pandas as pd

os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
ERG = []


def pruefe(k, ok, text):
    ERG.append(bool(ok))
    print("%-3s %-10s %s" % (k, "gleich" if ok else "ABWEICHUNG", text))


A = pd.read_csv("data/_spot/b4_vormessung.csv", sep=";", parse_dates=["t"])
c = sqlite3.connect("file:data/messdaten.db?mode=ro", uri=True)
syms = sorted(A.sym.unique())
kurse = {}
for s in syms:
    r = c.execute("SELECT date, close FROM price_history_ohlc WHERE symbol=? AND currency='USD' AND assetklasse='krypto' ORDER BY date", (s,)).fetchall()
    kurse[s] = {d[:10]: v for d, v in r}
letzter_tag = max(max(k) for k in kurse.values() if k)

# G1
eigen = []
for r in A.itertuples():
    k = kurse[r.sym]
    t1 = r.t + pd.Timedelta(days=1)
    v0 = k.get(t1.strftime("%Y-%m-%d"))
    if v0 is None:
        eigen.append(np.nan)
        continue
    v = v0
    for i in range(1, 366):
        x = k.get((t1 + pd.Timedelta(days=i)).strftime("%Y-%m-%d"))
        if x is None:
            break
        v = x
    eigen.append(v / v0)
A["ende_eigen"] = eigen
d = np.abs(A.ende_eigen - A.ende) / A.ende
pruefe("G1", np.nanmax(d) < 1e-9 and A.ende_eigen.notna().all(), "Ertrag aus Rohkursen an %d Ankern, groesste relative Abweichung %.1e" % (len(A), np.nanmax(d)))

# G2/G3
E = A[(A.ep == "E3") & A.p9.notna()].copy()
zellen = []
for (t, kl), g in E.groupby(["t", "kl"]):
    if len(g) >= 10:
        r = g.p9.rank(pct=True)
        zellen.append((t, kl, g.index.values, g.index.values[(r <= 0.2).values]))
n_u = sum(len(u) for *_, u in zellen)
pruefe("G2", n_u == 1474, "unteres Fuenftel E3: %d Anker (Messung 1.474)" % n_u)
y = A.ende_eigen - 1


def abstand(wahl):
    v, n = {}, {}
    for t, kl, m, u in zellen:
        q = wahl(t, kl, m, u)
        v[t] = v.get(t, 0) + (y[q].mean() - y[m].mean()) * len(m)
        n[t] = n.get(t, 0) + len(m)
    return np.mean([v[t] / n[t] for t in n])


echt = abstand(lambda t, kl, m, u: u)
pruefe("G3", abs(100 * echt - (-12.51)) < 0.01, "Abstand E3 %+.2f Pp (Messung -12,51)" % (100 * echt))

# G4
rng = np.random.default_rng(4343)
null = []
for _ in range(200):
    zz = {s: rng.random() for s in syms}
    null.append(abstand(lambda t, kl, m, u: sorted(m, key=lambda i: zz[A.sym[i]])[:len(u)]))
null = np.array(null)
rang = float(np.mean(null < echt))
pruefe("G4", rang <= 0.02 and abs(100 * np.percentile(null, 2.5) - (-6.51)) < 2.5,
       "bestaendige Nullwelt eigen: Rang %.3f (Messung 0,000) · 2,5./97,5. Perz. %+.2f / %+.2f (Messung -6,51 / +10,76)" % (
           rang, 100 * np.percentile(null, 2.5), 100 * np.percentile(null, 97.5)))
print("\n%d von %d gleich" % (sum(ERG), len(ERG)))
