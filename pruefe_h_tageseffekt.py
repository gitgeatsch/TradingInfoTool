# -*- coding: utf-8 -*-
"""Ist H ein TAGES-Signal statt eines Asset-Signals? (30.08.2026)

## Der Befund, der diese Frage aufwirft

    H gegen ALLE Anker (gepoolt, alle Tage)      +4,5 Punkte
    H gegen quotengleichen Zufall DESSELBEN Tages  -0,047  (umgekehrt!)

⚠️ Der Unterschied ist die TAGES-KLAMMER. Wenn H gegen Anker desselben Tages
verliert, gegen den Durchschnitt aller Tage aber gewinnt, dann liegt der
Vorteil NICHT in der Asset-Wahl - sondern darin, an welchen TAGEN H ueberhaupt
auftritt.

Das ist derselbe Befund wie bei V-0 (die Rollen-Kette hatte keine
Asset-Auswahl, nur einen Kalendertag-Effekt).

## Die faire Frage an H

Bevor H als wertlos gilt, muss geprueft werden, ob es als TAGES-Signal traegt:

    Sind Tage mit vielen H-Ankern bessere Tage als Tage mit wenigen?

Traegt es dort, ist H nicht wertlos - sondern falsch eingesetzt. Es waere ein
Timing-Merkmal, kein Auswahlmerkmal.
"""
import io, json, statistics as st, sys
import numpy as np
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import messe_bewertungskennzahl as MB

anker = json.loads(io.open("anker_h_2026_08_30.json", encoding="utf-8").read())
tage = {}
for a in anker:
    tage.setdefault(a["datum"], []).append(a)
tage = {t: z for t, z in tage.items() if len(z) >= 20}
rng = np.random.default_rng(20260830)

print("=" * 86)
print("IST H EIN TAGES-SIGNAL?")
print("=" * 86)
print("%d Kalendertage mit mindestens 20 Ankern" % len(tage))
print()
# je Tag: H-Anteil und die Bewegung ALLER Anker dieses Tages
zeilen = []
for t, z in tage.items():
    anteil = sum(1 for a in z if a["h"]) / len(z)
    zeilen.append((t, anteil, float(np.median([a["in_r"] for a in z]))))
anteile = [x[1] for x in zeilen]
print("  H-Anteil je Tag: Median %.1f %%, Spanne %.1f .. %.1f %%"
      % (100*st.median(anteile), 100*min(anteile), 100*max(anteile)))
print()
print("  %-22s %10s %14s" % ("H-Anteil des Tages", "Tage", "Median-Bewegung"))
grenzen = np.quantile(anteile, [0, 0.2, 0.4, 0.6, 0.8, 1.0])
for i in range(5):
    teil = [x for x in zeilen if grenzen[i] <= x[1] <= grenzen[i+1]]
    if teil:
        print("  %5.1f .. %5.1f %%        %10d %+13.4f R"
              % (100*grenzen[i], 100*grenzen[i+1], len(teil),
                 st.median([x[2] for x in teil])))
print()
r = np.corrcoef([x[1] for x in zeilen], [x[2] for x in zeilen])[0, 1]
print("  Zusammenhang H-Anteil <-> Tagesbewegung: r = %+.3f" % r)
# Bootstrap ueber Bloecke von Kalendertagen
d = {t: v for t, _a, v in zeilen}
hoch = {t: v for t, a, v in zeilen if a >= np.quantile(anteile, 0.8)}
tief = {t: v for t, a, v in zeilen if a <= np.quantile(anteile, 0.2)}
print("  Tage mit VIEL H : Median %+.4f R (%d Tage)"
      % (st.median(list(hoch.values())), len(hoch)))
print("  Tage mit WENIG H: Median %+.4f R (%d Tage)"
      % (st.median(list(tief.values())), len(tief)))
print("  Unterschied     : %+.4f R"
      % (st.median(list(hoch.values())) - st.median(list(tief.values()))))
print()
print("⚠️ Ein positiver Unterschied hiesse: H ist ein TAGES-Signal.")
print("   Es waere dann nicht wertlos, sondern an der falschen Stelle eingesetzt.")
