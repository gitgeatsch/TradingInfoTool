"""Gegenprobe O29 (Schritt7 §23.28): rechnet der BETRIEB (agent/binance_ankuendigungen) dieselben Merkmale wie die MESSUNG E-1?

    python Basisinfos/Rechenkern_02_10/e1_betrieb_gegenprobe.py

  G1 Art und Kuerzel: fuer ALLE 2.008 Meldungen des E-1-Archivs - Art aus dem Titel und die zugeordneten Assets gleich der E-1-Ablage
  G2 Fenster: fuer ALLE Einstiege der vier E-1-Mengen (e1_einstiege.csv) die Arten im Fenster gleich den E-1-Merkmalen. Erwartete und
     ausgewiesene Abweichung: Monitoring nach einer 'Kennzeichen entfernt'-Meldung (im Betrieb erkannt, in E-1 griff das Ende nie)
"""
import os
import sqlite3
import sys
import tempfile
from datetime import timedelta

import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(os.path.dirname(HIER))
os.chdir(PROJ)
sys.path.insert(0, PROJ)
sys.path.insert(0, HIER)
import agent.binance_ankuendigungen as BA     # noqa: E402
import e1_messung as EM                        # noqa: E402

E1 = os.path.join(PROJ, "data", "_e1", "binance_ankuendigungen.db")
c1 = sqlite3.connect("file:%s?mode=ro" % E1.replace("\\", "/"), uri=True)
mel = c1.execute("SELECT code, katalog, titel, release_ms, art, text FROM meldung").fetchall()
ev = {}
for code, sym in c1.execute("SELECT code, symbol FROM ereignis"):
    ev.setdefault(code, set()).add(sym)
W = BA.welt(os.path.join(PROJ, "data"))
art_ab = [m[2][:70] for m in mel if BA.art(m[2], m[1]) != m[4]]
kz_ab = [(m[2][:60], sorted(BA.kuerzel(m[4], m[2], m[5] or "", W) ^ ev.get(m[0], set()))[:6]) for m in mel
         if BA.kuerzel(m[4], m[2], m[5] or "", W) != ev.get(m[0], set())]
ok = n = 0


def pruefe(name, gut, info):
    global ok, n
    n += 1; ok += bool(gut)
    print("%-3s %s  %s" % (name, "gleich" if gut else "ABWEICHUNG", info), flush=True)


pruefe("G1", not art_ab, "Art: %d Meldungen, abweichend %d %s" % (len(mel), len(art_ab), art_ab[:3]))
pruefe("G1", not kz_ab, "Kuerzel: abweichend %d %s" % (len(kz_ab), kz_ab[:3]))

with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as d:
    c = BA.oeffne(d)
    c.executemany("INSERT INTO ankuendigung VALUES (?,?,?,?,?,?,?)", [(m[0], m[1], m[2], m[3], m[4], m[5], "") for m in mel])
    c.executemany("INSERT INTO ankuendigung_ereignis VALUES (?,?,?,?)",
                  [(code, a, s, ms) for (code, a, s, ms) in c1.execute("SELECT code, art, symbol, release_ms FROM ereignis")])
    c.commit()
    E = pd.read_csv(os.path.join(PROJ, "data", "_e1", "e1_einstiege.csv"), sep=";")
    arten = list(EM.FENSTER)
    ab, ab_mon_ende, gesamt = [], 0, 0
    ende_titel = [t for (t,) in c.execute("SELECT titel FROM ankuendigung WHERE art='monitoring_ende'")]
    for r in E.itertuples():
        ende = EM.B0 + timedelta(hours=int(r.stunde) + 1)
        bet = {x["art"] for x in BA.aktive(c, r.symbol, ende)}
        mes = {a for a in arten if bool(getattr(r, a))}
        gesamt += 1
        if bet != mes:
            if mes - bet == {"monitoring"} and not (bet - mes) and any(r.symbol in t for t in ende_titel):
                ab_mon_ende += 1
            else:
                ab.append((r.menge, r.symbol, int(r.stunde), sorted(mes), sorted(bet)))
    c.close()
pruefe("G2", not ab, "Fenster an %d Einstiegen: abweichend %d %s" % (gesamt, len(ab), ab[:3]))
print("    Auskunft: %d Einstiege mit Monitoring NACH einer 'Kennzeichen entfernt'-Meldung - im Betrieb richtig ohne Monitoring, in E-1 "
      "noch mitgezaehlt (E-1 ueberzaehlte dort)" % ab_mon_ende)
print("\n%d von %d gleich" % (ok, n))
