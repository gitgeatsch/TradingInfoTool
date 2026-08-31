# -*- coding: utf-8 -*-
"""G-2': wieviele PUNKTE traegt Turnover je Fuenftel? (30.08.2026, 2e)

Das Gegenstueck zu `rechne_funding_beitrag.py`. ⚠️ Es fehlte - und ohne diese
Tabelle waere Turnover mit GESCHAETZTEN Stufen registriert worden.
`messe_schwelle_kalibrierung.py` hat genau das getan: dort steht

    TURNOVER_STUFEN = (+0.81, +0.85, +0.25, -0.52, -1.39)   # "dieselbe Form"

also eine KOPIE der Funding-Stufen. Fuer eine Schwellensimulation ist das
vertretbar, fuer die Registrierung im Produktionscode nicht.

## Die Umrechnung, wie bei Funding

    Potential = quote * CRV - (1 - quote)
    d(Potential) = d(quote) * (1 + CRV)
    -> d(quote) = d(Potential) / (1 + CRV)          bei CRV 2,0 also 1/3

## ⚠️ IN-SAMPLE

Diese Zahlen stammen aus derselben Messung, die den Befund ergeben hat. Fuer
eine erste Kalibrierung ueblich, aber es gehoert benannt - und es ist der
Grund fuer die Halbierung ("geschrumpft"), dieselbe Vorsicht wie bei
`trefferbilanz.geschrumpft()`.

    python rechne_turnover_beitrag.py
"""
import statistics as st
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_bewertungskennzahl as MB
import messe_eigenschaft_beitrag as B
import messe_kandidaten_als_regel as K

HOR, CRV = 20, 2.0

reihen = B.lade()
menge = MB.reihe("data/onchain_historie.db", "splycur")
je_tag = K.baue(reihen, "turnover", menge)

sammel = {k: [] for k in range(5)}
for z in je_tag.values():
    if len(z) < 15:
        continue
    w = np.array([x["kennzahl"] for x in z])
    y = np.array([x["in_r"] for x in z])
    r = np.argsort(np.argsort(w)) / max(len(w) - 1, 1)
    for k in range(5):
        m = (r >= k / 5) & (r < (k + 1) / 5 if k < 4 else r <= 1.0)
        if m.sum() >= 2:
            sammel[k].append(float(np.median(y[m])))
werte = [st.mean(sammel[k]) for k in range(5)]
mittel = st.mean(werte)

print("=" * 74)
print("G-2' — die BEITRAGSTABELLE fuer Turnover")
print("=" * 74)
print("%d Kalendertage, Horizont %d, CRV %.1f"
      % (sum(1 for z in je_tag.values() if len(z) >= 15), HOR, CRV))
print()
print("  Fuenftel  Bewegung   gegen Mittel   Punkte roh   Punkte GESCHRUMPFT")
faktor = 1.0 / (1.0 + CRV)
stufen = []
for k in range(5):
    ab = werte[k] - mittel
    roh = 100.0 * ab * faktor
    stufen.append(round(roh / 2.0, 2))
    print("     %d     %+.4f R    %+.4f R      %+5.2f       %+5.2f"
          % (k, werte[k], ab, roh, roh / 2.0))
print()
print("  Spanne unterstes gegen oberstes Fuenftel: %+.2f Punkte roh, %+.2f geschrumpft"
      % (100 * (werte[0] - werte[4]) * faktor,
         100 * (werte[0] - werte[4]) * faktor / 2))
print()
print("  Fuer `wahrscheinlichkeit.BEITRAEGE`:")
print("    stufen=(%s)," % ", ".join("%+.2f" % s for s in stufen))
