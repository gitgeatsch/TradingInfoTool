# -*- coding: utf-8 -*-
"""Gegenpruefung zum Turnover-Befund (30.08.2026).

+0,0616 R als Regel - staerker als Funding (+0,0244). Drei Verdachtsmomente:

  V1 MITLAEUFER   Turnover und Funding messen beide "Aufmerksamkeit". Wenn
                  sie dasselbe sind, gibt es nicht zwei Beitraege sondern
                  einen. Test: Turnover-Regel INNERHALB der Funding-Schichten.
  V2 BREITE       nur 66 Symbole (die mit Umlaufmenge bei Coin Metrics).
  V3 BLOCKLAENGE  haelt es auch bei langen Bloecken?
"""
import statistics as st, sys
import numpy as np
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import messe_regel_wirksamkeit as W
import messe_kandidaten_als_regel as K
import messe_bewertungskennzahl as MB
import messe_eigenschaft_beitrag as B
import messe_funding_niveau as F

reihen = B.lade()
rng = np.random.default_rng(1234)
menge = MB.reihe("data/onchain_historie.db", "splycur")
funding = F.lade_funding()
tu = K.baue(reihen, "turnover", menge)

print("=" * 86)
print("GEGENPRUEFUNG TURNOVER")
print("=" * 86)
print()
print("V3 — Blocklaenge")
d, _, _, _ = W.wirkung(tu, True)
for block in (90, 180, 250, 400):
    MB.urteil_tage("    Block %3d" % block, d, rng, block)

print()
print("V1 — MITLAEUFER: ist Turnover dasselbe wie Funding?")
# Funding je Anker dazuholen
paare = []
for tag, z in tu.items():
    for x in z:
        f = funding.get(x["sym"].upper(), {}).get(tag)
        if f is not None:
            x["funding"] = f
            paare.append((x["kennzahl"], f))
if paare:
    a = np.array([p[0] for p in paare]); b = np.array([p[1] for p in paare])
    print("    Korrelation Turnover <-> Funding: %+.3f" % np.corrcoef(a, b)[0,1])
print("    Turnover-Regel INNERHALB gleicher Funding-Schicht:")
for schicht, name in ((0, "niedriges Funding"), (1, "mittleres"), (2, "hohes")):
    teil = {}
    for tag, z in tu.items():
        mit = [x for x in z if "funding" in x]
        if len(mit) < 12: continue
        r = MB.terzile([x["funding"] for x in mit])
        aus = [x for x, k in zip(mit, r) if k == schicht]
        if len(aus) >= 8:
            teil[tag] = aus
    if teil:
        dd, _, _, _ = W.wirkung(teil, True)
        MB.urteil_tage("      %-20s" % name, dd, rng, 250)

print()
print("V2 — welche 66 Symbole, und enden sie anders als der Rest?")
syms = sorted({x["sym"] for z in tu.values() for x in z})
def tiefer(s):
    z = reihen[s]; return z[-1][1] < z[200][1]
rest = [s for s in reihen if s not in syms]
print("    die %d Turnover-Symbole: %d enden tiefer (%.0f %%)"
      % (len(syms), sum(tiefer(s) for s in syms), 100*sum(tiefer(s) for s in syms)/len(syms)))
print("    die uebrigen %d          : %d enden tiefer (%.0f %%)"
      % (len(rest), sum(tiefer(s) for s in rest), 100*sum(tiefer(s) for s in rest)/len(rest)))
