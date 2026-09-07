# -*- coding: utf-8 -*-
"""SCHRITT 3 - DIE TRENNSCHAERFE JE MASSSTAB, auf echten Daten (06.09.2026)

## Die Frage, und warum sie vor allem anderen steht

Zweimal in zwei Tagen hat der MASSSTAB das Vorzeichen entschieden:

    05.09.  in_r gegen barriere   ->  TRAEGT gegen traegt nicht
    06.09.  Mittel gegen Rand     ->  "schlechter" gegen "BESSER"

Beide registrierten Beitraege (funding +0,0274 · turnover +0,0635) und
jedes "traegt nicht" der letzten Wochen sind am MITTELWERT gemessen. Bevor
irgendetwas weiter gemessen wird, muss entschieden sein, WORAN gemessen
wird - sonst ist jeder Lauf danach zu wiederholen.

## Was hier entschieden wird

    Randmass HAT Trennschaerfe   -> zweite Zielgroesse, Schritt 4a laeuft
                                    auf BEIDEN Massstaeben
    Randmass hat KEINE           -> wir bleiben beim Mittel, und 2.112 wird
                                    als benannte GRENZE gefuehrt, nicht als
                                    Loesung

⚠️ Das entscheidet die Messung, nicht die Plausibilitaet.

## Der faire Vergleich

Beide Massstaebe bekommen dieselbe koerperliche Pflanzung `y[gesperrt] -= s`
mit s in R. Verglichen wird das kleinste s, das der jeweilige Massstab
findet - dieselbe Einheit, dieselbe Welt, dieselben Bloecke.

## Dimensionierung (festgeschrieben, Plan vom 06.09.)

    Horizont 5 · Block 15 · ab 2024 · Klammer Tag · Kosten 0,00
    Menge frei (20 % folgt in Schritt 4a)

    python schritt3_trennschaerfe.py
"""
from __future__ import annotations

import sys
import time

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_bewertungskennzahl as MB                        # noqa: E402
import messe_eigenschaft_beitrag as B                        # noqa: E402
import messe_funding_niveau as F                             # noqa: E402
import messe_kandidaten_als_regel as K                       # noqa: E402
import messnorm as N                                         # noqa: E402
import messnorm_rand as R                                    # noqa: E402
from messnorm import Lage                                    # noqa: E402

HORIZONT = 5
AB = "2024-01-01"
STAERKEN = (0.02, 0.05, 0.10, 0.20, 0.40)


def _ab(je_tag: dict) -> dict:
    return {t: z for t, z in je_tag.items() if t >= AB}


def main() -> int:
    t0 = time.time()
    rng = np.random.default_rng(N.SAAT)
    L = Lage("spot", "einstieg")

    print("Lade Reihen ...", flush=True)
    reihen = B.lade()
    print("  %d Kryptoreihen" % len(reihen), flush=True)
    print("  lade funding ...", flush=True)
    fu = F.lade_funding()
    print("  lade turnover ...", flush=True)
    tu = MB.reihe("data/onchain_historie.db", "splycur")
    print("  lade terminmarkt ...", flush=True)
    try:
        tm = K.lade_terminmarkt()
    except Exception:                                        # noqa: BLE001
        tm = {}

    arten = [("schnitt50", None), ("vola", None), ("amihud", None),
             ("funding", fu), ("turnover", tu)]
    if "oi_aenderung" in tm:
        arten.append(("oi_aenderung", tm["oi_aenderung"]))

    print()
    print("=" * 104)
    print("SCHRITT 3 - TRENNSCHAERFE JE MASSSTAB   (Horizont %d · Block %d · "
          "ab %s · Menge frei)" % (HORIZONT, N._block(HORIZONT), AB[:4]))
    print("=" * 104)
    print("  %-14s %6s %5s  %-13s %-13s %-13s"
          % ("Kandidat", "Tage", "Blk", "Mittel", "Rand > +2 R", "Rand > +3 R"))

    zeilen = []
    for art, quelle in arten:
        gebaut = _ab(K.baue(reihen, art, quelle, horizont=HORIZONT))
        if len(gebaut) < 100:
            print("  %-14s   zu wenige Tage (%d)" % (art, len(gebaut)))
            continue
        ergebnis, tage, blk = {}, 0, 0
        for lab, fn in (
                ("mittel", lambda: N.pruefe(
                    art, gebaut, lage=L, frageart="markt", zielgroesse="bewegung_r",
                    menge="frei", rng=rng, horizont=HORIZONT,
                    staerken=STAERKEN)),
                ("rand2", lambda: R.pruefe_rand(
                    art, gebaut, lage=L, frageart="markt", menge="frei", rng=rng, marke=2.0,
                    horizont=HORIZONT, staerken=STAERKEN)),
                ("rand3", lambda: R.pruefe_rand(
                    art, gebaut, lage=L, frageart="markt", menge="frei", rng=rng, marke=3.0,
                    horizont=HORIZONT, staerken=STAERKEN))):
            try:
                f = fn()
            except Exception as e:                           # noqa: BLE001
                ergebnis[lab] = None
                print("     %s/%s: %s" % (art, lab, e))
                continue
            ergebnis[lab] = f
            tage, blk = f.n_tage, f.n_bloecke
        zeilen.append((art, tage, blk, ergebnis))
        print("  %-14s %6d %5d  %-13s %-13s %-13s"
              % (art, tage, blk,
                 *[(("%.2f R" % e.trennschaerfe_in_r)
                    if e is not None and e.trennschaerfe_in_r is not None
                    else "KEINE")
                   for e in (ergebnis.get("mittel"), ergebnis.get("rand2"),
                             ergebnis.get("rand3"))]), flush=True)

    print()
    print("=" * 104)
    print("DAS URTEIL JE KANDIDAT UND MASSSTAB")
    print("=" * 104)
    for art, _t, _b, e in zeilen:
        print("  %s" % art)
        for lab, name in (("mittel", "Mittel     "),
                          ("rand2", "Rand > +2 R"), ("rand3", "Rand > +3 R")):
            f = e.get(lab)
            if f is None:
                print("    %s  -" % name); continue
            print("    %s  %+9.5f  [%+.5f .. %+.5f] · Null %+.5f · %s"
                  % (name, f.wirkung, f.unten, f.oben, f.nullpunkt,
                     f.urteil))
            print("                 Treffer je Pflanzung: %s"
                  % f.protokoll.positiv_treffer)

    print()
    print("=" * 104)
    print("DIE ENTSCHEIDUNG")
    print("=" * 104)
    gut = {"mittel": 0, "rand2": 0, "rand3": 0}
    for _a, _t, _b, e in zeilen:
        for lab in gut:
            f = e.get(lab)
            if f is not None and f.trennschaerfe_in_r is not None:
                gut[lab] += 1
    n = len(zeilen)
    for lab, name in (("mittel", "Mittel     "), ("rand2", "Rand > +2 R"),
                      ("rand3", "Rand > +3 R")):
        print("  %s  findet eine Pflanzung bei %d von %d Kandidaten"
              % (name, gut[lab], n))
    print()
    print("  ⚠️ Ein Massstab OHNE Trennschaerfe kann kein 'traegt nicht'")
    print("     aussprechen - er liefert nur 'KEIN BEFUND'. Erst die")
    print("     Trennschaerfe macht die Aussage zu einer ueber die WELT.")
    print()
    print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
