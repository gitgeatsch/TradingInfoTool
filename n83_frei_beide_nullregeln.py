# -*- coding: utf-8 -*-
"""N-83 — R-R11: die ORIGINALBASIS von `funding` und `turnover` (08.09.)

## Warum dieser Lauf noetig ist

N-82 hat 16 Kandidaten auf den SELEKTIERTEN Mengen gemessen und dabei
`funding` von TRAEGT auf NICHT ENTSCHEIDBAR gebracht.

⚠️⚠️ **Das reproduziert den Originalbefund NICHT.** `funding` wurde am
30.08.2026 mit +0,137 R auf dem **Querschnitt aller Symbole je
Kalendertag** gemessen - das ist die Menge `frei`. Die Mengen-Systematik
gab es damals noch nicht.

> **R-R11:** Ein registrierter Befund darf nur von einer Messung
> umgestossen werden, die ihn ZUERST reproduziert. Wer die Basis aendert
> und ein anderes Ergebnis bekommt, hat nichts widerlegt.

Also wird hier die **Originalbasis** gemessen - `frei` - und zwar
wieder unter beiden Nullregeln. `turnover` laeuft mit, weil er im
selben Zustand ist (traegt auf `frei`, nicht auf den selektierten).

## Was welcher Ausgang bedeutet

    frei traegt unter BEIDEN      der Originalbefund steht; er ist eine
                                  MARKT-Aussage (P6), keine Beitragsaussage
    frei kippt mit der neuen      dann war auch der Originalbefund ein
    Regel                         Artefakt der fuenf Ziehungen

⚠️ Nur der zweite Ausgang widerlegt etwas. Der erste praezisiert nur,
WO der Befund gilt.

    python n83_frei_beide_nullregeln.py
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

FAELLE = ("funding", "turnover", "schnitt", "zufall")


def main() -> int:
    t0 = time.time()
    reihen = B.lade()
    mom = momentum250(reihen)
    lage = N.Lage(instrument="spot", strategie="einstieg")
    zus = zusatzquellen()
    print("=" * 104)
    print("N-83 — R-R11: die Originalbasis `frei`, unter BEIDEN Nullregeln")
    print("=" * 104)
    print("  ⚠️ `frei` beantwortet die MARKT-Frage (P6), nicht die")
    print("     Beitragsfrage - das gilt unabhaengig vom Ausgang.")
    print()
    print("  %-12s %10s %20s %10s %10s %9s %9s  %s"
          % ("Kandidat", "Wirkung", "Band", "null alt", "null neu",
             "Abst.alt", "Abst.neu", "alt->neu"))
    for a in FAELLE:
        je = K.baue(reihen, a, zus.get(a), horizont=HORIZONT)
        if not je:
            print("  %-12s leere Welt" % a)
            continue
        try:
            ba = MA.pruefe_auswahl(a, je, mom, lage=lage, menge="frei",
                                   rng=np.random.default_rng(20260908),
                                   horizont=HORIZONT,
                                   hypothese="N-83 Originalbasis",
                                   verwendung="Markt")
            bn = MA.pruefe_auswahl(a, je, mom, lage=lage, menge="frei",
                                   rng=np.random.default_rng(20260908),
                                   horizont=HORIZONT,
                                   hypothese="N-83 Originalbasis",
                                   verwendung="Markt",
                                   null_ziehungen=NULL_ZIEHUNGEN,
                                   null_perzentil=NULL_PERZENTIL)
        except Exception as exc:                             # noqa: BLE001
            print("  %-12s -> %s" % (a, str(exc)[:60]))
            continue
        wa = "T" if ba.traegt else "-"
        wn = "T" if bn.traegt else "-"
        print("  %-12s %+10.4f [%+.4f..%+.4f] %+10.4f %+10.4f %+9.4f %+9.4f  "
              "%s->%s%s"
              % (a, ba.wirkung, ba.unten, ba.oben, ba.null_oben, bn.null_oben,
                 ba.unten - max(0.0, ba.null_oben),
                 bn.unten - max(0.0, bn.null_oben), wa, wn,
                 "" if wa == wn else "   ⚠️ KIPPT"), flush=True)
        print("       %d Anker · %d Symbole · %d Bloecke · Trennschaerfe %s"
              % (ba.n_anker, ba.abdeckung_symbole, ba.n_bloecke,
                 ba.trennschaerfe))
        print("       alt: %s" % ba.urteil.split(" (")[0][:70])
        print("       neu: %s" % bn.urteil.split(" (")[0][:70])
    print()
    print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
