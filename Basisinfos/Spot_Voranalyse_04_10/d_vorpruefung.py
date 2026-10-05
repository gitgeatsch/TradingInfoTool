"""D1/D2 Vorpruefung (06.10.2026): NUR Datenlage und Zustaende des Klimas (BTC-q wie F3), KEINE Ertraege."""
import os, sqlite3, sys
import numpy as np, pandas as pd
os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
src = open("Basisinfos/Spot_Voranalyse_04_10/k3_gewichten.py", encoding="utf-8").read().split("pb, mb = lade")[0]
g = {"__file__": os.path.abspath("Basisinfos/Spot_Voranalyse_04_10/k3_gewichten.py")}; exec(compile(src, "k3", "exec"), g)
pb, mb = g["lade"]("btc"); q = g["klima"](pb, mb, pd.Timestamp("2013-01-01"))
c = sqlite3.connect("file:data/messdaten.db?mode=ro", uri=True)
for s in ("SOL", "ETH", "BTC"):
    print(s, "messdaten:", c.execute("SELECT MIN(date), MAX(date), COUNT(*) FROM price_history_ohlc WHERE assetklasse='krypto' AND currency='USD' AND symbol=?", (s,)).fetchone())
print("CoinMetrics:", sqlite3.connect("file:data/_spot/coinmetrics.db?mode=ro", uri=True).execute("SELECT asset, MIN(tag), MAX(tag) FROM tag GROUP BY asset").fetchall())
print("\nKlima q (BTC) je Jahr: Maximum, Tage >= 0,80 / 0,90 / 0,95 (ueberhitzt) und <= 0,20 / 0,10 / 0,05 (Zone)")
for j in range(2015, 2027):
    x = q[str(j)].dropna()
    print("  %d  max %.2f | ueberhitzt %3d / %3d / %3d | Zone %3d / %3d / %3d" % (j, x.max(), (x >= .8).sum(), (x >= .9).sum(), (x >= .95).sum(), (x <= .2).sum(), (x <= .1).sum(), (x <= .05).sum()))
