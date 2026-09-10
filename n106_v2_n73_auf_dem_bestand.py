# -*- coding: utf-8 -*-
"""V2 — N-73 AUF DEM BESTAND: halten `funding` und `turnover` die Huerde?

## Die Luecke, und warum sie geschlossen werden MUSS

Der Vierfachtest hat die Kandidaten ueber **alle zulaessigen Mengen**
gemessen (N-73). Ergebnis:

    schnitt      3 von 3   ✔ robust
    schnitt50    2 von 3
    vola         1 von 3   <- DAS Profil ist das Hin und Her
    amihud       0 von 3

⚠️⚠️ **Die registrierten Beitraege sind nie so gemessen worden.**
`funding` und `turnover` stehen auf `frei` - registriert, bevor es N-73
gab (2.294).

> Einen Kandidaten an einer Huerde scheitern zu lassen, die die
> laufenden Beitraege nie nehmen mussten, waere **zweierlei Mass** - und
> genau dieser Fehler ist am 07.09. schon einmal gefangen worden (N-2:
> *„einen Kandidaten an einer Huerde scheitern zu lassen, die die
> laufenden Beitraege nie nehmen mussten, waere zweierlei Mass gewesen"*).

## Was N-73 verlangt

> *„Die Zulaessigkeit sortiert aus, was zu duenn ist. Das URTEIL sollte
> ueber ALLE zulaessigen Mengen halten. Ein Kandidat, der nur auf einer
> von ihnen traegt, ist nicht robust - und das ist ein Befund ueber ihn,
> kein Grund, sich die passende Menge auszusuchen."*

⚠️ `frei` laeuft mit, zaehlt aber NICHT ins Urteil: sie beantwortet die
MARKT-Frage (P6), nicht die Beitragsfrage.

## ⚠️⚠️ Was dieser Lauf NICHT tut

Er stellt die Registrierung nicht in Frage und schaltet nichts ab. Er
beantwortet EINE Frage: **haetten `funding` und `turnover` die Huerde
genommen, an der die Kandidaten gemessen werden?**

Faellt einer durch, ist das ein Befund ueber den BESTAND - und die
Nutzervorgabe gilt auch dort: *„kein Beitrag faellt ohne Grund, und wenn
doch, muessen wir eine Loesung suchen"*.

## Die Vorhersage, VOR dem Lauf (Methodik 2.80)

    funding     offen. Er traegt auf `frei` (+0,0249) und laut 2.229 auf
                der Watchlist STAERKER (+0,0886) - aber ueber alle
                Mengen ist er nie geprueft worden
    turnover    offen. ⚠️ 2.161-rr11 haelt fest: auf der SELEKTIERTEN
                Menge liegt er bei +0,0865 [-0,0060 .. +0,1696] - das
                Band schliesst die Null ein. Das ist ein Warnzeichen
    oi_aenderung  laeuft als LIVE-Sperre mit
    zufall      darf nirgends tragen

⚠️ Bestehen die Bestandsbeitraege N-73 NICHT, waere `schnitt` mit 3 von 3
der einzige, der es tut - und die Huerde waere fuer den Bestand neu zu
begruenden, nicht fuer den Kandidaten zu senken.

    python n106_v2_n73_auf_dem_bestand.py
"""
from __future__ import annotations

import sys
import time

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import bestand as BE                                          # noqa: E402
import messe_eigenschaft_beitrag as B                         # noqa: E402
import messe_kandidaten_als_regel as K                        # noqa: E402
import messmenge                                              # noqa: E402
import messnorm as N                                          # noqa: E402
import messnorm_auswahl as MA                                 # noqa: E402
from messe_alle_kandidaten import HORIZONT, zusatzquellen     # noqa: E402
from messe_beitrag_auf_auswahl import momentum250             # noqa: E402

KANDIDATEN = ("funding", "turnover", "oi_aenderung", "zufall")
SAAT = 20260910


def traegt_wirklich(b) -> bool:
    """Das URTEIL lesen, nicht die Eigenschaft `traegt` (Fehler 4)."""
    return bool(b.traegt
                and not b.urteil.upper().startswith("KEIN BEFUND"))


def main() -> int:
    t0 = time.time()
    reihen = B.lade()
    mom = momentum250(reihen)
    zus = zusatzquellen()
    lage = N.Lage(instrument="spot", strategie="einstieg")

    print("=" * 112)
    print("V2 — N-73 AUF DEM BESTAND: halten `funding` und `turnover` "
          "die Huerde?")
    print("=" * 112)
    print("  %s" % messmenge.zeile())
    print("  %s" % N.standardzeile())
    print("  ⚠️ Das Urteil muss ueber ALLE zulaessigen Beitragsmengen "
          "halten (N-73).")
    print("  ⚠️ `frei` laeuft mit, zaehlt aber NICHT ins Urteil - sie ist "
          "die MARKT-Frage (P6).")
    print("  ⚠️⚠️ Dieser Lauf schaltet NICHTS ab. Er fragt nur, ob der "
          "Bestand die Huerde")
    print("     genommen haette, an der die Kandidaten gemessen werden.")

    erg = {}
    for kand in KANDIDATEN:
        try:
            je = K.baue(reihen, kand, zus.get(kand), horizont=HORIZONT)
        except Exception as exc:                              # noqa: BLE001
            print("\n  %-14s -> %s" % (kand, str(exc)[:60]))
            continue
        try:
            _m, fenster = BE.messbasis(kand)
        except KeyError:
            fenster = ""
        if fenster and fenster != "voll":
            je = {t: z for t, z in je.items() if str(t) >= fenster}
        try:
            zul = MA.zulaessige_mengen(je, mom, horizont=HORIZONT)
        except Exception as exc:                              # noqa: BLE001
            print("\n  %-14s -> Mengenwahl: %s" % (kand, str(exc)[:50]))
            continue

        print()
        print("  %s   (zulaessig: %s)" % (kand.upper(), ", ".join(zul)))
        traeger, geprueft = [], []
        for m in zul:
            try:
                b = MA.pruefe_auswahl(
                    kand, je, mom, lage=lage, menge=m,
                    rng=np.random.default_rng(SAAT), horizont=HORIZONT,
                    hypothese="V2 N-73 auf dem Bestand",
                    verwendung=("Markt" if m == "frei" else "Beitrag"))
            except Exception as exc:                          # noqa: BLE001
                print("     %-6s nicht messbar: %s" % (m, str(exc)[:48]))
                continue
            print("     %-6s %+9.4f [%+.4f .. %+.4f]  %s"
                  % (m, b.wirkung, b.unten, b.oben,
                     b.urteil.split(" (")[0][:44]), flush=True)
            if m == "frei":
                continue
            geprueft.append(m)
            if traegt_wirklich(b):
                traeger.append(m)
        if geprueft:
            erg[kand] = (len(traeger), len(geprueft), traeger)
            print("     -> traegt auf %d von %d Beitragsmengen%s"
                  % (len(traeger), len(geprueft),
                     "  ✔ ROBUST nach N-73" if len(traeger) == len(geprueft)
                     else "  ⚠️ NICHT robust"))
        else:
            print("     -> keine Beitragsmenge zulaessig - N-73 nicht "
                  "anwendbar")

    # ---- Die Abnahme -----------------------------------------------------
    print()
    print("=" * 112)
    print("DIE ABNAHME — zweierlei Mass oder nicht?")
    print("=" * 112)
    zf = erg.get("zufall")
    if zf and zf[0]:
        print("  ⚠️⚠️⚠️ `zufall` traegt auf %d von %d Mengen - der Lauf "
              "gilt NICHT." % (zf[0], zf[1]))
    elif zf:
        print("  ✔ `zufall` traegt auf keiner Beitragsmenge.")
    print()
    print("     %-14s %14s  %s" % ("Beitrag", "N-73", "Vergleich"))
    for kand in KANDIDATEN:
        v = erg.get(kand)
        if not v:
            continue
        print("     %-14s %6d von %-4d  %s"
              % (kand, v[0], v[1],
                 "✔ robust" if v[0] == v[1] else
                 "⚠️ traegt nur auf %s" % ", ".join(v[2] or ["keiner"])))
    print("     %-14s %6s        %s" % ("schnitt", "3 von 3",
                                        "✔ robust (Vierfachtest, 2.293)"))
    print()
    print("  ⚠️ Bestehen die Bestandsbeitraege N-73 NICHT, ist das ein "
          "Befund ueber den BESTAND -")
    print("     und die Huerde waere fuer ihn neu zu begruenden, nicht "
          "fuer die Kandidaten zu senken.")
    print("  ⚠️⚠️ Die Nutzervorgabe gilt auch hier: kein Beitrag faellt "
          "ohne Grund, und wenn doch,")
    print("     ist eine Loesung zu suchen. Dieser Lauf schaltet nichts "
          "ab.")
    print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
