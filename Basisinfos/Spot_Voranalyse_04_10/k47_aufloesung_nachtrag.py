"""Messung U2/U1 (Spot §46) - NACHTRAG Aufloesung, Auskunft (Planfehler korrigiert, die Vorabfestlegung bleibt sichtbar).

    python Basisinfos/Spot_Voranalyse_04_10/k47_aufloesung_nachtrag.py

Der vorab festgelegte Test (b) verlangte, dass +x Pp das VOLLE Urteil TRAEGT erreichen - also auch Korb > 0. Bei einer Nullwelt von
-5,4 / -5,8 Pp kann +5 Pp den Korb aber gar nicht ueber null heben: der Test war fuer x = 5 rechnerisch unbestehbar (Planfehler).
Hier gemessen, was die Aufloesung eigentlich fragt: findet die Anlage +x Pp GEGEN DIE NULLWELT (Rang >= 0,975)?
x = 2 / 3 / 5 / 10, je 100 Wiederholungen, 1.000 Ziehungen.
"""
import os
import sys

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
import k47_messung as KM7  # noqa: E402

V, T, K, IDX, RNG = KM7.V, KM7.T, KM7.K, KM7.IDX, np.random.default_rng(20261048)
rel = K.div(T.B, axis=0)
up, down, end, fertig = T.ziele(rel)
m, kl = T.maske()
m = m & fertig
F = V.merkmale()
print("NACHTRAG AUFLOESUNG U2/U1 (Auskunft): +x Pp gegen die Nullwelt mit Merkmal gefunden (Rang >= 0,975), 100 Wiederholungen x 1.000 Ziehungen\n")
for h, (name, seite) in KM7.HYP.items():
    X = F[name]
    Xm = X.where(m)
    p = Xm.rank(axis=1, pct=True)
    p.loc[Xm.notna().sum(axis=1) < 30] = np.nan
    pv = p if seite == "oben" else 1 - p
    lage = KM7.Lage(X, pv, m, kl, up, down)
    E = KM7.bewerte(pd.read_csv(os.path.join("data", "_spot", "k47_einstiege_%s_U.csv" % h), sep=";", parse_dates=["signal"]), up, down)
    G = KM7.gruppen(E, lage)
    zeile = []
    for x in (0.02, 0.03, 0.05, 0.10):
        f = 0
        for _ in range(100):
            Eb = E.copy()
            for g in G:
                if len(g["ex"]):
                    Eb.loc[g["idx"], "ex"] = RNG.choice(g["ex"], g["n"]) + x
            jk = Eb.groupby("mon").ex.mean().mean()
            nl = KM7.null_korb(G, 1000, RNG)
            f += np.mean(nl < jk) >= 0.975
        zeile.append("+%d Pp %d %%" % (round(100 * x), f))
    print("%s %s %s: %s" % (h, name, seite, " · ".join(zeile)))
