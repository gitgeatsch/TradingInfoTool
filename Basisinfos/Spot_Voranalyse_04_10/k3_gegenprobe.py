"""Gegenprobe K-3 (python Basisinfos/Spot_Voranalyse_04_10/k3_gegenprobe.py): V3/DCA mit eigener Monatsschleife nachgerechnet, dazu WORAN (q je Jahr)."""
import os, sqlite3, numpy as np, pandas as pd
os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
src = open("Basisinfos/Spot_Voranalyse_04_10/k3_gewichten.py", encoding="utf-8").read().split("pb, mb = lade")[0]
g = {"__file__": os.path.abspath("Basisinfos/Spot_Voranalyse_04_10/k3_gewichten.py")}; exec(compile(src, "k3", "exec"), g)
pb, mb = g["lade"]("btc"); q = g["klima"](pb, mb, pd.Timestamp("2013-01-01")); pb = pb[:"2026-10-04"]
for st in ("2017-01-01", "2018-01-01", "2021-01-01"):
    tage = pd.date_range(st, "2026-10-04", freq="MS"); bar = c3 = cd = 0.0
    for t in tage:
        bar += 1; k = bar * (1 - q[t - pd.Timedelta(days=1)]); c3 += k / pb[t]; bar -= k; cd += 1 / pb[t]
    print("Start %s: V3/DCA %.3f (V3 %.1f, DCA %.1f)" % (st, (c3 * pb.iloc[-1] + bar) / (cd * pb.iloc[-1]), c3 * pb.iloc[-1] + bar, cd * pb.iloc[-1]))
print("WORAN - Klima q (BTC) je Jahr, Mittel am Monatsersten, und Kursaenderung im Jahr:")
for j in range(2017, 2027):
    x = q["%d" % j]; x = x[x.index.day == 1]; k = pb["%d" % j]
    print("  %d  q %.2f  Kaufanteil %.2f  Kurs %+5.0f %%" % (j, x.mean(), 1 - x.mean(), 100 * (k.iloc[-1] / k.iloc[0] - 1)))
