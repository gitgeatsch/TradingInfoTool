# -*- coding: utf-8 -*-
"""H auf der ECHTEN Auswahl - Watchlist-Symbole, mit Binance-Daten."""
import sys, math
sys.path.insert(0, ".")
import numpy as np
import config as C
from messe_marken import laufe, CRV
from messe_struktur_bereinigt import MINDESTALTER, _reif
from simuliere_bremse import SAETZE_ZUM_BERICHTEN

prod = {x.symbol for x in C.get_watchlist()
        if str(getattr(x, "assetklasse", "")).lower() == "krypto"}
alle = _reif(laufe("data/messdaten.db", "krypto", roh_pruefen=False),
             MINDESTALTER)
f = [x for x in alle if x["sym"] in prod]
print(f"{len(f)} Anker aus {len({x['sym'] for x in f})} Watchlist-Symbolen")
h = [x for x in f if x["frei"] and x["gedeckt"]]
r = [x for x in f if not (x["frei"] and x["gedeckt"])]
qh = sum(1 for x in h if x["ausgang"] == "ziel") / len(h)
qr = sum(1 for x in r if x["ausgang"] == "ziel") / len(r)
sr = float(np.median([x["stop_relativ"] for x in h]))
tg = float(np.median([x["tage"] for x in h]))
print(f"  H        {len(h):6} Faelle   Quote {100 * qh:5.1f} %")
print(f"  Nicht-H  {len(r):6} Faelle   Quote {100 * qr:5.1f} %")
print(f"  -> Vorsprung {100 * (qh - qr):+.1f} Punkte, gebuehrenfrei")
print(f"\n  Stopabstand {100 * sr:.1f} %, Haltedauer {tg:.0f} Tage")
print(f"  {'Satz':22}{'netto R (H)':>14}{'netto R (Rest)':>16}")
for n, s in SAETZE_ZUM_BERICHTEN:
    print(f"  {n:22}{qh * CRV - (1 - qh) - 2 * s / sr:+14.3f}"
          f"{qr * CRV - (1 - qr) - 2 * s / sr:+16.3f}")

ziel = np.array([x["ausgang"] == "ziel" for x in f])
istH = np.array([x["frei"] and x["gedeckt"] for x in f])
ordn = {}
for pos, x in enumerate(f):
    ordn.setdefault(x["sym"], []).append((x["i"], pos))
bl = []
for vv in ordn.values():
    gr = []
    for ii, pos in sorted(vv):
        if not gr or ii - gr[-1][0] >= 250:
            gr.append([ii, []])
        gr[-1][1].append(pos)
    if len(gr) >= 2:
        bl.append([np.array(g[1]) for g in gr])
rng = np.random.default_rng(20260909)
zieh = []
for _ in range(200):
    gew = ziel.copy()
    for gr in bl:
        a_ = np.concatenate(gr)
        gew[a_] = ziel[np.concatenate(
            [gr[j] for j in rng.permutation(len(gr))])]
    zieh.append(float(gew[istH].mean()) - float(gew[~istH].mean()))
s95 = float(np.quantile(zieh, 0.95))
streu = float(np.std(zieh)) / math.sqrt(len(zieh))
d = qh - qr
print(f"\n  {len(bl)} Reihen mit zwei Bloecken, 200 Laeufe")
print(f"  SCHWELLE (95 %)  {100 * s95:+.1f}")
print(f"  gemessen         {100 * d:+.1f}")
print("  -> " + ("ZU KNAPP (2.48)" if abs(d - s95) < 2 * streu
                 else "TRAEGT" if d > s95 else "traegt nicht"))
