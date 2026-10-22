"""R-A GEGENRECHNUNG (22.10.2026, Recherche_Neue_Ansaetze_22_10.md P2): tragende Zahlen der Recherchen A und B mit EIGENEM Code nachrechnen.

    python Basisinfos/Rechenkern_02_10/ra_gegenrechnung.py

Daten (frei, Kopie in data/_ra/, nicht committet): AQR TSMOM monatlich, French Momentum und Research Factors; data/funding_historie.db (nur lesend).
G1 TSMOM: Sharpe 1985-2009 und 2013-05/2026 (Recherche B: 1,41 / 0,41)
G2 UMD (Momentum, French): Sharpe 1927-1993 und 1994-heute (Recherche B: 0,80 / 0,26 - Abgrenzung dort nicht genannt, hier Jegadeesh/Titman 1993)
G3 Funding je Jahr BTC/ETH/SOL in % p.a. (Recherche A: BTC 2024 11,9 · 2025 5,1 · 2026 2,6)
"""
import io
import os
import sqlite3
import sys
import zipfile

import numpy as np
import pandas as pd

os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass
R = os.path.join("data", "_ra")


def sharpe(r):
    r = np.asarray(r, float)
    return r.mean() / r.std(ddof=1) * np.sqrt(12), r.mean() / r.std(ddof=1) * np.sqrt(len(r))


x = pd.read_excel(os.path.join(R, "tsmom.xlsx"), header=None, skiprows=18).iloc[:, :2].dropna()
x.columns = ["datum", "tsmom"]
x["datum"] = pd.to_datetime(x.datum)
for a, b in (("1985-01-01", "2009-12-31"), ("2013-01-01", "2026-12-31")):
    s, t = sharpe(x[(x.datum >= a) & (x.datum <= b)].tsmom)
    print("G1 TSMOM %s..%s: Sharpe %.2f · t %.1f · Monate %d" % (a[:7], b[:7], s, t, ((x.datum >= a) & (x.datum <= b)).sum()))


def french(datei):
    z = zipfile.ZipFile(os.path.join(R, datei))
    t = z.read(z.namelist()[0]).decode("latin-1").splitlines()
    zeilen = [l.split(",") for l in t if l[:6].strip().isdigit() and len(l.split(",")[0].strip()) == 6]
    d = pd.DataFrame([[z_.strip() for z_ in l] for l in zeilen])
    d = d.drop_duplicates(0, keep="first")
    return d


m = french("F-F_Momentum_Factor_CSV.zip")
m.columns = ["ym", "umd"]
m["umd"] = m.umd.astype(float) / 100
m["ym"] = m.ym.astype(int)
for a, b in ((192701, 199312), (199401, 209912)):
    s, t = sharpe(m[(m.ym >= a) & (m.ym <= b)].umd)
    print("G2 UMD %d..%s: Sharpe %.2f · t %.1f" % (a, "heute" if b > 202700 else b, s, t))

c = sqlite3.connect("file:data/funding_historie.db?mode=ro", uri=True)
for sym in ("BTC", "ETH", "SOL"):
    f = pd.read_sql("SELECT datum, wert FROM funding WHERE symbol=?", c, params=(sym,), parse_dates=["datum"])
    teile = []
    for j in range(2020, 2027):
        y = f[f.datum.dt.year == j]
        if len(y):
            teile.append("%d %+.1f" % (j, 100 * y.wert.sum() * 365 / len(y)))
    print("G3 Funding %s %% p.a.: %s" % (sym, " · ".join(teile)))
c.close()
