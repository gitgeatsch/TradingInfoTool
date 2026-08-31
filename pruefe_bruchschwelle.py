# -*- coding: utf-8 -*-
"""Wieviele Reihen sind betroffen - je nach Schwelle?"""
import sys
import numpy as np
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import messe_eigenschaft_beitrag as B
reihen = B.lade()
print("Schwelle   Reihen mit Bruch   Anteil")
for s in (2.0, 3.0, 5.0, 10.0, 50.0):
    n = 0
    for sym, z in reihen.items():
        c = np.array([x[1] for x in z])
        v = c[1:] / np.maximum(c[:-1], 1e-12)
        if (v > s).any() or (v < 1.0/s).any():
            n += 1
    print("  %5.1f    %8d          %5.1f %%" % (s, n, 100*n/len(reihen)))
