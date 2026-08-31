# -*- coding: utf-8 -*-
"""R-A: Traegt ein WEITERES Ziel? (30.08.2026)

Die Luecke in K-2: geprueft wurde nur OHNE ZIEL gegen ZIEL 2,0 - und das fiel
an den Ausreiszern, weil "ohne Ziel" nach oben unbegrenzt ist (groeszter Wert
+80.584 R vor der Bereinigung).

ZIEL 3,0 und ZIEL 5,0 sind dagegen GEDECKELT: der Gewinn kann nie ueber +3
bzw. +5 R liegen, der Verlust nie unter -1 R. Ein einzelner Anker kann das
Mittel damit nicht dominieren. Der Vergleich ist robust messbar - und wurde
schlicht nicht gemacht.

## Vorab festgelegt

  traegt        ZIEL 5,0 minus ZIEL 2,0 ist positiv, das Bootstrap-Intervall
                UEBER DIE REIHEN schliesst die Null nicht ein, und der Befund
                haelt in beiden Haelften der Historie
  traegt nicht  sonst
"""
import sys
import numpy as np
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import messe_eigenschaft_beitrag as B
import messe_zielregel as Z

reihen = B.lade()
zeilen = Z.ergebnisse(reihen)
rng = np.random.default_rng(20260830)
print("=" * 84)
print("R-A — TRAEGT EIN WEITERES ZIEL?  (%d Anker, bereinigt)" % len(zeilen))
print("=" * 84)

def urteil(name_a, name_b, teil, titel):
    d = np.array([z[name_a] - z[name_b] for z in teil])
    s = np.sort(d)
    k = max(1, len(s)//100)
    # je Reihe - die ehrliche Einheit
    je = {}
    for z in teil:
        je.setdefault(z["sym"], []).append(z[name_a] - z[name_b])
    w = np.array([np.mean(v) for v in je.values()])
    n = len(w)
    boot = np.array([w[rng.integers(0, n, n)].mean() for _ in range(20000)])
    u, o = np.quantile(boot, [0.025, 0.975])
    print("  %-22s %+8.4f R   getrimmt %+8.4f   Anteil + %5.1f %%"
          % (titel, d.mean(), s[:-k].mean(), 100*(d > 0).mean()))
    print("  %-22s je Reihe %+8.4f R  [%+.4f .. %+.4f]  %d von %d positiv   %s"
          % ("", w.mean(), u, o, int((w > 0).sum()), n,
             "TRAEGT" if u > 0 else ("SCHADET" if o < 0 else "nicht trennbar")))

print()
print("GEPAARTE VERGLEICHE, alle auf denselben Ankern und demselben Pfad")
for a, b in (("ZIEL 3,0", "ZIEL 2,0"), ("ZIEL 5,0", "ZIEL 2,0"), ("ZIEL 5,0", "ZIEL 3,0")):
    urteil(a, b, zeilen, "%s minus %s" % (a, b))
    print()

print("ZEITSTABILITAET von ZIEL 5,0 minus ZIEL 2,0")
zeilen_s = sorted(zeilen, key=lambda z: (z["sym"], z["i"]))
# Haelften ueber die Zeitachse je Reihe
h1, h2 = [], []
je = {}
for z in zeilen:
    je.setdefault(z["sym"], []).append(z)
for v in je.values():
    v.sort(key=lambda z: z["i"])
    h1.extend(v[:len(v)//2]); h2.extend(v[len(v)//2:])
for titel, teil in (("erste Haelfte", h1), ("zweite Haelfte", h2)):
    urteil("ZIEL 5,0", "ZIEL 2,0", teil, titel)
    print()

print("JE MARKTPHASE")
for titel, teil in (("aufwaerts", [z for z in zeilen if z["steigend"]]),
                    ("abwaerts", [z for z in zeilen if not z["steigend"]])):
    urteil("ZIEL 5,0", "ZIEL 2,0", teil, titel)
    print()
