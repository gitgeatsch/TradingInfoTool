"""GRID AUFLOESUNG (Recherche_Grid_Trading_21_10.md §9.4): was verdient ein Gitter je Ausfuehrung bei EINGEPFLANZTER Rueckkehr bekannter Staerke?

    python Basisinfos/Spot_Voranalyse_04_10/grid_aufloesung.py

KEINE echten Ertraege. Kuenstliche Monate (720 Stunden) mit der BTC-Stundenschwankung, Stundenrenditen AR(1) mit phi; je phi 2.000 Monate.
Ausgewiesen: Ergebnis je Ausfuehrung (Nennwert) bei phi minus bei phi = 0 - das ist der Ertrag, den die Rueckkehr dem Gitter bringt.
Daneben die Uebersetzung der gemessenen Varianz-Ratio (G4, grid_stufe1_gegenprobe.txt) in ein gleichwertiges phi: VR(q) fuer AR(1).
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import grid_stufe1 as G  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass

N_MON, N_STD = 2000, 720
sig = float(np.std(np.diff(np.log(G.stunden("BTC")[0].values))))


def pfade(phi, saat):
    rr = np.random.default_rng(saat)
    e = rr.normal(0, sig * np.sqrt(1 - phi ** 2), (N_MON, N_STD - 1))
    x = np.empty_like(e)
    x[:, 0] = e[:, 0]
    for t in range(1, N_STD - 1):
        x[:, t] = phi * x[:, t - 1] + e[:, t]
    return np.concatenate([np.zeros((N_MON, 1)), np.cumsum(x, axis=1)], axis=1)


def vr_ar1(phi, q):
    return 1 + 2 * sum((1 - k / q) * phi ** k for k in range(1, q))


print("GRID AUFLOESUNG · BTC-Stundenschwankung %.3f %% · %d kuenstliche Monate je phi · Schwelle Fusion 0,25 %% je Ausfuehrung\n" % (100 * sig, N_MON))
basis = {}
for phi in (0.0, -0.05, -0.10, -0.20, -0.30):
    x = pfade(phi, 7)
    teile = []
    for g in (0.01, 0.02, 0.03):
        e, n = G.gitter(x, g)
        je = e.sum() / n.sum()
        if phi == 0.0:
            basis[g] = je
        teile.append("g %.0f %%: je Ausf. %+.3f %% (Rueckkehr-Ertrag %+.3f %%)" % (100 * g, 100 * je, 100 * (je - basis[g])))
    print("phi %+.2f (entspricht VR(24) %.3f, VR(168) %.3f): %s" % (phi, vr_ar1(phi, 24), vr_ar1(phi, 168), " · ".join(teile)))
print("\nGemessen (G4): VR(24) BTC 0,952 · ETH 1,030 · SOL 0,918 · LINK 0,940 -> phi etwa -0,025 · +0,015 · -0,04 · -0,03")
