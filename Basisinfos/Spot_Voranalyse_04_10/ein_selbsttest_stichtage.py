"""EICHUNG der Pruefanlage aus §29.2 - ab wie vielen Stichtagen haelt sie ihren Fehlalarm? (nachtraeglich, KEIN Ergebnis zu E-b)

    python Basisinfos/Spot_Voranalyse_04_10/ein_selbsttest_stichtage.py

Anlass: Selbsttest (a) in ein_messung.txt Fehlalarm 22 % bei 3 Stichtagen; Ursache Bootstrap-Entartung (Gegenprobe H7).
Gleiche Bedingungen (1)+(2) wie ein_messung.urteil (Block-Bootstrap zu 3, Zufallswelt gleiche Klasse), Null = Zufalls-Tor ueber die E-a-Einstiege.
Je Epoche und k offenen Stichtagen 100 Welten (Zufallswelt 100 Ziehungen). Liest nur data/_spot/ein_messung_anker.csv.
Zweck: die Mindestzahl Stichtage fuer das Vorwaertsprotokoll (§29.3) aus der Anlage ableiten statt setzen.
"""
import os

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
os.chdir(os.path.dirname(os.path.dirname(HIER)))
RNG = np.random.default_rng(20261008)
R = pd.read_csv(os.path.join("data", "_spot", "ein_messung_anker.csv"), sep=";", parse_dates=["t"])
KL = R[(R.arm == "KL") & (R.aus == "X2")]
POOL = {(t, k): g.ex.values for (t, k), g in KL.groupby(["t", "kl"])}


def boot(vals, n=1000):
    bs = []
    for _ in range(n):
        st = RNG.integers(0, max(len(vals) - 2, 1), size=int(np.ceil(len(vals) / 3)))
        bs.append(np.concatenate([vals[k:k + 3] for k in st])[:len(vals)].mean())
    return float(np.mean(np.array(bs) > 0))


def traegt(x, nz=100):
    jt = x.groupby("t").ex.mean().sort_index()
    if not len(jt) or jt.mean() <= 0 or boot(jt.values) < 0.95:
        return False
    z = []
    for _ in range(nz):
        m = []
        for t, g in x.groupby("t"):
            v = []
            for k, gg in g.groupby("kl"):
                p = POOL.get((t, k))
                if p is not None and len(p):
                    v += list(RNG.choice(p, size=len(gg)))
            m.append(np.mean(v))
        z.append(np.mean(m))
    return np.mean(np.array(z) < jt.mean()) >= 0.95


print("EICHUNG Pruefanlage §29.2: Fehlalarm des Zufalls-Tors nach Zahl offener Stichtage (100 Welten je Zeile)\n")
for ep in ("E2", "E3"):
    ea = R[(R.arm == "E-a") & (R.aus == "X2") & (R.ep == ep)]
    tage = np.array(sorted(ea.t.unique()))
    zeilen = []
    for k in (3, 4, 6, 8, 12, 16):
        if k > len(tage):
            continue
        f = sum(traegt(ea[ea.t.isin(RNG.choice(tage, size=k, replace=False))]) for _ in range(100))
        zeilen.append("k %2d: %3d %%" % (k, f))
    print("  %s (E-a: %d Einstiege an %d Stichtagen, Korb %+.1f %%): %s" % (
        ep, len(ea), len(tage), 100 * ea.groupby("t").ex.mean().mean(), " · ".join(zeilen)))
print("\nSoll <= 5 %. Die kleinste Zahl k, ab der beide Epochen <= 5 % liegen, ist die Mindestzahl Stichtage fuer das Vorwaertsprotokoll.")
