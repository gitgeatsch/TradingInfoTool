# -*- coding: utf-8 -*-
"""V3: ist der Funding-Befund ein Auswahleffekt?

Die 290 Symbole sind die, die HEUTE auf Binance Futures gelistet sind.
Delistete fehlen. Zwei Gegenproben:
  a) enden die 290 besser als der Rest unserer Reihen?
  b) haelt der Befund auch, wenn man nur die aeltesten Symbole nimmt
     (die also lange genug da waren, um delistet werden zu koennen)?
"""
import statistics as st, sys
import numpy as np
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import messe_funding_niveau as F
import messe_bewertungskennzahl as M
import messe_eigenschaft_beitrag as B

reihen = B.lade(); funding = F.lade_funding()
rng = np.random.default_rng(99)
mit = {s for s in reihen if s.upper() in funding}
ohne = set(reihen) - mit
def tiefer(s):
    z = reihen[s]
    return z[-1][1] < z[200][1]
print("a) enden die Funding-Symbole besser?")
print("   mit Funding (%3d): %3d enden tiefer (%.0f %%)"
      % (len(mit), sum(tiefer(s) for s in mit),
         100*sum(tiefer(s) for s in mit)/len(mit)))
print("   ohne        (%3d): %3d enden tiefer (%.0f %%)"
      % (len(ohne), sum(tiefer(s) for s in ohne),
         100*sum(tiefer(s) for s in ohne)/max(len(ohne),1)))
print()
print("b) haelt der Befund auf den AELTESTEN Symbolen (>= 1500 Handelstage)?")
alt = {s: r for s, r in reihen.items() if len(r) >= 1500 and s.upper() in funding}
print("   %d Symbole" % len(alt))
je_tag = {}
for sym, roh in alt.items():
    f = funding[sym.upper()]
    tage = [z[0] for z in roh]
    c = np.array([z[1] for z in roh])
    h = np.array([z[2] for z in roh]); t_ = np.array([z[3] for z in roh])
    breite = B.spanne(h, t_, c, B.SCHWANKUNG)
    for i in range(60, len(c) - 20):
        r = breite[i]
        if not np.isfinite(r) or r <= 0 or tage[i] not in f:
            continue
        je_tag.setdefault(tage[i], []).append(
            {"sym": sym, "kennzahl": f[tage[i]],
             "in_r": float((c[i+20] - c[i]) / r)})
je_tag = {t: z for t, z in je_tag.items() if len(z) >= 10}
M.urteil_tage("   nur die aeltesten", M.je_tag_quer(je_tag), rng, 250)
