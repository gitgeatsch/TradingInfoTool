# -*- coding: utf-8 -*-
"""Die Trennschaerfe der Regel-Messung, richtig gebaut (30.08.2026).

## Warum die ersten zwei Anlaeufe scheiterten

  1. Pflanzung auf die BEHALTENEN: die machen 80 % des Vergleichsmedians aus,
     der Effekt hob sich selbst auf.
  2. Pflanzung auf die GESPERRTEN: der Median (50. Perzentil) reagiert kaum,
     wenn man die aeusseren 20 % weiter nach unten schiebt.

⚠️ Beides sind Konstruktionsfehler, keine Befunde. Eine Kontrolle, die den
eigenen Effekt frisst, belegt nichts - und ohne sie ist jeder Nullbefund
wertlos.

## Die richtige Konstruktion: ein Merkmal BEKANNTER Guete

Statt am Ergebnis zu schrauben, wird das MERKMAL kuenstlich erzeugt:

    merkmal = -ziel + rauschen * k

Bei k = 0 ist es ein perfektes Orakel (das Merkmal IST der Ausgang), bei
grossem k reines Rauschen. Gemessen wird, ab welcher Korrelation zwischen
Merkmal und Ausgang die Regel ueberhaupt anschlaegt.

Das beantwortet die eigentliche Frage: **Wie gut muesste ein Merkmal sein,
damit diese Messung es findet?** Und daran gemessen wird, was Amihud und
Momentum tatsaechlich haben.
"""
import statistics as st, sys
import numpy as np
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import messe_regel_wirksamkeit as W
import messe_kandidaten_als_regel as K
import messe_bewertungskennzahl as M
import messe_eigenschaft_beitrag as B

reihen = B.lade()
rng = np.random.default_rng(4242)
basis = K.baue(reihen, "momentum")          # nur als Anker-Geruest
print("=" * 88)
print("TRENNSCHAERFE DER REGEL-MESSUNG")
print("=" * 88)
print("%d Kalendertage. Merkmal kuenstlich: -Ziel + Rauschen*k" % len(basis))
print()
print("  %-8s %-12s %s" % ("k", "Korrelation", "Wirkung der Regel"))
for k in (0.0, 1.0, 3.0, 6.0, 12.0):
    kunst, korr = {}, []
    for tag, z in basis.items():
        y = np.array([x["in_r"] for x in z])
        m = -y + rng.normal(0, max(k, 1e-9) * (np.std(y) or 1.0), len(y))
        if np.std(m) > 0 and np.std(y) > 0:
            korr.append(float(np.corrcoef(m, y)[0, 1]))
        kunst[tag] = [{"sym": x["sym"], "kennzahl": float(mm), "in_r": x["in_r"]}
                      for x, mm in zip(z, m)]
    d, anteil, gesp, uebr = W.wirkung(kunst, True)
    w = np.array(list(d.values()))
    print("  %-8.1f %-12.3f " % (k, st.mean(korr)), end="")
    M.urteil_tage("", d, rng, 90)
print()
print("  Zum Vergleich - die echten Korrelationen Merkmal <-> Ausgang:")
for art, name in (("amihud", "Amihud"), ("momentum", "Momentum 12-1"),
                  ("funding", None)):
    if name is None: continue
    jt = K.baue(reihen, art)
    kk = []
    for z in jt.values():
        m = np.array([x["kennzahl"] for x in z]); y = np.array([x["in_r"] for x in z])
        if np.std(m) > 0 and np.std(y) > 0:
            kk.append(float(np.corrcoef(m, y)[0, 1]))
    print("    %-16s %+.4f" % (name, st.mean(kk)))
