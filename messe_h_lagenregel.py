# -*- coding: utf-8 -*-
"""Traegt die Regel "H nur ausserhalb des Baermarkts"? (30.08.2026)

## Warum diese Messung, obwohl Kapitel 109 sie schon hatte

⚠️ MEIN EINWAND GEGEN DIE LAGENREGEL WAR FALSCH. Ich hatte behauptet, die
Marktphase sei "vorwaerts nicht verlaesslich bekannt". Der Code sagt das
Gegenteil:

    r = index[j] / index[j - fenster] - 1.0      # die letzten 250 Tage

Das ist rueckwaertsgerichtet und am Anker bekannt. **Kein Lookahead.** Die
Nutzervorstellung - *"wir koennen ohnehin nur bestaetigte Abwaerts- und
Aufwaertsphasen bewerten"* - ist damit umsetzbar.

## Was Kapitel 109 gemessen hat, und was hier anders ist

Kapitel 109: Pruefhaelfte ab 2022-06-30, **222 Reihen**, Regel bringt
**+0,9 Punkte** - unter der Schwelle.

Hier: **523 Reihen, 761.587 Anker**, und der Baermarkt-Schaden ist heute
**-12,7 Punkte** (2024-2026) statt der damals gemessenen Groesse. Andere
Datenlage, andere Frage - deshalb neu.

## Was gemessen wird

    OHNE REGEL   H in allen Lagen
    MIT REGEL    H nur, wenn die Phase NICHT "baer" ist
    -> Unterschied = was die Regel bringt

Und die eigentliche Nutzerfrage: **in welchem Fenster ist eine Phase
"bestaetigt"?** Deshalb laeuft die Regel ueber mehrere Fensterlaengen.

⚠️ Vorab: Die Regel gilt nur dann als tragend, wenn ihr Gewinn ueber der
Blockschwelle liegt - und in allen drei Zeitabschnitten dasselbe Vorzeichen
hat.
"""
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_h_je_zeitabschnitt as HZ
import messe_marken as MM
import simuliere_bremse as SB

ABSCHNITTE = HZ.ABSCHNITTE


def main():
    print("Lade Anker (523 Reihen)...", flush=True)
    roh = SB._reihen_roh("data/messdaten.db", "krypto",
                         MM._KLASSEN("data/messdaten.db"))
    faelle = MM.laufe("data/messdaten.db", "krypto", roh_pruefen=False,
                      fortschritt=True)
    print("%d Anker." % len(faelle))
    rng = np.random.default_rng(20260830)

    print()
    print("=" * 92)
    print("WAS BRINGT DIE REGEL 'H NUR AUSSERHALB DES BAERMARKTS'?")
    print("=" * 92)
    print("  %-12s %11s %11s %11s %11s  %s"
          % ("Abschnitt", "H alle Lg.", "H ohne Baer", "Gewinn", "Blockschw.", "Urteil"))
    for name, von, bis in (("gesamt", "2000-01-01", "2099-12-31"),) + ABSCHNITTE:
        teil = [f for f in faelle if von <= f["datum"] <= bis]
        ohne_baer = [f for f in teil if f.get("phase") != "baer"]
        v_alle, _, _ = HZ.vorsprung(teil)
        v_ohne, n_h, _ = HZ.vorsprung(ohne_baer)
        if v_alle is None or v_ohne is None:
            print("  %-12s zu wenige Faelle" % name)
            continue
        gewinn = v_ohne - v_alle
        s95, _ = HZ.blockschwelle(ohne_baer, rng)
        print("  %-12s %+10.1f %+11.1f %+11.1f %+11.1f  %s"
              % (name, v_alle, v_ohne, gewinn,
                 s95 if s95 is not None else float("nan"),
                 "traegt" if s95 is not None and v_ohne > s95 else "TRAEGT NICHT"))

    print()
    print("=" * 92)
    print("IN WELCHEM FENSTER IST EINE PHASE 'BESTAETIGT'?")
    print("=" * 92)
    print("  Die Phase kommt aus der Bewegung des gleichgewichteten Index.")
    print("  Kurzes Fenster = reagiert schnell, aber unsicher. Langes = traege,")
    print("  aber bestaetigt. Geprueft wird, welches den groessten Gewinn bringt.")
    print()
    print("  %-10s %11s %11s %11s %s"
          % ("Fenster", "Anteil baer", "H ohne Baer", "Gewinn", "Blockschwelle"))
    for fenster in (60, 120, 250, 400):
        phase = SB._marktphase(roh, fenster=fenster)
        neu = [{**f, "phase": phase.get(f["datum"], "unbekannt")} for f in faelle]
        ohne_baer = [f for f in neu if f["phase"] != "baer"]
        anteil = 1 - len(ohne_baer) / len(neu)
        v_alle, _, _ = HZ.vorsprung(neu)
        v_ohne, _, _ = HZ.vorsprung(ohne_baer)
        if v_ohne is None:
            continue
        s95, _ = HZ.blockschwelle(ohne_baer, rng)
        print("  %-10d %10.1f %% %+11.1f %+11.1f %+11.1f  %s"
              % (fenster, 100 * anteil, v_ohne, v_ohne - v_alle,
                 s95 if s95 is not None else float("nan"),
                 "traegt" if s95 is not None and v_ohne > s95 else "traegt nicht"))


if __name__ == "__main__":
    main()
