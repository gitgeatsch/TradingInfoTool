"""Spot §20: Tages-Marktwert (CapMrktCurUSD) aller bei der CoinMetrics Community API gefuehrten Assets laden (frei, ohne Schluessel, CC BY-NC 4.0 - privat).

    python Basisinfos/Spot_Voranalyse_04_10/lade_altcap.py

Schreibt NUR nach data/_spot/altcap.db (Messdatei des Spot-Strangs) - nie in die Produktion, nie in die Messbasis. Ein zweiter Lauf ersetzt die Tabelle.
"""
import json
import os
import sqlite3
import time
import urllib.request

os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
ZIEL = os.path.join("data", "_spot", "altcap.db")
KOPF = {"User-Agent": "TradingInfoTool/1.0 (Analyse, nicht kommerziell)"}


def hole(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=KOPF), timeout=60) as r:
        return json.loads(r.read().decode())


def main():
    kat = hole("https://community-api.coinmetrics.io/v4/catalog/asset-metrics?metrics=CapMrktCurUSD")["data"][0]
    assets = [f for f in kat["frequencies"] if f["frequency"] == "1d"][0]["assets"]
    zeilen = []
    for a in assets:
        url = ("https://community-api.coinmetrics.io/v4/timeseries/asset-metrics?assets=%s&metrics=CapMrktCurUSD&frequency=1d"
               "&start_time=2010-01-01&page_size=10000" % a)
        n = 0
        while url:
            d = hole(url)
            for z in d.get("data", []):
                if z.get("CapMrktCurUSD") not in (None, ""):
                    zeilen.append((a, z["time"][:10], float(z["CapMrktCurUSD"]))); n += 1
            url = d.get("next_page_url")
            time.sleep(0.7)
        print("%-14s %5d Tage" % (a, n), flush=True)
    os.makedirs(os.path.dirname(ZIEL), exist_ok=True)
    c = sqlite3.connect(ZIEL)
    c.execute("DROP TABLE IF EXISTS cap")
    c.execute("CREATE TABLE cap (asset TEXT, tag TEXT, cap REAL, PRIMARY KEY (asset, tag))")
    c.executemany("INSERT INTO cap VALUES (?,?,?)", zeilen)
    c.execute("CREATE TABLE IF NOT EXISTS _herkunft (schluessel TEXT PRIMARY KEY, wert TEXT)")
    c.execute("INSERT OR REPLACE INTO _herkunft VALUES ('quelle', 'CoinMetrics Community API v4 CapMrktCurUSD (CC BY-NC 4.0), geladen %s')" % time.strftime("%Y-%m-%d %H:%M"))
    c.commit(); c.close()
    print("geschrieben: %s (%d Zeilen, %d Assets)" % (ZIEL, len(zeilen), len(assets)))


if __name__ == "__main__":
    main()
