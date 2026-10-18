"""Gegenprobe P64 (18.10.2026) - zweite Wege fuer die tragenden Aussagen der L-C-Voranalyse. Nur lesend.

    python Basisinfos/Rechenkern_02_10/p64_gegenprobe.py

G1 Wayback CoinDesk: Tage mit Aufnahme 2025-26 OHNE collapse gezaehlt (alle Aufnahmen, Tage selbst gebildet) - gleich p64 (478)?
G2 Kein Vorgriff: in 6 ueber 2025-26 verteilten Aufnahmen liegt JEDES pubDate vor dem Aufnahmezeitpunkt (Wayback-Zeitstempel, UTC)
G3 Abdeckungsluecken: groesste Luecke zwischen zwei CoinDesk-Aufnahmetagen, und wie viele Stunden eine Aufnahme zurueckreicht (Median)
G4 Binance 7 T vor dem Einstieg auf zweitem Weg (merge_asof je Symbol) - gleich p64 (bestand 176)?
G5 T0 auf zweitem Weg: Tief binnen 24 h <= -10 % (bestand) aus dem Minimum der Tiefs per pandas-rolling - gleich p64 (319)?
"""
import os
import re
import sqlite3
import sys
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import numpy as np
import pandas as pd
import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p64_lc_voranalyse as P  # noqa: E402  (nur Kursreihe und Konstanten)

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass
ok = []


def pruefe(name, bed, info=""):
    ok.append(bool(bed))
    print("  %s  %s%s" % ("OK  " if bed else "FEHL", name, ("  (%s)" % info) if info else ""))


print("P64 GEGENPROBE\n")
url = "coindesk.com/arc/outboundfeeds/rss/"
FEHLT = []
rows = []                                                         # monatsweise: eine Gesamtabfrage stiess an die Obergrenze 20.000
for mon in pd.date_range("2025-01-01", "2026-10-01", freq="MS"):
    for v in range(6):                                            # das Archiv drosselt (18.10.: Verbindung abgewiesen) - warten, nie still auslassen
        try:
            r = requests.get("https://web.archive.org/cdx/search/cdx", params={"url": url, "from": mon.strftime("%Y%m"), "to": mon.strftime("%Y%m"),
                                                                               "output": "json", "filter": "statuscode:200", "fl": "urlkey,timestamp",
                                                                               "limit": 20000}, headers=P.H, timeout=180)
            rows += r.json()[1:]
            break
        except Exception:  # noqa: BLE001
            if v == 5:
                FEHLT.append(mon.strftime("%Y-%m"))
            time.sleep(30)
    time.sleep(5)
tage = sorted({x[1][:8] for x in rows})
pruefe("G1 CoinDesk-Aufnahmetage ohne collapse gleich p64 (478), kein Monat ausgefallen", len(tage) == 478 and not FEHLT, "%d Aufnahmen an %d Tagen, ausgefallene Monate %s" % (len(rows), len(tage), FEHLT or "keine"))
idx = np.linspace(0, len(rows) - 1, 6).astype(int)
spannen, vorgriff, n_items = [], 0, 0
for k in idx:
    ts = rows[k][1]
    time.sleep(2)
    t = ""
    for v in range(6):
        try:
            t = requests.get("https://web.archive.org/web/%sid_/https://%s" % (ts, url), headers=P.H, timeout=120).text
            break
        except Exception:  # noqa: BLE001
            time.sleep(30)
    auf = datetime.strptime(ts, "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
    pubs = [parsedate_to_datetime(p) for p in re.findall(r"<pubDate>(.*?)</pubDate>", t)]
    n_items += len(pubs)
    vorgriff += sum(p > auf for p in pubs)
    if pubs:
        spannen.append((auf - min(pubs)).total_seconds() / 3600)
pruefe("G2 kein pubDate nach dem Aufnahmezeitpunkt (6 Aufnahmen)", vorgriff == 0 and n_items > 0, "%d Meldungen, nach der Aufnahme %d" % (n_items, vorgriff))
d = pd.to_datetime(pd.Series(tage), format="%Y%m%d")
luecke = d.diff().dt.days.max()
print("  G3 groesste Luecke zwischen zwei Aufnahmetagen: %d T (Auskunft) · eine Aufnahme reicht im Median %.0f h zurueck · Tage mit Luecke > 2 T: %d" % (
    luecke, float(np.median(spannen)) if spannen else float("nan"), int((d.diff().dt.days > 2).sum())))
ok.append(True)
c = sqlite3.connect("file:data/_e1/binance_ankuendigungen.db?mode=ro", uri=True)
ev = pd.read_sql("SELECT symbol, release_ms FROM ereignis", c)
c.close()
ev["zeit"] = pd.to_datetime(ev.release_ms, unit="ms")
ev = ev[ev.zeit >= "2025-01-01"].sort_values("zeit")
E = pd.read_csv(os.path.join("data", "_vergleich", "kern48jbz_einstiege_bestand.csv"), sep=";")
E = E[E.jahr >= 2025].copy()
E["tag"] = (P.B0 + pd.to_timedelta(E.stunde, unit="h")).dt.normalize()
n7, n_alle, tief = 0, 0, 0
for s, g in E.groupby("symbol"):
    x = P.reihe(s)
    if x is None:
        continue
    a, L, C = x
    i = g.stunde.to_numpy().astype(int) - a
    gut = (i >= 0) & (i + 24 < len(C))
    i = i[gut]
    gg = g[gut]
    cl = C[i]
    lo = pd.Series(L).rolling(24).min().shift(-24).to_numpy()[i]     # Minimum der Tiefs in den Stunden i+1 .. i+24
    e24 = C[i + 24]
    fein = np.isfinite(cl) & np.isfinite(lo) & np.isfinite(e24)
    n_alle += int(fein.sum())
    tief += int(((lo / cl - 1) <= -0.10)[fein].sum())
    es = ev[ev.symbol == s][["zeit"]].rename(columns={"zeit": "ez"}).astype({"ez": "datetime64[ns]"})
    if len(es):
        m = pd.merge_asof(gg[fein].sort_values("tag")[["tag"]].astype({"tag": "datetime64[ns]"}), es.sort_values("ez"), left_on="tag", right_on="ez", direction="backward")
        n7 += int(((m.tag - m.ez) < pd.Timedelta(days=7)).sum())
pruefe("G4 Binance 7 T davor (merge_asof) gleich p64 (176)", n7 == 176, "%d von %d" % (n7, n_alle))
pruefe("G5 Tief 24 h <= -10 % (rolling) gleich p64 (319 von 8408)", tief == 319 and n_alle == 8408, "%d von %d" % (tief, n_alle))
print("\n%d Pruefungen, %s" % (len(ok), "ALLE BESTANDEN" if all(ok) else "%d FEHLGESCHLAGEN" % ok.count(False)))
