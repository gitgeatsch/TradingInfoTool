# -*- coding: utf-8 -*-
"""N8 GEGENPRUEFUNG (06.09.2026)

Die Rechnung galt fuer CRV 2,0. Drei Fragen:

  G1  HAENGT ES AM CRV?  Bei hoeherem CRV sind weniger Punkte noetig.
  G2  WELCHER CRV LAEUFT WIRKLICH?  Aus den Produktivsignalen.
  G3  WAS, WENN EIN MERKMAL FEHLT?  Dann greifen die Stufen nicht.
"""
from __future__ import annotations
import itertools
import sqlite3
import sys
import numpy as np
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, ".")
from agent import potential as P                             # noqa: E402
from agent import wahrscheinlichkeit as WK                   # noqa: E402


def main() -> int:
    sch = P.schwelle()
    bei = {b.merkmal: b.stufen for b in WK.BEITRAEGE if b.stufen}
    namen = list(bei)

    print("=" * 96)
    print("G1  HAENGT DAS ERGEBNIS AM CRV?")
    print("=" * 96)
    print("  %6s %9s %9s  %s" % ("CRV", "noetig", "durch/25",
                                 "welche turnover-Fuenftel kommen durch"))
    for crv in (1.5, 1.8, 2.0, 2.5, 3.0, 4.0):
        noetig = sch / ((1.0 + crv) / 100.0)
        durch = [(i, j) for i, j in itertools.product(range(5), range(5))
                 if bei[namen[0]][i] + bei[namen[1]][j] > noetig]
        tn = sorted({j for _i, j in durch})
        print("  %6.1f %9.2f %9d  %s"
              % (crv, noetig, len(durch),
                 tn if tn else "KEINES - gar nichts kommt durch"))
    print()
    print("  ⚠️ Nur wenn das niedrigste turnover-Fuenftel [0] die einzige")
    print("     Eintrittskarte bleibt, ist die Schwelle eine turnover-Sperre.")

    print()
    print("=" * 96)
    print("G2  WELCHER CRV LAEUFT WIRKLICH?  (aus den Produktivsignalen)")
    print("=" * 96)
    c = sqlite3.connect("data/tradinginfotool.db")
    sp = [r[0] for r in c.execute(
        "SELECT crv FROM signals WHERE crv IS NOT NULL AND crv > 0")] \
        if any(x[1] == "crv" for x in c.execute("PRAGMA table_info(signals)")) \
        else []
    if not sp:
        # CRV steht evtl. unter anderem Namen
        cols = [x[1] for x in c.execute("PRAGMA table_info(signals)")]
        kand = [k for k in cols if "crv" in k.lower() or "chance" in k.lower()]
        print("  Spalten mit CRV-Bezug in `signals`: %s" % (kand or "keine"))
        for k in kand:
            v = [r[0] for r in c.execute(
                "SELECT %s FROM signals WHERE %s IS NOT NULL" % (k, k))]
            if v:
                sp = [float(x) for x in v if isinstance(x, (int, float))]
                print("  aus %s: %d Werte" % (k, len(sp)))
                break
    if sp:
        a = np.array(sp, float)
        print("  %d Signale · Median %.2f · p10 %.2f · p90 %.2f · min %.2f "
              "· max %.2f" % (len(a), np.median(a), np.percentile(a, 10),
                              np.percentile(a, 90), a.min(), a.max()))
        for g in (2.0, 2.5, 3.0):
            print("    Anteil mit CRV >= %.1f : %5.1f %%"
                  % (g, 100 * float((a >= g).mean())))
    else:
        print("  ⚠️ kein CRV in `signals` gefunden - die Arithmetik bleibt")
        print("     damit auf die Bandbreite aus G1 angewiesen.")

    print()
    print("=" * 96)
    print("G3  WAS, WENN EIN MERKMAL FEHLT?")
    print("=" * 96)
    print("  Dann greift der Zustand 'fehlt' (N-15 C) statt einer Stufe -")
    print("  der Beitrag steuert NICHTS bei, also 0,00 Punkte.")
    for crv in (2.0, 3.0):
        noetig = sch / ((1.0 + crv) / 100.0)
        print("  CRV %.1f, noetig %+.2f:" % (crv, noetig))
        for lab, p in (("nur funding bestes, turnover FEHLT",
                        max(bei[namen[0]])),
                       ("nur turnover bestes, funding FEHLT",
                        max(bei[namen[1]])),
                       ("beide fehlen", 0.0)):
            w = (WK.basisrate(crv) + p / 100.0) * crv - (
                1.0 - (WK.basisrate(crv) + p / 100.0))
            print("    %-38s %+6.2f Pkt -> %+.4f R  %s"
                  % (lab, p, w, "DURCH" if w > sch else "-"))
    print()
    print("  ⚠️ Ein Wert ohne turnover-Rang kann die Schwelle NIE erreichen -")
    print("     unabhaengig davon, wie gut sein Funding ist.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
