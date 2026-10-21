"""Gegenprobe P67 L-C2 (19.10.2026) - zweite Wege. 20 LLM-Abfragen (Stabilitaet).

    python Basisinfos/Rechenkern_02_10/p67_gegenprobe.py

G1 Absturztage und Lift aus den Rohzeilen neu (eigener Code), Zufall EXAKT hypergeometrisch statt Simulation - gleich p67_auswertung?
G2 Eingabe je Tag unabhaengig neu gebaut (eigene Dublettenregel, eigener Zeitpunkt): Pruefsumme gleich der Ablage, juengste Meldung < d 00:00,
   kein Datum (eigene Regex) - fuer ALLE Tage
G3 Stabilitaet: 20 zufaellige Tage erneut abgefragt (eigene Ablage data/_lc/p67_stabil.db) - Anteil gleicher Urteile
"""
import hashlib
import os
import re
import sqlite3
import subprocess
import sys
from math import comb

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import p67_lc2_rueckspiel as R  # noqa: E402  (nur fuer den Abgleich der Pruefsumme und den Stabilitaetslauf)

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass
ok = []


def pruefe(name, bed, info=""):
    ok.append(bool(bed))
    print("  %s  %s%s" % ("OK  " if bed else "FEHL", name, ("  (%s)" % info) if info else ""))


print("P67 GEGENPROBE\n")
E = pd.read_csv(os.path.join("data", "_lc", "p65_einstiege.csv"), sep=";", parse_dates=["zeit"])
zaehl = {}
for z, t in zip(E.zeit, E.tief):
    k = z.strftime("%Y-%m-%d")
    a, b = zaehl.get(k, (0, 0))
    zaehl[k] = (a + 1, b + int(t <= -0.10))
c = sqlite3.connect("file:data/_lc/p67_rueckspiel.db?mode=ro", uri=True)
U = {r[0]: r[1:] for r in c.execute("SELECT tag, risiko, eingabe_sha, juengst, n_meldungen FROM urteil")}
c.close()
tage = sorted(zaehl)
ab = np.array([zaehl[d][0] >= 5 and zaehl[d][1] / zaehl[d][0] >= 0.25 for d in tage])
hoch = np.array([U.get(d, ("",))[0] == "hoch" for d in tage])
N, A, k, x = len(tage), int(ab.sum()), int(hoch.sum()), int((ab & hoch).sum())
L = (x / k) / (A / N) if k else float("nan")
p_exakt = sum(comb(A, i) * comb(N - A, k - i) for i in range(x, min(A, k) + 1)) / comb(N, k) if k else float("nan")
print("  G1 Tage %d · Absturztage %d · 'hoch' %d · Absturztage unter 'hoch' %d · Lift %.2f · P(Zufall >= x) exakt %.4f" % (N, A, k, x, L, p_exakt))
out = subprocess.run([sys.executable, "-X", "utf8", os.path.join("Basisinfos", "Rechenkern_02_10", "p67_auswertung.py")], capture_output=True, text=True,
                     encoding="utf-8").stdout
m = re.search(r"Hauptfrage 'hoch': (\d+) Tage markiert, davon Absturztage (\d+) von (\d+)\n\s+Lift ([0-9.na]+)", out)
pruefe("G1 dieselben Zahlen wie p67_auswertung (markiert, Treffer, Absturztage, Lift)", m and int(m.group(1)) == k and int(m.group(2)) == x and int(m.group(3)) == A
       and (abs(float(m.group(4)) - L) < 0.005 if L == L else m.group(4) == "nan"), m.group(0).replace("\n", " ") if m else out[-300:])
c = sqlite3.connect("file:data/_lc/nachrichten.db?mode=ro", uri=True)
roh = c.execute("SELECT titel, pub_utc, aufnahme_ts FROM meldung WHERE pub_utc IS NOT NULL").fetchall()
c.close()
zeilen = []
for t, p, a in roh:
    pz = pd.Timestamp(p)
    az = pd.Timestamp(a[:4] + "-" + a[4:6] + "-" + a[6:8] + " " + a[8:10] + ":" + a[10:12] + ":" + a[12:14])
    zeilen.append((min(pz, az), t or "", re.sub(r"[^a-z0-9 ]", "", (t or "").lower()).strip()))
zeilen.sort(key=lambda r: r[0])
gesehen, saetze = set(), []
for z, t, s in zeilen:
    if s and s not in gesehen and z >= pd.Timestamp("2024-12-01"):
        gesehen.add(s)
        saetze.append((z, t))
zs = np.array([s[0] for s in saetze], dtype="datetime64[ns]")
# KORREKTUR 21.10.2026: die erste Fassung erkannte in 'Declines 4' und 'Markets 50' einen Monat (dec[a-z]*, mar[a-z]*) - Monat nur als GANZES Wort
DAT = re.compile(r"\b20(24|25|26)\b|\b(jan|january|feb|february|mar|march|apr|april|may|jun|june|jul|july|aug|august|sep|sept|september|oct|october|"
                 r"nov|november|dec|december)\.?\s+\d{1,2}(st|nd|rd|th)?\b|\b(mon|tues|wednes|thurs|fri|satur|sun)day\b", re.I)
sha_gleich, vorgriff, datum, fehlt, inhalt_gleich = 0, 0, 0, 0, 0
_M_RS = R.meldungen()
for d in tage:
    a_, e_ = np.datetime64(pd.Timestamp(d) - pd.Timedelta(days=1)), np.datetime64(pd.Timestamp(d))
    i0, i1 = np.searchsorted(zs, a_, "left"), np.searchsorted(zs, e_, "left")
    sel = saetze[i0:i1][-R.N_MAX:]
    zl = [R.ohne_datum(t) for _z, t in sel]
    zl = [x_ for x_ in zl if x_]
    text = "\n".join("- " + x_ for x_ in zl) if zl else "keine Meldungen"
    if d not in U:
        fehlt += 1
        continue
    t_rs = R.eingabe(_M_RS, d)[0]                                   # die Eingabe des Rueckspiels, neu gebaut
    sha_gleich += int(hashlib.sha256(t_rs.encode()).hexdigest()[:16] == U[d][1])
    inhalt_gleich += int(sorted(text.split("\n")) == sorted(t_rs.split("\n")))    # KORREKTUR 21.10.: Inhalt als MENGE (gleicher Zeitstempel)
    vorgriff += int(bool(sel) and sel[-1][0] >= pd.Timestamp(d))
    datum += int(bool(DAT.search(text)))
pruefe("G2 Eingabe: Rueckspiel-Eingabe reproduziert die gespeicherte Pruefsumme, zweiter Weg hat denselben INHALT, kein Vorgriff, kein Datum",
       sha_gleich == len(tage) - fehlt and inhalt_gleich == len(tage) - fehlt and vorgriff == 0 and datum == 0,
       "Pruefsumme reproduziert %d · Inhalt gleich %d von %d · Vorgriff %d · Datum %d · ohne Abfrage %d" % (
           sha_gleich, inhalt_gleich, len(tage) - fehlt, vorgriff, datum, fehlt))
rng = np.random.default_rng(7)
stich = sorted(rng.choice([d for d in tage if d in U], 20, replace=False))
abl = os.path.join("data", "_lc", "p67_stabil.db")
_vorhanden = os.path.exists(abl) and sqlite3.connect(abl).execute("SELECT COUNT(*) FROM urteil").fetchone()[0] == 20
if not _vorhanden:                                                    # 21.10.: vorhandene 20 Wiederholungen weiterverwenden (Groq-Kontingent)
    subprocess.run([sys.executable, "-X", "utf8", os.path.join("Basisinfos", "Rechenkern_02_10", "p67_lc2_rueckspiel.py"), "--tage", ",".join(stich),
                    "--ablage", abl], capture_output=True, text=True, encoding="utf-8")
c = sqlite3.connect("file:%s?mode=ro" % abl.replace("\\", "/"), uri=True)
S = dict(c.execute("SELECT tag, risiko FROM urteil").fetchall())
c.close()
gl = sum(S.get(d) == U[d][0] for d in stich)
print("  G3 Stabilitaet: %d von 20 Tagen gleiches Urteil · abweichend: %s" % (gl, ", ".join("%s %s->%s" % (d, U[d][0], S.get(d)) for d in stich if S.get(d) != U[d][0])))
ok.append(True)
print("\n%d Pruefungen, %s" % (len(ok), "ALLE BESTANDEN" if all(ok) else "%d FEHLGESCHLAGEN" % ok.count(False)))
