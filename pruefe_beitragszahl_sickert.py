# -*- coding: utf-8 -*-
"""N-41g: WELCHE der beiden Ursachen? (05.09.2026)

Die Invarianzpruefung (F-218) zeigte: ein additiver Versatz c auf ALLE
Stufen senkt die gemessene Steigung monoton (0,089 -> 0,052 bei c=2).
Dafuer gibt es zwei Erklaerungen, und sie haben sehr verschiedene Folgen:

  URSACHE A  Die Gruppierung nach `round(wert_r, 3)` schneidet bei jedem
             Versatz anders. -> Das MESSWERKZEUG ist kaputt, die Bewertung
             nicht. Reparatur: nicht binnen, sondern stetig regressieren.

  URSACHE B  Der Versatz ist gar nicht konstant JE ANKER: wo beide
             Beitraege greifen, wandert das Potential um 2c, wo nur einer
             greift, um c. Dann verschiebt eine Konstante die RANGFOLGE -
             und die ZAHL der vorhandenen Beitraege steckt in der
             Bewertung. -> Die BEWERTUNG ist betroffen, nicht nur das Mass.

⚠️ B waere die teurere Diagnose und deckt sich mit dem registrierten
Befund "Die Summe der Beitraege taugt nicht als Rangfolge".

## Die Unterscheidung

    1  Wie viele Anker bekommen 0, 1, 2 Beitraege?
       Bekommen ALLE zwei, scheidet B aus.

    2  Steigung nur auf den Ankern mit VOLLSTAENDIGEN Beitraegen.
       Ist sie dort invariant gegen c, war es B.
       Wandert sie auch dort, ist (auch) A im Spiel.

    python pruefe_beitragszahl_sickert.py
"""
from __future__ import annotations

import sys
from collections import Counter

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_bewertungskennzahl as MB                       # noqa: E402
import messe_eigenschaft_beitrag as B                       # noqa: E402
import messe_funding_niveau as F                            # noqa: E402
import messe_kandidaten_als_regel as K                      # noqa: E402
import messe_zielregel as ZR                                # noqa: E402
from messe_bewertung_kalibrierung import (                  # noqa: E402
    _fuenftel_je_tag, _steigung, baue_gruppen, _mit_stufen)
from agent import wahrscheinlichkeit as W                   # noqa: E402

SAAT = 20260905


def main() -> int:
    print("Lade Reihen...", flush=True)
    reihen = B.lade()
    tage_je_sym = {s: [z[0] for z in roh] for s, roh in reihen.items()}
    zeilen = ZR.ergebnisse(reihen)
    quellen = {"funding": F.lade_funding(),
               "turnover": MB.reihe("data/onchain_historie.db", "splycur")}
    f5 = {a: _fuenftel_je_tag(K.baue(reihen, a, quellen[a], horizont=20))
          for a in ("funding", "turnover")}
    alle = sorted(set(f5["funding"]) | set(f5["turnover"]))
    zweite = {t for t in alle if t >= alle[len(alle) // 2]}

    # ---- 1. Wie viele Beitraege greifen je Anker? --------------------
    zaehl = Counter()
    voll_tage = Counter()
    for z in zeilen:
        tage = tage_je_sym.get(z["sym"])
        if not tage or z["i"] >= len(tage):
            continue
        tag = tage[z["i"]]
        if tag not in zweite:
            continue
        n = sum(1 for a in ("funding", "turnover")
                if (f5[a].get(tag) or {}).get(z["sym"]) is not None)
        zaehl[n] += 1
        if n == 2:
            voll_tage[tag] += 1

    ges = sum(zaehl.values())
    print()
    print("=" * 92)
    print("1. WIE VIELE BEITRAEGE GREIFEN JE ANKER? (zweite Haelfte)")
    print("=" * 92)
    for n in sorted(zaehl):
        print("    %d Beitraege  %8d  (%5.1f %%)" % (n, zaehl[n], 100 * zaehl[n] / max(ges, 1)))
    if zaehl.get(2, 0) == ges:
        print("  -> ALLE Anker vollstaendig: Ursache B scheidet aus")
    else:
        print("  ⚠️ NICHT alle Anker vollstaendig -> ein additiver Versatz")
        print("     verschiebt die Rangfolge. Ursache B ist moeglich.")

    # ---- 2. Steigung NUR auf vollstaendigen Ankern -------------------
    print()
    print("=" * 92)
    print("2. INVARIANZ auf den VOLLSTAENDIGEN Ankern")
    print("=" * 92)
    print("  Nur Tage, an denen beide Beitraege vorliegen. Dort ist der")
    print("  Versatz je Anker WIRKLICH konstant - die Steigung MUSS halten.")
    print()
    # ⚠️ JE ANKER FILTERN, NICHT JE TAG (05.09., eigener Fehler im ersten
    # Anlauf). `nur_tage=` behaelt einen Tag, sobald EIN Anker vollstaendig
    # ist - das waren 1.323 von 1.363 Tagen, also praktisch alles. Der Test
    # mass dieselbe Stichprobe wie zuvor und konnte nichts unterscheiden.
    voll_zeilen = []
    for z in zeilen:
        tage = tage_je_sym.get(z["sym"])
        if not tage or z["i"] >= len(tage):
            continue
        tag = tage[z["i"]]
        if all((f5[a].get(tag) or {}).get(z["sym"]) is not None
               for a in ("funding", "turnover")):
            voll_zeilen.append(z)
    print("  %d von %d Ankern sind vollstaendig" % (len(voll_zeilen), len(zeilen)))
    nur_voll = zweite

    grund_f = next((b.stufen for b in W.BEITRAEGE
                    if b.merkmal == "funding_fuenftel" and b.stufen), [0.0] * 5)
    grund_t = next((b.stufen for b in W.BEITRAEGE
                    if b.merkmal == "turnover_fuenftel" and b.stufen), [0.0] * 5)

    alt = W.BEITRAEGE
    try:
        for c in (0.0, 2.0):
            W.BEITRAEGE = _mit_stufen([x + c for x in grund_f],
                                      [x + c for x in grund_t])
            rng = np.random.default_rng(SAAT)
            g = baue_gruppen(voll_zeilen, tage_je_sym, f5["funding"],
                             f5["turnover"], nur_tage=nur_voll)
            print()
            print("  c = %+.1f · %d Gruppen" % (c, len(g)))
            _steigung(g, rng)
    finally:
        W.BEITRAEGE = alt

    print()
    print("  ⚠️ LESEART")
    print("     Steigung HAELT hier -> Ursache B: die Zahl der Beitraege")
    print("        sickert in die Bewertung. Das MASS ist in Ordnung.")
    print("     Steigung WANDERT auch hier -> Ursache A: die Gruppierung")
    print("        nach round(wert_r,3) taugt nicht. Beide koennen gelten.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
