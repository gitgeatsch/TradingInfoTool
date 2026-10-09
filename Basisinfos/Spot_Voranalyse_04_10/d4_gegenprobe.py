"""Gegenprobe D4 (§39.9) - eigene Perzentile je Zelle (pandas groupby), eigener Wert, eigener Saldo; gegen d4_wirkung.csv/.txt, nur lesend.

  G1/G2 Fuenftel mit vollem Wert / ohne F9 je Anker gleich der Ablage · G3 Wechselanteil E3 gleich der Ausgabe
  G4/G5 Saldo unteres Fuenftel E3 voll (-16,3) und ohne F9 (-17,2) aus eigener Rechnung
"""
import os
import re
import sys

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
os.chdir(os.path.dirname(os.path.dirname(HIER)))
import mk_messung as MK  # noqa: E402

ok = n = 0


def pruefe(name, gut, info):
    global ok, n
    n += 1; ok += bool(gut)
    print("%-3s %s  %s" % (name, "gleich" if gut else "ABWEICHUNG", info), flush=True)


D = MK.paare_mw(365).reset_index(drop=True)
F = MK.M.merkmale(D)
X = pd.DataFrame({k: F[k] for k in ("F1", "F2", "F8", "F9")})
X["F1"] = -X["F1"]                                   # F1 'unten' -> umgedreht ranken
X["zelle"] = list(zip(D.t, D.kl))


def rang(s):
    return s.rank(pct=True) if s.notna().sum() >= 10 else s * np.nan


def eigen(merk):
    P = pd.concat([X.groupby("zelle")[k].transform(rang) for k in merk], axis=1)
    P.loc[:, "F1"] = 1 - X.groupby("zelle")["F1"].transform(lambda s: (-s).rank(pct=True) if s.notna().sum() >= 10 else s * np.nan)
    wert = P.mean(axis=1, skipna=True)
    p = wert.groupby(X.zelle).transform(rang)
    return np.where(p.isna(), np.nan, np.clip(np.ceil(p * 5), 1, 5)), p


A = pd.read_csv(os.path.join("data", "_spot", "d4_wirkung.csv"), sep=";")
q, p = eigen(["F1", "F2", "F8", "F9"])
q9, p9 = eigen(["F1", "F2", "F8"])
g = lambda a, b: np.array_equal(np.nan_to_num(a, nan=-1), np.nan_to_num(b, nan=-1))
pruefe("G1", g(q, A.q.values), "voller Wert: abweichende Anker %d" % int(np.sum(np.nan_to_num(q, nan=-1) != np.nan_to_num(A.q.values, nan=-1))))
pruefe("G2", g(q9, A.q9.values), "ohne F9: abweichende Anker %d" % int(np.sum(np.nan_to_num(q9, nan=-1) != np.nan_to_num(A.q9.values, nan=-1))))
aus = open(os.path.join("Basisinfos", "Spot_Voranalyse_04_10", "d4_wirkung.txt"), encoding="utf-8").read()
e = (D.ep.values == "E3") & ~np.isnan(q) & ~np.isnan(q9)
wa = float(re.search(r"D4 E3: .*?ohne F9 ([\d.]+) %", aus).group(1))
pruefe("G3", abs(100 * np.mean(q[e] != q9[e]) - wa) < 0.06, "eigener Wechselanteil E3 %.2f %% · Ausgabe %.1f %%" % (100 * np.mean(q[e] != q9[e]), wa))
a = D.r2.astype(float).values - D.l.astype(float).values


def saldo(pp, ep):
    num, den = {}, {}
    for (t, k), ix in D.groupby(["t", "kl"]).groups.items():
        if MK.A.epoche(t) != ep:
            continue
        ix = np.array(ix)
        m = ix[~np.isnan(pp[ix])]
        if len(m) < 10:
            continue
        u = m[pp[m] <= 0.2]
        if not len(u):
            continue
        num[t] = num.get(t, 0) + (a[u].mean() - a[m].mean()) * len(m); den[t] = den.get(t, 0) + len(m)
    return 100 * np.mean([num[t] / den[t] for t in sorted(den)])


s1, s9 = saldo(p.values, "E3"), saldo(p9.values, "E3")
pruefe("G4", abs(s1 + 16.3) < 0.06, "unteres Fuenftel E3 voll %+.2f Pp (Soll -16,3)" % s1)
pruefe("G5", abs(s9 + 17.2) < 0.06, "unteres Fuenftel E3 ohne F9 %+.2f Pp (Ausgabe -17,2)" % s9)
print("\n%d von %d gleich" % (ok, n))
