"""P65 L-C: Nachrichtenarchiv 2025-26 aus dem Wayback-Archiv der RSS-Feeds laden (19.10.2026, Schritt7 §23.72). Nur Abruf und Ablage.

    python Basisinfos/Rechenkern_02_10/p65_lc_archiv_laden.py

Je Feed die ERSTE Aufnahme jedes Tages (CDX, Status 200), daraus jede Meldung mit Titel, Link, Veroeffentlichungszeit (pubDate, UTC),
Kurzbeschreibung (ohne HTML, 300 Zeichen) und dem Zeitpunkt der Aufnahme, in der sie zuerst stand. Dubletten je Feed ueber guid/Link.
Wiederaufnehmbar (geladene Aufnahmen werden uebersprungen); Fehler werden je Aufnahme vermerkt, nie still ausgelassen.
Ablage data/_lc/nachrichten.db (Forschungsdaten, nie Produktion). 2,5 s Pause je Abruf, bei Abweisung 30 s und bis zu 5 Wiederholungen.
"""
import html
import os
import re
import sqlite3
import sys
import time
from datetime import timezone
from email.utils import parsedate_to_datetime

import pandas as pd
import requests

os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass
FEEDS = {"cointelegraph": "cointelegraph.com/rss", "coindesk": "coindesk.com/arc/outboundfeeds/rss/", "decrypt": "decrypt.co/feed",
         "cryptoslate": "cryptoslate.com/feed/", "theblock": "www.theblock.co/rss.xml", "bitcoinist": "bitcoinist.com/feed/",
         "coingape": "coingape.com/feed/", "cryptopotato": "cryptopotato.com/feed/", "dailyhodl": "dailyhodl.com/feed/"}
H = {"User-Agent": "Mozilla/5.0 (TradingInfoTool Forschung)"}
os.makedirs(os.path.join("data", "_lc"), exist_ok=True)
c = sqlite3.connect(os.path.join("data", "_lc", "nachrichten.db"))
c.execute("CREATE TABLE IF NOT EXISTS aufnahme (feed TEXT, ts TEXT, status TEXT, n INTEGER, PRIMARY KEY (feed, ts))")
c.execute("CREATE TABLE IF NOT EXISTS meldung (feed TEXT, schluessel TEXT, titel TEXT, link TEXT, pub_utc TEXT, beschreibung TEXT, aufnahme_ts TEXT, "
          "PRIMARY KEY (feed, schluessel))")


def hole(url, params=None):
    for v in range(6):
        try:
            r = requests.get(url, params=params, headers=H, timeout=120)
            if r.status_code in (429, 503):
                raise requests.RequestException("Status %s" % r.status_code)
            return r
        except requests.RequestException:
            if v == 5:
                return None
            time.sleep(30)


def text(x):
    x = re.sub(r"<!\[CDATA\[(.*?)\]\]>", r"\1", x or "", flags=re.S)
    return html.unescape(re.sub(r"<[^>]+>", " ", x)).strip()


def feld(item, tag):
    m = re.search(r"<%s[^>]*>(.*?)</%s>" % (tag, tag), item, re.S)
    return text(m.group(1)) if m else ""


gesamt = {}
for name, url in FEEDS.items():
    ts_alle = []
    for mon in pd.date_range("2025-01-01", "2026-10-01", freq="MS"):
        r = hole("https://web.archive.org/cdx/search/cdx", {"url": url, "from": mon.strftime("%Y%m"), "to": mon.strftime("%Y%m"), "output": "json",
                                                            "filter": "statuscode:200", "collapse": "timestamp:8", "fl": "timestamp", "limit": 2000})
        if r is None:
            print("  %s %s: CDX nicht abrufbar - Monat FEHLT" % (name, mon.strftime("%Y-%m")), flush=True)
            c.execute("INSERT OR REPLACE INTO aufnahme VALUES (?,?,?,?)", (name, "CDX" + mon.strftime("%Y%m"), "cdx_fehler", 0))
            continue
        try:
            ts_alle += [x[0] for x in r.json()[1:]]
        except Exception:  # noqa: BLE001
            c.execute("INSERT OR REPLACE INTO aufnahme VALUES (?,?,?,?)", (name, "CDX" + mon.strftime("%Y%m"), "cdx_leer", 0))
        time.sleep(1.5)
    da = {r_[0] for r_ in c.execute("SELECT ts FROM aufnahme WHERE feed=? AND status='ok'", (name,))}
    neu = 0
    for ts in ts_alle:
        if ts in da:
            continue
        r = hole("https://web.archive.org/web/%sid_/https://%s" % (ts, url))
        if r is None or r.status_code != 200:
            c.execute("INSERT OR REPLACE INTO aufnahme VALUES (?,?,?,?)", (name, ts, "fehler %s" % (r.status_code if r is not None else "abgewiesen"), 0))
            c.commit()
            time.sleep(2.5)
            continue
        items = re.findall(r"<item[ >].*?</item>", r.text, re.S) or re.findall(r"<entry[ >].*?</entry>", r.text, re.S)
        rows = []
        for it in items:
            pub = feld(it, "pubDate") or feld(it, "published") or feld(it, "updated")
            try:
                pu = parsedate_to_datetime(pub).astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            except Exception:  # noqa: BLE001
                try:
                    pu = pd.Timestamp(pub).tz_convert("UTC").strftime("%Y-%m-%d %H:%M:%S")
                except Exception:  # noqa: BLE001
                    pu = None
            link = feld(it, "link") or (re.search(r'<link[^>]*href="([^"]+)"', it) or [None, ""])[1]
            schl = feld(it, "guid") or feld(it, "id") or link or feld(it, "title")
            rows.append((name, schl, feld(it, "title"), link, pu, feld(it, "description")[:300], ts))
        c.executemany("INSERT OR IGNORE INTO meldung VALUES (?,?,?,?,?,?,?)", rows)
        c.execute("INSERT OR REPLACE INTO aufnahme VALUES (?,?,?,?)", (name, ts, "ok", len(rows)))
        c.commit()
        neu += 1
        if neu % 50 == 0:
            print("  %s: %d Aufnahmen geladen (zuletzt %s)" % (name, neu, ts[:8]), flush=True)
        time.sleep(2.5)
    z = c.execute("SELECT COUNT(*), SUM(status='ok'), SUM(status!='ok') FROM aufnahme WHERE feed=? AND ts NOT LIKE 'CDX%'", (name,)).fetchone()
    m = c.execute("SELECT COUNT(*), MIN(pub_utc), MAX(pub_utc) FROM meldung WHERE feed=?", (name,)).fetchone()
    print("%-13s Aufnahmen %d (ok %d, fehlgeschlagen %d) · Meldungen %d (%s .. %s)" % (name, z[0], z[1] or 0, z[2] or 0, m[0], m[1], m[2]), flush=True)
c.close()
