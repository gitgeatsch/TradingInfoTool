"""C2 (Spot §38): Binance-Katalog 48 und Upbit-Handelsmeldungen laden - oeffentliche Schnittstellen ohne Schluessel.

    python Basisinfos/Spot_Voranalyse_04_10/c2_lade.py

Ablage am DESKTOP data/_c2/ankuendigungen.db (nicht die Produktion, keine Messbasis). Nur Titel und Zeitpunkt, keine Einzeltexte.
"""
import os
import sqlite3
import time
from datetime import datetime, timezone

import requests

HIER = os.path.dirname(os.path.abspath(__file__))
os.chdir(os.path.dirname(os.path.dirname(HIER)))
ABLAGE = os.path.join("data", "_c2", "ankuendigungen.db")
H = {"User-Agent": "Mozilla/5.0 TradingInfoTool-C2"}


def main():
    os.makedirs(os.path.dirname(ABLAGE), exist_ok=True)
    c = sqlite3.connect(ABLAGE)
    c.execute("CREATE TABLE IF NOT EXISTS binance (code TEXT PRIMARY KEY, titel TEXT, release_ms INTEGER)")
    c.execute("CREATE TABLE IF NOT EXISTS upbit (id INTEGER PRIMARY KEY, titel TEXT, utc TEXT)")
    nb = 0
    for seite in range(1, 101):
        for versuch in range(4):
            try:
                r = requests.get("https://www.binance.com/bapi/composite/v1/public/cms/article/list/query",
                                 params={"type": 1, "catalogId": 48, "pageNo": seite, "pageSize": 50}, headers=H, timeout=30)
                j = r.json()
                kat = j["data"]["catalogs"]
                if j.get("success") and j.get("code") == "000000" and kat == []:
                    arts = []                                   # echtes Ende: Binance meldet es mit LEERER Katalogliste
                else:
                    arts = kat[0]["articles"]
                break
            except Exception:
                time.sleep(5 * (versuch + 1))
        else:
            raise SystemExit("Binance Seite %d nicht ladbar - Abbruch (keine leere Seite vortaeuschen)" % seite)
        if not arts:
            break
        c.executemany("INSERT OR IGNORE INTO binance VALUES (?,?,?)", [(a["code"], a["title"], a["releaseDate"]) for a in arts])
        nb += len(arts)
        time.sleep(1.0)
    nu = 0
    for seite in range(1, 200):
        for versuch in range(4):
            try:
                j = requests.get("https://api-manager.upbit.com/api/v1/announcements",
                                 params={"os": "web", "page": seite, "per_page": 20, "category": "trade"}, headers=H, timeout=30).json()
                no = j["data"]["notices"]
                break
            except Exception:
                time.sleep(5 * (versuch + 1))
        else:
            raise SystemExit("Upbit Seite %d nicht ladbar - Abbruch" % seite)
        if not no:
            break
        z = []
        for x in no:
            t = datetime.fromisoformat(x.get("first_listed_at") or x["listed_at"]).astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            z.append((x["id"], x["title"], t))
        c.executemany("INSERT OR IGNORE INTO upbit VALUES (?,?,?)", z)
        nu += len(no)
        time.sleep(1.0)
    c.commit()
    print("Binance geladen %d (Ablage %d) · Upbit geladen %d (Ablage %d)" % (
        nb, c.execute("select count(*) from binance").fetchone()[0], nu, c.execute("select count(*) from upbit").fetchone()[0]))
    print("Binance %s bis %s · Upbit %s bis %s" % (
        *[datetime.fromtimestamp(x / 1000, timezone.utc).date() for x in c.execute("select min(release_ms), max(release_ms) from binance").fetchone()],
        *c.execute("select min(utc), max(utc) from upbit").fetchone()))


if __name__ == "__main__":
    main()
