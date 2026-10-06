"""Gegenprobe MACD (python Basisinfos/Spot_Voranalyse_04_10/macd_gegenprobe.py) - eigener Rechenweg, nur lesend.

  G1 Kettenindex: in Monaten ohne Zu- oder Abgang von Assets muss die Monatsaenderung des Kettenindex gleich der Aenderung der einfachen Summe sein
  G2 MACD: eigene EMA-Schleife (alpha = 2/(n+1), Start = erster Wert) auf den Monatsschluessen, Kreuzungsdaten gegen macd_messung
"""
import os, sqlite3, sys
import numpy as np, pandas as pd
os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, "Basisinfos/Spot_Voranalyse_04_10")
import macd_messung as M

C = M.lade()
alt = [a for a in C.columns if a not in M.STATT]
I3 = M.kette(C[[a for a in alt if a != "eth"]])
P = C[[a for a in alt if a != "eth"]]
P = P[P.index >= "2014-01-01"]
mo_ix = I3.resample("ME").last()
gleich = n = 0
for k in range(1, len(mo_ix)):
    a, b = mo_ix.index[k - 1], mo_ix.index[k]
    w = P[(P.index >= a) & (P.index <= b)]
    if w.notna().all().equals(w.notna().any()) and (w.notna().sum() == len(w)).sum() == w.notna().any().sum():   # gleiche Assets durchgehend
        s0, s1 = w.iloc[0].sum(), w.iloc[-1].sum()
        n += 1; gleich += abs((s1 / s0) - (mo_ix.iloc[k] / mo_ix.iloc[k - 1])) < 1e-9
print("G1 Kettenindex I3: %d von %d Monaten ohne Zu-/Abgang gleich der einfachen Summe" % (gleich, n))


def ema(x, n):
    a, out = 2 / (n + 1), []
    for v in x:
        out.append(v if not out else a * v + (1 - a) * out[-1])
    return np.array(out)


for name, reihe in (("I1", M.kette(C[alt])), ("I3", I3)):
    ende = C.dropna(how="all").index.max()
    m = reihe.resample("ME").last(); m = m[m.index <= ende]
    if ende.day < m.index[-1].day:
        m = m.iloc[:-1]
    x = m.values
    l = ema(x, 12) - ema(x, 26); s = ema(l, 9)
    S = [m.index[k].strftime("%Y-%m") for k in range(36, len(x)) if l[k] > s[k] and l[k - 1] <= s[k - 1]]
    N = [m.index[k].strftime("%Y-%m") for k in range(36, len(x)) if l[k] > 0 and l[k - 1] <= 0]
    print("G2 %s eigene Schleife: S %s · N %s" % (name, ", ".join(S), ", ".join(N)))
