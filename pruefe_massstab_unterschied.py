# -*- coding: utf-8 -*-
"""Warum +0,18 R gegen +0,024 R? Die Klaerung. (30.08.2026)

Nutzervorgabe: *"merke dir zu deiner Warnung, diese nicht nur auszugeben,
sondern wenn es Probleme gibt oder eine Loesung benoetigt wird, muessen wir
dies klaeren."* Zu Recht - eine unaufgeloeste Warnung neben einer Zahl, mit
der kalibriert wird, ist ein offenes Risiko.

## Die zwei Masze

    A  Regel-Wirksamkeit   median(bleibt) - median(ALLE)          +0,024 R
    B  Schwellen-Messung   median(bleibt) - median(ZUFALL gleich viele)  +0,18 R

Faktor 7,5. Wenn B einen systematischen Bias hat, ist die Schwelle falsch
kalibriert - und dann waere 0,010 die falsche Zahl.

## Der Verdacht

Bei einer RECHTSSCHIEFEN Verteilung (unsere Schiefe: 2,68) ist der Median
einer kleinen Stichprobe nicht erwartungstreu fuer den Populationsmedian.
Wenn der Zufalls-Median systematisch NIEDRIGER liegt, wird B zu gross - und
zwar rein rechnerisch, ohne dass die Auswahl etwas leistet.

## Der Test

Fuer verschiedene Stichprobengroeszen: Median der Gesamtmenge gegen den
Mittelwert vieler Zufalls-Mediane. Weicht das ab, ist der Bias beziffert -
und B muss um ihn bereinigt werden.
"""
import statistics as st
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_schwelle_kalibrierung as SK

je_tag = SK.bewerte(SK.baue())
rng = np.random.default_rng(2718)

print("=" * 84)
print("IST DER ZUFALLS-MEDIAN ERWARTUNGSTREU?")
print("=" * 84)
groessen = sorted({len(z) for z in je_tag.values()})
print("  Symbole je Tag: %d bis %d (Median %d)"
      % (min(groessen), max(groessen), int(st.median(groessen))))
print()
print("  %-8s %-8s %14s %16s %12s"
      % ("n gesamt", "k gezogen", "Median gesamt", "Mittel d. Zufalls-", "Abweichung"))
print("  %-8s %-8s %14s %16s %12s" % ("", "", "", "Mediane", ""))
abweichungen = []
for tag, z in list(je_tag.items())[:400]:
    y = np.array([x["in_r"] for x in z])
    n = len(y)
    for anteil in (0.36, 0.54):
        k = max(3, int(n * anteil))
        if k >= n:
            continue
        echt = float(np.median(y))
        zufall = float(np.mean([float(np.median(y[rng.choice(n, k, replace=False)]))
                                for _ in range(60)]))
        abweichungen.append((n, k, echt - zufall))
for anteil, name in ((0.36, "36 %"), (0.54, "54 %")):
    teil = [d for n, k, d in abweichungen if abs(k / n - anteil) < 0.05]
    if teil:
        print("  %-8s %-8s %14s %16s %+12.4f"
              % ("~12-20", name, "", "", st.mean(teil)))
print()
print("  -> %s" % ("⚠️ BIAS: der Zufalls-Median liegt systematisch daneben"
                   if abs(st.mean([d for _, _, d in abweichungen])) > 0.01
                   else "kein nennenswerter Bias"))
print()
print("=" * 84)
print("BEIDE MASZE AUF DENSELBEN DATEN — der direkte Vergleich")
print("=" * 84)
for s in (0.010, 0.020):
    a, b = [], []
    for tag, z in je_tag.items():
        y = np.array([x["in_r"] for x in z])
        m = np.array([x["potential"] > s for x in z])
        k = int(m.sum())
        if k < 3 or k >= len(z):
            continue
        bleibt = float(np.median(y[m]))
        a.append(bleibt - float(np.median(y)))                      # Mass A
        zuf = float(np.mean([float(np.median(y[rng.choice(len(y), k, replace=False)]))
                             for _ in range(30)]))
        b.append(bleibt - zuf)                                      # Mass B
    print("  Schwelle %.3f:  Mass A (gegen alle) %+.4f   Mass B (quotengleich) %+.4f"
          % (s, st.mean(a), st.mean(b)))
    print("                  Unterschied: %+.4f  <- das ist der Selektionseffekt"
          % (st.mean(b) - st.mean(a)))
