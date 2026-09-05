# -*- coding: utf-8 -*-
"""N-43b: Ist `vola` unabhaengig von `funding`? (05.09.2026)

## Warum das VOR der Entscheidung kommt

N-43 hat `vola` als einzigen Kandidaten gefunden, der BEIDE Kriterien
erfuellt:

    Abdeckung    516 von 516 Symbolen   = 100 %
    Stabilitaet  +0,647 gegen den Nullpunkt -0,013 der Kunstgroesse
                 - zwischen der 2- und der 4-Punkt-Pflanzung

Das ist rund viermal so stabil wie `funding` (+0,180) und deckt fast doppelt
so viele Symbole.

⚠️ **Trotzdem waere die Registrierung verfrueht.** Ein zweiter Beitrag, der
dasselbe misst wie der erste, bringt keine zusaetzliche Information - er
verdoppelt nur ein vorhandenes Urteil und laesst die Bewertung breiter
aussehen, als sie ist. Genau davor warnt die stehende Vorgabe, Indikatoren
auch in KOMBINATION zu pruefen.

## Zwei Fragen, zwei Messungen

    1  UEBERLAPPUNG   Wie stark haengen die Fuenftel zusammen? Spearman
                      ueber alle (Tag, Symbol), bei denen beide vorliegen.

    2  BEDINGT        Ordnet `vola` die Barrieren-Quote noch INNERHALB
                      eines festen funding-Fuenftels? Das ist die
                      eigentliche Frage - eine hohe Ueberlappung waere
                      unschaedlich, solange vola darin noch trennt.

⚠️ Frage 2 ist die entscheidende. Eine Korrelation sagt nur, dass sich zwei
Groessen aehneln; sie sagt nicht, ob die zweite noch etwas beitraegt.

## Die Kontrolle

`zufall` laeuft in Frage 2 mit: eine Kunstgroesse darf INNERHALB eines
funding-Fuenftels nichts ordnen. Tut sie es doch, misst das Verfahren einen
Artefakt und keine Information.

    python pruefe_vola_unabhaengig.py
"""
from __future__ import annotations

import sys
from collections import defaultdict

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_eigenschaft_beitrag as B                       # noqa: E402
import messe_funding_niveau as F                            # noqa: E402
import messe_kandidaten_als_regel as K                      # noqa: E402
import messe_zielregel as ZR                                # noqa: E402
from messe_bewertung_kalibrierung import _fuenftel_je_tag   # noqa: E402
from messe_stufen_aus_quote import quote_je_fuenftel        # noqa: E402

SAAT = 20260905
MIND = 800


def main() -> int:
    print("Lade Reihen...", flush=True)
    reihen = B.lade()
    tage_je_sym = {s: [z[0] for z in roh] for s, roh in reihen.items()}
    zeilen = ZR.ergebnisse(reihen)
    print("  %d Anker · %d Reihen" % (len(zeilen), len(reihen)))

    funding = F.lade_funding()
    f5 = {}
    for art, q in (("vola", None), ("funding", funding), ("zufall", None)):
        print("  baue %s ..." % art, flush=True)
        f5[art] = _fuenftel_je_tag(K.baue(reihen, art, q, horizont=20))

    # ---- 1. Ueberlappung --------------------------------------------
    paare = []
    for tag, d in f5["vola"].items():
        dg = f5["funding"].get(tag) or {}
        for sym, v in d.items():
            g = dg.get(sym)
            if g is not None:
                paare.append((v, g))
    print()
    print("=" * 92)
    print("1. UEBERLAPPUNG der Fuenftel")
    print("=" * 92)
    if len(paare) < 100:
        print("  zu wenige gemeinsame Punkte")
    else:
        a = np.array([p[0] for p in paare], float)
        b = np.array([p[1] for p in paare], float)
        r = float(np.corrcoef(a, b)[0, 1])
        print("  %d gemeinsame (Tag, Symbol) · Korrelation der Fuenftel %+.3f"
              % (len(paare), r))
        print("  -> %s" % ("praktisch unabhaengig" if abs(r) < 0.15 else
                           "schwach gekoppelt" if abs(r) < 0.35 else
                           "⚠️ STARK gekoppelt - vola waere weitgehend Ersatz"))
        # Wie oft landet ein Wert im GLEICHEN Fuenftel?
        gleich = sum(1 for x, y in paare if x == y)
        print("  gleiches Fuenftel in %.1f %% der Faelle (Zufall waere 20 %%)"
              % (100.0 * gleich / len(paare)))

    # ---- 2. Bedingt: ordnet vola INNERHALB eines funding-Fuenftels? --
    print()
    print("=" * 92)
    print("2. BEDINGT — ordnet die Groesse noch INNERHALB eines funding-Fuenftels?")
    print("=" * 92)
    print("  Je funding-Fuenftel wird die Barrieren-Quote ueber die")
    print("  Fuenftel der zu pruefenden Groesse gemessen. Spanne in Punkten.")
    print()

    for art in ("vola", "zufall"):
        print("  %s" % art.upper())
        spannen = []
        for g in range(5):
            # nur die Anker, die in diesem funding-Fuenftel liegen
            nur = {}
            for tag, d in f5[art].items():
                dg = f5["funding"].get(tag) or {}
                treffer = {s: v for s, v in d.items() if dg.get(s) == g}
                if treffer:
                    nur[tag] = treffer
            je = quote_je_fuenftel(zeilen, tage_je_sym, nur)
            if not je or any(je.get(f, (0, 0))[1] < MIND for f in range(5)):
                n = min((je.get(f, (0, 0))[1] for f in range(5)), default=0)
                print("    funding-Fuenftel %d: zu duenn (n_min %d)" % (g, n))
                continue
            q = [100.0 * je[f][0] / je[f][1] for f in range(5)]
            sp = max(q) - min(q)
            spannen.append(sp)
            print("    funding-Fuenftel %d: %s · Spanne %.2f Punkte"
                  % (g, " ".join("%.1f" % x for x in q), sp))
        if spannen:
            print("    -> mittlere Spanne %.2f Punkte" % float(np.mean(spannen)))
        print()

    print("  ⚠️ LESEART")
    print("     vola deutlich ueber zufall -> sie traegt ZUSAETZLICH zu funding")
    print("     beide aehnlich             -> die Spanne ist ein Artefakt der")
    print("                                   Fuenftelbildung, kein Beitrag")
    return 0


if __name__ == "__main__":
    sys.exit(main())
