"""Gegenprobe der Vorpruefung Spot-Einstieg (§29) - eigener Rechenweg, nur lesend.

    python Basisinfos/Spot_Voranalyse_04_10/ein_vorpruefung_gegenprobe.py

  G1 Ausstieg: 30 zufaellige Anker (alle Arme) mit einer ZWEITEN Umsetzung der Marke (pandas, cummax) - Ertrag, BTC-Ertrag, Haltetage gleich
  G2 Altseason-Breite an 6 Stichtagen mit eigener Rangrechnung (Umlauf x Kurs direkt) - gleich
  G3 E-c-Einstieg: an 15 Eintritten der erste Tag mit 30-T-Ertrag ueber BTC binnen 60 T - eigene Suche, gleich
  G4 E3 UNBERUEHRT: die Ausgabe ein_vorpruefung.txt enthaelt fuer E3 keine Ertragszahl
"""
import os
import re
import sys

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
os.chdir(os.path.dirname(os.path.dirname(HIER)))
import as_messung as M      # noqa: E402
import mk_messung as MK     # noqa: E402

K, POS, BTCV, IDX = M.K, M.POS, M.BTCV, M.IDX
R = pd.read_csv(os.path.join("data", "_spot", "ein_vorpruefung_anker.csv"), sep=";", parse_dates=["t"])
ok = n = 0


def pruefe(name, gut, info):
    global ok, n
    n += 1; ok += bool(gut)
    print("%-3s %s  %s" % (name, "gleich" if gut else "ABWEICHUNG", info), flush=True)


def marke2(s, i0):
    x = pd.Series(K[s].values[i0:i0 + 366])
    gueltig = x.notna()
    if not gueltig.all():
        x = x[:gueltig.values.argmin()]
    hoch = x.cummax()
    schwelle = np.maximum(0.65 * hoch, 0.5 * x.iloc[0])
    unter = np.where((x.values < schwelle.values) & (np.arange(len(x)) > 0))[0]
    if len(unter) and unter[0] + 1 < len(x):
        j = int(unter[0]) + 1
    else:
        j = len(x) - 1
    return x.iloc[j] / x.iloc[0] - 1, BTCV[i0 + j] / BTCV[i0] - 1, j


rng = np.random.default_rng(4)
for r in R[R.arm != "E-c"].sample(30, random_state=4).itertuples():
    a, b, j = marke2(r.sym, POS[r.t] + 1)
    pruefe("G1", abs(a - r.r) < 1e-9 and abs(b - r.rb) < 1e-9 and j == r.tage, "%s %s %s: %+.4f/%+.4f %d T (Skript %+.4f/%+.4f %d)" % (
        r.arm, r.sym, r.t.date(), a, b, j, r.r, r.rb, r.tage))

for t in sorted(R.t.unique())[::14][:6]:
    t = pd.Timestamp(t)
    kl, rg = MK.rang_mw(t)
    top = [s for s in rg.sort_values().index[:50] if s != "BTC"]
    i = POS[t]
    b90 = BTCV[i] / BTCV[i - 90] - 1
    eig = np.mean([(K[s].values[i] / K[s].values[i - 90] - 1) > b90 for s in top if K[s].values[i - 90] > 0])
    import ein_vorpruefung as EV
    pruefe("G2", abs(eig - EV.breite(t)) < 1e-12, "%s Breite %.3f" % (t.date(), eig))

ec = R[R.arm == "E-c"].sample(15, random_state=5)
for r in ec.itertuples():
    i = POS[r.t]
    v = K[r.sym].values
    j = next((k + 1 for k in range(i, min(i + 60, len(v) - 2)) if k >= 30 and v[k - 30] > 0 and v[k] / v[k - 30] > BTCV[k] / BTCV[k - 30]), None)
    a, b, h = marke2(r.sym, j)
    pruefe("G3", j is not None and abs(a - r.r) < 1e-9 and h == r.tage, "%s %s Kauf %s nach %d T" % (r.sym, r.t.date(), IDX[j].date(), j - i))

txt = open(os.path.join(HIER, "ein_vorpruefung.txt"), encoding="utf-8").read()
e3_zeilen = [z for z in txt.splitlines() if "E3" in z and re.search(r"[+-]\d+\.\d %", z) and "Breite" not in z]
pruefe("G4", not e3_zeilen, "E3-Zeilen mit Ertragszahl: %d" % len(e3_zeilen))
print("\n%d von %d gleich" % (ok, n))
