"""Gegenprobe GRID AUFLOESUNG (§9.4): anderer Startwert, eigene Gitterschleife (gitter_einfach) auf 400 Monaten je phi, g 1 %.

    python Basisinfos/Spot_Voranalyse_04_10/grid_aufloesung_gegenprobe.py

Erwartet: Rueckkehr-Ertrag bei phi -0,10 nahe +0,07 % und bei phi -0,30 unter der Gebuehr 0,25 % je Ausfuehrung (wie grid_aufloesung.txt).
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import grid_stufe1 as G  # noqa: E402


def gitter_einfach(preise, g):
    """Wortgleich mit grid_stufe1_gegenprobe.gitter_einfach (dort in G1 gegen grid_stufe1 geprueft) - hier kopiert, weil der Import
    jenes Moduls dessen ganze Gegenprobe ausfuehren wuerde."""
    q = 1.0 + g
    p0 = preise[0]
    ell, menge, geld, nenn = 0, 0.0, 0.0, 0.0
    for p in preise[1:]:
        while p >= p0 * q ** (ell + 1) * (1 - 1e-12):
            ell += 1
            menge -= 1.0 / (p0 * q ** ell)
            geld += 1.0
            nenn += 1.0
        while p <= p0 * q ** (ell - 1) * (1 + 1e-12):
            ell -= 1
            menge += 1.0 / (p0 * q ** ell)
            geld -= 1.0
            nenn += 1.0
    wert = menge * preise[-1]
    return geld + wert, nenn + abs(wert)


sig = float(np.std(np.diff(np.log(G.stunden("BTC")[0].values))))
je = {}
for phi in (0.0, -0.10, -0.30):
    rr = np.random.default_rng(99)
    s_e = s_n = 0.0
    for _ in range(400):
        e = rr.normal(0, sig * np.sqrt(1 - phi ** 2), 719)
        x = np.empty(719)
        x[0] = e[0]
        for t in range(1, 719):
            x[t] = phi * x[t - 1] + e[t]
        a, b = gitter_einfach(np.exp(np.concatenate([[0.0], np.cumsum(x)])), 0.01)
        s_e += a
        s_n += b
    je[phi] = s_e / s_n
print("phi 0: %+.3f %% · phi -0,10: %+.3f %% (Rueckkehr-Ertrag %+.3f %%) · phi -0,30: %+.3f %% (Rueckkehr-Ertrag %+.3f %%)"
      % (100 * je[0.0], 100 * je[-0.10], 100 * (je[-0.10] - je[0.0]), 100 * je[-0.30], 100 * (je[-0.30] - je[0.0])))
ok = 0.04 <= 100 * (je[-0.10] - je[0.0]) <= 0.10 and 100 * (je[-0.30] - je[0.0]) < 0.25
print("Gegenprobe %s" % ("BESTANDEN" if ok else "NICHT BESTANDEN"))
