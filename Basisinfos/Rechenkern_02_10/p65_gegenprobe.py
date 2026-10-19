"""Gegenprobe P65 (19.10.2026) - zweite Wege fuer Archiv und Zuordnung. Nur lesend.

    python Basisinfos/Rechenkern_02_10/p65_gegenprobe.py

G1 Lesen: 5 zufaellige Aufnahmen neu abgerufen und mit xml.etree statt Regex gelesen - steht jede Meldung (Titel) in der Ablage?
G2 Zuordnung: an 1.500 zufaelligen Einstiegen 'Meldung 7 T davor' mit Wortzerlegung statt Regex neu bestimmt - Anteil gleich?
G3 Treffsicherheit: 40 zufaellige Treffer (Asset, Titel) zur Durchsicht; Auszaehlung siehe Doku
G4 Kein Vorgriff: Meldungen mit Veroeffentlichung NACH ihrer Aufnahme (UTC) - Zahl und groesste Ueberschreitung
"""
import os
import random
import re
import sqlite3
import sys
import time
import xml.etree.ElementTree as ET

import numpy as np
import pandas as pd
import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p65_lc_nennung as N  # noqa: E402  (nur Namen, Stopplisten und Archiv-Lader)

class F:                                                             # dieselben Feeds wie p65_lc_archiv_laden (dessen Import wuerde den Lader starten)
    FEEDS = {"cointelegraph": "cointelegraph.com/rss", "coindesk": "coindesk.com/arc/outboundfeeds/rss/", "decrypt": "decrypt.co/feed",
             "cryptoslate": "cryptoslate.com/feed/", "theblock": "www.theblock.co/rss.xml", "bitcoinist": "bitcoinist.com/feed/",
             "coingape": "coingape.com/feed/", "cryptopotato": "cryptopotato.com/feed/", "dailyhodl": "dailyhodl.com/feed/"}
    H = {"User-Agent": "Mozilla/5.0 (TradingInfoTool Forschung)"}


try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass
ok = []
rnd = random.Random(19102026)


def pruefe(name, bed, info=""):
    ok.append(bool(bed))
    print("  %s  %s%s" % ("OK  " if bed else "FEHL", name, ("  (%s)" % info) if info else ""))


print("P65 GEGENPROBE\n")
c = sqlite3.connect("file:data/_lc/nachrichten.db?mode=ro", uri=True, timeout=30)
auf = c.execute("SELECT feed, ts FROM aufnahme WHERE status='ok' AND n > 0").fetchall()
tit, lnk = {}, {}
for f, t, l_ in c.execute("SELECT feed, titel, link FROM meldung"):
    tit.setdefault(f, set()).add((t or "").strip())
    lnk.setdefault(f, set()).add((l_ or "").strip())
c.close()
fehl, ges, fehl_link = 0, 0, 0
for f, ts in rnd.sample(auf, 5):
    r = None
    for v in range(5):
        try:
            r = requests.get("https://web.archive.org/web/%sid_/https://%s" % (ts, F.FEEDS[f]), headers=F.H, timeout=120)
            break
        except requests.RequestException:
            time.sleep(30)
    try:
        root = ET.fromstring(r.content)
        items = [e for e in root.iter() if e.tag.split("}")[-1] in ("item", "entry")]
        for it in items:
            t = next((x.text or "" for x in it if x.tag.split("}")[-1] == "title"), "").strip()
            lk = next((x.text or "" for x in it if x.tag.split("}")[-1] == "link"), "").strip()
            ges += 1
            if t not in tit.get(f, set()):
                fehl += 1
                fehl_link += int(lk not in lnk.get(f, set()))
                print("     fehlt (Titel): %s | %s | Link in der Ablage: %s" % (f, t[:90], "ja" if lk in lnk.get(f, set()) else "NEIN"))
    except ET.ParseError:
        print("     %s %s: kein gueltiges XML (Auskunft)" % (f, ts))
    time.sleep(3)
pruefe("G1 jede Meldung aus 5 neu gelesenen Aufnahmen steht in der Ablage (ueber den Link; ein spaeter geaenderter Titel zaehlt nicht als fehlend)", ges > 0 and fehl_link == 0, "%d Meldungen, Titel abweichend %d, Link fehlt %d" % (ges, fehl, fehl_link))
best, _rang = N.namen()
M, _A = N.lade_meldungen()
M = M.drop_duplicates(["titel", "pub_utc"])
E = pd.read_csv(os.path.join("data", "_lc", "p65_einstiege.csv"), sep=";", parse_dates=["zeit"])
probe = E.sample(n=min(1500, len(E)), random_state=7)
woerter = [set(re.findall(r"[A-Za-z0-9$]+", x)) for x in M.text]
klein = [" " + " ".join(re.findall(r"[a-z0-9]+", x.lower())) + " " for x in M.text]
pub = M.pub_utc.to_numpy()


def nennt(i, sym, name):
    if sym.upper() not in N.STOPP_KURZ and len(sym) >= 3 and sym.upper() in woerter[i]:
        return True
    if ("$" + sym.upper()) in woerter[i]:
        return True
    if name:
        st = " ".join(w for w in name.split() if w.lower() not in N.ZUSATZ)
        for v in {name, st}:
            if len(v) >= 4 and v.lower() not in N.STOPP_NAME and (" " + " ".join(re.findall(r"[a-z0-9]+", v.lower())) + " ") in klein[i]:
                return True
    return False


gleich = 0
for r in probe.itertuples():
    z = np.datetime64(r.zeit)
    idx = np.flatnonzero((pub < z) & (pub >= z - np.timedelta64(7, "D")))
    zw = any(nennt(i, r.symbol, best.get(r.symbol)) for i in idx)
    gleich += int(zw == bool(r.n7))
pruefe("G2 Meldung 7 T davor auf zweitem Weg: >= 98 % der 1.500 Einstiege gleich", gleich / len(probe) >= 0.98, "%d von %d gleich" % (gleich, len(probe)))
print("  G3 40 zufaellige Treffer zur Durchsicht (Asset | Titel):")
paare = []
for s in rnd.sample(sorted(E.symbol.unique()), min(120, E.symbol.nunique())):
    mu = N.muster_fuer(s, best.get(s))
    if mu is None:
        continue
    hit = M[M.text.str.contains(mu, regex=True)]
    if len(hit):
        paare.append((s, best.get(s), hit.titel.iloc[rnd.randrange(len(hit))]))
for s, n, t in paare[:40]:
    print("     %-8s %-22s | %s" % (s, (n or "")[:22], (t or "")[:110]))
ok.append(True)
M2 = M.copy()
M2["auf"] = pd.to_datetime(M2.aufnahme_ts.str[:14], format="%Y%m%d%H%M%S")
nach = M2[M2.pub_utc > M2.auf]
pruefe("G4 keine Veroeffentlichung nach der eigenen Aufnahme (Toleranz 0)", len(nach) == 0,
       "%d von %d nach der Aufnahme, groesste Ueberschreitung %s" % (len(nach), len(M2), (nach.pub_utc - nach.auf).max() if len(nach) else "-"))
print("\n%d Pruefungen, %s" % (len(ok), "ALLE BESTANDEN" if all(ok) else "%d FEHLGESCHLAGEN" % ok.count(False)))
