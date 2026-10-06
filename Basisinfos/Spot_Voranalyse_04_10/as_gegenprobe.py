"""Gegenprobe Asymmetrie-Messung (python Basisinfos/Spot_Voranalyse_04_10/as_gegenprobe.py) - eigener Rechenweg, nur lesend.

  G1 Merkmale F1, F2, F3, F5, F6, F8, F11 fuer 10 zufaellige Coin-Anker direkt aus SQL nachgerechnet
  G2 Saldo des oberen Fuenftels von F3 in E2 und E3 mit pandas (rank/groupby) statt der Zellenschleife
  G3 Lift R2 / Lift D2 derselben Faelle mit pandas
"""
import os, random, sqlite3, sys
from datetime import timedelta
import numpy as np, pandas as pd

os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, "Basisinfos/Spot_Voranalyse_04_10")
import as_messung as M  # noqa: E402

D = M.paare(365).reset_index(drop=True)
F = M.merkmale(D)
c = sqlite3.connect("file:data/messdaten.db?mode=ro", uri=True)
cf = sqlite3.connect("file:data/funding_historie.db?mode=ro", uri=True)

random.seed(12)
gleich = n = 0
for j in random.sample(range(len(D)), 10):
    t, s = D.t[j], D.sym[j]
    r = pd.read_sql("SELECT date, close FROM price_history_ohlc WHERE assetklasse='krypto' AND currency='USD' AND symbol=? AND date<=? ORDER BY date",
                    c, params=(s, t.date().isoformat()), parse_dates=["date"]).set_index("date")["close"].asfreq("D")
    x = r.iloc[-1]
    eigen = {}
    if r.notna().sum() >= 180:
        eigen["F1"] = x / r.max() - 1
        eigen["F2"] = (t - r.idxmax()).days
        eigen["F5"] = x / r.iloc[-365:].min() - 1 if r.iloc[-365:].notna().sum() >= 180 else np.nan
    ret = r.pct_change(fill_method=None)
    w = ret.iloc[-91:-1]
    eigen["F3"] = w.std() if w.notna().sum() >= 60 else np.nan
    if len(r) > 180 and pd.notna(r.iloc[-181]):
        eigen["F6"] = x / r.iloc[-181] - 1
    eigen["F8"] = (t - r.first_valid_index()).days
    fu = cf.execute("SELECT wert FROM funding WHERE symbol=? AND datum>=? AND datum<=?", (s, (t - timedelta(days=30)).date().isoformat(),
                                                                                       (t - timedelta(days=1)).date().isoformat())).fetchall()
    eigen["F11"] = np.mean([v for v, in fu]) if len(fu) >= 20 else np.nan
    for k, v in eigen.items():
        m = F[k][j]
        ok = (np.isnan(v) and np.isnan(m)) or (not np.isnan(v) and not np.isnan(m) and abs(v - m) <= 1e-9 * max(1, abs(v)))
        gleich += ok; n += 1
        if not ok:
            print("G1 ABWEICHUNG %s %s %s: Messung %r Gegenprobe %r" % (t.date(), s, k, m, v))
print("G1 Merkmale: %d von %d Werten gleich (10 Coin-Anker)" % (gleich, n))

d = D.assign(f=F["F3"], a=D.r2.astype(float) - D.l.astype(float))
d = d[d.f.notna()]
d["n_z"] = d.groupby(["t", "kl"]).f.transform("count")
d = d[d.n_z >= 10]
d["p"] = d.groupby(["t", "kl"]).f.rank(pct=True)
d["s_alle"] = d.groupby(["t", "kl"]).a.transform("mean")
for ep in ("E2", "E3"):
    x = d[d.ep == ep]
    q = x[x.p > 0.8]
    zelle = q.groupby(["t", "kl"]).agg(sq=("a", "mean"), salle=("s_alle", "first")).join(x.groupby(["t", "kl"]).size().rename("nz"))
    zelle["v"] = (zelle.sq - zelle.salle) * zelle.nz
    tag = zelle.groupby(level=0).apply(lambda z: z.v.sum() / z.nz.sum())
    lr2 = q.r2.sum() / (x.groupby(["t", "kl"]).r2.transform("mean")[q.index]).sum()
    ld2 = q.d2.sum() / (x.groupby(["t", "kl"]).d2.transform("mean")[q.index]).sum()
    o = M.bewerte(M.Zellen(D), F["F3"], "oben", null=False, ep_liste=(ep,))[ep]
    print("G2/G3 F3 oben %s: Saldo Gegenprobe %+.5f Messung %+.5f · Lift R2 %.5f / %.5f · Lift D2 %.5f / %.5f" % (ep, tag.mean(), o["saldo"], lr2, o["lift_r2"], ld2, o["lift_d2"]))
