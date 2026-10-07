"""Gegenprobe E-1 (Schritt7 §23.23) - eigener Rechenweg, nur lesend, keine Aufrufe.

    python Basisinfos/Rechenkern_02_10/e1_gegenprobe.py

  G1 Kuerzel: an 30 zufaelligen Meldungen (je Art) mit einem ZWEITEN Weg gezogen - alle Woerter aus Titel+Text, die es in unserer
     Asset-Welt gibt - der Lader muss eine TEILMENGE davon liefern, und bei token_delist/futures_delist genau die Titel-/Kontraktwoerter
  G2 Merkmale: an 400 zufaelligen Einstiegen (unverzerrt_1) die Fenster mit einer eigenen Schleife ueber die Rohtabelle neu gerechnet
  G3 Unterschiede mit - ohne je Menge fuer SCHWER mit numpy aus e1_einstiege.csv gegen den Bericht
  G4 Nullwelt: (a) 200 ZUFALLSmerkmale mit gleicher Zahl je Menge -> Anteil |Unterschied| ueber P95 nahe 5 %; (b) GEPFLANZT: die
     schlechtesten 24-h-Ertraege als Merkmal -> ueber P95
  G5 Plausibilitaet: 12 Ereignis-Einstiege mit Titel und Ausgang (zum Lesen)
"""
import os
import re
import sqlite3
import sys

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
import e1_lade_binance as LB    # noqa: E402
import e1_messung as EM         # noqa: E402

ok = n = 0
BER = open(os.path.join(HIER, "e1_messung.txt"), encoding="utf-8").read()


def pruefe(name, gut, info):
    global ok, n
    n += 1; ok += bool(gut)
    print("%-4s %s  %s" % (name, "gleich" if gut else "ABWEICHUNG", info), flush=True)


W = LB.welt()
c = sqlite3.connect("file:%s?mode=ro" % LB.ABLAGE.replace("\\", "/"), uri=True)
mel = pd.read_sql("SELECT code, titel, art, text FROM meldung WHERE art NOT IN ('sonstiges', 'monitoring_ende')", c)
evt = pd.read_sql("SELECT code, symbol, art, release_ms FROM ereignis", c)
for art_, g in mel.groupby("art"):
    probe = g.sample(min(6, len(g)), random_state=7)
    for r in probe.itertuples():
        lader = set(evt[evt.code == r.code].symbol)
        # KORREKTUR nach dem ersten Lauf: erst die Rohwoerter umformen (PORT3USDT -> PORT3, 1000X -> X), DANN mit der Welt schneiden;
        # auch einbuchstabige Kuerzel (D)
        roh = set(re.findall(r"[A-Z0-9]{1,24}", (r.titel or "") + " " + (r.text or "")))
        woerter = (roh | {LB.basis(w) for w in roh} | {LB.basis(w[:-4]) for w in roh if w.endswith("USDT")}) & W
        teil = lader <= woerter
        genau = True
        if art_ == "token_delist":
            genau = lader == (set(re.findall(r"[A-Z0-9]{2,15}", r.titel.split(" on ")[0])) & W) - LB.QUOTE
        if art_ == "futures_delist":
            genau = lader == ({LB.basis(x) for x in re.findall(r"([A-Z0-9]{2,20})USDT", r.text or "")} & W) - LB.QUOTE
        pruefe("G1", teil and genau, "[%s] %s -> %s" % (art_, r.titel[:70], sorted(lader)[:8]))

E = pd.read_csv(os.path.join(EM.D, "_e1", "e1_einstiege.csv"), sep=";")
x = E[E.menge == "unverzerrt_1"].reset_index(drop=True)
ev = evt.assign(zeit=pd.to_datetime(evt.release_ms, unit="ms"))
probe = x.sample(400, random_state=11)
fehl = 0
for r in probe.itertuples():
    ende = EM.B0 + pd.Timedelta(hours=int(r.stunde) + 1)
    soll = {}
    for a, w in EM.FENSTER.items():
        y = ev[(ev.symbol == r.symbol) & (ev.art == a) & (ev.zeit <= ende) & (ev.zeit > ende - pd.Timedelta(days=w))]
        if a == "monitoring" and len(y):
            z = ev[(ev.symbol == r.symbol) & (ev.art == "monitoring_ende") & (ev.zeit > y.zeit.max()) & (ev.zeit <= ende)]
            soll[a] = z.empty
        else:
            soll[a] = len(y) > 0
    fehl += any(bool(getattr(r, a)) != soll[a] for a in EM.FENSTER) or bool(r.SCHWER) != (soll["token_delist"] or soll["futures_delist"] or soll["monitoring"])
pruefe("G2", fehl == 0, "400 Einstiege, Abweichungen %d · davon mit SCHWER %d" % (fehl, int(probe.SCHWER.sum())))

for m, g in E.groupby("menge"):
    f = g.SCHWER.values.astype(bool)
    if f.sum() < 2:
        continue
    d = np.nanmean(g.ertrag24.values[f]) - np.nanmean(g.ertrag24.values[~f])
    mm = re.search(r"SCHWER  \(HAUPT\).*?\n(?:.*\n)*?\s+%s\s+mit\s+\d+ \(Assets\s+\d+\) · 24 h ([-+][\d.]+) %%" % m, BER)
    pruefe("G3", mm is not None and abs(float(mm.group(1)) - 100 * d) < 0.006, "%s SCHWER 24 h numpy %+.3f %% Bericht %s" % (m, 100 * d, mm.group(1) if mm else "-"))

g = E[E.menge == "unverzerrt_1"].copy()
g["tag"] = [str(EM.B0 + pd.Timedelta(hours=int(h)))[:10] for h in g.stunde]
k = int(g.SCHWER.sum())
rng = np.random.default_rng(3)
tr = 0
for i in range(200):
    f = np.zeros(len(g), bool); f[rng.choice(len(g), size=max(k, 30), replace=False)] = True
    dE = EM.diff(g, f)[0]
    tr += abs(dE) > np.nanpercentile(np.abs(EM.null(g, f, nz=200)), 95)
pruefe("G4a", 0.02 <= tr / 200 <= 0.10, "Zufallsmerkmale (je %d Einstiege) ueber P95: %d von 200 (%.1f %%, Soll ~5 %%)" % (max(k, 30), tr, 100 * tr / 200))
f = np.zeros(len(g), bool)
f[np.argsort(g.ertrag24.fillna(0).values)[:max(k, 30)]] = True
dE = EM.diff(g, f)[0]
p95 = np.nanpercentile(np.abs(EM.null(g, f, nz=200)), 95)
pruefe("G4b", abs(dE) > p95, "gepflanzt (schlechteste Ertraege): %+.2f %% gegen P95 %.2f %%" % (100 * dE, 100 * p95))

print("\nG5 Plausibilitaet - 12 Einstiege mit SCHWER (unverzerrt_1):")
z = g[g.SCHWER].sample(min(12, int(g.SCHWER.sum())), random_state=5)
for r in z.itertuples():
    t = EM.B0 + pd.Timedelta(hours=int(r.stunde))
    y = ev[(ev.symbol == r.symbol) & (ev.zeit <= t + pd.Timedelta(hours=1))].sort_values("zeit").tail(1)
    titel = mel.set_index("code").titel.get(y.code.iloc[0], "?") if len(y) else "?"
    print("   %-8s %s · 24 h %+6.1f %% · Meldung %s: %s" % (r.symbol, str(t)[:16], 100 * r.ertrag24, str(y.zeit.iloc[0])[:16] if len(y) else "-", titel[:80]))
print("\n%d von %d gleich" % (ok, n))
