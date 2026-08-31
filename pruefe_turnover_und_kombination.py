# -*- coding: utf-8 -*-
"""Turnover: Survivorship aufloesen, und wirkt er ZUSAETZLICH zu Funding?

Zwei Fragen vor der Aufnahme:

  A  Der Survivorship-Vorbehalt: die 66 Symbole mit Umlaufmenge enden zu 71 %
     tiefer, die uebrigen 457 zu 90 %. Traegt die Regel auch bei den
     SCHLECHTEREN dieser 66? Wenn ja, ist der Auswahleffekt keine Erklaerung.
  B  Wirken Funding und Turnover zusammen - oder ersetzen sie einander?
     Fuer den Bau entscheidend: zwei Beitraege oder einer.
"""
import statistics as st, sys
import numpy as np
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import messe_regel_wirksamkeit as W
import messe_kandidaten_als_regel as K
import messe_bewertungskennzahl as MB
import messe_eigenschaft_beitrag as B
import messe_funding_niveau as F

reihen = B.lade()
rng = np.random.default_rng(2468)
menge = MB.reihe("data/onchain_historie.db", "splycur")
funding = F.lade_funding()
tu = K.baue(reihen, "turnover", menge)
syms = sorted({x["sym"] for z in tu.values() for x in z})

print("=" * 88)
print("A — SURVIVORSHIP: traegt die Regel auch bei den SCHLECHTEREN der 66?")
print("=" * 88)
end = {}
for s in syms:
    z = reihen[s]
    end[s] = z[-1][1] / z[200][1] if z[200][1] > 0 else 1.0
mitte = st.median(list(end.values()))
for name, bed in (("die schwaecheren 33", lambda s: end[s] <= mitte),
                  ("die staerkeren 33", lambda s: end[s] > mitte)):
    teil = {}
    for tag, z in tu.items():
        aus = [x for x in z if bed(x["sym"])]
        if len(aus) >= 8:
            teil[tag] = aus
    if teil:
        d, a, g, u = W.wirkung(teil, True)
        MB.urteil_tage("  %-22s" % name, d, rng, 250)

print()
print("=" * 88)
print("B — KOMBINATION: wirkt Turnover ZUSAETZLICH zu Funding?")
print("=" * 88)
# Funding an die Turnover-Anker haengen
for tag, z in tu.items():
    for x in z:
        f = funding.get(x["sym"].upper(), {}).get(tag)
        if f is not None:
            x["funding"] = f
gemeinsam = {t: [x for x in z if "funding" in x] for t, z in tu.items()}
gemeinsam = {t: z for t, z in gemeinsam.items() if len(z) >= 12}
n = sum(len(z) for z in gemeinsam.values())
print("  %d Anker mit BEIDEN Groessen, %d Kalendertage" % (n, len(gemeinsam)))
print()
print("  Einzeln auf DIESER gemeinsamen Basis:")
d1, _, _, _ = W.wirkung(gemeinsam, True)
MB.urteil_tage("    nur Turnover", d1, rng, 250)
fu = {t: [{"sym": x["sym"], "kennzahl": x["funding"], "in_r": x["in_r"]} for x in z]
      for t, z in gemeinsam.items()}
d2, _, _, _ = W.wirkung(fu, True)
MB.urteil_tage("    nur Funding", d2, rng, 250)
print()
print("  BEIDE zusammen (gesperrt, wenn EINE der beiden Regeln greift):")
d3 = {}
for tag, z in gemeinsam.items():
    t_ = np.array([x["kennzahl"] for x in z]); f_ = np.array([x["funding"] for x in z])
    y = np.array([x["in_r"] for x in z])
    rt = np.argsort(np.argsort(t_)) / max(len(t_)-1, 1)
    rf = np.argsort(np.argsort(f_)) / max(len(f_)-1, 1)
    frei = (rt < 0.80) & (rf < 0.80)
    if frei.sum() >= 3 and (~frei).sum() >= 1:
        d3[tag] = float(np.median(y[frei]) - np.median(y))
MB.urteil_tage("    beide", d3, rng, 250)
anteil = st.mean([1 - ((np.argsort(np.argsort([x["kennzahl"] for x in z]))/max(len(z)-1,1) < .8) &
                       (np.argsort(np.argsort([x["funding"] for x in z]))/max(len(z)-1,1) < .8)).mean()
                  for z in gemeinsam.values() if len(z) >= 12])
print("    -> gesperrt: %.1f %% (statt je 20 %%)" % (100*anteil))
