"""O47: CMC-Wochenaufnahmen laden (18.10.2026, Spot §59.4) - NUR Abruf und Ablage, keine Rechnung.

    python Basisinfos/Spot_Voranalyse_04_10/o47_cmc_abruf.py

Quelle: coinmarketcap.com/historical/JJJJMMTT/ (oeffentlich, frei), eingebettete Rangliste (Top 200 nach Marktwert) mit Kurs, Marktwert,
Umsatz 24 h. Jeden Sonntag von 2016-07-03 bis zum letzten Sonntag; schon geladene Sonntage werden uebersprungen (wiederaufnehmbar).
Ablage data/_spot/o47_cm.db, Tabelle cmc_woche. 2 s Pause je Seite.
"""
import json
import os
import re
import sqlite3
import sys
import time
from datetime import date, timedelta

import requests

os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass
H = {"User-Agent": "Mozilla/5.0 (TradingInfoTool Forschung)"}
c = sqlite3.connect(os.path.join("data", "_spot", "o47_cm.db"))
c.execute("CREATE TABLE IF NOT EXISTS cmc_woche (stichtag TEXT, id INTEGER, rang INTEGER, symbol TEXT, slug TEXT, name TEXT, preis REAL, "
          "cap REAL, umsatz REAL, PRIMARY KEY (stichtag, id))")
c.execute("CREATE TABLE IF NOT EXISTS cmc_woche_lauf (stichtag TEXT PRIMARY KEY, n INTEGER, geladen TEXT)")
da = {r[0] for r in c.execute("SELECT stichtag FROM cmc_woche_lauf")}
t, ende, neu, fehl = date(2016, 7, 3), date.today() - timedelta(days=1), 0, []
while t <= ende:
    s = t.isoformat()
    if s not in da:
        for v in range(4):
            try:
                txt = requests.get("https://coinmarketcap.com/historical/%s/" % s.replace("-", ""), headers=H, timeout=90).text
                m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', txt, re.S)
                L = json.loads(json.loads(m.group(1))["props"]["initialState"])["cryptocurrency"]["listingHistorical"]["data"]
                rows = [(s, int(x["id"]), int(x["cmcRank"]), x["symbol"], x["slug"], x["name"], x["quote"]["USD"].get("price"),
                         x["quote"]["USD"].get("marketCap"), x["quote"]["USD"].get("volume24h")) for x in L]
                c.executemany("INSERT OR REPLACE INTO cmc_woche VALUES (?,?,?,?,?,?,?,?,?)", rows)
                c.execute("INSERT OR REPLACE INTO cmc_woche_lauf VALUES (?,?,?)", (s, len(rows), time.strftime("%Y-%m-%d %H:%M")))
                c.commit()
                neu += 1
                break
            except Exception as exc:  # noqa: BLE001
                if v == 3:
                    fehl.append((s, str(exc)[:80]))
                time.sleep(10 * (v + 1))
        time.sleep(2)
        if neu % 50 == 0 and neu:
            print("  %s geladen (%d neu)" % (s, neu), flush=True)
    t += timedelta(days=7)
n = c.execute("SELECT COUNT(*), MIN(stichtag), MAX(stichtag), MIN(n), MAX(n) FROM cmc_woche_lauf").fetchone()
print("CMC-Wochenaufnahmen: %d Sonntage %s..%s, je %d-%d Coins · neu %d · Fehler %d %s" % (n[0], n[1], n[2], n[3], n[4], neu, len(fehl), fehl[:5]))
c.close()
