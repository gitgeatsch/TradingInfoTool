# -*- coding: utf-8 -*-
"""N-45: Sind die vier Kandidaten UNTEREINANDER unabhaengig? (05.09.2026)

## Warum das jetzt kommt

N-43 und N-44 haben vier Groessen gefunden, die Abdeckung UND Stabilitaet
erfuellen - alle aus reinen Kursdaten, alle 100 % gedeckt:

    vola       +0,647      schnitt50  +0,553
    schnitt    +0,613      amihud     +0,473
                           (Rauschgrenze +0,160)

Beide REGISTRIERTEN Beitraege liegen darunter: funding +0,180, turnover
+0,113.

⚠️ **Einzeln zu tragen heisst nicht, gemeinsam etwas beizutragen.**
`schnitt` und `schnitt50` sind beide Abstandsmasse zu einem gleitenden
Durchschnitt - sehr wahrscheinlich dieselbe Groesse in zwei Faerbungen.
`amihud` (Illiquiditaet) haengt plausibel mit `vola` zusammen. Vier
Kandidaten, die einzeln tragen, koennen zusammen EIN Beitrag sein.

Genau davor warnt die stehende Vorgabe, Indikatoren auch in KOMBINATION zu
pruefen - vorab benannt, nicht frei durchsucht.

## Zwei Messungen

    1  UEBERLAPPUNG   Korrelation der Fuenftel, paarweise ueber alle
                      gemeinsamen (Tag, Symbol). Eine Matrix, keine
                      Einzelzahl - sonst sieht man Gruppen nicht.

    2  REGEL 3        Fuenftel je Symbol aus der EIGENEN Vergangenheit,
                      nachlaufend. Trennt die Groesse auch INNERHALB eines
                      Symbols ueber die Zeit, oder rangiert sie nur Assets?

⚠️ `zufall` laeuft in beiden mit. In der Matrix muss es ueberall bei null
liegen, laengs darf es nichts ordnen.

    python pruefe_kandidaten_untereinander.py
"""
from __future__ import annotations

import sys
from collections import defaultdict

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_eigenschaft_beitrag as B                       # noqa: E402
import messe_funding_niveau as F                            # noqa: E402
import messe_kandidaten_als_regel as K                      # noqa: E402
import messe_zielregel as ZR                                # noqa: E402
from messe_bewertung_kalibrierung import _fuenftel_je_tag   # noqa: E402
from messe_stufen_aus_quote import quote_je_fuenftel        # noqa: E402
# ⚠️ IMPORTIERT, NICHT NACHGEBAUT - dieselbe Rechnung wie in N-43c.
from pruefe_vola_zeitpunkt_oder_asset import (              # noqa: E402
    laengs_fuenftel, _als_reihen)

ARTEN = ("vola", "schnitt", "schnitt50", "amihud", "rsi", "funding", "zufall")
OHNE_QUELLE = ("vola", "schnitt", "schnitt50", "amihud", "rsi", "zufall")
MIND_LAENGS = 2000


def main() -> int:
    print("Lade Reihen...", flush=True)
    reihen = B.lade()
    tage_je_sym = {s: [z[0] for z in roh] for s, roh in reihen.items()}
    zeilen = ZR.ergebnisse(reihen)
    print("  %d Anker · %d Reihen" % (len(zeilen), len(reihen)))

    funding = F.lade_funding()
    gebaut, quer = {}, {}
    for art in ARTEN:
        print("  baue %s ..." % art, flush=True)
        q = None if art in OHNE_QUELLE else funding
        gebaut[art] = K.baue(reihen, art, q, horizont=20)
        quer[art] = _fuenftel_je_tag(gebaut[art])

    # ---- 1. Ueberlappungsmatrix -------------------------------------
    print()
    print("=" * 92)
    print("1. UEBERLAPPUNG — Korrelation der Fuenftel, paarweise")
    print("=" * 92)
    print("     %s" % " ".join("%9s" % a[:9] for a in ARTEN))
    for a in ARTEN:
        zeile = []
        for b in ARTEN:
            if a == b:
                zeile.append("        -")
                continue
            xs, ys = [], []
            for tag, da in quer[a].items():
                db = quer[b].get(tag)
                if not db:
                    continue
                for sym, v in da.items():
                    w = db.get(sym)
                    if w is not None:
                        xs.append(v)
                        ys.append(w)
            if len(xs) < 1000:
                zeile.append("        .")
            else:
                r = float(np.corrcoef(np.array(xs, float),
                                      np.array(ys, float))[0, 1])
                zeile.append("%9.3f" % r)
        print("  %-9s %s" % (a[:9], " ".join(zeile)))
    print()
    print("  ⚠️ |r| ueber 0,35 heisst: die beiden messen weitgehend dasselbe.")
    print("     Aus so einer Gruppe gehoert EINE Groesse in die Bewertung,")
    print("     nicht mehrere - sonst zaehlt dasselbe Urteil doppelt.")

    # ---- 2. Regel 3, laengs -----------------------------------------
    print()
    print("=" * 92)
    print("2. REGEL 3 — trennt die Groesse LAENGS, im eigenen Symbol?")
    print("=" * 92)
    print("  %-11s %-34s %8s %8s" % ("Groesse", "Quote je eigenem Fuenftel",
                                     "Spanne", "monoton"))
    for art in ARTEN:
        if art == "funding":
            continue                      # laengs nicht sinnvoll gedeckt
        werte = _als_reihen(gebaut[art], tage_je_sym)
        f5 = laengs_fuenftel(werte, tage_je_sym)
        je = quote_je_fuenftel(zeilen, tage_je_sym, f5)
        if not je or any(je.get(f, (0, 0))[1] < MIND_LAENGS for f in range(5)):
            n = min((je.get(f, (0, 0))[1] for f in range(5)), default=0)
            print("  %-11s zu duenn (n_min %d)" % (art, n))
            continue
        q = [100.0 * je[f][0] / je[f][1] for f in range(5)]
        mon = (all(q[i] >= q[i + 1] for i in range(4))
               or all(q[i] <= q[i + 1] for i in range(4)))
        print("  %-11s %-34s %7.2f %8s"
              % (art, " ".join("%.1f" % x for x in q), max(q) - min(q),
                 "ja" if mon else "nein"))
    print()
    print("  ⚠️ `zufall` ist der Massstab: was seine Spanne nicht deutlich")
    print("     uebersteigt, ist keine Zeitpunkt-Aussage.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
