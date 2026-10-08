"""Gegenprobe Kalibrierung Season-Ampel (Spot §36.3) - eigener Rechenweg, nur lesend, keine Abrufe.

    python Basisinfos/Spot_Voranalyse_04_10/am_gegenprobe.py

  A1 Stand je Tag aus den abgelegten Bedingungen mit Ganzzahl-Logik neu (die numpy-bool-Falle) - gleich
  A2 K2: Season-Anteil je Stand neu = Ausgabe
  A3 K1: oberes Fuenftel von B2 und Netto-Liq mit np.percentile neu = Ausgabe
  A4 Leave-one-out ohne 2020/21: Season-Anteil bei 3/3 neu = Ausgabe
  A5 K5: Fehlalarm-Abschnitte mit eigener Laufsuche = Ausgabe
  A6 Wahrheit: Season-Tage = rel90 >= 0,25 an 5 Tagen direkt aus dem S1-Korb (Korb und BTC 90 T vorwaerts) neu
"""
import os
import re
import sys

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
os.chdir(os.path.dirname(os.path.dirname(HIER)))

TXT = open(os.path.join(HIER, "am_kalibrierung.txt"), encoding="utf-8").read()
Z = pd.read_csv(os.path.join("data", "_spot", "am_kalibrierung.csv"), sep=";", index_col=0, parse_dates=True)
Z["season"] = Z.season.astype(str).str.lower().eq("true")
ok = n = 0


def pruefe(name, gut, info):
    global ok, n
    n += 1; ok += bool(gut)
    print("%-3s %s  %s" % (name, "gleich" if gut else "ABWEICHUNG", info), flush=True)


st = np.zeros(len(Z), dtype=int)
for b, s in (("B1", 0.20), ("B2", 0.05), ("B3", 0.10)):
    st += (Z[b].values > s).astype(int)
pruefe("A1", (st == Z.stand.values).all(), "Stand neu an %d Tagen, Abweichungen %d" % (len(Z), int((st != Z.stand.values).sum())))

aus = dict((int(k), float(v)) for k, v in re.findall(r"(\d) von 3: Tage +\d+ \( *[\d.]+ %\) · Season-Tage +([\d.]+) %", TXT))
neu = {k: 100 * Z.season[st == k].mean() for k in range(4)}
pruefe("A2", all(abs(neu[k] - aus[k]) < 0.06 for k in aus), "neu %s · Ausgabe %s" % ({k: round(v, 1) for k, v in neu.items()}, aus))

basis = Z.season.mean()
gut = True
for c, muster in (("B2", r"B2 .*\| ([\d.]+)\.\.([\d.]+): +([\d.]+) % \(Lift"), ("Netto-Liq 13W", r"Netto-Liq 13W .*\| ([\d.]+)\.\.([\d.]+): +([\d.]+) % \(Lift")):
    x = Z[c].dropna()
    g = Z.loc[x.index]
    oben = g[x > np.percentile(x, 80)].season.mean()      # wie qcut: oberes Fuenftel = (p80, max], die Grenze gehoert nach unten
    m = re.search(muster, TXT)
    gut &= bool(m) and abs(100 * oben - float(m.group(3))) < 0.6
pruefe("A3", gut, "oberes Fuenftel B2 und Netto-Liq neu gegen Ausgabe")

m = re.search(r"ohne 2020-11-12\.\.2021-03-23: .*?3: ([\d.]+) %", TXT)
Y = Z[(Z.index < "2020-11-12") | (Z.index > "2021-03-23")]
v = 100 * Y.season[(Y.stand == 3)].mean()
pruefe("A4", m and abs(v - float(m.group(1))) < 0.06, "ohne 2020/21: Season bei 3/3 neu %.2f %% · Ausgabe %s" % (v, m.group(1) if m else None))

alle_season = Z.season
laeufe, a0 = [], None
drei = pd.Series(st >= 3, index=Z.index)
for d, w in drei.items():
    if w and a0 is None:
        a0 = d
    if not w and a0 is not None:
        laeufe.append((a0, d)); a0 = None
fa = [(a, e) for a, e in laeufe if (e - a).days >= 14 and not alle_season[a:e + pd.Timedelta(days=90)].any()]
aus_fa = re.findall(r"(\d{4}-\d\d-\d\d)\.\.(\d{4}-\d\d-\d\d) \(\d+ T\) FEHLALARM", TXT)
pruefe("A5", [(str(a.date()), str(e.date())) for a, e in fa] == aus_fa, "Fehlalarm-Abschnitte neu %s · Ausgabe %s" % ([(str(a.date()), str(e.date())) for a, e in fa], aus_fa))

import s1_messung as S1  # noqa: E402
s1 = S1.baue()
korb, Bi = s1["korb"], s1["Bi"]
fx = 0
for d in [pd.Timestamp(x) for x in ("2020-04-15", "2020-12-01", "2021-07-01", "2022-05-20", "2024-03-01")]:
    r = (korb[d + pd.Timedelta(days=90)] / korb[d]) / (Bi[d + pd.Timedelta(days=90)] / Bi[d]) - 1
    fx += (r >= 0.25) != bool(Z.season.get(d, False))
pruefe("A6", fx == 0, "Season-Kennzeichen an 5 Tagen aus Korb/BTC neu, Abweichungen %d" % fx)
print("\n%d von %d gleich" % (ok, n))

# A7 K2b Muster eigene Rechnung
b1, b2, b3 = (Z.B1.values > 0.20), (Z.B2.values > 0.05), (Z.B3.values > 0.10)
fx = 0
for name, mm in (("nur BTC", b1 & ~b2 & ~b3), ("nur Geld \(M2 und Stable\)", ~b1 & b2 & b3), ("BTC \+ M2, Stablecoins fehlen", b1 & b2 & ~b3), ("alle drei", b1 & b2 & b3)):
    m = re.search(r"%s +Tage +(\d+) · Season-Tage +([\d.]+) %%" % name, TXT)
    tage, anteil = int(mm.sum()), (100 * Z.season.values[mm].mean() if mm.sum() else 0.0)
    fx += not (m and int(m.group(1)) == tage and abs(float(m.group(2)) - anteil) < 0.06)
pruefe("A7", fx == 0, "Muster nur BTC / nur Geld / BTC+M2 ohne Stable / alle drei neu gegen Ausgabe, Abweichungen %d" % fx)
print("%d von %d gleich (mit A7)" % (ok, n))
