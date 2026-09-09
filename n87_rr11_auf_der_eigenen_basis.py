# -*- coding: utf-8 -*-
"""N-87 — R-R11: jeder Beitrag auf SEINER EIGENEN Basis (08.09.2026)

## ⚠️⚠️ Warum dieser Lauf noetig ist — eine eigene Korrektur

Heute wurden `funding`, `turnover` und `schnitt` unter dem neuen
Messstandard gemessen - alle auf denselben Mengen und ueber die VOLLE
Historie. Daraus wurde geschlossen, `turnover` sei "nicht trennbar".

**Das war ein R-R11-Verstoss.** Befund 2.162 haelt fest:

> DIE LOESUNG FUER `turnover`: DIE MENGE MUSS ZUR DATENLAGE PASSEN.
> Kriterium, vorab gesetzt und fuer ALLE Beitraege gleich: die SCHMALSTE
> Menge, die noch >= 12 Anker je Tag liefert. Ergebnis: turnover 50 %,
> funding 10 %, oi_aenderung 20 %, zufall 5 %. Dort traegt jeder der
> drei **ab 2022**.

    turnover        Menge 50 %,  Fenster ab 2022,  Anker +0,0598
    funding         Menge 10 %,  Fenster ab 2022,  Anker +0,0607
    oi_aenderung    Menge 20 %,  Fenster ab 2022,  Anker +0,0446
    zufall          Menge  5 %,  Fenster ab 2022,  Anker +0,0052 (Null im Band)

Wer die Basis wechselt und ein anderes Ergebnis bekommt, hat nichts
widerlegt - er hat etwas anderes gemessen. Genau das war passiert.

## Was hier gemessen wird

Jeder auf **seiner registrierten Basis**, unter dem Messstandard vom
08.09. Und zusaetzlich, zum Vergleich, dieselbe Groesse ueber die volle
Historie - damit sichtbar ist, ob der Unterschied vom FENSTER oder vom
Messstandard kommt.

## Die Vorhersage, VOR dem Lauf

    auf der eigenen Basis ab 2022   alle drei tragen weiter
                                    -> 2.162 ist reproduziert, und meine
                                       heutige Aussage zu `turnover` faellt
    auf der vollen Historie         turnover schwaecher
                                    -> der Unterschied ist das FENSTER

⚠️ Traegt `turnover` auch auf seiner eigenen Basis nicht mehr, ist 2.162
durch den neuen Messstandard ueberholt - DANN, und erst dann, ist die
Aussage "unentschieden" belegt.

    python n87_rr11_auf_der_eigenen_basis.py
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
from messe_alle_kandidaten import HORIZONT, zusatzquellen    # noqa: E402
from messe_beitrag_auf_auswahl import momentum250            # noqa: E402

AB = "2022-01-01"
# Basis, Anker aus 2.162 - genau so registriert.
BASIS = (("turnover", "50%", +0.0598),
         ("funding", "10%", +0.0607),
         ("oi_aenderung", "20%", +0.0446),
         ("zufall", "5%", +0.0052))


def kurz(u: str) -> str:
    return u.split(" (")[0].split(" - ")[0][:26]


def main() -> int:
    t0 = time.time()
    reihen = B.lade()
    mom = momentum250(reihen)
    lage = N.Lage(instrument="spot", strategie="einstieg")
    zus = zusatzquellen()
    print("=" * 108)
    print("N-87 — R-R11: jeder Beitrag auf SEINER EIGENEN Basis (2.162)")
    print("=" * 108)
    print("  %s" % N.standardzeile())
    print()
    print("  %-14s %-5s %-9s %9s %20s %9s  %-24s %s"
          % ("Kandidat", "Menge", "Fenster", "Wirkung", "Band", "Tsch.",
             "Urteil", "Anker 2.162"))
    erg = {}
    for kand, menge, anker in BASIS:
        try:
            je_voll = K.baue(reihen, kand, zus.get(kand), horizont=HORIZONT)
        except Exception as exc:                             # noqa: BLE001
            print("  %-14s -> %s" % (kand, str(exc)[:60]))
            continue
        for fenster, je in (("ab 2022",
                             {t: z for t, z in je_voll.items()
                              if str(t) >= AB}),
                            ("voll", je_voll)):
            if not je:
                continue
            try:
                b = MA.pruefe_auswahl(
                    kand, je, mom, lage=lage, menge=menge,
                    rng=np.random.default_rng(20260908), horizont=HORIZONT,
                    hypothese="N-87 R-R11 eigene Basis",
                    verwendung="Beitrag")
            except Exception as exc:                         # noqa: BLE001
                print("  %-14s %-5s %-9s -> %s"
                      % (kand, menge, fenster, str(exc)[:44]))
                continue
            erg[(kand, fenster)] = b
            print("  %-14s %-5s %-9s %+9.4f [%+.4f..%+.4f] %9s  %-24s %s"
                  % (kand, menge, fenster, b.wirkung, b.unten, b.oben,
                     ("%.4f" % b.trennschaerfe) if b.trennschaerfe
                     else "KEINE", kurz(b.urteil),
                     ("%+.4f" % anker) if fenster == "ab 2022" else ""),
                  flush=True)
        print()

    # ---- Urteil ---------------------------------------------------------
    print("=" * 108)
    print("IST 2.162 REPRODUZIERT?")
    print("=" * 108)
    zf = erg.get(("zufall", "ab 2022"))
    if zf is not None and zf.traegt:
        print("  ⚠️⚠️ Kontrolle `zufall` traegt auf ihrer eigenen Basis - "
              "der Lauf ist wertlos.")
        return 1
    print("  ✔ Kontrolle `zufall` auf 5 %% ab 2022: %s"
          % (kurz(zf.urteil) if zf is not None else "nicht messbar"))
    print()
    for kand, menge, anker in BASIS:
        if kand == "zufall":
            continue
        b = erg.get((kand, "ab 2022"))
        v = erg.get((kand, "voll"))
        if b is None:
            continue
        print("  %-14s eigene Basis (%s, ab 2022): %+.4f  %s"
              % (kand, menge, b.wirkung, "TRAEGT" if b.traegt
                 else "traegt NICHT"))
        if v is not None:
            print("  %-14s volle Historie:            %+.4f  %s"
                  % ("", v.wirkung, "TRAEGT" if v.traegt
                     else "traegt NICHT"))
        if b.traegt and (v is None or not v.traegt):
            print("                 -> der Unterschied ist das FENSTER, "
                  "nicht der Messstandard")
        elif not b.traegt:
            print("                 ⚠️ auch auf der EIGENEN Basis nicht - "
                  "2.162 ist ueberholt")
    print()
    print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
