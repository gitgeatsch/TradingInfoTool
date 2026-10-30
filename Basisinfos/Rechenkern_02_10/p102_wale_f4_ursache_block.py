# -*- coding: utf-8 -*-
"""Ursache S2-Fehlalarm im Permutationstest (Fassung 4c) - nur künstliche Signale, KEIN echtes Ergebnis.
Permutationstest mit verschiedenen Blocklängen: 15 / 30 / 60 T und Kalendermonat. Dazu Lauflänge der Fünftel (echtes E gegen S1/S2)."""
import sys
import numpy as np
sys.path.insert(0, r"D:\CLAUDE_Projects\SoftwareProjekte\TradingInfoTool\Basisinfos\Rechenkern_02_10")
import p102_wale_f4 as F  # noqa: E402
import p102_wale_basis as B  # noqa: E402

B.fassung4()
WELTEN = int(sys.argv[1]) if len(sys.argv) > 1 else 500
PERM = 200
rng = np.random.default_rng(777001)
tg, aus = B.lade()
w = B.maske(tg, B.URTEIL)
n, S, M = len(tg), B.SYMBOLE, "spot"
es = {s: aus[s]["markt"][M][B.Q_HAUPT][2] for s in S}
phis = {}
for s in S:
    e = es[s]; f = np.isfinite(e[:-1]) & np.isfinite(e[1:]); phis[s] = float(np.corrcoef(e[:-1][f], e[1:][f])[0, 1])
rho = 0.021
ys = {h: [aus[s]["y"][(h, 0)][w] for s in S] for h in (1, 3, 7)}
monat = np.unique(np.array([d.year * 12 + d.month for d in tg]), return_inverse=True)[1]
mon_w = monat[w] - monat[w].min()
lang = int(w.sum())


def bloecke(art):
    if art == "monat":
        return [np.where(mon_w == m)[0] for m in range(mon_w.max() + 1)]
    return [np.arange(i * art, min((i + 1) * art, lang)) for i in range(-(-lang // art))]


ARTEN = (15, 30, 60, "monat")
BL = {a: bloecke(a) for a in ARTEN}


def s1():
    c = F.ar1(rng, n, float(np.mean(list(phis.values()))))
    return [np.sqrt(rho) * c + np.sqrt(1 - rho) * F.ar1(rng, n, phis[s]) for s in S]


def s2():
    m = rng.standard_normal(monat.max() + 1)[monat]
    return [m + 0.2 * rng.standard_normal(n) for _ in S]


def lauf(l):
    l = l[np.isfinite(l)]
    return len(l) / max(1, 1 + np.sum(l[1:] != l[:-1]))


print("Mittlere Lauflänge der Fünftel (Tage): echtes E %s" % ", ".join(
    "%s %.2f" % (s[:-4], lauf(B.fuenftel(es[s])[w])) for s in S), flush=True)
for name, welt in (("S1", s1), ("S2", s2)):
    tr = {(a, h): 0 for a in ARTEN for h in (1, 3, 7)}
    lz = []
    for i in range(WELTEN):
        labs0 = [B.fuenftel(e)[w] for e in welt()]
        lz.append(np.mean([lauf(l) for l in labs0]))
        for h in (1, 3, 7):
            labs = [np.where(np.isfinite(l) & np.isfinite(y), l, np.nan) for l, y in zip(labs0, ys[h])]
            yy = [np.where(np.isfinite(l), y, np.nan) for l, y in zip(labs, ys[h])]
            d = B.differenz_gepoolt(labs, yy)
            for a in ARTEN:
                bl = BL[a]
                null = []
                for _ in range(PERM):
                    idx = np.concatenate([bl[j] for j in rng.permutation(len(bl))])      # EINE Vertauschung für alle sechs
                    null.append(B.differenz_gepoolt([l[idx] for l in labs], yy))
                null = np.array(null)
                tr[(a, h)] += d > np.quantile(null[np.isfinite(null)], 0.95)
    print("%s (%d Welten, %d Vertauschungen) · Lauflänge Fünftel %.2f T" % (name, WELTEN, PERM, np.mean(lz)), flush=True)
    for a in ARTEN:
        print("   Block %-6s  H1 %4.1f %%  H3 %4.1f %%  H7 %4.1f %%  (%d Blöcke)" % (
            a, *(100 * tr[(a, h)] / WELTEN for h in (1, 3, 7)), len(BL[a])), flush=True)
print("Standardfehler bei 5 %%: %.2f Pp" % (100 * np.sqrt(0.05 * 0.95 / WELTEN)))
