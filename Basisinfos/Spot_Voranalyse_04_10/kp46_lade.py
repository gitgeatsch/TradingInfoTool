"""Spot §45.5 - Lader fuer U1 (Stablecoins je Kette, DefiLlama) und U4 (MVRV je Altcoin, CoinMetrics Community). Frei, ohne Schluessel.
Schreibt NUR nach data/_spot/stablecoins_kette.db und data/_spot/coinmetrics_alt.db (Wegwerf-/Forschungsdateien, nicht die Produktion).

    python Basisinfos/Spot_Voranalyse_04_10/kp46_lade.py

Zuordnung U1: DefiLlama /v2/chains (gecko_id) gegen strukturprofil.cg_id; nur Ketten, die in stablecoinchains vorkommen.
Zuordnung U4: CoinMetrics-Katalog (Asset-Kuerzel) gegen die Krypto-Symbole der Messbasis, nur Assets mit CapMVRVCur.
"""
import os
import sqlite3
import time

import pandas as pd
import requests

os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
UA = {"User-Agent": "TradingInfoTool-Forschung/1.0 (privat)"}
assert "tradinginfotool" not in "data/_spot/stablecoins_kette.db data/_spot/coinmetrics_alt.db"


def hole(url, versuche=4):
    for i in range(versuche):
        r = requests.get(url, headers=UA, timeout=60)
        if r.status_code == 200:
            return r.json()
        time.sleep(3 * (i + 1))
    raise RuntimeError("%s -> %s" % (url, r.status_code))


md = sqlite3.connect("file:data/messdaten.db?mode=ro", uri=True)
syms = {s for (s,) in md.execute("SELECT DISTINCT symbol FROM price_history_ohlc WHERE assetklasse='krypto' AND currency='USD'")}
pr = pd.read_sql("SELECT symbol, cg_id FROM profil", sqlite3.connect("file:data/_spot/strukturprofil.db?mode=ro", uri=True))
cg = {r.cg_id: r.symbol for r in pr.itertuples() if isinstance(r.cg_id, str)}

# U1
stc = {c["name"] for c in hole("https://stablecoins.llama.fi/stablecoinchains")}
ketten = {cg[c["gecko_id"]]: c["name"] for c in hole("https://api.llama.fi/v2/chains") if c.get("gecko_id") in cg and c["name"] in stc}
o = sqlite3.connect("data/_spot/stablecoins_kette.db")
o.execute("CREATE TABLE IF NOT EXISTS bestand (symbol TEXT, kette TEXT, datum TEXT, usd REAL, PRIMARY KEY (symbol, datum))")
o.execute("DELETE FROM bestand")
n = 0
for s, k in sorted(ketten.items()):
    h = hole("https://stablecoins.llama.fi/stablecoincharts/%s" % requests.utils.quote(k))
    z = [(s, k, pd.to_datetime(int(x["date"]), unit="s").strftime("%Y-%m-%d"), float((x.get("totalCirculatingUSD") or {}).get("peggedUSD") or 0)) for x in h]
    o.executemany("INSERT OR REPLACE INTO bestand VALUES (?,?,?,?)", z)
    n += len(z)
    time.sleep(0.4)
o.commit()
print("U1 Stablecoins je Kette: %d Kettentoken, %d Tageswerte -> data/_spot/stablecoins_kette.db" % (len(ketten), n))

# U4
cat = hole("https://community-api.coinmetrics.io/v4/catalog-v2/asset-metrics?pretty=false&page_size=10000")["data"]
assets = sorted(z["asset"] for z in cat if z["asset"].upper() in syms and z["asset"].upper() not in ("BTC", "ETH", "SOL")
                and any(m["metric"] == "CapMVRVCur" for m in z.get("metrics", [])))
o = sqlite3.connect("data/_spot/coinmetrics_alt.db")
o.execute("CREATE TABLE IF NOT EXISTS mvrv (symbol TEXT, datum TEXT, wert REAL, PRIMARY KEY (symbol, datum))")
o.execute("DELETE FROM mvrv")
n = 0
for a in assets:
    url = ("https://community-api.coinmetrics.io/v4/timeseries/asset-metrics?assets=%s&metrics=CapMVRVCur&frequency=1d&start_time=2021-06-01"
           "&page_size=10000&pretty=false" % a)
    while url:
        j = hole(url)
        z = [(a.upper(), x["time"][:10], float(x["CapMVRVCur"])) for x in j.get("data", []) if x.get("CapMVRVCur") not in (None, "")]
        o.executemany("INSERT OR REPLACE INTO mvrv VALUES (?,?,?)", z)
        n += len(z)
        url = j.get("next_page_url")
    time.sleep(0.6)
o.commit()
print("U4 MVRV je Altcoin: %d Assets, %d Tageswerte -> data/_spot/coinmetrics_alt.db" % (len(assets), n))
