# -*- coding: utf-8 -*-
"""N-84 — die TRENNSCHAERFE gegen denselben Massstab wie das Urteil (08.09.)

## Der Widerspruch, im Klartext

`turnover` auf `frei`, Urteil woertlich:

    "Wirkung +0,0639 ueber der Trennschaerfe 0,0500 R, aber ..."

Die **Trennschaerfe** entsteht aus `pb["unten"] > 0` - gegen NULL.
Das **Urteil** faellt aus `unten > max(0, null_oben)` - gegen 0,0220.
**Zwei Massstaebe in einem Satz.** Ein Kandidat kann laut Trennschaerfe
gross genug sein und trotzdem kein TRAEGT erreichen.

## Warum das VOR einer Abwertung geklaert gehoert

Nutzervorgabe, stehend: *"bevor eine Bewertung fällt müssen wir alles
unternehmen - was ist der Grund und dass wir eine Lösung finden."*

`turnover` steht genau an dieser Kante. Faellt er, dann bitte nach einem
Massstab, der sich nicht selbst widerspricht.

## Was gemessen wird

Jeder der vier Faelle auf `frei` **und** auf den selektierten Mengen,
unter der stabilen Nullregel (40 Ziehungen, p90), einmal mit der alten
und einmal mit der gleichgezogenen Trennschaerfe.

## Die Vorhersage, VOR dem Lauf

    Die Trennschaerfe wird SCHLECHTER (groesser oder None) - die Latte
    liegt hoeher. Das URTEIL selbst aendert sich dadurch NICHT, denn
    `traegt` haengt nicht an der Trennschaerfe. Was sich aendert, ist
    die BEGRUENDUNG: aus "traegt nicht bis 0,05" wird ehrlicher
    "nicht trennbar" oder "kein Befund".

⚠️ Aendert sich ein `traegt`, habe ich etwas uebersehen - dann ist die
Aenderung nicht das, wofuer ich sie halte.

    python n84_trennschaerfe_massstab.py
"""
from __future__ import annotations

import sys
import time

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_eigenschaft_beitrag as B                        # noqa: E402
import messe_kandidaten_als_regel as K                       # noqa: E402
import messnorm as N                                          # noqa: E402
import messnorm_auswahl as MA                                # noqa: E402
from messe_alle_kandidaten import HORIZONT, zusatzquellen    # noqa: E402
from messe_beitrag_auf_auswahl import momentum250            # noqa: E402
from n82_beitragslage_beide_nullregeln import (NULL_PERZENTIL,  # noqa: E402
                                               NULL_ZIEHUNGEN)

FAELLE = (("turnover", ("frei", "50%")), ("funding", ("frei", "50%")),
          ("schnitt", ("frei", "10%", "20%")), ("zufall", ("frei", "20%")))


def main() -> int:
    t0 = time.time()
    reihen = B.lade()
    mom = momentum250(reihen)
    lage = N.Lage(instrument="spot", strategie="einstieg")
    zus = zusatzquellen()
    print("=" * 108)
    print("N-84 — Trennschaerfe gegen NULL (alt) vs. gegen `null_oben` (neu)")
    print("=" * 108)
    print("  Nullregel in BEIDEN Spalten stabil (%d Ziehungen, p%.0f) -"
          % (NULL_ZIEHUNGEN, NULL_PERZENTIL))
    print("  es aendert sich NUR der Massstab der Trennschaerfe.")
    print()
    print("  %-10s %-5s %9s %9s %9s %9s   %-24s %s"
          % ("Kandidat", "Menge", "Wirkung", "Band u.", "null_ob", "Tsch.",
             "Urteil alt", "Urteil neu"))
    kippt = []
    for a, mengen in FAELLE:
        je = K.baue(reihen, a, zus.get(a), horizont=HORIZONT)
        for m in mengen:
            try:
                ba = MA.pruefe_auswahl(a, je, mom, lage=lage, menge=m,
                                       rng=np.random.default_rng(20260908),
                                       horizont=HORIZONT, hypothese="N-84",
                                       verwendung="Beitrag",
                                       null_ziehungen=NULL_ZIEHUNGEN,
                                       null_perzentil=NULL_PERZENTIL)
                bn = MA.pruefe_auswahl(a, je, mom, lage=lage, menge=m,
                                       rng=np.random.default_rng(20260908),
                                       horizont=HORIZONT, hypothese="N-84",
                                       verwendung="Beitrag",
                                       null_ziehungen=NULL_ZIEHUNGEN,
                                       null_perzentil=NULL_PERZENTIL,
                                       trennschaerfe_gegen_nullpunkt=True)
            except Exception as exc:                         # noqa: BLE001
                print("  %-10s %-5s -> %s" % (a, m, str(exc)[:50]))
                continue
            if ba.traegt != bn.traegt:
                kippt.append((a, m))
            print("  %-10s %-5s %+9.4f %+9.4f %+9.4f %5s->%-5s %-24s %s"
                  % (a, m, ba.wirkung, ba.unten, ba.null_oben,
                     ba.trennschaerfe, bn.trennschaerfe,
                     ba.urteil.split(" (")[0].split(" - ")[0][:24],
                     bn.urteil.split(" (")[0].split(" - ")[0][:30]),
                  flush=True)
    print()
    if kippt:
        print("  ⚠️⚠️ Ein `traegt` hat sich geaendert: %s" % kippt)
        print("     Die Vorhersage war FALSCH - die Aenderung tut mehr,")
        print("     als ich angenommen habe. Nicht uebernehmen.")
    else:
        print("  ✔ Kein einziges `traegt` hat sich geaendert - wie")
        print("    vorhergesagt. Es aendert sich nur die BEGRUENDUNG.")
    print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
