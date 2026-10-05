"""Spot K-2 (E-61): BTC- und ETH-Tageswerte aus der CoinMetrics Community API laden (frei, ohne Schluessel, Lizenz CC BY-NC 4.0 - privat).

    python Basisinfos/Spot_Voranalyse_04_10/lade_coinmetrics.py

Schreibt NUR nach data/_spot/coinmetrics.db (Wegwerf- bzw. Messdatei des Spot-Strangs, T-2/T-5) - nie in die Produktion, nie in die
Messbasis. Holt PriceUSD, CapMrktCurUSD, CapMVRVCur, SplyCur ab 2010 fuer btc und eth. Ein zweiter Lauf ersetzt die Tabelle.
"""
import json
import os
import sqlite3
import sys
import time
import urllib.request

os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
ZIEL = os.path.join("data", "_spot", "coinmetrics.db")
METRIKEN = ("PriceUSD", "CapMrktCurUSD", "CapMVRVCur", "SplyCur")
URL = ("https://community-api.coinmetrics.io/v4/timeseries/asset-metrics?assets={a}&metrics={m}&frequency=1d"
       "&start_time=2010-01-01&page_size=10000")


def hole(asset: str) -> list:
    url = URL.format(a=asset, m=",".join(METRIKEN))
    zeilen = []
    while url:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "TradingInfoTool-Spot-K2"}), timeout=60) as r:
            d = json.loads(r.read().decode())
        for z in d.get("data", []):
            zeilen.append((asset, z["time"][:10]) + tuple(float(z[m]) if z.get(m) not in (None, "") else None for m in METRIKEN))
        url = d.get("next_page_url")
        time.sleep(1.0)                              # die Community-API ist gedrosselt - sanft abfragen
    return zeilen


def main() -> int:
    os.makedirs(os.path.dirname(ZIEL), exist_ok=True)
    alle = []
    for a in ("btc", "eth"):
        z = hole(a)
        print("%s: %d Tage, %s bis %s" % (a, len(z), z[0][1] if z else "-", z[-1][1] if z else "-"))
        alle += z
    c = sqlite3.connect(ZIEL)
    c.execute("DROP TABLE IF EXISTS tag")
    c.execute("CREATE TABLE tag (asset TEXT, tag TEXT, %s, PRIMARY KEY (asset, tag))" % ", ".join("%s REAL" % m for m in METRIKEN))
    c.executemany("INSERT INTO tag VALUES (%s)" % ",".join("?" * (2 + len(METRIKEN))), alle)
    c.execute("CREATE TABLE IF NOT EXISTS _herkunft (schluessel TEXT PRIMARY KEY, wert TEXT)")
    c.execute("INSERT OR REPLACE INTO _herkunft VALUES ('quelle', 'CoinMetrics Community API v4 (CC BY-NC 4.0), geladen %s')"
              % time.strftime("%Y-%m-%d %H:%M"))
    c.commit(); c.close()
    print("geschrieben: %s (%d Zeilen)" % (ZIEL, len(alle)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
