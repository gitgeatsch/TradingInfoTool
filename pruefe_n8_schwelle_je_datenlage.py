# -*- coding: utf-8 -*-
"""N8 NEU - mit der SCHWELLE JE DATENLAGE (06.09.2026)

⚠️ Die erste Fassung rechnete gegen `potential.schwelle()` - die FESTE
Vorgabe 0,080. Das laufende Tor benutzt `Potential.schwelle`, einen ANTEIL
der bei DIESER Datenlage erreichbaren Spanne. Der Unterschied ist genau der
Befund, den das Projekt am 31.08. selbst gemacht und behoben hat.

Daraus folgte faelschlich "88 % der Werte koennen die Schwelle nie
erreichen". Das ist widerlegt. Hier die richtige Rechnung.
"""
from __future__ import annotations
import itertools
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, ".")
from agent import potential as P                             # noqa: E402
from agent import wahrscheinlichkeit as WK                   # noqa: E402

CRV = 2.0


def w_r(p):
    q = WK.basisrate(CRV) + p / 100.0
    return q * CRV - (1.0 - q)


def main() -> int:
    bei = {b.name: b.stufen for b in WK.BEITRAEGE if b.stufen}
    namen = list(bei)
    fu_max, tu_max = max(bei[namen[0]]), max(bei[namen[1]])
    voll = w_r(fu_max + tu_max)
    anteil = P.SCHWELLE_VORGABE / voll
    print("=" * 96)
    print("DIE SCHWELLE IST EIN ANTEIL DER ERREICHBAREN SPANNE")
    print("=" * 96)
    print("  erreichbar bei VOLLER Datenlage : %+.4f R" % voll)
    print("  Vorgabe                          : %+.4f R" % P.SCHWELLE_VORGABE)
    print("  -> der Anteil                    : %.1f %%" % (100 * anteil))

    print()
    print("=" * 96)
    print("FALL A — Wert MIT beiden Raengen (7 von 57 im Betrieb)")
    print("=" * 96)
    s_a = anteil * voll
    print("  erreichbar %+.4f R · Schwelle %+.4f R · noetige Punkte %+.2f"
          % (voll, s_a, s_a / 0.03))
    durch_a = [(i, j) for i, j in itertools.product(range(5), range(5))
               if w_r(bei[namen[0]][i] + bei[namen[1]][j]) > s_a]
    print("  es kommen %d von 25 Kombinationen durch: %s"
          % (len(durch_a), ", ".join("(%d,%d)" % x for x in durch_a)))
    print("  benoetigte turnover-Fuenftel: %s"
          % sorted({j for _i, j in durch_a}))

    print()
    print("=" * 96)
    print("FALL B — Wert NUR mit Funding-Rang (36 von 57 im Betrieb)")
    print("=" * 96)
    voll_b = w_r(fu_max)
    s_b = anteil * voll_b
    print("  erreichbar %+.4f R · Schwelle %+.4f R · noetige Punkte %+.2f"
          % (voll_b, s_b, s_b / 0.03))
    durch_b = [i for i in range(5) if w_r(bei[namen[0]][i]) > s_b]
    print("  es kommen %d von 5 Fuenfteln durch: %s  (%.0f %%)"
          % (len(durch_b), durch_b, 100 * len(durch_b) / 5))

    print()
    print("=" * 96)
    print("DAS ERGEBNIS — und es kehrt die erste Fassung UM")
    print("=" * 96)
    print("  Fall A (beide Raenge) : %2d von 25 = %.0f %% kommen durch"
          % (len(durch_a), 100 * len(durch_a) / 25))
    print("  Fall B (nur Funding)  : %2d von  5 = %.0f %% kommen durch"
          % (len(durch_b), 100 * len(durch_b) / 5))
    print()
    print("  ⚠️ Ein Wert mit NUR Funding hat eine BESSERE Chance als einer")
    print("     mit beiden Raengen - weil die Schwelle an der erreichbaren")
    print("     Spanne haengt und turnovers Spanne sehr breit ist.")
    print()
    print("=" * 96)
    print("DIE ANTWORT AUF N8")
    print("=" * 96)
    print("  Wo turnover VORLIEGT (7 von 57): das Tor verlangt ohnehin")
    print("  turnover-Fuenftel %s. Eine ODER-Sperre wuerde Fuenftel 4"
          % sorted({j for _i, j in durch_a}))
    print("  sperren - eine Gruppe, die das Tor ohnehin nie passiert.")
    print("  -> die turnover-Komponente waere dort WIRKUNGSLOS, nicht")
    print("     doppelt gezaehlt.")
    print()
    print("  Wo turnover FEHLT (50 von 57): die ODER-Sperre kann ihn gar")
    print("  nicht auswerten. Nur die vola-Komponente wuerde wirken.")
    print()
    print("  ⚠️ `vola` kommt aus der KURSREIHE und deckt ALLE Werte ab.")
    print("     Damit ist die eigentliche Frage nicht 'ODER oder nicht',")
    print("     sondern: traegt `vola` ALLEIN als Sperre genug?")
    return 0


if __name__ == "__main__":
    sys.exit(main())
