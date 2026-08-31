# -*- coding: utf-8 -*-
"""G-2': wieviele PUNKTE traegt Funding je Fuenftel? (30.08.2026)

`wahrscheinlichkeit.BEITRAEGE` erwartet Prozentpunkte auf die Quote, nicht R.
Die Umrechnung folgt aus der Potentialformel:

    Potential = quote * CRV - (1 - quote)
    d(Potential) = d(quote) * (1 + CRV)
    -> d(quote) = d(Potential) / (1 + CRV)

Bei CRV 2,0 ist der Faktor also 1/3.

⚠️ IN-SAMPLE. Diese Zahlen stammen aus derselben Messung, die den Befund
ergeben hat. Das ist fuer eine erste Kalibrierung ueblich, aber es gehoert
benannt - und es ist der Grund fuer die Schrumpfung unten.
"""
import statistics as st, sys
import numpy as np
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import messe_funding_niveau as F
import messe_eigenschaft_beitrag as B

HOR, CRV = 20, 2.0
reihen = B.lade(); funding = F.lade_funding()
je_tag = {}
for sym, roh in reihen.items():
    f = funding.get(sym.upper())
    if not f: continue
    tage = [z[0] for z in roh]
    c = np.array([z[1] for z in roh])
    h = np.array([z[2] for z in roh]); t_ = np.array([z[3] for z in roh])
    breite = B.spanne(h, t_, c, B.SCHWANKUNG)
    for i in range(60, len(c) - HOR):
        r = breite[i]
        if not np.isfinite(r) or r <= 0 or tage[i] not in f: continue
        je_tag.setdefault(tage[i], []).append(
            (f[tage[i]], float((c[i+HOR] - c[i]) / r)))
je_tag = {t: z for t, z in je_tag.items() if len(z) >= 15}

# je Tag Fuenftel, dann ueber die Tage mitteln (Marktlage festgehalten)
sammel = {k: [] for k in range(5)}
for z in je_tag.values():
    w = np.array([x[0] for x in z]); y = np.array([x[1] for x in z])
    r = np.argsort(np.argsort(w)) / max(len(w)-1, 1)
    for k in range(5):
        m = (r >= k/5) & (r < (k+1)/5 if k < 4 else r <= 1.0)
        if m.sum() >= 2:
            sammel[k].append(float(np.median(y[m])))
werte = [st.mean(sammel[k]) for k in range(5)]
mittel = st.mean(werte)

print("=" * 74)
print("G-2' — die BEITRAGSTABELLE fuer Funding")
print("=" * 74)
print("%d Kalendertage, Horizont %d, CRV %.1f" % (len(je_tag), HOR, CRV))
print()
print("  Fuenftel  Bewegung   gegen Mittel   Punkte roh   Punkte GESCHRUMPFT")
faktor = 1.0 / (1.0 + CRV)
# Schrumpfung: In-Sample-Kalibrierung wird halbiert - dieselbe Vorsicht wie
# bei `trefferbilanz.geschrumpft()`
for k in range(5):
    ab = werte[k] - mittel
    roh = 100.0 * ab * faktor
    print("     %d     %+.4f R    %+.4f R      %+5.2f       %+5.2f"
          % (k, werte[k], ab, roh, roh / 2.0))
print()
print("  Spanne unterstes gegen oberstes Fuenftel: %+.2f Punkte roh, %+.2f geschrumpft"
      % (100*(werte[0]-werte[4])*faktor, 100*(werte[0]-werte[4])*faktor/2))
print("  Zum Vergleich: Vorfilter H traegt +4,50 Punkte (als Schalter)")
