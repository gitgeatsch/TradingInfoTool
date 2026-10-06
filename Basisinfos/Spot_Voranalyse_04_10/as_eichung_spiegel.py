"""Eichung der Spiegelschwelle fuer die Asymmetrie-Messung (Voranalyse_Spot §19.4) - Methode wie Befund 2.603 (26.09.): bekannte Wahrheit gepflanzt.

    python Basisinfos/Spot_Voranalyse_04_10/as_eichung_spiegel.py

Anlass: Selbsttest (b) in as_messung.py fand das gepflanzte Richtungsmerkmal sicher (Rang 1,000), die Spiegelschwelle 1,717 (geeicht fuer
stuendliche Hebel-Ereignisse) verwarf es. Hier wird die Schwelle FUER DIESE Zielgroesse (12-Monats-Fenster, R2 gegen D2) bestimmt.

  Bewegungswelt  f = s * (R2 + D2) + N(0,1)   hebt BEIDE Enden: darf die Probe nicht bestehen
  Richtungswelt  f = s * R2 + N(0,1)          hebt nur das rechte Ende: soll sie bestehen
  Staerken s = 0,15 / 0,3 / 0,6 / 1,0, je 40 Rauschziehungen, je Epoche E2/E3, oberes Fuenftel, Spiegel = Lift(R2) / Lift(D2)
  Regel (vorab): Schwelle = kleinster Wert, den in KEINER Staerke mehr als 2,5 % der Bewegungswelten erreichen (je Epoche, dann das Maximum)
"""
import os
import sys

import numpy as np

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
import as_messung as M  # noqa: E402

RNG = np.random.default_rng(20261011)


def main():
    D = M.paare(365).reset_index(drop=True)
    Z = M.Zellen(D)
    st = (0.15, 0.3, 0.6, 1.0)
    welt = {}
    for name, basis in (("Bewegung", Z.r2 + Z.d2), ("Richtung", Z.r2)):
        for s in st:
            w = {"E2": [], "E3": []}
            for _ in range(40):
                o = M.bewerte(Z, s * basis + RNG.normal(size=len(D)), "oben", null=False, ep_liste=("E2", "E3"))
                for e in w:
                    w[e].append(o[e]["spiegel"])
            welt[(name, s)] = {e: np.array(v) for e, v in w.items()}
    print("Eichung Spiegelschwelle (§19.4) · %d Coin-Anker · Spiegel = Lift(R2)/Lift(D2), oberes Fuenftel, je 40 Ziehungen\n" % len(D))
    print("  %-9s %5s | %-40s | %-40s" % ("Welt", "s", "E2: Median · 97,5. Perzentil · Max", "E3: Median · 97,5. Perzentil · Max"))
    for (name, s), w in welt.items():
        print("  %-9s %5.2f | %s | %s" % (name, s, *("%6.3f · %6.3f · %6.3f%s" % (np.median(w[e]), np.percentile(w[e], 97.5), w[e].max(), " " * 18) for e in ("E2", "E3"))))
    schwelle = max(np.percentile(welt[("Bewegung", s)][e], 97.5) for s in st for e in ("E2", "E3"))
    print("\nSchwelle nach Regel: %.3f (hoechstes 97,5. Perzentil der Bewegungswelten ueber alle Staerken und beide Epochen)" % schwelle)
    print("Fehlalarm und Fundquote bei dieser Schwelle:")
    for (name, s), w in welt.items():
        print("  %-9s s %.2f  E2 %3.0f %% · E3 %3.0f %% · beide %3.0f %%" % (name, s, 100 * np.mean(w["E2"] >= schwelle), 100 * np.mean(w["E3"] >= schwelle),
                                                                         100 * np.mean((w["E2"] >= schwelle) & (w["E3"] >= schwelle))))
    print("Zum Vergleich die alte Schwelle 1,717: Richtung s 0,30 besteht in beiden Epochen zu %.0f %%" % (
        100 * np.mean((welt[("Richtung", 0.3)]["E2"] >= 1.717) & (welt[("Richtung", 0.3)]["E3"] >= 1.717))))


if __name__ == "__main__":
    main()
