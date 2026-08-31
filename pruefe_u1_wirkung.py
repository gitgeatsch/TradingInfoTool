# -*- coding: utf-8 -*-
"""Was aendert U-1 an der DURCHLASSQUOTE? Eindeutig gerechnet. (30.08.2026)

Nutzereinwand: *"ueber die Wirkung muessen wir nochmal reden, da ich deine
Darstellung nicht sauber interpretieren kann - kommen jetzt Kombinationen mit
H durch oder mehr oder weniger?"*

Zu Recht. "9 von 25 Kombinationen" ist KEINE Durchlassquote - die
Kombinationen sind unterschiedlich haeufig, und H kommt oben drauf. Hier
steht, wieviele SIGNALE durchkommen.
"""
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from agent import potential as PT
from agent import trefferbilanz as TB

CRV, STOP = 2.0, 0.05
H_QUOTE = 0.050          # NB-Export 29.08.: 31 von 617 Faellen
F = (+0.81, +0.85, +0.25, -0.52, -1.39)
T = (+0.81, +0.85, +0.25, -0.52, -1.39)


def pot(punkte):
    q = 1.0 / (1.0 + CRV) + punkte / 100.0
    return q * CRV - (1.0 - q)


print("=" * 82)
print("WAS AENDERT U-1? Die Durchlassquote, eindeutig")
print("=" * 82)
print()
print("### VORHER — Stufe 11 mit trefferbilanz (Gebuehren-Breakeven) ###")
kosten = 2 * 0.015 / STOP
b = TB.bewerte({}, ("x",), kosten_r=kosten, crv=CRV)
print("  Stop %.0f %%, Gebuehr 1,5 %% je Seite -> kosten_r %.2f" % (100*STOP, kosten))
print("  Quote %.4f gegen Schwelle %.4f  ->  %s"
      % (b["wahrscheinlichkeit"], b["breakeven"],
         "traegt" if b["traegt"] else "TRAEGT NICHT"))
print("  ⚠️ Das galt fuer JEDES Signal - unabhaengig von H, Funding, allem.")
print("     Die Stufe zaehlte nur, deshalb kamen faktisch 100 %% durch.")
print("     HAETTE sie verworfen, waeren es 0 %% gewesen.")
print()
print("### NACHHER — Stufe 11 mit potential, Schwelle %.3f R ###" % PT.schwelle())
print()
print("  a) Signale MIT Vorfilter H (%.0f %% aller Faelle):" % (100*H_QUOTE))
schlechteste = pot(4.5 + F[4] + T[4])
print("     schlechteste Kombination (H + beide Fuenftel 4): %+.4f R" % schlechteste)
print("     -> %s"
      % ("ALLE kommen durch - H allein traegt weit ueber die Schwelle"
         if PT.traegt(schlechteste) else "nicht alle"))
print()
print("  b) Signale OHNE H (%.0f %%):" % (100*(1-H_QUOTE)))
durch = sum(1 for f in F for t in T if PT.traegt(pot(f + t)))
print("     %d von 25 Fuenftel-Kombinationen kommen durch" % durch)
print("     bei gleichverteilten Fuenfteln sind das %.0f %% dieser Signale"
      % (100*durch/25))
print()
gesamt = H_QUOTE * 1.0 + (1 - H_QUOTE) * (durch / 25)
print("  ==> INSGESAMT kommen %.0f %% der Signale durch." % (100*gesamt))
print("      %.0f %% werden verworfen - mit Begruendung." % (100*(1-gesamt)))
print()
print("### Zum Vergleich: was traegt WIEVIEL? ###")
for name, punkte in (("nur H", 4.5), ("nur bestes Funding", 0.85),
                     ("bestes Funding + bester Turnover", 1.70),
                     ("beide Fuenftel 2 (mittel)", 0.50),
                     ("beide Fuenftel 3", -1.04),
                     ("beide Fuenftel 4 (schlechteste)", -2.78)):
    w = pot(punkte)
    print("  %-34s %+7.4f R   %s" % (name, w, "durch" if PT.traegt(w) else "VERWORFEN"))
print()
print("### Erweiterbarkeit: was passiert mit einem DRITTEN Beitrag? ###")
print("  Ein weiterer Beitrag verschiebt jede Zeile um seinen Punktwert.")
for zusatz in (0.5, 1.0, 2.0):
    d = sum(1 for f in F for t in T if PT.traegt(pot(f + t + zusatz)))
    g = H_QUOTE + (1 - H_QUOTE) * (d / 25)
    print("     +%.1f Punkte -> %2d von 25 Kombinationen, insgesamt %.0f %% Durchlass"
          % (zusatz, d, 100*g))
