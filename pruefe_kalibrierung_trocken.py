# -*- coding: utf-8 -*-
"""TROCKENLAUF DER KALIBRIERUNG — was passiert, BEVOR etwas geändert wird
(06.09.2026)

## Warum ein Trockenlauf

Die vorgesehene Kalibrierung:

    funding    5 Stufen (+0,82 .. -1,70)  ->  Zweiteilung +0,198 / -0,194
    turnover   5 Stufen (+3,15 .. -2,40)  ->  NULL, stillgelegt
    vola       -                          ->  Dreiteilung (spaeter, Bau)

⚠️ Das ist keine reine Zahlenaenderung. Sie greift in drei Mechaniken:

  1  `erreichbar_max` zaehlt nur Beitraege mit `zustand == "traegt"`.
     Faellt `turnover` heraus, sind "nur funding" und "beide" DIESELBE
     Datenlage - und die Suite-Pruefung `_p_ein.schwelle < _p_zwei.schwelle`
     bricht.

  2  Die SCHWELLE ist ein Anteil von `erreichbar_max`. Schrumpft der,
     schrumpft sie mit - aber der ANTEIL war fuer die alte Beitragslage
     kalibriert (R-R9).

  3  Der DURCHLASS aendert sich. Wieviele Kombinationen kommen noch durch?

**Dieser Lauf aendert NICHTS.** Er rechnet die Folgen durch, damit die
Entscheidung mit offenen Augen faellt.

    python pruefe_kalibrierung_trocken.py
"""
from __future__ import annotations

import itertools
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, ".")

from agent import potential as P                             # noqa: E402
from agent import wahrscheinlichkeit as WK                   # noqa: E402

CRV = 2.0

ALT = {"funding": (+0.82, +1.30, +0.12, -0.54, -1.70),
       "turnover": (+3.15, +0.83, +0.22, -1.79, -2.40)}

# ⚠️ Die Zweiteilung auf der FUENFTEL-Skala ist nicht exakt darstellbar:
# 50/50 liegt zwischen Fuenftel 2 und 3. Zwei Naeherungen werden gerechnet.
NEU_40_60 = {"funding": (+0.198, +0.198, -0.194, -0.194, -0.194)}
NEU_60_40 = {"funding": (+0.198, +0.198, +0.198, -0.194, -0.194)}
VOLA = (+1.461, -0.132, -1.323)      # Dreiteilung, spaeterer Bau


def wert_r(punkte, crv=CRV):
    q = WK.basisrate(crv) + punkte / 100.0
    return q * crv - (1.0 - q)


def lage(stufen: dict, mit_vola=False):
    """erreichbar_max, Schwelle, Durchlass fuer eine Beitragslage."""
    maxima = [max(s) for s in stufen.values()]
    if mit_vola:
        maxima.append(max(VOLA))
    voll = wert_r(sum(maxima))
    anteil = P.SCHWELLE_VORGABE / wert_r(sum(max(s) for s in ALT.values()))
    schwelle = anteil * voll
    return voll, schwelle, anteil


def durchlass(stufen: dict, schwelle, mit_vola=False):
    listen = list(stufen.values())
    if mit_vola:
        listen.append(VOLA)
    durch = 0
    ges = 0
    for k in itertools.product(*[range(len(s)) for s in listen]):
        p = sum(listen[i][k[i]] for i in range(len(listen)))
        ges += 1
        if wert_r(p) > schwelle:
            durch += 1
    return durch, ges


def main() -> int:
    print("=" * 92)
    print("TROCKENLAUF — die Folgen der Kalibrierung, BEVOR etwas geaendert wird")
    print("=" * 92)
    v_alt, s_alt, anteil = lage(ALT)
    d_alt, g_alt = durchlass(ALT, s_alt)
    print("  HEUTE")
    print("    erreichbar_max %.4f R · Schwelle %.4f R (Anteil %.1f %%)"
          % (v_alt, s_alt, 100 * anteil))
    print("    Durchlass %d von %d Kombinationen (%.0f %%)"
          % (d_alt, g_alt, 100 * d_alt / g_alt))

    for lab, neu in (("NACH KALIBRIERUNG (40/60-Naeherung)", NEU_40_60),
                     ("NACH KALIBRIERUNG (60/40-Naeherung)", NEU_60_40)):
        print()
        print("  %s — turnover auf NULL" % lab)
        v, s, _a = lage(neu)
        d, g = durchlass(neu, s)
        print("    erreichbar_max %.4f R · Schwelle %.4f R" % (v, s))
        print("    Durchlass %d von %d (%.0f %%)" % (d, g, 100 * d / g))
        print("    ⚠️ erreichbar_max faellt um Faktor %.1f" % (v_alt / v))
        # mit vola
        v2, s2, _a2 = lage(neu, mit_vola=True)
        d2, g2 = durchlass(neu, s2, mit_vola=True)
        print("    MIT `vola` (spaeterer Bau):")
        print("      erreichbar_max %.4f R · Schwelle %.4f R" % (v2, s2))
        print("      Durchlass %d von %d (%.0f %%)" % (d2, g2, 100 * d2 / g2))
        gew = max(VOLA) / (max(VOLA) + max(neu["funding"]))
        print("      ⚠️ `vola` traegt %.0f %% des Beitragsgewichts"
              % (100 * gew))

    print()
    print("=" * 92)
    print("WAS AN DER SUITE BRICHT")
    print("=" * 92)
    print("  Die Pruefung `_p_ein.schwelle < _p_zwei.schwelle` vergleicht")
    print("  'nur funding' gegen 'funding UND turnover'.")
    print()
    print("  ⚠️ Mit `turnover` auf NULL faellt er aus `erreichbar_max` -")
    print("     beide Datenlagen werden IDENTISCH, und die Pruefung bricht.")
    print()
    print("  Zwei Auswege:")
    print("    A  `turnover` NICHT auf null, sondern auf den gemessenen")
    print("       Kleinstwert -> aber der ist nicht belegt (Band mit Null)")
    print("    B  die Pruefung auf `funding` gegen `funding+vola` umstellen")
    print("       -> ehrlich, aber erst NACH dem vola-Bau moeglich")
    print()
    print("  ⚠️⚠️ Daraus folgt eine REIHENFOLGE, die vorher nicht sichtbar war:")
    print("     `vola` muss GEBAUT sein, BEVOR `turnover` stillgelegt wird -")
    print("     sonst hat das System voruebergehend nur EINEN Beitrag, und")
    print("     die Datenlagen-Schwelle verliert ihren Sinn.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
