"""Altcoin-Spot Fassung 2 (antizyklisch + gefuehrt), Vorpruefung 06.10.2026: NUR Zahl der Ereignisse je Ansatz, Jahr und Klasse, KEINE Ertraege.
A  Boden je Coin: Coin >= 75 % unter seinem 365-T-Hoch, danach WENDE: Schluss ueber dem 50-T-Schnitt nach >= 60 T darunter (Ruhe 180 T je Coin)
B  Markt-Boden: BTC-Klima q <= 0,20 (Zone) - Episoden (Kaufzeitraum fuer einen Korb)
D  relative Trendfolge: Coin/BTC schliesst ueber seinem steigenden 200-T-Schnitt nach >= 60 T darunter (Ruhe 180 T)"""
import os, sqlite3, sys
import numpy as np, pandas as pd
os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.argv = ["x"]
src = open("Basisinfos/Spot_Voranalyse_04_10/s3_stufe1.py", encoding="utf-8").read().split("zeilen, gnh = [], {}")[0]
g = {"__file__": os.path.abspath("Basisinfos/Spot_Voranalyse_04_10/s3_stufe1.py")}; exec(compile(src, "s3", "exec"), g)
K, UNIV, klassen = g["K"], g["UNIV"], g["klassen"]
X = K[UNIV]
hoch365 = X.rolling(365, min_periods=180).max()
dd = X / hoch365 - 1
s50 = X.rolling(50, min_periods=50).mean()
unter = (X < s50).astype(float)
nach60 = unter.rolling(60).sum().shift(1) >= 60
tief = (dd.rolling(60).min() <= -0.75)
A = (X > s50) & nach60 & tief
rel = X.div(K["BTC"], axis=0)
r200 = rel.rolling(200, min_periods=200).mean()
unter_r = (rel < r200).astype(float)
D = (rel > r200) & (r200 > r200.shift(20)) & (unter_r.rolling(60).sum().shift(1) >= 60)
def mit_ruhe(E):
    out = []
    for s in E.columns:
        last = None
        for t in E.index[E[s].fillna(False)]:
            if last is None or (t - last).days >= 180:
                out.append((t, s)); last = t
    return pd.DataFrame(out, columns=["t", "sym"])
for name, E in (("A Boden je Coin (>= 75 % unter 365-T-Hoch, dann Wende ueber 50-T-Schnitt)", A), ("D relative Trendfolge (Coin/BTC ueber steigendem 200-T-Schnitt)", D)):
    ev = mit_ruhe(E); ev = ev[ev.t >= "2020-01-01"]
    kl = []
    for t, s in ev.itertuples(index=False):
        k, _ = klassen(t.replace(day=1)); kl.append(k.get(s, "-"))
    ev["klasse"] = kl
    print(name)
    print(ev.groupby([ev.t.dt.year, "klasse"]).size().unstack(fill_value=0).to_string())
src_q = open("Basisinfos/Spot_Voranalyse_04_10/k3_gewichten.py", encoding="utf-8").read().split("pb, mb = lade")[0]
gq = {"__file__": os.path.abspath("Basisinfos/Spot_Voranalyse_04_10/k3_gewichten.py")}; exec(compile(src_q, "k3", "exec"), gq)
pb, mb = gq["lade"]("btc"); q = gq["klima"](pb, mb, pd.Timestamp("2013-01-01"))
z = (q <= 0.20)[q.index >= "2018-01-01"]
ep, a0, lz = [], None, None
for t, v in z.items():
    if v:
        if a0 is None or (lz is not None and (t - lz).days >= 30):
            if a0 is not None: ep.append((a0, lz))
            a0 = t
        lz = t
if a0 is not None: ep.append((a0, lz))
print("B Markt-Boden (BTC-Klima-Zone q <= 0,20), Episoden:", " · ".join("%s..%s" % (a.date(), e.date()) for a, e in ep))
