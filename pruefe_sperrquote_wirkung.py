# -*- coding: utf-8 -*-
"""Woher kommt der Faktor 8? Die vollstaendige Klaerung. (30.08.2026)

    Funding-Regel, 290 Symbole, 20,6 % gesperrt   ->  +0,0244 R
    Schwelle 0,010,  66 Symbole, 61,1 % gesperrt  ->  +0,1957 R

Drei Unterschiede kommen in Frage. Jeder wird EINZELN geprueft:

    U1  SPERRQUOTE   20,6 % gegen 61,1 %
    U2  BASIS        290 Symbole gegen 66 (die mit Umlaufmenge)
    U3  ZWEI MERKMALE statt einem

Erst wenn klar ist, welcher davon traegt, ist die Schwelle 0,010 verlaesslich
kalibriert.
"""
import statistics as st
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_bewertungskennzahl as MB
import messe_eigenschaft_beitrag as B
import messe_funding_niveau as F
import messe_kandidaten_als_regel as K
import messe_schwelle_kalibrierung as SK

rng = np.random.default_rng(161803)


def wirkung(je_tag, waehle):
    """Median(bleibt) - Median(alle), je Kalendertag - Mass A."""
    d = []
    for z in je_tag.values():
        y = np.array([x["in_r"] for x in z])
        m = waehle(z)
        if 3 <= m.sum() < len(z):
            d.append(float(np.median(y[m]) - np.median(y)))
    return st.mean(d) if d else float("nan")


print("=" * 86)
print("U1 — DIE SPERRQUOTE, alles andere gleich")
print("=" * 86)
reihen = B.lade()
funding = F.lade_funding()
fu = K.baue(reihen, "funding", funding)          # 290 Symbole, nur Funding
print("  Funding allein, 290 Symbole - Wirkung je Sperrquote:")
for grenze in (0.90, 0.80, 0.60, 0.40):
    def w(z, g=grenze):
        r = np.argsort(np.argsort([x["kennzahl"] for x in z])) / max(len(z)-1, 1)
        return r < g
    print("    %4.0f %% gesperrt -> %+.4f R" % (100*(1-grenze), wirkung(fu, w)))

print()
print("=" * 86)
print("U2 — DIE BASIS: dieselbe Regel auf 290 gegen 66 Symbole")
print("=" * 86)
menge = MB.reihe("data/onchain_historie.db", "splycur")
tu = K.baue(reihen, "turnover", menge)
schmal = set()
for z in tu.values():
    for x in z:
        schmal.add(x["sym"])
fu_schmal = {t: [x for x in z if x["sym"] in schmal] for t, z in fu.items()}
fu_schmal = {t: z for t, z in fu_schmal.items() if len(z) >= 12}
def w20(z):
    r = np.argsort(np.argsort([x["kennzahl"] for x in z])) / max(len(z)-1, 1)
    return r < 0.80
print("  Funding, 20 %% gesperrt, auf 290 Symbolen: %+.4f R" % wirkung(fu, w20))
print("  Funding, 20 %% gesperrt, auf  %2d Symbolen: %+.4f R"
      % (len(schmal), wirkung(fu_schmal, w20)))
print("  Symbole je Tag: %d (breit) gegen %d (schmal)"
      % (int(st.median([len(z) for z in fu.values()])),
         int(st.median([len(z) for z in fu_schmal.values()]))))

print()
print("=" * 86)
print("U3 — EIN Merkmal gegen ZWEI, bei gleicher Sperrquote")
print("=" * 86)
je_tag = SK.bewerte(SK.baue())
for name, waehle in (
        ("nur Turnover, 61 % gesperrt", lambda z: (
            np.argsort(np.argsort([x["turnover"] for x in z]))
            / max(len(z)-1, 1)) < 0.39),
        ("Potential > 0,010 (beide)", lambda z: np.array(
            [x["potential"] > 0.010 for x in z]))):
    print("  %-32s %+.4f R" % (name, wirkung(je_tag, waehle)))
