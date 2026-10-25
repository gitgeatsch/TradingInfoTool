"""P89d URSACHE L1-a (25.10.2026, §9.5: Fassung 2 haelt nicht -> Ursache) wie p89b, aber NUR Coins mit >= 730 T in beiden Quellen: Rangkorrelation CMC gegen Binance JE MERKMAL (F1, F2, F8) und Jahr.

    python -X utf8 Basisinfos/Rechenkern_02_10/p89d_bruecke_ursache_gleiche_historie.py
Nur lesend. Binance-Merkmale aus as_messung.merkmale (dieselben, die den B4-Wert bilden), CMC aus p89.merkmale.
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
    for k in ("F1", "F2", "F8"):
        D[k] = F[k]
    W = P89.merkmale(P89.lade())
    wochen = np.sort(W.stichtag.unique())
    z = []
    for t in sorted(D.t.unique()):
        i = np.searchsorted(wochen, np.datetime64(t), side="right") - 1
        if i < 0:
            continue
        C = W[W.stichtag == wochen[i]]
        C = C[~C.symbol.duplicated(keep=False)]
        m = D[D.t == t].merge(C[["symbol", "F1", "F2", "F8", "erst"]], left_on="sym", right_on="symbol", suffixes=("_b", "_c"))
        m = m[(m.F8_b >= 730) & ((pd.Timestamp(t) - m.erst).dt.days >= 730)]
        for k in ("F1", "F2", "F8"):
            ok = m[k + "_b"].notna() & m[k + "_c"].notna()
            if ok.sum() >= 10:
                z.append((pd.Timestamp(t).year, k, m.loc[ok, k + "_b"].rank().corr(m.loc[ok, k + "_c"].rank()), int(ok.sum())))
        # Zensur des Alters: Anteil gemeinsamer Coins, deren erstes CMC-Erscheinen die erste CMC-Woche ist (2016-07-03)
        z.append((pd.Timestamp(t).year, "F8 zensiert (erst = 2016-07-03)", float((m.erst == W.stichtag.min()).mean()) if len(m) else np.nan, len(m)))
    Z = pd.DataFrame(z, columns=["jahr", "merkmal", "wert", "n"])
    print("P89d URSACHE L1-a (>= 730 T in beiden Quellen): Rangkorrelation CMC gegen Binance je Merkmal und Jahr (Mittel der Stichtage)\n")
    print(Z.pivot_table(index="merkmal", columns="jahr", values="wert", aggfunc="mean").round(2).to_string())


if __name__ == "__main__":
    main()
