# -*- coding: utf-8 -*-
"""Schwellen-Kalibrierung, richtig: gegen den QUOTENGLEICHEN Zufall.

## Warum der erste Anlauf falsch war

Er verglich den Median der Verbliebenen mit dem Median ALLER. Das misst zwei
Dinge zugleich: die Auswahl UND den Selektionseffekt. Je mehr man sperrt,
desto groesser scheint der Vorsprung - auch bei Zufall. Die Zufallsprobe
belegte es: bester Zufallswert +0,3416 gegen gemessene +0,2104.

⚠️ Der Fehler hat einen Namen im Projekt: "der Vergleich muss die QUOTE
festhalten" (Tagewahl-Befund 23.08.). Genau dieselbe Falle.

## Die richtige Konstruktion

Fuer jede Schwelle wird eine ZUFALLSAUSWAHL DERSELBEN GROESSE gezogen:

    echt    Median der Anker mit Potential ueber der Schwelle
    zufall  Median gleich vieler, zufaellig gezogener Anker desselben Tages
    -> die Differenz ist die Auswahlleistung, ohne Selektionseffekt

Bootstrap ueber Bloecke von Kalendertagen (Block > Horizont).
"""
import statistics as st
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_bewertungskennzahl as MB
import messe_schwelle_kalibrierung as SK

ZIEHUNGEN = 30


def main():
    je_tag = SK.bewerte(SK.baue())
    alle = [x for z in je_tag.values() for x in z]
    rng = np.random.default_rng(20260830)
    print("=" * 90)
    print("SCHWELLE gegen den QUOTENGLEICHEN ZUFALL")
    print("=" * 90)
    print("%d Anker, %d Kalendertage" % (len(alle), len(je_tag)))
    print()
    print("  %-9s %10s   %s" % ("Schwelle", "Durchlass", "echt minus quotengleicher Zufall"))
    for s in SK.SCHWELLEN:
        d = {}
        for tag, z in je_tag.items():
            y = np.array([x["in_r"] for x in z])
            maske = np.array([x["potential"] > s for x in z])
            k = int(maske.sum())
            if k < 3 or k >= len(z):
                continue
            echt = float(np.median(y[maske]))
            zufall = float(np.mean([
                np.median(y[rng.choice(len(y), k, replace=False)])
                for _ in range(ZIEHUNGEN)]))
            d[tag] = echt - zufall
        if len(d) < 100:
            print("  %-9.3f %9s   zu wenige Tage"
                  % (s, "%.1f %%" % (100 * sum(1 for x in alle
                                               if x["potential"] > s) / len(alle))))
            continue
        durch = 100 * sum(1 for x in alle if x["potential"] > s) / len(alle)
        print("  %-9.3f %8.1f %%  " % (s, durch), end="")
        MB.urteil_tage("", d, rng, 250)


if __name__ == "__main__":
    main()
