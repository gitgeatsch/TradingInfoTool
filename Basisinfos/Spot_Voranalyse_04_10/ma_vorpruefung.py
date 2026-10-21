"""M-A Vorpruefung (21.10.2026): NUR Zustandswechsel und Datenlage der drei Literatur-Trendregeln auf BTC - KEINE Ertraege.

    python Basisinfos/Spot_Voranalyse_04_10/ma_vorpruefung.py

R1 Tagesschluss ueber dem 200-Tage-Schnitt (gleitend, Tage) · R2 Monatsschluss ueber dem 10-Monats-Schnitt (Faber 2007)
R3 Zeitreihen-Momentum: Ertrag der letzten 12 Monate > 0 (Moskowitz/Ooi/Pedersen 2012). Gezaehlt: Wechsel je Jahr, Anteil 'drin'.
"""
import os
import sqlite3
import sys

import pandas as pd

os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass
c = sqlite3.connect("file:data/_spot/coinmetrics.db?mode=ro", uri=True)
P = pd.read_sql("SELECT tag, PriceUSD FROM tag WHERE asset='btc' AND PriceUSD IS NOT NULL", c, parse_dates=["tag"]).set_index("tag").PriceUSD
c.close()
print("BTC Kurs %s bis %s, %d Tage, Luecken im Tagesraster %d" % (P.index[0].date(), P.index[-1].date(), len(P),
      len(pd.date_range(P.index[0], P.index[-1])) - len(P)))
r1 = (P > P.rolling(200).mean()).where(P.rolling(200).count() == 200)
M = P.resample("ME").last()
r2 = (M > M.rolling(10).mean()).where(M.rolling(10).count() == 10)
r3 = (M / M.shift(12) - 1 > 0).where(M.shift(12).notna())
zeilen = []
for name, s in (("R1 200-Tage", r1), ("R2 10-Monate", r2), ("R3 12-Monats-Momentum", r3)):
    s = s.dropna().astype(bool)
    w = s.ne(s.shift()).iloc[1:]
    print("\n%s: ab %s" % (name, s.index[0].date()))
    for j in range(s.index[0].year, s.index[-1].year + 1):
        sj = s[s.index.year == j]
        zeilen.append((name, j, int(w[w.index.year == j].sum()), round(sj.mean(), 2)))
        print("  %d  Wechsel %3d  Anteil drin %.2f" % zeilen[-1][1:])
