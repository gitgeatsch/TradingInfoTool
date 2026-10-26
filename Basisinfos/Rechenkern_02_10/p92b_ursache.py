"""P92b URSACHE L1-c Schritt 0 nicht reproduziert (26.10.2026): liegt es am WERT (CMC-Fuenftel != Binance-Fuenftel) oder an
Gruppe/Ertrag/Universum? Auf denselben Coins (in beiden Quellen) und denselben CMC-Ertraegen (4 Wochen), Monatsstichtage 2019-01..2026-08:
  a) Fuenftel aus dem CMC-Wert   b) Fuenftel aus dem Binance-Wert (p85.wert_tabelle(1), wie A1)   - Gruppe CMC Top 30 bzw. Gesamt.
    python -X utf8 Basisinfos/Rechenkern_02_10/p92b_ursache.py
Nur lesend.
"""
import os
import sys

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
import p92_l1c_cmc_eigene_basis as P  # noqa: E402

import p85_atlas_voranalyse as P85  # noqa: E402


def main():
    B = P.Basis()
    BW = P85.wert_tabelle(1)
    BW["f_b"] = np.ceil(BW.p * 5).clip(1, 5)
    erg = {(g, v): [] for g in ("Top 30", "Gesamt") for v in ("a CMC-Wert", "b Binance-Wert", "c beide oben")}
    n_c = []
    for t in pd.date_range("2019-01-01", "2026-08-01", freq="MS"):
        i = np.searchsorted(B.wochen, np.datetime64(t), side="right") - 1
        Z = B.T[B.T.stichtag == B.wochen[i]]
        Z = Z[~Z.symbol.duplicated(keep=False)]
        r, aus = B.ertrag(Z, 4)
        if r is None:
            continue
        Z = Z.assign(r=r).merge(BW[BW.t == t][["sym", "f_b"]], left_on="symbol", right_on="sym")
        n_c.append(len(Z))
        for g, m in (("Top 30", Z.kl == "H"), ("Gesamt", np.ones(len(Z), bool))):
            G = Z[m]
            if len(G) < 5:
                continue
            for v, sel in (("a CMC-Wert", G.f == 5), ("b Binance-Wert", G.f_b == 5), ("c beide oben", (G.f == 5) & (G.f_b == 5))):
                if sel.any():
                    erg[(g, v)].append(G.r[sel].mean() - G.r.mean())
    print("P92b URSACHE · gemeinsame Coins je Stichtag im Mittel %.0f · CMC-Ertraege 4 Wochen · oberes Fuenftel minus Gruppe (gemeinsame Coins)\n" % np.mean(n_c))
    for (g, v), d in erg.items():
        d = np.array(d)
        lo, hi = P.P86.band(d, 3)
        print("  %-7s %-15s %3d Stichtage · %+.1f Pp [%+.1f; %+.1f]" % (g, v, len(d), 100 * d.mean(), 100 * lo, 100 * hi))


if __name__ == "__main__":
    main()
