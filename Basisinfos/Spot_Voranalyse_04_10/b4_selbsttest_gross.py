"""B4-Vormessung (Spot §43) - Selbsttest GROSS, Auskunft: ist die Fehlalarmquote der bestaendigen Nullwelt hoeher als die Stufung erklaert?

    python Basisinfos/Spot_Voranalyse_04_10/b4_selbsttest_gross.py

200 bestaendige Zufallswerte, je 1.000 Ziehungen. Unter der Nullhypothese ist der Rang gleichverteilt (Zufallswert und Nullauswahl sind
gleich gebaut): je Seite (<= 0,025 bzw. >= 0,975) erwartet 26/1001 = 2,6 %, zusammen 5,2 %. Dazu der Rang selbst (Gleichverteilung,
Kolmogorow-Smirnow) und die Fehlalarmquote bei der Strenge des echten Befunds (Rang 0 von 200, also <= 0,005).
"""
import os
import sys

import numpy as np
from scipy import stats

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
import b4_vormessung as B  # noqa: E402

D4, MK, M, W = B.D4, B.MK, B.M, B.W
RNG = np.random.default_rng(20261045)
D = MK.paare_mw(365).reset_index(drop=True)
Z = M.Zellen(D)
p = M.pct_in_zelle(Z, W.wert(Z, M.merkmale(D), wahl=D4.OHNE_F9))
R = B.Rechner(D, p, D.ende.values - 1.0)
raenge = []
for i in range(200):
    g = np.where(np.isnan(p), np.nan, RNG.random(R.nsym)[R.code])
    a = R.abstand(g, "E3")
    raenge.append(float(np.mean(R.null(g, "E3", 1000, RNG) < a)))
r = np.array(raenge)
print("B4 SELBSTTEST GROSS (Auskunft) · E3 · 200 Zufallswerte x 1.000 Ziehungen")
print("  Rang <= 0,025: %d (%.1f %%) · Rang >= 0,975: %d (%.1f %%) · zusammen %.1f %% (erwartet 2,6 / 2,6 / 5,2 %%)" % (
    (r <= 0.025).sum(), 100 * np.mean(r <= 0.025), (r >= 0.975).sum(), 100 * np.mean(r >= 0.975), 100 * np.mean((r <= 0.025) | (r >= 0.975))))
print("  Rang <= 0,005 (Strenge des echten Befunds): %d (%.1f %%, erwartet 0,6 %%)" % ((r <= 0.005).sum(), 100 * np.mean(r <= 0.005)))
print("  Gleichverteilung des Rangs: KS p = %.3f" % stats.kstest(r, "uniform").pvalue)
