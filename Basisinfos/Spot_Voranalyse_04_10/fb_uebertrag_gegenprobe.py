"""Gegenprobe Uebertragbarkeit B1 (§39.6) - eigene Schleife je Position aus Rohkursen gegen data/_spot/fb_uebertrag.csv, nur lesend.

  G1 kein Kern-Symbol, nur Starttage ab 2024 · G2 Ausloesung (erster Tagesschluss >= 3 x Startkurs, Verkauf Folgetag) je Position gleich
  G3 d = 0,5 x (Kurs Verkauf - Kurs Ende) / Startkurs je Position gleich · G4 Korb (Mittel ueber Starttage) gleich der Ausgabe
"""
import os
import re
import sys

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
os.chdir(os.path.dirname(os.path.dirname(HIER)))
import fb_messung as FB  # noqa: E402

ok = n = 0


def pruefe(name, gut, info):
    global ok, n
    n += 1; ok += bool(gut)
    print("%-3s %s  %s" % (name, "gleich" if gut else "ABWEICHUNG", info), flush=True)


D = pd.read_csv(os.path.join("data", "_spot", "fb_uebertrag.csv"), sep=";", parse_dates=["t"])
pruefe("G1", not D.sym.isin(["BTC", "ETH", "SOL"]).any() and (D.t >= "2024-01-01").all(), "Positionen %d · Starttage %d" % (len(D), D.t.nunique()))
aus_f = d_f = 0
dd = []
for r in D.itertuples():
    v = FB.K[r.sym].values
    i = FB.POS[r.t]
    p0 = v[i]
    tag, ende = None, None
    for j in range(1, 366):
        if i + j >= len(v) or not np.isfinite(v[i + j]):
            break
        ende = v[i + j]
        if tag is None and v[i + j] >= 3 * p0:
            tag = j + 1                                       # Verkauf am Folgetag
    letzt = j - 1 if (i + j >= len(v) or not np.isfinite(v[i + j])) else 365
    if tag is not None and tag > letzt:
        tag = None                                            # Folgetag liegt hinter dem Fensterende -> keine Ausloesung
    d = 0.5 * (v[i + tag] - ende) / p0 if tag is not None else 0.0
    aus_f += (tag is not None) != bool(r.aus)
    d_f += abs(d - r.d) > 1e-9
    dd.append(d)
pruefe("G2", aus_f == 0, "Ausloesungen eigene %d · Ablage %d · abweichend %d" % (int(np.sum(np.array(dd) != 0)), int(D.aus.sum()), aus_f))
pruefe("G3", d_f == 0, "d abweichend an %d Positionen" % d_f)
D["d2"] = dd
k = D.groupby("t").d2.mean().mean()
aus = open(os.path.join("Basisinfos", "Spot_Voranalyse_04_10", "fb_uebertrag.txt"), encoding="utf-8").read()
ka = float(re.search(r"ALLE ohne Kern.*?Korb ([+-][\d.]+) Pp", aus).group(1))
pruefe("G4", abs(100 * k - ka) < 0.006, "eigener Korb %+.3f Pp · Ausgabe %+.2f Pp" % (100 * k, ka))
print("\n%d von %d gleich" % (ok, n))
