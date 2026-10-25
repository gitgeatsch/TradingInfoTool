"""P89c L1-a (Voranalyse_L1_L2 §9.4, vorab 2d0c00cc): Bruecke Fassung 2 "gleiche Historie" - nur Coins mit >= 730 T Kursgeschichte in
BEIDEN Quellen (Binance-Alter F8 >= 730 und CMC seit erstem Erscheinen >= 730). Rangfolge des Werts unter diesen Coins je Stichtag und
Klasse (Zellen >= 10), Kriterium Mittel >= 0,8 und oberes Fuenftel >= 50 % gleich.

    python -X utf8 Basisinfos/Rechenkern_02_10/p89c_bruecke_gleiche_historie.py
Nur lesend.
"""
import os
import sys

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(os.path.dirname(HIER))
sys.path.insert(0, os.path.join(WURZEL, "Basisinfos", "Spot_Voranalyse_04_10"))
sys.path.insert(0, HIER)
os.chdir(WURZEL)
sys.stdout.reconfigure(encoding="utf-8")
import warnings  # noqa: E402

warnings.filterwarnings("ignore", category=RuntimeWarning)
import p85_atlas_voranalyse as P85  # noqa: E402
import p89_l1_cmc as P89  # noqa: E402

MK = P85.MK


def main():
    D = MK.paare_mw(1).reset_index(drop=True)
    F = P85.M.merkmale(D)
    D["F8"] = F["F8"]
    B = P85.wert_tabelle(1).merge(D[["t", "sym", "F8"]], on=["t", "sym"], how="left")
    W = P89.merkmale(P89.lade())
    T = P89.wert(W).merge(W[["stichtag", "id", "erst"]], on=["stichtag", "id"])
    wochen = np.sort(T.stichtag.unique())
    rk, ueb, n_c, je = [], [], [], []
    for t in sorted(B.t.unique()):
        if t < pd.Timestamp("2019-01-01"):
            continue
        i = np.searchsorted(wochen, np.datetime64(t), side="right") - 1
        if i < 0:
            continue
        C = T[T.stichtag == wochen[i]]
        C = C[~C.symbol.duplicated(keep=False)]
        m = B[B.t == t].merge(C[["symbol", "p", "erst"]], left_on="sym", right_on="symbol", suffixes=("_b", "_c"))
        m = m[m.p_b.notna() & m.p_c.notna() & (m.F8 >= 730) & ((pd.Timestamp(t) - m.erst).dt.days >= 730)]
        n_c.append(len(m))
        for k, z in m.groupby("kl"):
            if len(z) >= 10:
                r = z.p_b.rank().corr(z.p_c.rank())
                rk.append(r)
                je.append((pd.Timestamp(t).year, r))
        if len(m) >= 10:
            fb = np.ceil(m.p_b.rank(pct=True) * 5)
            fc = np.ceil(m.p_c.rank(pct=True) * 5)
            o = fb == 5
            if o.sum():
                ueb.append(float((fc[o] == 5).mean()))
    r_m, u_m = float(np.nanmean(rk)), float(np.mean(ueb))
    ok = r_m >= 0.8 and u_m >= 0.5
    print("P89c L1-a BRUECKE FASSUNG 2 'gleiche Historie' (>= 730 T in beiden Quellen), Monatsstichtage 2019-01..2026-09")
    print("  Zellen %d · gemeinsame Coins mit gleicher Historie je Stichtag im Mittel %.0f" % (len(rk), np.mean(n_c)))
    print("  Rangkorrelation im Mittel %.3f (Soll >= 0,8) · Median %.3f · 10. Perz. %.3f" % (r_m, float(np.nanmedian(rk)), float(np.nanpercentile(rk, 10))))
    print("  oberes Fuenftel gleich %.0f %% (Soll >= 50 %%)" % (100 * u_m))
    j = pd.DataFrame(je, columns=["jahr", "r"])
    print("  je Jahr: " + " · ".join("%d %.2f (%d Zellen)" % (a, g.r.mean(), len(g)) for a, g in j.groupby("jahr")))
    print("  -> BRUECKE FASSUNG 2 %s" % ("HAELT - die Abweichung in Teil 1 lag an der Datenlaenge" if ok else "HAELT NICHT - Unterschied ueber die Datenlaenge hinaus"))


if __name__ == "__main__":
    main()
