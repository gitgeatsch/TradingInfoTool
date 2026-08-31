# -*- coding: utf-8 -*-
"""Gegenpruefung zum MC/TVL-Befund (30.08.2026).

Drei Verdachtsmomente, alle vor dem Lauf benannt:

  V1 BLOCKLAENGE   Der Bootstrap nutzt 30-Tage-Bloecke. Bei Horizont 60
                   ueberlappen benachbarte Anker um 60 Tage - die Bloecke sind
                   KUERZER als das Vorwaertsfenster. Genau daran ist Kapitel
                   103 gescheitert: "die Blocklaenge (250) muss ueber dem
                   Vorwaertsfenster (120) liegen".
  V2 SURVIVORSHIP  Die 19 Symbole sind die, die HEUTE noch TVL melden UND bei
                   Coin Metrics gefuehrt werden. Gestorbene Protokolle fehlen.
                   Wenn "guenstig" mit "ueberlebt" zusammenhaengt, ist der
                   Befund ein Auswahleffekt.
  V3 BREITE        19 Symbole, Terzile also je ~6 Werte. Ein einzelner Wert
                   kann ein Terzil dominieren.
"""
import statistics as st, sys
import numpy as np
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import messe_bewertungskennzahl as M
import messe_eigenschaft_beitrag as B

menge = M.reihe("data/onchain_historie.db", "splycur")
tvl = M.reihe("data/tvl_historie.db", "tvl_historie", "tvl_usd")
reihen = B.lade()
rng = np.random.default_rng(31)

print("=" * 88)
print("GEGENPRUEFUNG MC/TVL")
print("=" * 88)
print()
print("V1 — BLOCKLAENGE muss ueber dem Horizont liegen")
for horizont in (5, 20, 60):
    je_tag = M.baue(reihen, menge, tvl, horizont)
    w = M.je_tag_quer(je_tag)
    print("  Horizont %2d:" % horizont)
    for block in (30, 90, 180, 250):
        if block < horizont:
            continue
        M.urteil_tage("    Block %3d Tage" % block, w, rng, block=block)

print()
print("V3 — welche 19 Symbole, und wie breit sind die Terzile?")
je_tag = M.baue(reihen, menge, tvl, 20)
syms = sorted({x["sym"] for z in je_tag.values() for x in z})
print("  %s" % ", ".join(syms))
groessen = [len(z) for z in je_tag.values()]
print("  Symbole je Tag: Median %d  (min %d, max %d)  -> Terzil ~%d Werte"
      % (st.median(groessen), min(groessen), max(groessen), st.median(groessen)//3))

print()
print("V2 — SURVIVORSHIP: enden die 19 hoeher oder tiefer als der Rest?")
alle = B.lade()
def endet_tiefer(s):
    z = alle[s]
    return z[-1][1] < z[200][1]
inn = [s for s in syms if s in alle]
rest = [s for s in alle if s not in syms]
print("  die 19 Symbole : %d von %d enden tiefer (%.0f %%)"
      % (sum(endet_tiefer(s) for s in inn), len(inn),
         100*sum(endet_tiefer(s) for s in inn)/len(inn)))
print("  alle uebrigen  : %d von %d enden tiefer (%.0f %%)"
      % (sum(endet_tiefer(s) for s in rest), len(rest),
         100*sum(endet_tiefer(s) for s in rest)/len(rest)))
print("  -> %s" % ("⚠️ AUSWAHLEFFEKT: die 19 sind die Ueberlebenden"
                    if 100*sum(endet_tiefer(s) for s in inn)/len(inn) < 70
                    else "kein auffaelliger Unterschied"))
