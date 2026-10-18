"""O47 Gegenprobe der Voranalyse (18.10.2026, Spot §59) - nur lesend, Abrufe frei. Rechnet auf dem Holdout weder Ampel noch Wahrheit.

    python Basisinfos/Spot_Voranalyse_04_10/o47_gegenprobe.py

G1 Stablecoins auf einem DRITTEN Weg: die USDT-Einzelreihe von DefiLlama (stablecoin/1) gegen CoinMetrics usdt - ist die Luecke der
   Summenreihe 2019/20 eine fehlende Kette (Omni) oder liegt CoinMetrics zu hoch?
G2 B3 je Jahr (Kalibrierungszeitraum): an wie vielen Tagen 91 T > 10 % nach CoinMetrics-Summe gegen DefiLlama-Summe
G3 Wochenaufnahmen CMC: an sechs Stichtagen 2016-2023 vorhanden, je 200 Coins mit Kurs, Marktwert und Umsatz
"""
import json
import os
import re
import sqlite3
import sys
import time

import pandas as pd
import requests

os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass
STABLE_CM = ("usdt", "usdc", "pax", "tusd", "gusd", "busd", "dai", "husd", "usdk", "sai")
c = sqlite3.connect("file:data/_spot/o47_cm.db?mode=ro", uri=True)
print("O47 GEGENPROBE der Voranalyse (Holdout nicht beruehrt)\n")

j = requests.get("https://stablecoins.llama.fi/stablecoin/1", timeout=120).json()
dl_u = pd.Series({pd.Timestamp(int(x["date"]), unit="s").normalize(): x.get("circulating", {}).get("peggedUSD") for x in j.get("tokens") or []}).sort_index().dropna()
cm_u = pd.read_sql("SELECT tag, SplyCur FROM tag WHERE asset='usdt'", c, parse_dates=["tag"]).set_index("tag").SplyCur
ketten = {k: pd.Timestamp(int(v["tokens"][0]["date"]), unit="s").date() for k, v in (j.get("chainBalances") or {}).items() if v.get("tokens")}
print("G1 USDT einzeln, DefiLlama ab %s · Ketten frueh erfasst: %s · Omni erfasst: %s" % (
    dl_u.index[0].date(), ", ".join("%s %s" % (k, d) for k, d in sorted(ketten.items(), key=lambda x: x[1])[:4]),
    ketten.get("Omni", "NEIN")))
for t in ("2017-12-01", "2018-06-01", "2019-04-01", "2019-10-01", "2020-04-01", "2020-10-01", "2021-04-01"):
    T = pd.Timestamp(t)
    print("   %s  DefiLlama-USDT %6.2f Mrd · CoinMetrics usdt %6.2f Mrd" % (t, (dl_u.asof(T) if dl_u.index[0] <= T else 0) / 1e9, cm_u.asof(T) / 1e9))

S = pd.read_sql("SELECT asset, tag, SplyCur FROM tag WHERE SplyCur IS NOT NULL AND asset IN (%s)" % ",".join("?" * len(STABLE_CM)), c, params=STABLE_CM,
                parse_dates=["tag"])
cm = S.pivot(index="tag", columns="asset", values="SplyCur").sort_index().asfreq("D").ffill().fillna(0).sum(axis=1)
k = requests.get("https://stablecoins.llama.fi/stablecoincharts/all", timeout=120).json()
dl = pd.Series({pd.Timestamp(int(x["date"]), unit="s").normalize() + pd.Timedelta(days=1): x["totalCirculatingUSD"].get("peggedUSD", 0) for x in k}).sort_index()
g = pd.concat([cm.rename("cm"), dl.rename("dl")], axis=1).dropna()
g = g[g.index >= "2019-01-01"]
d = pd.DataFrame({"cm": g.cm / g.cm.shift(91) - 1 > 0.10, "dl": g.dl / g.dl.shift(91) - 1 > 0.10, "r": g.cm / g.dl})
d = d[d.index >= "2019-04-01"]
print("\nG2 B3 (91 T > 10 %) je Jahr: CoinMetrics-Summe gegen DefiLlama-Summe")
for y, x in d.groupby(d.index.year):
    print("   %d  gleich %5.1f %% · an CM %5.1f %% · an DL %5.1f %% · Verhaeltnis CM/DL Median %.2f" % (
        y, 100 * (x.cm == x.dl).mean(), 100 * x.cm.mean(), 100 * x.dl.mean(), x.r.median()))

print("\nG3 CMC-Wochenaufnahmen")
for s in ("20161002", "20170507", "20170514", "20170521", "20190407", "20230604"):
    t = requests.get("https://coinmarketcap.com/historical/%s/" % s, headers={"User-Agent": "Mozilla/5.0"}, timeout=90).text
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', t, re.S)
    L = json.loads(json.loads(m.group(1))["props"]["initialState"])["cryptocurrency"]["listingHistorical"]["data"]
    print("   %s  %d Coins, mit Umsatz %d, mit Marktwert %d" % (s, len(L), sum(bool(x["quote"]["USD"].get("volume24h")) for x in L),
                                                             sum(bool(x["quote"]["USD"].get("marketCap")) for x in L)))
    time.sleep(2)
c.close()
