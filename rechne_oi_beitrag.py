# -*- coding: utf-8 -*-
"""H-4c': wieviele PUNKTE traegt `oi_aenderung` je Fuenftel? (02.09.2026)

Dieselbe Rechnung wie `rechne_funding_beitrag.py` und
`rechne_turnover_beitrag.py` - kein neues Verfahren, damit der dritte
Beitrag ueber DENSELBEN Massstab laeuft wie die beiden bestehenden.

    Potential = quote * CRV - (1 - quote)
    d(Potential) = d(quote) * (1 + CRV)   ->   d(quote) = d(Potential)/(1+CRV)

⚠️ IN-SAMPLE, und deshalb halbiert - dieselbe Vorsicht wie bei den beiden
anderen.

## Vorab festgelegt, BEVOR die Zahlen da sind

  nutzbar        die Stufen sind MONOTON ueber die Fuenftel und die Spanne
                 ist groesser als null
  nicht nutzbar  sonst - dann wird NICHT registriert

⚠️ Genau an dieser Bedingung ist der Schnittabstand am 31.08. gescheitert
(+1,27 / +1,59 / ...), und ich hatte ihn trotzdem registriert. Sie steht
hier, damit das nicht ein zweites Mal passiert.

## ⚠️ Was diese Datei NICHT entscheidet

Ob der Beitrag eingebaut wird. Nach R-R9 verlangt jeder Beitragswechsel
eine NEUKALIBRIERUNG der Schwelle - und die Vorgabe (heute 0,080) ist eine
Nutzerentscheidung. Diese Datei liefert nur die Zahlen dafuer.

    python rechne_oi_beitrag.py [--horizont 20]
"""
import argparse as _ap
import statistics as st
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_eigenschaft_beitrag as B
import messe_kandidaten_als_regel as K

_a = _ap.ArgumentParser()
_a.add_argument("--horizont", type=int, default=20)
HOR = _a.parse_known_args()[0].horizont
CRV = 2.0

print("HORIZONT H%d" % HOR)
reihen = B.lade()
tm = K.lade_terminmarkt()
quelle = tm["oi_aenderung"]

je_tag = {}
for sym, roh in reihen.items():
    f = quelle.get(sym.upper())
    if not f:
        continue
    tage = [z[0] for z in roh]
    c = np.array([z[1] for z in roh])
    h = np.array([z[2] for z in roh])
    t_ = np.array([z[3] for z in roh])
    breite = B.spanne(h, t_, c, B.SCHWANKUNG)
    for i in range(60, len(c) - HOR):
        r = breite[i]
        if not np.isfinite(r) or r <= 0 or tage[i] not in f:
            continue
        je_tag.setdefault(tage[i], []).append(
            (f[tage[i]], float((c[i + HOR] - c[i]) / r)))
je_tag = {t: z for t, z in je_tag.items() if len(z) >= 15}

sammel = {k: [] for k in range(5)}
for z in je_tag.values():
    w = np.array([x[0] for x in z])
    y = np.array([x[1] for x in z])
    r = np.argsort(np.argsort(w)) / max(len(w) - 1, 1)
    for k in range(5):
        m = (r >= k / 5) & (r < (k + 1) / 5 if k < 4 else r <= 1.0)
        if m.sum() >= 2:
            sammel[k].append(float(np.median(y[m])))
werte = [st.mean(sammel[k]) for k in range(5)]
mittel = st.mean(werte)
faktor = 1.0 / (1.0 + CRV)

print("=" * 78)
print("H-4c' — die BEITRAGSTABELLE fuer `oi_aenderung`")
print("=" * 78)
print("%d Kalendertage, %d Symbole, Horizont %d, CRV %.1f"
      % (len(je_tag), len({x for z in je_tag.values() for x in ()}) or
         len({s for s in reihen if s.upper() in quelle}), HOR, CRV))
print()
print("  ⚠️ Fuenftel 0 ist der NIEDRIGSTE Rohwert (`marktrang._rang` sortiert")
print("     aufsteigend). Bei `oi_aenderung` ist niedrig das Gute - starker")
print("     OI-Aufbau heisst gehebelte Ueberhitzung. Wer die Sortierrichtung")
print("     dreht, dreht den Beitrag ins Gegenteil, ohne dass etwas anschlaegt.")
print()
print("  Fuenftel  Bewegung   gegen Mittel   Punkte roh   Punkte GESCHRUMPFT")
punkte = []
for k in range(5):
    ab = werte[k] - mittel
    roh = 100.0 * ab * faktor
    punkte.append(roh / 2.0)
    print("     %d     %+.4f R    %+.4f R      %+5.2f       %+5.2f"
          % (k, werte[k], ab, roh, roh / 2.0))
print()
spanne = 100 * (werte[0] - werte[4]) * faktor
print("  Spanne unterstes gegen oberstes Fuenftel: %+.2f roh, %+.2f geschrumpft"
      % (spanne, spanne / 2))
print("  Zum Vergleich: Funding %+.2f, Turnover %+.2f (geschrumpft)"
      % (0.82 - (-1.70), 3.15 - (-2.40)))
print()

# ---- DIE VORAB FESTGELEGTE BEDINGUNG --------------------------------------
fallend = all(punkte[k] >= punkte[k + 1] for k in range(4))
steigend = all(punkte[k] <= punkte[k + 1] for k in range(4))
monoton = fallend or steigend
print("=" * 78)
print("  MONOTON ueber die fuenf Fuenftel:  %s" % ("JA" if monoton else "NEIN"))
print("  Spanne groesser null:              %s" % ("JA" if abs(spanne) > 0 else "NEIN"))
print("  ->  %s" % ("✔ NUTZBAR - die Stufen duerfen registriert werden, "
                    "sobald die\n      Schwelle nach R-R9 neu kalibriert ist"
                    if monoton and abs(spanne) > 0 else
                    "✖ NICHT NUTZBAR - nicht registrieren. Der Befund aus\n"
                    "      H-4c bleibt bestehen, aber er ist in dieser Form\n"
                    "      nicht als abgestufter Beitrag verwendbar."))
print("=" * 78)
print()
print("  stufen=(%s)," % ", ".join("%+.2f" % p for p in punkte))
