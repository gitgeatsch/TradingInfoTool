"""Gegenprobe Messung §25 (python Basisinfos/Spot_Voranalyse_04_10/mk_gegenprobe.py) - eigener Rechenweg, nur lesend.

  G1 Marktwert und Marktwert-Rang fuer 10 Coin-Stichtage direkt aus SQL (Kurs, Umlauf aus strukturprofil.db bzw. CoinMetrics) gegen mk_messung
  G2 Klasse H/M/S fuer dieselben Faelle aus dem eigenen Rang (t, t-1M, t-2M, Alter) gegen mk_messung.klassen_mw
  G3 Saldo eines binaeren Fakts (A1 Hoechstmenge fest, E3) mit pandas gegen mk_messung.binaer
  G4 QNT 06/2022: Kurs, Umlauf, Marktwert, Rang direkt aus SQL
"""
import os, random, sqlite3, sys
from datetime import timedelta
import numpy as np, pandas as pd

os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, "Basisinfos/Spot_Voranalyse_04_10")
import mk_messung as MK  # noqa: E402
A, M = MK.A, MK.M
c = sqlite3.connect("file:data/messdaten.db?mode=ro", uri=True)
pr = pd.read_sql("SELECT symbol, umlauf FROM profil", sqlite3.connect("file:data/_spot/strukturprofil.db?mode=ro", uri=True)).set_index("symbol").umlauf
oc = sqlite3.connect("file:data/onchain_historie.db?mode=ro", uri=True)


def kurs(s, t):
    r = c.execute("SELECT close FROM price_history_ohlc WHERE assetklasse='krypto' AND currency='USD' AND symbol=? AND date=?", (s, t.date().isoformat())).fetchone()
    return r[0] if r else np.nan


def uml(s, t):
    r = oc.execute("SELECT datum, wert FROM splycur WHERE symbol=? AND datum<=? ORDER BY datum DESC LIMIT 1", (s, t.date().isoformat())).fetchone()
    if r and (t - pd.Timestamp(r[0])).days <= 7 and r[1] > 0:
        return r[1]
    return pr.get(s, np.nan)


def eigener_rang(t):
    kl = A.klassen(t)[0]
    mw = {s: uml(s, t) * kurs(s, t) for s in kl}
    return pd.Series({s: v for s, v in mw.items() if v == v and v > 0}).rank(ascending=False)


random.seed(14)
gl = n = 0
faelle = [(pd.Timestamp(t), s) for t, s in [("2022-06-01", "QNT"), ("2024-03-01", "LINK"), ("2025-05-01", "HBAR")]]
for t in random.sample(list(pd.date_range("2021-01-01", "2025-08-01", freq="MS")), 7):
    kl = A.klassen(t)[0]
    faelle.append((t, random.choice(sorted(kl))))
cache = {}
for t, s in faelle:
    for tt in (t, t - pd.DateOffset(months=1), t - pd.DateOffset(months=2)):
        if tt not in cache:
            cache[tt] = eigener_rang(tt)
    r = cache[t]
    mess_out, _, ums = MK.klassen_mw(t)
    if s not in r.index:
        eigen_k = ums.get(s)
    else:
        x = r[s]
        alt = (t - A.K[s].dropna().index[0]).days >= 730
        eigen_k = "H" if (x <= 30 and cache[t - pd.DateOffset(months=1)].get(s, 999) <= 30 and cache[t - pd.DateOffset(months=2)].get(s, 999) <= 30 and alt) \
            else ("M" if x <= 100 else "S")
    _, mr = MK.rang_mw(t)
    ok = (eigen_k == mess_out.get(s)) and ((s not in r.index and s not in mr.index) or abs(r.get(s, np.nan) - mr.get(s, np.nan)) < 1e-9)
    gl += ok; n += 1
    print("G1/G2 %s %-7s Rang eigen %s / Messung %s · Klasse eigen %s / Messung %s  %s" % (
        t.date(), s, r.get(s, "-"), mr.get(s, "-"), eigen_k, mess_out.get(s), "gleich" if ok else "ABWEICHUNG"))
D = MK.paare_mw(365).reset_index(drop=True)
Z = M.Zellen(D)
F = M.merkmale(D)
FA = MK.fakten(D, F)
x = FA["A1 Hoechstmenge fest"]
d = D.assign(x=x, a=D.r2.astype(float) - D.l.astype(float))
d = d[d.x.notna() & (d.ep == "E3")]
d["nz"] = d.groupby(["t", "kl"]).x.transform("count")
d["nm"] = d.groupby(["t", "kl"]).x.transform("sum")
d = d[(d.nz >= 10) & (d.nm > 0) & (d.nm < d.nz)]
zelle = d.groupby(["t", "kl"]).apply(lambda g: pd.Series({"v": g[g.x == 1].a.mean() - g.a.mean(), "n": len(g)}))
tag = zelle.groupby(level=0).apply(lambda z: (z.v * z.n).sum() / z.n.sum())
MK.M.GRID.update({"E2": np.array([[1.0, 1.0]] * 300), "E3": np.array([[1.0, 1.0]] * 300)})   # nur fuer spiegel_ok im Aufruf, nicht Teil der Probe
mess = MK.binaer(Z, x)["E3"]["saldo"]
ok = abs(tag.mean() - mess) < 1e-9; gl += ok; n += 1
print("G3 A1 Hoechstmenge fest, E3: Saldo pandas %+.5f · Messung %+.5f  %s" % (tag.mean(), mess, "gleich" if ok else "ABWEICHUNG"))
t = pd.Timestamp("2022-06-01")
print("G4 QNT %s: Kurs %.2f · Umlauf %.0f · Marktwert %.2f Mrd · Rang %s von %d" % (t.date(), kurs("QNT", t), uml("QNT", t), uml("QNT", t) * kurs("QNT", t) / 1e9,
                                                                               int(cache[t]["QNT"]), len(cache[t])))
print("\n%d von %d gleich" % (gl, n))
