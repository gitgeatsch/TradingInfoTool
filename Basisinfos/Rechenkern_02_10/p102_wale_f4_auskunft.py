# -*- coding: utf-8 -*-
"""Auskunft nach der Messung F4d (NICHT Teil des Urteils): p mit 10.000 Vertauschungen und anderem Startwert, je Blocklänge,
Weglassen je eines Wertes."""
import sys
import numpy as np
sys.path.insert(0, r"D:\CLAUDE_Projects\SoftwareProjekte\TradingInfoTool\Basisinfos\Rechenkern_02_10")
import p102_wale_f4 as F  # noqa
import p102_wale_basis as B  # noqa
vorher = B.fingerabdruck()
tg, aus = B.lade()
w = B.maske(tg, B.URTEIL)
S = B.SYMBOLE


def p_wert(syms, block, n, seed):
    rng = np.random.default_rng(seed)
    labs = [aus[s]["markt"]["spot"][B.Q_HAUPT][3][w] for s in syms]
    ys = [aus[s]["y"][(1, 0)][w] for s in syms]
    labs = [np.where(np.isfinite(l) & np.isfinite(y), l, np.nan) for l, y in zip(labs, ys)]
    ys = [np.where(np.isfinite(l), y, np.nan) for l, y in zip(labs, ys)]
    d = B.differenz_gepoolt(labs, ys)
    alt = B.NULL_BLOCK; B.NULL_BLOCK = block
    _, _, _, null = B.nullpunkt_gepoolt(labs, ys, rng, n=n, verteilung=True)
    B.NULL_BLOCK = alt
    return d, float(np.quantile(null, 0.95)), (1 + (null >= d).sum()) / (1 + len(null))


for blk in (30, 15, 60):
    d, sw, p = p_wert(S, blk, 10000, 99)
    print("Alle sechs · Block %2d T · 10.000 Vertauschungen: D %+.3f · Schwelle %+.3f · p %.4f" % (blk, 100 * d, 100 * sw, p), flush=True)
for s in S:
    rest = tuple(x for x in S if x != s)
    d, sw, p = p_wert(rest, 30, 5000, 98)
    print("ohne %-9s D %+.3f · Schwelle %+.3f · p %.4f" % (s, 100 * d, 100 * sw, p), flush=True)
print("Seiteneffekt: geschützte Datei unverändert:", B.fingerabdruck() == vorher)
