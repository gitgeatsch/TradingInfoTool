"""B4-Vormessung (Spot §43) - NACHTRAG zum Selbsttest, AUSKUNFT (die Vorabfestlegung bleibt unveraendert). Nur lesend.

    python Basisinfos/Spot_Voranalyse_04_10/b4_selbsttest_nachtrag.py

Der vorab festgelegte Selbsttest (40 Ziehungen je Zufallswert, Fehlalarm <= 5 % ZWEISEITIG) fiel mit 11 von 100.
Vermutete Ursache, hier GEMESSEN statt behauptet: mit 40 Ziehungen ist der Rang diskret (Schritt 1/40). Eine Seite schlaegt an bei hoechstens
1 von 40 Ziehungen unter (bzw. ueber) dem echten Wert - unter der Nullhypothese mit Wahrscheinlichkeit 2/41 = 4,9 % JE SEITE, zusammen 9,8 %.
  N1  derselbe Test mit 200 Ziehungen je Zufallswert (wie die Hauptmessung): Fehlalarm zweiseitig, Soll um 5 %
  N2  derselbe Test mit 40 Ziehungen, aber Fehlalarm je Seite gezaehlt: Soll um 4,9 % je Seite
  N3  Aufloesung: gepflanzt s x Perzentil(Ertrag) + N(0,1), s = 0,3 / 1 / 2 / 4, je 10 Wiederholungen mit 200 Ziehungen - ab welcher Staerke
      wird SCHLECHTER gefunden, und welcher Abstand entspricht ihr (gegen den echten Befund -12,5 Pp)
"""
import os
import sys

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
import b4_vormessung as B  # noqa: E402

D4, MK, M, W = B.D4, B.MK, B.M, B.W
RNG = np.random.default_rng(20261044)

D = MK.paare_mw(365).reset_index(drop=True)
Z = M.Zellen(D)
p = M.pct_in_zelle(Z, W.wert(Z, M.merkmale(D), wahl=D4.OHNE_F9))
y = D.ende.values - 1.0
R = B.Rechner(D, p, y)
print("B4-VORMESSUNG · NACHTRAG SELBSTTEST (Auskunft) · E3\n")


def zufall():
    return np.where(np.isnan(p), np.nan, RNG.random(R.nsym)[R.code])


n1 = n2u = n2o = 0
for i in range(100):
    g = zufall()
    a = R.abstand(g, "E3")
    n1 += B.urteil(a, float(np.mean(R.null(g, "E3", 200, RNG) < a))) != "nicht entscheidbar"
    g = zufall()
    a = R.abstand(g, "E3")
    r = float(np.mean(R.null(g, "E3", 40, RNG) < a))
    n2u += a < 0 and r <= 0.025
    n2o += a > 0 and r >= 0.975
print("N1 200 Ziehungen: Fehlalarm zweiseitig %d von 100 (Soll um 5)" % n1)
print("N2  40 Ziehungen: SCHLECHTER %d · BESSER %d von 100 (Soll je Seite um 4,9 - zusammen 9,8)\n" % (n2u, n2o))

pp = np.full(len(D), np.nan)
for t, k, m in R.zellen:
    pp[m] = pd.Series(y[m]).rank(pct=True).values
for s in (0.3, 1.0, 2.0, 4.0):
    funde, ab = 0, []
    for _ in range(10):
        gp = np.where(np.isnan(p), np.nan, s * pp + RNG.normal(size=len(D)))
        a = R.abstand(gp, "E3")
        ab.append(a)
        funde += B.urteil(a, float(np.mean(R.null(gp, "E3", 200, RNG) < a))) == "SCHLECHTER"
    print("N3 gepflanzt s %.1f: Abstand Mittel %+.1f Pp · SCHLECHTER gefunden %d von 10" % (s, 100 * np.mean(ab), funde))
