# -*- coding: utf-8 -*-
"""⚠️⚠️ VORANALYSE — VOR dem Bauen (21.09.2026).

ZWEI SYMBOLE STEHEN IM LAUFENDEN NENNER NACHWEISLICH FALSCH - WIE
NIMMT MAN SIE HERAUS, OHNE EINE NAMENSLISTE ZU BAUEN?

    XVG   SplyCur 1,6522e12   richtig 1,6522e10   Faktor 100 zu HOCH
    KNC   SplyCur 1,1264e7    richtig 2,0923e8    Faktor 18,6 zu NIEDRIG

Beide sind frisch (9 Tage, Grenze 21) und gehen taeglich in den Rang
ein. XVG bekommt dadurch dauerhaft das unterste Fuenftel (+3,15 Punkte,
die groesste Stufe im System), KNC dauerhaft das oberste (-2,40).

═══════════════════════════════════════════════════════════════════════
 DREI FRAGEN, BEVOR IRGENDETWAS GEBAUT WIRD
═══════════════════════════════════════════════════════════════════════

**A - GIBT ES EINE STRUKTURELLE SPERRE?** Eine Namensliste veraltet
still (`pruefung-zaehlt-zustaende-auf`). Die Decke von `turnover`
(2.504-umschlagdecke, 1,0) faengt sie NICHT: XVG landet durch die zu
hohe Menge zu TIEF, KNC bei rund 0,19 - hoch, aber unter der Decke.
Also: wo liegen sie in der Verteilung, und trennt ein BODEN sie sauber
ab?

**B - WAS KOSTET DAS ENTFERNEN?** Ein Rang ist ein Perzentil. Wer die
Menge aendert, aendert jeden Wert darin
(`grundgesamtheit-ist-keine-stellschraube`). Zwei von 66 Symbolen sind
3 Prozent - aber die Fuenftelgrenzen verschieben sich fuer ALLE.
Gemessen wird, wie viele Symbol-Tage das Fuenftel wechseln.

**C - WELCHE SPERRE TRIFFT GENAU DIESE ZWEI?** Eine Regel, die
nebenbei zehn gesunde Symbole mitnimmt, ist schlechter als der Fehler,
den sie behebt.

⚠️ NUR LESEND. Es wird NICHTS gebaut - diese Datei entscheidet, WAS
gebaut wird.

    python phase4_c_plausibilitaet_nenner.py
"""
from __future__ import annotations

import os
import statistics as st
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
os.chdir("D:/CLAUDE_Projects/SoftwareProjekte/TradingInfoTool")
sys.path.insert(0, "D:/CLAUDE_Projects/SoftwareProjekte/TradingInfoTool")

import agent.marktrang as MR                               # noqa: E402
import messe_bewertungskennzahl as MB                      # noqa: E402
import messe_eigenschaft_beitrag as B                      # noqa: E402
import messe_kandidaten_als_regel as K                     # noqa: E402

HORIZONT = 20
# ⚠️ Die beiden belegten Faelle - hier NICHT als Sperrliste, sondern als
# das, was die Sperre finden MUSS. Der Unterschied ist wesentlich.
BELEGT_FALSCH = ("XVG", "KNC")


def main() -> int:
    print("=" * 104)
    print("VORANALYSE - wie nimmt man zwei falsche Nenner heraus?")
    print("=" * 104)
    reihen = B.lade()
    splycur = MB.reihe("data/onchain_historie.db", "splycur")
    je_tag = K.baue(reihen, "turnover", splycur, horizont=HORIZONT)
    print("  Basis: %d Kalendertage · %d Symbole"
          % (len(je_tag), len({x["sym"] for z in je_tag.values()
                               for x in z})))

    # ---- A  die Verteilung, beide Raender ----------------------------
    je_sym = {}
    for _t, z in je_tag.items():
        for x in z:
            je_sym.setdefault(x["sym"], []).append(float(x["kennzahl"]))
    med = {s: st.median(v) for s, v in je_sym.items() if len(v) >= 60}
    werte = sorted(med.values())
    print()
    print("-" * 104)
    print("  A) DIE VERTEILUNG DES UMSCHLAGS - beide Raender")
    print("-" * 104)
    print("     %d Symbole mit mindestens 60 Tagen" % len(med))
    for q in (0, 1, 5, 25, 50, 75, 95, 99, 100):
        i = min(len(werte) - 1, int(round(q / 100.0 * (len(werte) - 1))))
        print("       %3d. Perzentil  %12.6g" % (q, werte[i]))
    print()
    print("     %-8s %14s %10s   %s" % ("Symbol", "Median", "Perzentil",
                                        "Lage"))
    for s in BELEGT_FALSCH:
        if s not in med:
            print("     %-8s nicht in der Basis" % s)
            continue
        p = 100.0 * sum(1 for v in werte if v < med[s]) / len(werte)
        print("     %-8s %14.6g %9.0f %%   %s"
              % (s, med[s], p,
                 "unterer Rand" if p < 10 else
                 ("oberer Rand" if p > 90 else "⚠️ MITTENDRIN - eine "
                  "Randsperre faengt es NICHT")))
    print()
    print("     ⚠️ Wer am Rand liegt, ist mit einer Schwelle zu fangen. "
          "Wer mittendrin")
    print("        liegt, NICHT - dann braucht es eine zweite Quelle.")

    # ---- B  was kostet das Entfernen? --------------------------------
    print()
    print("-" * 104)
    print("  B) WAS KOSTET DAS ENTFERNEN? - die Grundgesamtheit ist "
          "keine Stellschraube")
    print("-" * 104)
    raus = {s for s in BELEGT_FALSCH if s in med}
    gew = gleich = 0
    zwei = 0
    betroffen = {}
    for _t, z in je_tag.items():
        mit = {x["sym"]: float(x["kennzahl"]) for x in z}
        ohne = {s: w for s, w in mit.items() if s not in raus}
        if len(ohne) < 12:
            continue
        ra, rb = MR._rang(mit), MR._rang(ohne)
        for s in ohne:
            fa, fb = MR._fuenftel(ra[s]), MR._fuenftel(rb[s])
            if fa == fb:
                gleich += 1
            else:
                gew += 1
                zwei += (abs(fa - fb) >= 2)
                betroffen[s] = betroffen.get(s, 0) + 1
    ges = gew + gleich
    print("     entfernt: %s" % ", ".join(sorted(raus)))
    print("     Symbol-Tage der UEBRIGEN verglichen: %d" % ges)
    print("     Fuenftel gewechselt: %d = %.2f %%"
          % (gew, 100.0 * gew / ges if ges else 0))
    print("     davon um zwei oder mehr Stufen: %d" % zwei)
    if betroffen:
        print("     die fuenf am staerksten betroffenen:")
        for s, n in sorted(betroffen.items(), key=lambda x: -x[1])[:5]:
            tage = len(je_sym.get(s, []))
            print("       %-8s %4d von %4d Tagen = %.0f %%"
                  % (s, n, tage, 100.0 * n / tage if tage else 0))
    print()
    print("     ⚠️ Zum Vergleich: die Frischegrenze im Haus akzeptiert "
          "6,5 %% Wechsel.")

    # ---- C  welche Sperre traefe genau diese zwei? -------------------
    print()
    print("-" * 104)
    print("  C) WELCHE SPERRE TRAEFE GENAU DIESE ZWEI - und wen noch?")
    print("-" * 104)
    print("     %-34s %8s   %s" % ("Sperre", "trifft", "Kollateral"))
    for name, fn in (
            ("Umschlag ueber 1,0 (Decke, 2.504)",
             lambda v: v > 1.0),
            ("Umschlag unter dem 1. Perzentil",
             lambda v: v < werte[max(0, int(0.01 * (len(werte) - 1)))]),
            ("Umschlag unter 1e-4",
             lambda v: v < 1e-4),
            ("Umschlag unter 1e-5",
             lambda v: v < 1e-5),
            ("Umschlag ueber dem 99. Perzentil",
             lambda v: v > werte[int(0.99 * (len(werte) - 1))])):
        trifft = sorted(s for s, v in med.items() if fn(v))
        soll = set(BELEGT_FALSCH) & set(med)
        kollateral = sorted(set(trifft) - soll)
        fehlt = sorted(soll - set(trifft))
        print("     %-34s %8d   %s%s"
              % (name, len(trifft),
                 ", ".join(kollateral[:6]) if kollateral else "keines",
                 ("  ⚠️ verfehlt %s" % ", ".join(fehlt)) if fehlt else
                 "  ✔ trifft beide"))
    print()
    print("     ⚠️⚠️ EINE SPERRE, DIE GESUNDE SYMBOLE MITNIMMT, IST "
          "SCHLECHTER ALS DER")
    print("        FEHLER, DEN SIE BEHEBT. Trifft keine Schwelle beide "
          "ohne Kollateral,")
    print("        ist die strukturelle Sperre nicht die "
          "Zweitquellenpruefung - dann")
    print("        gehoert die zweite Quelle in den Betrieb, nicht eine "
          "Schwelle.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
