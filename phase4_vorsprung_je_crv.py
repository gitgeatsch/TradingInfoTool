# -*- coding: utf-8 -*-
"""WOHER KANN MEHR VORSPRUNG KOMMEN? (Nutzerfrage 20.09.2026)

## Die Frage

Der Gewinn einer Wette haengt nicht an der Trefferquote `q`, sondern am
**VORSPRUNG** `q - Breakeven`, mit `Breakeven = 1/(1+CRV)`. An den 16
echten Hebelsignalen betraegt er **0,8 bis 1,3 Prozentpunkte** - weniger
als die Messunsicherheit.

Zwei Wege sind denkbar:

    (a) HOEHERES CRV   senkt den Breakeven (bei CRV 3 auf 0,25)
    (b) MEHR BEITRAG   hebt die Quote

⚠️ (a) klingt nach einem freien Gewinn und ist meist keiner: ein
entfernteres Ziel wird SELTENER erreicht. Ob der Breakeven schneller
faellt als die Trefferquote, ist eine MESSFRAGE - und sie ist hier
beantwortbar, weil die Barrieren-Quoten je CRV schon gemessen sind
(Machbarkeitszaehlung zu 2b, 20.09.2026, 536 Kryptoreihen ab 2023).

## ⚠️⚠️ Beide Maße gehoeren nebeneinander

    BEDINGT     P(Ziel | aufgeloest) - die Basisrate 1/(1+CRV) ist genau
                dieses Mass (driftfrei, unter den Aufgeloesten)
    UNBEDINGT   P(Ziel) - ungeloeste Anker zaehlen als Fehlschlag. Das
                ist `q` der Potentialformel (2.139-quote)

Die Bewertung rechnet mit dem BEDINGTEN Nullpunkt und meint das
unbedingte `q`. Bei H20 sind 95 Prozent aufgeloest, der Unterschied ist
klein - bei H2 sind es 38 Prozent.

⚠️ NUR LESEND, keine DB, kein Netz - die Zahlen stammen aus der
Zaehlung zu 2b und stehen hier als Konstanten, mit Datum.

    python phase4_vorsprung_je_crv.py
"""
from __future__ import annotations

import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Gemessen am 20.09.2026 (Machbarkeitszaehlung zu 2b): 536 Kryptoreihen,
# Fenster ab 2023-01-01, Produktionsgeometrie
# stop = min(25 %, max(5 %, 0,75 x ATR)).
#   Horizont -> {Zielhoehe: (Anteil aufgeloest, P(Ziel|auf), P(Ziel))}
GEMESSEN = {
    20: {1.0: (0.974, 0.487, 0.475), 1.5: (0.964, 0.396, 0.382),
         2.0: (0.951, 0.332, 0.316), 2.5: (0.936, 0.285, 0.267),
         3.0: (0.920, 0.248, 0.228)},
    7:  {1.0: (0.901, 0.489, 0.441), 1.5: (0.837, 0.387, 0.324),
         2.0: (0.780, 0.311, 0.242), 2.5: (0.735, 0.250, 0.184),
         3.0: (0.700, 0.203, 0.142)},
    2:  {1.0: (0.555, 0.492, 0.273), 1.5: (0.441, 0.345, 0.152),
         2.0: (0.383, 0.241, 0.092), 2.5: (0.353, 0.171, 0.060),
         3.0: (0.335, 0.125, 0.042)},
}
# Die Beitragsstufen (Prozentpunkte der Trefferquote), gemessen bei CRV 2.
BESTER_ZUSCHLAG = 4.45      # funding 1,30 + turnover 3,15
HEUTE_ZUSCHLAG = 1.27       # der reale Arbeitspunkt (2.496-2c-kennlinie)


def main() -> int:
    print("=" * 100)
    print("WOHER KANN MEHR VORSPRUNG KOMMEN?")
    print("=" * 100)
    print("  Vorsprung = Trefferquote minus Breakeven, Breakeven = "
          "1/(1+CRV).")
    print("  Zahlen aus der Zaehlung zu 2b (20.09.2026, 536 Reihen ab 2023).")
    print()
    for H in sorted(GEMESSEN, reverse=True):
        print("-" * 100)
        print("  HORIZONT H%d" % H)
        print("  %-6s %9s %11s %11s %11s %11s"
              % ("CRV", "Breakeven", "P(Z|auf)", "Vorspr. bed.",
                 "P(Ziel)", "Vorspr. unbed."))
        for crv in sorted(GEMESSEN[H]):
            auf, bed, unbed = GEMESSEN[H][crv]
            be = 1.0 / (1.0 + crv)
            print("  %-6.1f %9.4f %11.3f %+11.4f %11.3f %+11.4f"
                  % (crv, be, bed, bed - be, unbed, unbed - be))
        print()
    print("=" * 100)
    print("WAS DAS HEISST")
    print("=" * 100)
    print("  (a) EIN HOEHERES CRV BRINGT KEINEN VORSPRUNG. Bei H20 liegt "
          "der bedingte Vorsprung")
    print("      bei JEDEM CRV zwischen -0,013 und -0,001 - der Breakeven "
          "faellt genau so")
    print("      schnell wie die Trefferquote. Das ist die Aussage "
          "„Barrierensystem mit")
    print("      Erwartungswert null“, jetzt je Zielhoehe belegt.")
    print()
    print("  ⚠️ Auf der UNBEDINGTEN Quote ist der Vorsprung bei H20 sogar "
          "durchgehend negativ")
    print("     (-0,017 bis -0,025) - nicht aufgeloeste Anker zaehlen als "
          "Fehlschlag, und das")
    print("     kostet mehr, als ein hoeheres CRV einbringt.")
    print()
    print("  (b) DER VORSPRUNG KANN NUR AUS DEN BEITRAEGEN KOMMEN. Heute "
          "liegt der Zuschlag am")
    print("      Arbeitspunkt bei %+.2f Punkten; der beste erreichbare "
          "waere %+.2f" % (HEUTE_ZUSCHLAG, BESTER_ZUSCHLAG))
    print("      (funding 1,30 + turnover 3,15). ⚠️ Das ist ein Faktor "
          "3,5 - und er liegt")
    print("      nicht an einer besseren Formel, sondern daran, dass "
          "`turnover` bei 77 % der")
    print("      Kryptopositionen fehlt.")
    print()
    print("  ⚠️⚠️⚠️ UND SO IST (b) ZU LESEN: die Beitraege heben NICHT die "
          "mittlere Quote - ihre")
    print("     Stufen summieren sich zu null (Mittelwert funding +0,0000, "
          "turnover +0,0020).")
    print("     Sie erzeugen UNTERSCHEIDUNG, nicht Ertrag. Der Vorsprung "
          "entsteht erst durch die")
    print("     AUSWAHL: gehandelt wird nur, wo der Zuschlag hoch ist. "
          "Wer keinen Wert hat, kann")
    print("     nicht auswaehlen - und genau das ist die `turnover`-Luecke.")
    print()
    print("  ⚠️⚠️ EINSCHRAENKUNG, die dazugehoert: die Beitragsstufen sind "
          "bei CRV 2 gemessen.")
    print("     Ob sie bei CRV 3 dieselben waeren, ist UNGEMESSEN - die "
          "Tabelle oben sagt nur,")
    print("     dass die BASIS keinen Vorsprung hergibt, nicht was die "
          "Beitraege dort taeten.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
