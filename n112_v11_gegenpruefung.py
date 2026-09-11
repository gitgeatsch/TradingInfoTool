# -*- coding: utf-8 -*-
"""V11 GEGENPRUEFUNG — und der Auswahl-Test, den ich gestern versaeumt habe

## ⚠️⚠️⚠️ Der Grund fuer diesen Lauf steht im Docstring des Werkzeugs

`n68_zeitstabilitaet.entzerrte_reihe` traegt seit dem 09.09. einen
Parameter `auswahl_saat` - und die Begruendung dazu:

> *„N-88 hat gezeigt, dass `schnitt`s Haelftenunterschied NUR auf den
> schmalen Momentum-Mengen kippt (-0,431 bei 5 %, +0,197 bei 20 %) und
> auf den weiten ruhig ist (+0,002 bei 50 %, +0,018 auf `frei`).
> **Der Verdacht: Kollinearitaet mit der Auswahl.** `schnitt` und das
> 250-Tage-Momentum korrelieren mit Spearman +0,704 ... Mit
> `auswahl_saat` wird je Tag GLEICH VIEL gewaehlt, aber ZUFAELLIG.
> **Traegt die Instabilitaet dann nicht mehr, ist sie eine Eigenschaft
> der AUSWAHL und nicht von `schnitt`.**"*

⚠️ **Ich habe ihn gestern nicht gesetzt.** Befund 2.325 (,`schnitt`
faellt an Kriterium 2') steht damit selbst zur Pruefung - und 2.222
haette mich darauf fuehren muessen:

> *„`schnitt`s WIRKUNG IST ZU VIER FUENFTELN EIN AUSWAHL-ARTEFAKT:
> +0,1858 auf der Momentummenge -> +0,0366 auf Zufallsmengen."*

Wenn seine WIRKUNG ein Auswahlartefakt ist, kann seine INSTABILITAET es
auch sein. Genau auf der 20-%-Menge, wo er faellt.

## Was hier geprueft wird - vier Fragen, alle vorab benannt

    G1  MASSSTAB      ist die entzerrte Reihe dieselbe Skala wie die
                      Wirkung? Sonst ist das Verhaeltnis in Teil C Unsinn
    G2  REPRODUKTION  treffen V11s Zahlen die von n108/n110/2.308?
    G3  ⚠️⚠️⚠️ DER AUSWAHL-TEST
                      mit ZUFAELLIGER statt Momentum-Auswahl, drei Saaten:
                      kippt `schnitt`s Haelftenunterschied dann noch?
    G4  SKALENBLIND?  Haelftenunterschied im VERHAELTNIS zur eigenen
                      Wirkung - bestraft Kriterium 2 die grosse Wirkung?

⚠️ **Drei Saaten, nicht eine** - ein Parameterwert ist kein Nachweis.

## Die Vorhersage, VOR dem Lauf (Methodik 2.80)

    G1  ⚠️ mean(entzerrt) ~ wirkung - nullpunkt. Trifft das nicht,
        faellt Teil C von V11
    G2  reproduziert - dieselben Werkzeuge, dieselbe Saat
    G3  ⚠️⚠️ ich erwarte, dass `schnitt`s Unterschied bei zufaelliger
        Auswahl DEUTLICH kleiner wird. Dann ist 2.325 zu relativieren:
        er faellt an einer Eigenschaft der AUSWAHL, nicht an sich
    G4  ⚠️ `schnitt` 1,06 · `funding` 0,89 · `schnitt50` 0,80 - alle
        drei bewegen sich um ~80 bis 106 % ihrer eigenen Wirkung.
        Dann trennt Kriterium 2 nicht stabil von instabil, sondern
        GROSS von KLEIN

    python n112_v11_gegenpruefung.py
"""
from __future__ import annotations

import sys
import time

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_eigenschaft_beitrag as B                         # noqa: E402
import messe_kandidaten_als_regel as K                        # noqa: E402
import messnorm as N                                          # noqa: E402
import messnorm_auswahl as MA                                 # noqa: E402
from messe_alle_kandidaten import HORIZONT, zusatzquellen     # noqa: E402
from messe_beitrag_auf_auswahl import momentum250             # noqa: E402
from n68_zeitstabilitaet import (entzerrte_reihe,             # noqa: E402
                                 stabilitaetsurteil)

KAND = ("schnitt", "schnitt50", "funding", "zufall")
SAATEN = (20260911, 4242, 99001)
# aus V11 (n111) - Wirkung je Menge
W = {("schnitt", "10%"): 0.1830, ("schnitt", "20%"): 0.1858,
     ("schnitt", "50%"): 0.0434,
     ("schnitt50", "10%"): 0.0846, ("schnitt50", "20%"): 0.0698,
     ("schnitt50", "50%"): 0.0156,
     ("funding", "10%"): 0.0688, ("funding", "20%"): 0.0582,
     ("funding", "50%"): 0.0313,
     ("zufall", "10%"): 0.0010, ("zufall", "20%"): 0.0163,
     ("zufall", "50%"): -0.0048}
NULLP = {("schnitt", "20%"): 0.0136, ("schnitt50", "20%"): 0.0140,
         ("funding", "20%"): 0.0141, ("zufall", "20%"): 0.0149}
# Haelftenunterschiede aus n110 (10.09.) - Reproduktionspruefung
H110 = {("schnitt", "10%"): -0.0805, ("schnitt", "20%"): 0.1973,
        ("schnitt", "50%"): 0.0024,
        ("schnitt50", "10%"): -0.0364, ("schnitt50", "20%"): 0.0560,
        ("schnitt50", "50%"): -0.0450,
        ("funding", "10%"): 0.0430, ("funding", "20%"): 0.0520,
        ("funding", "50%"): 0.0025,
        ("zufall", "10%"): -0.0215, ("zufall", "20%"): 0.0031,
        ("zufall", "50%"): -0.0183}
# N-88 (09.09.) - was der Docstring als bekannt nennt
N88 = {"5%": -0.431, "20%": 0.197, "50%": 0.002, "frei": 0.018}


def main() -> int:
    t0 = time.time()
    reihen = B.lade()
    mom = momentum250(reihen)
    zus = zusatzquellen()
    block = N._block(HORIZONT)
    je = {k: K.baue(reihen, k, zus.get(k), horizont=HORIZONT) for k in KAND}

    print("=" * 112)
    print("V11 GEGENPRUEFUNG — und der Auswahl-Test, den ich gestern "
          "versaeumt habe")
    print("=" * 112)

    # ---- G1  MASSSTAB ----------------------------------------------------
    print()
    print("G1  MASSSTAB — ist die entzerrte Reihe dieselbe Skala wie die "
          "Wirkung?")
    print("    Erwartet: mean(entzerrt) ~ Wirkung - Nullpunkt. Sonst ist "
          "Teil C von V11 Unsinn.")
    print("    %-10s %11s %10s %12s %12s  %s"
          % ("Kandidat", "Wirkung", "Nullpkt", "W - Null", "mean(entz)",
             "Urteil"))
    g1 = True
    for k in KAND:
        e = entzerrte_reihe(je[k], mom, MA.MENGEN["20%"])
        m = float(np.mean(list(e.values())))
        w, nu = W[(k, "20%")], NULLP[(k, "20%")]
        erw = w - nu
        gut = abs(m - erw) < 0.02
        g1 = g1 and gut
        print("    %-10s %+11.4f %+10.4f %+12.4f %+12.4f  %s"
              % (k, w, nu, erw, m,
                 "✔ gleiche Skala" if gut else "⚠️ WEICHT AB"))
    print("    -> %s" % ("✔ Teil C von V11 steht" if g1 else
                         "⚠️⚠️ Teil C von V11 FAELLT - andere Skala"))

    # ---- G2  REPRODUKTION ------------------------------------------------
    print()
    print("G2  REPRODUKTION — treffen die Haelftenunterschiede die von "
          "n110 (10.09.)?")
    print("    %-10s %-6s %11s %11s  %s"
          % ("Kandidat", "Menge", "n110", "jetzt", "Urteil"))
    g2 = True
    jetzt = {}
    for k in KAND:
        for m in ("10%", "20%", "50%"):
            e = entzerrte_reihe(je[k], mom, MA.MENGEN[m])
            r = stabilitaetsurteil(e, block)
            if r is None:
                continue
            jetzt[(k, m)] = r
            alt = H110[(k, m)]
            gut = abs(r["diff"] - alt) < 0.005
            g2 = g2 and gut
            print("    %-10s %-6s %+11.4f %+11.4f  %s"
                  % (k, m, alt, r["diff"],
                     "✔" if gut else "⚠️ WEICHT AB"), flush=True)
    print("    -> %s" % ("✔ n110 reproduziert - R-R11 erfuellt"
                         if g2 else "⚠️⚠️ NICHT reproduziert"))

    # ---- G3  DER AUSWAHL-TEST -------------------------------------------
    print()
    print("G3  ⚠️⚠️⚠️ DER AUSWAHL-TEST — Momentum-Auswahl gegen ZUFAELLIGE, "
          "gleich gross")
    print("    Traegt die Instabilitaet ohne die Momentum-Auswahl nicht "
          "mehr, ist sie eine")
    print("    Eigenschaft der AUSWAHL und nicht des Kandidaten "
          "(`entzerrte_reihe`-Docstring).")
    print("    ⚠️ DREI Saaten - ein Parameterwert ist kein Nachweis.")
    print()
    print("    %-10s %-6s %11s %28s  %s"
          % ("Kandidat", "Menge", "Momentum", "ZUFALLSauswahl (3 Saaten)",
             "Urteil bei Zufallsauswahl"))
    for k in KAND:
        for m in ("10%", "20%", "50%"):
            if (k, m) not in jetzt:
                continue
            diffs, urt = [], []
            for s in SAATEN:
                e = entzerrte_reihe(je[k], mom, MA.MENGEN[m],
                                    auswahl_saat=s)
                r = stabilitaetsurteil(e, block)
                if r is None:
                    continue
                diffs.append(r["diff"])
                urt.append("NICHT STABIL" if r["nachgewiesen"] else
                           "stabil" if r["stabil"] else "n.trennbar")
            if not diffs:
                continue
            nst = sum(1 for u in urt if u == "NICHT STABIL")
            print("    %-10s %-6s %+11.4f  %s  %s"
                  % (k, m, jetzt[(k, m)]["diff"],
                     " ".join("%+8.4f" % d for d in diffs),
                     ("⚠️ %d von %d NICHT STABIL" % (nst, len(urt)))
                     if nst else "✔ stabil in allen %d" % len(urt)),
                  flush=True)

    # ---- G4  SKALENBLIND? ------------------------------------------------
    print()
    print("G4  SKALENBLIND? — der Unterschied im VERHAELTNIS zur eigenen "
          "Wirkung")
    print("    Bewegen sich alle um einen aehnlichen ANTEIL ihrer Wirkung, "
          "trennt Kriterium 2")
    print("    nicht stabil von instabil, sondern GROSS von KLEIN.")
    print("    %-10s %-6s %10s %11s %9s  %s"
          % ("Kandidat", "Menge", "Wirkung", "Haelften", "Anteil",
             "Urteil"))
    for k in KAND:
        for m in ("10%", "20%", "50%"):
            r = jetzt.get((k, m))
            if r is None:
                continue
            w = W[(k, m)]
            q = abs(r["diff"]) / abs(w) if w else float("nan")
            print("    %-10s %-6s %+10.4f %+11.4f %9.2f  %s"
                  % (k, m, w, r["diff"], q, r["urteil"][:34]))
    print()
    print("    ⚠️ `zufall` hat fast keine Wirkung - sein Anteil explodiert "
          "und ist BEDEUTUNGSLOS.")
    print("       Vergleichbar sind nur die drei mit echter Wirkung.")
    print()
    print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
