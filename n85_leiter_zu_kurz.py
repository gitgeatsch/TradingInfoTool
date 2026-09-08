# -*- coding: utf-8 -*-
"""N-85 — die LEITER der gepflanzten Staerken endet zu frueh (08.09.2026)

## Der Fund aus N-84

Mit gleichgezogener Trennschaerfe kippen Urteile auf "KEIN BEFUND -
untermaechtig: selbst +0,10 R gepflanzt wurde nicht gefunden":

    schnitt 20 %   Wirkung +0,1858   traegt = TRUE   ->  "KEIN BEFUND"

⚠️ **Der eigene Effekt ist fast doppelt so gross wie die groesste
gepflanzte Stufe.** Das ist keine Aussage ueber die Anlage, sondern
darueber, dass die Leiter zu kurz ist.

## ⚠️ Und ein Ordnungsfehler in `messnorm.urteil`

    if self.trennschaerfe is None:      return "KEIN BEFUND ..."
    ...
    if self.traegt:                      return "TRAEGT"

Die None-Abfrage steht VOR `traegt`. Ein echtes TRAEGT wird dadurch
verdeckt. `Befund.traegt` selbst bleibt korrekt - nur der ausgegebene
Satz widerspricht ihm.

## Der eigene Bestand widerspricht sich hier ohnehin

    messnorm.py / messnorm_auswahl.py    (0.02, 0.05, 0.10)
    messnorm_rand.py                     (0.02, 0.05, 0.10, 0.20)

Die laengere Leiter ist im Projekt bereits in Gebrauch.

## Was gemessen wird

Dieselben Faelle wie N-84, stabile Nullregel, Trennschaerfe gegen
`null_oben` - einmal mit der kurzen und einmal mit der Leiter
(0,02 · 0,05 · 0,10 · 0,20 · 0,40).

## Die Vorhersage, VOR dem Lauf

    `traegt` aendert sich NIRGENDS - die Leiter beruehrt es nicht.
    Wo die Wirkung ueber 0,10 liegt (schnitt 10 % und 20 %), findet
    die laengere Leiter eine Trennschaerfe, und "KEIN BEFUND" wird
    wieder zu "TRAEGT".
    Wo die Wirkung klein ist (turnover +0,064, funding 50 % +0,031),
    hilft die laengere Leiter NICHT - dort ist die Anlage wirklich zu
    grob, und "KEIN BEFUND" bleibt die richtige Antwort.

⚠️ Genau der zweite Teil ist die Probe: waere die lange Leiter ein
Freibrief, wuerde sie auch dort etwas finden.

    python n85_leiter_zu_kurz.py
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

KURZ = (0.02, 0.05, 0.10)
LANG = (0.02, 0.05, 0.10, 0.20, 0.40)
FAELLE = (("schnitt", ("10%", "20%")), ("turnover", ("frei", "50%")),
          ("funding", ("frei", "50%")), ("zufall", ("frei", "20%")))


def main() -> int:
    t0 = time.time()
    reihen = B.lade()
    mom = momentum250(reihen)
    lage = N.Lage(instrument="spot", strategie="einstieg")
    zus = zusatzquellen()
    print("=" * 108)
    print("N-85 — kurze Leiter (bis 0,10) gegen lange (bis 0,40)")
    print("=" * 108)
    print("  Nullregel stabil · Trennschaerfe gegen `null_oben` in BEIDEN")
    print()
    print("  %-10s %-5s %9s %8s %12s   %-26s %s"
          % ("Kandidat", "Menge", "Wirkung", "traegt", "Tsch. k->l",
             "Urteil kurze Leiter", "Urteil lange Leiter"))
    fehler = []
    for a, mengen in FAELLE:
        je = K.baue(reihen, a, zus.get(a), horizont=HORIZONT)
        for m in mengen:
            g = dict(lage=lage, menge=m, horizont=HORIZONT, hypothese="N-85",
                     verwendung="Beitrag", null_ziehungen=NULL_ZIEHUNGEN,
                     null_perzentil=NULL_PERZENTIL,
                     trennschaerfe_gegen_nullpunkt=True)
            try:
                bk = MA.pruefe_auswahl(a, je, mom,
                                       rng=np.random.default_rng(20260908),
                                       staerken=KURZ, **g)
                bl = MA.pruefe_auswahl(a, je, mom,
                                       rng=np.random.default_rng(20260908),
                                       staerken=LANG, **g)
            except Exception as exc:                         # noqa: BLE001
                print("  %-10s %-5s -> %s" % (a, m, str(exc)[:50]))
                continue
            if bk.traegt != bl.traegt:
                fehler.append((a, m))
            print("  %-10s %-5s %+9.4f %8s %5s->%-6s %-26s %s"
                  % (a, m, bk.wirkung, str(bk.traegt),
                     bk.trennschaerfe, bl.trennschaerfe,
                     bk.urteil.split(" (")[0].split(" - ")[0][:26],
                     bl.urteil.split(" (")[0].split(" - ")[0][:32]),
                  flush=True)
    print()
    if fehler:
        print("  ⚠️⚠️ `traegt` hat sich geaendert bei %s - die Leiter tut"
              % fehler)
        print("     mehr als angenommen. NICHT uebernehmen.")
    else:
        print("  ✔ `traegt` unveraendert - die Leiter beruehrt nur die")
        print("    BEGRUENDUNG, wie vorhergesagt.")
    print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
