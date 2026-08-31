# -*- coding: utf-8 -*-
"""Sind die Extremwerte in messdaten.db echt oder Datenfehler? (29.08.2026)

Anlass: K-2 lieferte einen Einzelwert von +80.584 R. Das ist kein
Marktereignis. Betrifft ALLE Messungen dieses Tages, die auf Mittelwerten
beruhen.
"""
import sys
import numpy as np
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import messe_eigenschaft_beitrag as B

reihen = B.lade()
print("=" * 80)
print("DATENQUALITAET — die Extremwerte in messdaten.db")
print("=" * 80)
verdacht = []
for sym, z in reihen.items():
    c = np.array([x[1] for x in z])
    tage = [x[0] for x in z]
    spruenge = c[1:] / np.maximum(c[:-1], 1e-12)
    i = int(np.argmax(spruenge))
    if spruenge[i] > 5.0:
        verdacht.append((float(spruenge[i]), sym, tage[i], tage[i+1],
                         float(c[i]), float(c[i+1])))
verdacht.sort(reverse=True)
print("Reihen mit einem Tagessprung ueber Faktor 5: %d von %d"
      % (len(verdacht), len(reihen)))
print()
print("%-9s %10s  %-11s -> %-11s %14s -> %-14s" % ("Symbol", "Faktor", "von", "bis", "Kurs", "Kurs"))
for f, s, t1, t2, k1, k2 in verdacht[:12]:
    print("%-9s %10.1f  %-11s -> %-11s %14.8f -> %-14.8f" % (s, f, t1, t2, k1, k2))
print()
for sym in ("COCOS", "DREP", "ERD"):
    if sym in reihen:
        z = reihen[sym]
        c = [x[1] for x in z]
        print("%-7s %d Tage, Kurs %.8f (%s) .. %.8f (%s), min %.10f max %.6f"
              % (sym, len(z), c[0], z[0][0], c[-1], z[-1][0], min(c), max(c)))
