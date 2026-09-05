# -*- coding: utf-8 -*-
"""N-46b: Ist der `amihud`-Befund ein Artefakt nicht handelbarer Kurse? (05.09.2026)

## Der Vorbehalt

N-46 (F-223) hat `amihud` unter der Tagesklammer als staerksten Kandidaten
gemessen:

    amihud quer, Tagesklammer:  -2,79  -2,69  -0,36  +2,17  +3,72
                                Spanne 6,51 Punkte, streng monoton

Groesser als beide registrierten Beitraege, 100 % Abdeckung, unabhaengig.

⚠️ **Amihud misst Illiquiditaet, und das beste Fuenftel ist das
illiquideste.** Genau dort ist die Barrieren-Simulation am wenigsten
vertrauenswuerdig: sie rechnet auf OHLC-Kursen und kennt weder Slippage
noch duenne Buecher. Ein Hoch, das aus einem einzigen Kleinsttrade stammt,
zaehlt als Zielberuehrung - handelbar war es nie.

⚠️ **Das ist KEINE Gebuehrenfrage** (Regel 2 bleibt unberuehrt), sondern
die Frage, ob es den Kurs ueberhaupt gab.

## Die Messung

Der Befund wird auf **handelbare** Werte eingeschraenkt und neu gerechnet:

    ALLE           516 Symbole - der Ausgangsbefund
    OBERE HAELFTE  Symbole ueber dem Median des eigenen Medianumsatzes
    OBERES DRITTEL  die liquidesten - der schaerfste Test

Haelt die Spanne dort, ist sie kein Duennbuch-Artefakt. Bricht sie ein,
war der Befund genau das.

⚠️ **Die Einschraenkung geschieht ueber das SYMBOL, nicht ueber den
einzelnen Tag** - sonst waehlt man je Tag die gerade aktiven Werte aus und
baut sich eine Ueberlebensauswahl (Survivorship).

## Die Kontrolle

`zufall` laeuft in jeder Schicht mit. Er muss ueberall im Rauschen bleiben;
tut er es nicht, erzeugt die Einschraenkung selbst einen Effekt.

    python pruefe_amihud_handelbarkeit.py
"""
from __future__ import annotations

import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_eigenschaft_beitrag as B                       # noqa: E402
import messe_kandidaten_als_regel as K                      # noqa: E402
import messe_zielregel as ZR                                # noqa: E402
from messe_bewertung_kalibrierung import _fuenftel_je_tag   # noqa: E402
# ⚠️ IMPORTIERT, NICHT NACHGEBAUT - dieselbe Klammer wie in N-46.
from messe_fuenftel_mit_tagesklammer import (               # noqa: E402
    je_tag_und_fuenftel, abweichung_je_fuenftel, _spanne)

ARTEN = ("amihud", "vola", "schnitt50", "zufall")
MIND_TAGE = 200


def median_umsatz(reihen: dict) -> dict:
    """{sym: Median des Tagesumsatzes} - die Reihe ist (tag, c, h, l, vol)."""
    aus = {}
    for sym, roh in reihen.items():
        v = [float(z[4]) for z in roh
             if len(z) > 4 and z[4] is not None and float(z[4]) > 0]
        if v:
            aus[sym] = float(np.median(v))
    return aus


def main() -> int:
    print("Lade Reihen...", flush=True)
    reihen = B.lade()
    tage_je_sym = {s: [z[0] for z in roh] for s, roh in reihen.items()}
    zeilen = ZR.ergebnisse(reihen)
    print("  %d Anker · %d Reihen" % (len(zeilen), len(reihen)))

    mu = median_umsatz(reihen)
    werte = sorted(mu.values())
    gr_haelfte = werte[len(werte) // 2]
    gr_drittel = werte[2 * len(werte) // 3]
    schichten = (
        ("ALLE", None),
        ("OBERE HAELFTE", gr_haelfte),
        ("OBERES DRITTEL", gr_drittel),
    )
    print("  Medianumsatz: Median %.3g · oberes Drittel ab %.3g"
          % (gr_haelfte, gr_drittel))

    gebaut = {}
    for art in ARTEN:
        print("  baue %s ..." % art, flush=True)
        gebaut[art] = K.baue(reihen, art, None, horizont=20)

    for name, grenze in schichten:
        if grenze is None:
            erlaubt = set(reihen)
        else:
            erlaubt = {s for s, v in mu.items() if v >= grenze}
        print()
        print("=" * 92)
        print("%s — %d Symbole" % (name, len(erlaubt)))
        print("=" * 92)
        print("  %-11s %-34s %8s %s"
              % ("Groesse", "Abweichung je Fuenftel (Punkte)", "Spanne",
                 "Rauschen"))
        for art in ARTEN:
            # ⚠️ Die Fuenftel werden INNERHALB der Schicht neu gebildet -
            # sonst vergleicht man die liquiden Werte gegen eine Rangfolge,
            # die aus dem ganzen Universum stammt.
            eng = {tag: [e for e in liste if e["sym"] in erlaubt]
                   for tag, liste in gebaut[art].items()}
            eng = {t: v for t, v in eng.items() if len(v) >= 10}
            f5 = _fuenftel_je_tag(eng)
            tg, n_tage, feh = abweichung_je_fuenftel(
                je_tag_und_fuenftel(zeilen, tage_je_sym, f5))
            if n_tage < MIND_TAGE:
                print("  %-11s zu wenige verwertbare Tage (%d)" % (art, n_tage))
                continue
            gr = 2.0 * max(x for x in feh if x == x)
            sp = _spanne(tg)
            mark = "" if sp > gr else "   <- im Rauschen"
            print("  %-11s %-34s %7.2f %8.2f%s"
                  % (art, " ".join("%+5.2f" % x for x in tg), sp, gr, mark))

    print()
    print("=" * 92)
    print("⚠️ LESEART")
    print("=" * 92)
    print("  amihud haelt in allen Schichten  -> kein Duennbuch-Artefakt,")
    print("     der Beitrag ist registrierbar")
    print("  amihud bricht mit der Liquiditaet ein -> der Befund lebte von")
    print("     Kursen, die niemand handeln konnte. NICHT registrieren.")
    print("  `zufall` muss ueberall im Rauschen bleiben.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
