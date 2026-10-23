"""Gegenprobe P72 (23.10.2026) - zweite Wege.

    python Basisinfos/Rechenkern_02_10/p72_gegenprobe.py

G1 Strecken F6 (BTC ueber 200 T) eigener Weg: Lauflaengen per itertools.groupby statt diff - gleich?
G2 Aufloesung mit anderem Startwert (Struktur F6, D = 1,0 Pp): 2024-26 deutlich unter 2020-26?
G3 Baerenphasen >= -50 % vom Allzeithoch per cummax-Rueckgang (eigener Weg) - dieselben Hoch-Daten?
"""
import itertools
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
WURZEL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, WURZEL)
os.chdir(WURZEL)
import p71_marktfilter as Q  # noqa: E402
import p72_historie_voranalyse as V  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass
ok = []


def pruefe(name, bed, info=""):
    ok.append(bool(bed))
    print("  %s  %s%s" % ("OK  " if bed else "FEHL", name, ("  (%s)" % info) if info else ""))


print("P72 GEGENPROBE\n")
p = V.btc()
an = (p > p.rolling(200).mean()).where(p.rolling(200).count() == 200).shift(1)
for a, b, soll in (("2024-01-01", "2026-08-31", 31), ("2020-06-01", "2026-08-31", 53)):
    z = an[a:b].dropna().astype(int).tolist()
    zahl = sum(1 for _ in itertools.groupby(z))
    pruefe("G1 Strecken F6 %s..%s per groupby" % (a[:7], b[:7]), zahl == soll, "%d (Soll %d)" % (zahl, soll))
R = Q.tagesreihe("unverzerrt_1")
s, n = R
tag = np.where(n > 0, s / np.maximum(n, 1), 0.0)
rng = np.random.default_rng(999)
zk = an["2024-01-01":"2026-08-31"].fillna(1).astype(int).to_numpy()
zl = an["2020-06-01":"2026-08-31"].fillna(1).astype(int).to_numpy()
ak = V.aufloesung(zk, tag, n, (0.01,), rng, laeufe=100)[0.01]
al = V.aufloesung(zl, tag, n, (0.01,), rng, laeufe=100)[0.01]
pruefe("G2 Aufloesung D 1,0 Pp anderer Startwert: verlaengert deutlich besser (>= +30 Pp)", al - ak >= 0.30, "2024-26 %.0f %% · 2020-26 %.0f %%" % (100 * ak, 100 * al))
q = p["2013-01-01":]
dd = q / q.cummax() - 1
hochs = []
in_phase = False
for t, v in dd.items():
    if not in_phase and v <= -0.5:
        in_phase = True
        hochs.append(q[:t].idxmax().date())
    elif in_phase and v == 0:
        in_phase = False
soll = [h.date() for h, *_ in V.uebergeordnet(q)]
pruefe("G3 Baerenphasen-Hochs per cummax gleich", hochs == soll, "%s" % [str(h) for h in hochs])
print("\n%d Pruefungen, %s" % (len(ok), "ALLE BESTANDEN" if all(ok) else "%d FEHLGESCHLAGEN" % ok.count(False)))
