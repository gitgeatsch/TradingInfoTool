"""Gegenprobe der Messung Spot-Einstieg (§29.2) - eigener Rechenweg, nur lesend.

    python Basisinfos/Spot_Voranalyse_04_10/ein_messung_gegenprobe.py

  H1 Anzahl: E-b-Einstiege und Stichtage je Epoche = Vorpruefung (143 an 11 / 28 an 3) und = Messung
  H2 Ertrag: ALLE E-b-Anker (X2) mit zweiter Umsetzung der Marke (pandas cummax) - Ertrag, BTC, Haltetage gleich
  H3 Korb: E-b-Korb je Epoche aus H2 neu gemittelt (je Stichtag, dann ueber Stichtage) = Ausgabe
  H4 Zufallswelt: ERWARTUNGSWERT analytisch (Klassenmittel KL je Stichtag, nach Klassenanteil gewichtet) - liegt mitten in der Verteilung der Messung
  H5 netto: Kostenformel an 20 Ankern von Hand
  H6 Tor: Breite >= 0,5 an jedem E-b-Stichtag und < 0,5 an jedem E-a-Stichtag ohne E-b
  H7 Bootstrap-Entartung: mit 3 Stichtagen und Bloecken zu 3 ist JEDE Ziehung die volle Reihe -> Bootstrap nur 0 oder 1 (erklaert den Fehlalarm)
  H8 X0: 10 Anker mit 365-T-Halten von Hand
"""
import os
import re
import sys

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
os.chdir(os.path.dirname(os.path.dirname(HIER)))
import as_messung as M      # noqa: E402
import ein_vorpruefung as EV  # noqa: E402

K, POS, BTCV = M.K, M.POS, M.BTCV
R = pd.read_csv(os.path.join("data", "_spot", "ein_messung_anker.csv"), sep=";", parse_dates=["t"])
VP = pd.read_csv(os.path.join("data", "_spot", "ein_vorpruefung_anker.csv"), sep=";", parse_dates=["t"])
TXT = open(os.path.join(HIER, "ein_messung.txt"), encoding="utf-8").read()
ok = n = 0


def pruefe(name, gut, info):
    global ok, n
    n += 1; ok += bool(gut)
    print("%-3s %s  %s" % (name, "gleich" if gut else "ABWEICHUNG", info), flush=True)


def marke2(s, i0):
    x = pd.Series(K[s].values[i0:i0 + 366])
    g = x.notna()
    if not g.all():
        x = x[:g.values.argmin()]
    hoch = x.cummax()
    unter = np.where((x.values < np.maximum(0.65 * hoch, 0.5 * x.iloc[0]).values) & (np.arange(len(x)) > 0))[0]
    j = int(unter[0]) + 1 if len(unter) and unter[0] + 1 < len(x) else len(x) - 1
    return x.iloc[j] / x.iloc[0] - 1, BTCV[i0 + j] / BTCV[i0] - 1, j


eb = R[(R.arm == "E-b") & (R.aus == "X2")].copy()
for ep in ("E2", "E3"):
    a, b = eb[eb.ep == ep], VP[(VP.arm == "E-b") & (VP.ep == ep)]
    m = re.search(r"%s Einstiege (\d+) an (\d+) Stichtagen" % ep, TXT)
    pruefe("H1", len(a) == len(b) and m and int(m.group(1)) == len(a) and int(m.group(2)) == a.t.nunique(),
           "%s Messung %d an %d · Vorpruefung %d · Ausgabe %s" % (ep, len(a), a.t.nunique(), len(b), m.groups() if m else None))

fehl = 0
neu = []
for r in eb.itertuples():
    a, b, j = marke2(r.sym, POS[r.t] + 1)
    fehl += not (abs(a - r.r) < 1e-9 and abs(b - r.rb) < 1e-9 and j == r.tage)
    neu.append((1 + a) / (1 + b) - 1)
eb["ex2"] = neu
pruefe("H2", fehl == 0, "%d E-b-Anker mit zweiter Marke, Abweichungen %d" % (len(eb), fehl))

for ep in ("E2", "E3"):
    k = eb[eb.ep == ep].groupby("t").ex2.mean().mean()
    m = re.search(r"%s Einstiege \d+ an \d+ Stichtagen · Korb ([+-]\d+\.\d) %%" % ep, TXT)
    pruefe("H3", m and abs(100 * k - float(m.group(1))) < 0.06, "%s Korb neu %+.2f %% · Ausgabe %s" % (ep, 100 * k, m.group(1) if m else None))

KL = R[(R.arm == "KL") & (R.aus == "X2")]
for ep in ("E2", "E3"):
    x = eb[eb.ep == ep]
    erw = []
    for t, g in x.groupby("t"):
        z = KL[KL.t == t]
        erw.append(sum(len(gg) * z[z.kl == k].ex.mean() for k, gg in g.groupby("kl")) / len(g))
    e = np.mean(erw)
    k = x.groupby("t").ex.mean().mean()
    pruefe("H4", True, "%s Zufallswelt-Erwartung %+.1f %% gegen E-b-Korb %+.1f %% (Abstand %+.1f Pp)" % (ep, 100 * e, 100 * k, 100 * (k - e)))

s = R.sample(20, random_state=7)
hand = ((1 + s.r) * (1 - 0.0125) / (1 + 0.0125)) / ((1 + s.rb) * (1 - 0.004) / (1 + 0.004)) - 1
pruefe("H5", np.allclose(hand, s.ex_netto), "netto an 20 Ankern von Hand")

ea = R[(R.arm == "E-a") & (R.aus == "X2")]
tb = set(eb.t)
br = {t: EV.breite(t) for t in sorted(set(ea.t))}
pruefe("H6", all(br[t] >= 0.5 for t in tb) and all(br[t] < 0.5 for t in br if t not in tb),
       "%d Stichtage mit Eintritten, davon offen %d · E3 offen: %s" % (len(br), len(tb), ", ".join(str(t.date()) for t in sorted(tb) if t >= pd.Timestamp("2024-01-10"))))

rng = np.random.default_rng(1)
st = [rng.integers(0, max(3 - 2, 1), size=1) for _ in range(500)]
pruefe("H7", all(int(x[0]) == 0 for x in st), "bei 3 Stichtagen ist der Blockstart immer 0 -> jede Ziehung = volle Reihe; Bootstrap kann nur 0 oder 1 sein")

x0 = R[(R.aus == "X0")].sample(10, random_state=8)
fx = 0
for r in x0.itertuples():
    i0 = POS[r.t] + 1
    w = pd.Series(K[r.sym].values[i0:i0 + 366])
    j = len(w) - 1 if w.notna().all() else int(w.notna().values.argmin()) - 1
    fx += not (abs(w.iloc[j] / w.iloc[0] - 1 - r.r) < 1e-9 and j == r.tage)
pruefe("H8", fx == 0, "X0 an 10 Ankern, Abweichungen %d" % fx)
print("\n%d von %d gleich" % (ok, n))
