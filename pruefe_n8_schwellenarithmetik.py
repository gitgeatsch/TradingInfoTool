# -*- coding: utf-8 -*-
"""N8 - WENDET EINE ODER-SPERRE `turnover` ZWEIMAL AN? (06.09.2026)

Der Verdacht aus 2.121: `turnover` ist bereits als REGLER am Mittel
registriert. Eine Sperre, die ihn benutzt, wendet ihn ein zweites Mal an.

⚠️ Diese Frage ist ohne neue Messung zu beantworten - sie steckt in der
Arithmetik der Bewertung. Genau deshalb wird sie hier durchgerechnet und
nicht geschaetzt.

    q      = basisrate(CRV) + punkte / 100
    wert_r = q * CRV - (1 - q)
    Gate:    wert_r > schwelle
"""
from __future__ import annotations
import itertools
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, ".")
from agent import potential as P                             # noqa: E402
from agent import wahrscheinlichkeit as WK                   # noqa: E402


def wert_r(punkte, crv):
    q = WK.basisrate(crv) + punkte / 100.0
    return q * crv - (1.0 - q)


def main() -> int:
    sch = P.schwelle()
    print("=" * 92)
    print("N8  DIE ARITHMETIK DER SCHWELLE")
    print("=" * 92)
    print("  Schwelle: %.4f R   (Vorgabe %.4f)" % (sch, P.SCHWELLE_VORGABE))
    for crv in (1.5, 2.0, 3.0):
        b = WK.basisrate(crv)
        # wert_r ist linear in punkte: wert_r = punkte/100 * (1 + crv)
        noetig = sch / ((1.0 + crv) / 100.0)
        print("  CRV %.1f · Basisrate %.4f · Potential ohne Beitraege %+.4f R"
              "  ->  noetige Punkte fuer die Schwelle: %+.2f"
              % (crv, b, wert_r(0.0, crv), noetig))
    print()
    print("  ⚠️ Ohne Beitraege ist das Potential exakt NULL - ein")
    print("     Barrierensystem auf driftfreiem Pfad. Alles, was durchkommt,")
    print("     kommt aus den Beitraegen.")

    bei = {b.merkmal: b.stufen for b in WK.BEITRAEGE if b.stufen}
    print()
    print("=" * 92)
    print("WELCHE KOMBINATION ERREICHT DIE SCHWELLE?  (CRV 2,0)")
    print("=" * 92)
    for m, st in bei.items():
        print("  %-20s %s" % (m, " · ".join("%+.2f" % x for x in st)))
    namen = list(bei)
    crv = 2.0
    noetig = sch / ((1.0 + crv) / 100.0)
    print()
    print("  benoetigt: %+.2f Punkte" % noetig)
    print()
    print("  %-10s %-10s %9s %10s  %s"
          % (namen[0][:9], namen[1][:9], "Punkte", "wert_r", "Gate"))
    durch = []
    for i, j in itertools.product(range(5), range(5)):
        p = bei[namen[0]][i] + bei[namen[1]][j]
        w = wert_r(p, crv)
        ok = w > sch
        if ok:
            durch.append((i, j))
        print("  Fuenftel %d Fuenftel %d %9.2f %+10.4f  %s"
              % (i, j, p, w, "DURCH" if ok else "-"))
    print()
    print("=" * 92)
    print("DAS ERGEBNIS")
    print("=" * 92)
    print("  Es kommen %d von 25 Kombinationen durch: %s"
          % (len(durch), ", ".join("(%d,%d)" % x for x in durch)))
    tn = sorted({j for _i, j in durch})
    fn = sorted({i for i, _j in durch})
    print("  benoetigte %s-Fuenftel: %s" % (namen[0], fn))
    print("  benoetigte %s-Fuenftel: %s" % (namen[1], tn))
    print()
    print("  ⚠️ FUENFTEL 0 IST DER NIEDRIGSTE ROHWERT - bei beiden Groessen")
    print("     ist niedrig das Gute.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
