# -*- coding: utf-8 -*-
"""Haelt der QUERSCHNITTS-Befund auch je Marktphase? (30.08.2026)

Anlass: die Je-Reihe-Sicht trug nur OHNE Marktkontrolle (+0,169) und fiel MIT
(-0,076). Also war sie Markt-Timing. Die Frage ist damit unausweichlich:

    Ist auch der Querschnittsbefund Markt-Timing?

Er sollte es NICHT sein - er vergleicht Assets an DEMSELBEN Tag, haelt die
Marktlage also per Konstruktion fest. Das ist zu belegen, nicht zu behaupten.

Geprueft wird je Marktphase (BTC ueber/unter seinem 200-Tage-Schnitt) und je
Funding-Marktniveau (Tage mit hohem/niedrigem Markt-Funding).
"""
import statistics as st, sys
import numpy as np
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import messe_funding_niveau as F
import messe_bewertungskennzahl as M
import messe_eigenschaft_beitrag as B

reihen = B.lade(); funding = F.lade_funding()
rng = np.random.default_rng(555)
HOR = 20

# BTC-Phase je Tag
btc = reihen.get("BTC")
phase = {}
if btc:
    tage = [z[0] for z in btc]; c = np.array([z[1] for z in btc])
    for i in range(200, len(c)):
        phase[tage[i]] = "auf" if c[i] > c[i-200:i].mean() else "ab"

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
            {"sym": sym, "kennzahl": f[tage[i]],
             "in_r": float((c[i+HOR] - c[i]) / r)})
je_tag = {t: z for t, z in je_tag.items() if len(z) >= 12}

print("=" * 84)
print("QUERSCHNITT je MARKTPHASE  (%d Kalendertage)" % len(je_tag))
print("=" * 84)
for p in ("auf", "ab"):
    teil = {t: z for t, z in je_tag.items() if phase.get(t) == p}
    M.urteil_tage("  BTC %s (%d Tage)" % (p.upper(), len(teil)),
                  M.je_tag_quer(teil), rng, 250)
print()
print("je MARKT-FUNDINGNIVEAU (sind es nur die ueberhitzten Tage?)")
median_tag = {t: st.median([x["kennzahl"] for x in z]) for t, z in je_tag.items()}
schwelle = st.median(list(median_tag.values()))
for name, bed in (("Markt-Funding NIEDRIG", lambda v: v <= schwelle),
                  ("Markt-Funding HOCH", lambda v: v > schwelle)):
    teil = {t: z for t, z in je_tag.items() if bed(median_tag[t])}
    M.urteil_tage("  %s (%d Tage)" % (name, len(teil)),
                  M.je_tag_quer(teil), rng, 250)
print()
print("und die JUENGSTE Zeit — seit dem Marktwechsel am 22.08.2026 gibt es zu")
print("wenige Tage; deshalb das letzte JAHR:")
letzte = {t: z for t, z in je_tag.items() if t >= "2025-08-30"}
M.urteil_tage("  seit 30.08.2025 (%d Tage)" % len(letzte),
              M.je_tag_quer(letzte), rng, 90)
