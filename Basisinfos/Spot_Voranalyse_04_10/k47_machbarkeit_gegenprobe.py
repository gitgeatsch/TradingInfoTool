"""MACHBARKEIT Messplan U2/U1 (Spot §46) - GEGENPROBE mit zweiter Umsetzung (Tag fuer Tag statt Coin fuer Coin). Nur lesend.

    python Basisinfos/Spot_Voranalyse_04_10/k47_machbarkeit_gegenprobe.py

  G1 Einstiege ab 2024 Tag fuer Tag mit eigener Sperre je Coin (offen bis i_aus) und eigenem Perzentil - gegen die Ablage k47_einstiege_*_U
  G2 keine ueberlappenden Haltezeiten je Coin; Signal am Signaltag erfuellt (Fuenftel, Maske, Querschnitt >= 30)
  G3 Nullwelt-Vorrat (mit Merkmal, ohne Signal) an 30 zufaelligen Einstiegen selbst gezaehlt
"""
import os
import random
import sys

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
import kp46_vorpruefung as V  # noqa: E402

T, K, IDX = V.T, V.K, V.IDX
random.seed(47)
ERG = []


def pruefe(k, ok, text):
    ERG.append(bool(ok))
    print("%-3s %-10s %s" % (k, "gleich" if ok else "ABWEICHUNG", text))


rel = K.div(T.B, axis=0)
up, down, end, fertig = T.ziele(rel)
m, kl = T.maske()
m = m & fertig
F = V.merkmale()
syms = list(K.columns)
for h, name, seite in (("U2", "gebuehr90", "oben"), ("U1", "stab90", "unten")):
    X, M_, KL = F[name].values, m.values, kl.values
    offen = {}
    eigen = []
    i0 = IDX.get_loc(pd.Timestamp("2024-01-01"))
    for i in range(i0, len(IDX)):
        j = np.where(M_[i] & ~np.isnan(X[i]))[0]
        if len(j) < 30:
            continue
        p = pd.Series(X[i, j]).rank(pct=True).values
        sel = j[p >= 0.8] if seite == "oben" else j[p <= 0.2]
        for c in sel:
            if KL[i, c] not in ("H", "M", "S"):
                continue
            if c in offen and i <= offen[c]:
                continue
            if i + 31 > len(IDX) - 1:
                continue
            eigen.append((IDX[i], syms[c], KL[i, c], i + 1, i + 31))
            offen[c] = i + 31
    E2 = pd.DataFrame(eigen, columns=["signal", "sym", "kl", "i_kauf", "i_aus"]).sort_values(["signal", "sym"]).reset_index(drop=True)
    A = pd.read_csv("data/_spot/k47_einstiege_%s_U.csv" % h, sep=";", parse_dates=["signal"]).sort_values(["signal", "sym"]).reset_index(drop=True)
    gleich = E2.equals(A[E2.columns])
    pruefe("G1", gleich, "%s: Einstiege Tag fuer Tag %d · Ablage %d · gleich %s" % (h, len(E2), len(A), gleich))
    ueb = sum(((g.i_kauf.values[1:] <= g.i_aus.values[:-1]).any()) for _, g in A.sort_values("i_kauf").groupby("sym"))
    pruefe("G2", ueb == 0, "%s: Coins mit ueberlappender Haltezeit %d" % (h, ueb))
    v = []
    for r in A.sample(30, random_state=47).itertuples():
        i = IDX.get_loc(r.signal)
        j = np.where(M_[i] & ~np.isnan(X[i]))[0]
        p = pd.Series(X[i, j]).rank(pct=True).values
        sig = set(j[p >= 0.8] if seite == "oben" else j[p <= 0.2])
        v.append(sum(1 for c in j if KL[i, c] == r.kl and c not in sig))
    pruefe("G3", min(v) >= 2, "%s: Vorrat mit Merkmal an 30 Einstiegen min %d / Median %d" % (h, min(v), int(np.median(v))))
print("\n%d von %d gleich" % (sum(ERG), len(ERG)))
