"""K-1/K-2 Messplan (Spot §44) - Gegenprobe der MACHBARKEIT vor dem Plan. Nur lesend, Desktop.

    python Basisinfos/Spot_Voranalyse_04_10/k44_machbarkeit_gegenprobe.py

  M1 Spitzen-Tage 2023 mit eigenem SQL (Tagesschluss = letzte Stunde des Tages, eigener 30-T-Vergleich per Datum statt Zeilenversatz)
  M2 Einstiege H 2023 an Spitzen-Tagen: 29 an 6 Monaten (Plan §44.2)
  M3 Teil 0 vorab machbar: auf 2024+ +6,3 Pp (n 71) / -0,8 Pp aus der Ablage k37_messung_H.csv, Korb je Monat wie §37.2
"""
import os
import sqlite3
from datetime import timedelta

import pandas as pd

os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
ERG = []


def pruefe(k, ok, text):
    ERG.append(bool(ok))
    print("%-3s %-10s %s" % (k, "gleich" if ok else "ABWEICHUNG", text))


c = sqlite3.connect("file:data/richtung_historie.db?mode=ro", uri=True)
rows = c.execute("SELECT stunde, close FROM btcdom ORDER BY stunde").fetchall()
schluss = {}
for st, cl in rows:
    schluss[st[:10]] = cl            # letzte Stunde des Tages gewinnt (sortiert)
tage = sorted(schluss)
spitze = set()
for d in tage:
    v = (pd.Timestamp(d) - timedelta(days=30)).strftime("%Y-%m-%d")
    if v in schluss and schluss[d] / schluss[v] - 1 >= 0.087:
        spitze.add(d)
s23 = sorted(x for x in spitze if x.startswith("2023"))
pruefe("M1", len(s23) == 75 and len({x[5:7] for x in s23}) == 8, "Spitzen-Tage 2023: %d in %d Monaten (Plan 75 / 8)" % (len(s23), len({x[5:7] for x in s23})))

E = pd.read_csv("data/_spot/k37_einstiege_H_W.csv", sep=";", parse_dates=["signal"])
e = E[E.signal.dt.strftime("%Y-%m-%d").isin(spitze)]
pruefe("M2", len(e) == 29 and e.signal.dt.to_period("M").nunique() == 6, "Einstiege H 2023 an Spitzen-Tagen: %d an %d Monaten (Plan 29 / 6)" % (
    len(e), e.signal.dt.to_period("M").nunique()))

U = pd.read_csv("data/_spot/k37_messung_H.csv", sep=";", parse_dates=["signal"])
sp = U.signal.dt.strftime("%Y-%m-%d").isin(spitze)


def korb(g):
    return g.groupby(g.signal.dt.to_period("M")).ex.mean().mean()


a, b = 100 * korb(U[sp]), 100 * korb(U[~sp])
pruefe("M3", int(sp.sum()) == 71 and abs(a - 6.3) < 0.1 and abs(b + 0.8) < 0.1, "2024+ Spitze %+.2f Pp (n %d) / sonst %+.2f Pp (Plan +6,3 / 71 / -0,8)" % (
    a, int(sp.sum()), b))
print("\n%d von %d gleich" % (sum(ERG), len(ERG)))
