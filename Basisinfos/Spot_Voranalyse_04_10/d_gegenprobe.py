"""Gegenprobe D1/D2 (python Basisinfos/Spot_Voranalyse_04_10/d_gegenprobe.py): zwei Faelle mit eigener, einfacher Schleife nachgerechnet."""
import os, sqlite3
import pandas as pd
os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
src = open("Basisinfos/Spot_Voranalyse_04_10/k3_gewichten.py", encoding="utf-8").read().split("pb, mb = lade")[0]
g = {"__file__": os.path.abspath("Basisinfos/Spot_Voranalyse_04_10/k3_gewichten.py")}; exec(compile(src, "k3", "exec"), g)
pb, mb = g["lade"]("btc"); pe, _ = g["lade"]("eth"); q = g["klima"](pb, mb, pd.Timestamp("2013-01-01"))
c = sqlite3.connect("file:data/messdaten.db?mode=ro", uri=True)
ps = pd.read_sql("SELECT date, close FROM price_history_ohlc WHERE assetklasse='krypto' AND currency='USD' AND symbol='SOL'", c, parse_dates=["date"]).set_index("date")["close"].asfreq("D").ffill()
# D1: V2 R0 Start 2021-01-01 bis 2026-09-20 gegen M0
ende = pd.Timestamp("2026-09-20"); mon = pd.date_range("2021-01-01", ende, freq="MS")
b = sum(0.7 / pb[t] for t in mon); e = sum(0.2 / pe[t] for t in mon); s = sum(0.1 / ps[t] for t in mon); m0 = sum(1 / pb[t] for t in mon)
print("D1 V2 R0 Start 2021: Vermoegen / M0 = %.2f" % ((b * pb[ende] + e * pe[ende] + s * ps[ende]) / (m0 * pb[ende])))
# D2: BTC b1 Start 2017-01-01: 10 % je Stufe 0,8/0,9/0,95, alles zurueck bei der ersten Zone; Stufen wieder scharf nach Zone
tage = pd.date_range("2017-01-01", pb.index[-1]); stk = h = geld = 0.0; scharf = {0.8, 0.9, 0.95}
for t in tage:
    if t.day == 1 or t == tage[0]:
        stk += 1 / pb[t]; h += 1 / pb[t]
    qq = q[t - pd.Timedelta(days=1)]
    for x in sorted(scharf):
        if qq >= x:
            scharf.discard(x); geld += 0.1 * stk * pb[t]; stk *= 0.9
    if qq <= 0.2:
        scharf = {0.8, 0.9, 0.95}
        if geld > 0:
            stk += geld / pb[t]; geld = 0.0
print("D2 BTC b1 Start 2017: Stueck / H0 = %.3f" % (stk / h))
