"""P58 GEGENPROBE: Gelten die Zusammenhaenge Merkmal -> 24-h-Ertrag der 249 Anker auch auf ALLEN REGEL0-Einstiegen 2025/26? (15.10.2026)

    python Basisinfos/Rechenkern_02_10/p58_gegenprobe.py

Nur lesend. Stichprobe je Jahr 1.200 Einstiege (feste Saat) aus data/_vergleich/kern48jbz_einstiege_bestand.csv; Merkmale und Ertrag mit
DEMSELBEN Rechenweg wie der Regel-Arm F (n5_auswertung.merkmale / ertrag24). Ausgabe: Rangkorrelation je Merkmal und Jahr, dazu die
Standardabweichung der Schaetzung (1/sqrt(n)) - was ueber 2 SE liegt, ist kein Zufall der kleinen Ankermenge.
"""
import os
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(os.path.dirname(HIER))
os.chdir(PROJ)
sys.path.insert(0, PROJ)
sys.path.insert(0, HIER)

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import n5_auswertung as A5  # noqa: E402

N = 1200
E = pd.read_csv(os.path.join("data", "_vergleich", "kern48jbz_einstiege_bestand.csv"), sep=";")
rng = np.random.default_rng(58)
print("P58 GEGENPROBE · Merkmal -> 24-h-Ertrag auf REGEL0-Einstiegen (Stichprobe %d je Jahr)\n" % N)
print("   %-20s %s" % ("Merkmal", "   ".join("%d (rho, z)" % j for j in (2024, 2025, 2026))))
erg = {}
for j in (2024, 2025, 2026):
    g = E[E.jahr == j]
    g = g.iloc[rng.choice(len(g), size=min(N, len(g)), replace=False)]
    zeilen = []
    for r in g.itertuples():
        st = (A5.B0 + pd.Timedelta(hours=int(r.stunde))).strftime("%Y-%m-%d %H:%M")
        m = A5.merkmale(r.symbol, st)
        m["y"] = A5.ertrag24(r.symbol, st)
        zeilen.append(m)
    X = pd.DataFrame(zeilen).dropna(subset=["y"])
    erg[j] = {k: (X[k].rank().corr(X.y.rank()), len(X[X[k].notna()])) for k in A5.MERK}
    erg[j]["_y"] = (X.y.mean(), len(X))
for k in A5.MERK:
    print("   %-20s %s" % (k, "   ".join("%+.3f (%+.1f)" % (erg[j][k][0], erg[j][k][0] * np.sqrt(erg[j][k][1])) for j in (2024, 2025, 2026))))
print("\n   mittlerer 24-h-Ertrag: %s" % " · ".join("%d %+.2f %% (n %d)" % (j, 100 * erg[j]["_y"][0], erg[j]["_y"][1]) for j in (2024, 2025, 2026)))
