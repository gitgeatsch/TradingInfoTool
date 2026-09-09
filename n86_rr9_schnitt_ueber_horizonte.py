# -*- coding: utf-8 -*-
"""N-86 — R-R11 fuer `schnitt`: die Ruecknahme vom 31.08. nachmessen

## Warum

R-R9 verlangt eine Neukalibrierung, sobald sich die Beitragslage aendert.
Beim Nachsehen, WAS eigentlich registriert ist, kam heraus:

    KALIBRIERT_FUER = "funding_fuenftel:... turnover_fuenftel:..."

`schnitt` steht im Register, aber mit `zustand="null", stufen=None` -
**am 31.08.2026 zurueckgenommen, noch am Tag der Registrierung**:

    H 1  +0,0000   H 2  +0,0000   H 3  -0,0005
    H 5  -0,0069   H10  -0,0118   H20  -0,0221
    "bei keinem Horizont trennbar"

⚠️⚠️ Diese Messung lief auf der **freien** Menge. Heute traegt `schnitt`
auf der **selektierten** mit +0,1858 R - dem 6,3-fachen der am 08.09.
gemessenen Aufloesung. **Diese Frage wurde am 31.08. nie gestellt**; die
Mengen-Systematik gab es noch nicht.

## ⚠️ R-R11 — die Reproduktionspflicht

> Ein registrierter Befund darf nur von einer Messung umgestossen werden,
> die ihn ZUERST reproduziert. Wer die Basis aendert und ein anderes
> Ergebnis bekommt, hat nichts widerlegt - er hat etwas anderes gemessen.

Deshalb laeuft hier BEIDES: die alte Basis (`frei`, alle sechs Horizonte)
und die neue (selektierte Mengen, dieselben Horizonte).

## Die Vorhersage, VOR dem Lauf (Methodik 2.80)

    auf `frei`          traegt nicht, auf KEINEM Horizont
                        -> die Ruecknahme vom 31.08. ist reproduziert
    auf 10 % / 20 %     traegt, und zwar nicht nur bei H20
                        -> es ist eine andere Frage, keine Widerlegung

⚠️ Traegt er auf `frei` bei irgendeinem Horizont, ist die Ruecknahme
NICHT reproduziert - dann ist die alte Zahl fraglich und nicht die neue.
⚠️ Traegt er auf den selektierten Mengen NUR bei H20, ist es ein
Horizont-Einzelfall und kein Beitrag.

## Warum die Horizonte mitmuessen

Die Ruecknahme stuetzte sich ausdruecklich auf "bei KEINEM Horizont".
Eine Gegenmessung nur bei H20 waere die schwaechere Aussage - und
angreifbar mit demselben Argument.

    python n86_rr9_schnitt_ueber_horizonte.py
"""
from __future__ import annotations

import sys
import time

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_eigenschaft_beitrag as B                        # noqa: E402
import messe_kandidaten_als_regel as K                       # noqa: E402
import messnorm as N                                          # noqa: E402
import messnorm_auswahl as MA                                # noqa: E402
from messe_alle_kandidaten import SELEKTIERT, zusatzquellen  # noqa: E402
from messe_beitrag_auf_auswahl import momentum250            # noqa: E402

HORIZONTE = (1, 2, 3, 5, 10, 20)
# Die Zahlen vom 31.08., gegen die reproduziert wird.
ALT = {1: 0.0000, 2: 0.0000, 3: -0.0005, 5: -0.0069, 10: -0.0118,
       20: -0.0221}
KANDIDATEN = ("schnitt", "zufall")


def kurz(u: str) -> str:
    return u.split(" (")[0].split(" - ")[0][:22]


def main() -> int:
    t0 = time.time()
    reihen = B.lade()
    mom = momentum250(reihen)
    lage = N.Lage(instrument="spot", strategie="einstieg")
    zus = zusatzquellen()
    print("=" * 104)
    print("N-86 — R-R11 fuer `schnitt`: alte Basis (frei) UND neue "
          "(selektiert), sechs Horizonte")
    print("=" * 104)
    print("  %s" % N.standardzeile())
    print("  Vorhersage: auf `frei` traegt er auf KEINEM Horizont "
          "(= Reproduktion),")
    print("  auf den selektierten Mengen traegt er auf MEHREREN "
          "(= andere Frage).")

    erg = {}
    for kand in KANDIDATEN:
        print()
        print("  %s" % kand.upper())
        print("     %3s %-5s %9s %20s %9s  %-22s %s"
              % ("H", "Menge", "Wirkung", "Band", "Tsch.", "Urteil",
                 "31.08."))
        for h in HORIZONTE:
            try:
                je = K.baue(reihen, kand, zus.get(kand), horizont=h)
            except Exception as exc:                         # noqa: BLE001
                print("     %3d -> %s" % (h, str(exc)[:60]))
                continue
            mengen = ["frei"] + [m for m in
                                 MA.zulaessige_mengen(je, mom, horizont=h)
                                 if m in SELEKTIERT]
            for m in mengen:
                try:
                    b = MA.pruefe_auswahl(
                        kand, je, mom, lage=lage, menge=m,
                        rng=np.random.default_rng(20260908), horizont=h,
                        hypothese="N-86 R-R11 Reproduktion",
                        verwendung=("Markt" if m == "frei" else "Beitrag"))
                except Exception as exc:                     # noqa: BLE001
                    print("     %3d %-5s -> %s" % (h, m, str(exc)[:44]))
                    continue
                erg[(kand, h, m)] = b
                alt = ("%+.4f" % ALT[h]) if (kand == "schnitt"
                                             and m == "frei") else ""
                print("     %3d %-5s %+9.4f [%+.4f..%+.4f] %9s  %-22s %s"
                      % (h, m, b.wirkung, b.unten, b.oben,
                         ("%.4f" % b.trennschaerfe) if b.trennschaerfe
                         else "KEINE", kurz(b.urteil), alt), flush=True)

    # ---- Das Urteil ------------------------------------------------------
    print()
    print("=" * 104)
    print("R-R11 — IST DIE RUECKNAHME VOM 31.08. REPRODUZIERT?")
    print("=" * 104)
    frei = [(h, erg[("schnitt", h, "frei")])
            for h in HORIZONTE if ("schnitt", h, "frei") in erg]
    traegt_frei = [h for h, b in frei if b.traegt]
    if traegt_frei:
        print("  ⚠️⚠️ NEIN - `schnitt` traegt auf `frei` bei H%s."
              % ", H".join(str(h) for h in traegt_frei))
        print("     Damit ist die ALTE Zahl fraglich, nicht die neue -")
        print("     und nichts darf auf die neue gestuetzt werden, bevor")
        print("     dieser Widerspruch geklaert ist.")
    else:
        print("  ✔ JA - auf `frei` traegt er auf KEINEM der %d Horizonte."
              % len(frei))
        print("     Die Ruecknahme vom 31.08. ist reproduziert.")

    sel = [(h, m, b) for (k, h, m), b in erg.items()
           if k == "schnitt" and m != "frei"]
    tr = [(h, m) for h, m, b in sel if b.traegt]
    print()
    print("  Auf den SELEKTIERTEN Mengen traegt er in %d von %d Faellen"
          % (len(tr), len(sel)))
    if tr:
        hs = sorted({h for h, _m in tr})
        print("     Horizonte: %s" % ", ".join("H%d" % h for h in hs))
        if len(hs) == 1:
            print("     ⚠️ NUR EIN Horizont - das ist ein Einzelfall, kein")
            print("        Beitrag. Die Ruecknahme bleibt richtig.")
        else:
            print("     ✔ MEHRERE Horizonte - es ist eine andere FRAGE,")
            print("       keine Widerlegung der Ruecknahme.")

    zf = [b for (k, _h, _m), b in erg.items() if k == "zufall"]
    schlecht = [b for b in zf if b.traegt]
    print()
    if schlecht:
        print("  ⚠️⚠️ Kontrolle `zufall` traegt %d mal - der Lauf ist "
              "wertlos." % len(schlecht))
        return 1
    print("  ✔ Kontrolle `zufall`: traegt in keinem der %d Faelle." % len(zf))
    print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
