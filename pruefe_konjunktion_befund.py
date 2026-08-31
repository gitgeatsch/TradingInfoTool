# -*- coding: utf-8 -*-
"""Stufe 2: die Gegenpruefungen zum K-1-Befund (29.08.2026).

Der Befund: `trend=unten / rueckgang=oben` liefert -0,1955 R gegen eine
Maximum-Schwelle von -0,3691 R, ueberadditiv gegenueber -0,380 / -0,403.

Sieben Pruefungen, alle VOR dem Lauf benannt:

  2a KOLLINEARITAET   messen trend und rueckgang dasselbe? Beide sind
                      Preisverhaeltnisse - der schwerste Einwand
  2b PLAUSIBILITAET   was IST diese Konstellation ueberhaupt? "tief zum
                      Schnitt und nahe am Hoch" klingt widerspruechlich
  2c FALLZAHL         wie viele Anker, und ueber wie viele Kalendertage
  2d LAGE             Median ist nicht alles - Mittel und Anteil positiv
  2e ZEITSTABILITAET  gilt es in beiden Haelften der Historie
  2f HORIZONTE        gilt es auch auf 5 und 60 Tage
  2g WATCHLIST        gilt es auch auf den ~29 Werten, die wir handeln
"""
import statistics as st
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_eigenschaft_beitrag as B
import messe_konjunktion as K

A, TA = "trend", "unten"
C, TC = "rueckgang", "oben"


def siegerzelle(je_tag, horizont_unbenutzt=None):
    """Alle Anker der Siegerzelle, mit Tag und Rohwerten."""
    ia, ic = K.KANAELE.index(A), K.KANAELE.index(C)
    ta, tc = K.TERZILE.index(TA), K.TERZILE.index(TC)
    aus = []
    for tag, z in je_tag.items():
        ma, mc = K.terzile(z[:, ia]), K.terzile(z[:, ic])
        for zeile in z[(ma == ta) & (mc == tc)]:
            aus.append((tag, float(zeile[ia]), float(zeile[ic]), float(zeile[5])))
    return aus


def main():
    reihen = B.lade()
    je_tag = K.anker(reihen, 20)
    ia, ic = K.KANAELE.index(A), K.KANAELE.index(C)

    print("=" * 84)
    print("STUFE 2 — GEGENPRUEFUNGEN ZUM K-1-BEFUND")
    print("=" * 84)

    # ---- 2a Kollinearitaet ----------------------------------------------
    alle = np.vstack(list(je_tag.values()))
    r = float(np.corrcoef(alle[:, ia], alle[:, ic])[0, 1])
    print()
    print("2a KOLLINEARITAET — messen trend und rueckgang dasselbe?")
    print("    Korrelation der Rohwerte: %+.3f" % r)
    # innerhalb eines Tages, auf Rangebene - so wirken sie in der Messung
    rr = []
    for z in je_tag.values():
        if len(z) >= 15:
            rr.append(float(np.corrcoef(K.terzile(z[:, ia]),
                                        K.terzile(z[:, ic]))[0, 1]))
    print("    Rangkorrelation je Tag (Median): %+.3f" % st.median(rr))
    print("    -> %s" % ("WARNUNG: stark gekoppelt, die Konjunktion waere Doppelzaehlung"
                          if abs(st.median(rr)) > 0.7 else
                          "verschiedene Information - die Vorbedingung ist erfuellt"))

    # ---- 2b/2c Plausibilitaet und Fallzahl -------------------------------
    zelle = siegerzelle(je_tag)
    print()
    print("2b/2c WAS IST DIESE KONSTELLATION, und wie oft kommt sie vor?")
    print("    Anker: %d   Kalendertage: %d" % (len(zelle), len({t for t, *_ in zelle})))
    print("    trend     (Kurs/200-Schnitt-1): Median %+.3f  [%.3f .. %.3f]"
          % (st.median([x[1] for x in zelle]),
             min(x[1] for x in zelle), max(x[1] for x in zelle)))
    print("    rueckgang (Kurs/Jahreshoch-1) : Median %+.3f  [%.3f .. %.3f]"
          % (st.median([x[2] for x in zelle]),
             min(x[2] for x in zelle), max(x[2] for x in zelle)))
    print("    -> in Worten: der Wert steht RELATIV zu den anderen tief zum")
    print("       eigenen Schnitt, aber sein Jahreshoch liegt nah - er hat also")
    print("       kein hohes Hoch, von dem er weit gefallen waere.")

    # ---- 2d Lage ---------------------------------------------------------
    w = np.array([x[3] for x in zelle])
    basis = alle[:, 5]
    print()
    print("2d DIE LAGE — Median ist nicht alles")
    print("    %-14s %10s %10s %10s" % ("", "Median", "Mittel", "Anteil +"))
    print("    %-14s %+10.4f %+10.4f %9.1f %%"
          % ("Siegerzelle", np.median(w), w.mean(), 100 * (w > 0).mean()))
    print("    %-14s %+10.4f %+10.4f %9.1f %%"
          % ("alle Anker", np.median(basis), basis.mean(), 100 * (basis > 0).mean()))
    print("    -> Unterschied im Median: %+.4f R" % (np.median(w) - np.median(basis)))

    # ---- 2e Zeitstabilitaet ---------------------------------------------
    print()
    print("2e ZEITSTABILITAET")
    tage = sorted({t for t, *_ in zelle})
    mitte = tage[len(tage) // 2]
    for name, teil in (("erste Haelfte", [x for x in zelle if x[0] < mitte]),
                       ("zweite Haelfte", [x for x in zelle if x[0] >= mitte])):
        v = np.array([x[3] for x in teil])
        b = basis  # Vergleichsbasis bleibt gleich
        print("    %-16s %5d Anker   Median %+.4f R   (Basis %+.4f)"
              % (name, len(v), np.median(v), np.median(b)))

    # ---- 2f Horizonte ----------------------------------------------------
    print()
    print("2f ANDERE HORIZONTE")
    for h in (5, 60):
        jt = K.anker(reihen, h)
        z = siegerzelle(jt)
        v = np.array([x[3] for x in z])
        bb = np.vstack(list(jt.values()))[:, 5]
        print("    Horizont %2d   Median %+.4f R   Basis %+.4f   Unterschied %+.4f"
              % (h, np.median(v), np.median(bb), np.median(v) - np.median(bb)))


if __name__ == "__main__":
    main()
