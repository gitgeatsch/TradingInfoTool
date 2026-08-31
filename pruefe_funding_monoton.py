# -*- coding: utf-8 -*-
"""V4 richtig gerechnet: die Fuenftel JE TAG, nicht gepoolt.

Der Widerspruch: gepoolt ueber alle Anker liegen alle fuenf Funding-Fuenftel
bei rund -0,53 R (Unterschied +0,011). Der Hauptbefund sagt +0,137 R.

Der Grund kann nur in der TAGESSTRUKTUR liegen: gepoolt mischen sich
Marktphasen, je Tag ist die Marktlage festgehalten. Welche Rechnung stimmt,
entscheidet ueber die Anwendbarkeit - eine Groesse ohne monotonen Verlauf
kann man nicht als Rangfolge benutzen.
"""
import statistics as st, sys
import numpy as np
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import messe_funding_niveau as F
import messe_eigenschaft_beitrag as B

reihen = B.lade(); funding = F.lade_funding()
HOR = 20
je_tag = {}
for sym, roh in reihen.items():
    f = funding.get(sym.upper())
    if not f:
        continue
    tage = [z[0] for z in roh]
    c = np.array([z[1] for z in roh])
    h = np.array([z[2] for z in roh]); t_ = np.array([z[3] for z in roh])
    breite = B.spanne(h, t_, c, B.SCHWANKUNG)
    for i in range(60, len(c) - HOR):
        r = breite[i]
        if not np.isfinite(r) or r <= 0 or tage[i] not in f:
            continue
        je_tag.setdefault(tage[i], []).append(
            (f[tage[i]], float((c[i+HOR] - c[i]) / r)))
je_tag = {t: z for t, z in je_tag.items() if len(z) >= 15}

print("=" * 76)
print("V4 KORRIGIERT — Funding-Fuenftel JE TAG (Marktlage festgehalten)")
print("=" * 76)
print("%d Kalendertage" % len(je_tag))
print()
# je Tag die Fuenftel bilden, dann ueber die Tage mitteln
sammel = {k: [] for k in range(5)}
for z in je_tag.values():
    w = np.array([x[0] for x in z]); y = np.array([x[1] for x in z])
    r = np.argsort(np.argsort(w)) / max(len(w)-1, 1)
    for k in range(5):
        maske = (r >= k/5) & (r < (k+1)/5 if k < 4 else r <= 1.0)
        if maske.sum() >= 2:
            sammel[k].append(float(np.median(y[maske])))
print("  Fuenftel   Tage    Median-Bewegung (Mittel ueber die Tage)")
werte = []
for k in range(5):
    m = st.mean(sammel[k])
    werte.append(m)
    print("     %d      %5d          %+.4f R" % (k, len(sammel[k]), m))
print()
print("  niedrigstes minus hoechstes: %+.4f R" % (werte[0] - werte[4]))
mono = all(werte[i] >= werte[i+1] - 0.02 for i in range(4))
print("  monoton fallend? %s" % ("ja" if mono else "NEIN - kein stetiger Verlauf"))
print()
print("  Zum Vergleich gepoolt ueber alle Anker (mischt Marktphasen):")
alle = [(x[0], x[1]) for z in je_tag.values() for x in z]
w = np.array([a for a, _ in alle]); y = np.array([b for _, b in alle])
r = np.argsort(np.argsort(w)) / max(len(w)-1, 1)
for k in range(5):
    maske = (r >= k/5) & (r < (k+1)/5 if k < 4 else r <= 1.0)
    print("     %d      %6d Anker     %+.4f R" % (k, maske.sum(), np.median(y[maske])))
