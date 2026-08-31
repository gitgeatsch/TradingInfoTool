# -*- coding: utf-8 -*-
"""Wie scharf ist die Momentum-Messung? Ohne diese Zahl ist der Nullbefund wertlos."""
import sys
import numpy as np
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import messe_momentum_12_1 as MM
import messe_bewertungskennzahl as M
import messe_eigenschaft_beitrag as B

reihen = B.lade()
rng = np.random.default_rng(808)
for horizont in (20,):
    je_tag = MM.baue(reihen, horizont, 252, 21)
    print("MOMENTUM 12_1, Horizont %d — %d Kalendertage" % (horizont, len(je_tag)))
    print("Positivkontrolle: Effekt auf das oberste Fuenftel gepflanzt")
    for s in (0.05, 0.10, 0.20, 0.30):
        # pflanzen auf HOHES Momentum, dann Vorzeichen drehen wie im Hauptlauf
        w = {}
        for t, z in je_tag.items():
            r = M.terzile([x["kennzahl"] for x in z])
            g = [x["in_r"] for x, k in zip(z, r) if k == 0]
            h = [x["in_r"] + s for x, k in zip(z, r) if k == 2]
            if len(g) >= 3 and len(h) >= 3:
                w[t] = float(np.median(h) - np.median(g))
        M.urteil_tage("  gepflanzt %+.2f R" % s, w, rng, 90)
