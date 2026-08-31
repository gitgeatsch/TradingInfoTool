# -*- coding: utf-8 -*-
"""Gegenpruefung zum Funding-Befund (30.08.2026).

Vier Verdachtsmomente, alle VOR dem Lauf benannt:

  V1 MITLAEUFER   Ist Funding nur eine Umschreibung von MOMENTUM? Nach einem
                  Anstieg steigt das Funding, weil Longs draengen. Dann waere
                  der Befund die bekannte Mean Reversion in neuen Kleidern -
                  und Momentum ist im Projekt bereits als Kanal geprueft.
                  ⚠️ Der schwerste Einwand.
  V2 BLOCKLAENGE  Haelt der Befund auch bei sehr langen Bloecken?
  V3 SURVIVORSHIP 290 Symbole = die heute auf Binance Futures gelisteten.
  V4 RICHTUNG     Sitzt der Effekt bei EXTREM hohem Funding (Ueberhitzung) oder
                  ist er ueber die ganze Spanne stetig? Ein Schalter waere
                  schwaecher als eine stetige Groesse.
"""
import statistics as st, sys
import numpy as np
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import messe_funding_niveau as F
import messe_bewertungskennzahl as M
import messe_eigenschaft_beitrag as B

reihen = B.lade(); funding = F.lade_funding()
rng = np.random.default_rng(77)
HOR = 20

# Anker mit Funding UND Momentum
je_tag = {}
for sym, roh in reihen.items():
    f = funding.get(sym.upper())
    if not f:
        continue
    tage = [z[0] for z in roh]
    schluss = np.array([z[1] for z in roh])
    hoch = np.array([z[2] for z in roh]); tief = np.array([z[3] for z in roh])
    breite = B.spanne(hoch, tief, schluss, B.SCHWANKUNG)
    for i in range(60, len(schluss) - HOR):
        r = breite[i]
        if not np.isfinite(r) or r <= 0 or tage[i] not in f:
            continue
        je_tag.setdefault(tage[i], []).append({
            "sym": sym, "kennzahl": f[tage[i]],
            "momentum": float(schluss[i] / schluss[i-20] - 1.0),
            "in_r": float((schluss[i+HOR] - schluss[i]) / r)})
je_tag = {t: z for t, z in je_tag.items() if len(z) >= 12}

print("=" * 88)
print("GEGENPRUEFUNG FUNDING  (Horizont %d, %d Kalendertage)" % (HOR, len(je_tag)))
print("=" * 88)

print()
print("V1 — MITLAEUFER: ist Funding nur Momentum?")
alle = [x for z in je_tag.values() for x in z]
r = np.corrcoef([x["kennzahl"] for x in alle], [x["momentum"] for x in alle])[0,1]
print("  Korrelation Funding <-> Momentum: %+.3f" % r)
print("  Der Test: Funding-Effekt INNERHALB gleicher Momentum-Schicht")
for schicht, name in ((0, "unteres Momentum-Drittel"),
                      (1, "mittleres"), (2, "oberes")):
    teil = {}
    for t, z in je_tag.items():
        m = M.terzile([x["momentum"] for x in z])
        aus = [x for x, k in zip(z, m) if k == schicht]
        if len(aus) >= 8:
            teil[t] = aus
    M.urteil_tage("    %-26s" % name, M.je_tag_quer(teil), rng, 90)

print()
print("V2 — BLOCKLAENGE")
w = M.je_tag_quer(je_tag)
for block in (90, 180, 250, 400):
    M.urteil_tage("    Block %3d Tage" % block, w, rng, block)

print()
print("V4 — sitzt der Effekt am EXTREM oder ist er stetig?")
fuenftel = {}
for t, z in je_tag.items():
    r5 = np.argsort(np.argsort([x["kennzahl"] for x in z]))
    q = r5 / max(len(r5)-1, 1)
    for x, qq in zip(z, q):
        k = min(int(qq*5), 4)
        fuenftel.setdefault(k, []).append(x["in_r"])
print("  Funding-Fuenftel (0 = niedrigstes) -> Median-Bewegung in R")
for k in sorted(fuenftel):
    print("    %d  %6d Anker   Median %+.4f R" % (k, len(fuenftel[k]),
                                                   st.median(fuenftel[k])))
