"""Gegenprobe O47 F2-A A1 (18.10.2026) - zweiter Weg, ohne o47_f2a. Holdout wird NICHT beruehrt.

    python Basisinfos/Spot_Voranalyse_04_10/o47_f2a_gegenprobe.py

G1 Stand je Sonntag neu aus den Rohspalten (am_kalibrierung.csv B1/B2, o47_schritt0.csv B3_V) gegen o47_f2a_A1.csv
G2 K2 neu gezaehlt: Season-Sonntage je Stand aus o47_schritt1.csv (rel13 >= 0,25), 2019-04-01..2026-06-22
G3 Ordnung und Lift 3 von 3 wie vorab (0 < 1 < 2 < 3, Lift >= 2)
Auskunft (aendert nichts): Wilson-Intervall 95 % je Stand; Season-Anteil je GELTENDER STUFE (die Ampel meldet Stufen, nicht den Stand)
"""
import math
import os
import sys

import pandas as pd

os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass
ok = []


def pruefe(name, bed, info=""):
    ok.append(bool(bed))
    print("  %s  %s%s" % ("OK  " if bed else "FEHL", name, ("  (%s)" % info) if info else ""))


def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    m = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    c = (p + z * z / (2 * n)) / (1 + z * z / n)
    return c - m, c + m


K = pd.read_csv("data/_spot/am_kalibrierung.csv", sep=";", parse_dates=["date"]).set_index("date")
B3 = pd.read_csv("data/_spot/o47_schritt0.csv", sep=";", parse_dates=[0], index_col=0).B3_V
W1 = pd.read_csv("data/_spot/o47_schritt1.csv", sep=";", parse_dates=[0], index_col=0)
A1 = pd.read_csv("data/_spot/o47_f2a_A1.csv", sep=";", parse_dates=[0], index_col=0)
so = [t for t in W1.index if pd.Timestamp("2019-04-01") <= t <= pd.Timestamp("2026-06-22") and W1.rel13[t] == W1.rel13[t] and t in K.index]
print("O47 F2-A A1 GEGENPROBE · %d Sonntage\n" % len(so))
st = {t: int(K.B1[t] > 0.20) + int(K.B2[t] > 0.05) + int(B3[t] > 0.10) for t in so}
pruefe("G1 Stand je Sonntag gleich", all(st[t] == int(A1.stand[t]) for t in so), "%d von %d" % (sum(st[t] == int(A1.stand[t]) for t in so), len(so)))
zahl = {s: [0, 0] for s in range(4)}
for t in so:
    zahl[st[t]][0] += 1
    zahl[st[t]][1] += int(W1.rel13[t] >= 0.25)
basis = sum(v[1] for v in zahl.values()) / len(so)
anteil = {s: v[1] / v[0] for s, v in zahl.items()}
print("  K2 neu: " + " · ".join("%d von 3: %d/%d = %.1f %% [95 %%: %.1f..%.1f]" % (s, v[1], v[0], 100 * anteil[s], *(100 * x for x in wilson(v[1], v[0])))
                                 for s, v in zahl.items()))
pruefe("G2 Zahlen wie o47_f2a (Season 1,0 / 2,9 / 2,7 / 25,4 %)", [round(100 * anteil[s], 1) for s in range(4)] == [1.0, 2.9, 2.7, 25.4])
mono = all(anteil[s] < anteil[s + 1] for s in range(3))
lift = anteil[3] / basis
pruefe("G3 Ordnung bricht zwischen 1 und 2 von 3, Lift 3 von 3 >= 2 -> STOPP wie o47_f2a", (not mono) and lift >= 2 and anteil[1] > anteil[2],
       "Lift %.2f" % lift)
print("\nAuskunft: Season-Anteil je GELTENDER Stufe (Sonntage, Kalibrierungszeitraum):")
g = pd.DataFrame({"stufe": [A1.geltend[t] for t in so], "w": [W1.rel13[t] >= 0.25 for t in so]})
for s, x in g.groupby("stufe"):
    lo, hi = wilson(int(x.w.sum()), len(x))
    print("   %-13s %3d So · Season %2d = %5.1f %% [95 %%: %.1f..%.1f] · Lift %.2f" % (s, len(x), int(x.w.sum()), 100 * x.w.mean(), 100 * lo, 100 * hi,
                                                                                    x.w.mean() / basis))
print("\n%d Pruefungen, %s" % (len(ok), "ALLE BESTANDEN" if all(ok) else "%d FEHLGESCHLAGEN" % ok.count(False)))
