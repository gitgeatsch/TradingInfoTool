"""Gegenprobe Atlas T1/T2/T3 (23.10.2026) - zweite Wege, eigener Code.

    python Basisinfos/Rechenkern_02_10/p75_gegenprobe.py

G1 T1 Fear & Greed: Vorlauf-Quote je Haelfte per einfacher Schleife ueber die Wendepunkte = p75?
G2 T1 Fear & Greed: Rang mit anderem Startwert und 2.000 Ziehungen - beide Haelften weiter >= 0,95?
G3 T1 Wendepunkte: Zickzack per eigener Schleife (ohne V.zickzack) - 86 Wenden?
G4 T2 Netto-Liquiditaet: Anteil der Aufwaerts-Tage ohne Ausweitung per eigener Zaehlung = p74 (48 %)?
G5 T3 Nasdaq: Zahl der Baerenmaerkte >= -20 % per cummax-Rueckgang (eigener Weg) = 13, kein laufender (p73: laufender Bullenmarkt)?
   KORREKTUR 23.10.: die erste Fassung erwartete 13 + 1 laufend - p73 meldet einen laufenden BULLENmarkt, also war die Erwartung falsch
"""
import os
import re
import subprocess
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
WURZEL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, WURZEL)
os.chdir(WURZEL)
import p72_historie_voranalyse as V  # noqa: E402  (nur btc())

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass
ok = []


def pruefe(name, bed, info=""):
    ok.append(bool(bed))
    print("  %s  %s%s" % ("OK  " if bed else "FEHL", name, ("  (%s)" % info) if info else ""))


print("ATLAS GEGENPROBE\n")
p = V.btc()["2013-01-01":"2026-10-04"]
wenden, rich, et, ep = [], "auf", p.index[0], p.iloc[0]
for t, v in p.items():
    if rich == "auf":
        if v > ep:
            et, ep = t, v
        elif v <= 0.8 * ep:
            wenden.append((et, "Hoch")); rich, et, ep = "ab", t, v
    else:
        if v < ep:
            et, ep = t, v
        elif v >= 1.25 * ep:
            wenden.append((et, "Tief")); rich, et, ep = "auf", t, v
pruefe("G3 Zickzack eigene Schleife: 86 Wenden", len(wenden) == 86, "%d" % len(wenden))
Z = pd.read_csv(os.path.join("data", "_ra", "p75_zustaende.csv"), index_col=0, parse_dates=True)
fg = Z["Fear & Greed"]
out = subprocess.run([sys.executable, "-X", "utf8", os.path.join("Basisinfos", "Rechenkern_02_10", "p75_atlas_t1_krypto.py")],
                     capture_output=True, text=True, encoding="utf-8").stdout
mo = re.search(r"Fear & Greed\s+VOR\s+(\d+)%/\d+%/[0-9.]+ \(n(\d+)\) \| (\d+)%/\d+%/[0-9.]+ \(n(\d+)\)", out)


def q_einfach(t_liste):
    tr = 0
    for t, k in t_liste:
        ziel = -1.0 if k == "Hoch" else 1.0
        fen = fg[t - pd.Timedelta(days=31):t - pd.Timedelta(days=1)]
        vor = fg.shift(1)[t - pd.Timedelta(days=31):t - pd.Timedelta(days=1)]
        tr += int(((fen == ziel) & (vor != ziel)).any())
    return tr / len(t_liste)


h1 = [(t, k) for t, k in wenden if t.year <= 2019 and pd.notna(fg.get(t))]
h2 = [(t, k) for t, k in wenden if t.year >= 2020 and pd.notna(fg.get(t))]
q1, q2 = q_einfach(h1), q_einfach(h2)
pruefe("G1 F&G Vorlauf-Quote per einfacher Schleife = p75", mo and abs(100 * q1 - int(mo.group(1))) <= 1 and abs(100 * q2 - int(mo.group(3))) <= 1,
       "hier %.0f %% (n%d) / %.0f %% (n%d) · p75 %s" % (100 * q1, len(h1), 100 * q2, len(h2), mo.groups() if mo else "-"))
rng = np.random.default_rng(4242)
raenge = []
for name, liste, a, b in (("2013-19", h1, "2013-01-01", "2019-12-31"), ("2020-26", h2, "2020-01-01", "2026-10-04")):
    tage = fg[a:b].dropna().index
    arten = [k for _, k in liste]
    null = []
    for _ in range(2000):
        zt = rng.choice(tage, len(liste))
        null.append(q_einfach(list(zip(pd.DatetimeIndex(zt), arten))))
    raenge.append(float(np.mean(np.array(null) < (q1 if name == "2013-19" else q2))))
pruefe("G2 F&G Rang anderer Startwert, 2.000 Ziehungen: beide >= 0,95", min(raenge) >= 0.95, "%.3f / %.3f" % tuple(raenge))
import p74_atlas_t2_geld as T2  # noqa: E402
R = T2.lade()
G = T2.geldmasse(R, p.index)
g = G["(ii) Netto-Liquiditaet 26 W"]
auf = pd.Series(False, index=p.index)
for (t1, a1), (t2, a2) in zip(wenden[:-1], wenden[1:]):
    if a1 == "Tief":
        auf[t1:t2] = True
m = g.notna()
anteil = float(((g <= 0) & auf & m).sum() / (auf & m).sum())
pruefe("G4 T2 Netto-Liquiditaet: Aufwaerts-Tage ohne Ausweitung = 48 %", abs(100 * anteil - 48) <= 1, "%.1f %%" % (100 * anteil))
nq = pd.read_csv(os.path.join("data", "_ra", "p73_fred.csv"), parse_dates=["datum"])
nq = nq[nq.reihe == "NASDAQCOM"].set_index("datum").wert
dd = nq / nq.cummax() - 1
zahl, im = 0, False
for v in dd:
    if not im and v <= -0.20:
        im, zahl = True, zahl + 1
    elif im and v == 0:
        im = False
pruefe("G5 T3 Nasdaq-Baerenmaerkte per cummax: 13, keiner laufend", zahl == 13 and not im, "%d (laufend: %s)" % (zahl, im))
print("\n%d Pruefungen, %s" % (len(ok), "ALLE BESTANDEN" if all(ok) else "%d FEHLGESCHLAGEN" % ok.count(False)))
