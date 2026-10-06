"""Gegenprobe der Vorpruefung Asymmetrie: 12 zufaellige Coin-Anker (365 T) mit eigener Schleife direkt aus SQL - R2, R3, L, eingestellt."""
import os, random, sqlite3, sys
from datetime import timedelta
import pandas as pd
os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, "Basisinfos/Spot_Voranalyse_04_10")
import as_vorpruefung as V
c = sqlite3.connect("file:data/messdaten.db?mode=ro", uri=True)
ende = pd.Timestamp(c.execute("SELECT MAX(date) FROM price_history_ohlc WHERE assetklasse='krypto' AND currency='USD'").fetchone()[0])
random.seed(11)
D = V.anker(365)
gl = 0
for r in D.sample(12, random_state=11).itertuples():
    d1 = (r.t + timedelta(days=1)).date()
    p = dict(c.execute("SELECT date, close FROM price_history_ohlc WHERE assetklasse='krypto' AND currency='USD' AND symbol=? AND date>=? AND date<=?",
                       (r.sym, d1.isoformat(), (d1 + timedelta(days=365)).isoformat())).fetchall())
    v = []
    for k in range(366):
        x = p.get((d1 + timedelta(days=k)).isoformat())
        if x is None: break
        v.append(x)
    eing = len(v) < 366 and (pd.Timestamp(d1) + timedelta(days=len(v) - 1)) < ende - timedelta(days=10)
    e = (max(v) / v[0] >= 2, max(v) / v[0] >= 3, min(v) / v[0] <= 0.30 or eing, eing)
    m = (bool(r.r2), bool(r.r3), bool(r.l), bool(r.eing))
    gl += e == m
    print("%s %-9s %s  Messung R2/R3/L/eing %s  Gegenprobe %s  %s" % (r.t.date(), r.sym, r.kl, m, e, "gleich" if e == m else "ABWEICHUNG"))
print("\n%d von 12 gleich" % gl)
