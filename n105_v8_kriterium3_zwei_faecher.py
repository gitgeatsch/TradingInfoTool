# -*- coding: utf-8 -*-
"""V8 — KRITERIUM 3 mit ZWEI Faechern statt fuenf (10.09.2026)

## Warum dieser Lauf

V7 hat Kriterium 3 gemessen und **genau EIN gedecktes Urteil** geliefert:
`turnover` ist unabhaengig von `funding` (2 gegen 0 Faecher). Fuer die
KANDIDATEN war es nicht entscheidbar - aus drei Gruenden (2.303):

    vola                 0 von 5 Faechern, echt WIE gemischt
                         -> die SCHICHTUNG kostet die Macht
    schnitt, schnitt50   tragen auf `frei` ohnehin nicht
                         -> das ist die MARKT-Frage (P6), nicht ihre
                            Beitragsmenge
    oi_aenderung         2 gegen 3 Faecher -> Aufloesungsgrenze

⚠️ **Kein Konstruktionsfehler, ein Dimensionierungsproblem.** Bei
Kriterium 4 war das Werkzeug falsch (V1); hier ist es richtig, es fehlt
die MACHT.

## Was hier anders ist - beide Gruende zugleich

    ZWEI Faecher statt fuenf     5 -> 30 Symbole je Tag
                                 2 -> 75 Symbole je Tag
    auf der BEITRAGSmenge        statt auf `frei`
                                 20 % von 250 = 50, halbiert = 25 je Tag
                                 (Mindestquerschnitt ist 12)

## ⚠️⚠️ DIE MENGENWAHL STEHT VORAB FEST - sie haengt NICHT am Ergebnis

    registrierte Basis vorhanden   ->  diese  (turnover, oi_aenderung: frei)
    keine Basis                    ->  20 %

**Warum ausgerechnet 20 %:** F-212 und 2.262 halten fest, dass die
Live-Auswahl `auswahl.waehle` k=2 aus 43 nimmt - rund 4,7 %. Von den
verfuegbaren Mengen ist 20 % die schmalste, die nach der Halbierung noch
ueber dem Mindestquerschnitt liegt.

⚠️ **Was hier ausdruecklich NICHT passiert:** die Menge zu waehlen, auf
der ein Kandidat am besten dasteht. Das waere genau der Fehler, vor dem
N-73 warnt - *„kein Grund, sich die passende Menge auszusuchen"*.

## Die Gegenkontrolle bleibt der Kern

Dieselbe Schichtung mit **gemischtem** Funding: gleiche Fachgroesse,
keine Information.

    faellt ECHT, GEMISCHT nicht   ->  `funding` erklaert es
    fallen BEIDE gleich           ->  die Schichtung kostet

⚠️ Und die **Aufloesungsgrenze** gilt weiter, nur schaerfer: bei ZWEI
Faechern ist ein Fach die Haelfte. Ein Unterschied von einem Fach ist
damit NOCH weniger aussagekraeftig als bei fuenf - das Urteil braucht
**beide** Faecher auf der einen und **keinen** auf der anderen Seite.

## Die Vorhersage, VOR dem Lauf (Methodik 2.80)

    turnover     bestaetigt sich - er hatte schon bei fuenf Faechern
                 2 gegen 0
    schnitt      offen; auf 20 % traegt er (Vierfachtest +0,1858), also
                 hat die Vorfrage jetzt eine Chance
    vola         offen - bei fuenf Faechern verlor er alles
    zufall       traegt nirgends

⚠️ Bleibt es auch mit zwei Faechern unentscheidbar, ist Kriterium 3 mit
den vorhandenen Daten **nicht erfuellbar** - und das waere ein Befund
ueber die Datenlage, kein Urteil ueber die Kandidaten.

    python n105_v8_kriterium3_zwei_faecher.py
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
import messe_regel_wirksamkeit as W                           # noqa: E402
import messmenge                                              # noqa: E402
import messnorm as N                                          # noqa: E402
from messe_alle_kandidaten import HORIZONT, zusatzquellen     # noqa: E402
from messe_beitrag_auf_auswahl import momentum250             # noqa: E402
from n104_v7_kriterium3 import miss                           # noqa: E402

KANDIDATEN = ("schnitt", "schnitt50", "vola", "turnover",
              "oi_aenderung", "zufall")
FAECHER = 2
ERSATZMENGE = "20%"      # ⚠️ VORAB gesetzt, siehe Kopf
SAAT = 20260910


def traegt_wirklich(b) -> bool:
    """Das URTEIL lesen, nicht die Eigenschaft `traegt`.

    ## ⚠️⚠️ Fehler 4 vom 08.09.2026, hier beinahe wiederholt

    `Befund.traegt` prueft nur „Band ueber dem Bezugspunkt" - es weiss
    NICHTS von der Blockzahl. Bei zu wenigen Bloecken deckt das Band
    nicht, und `messnorm.urteil` sagt deshalb KEIN BEFUND, waehrend die
    Eigenschaft weiter `True` liefert.

    `k1c_lagen_eigene_zielgroesse` ist genau daran einmal gescheitert -
    es meldete drei Traeger, waehrend ALLE FUENF „KEIN BEFUND" lauteten.
    Bei zwei Faechern auf einer 20-%%-Menge ist die Blockzahl knapp,
    also ist der Fall hier realistisch und nicht theoretisch.
    """
    return bool(b.traegt
                and not b.urteil.upper().startswith("KEIN BEFUND"))


def funding_faecher(je_funding: dict, mische: bool = False,
                    saat: int = SAAT) -> list:
    """Je Fach eine Menge JE TAG - wie V7, aber mit `FAECHER` Faechern.

    ⚠️ Der Rang entsteht ueber den vollen Tagesquerschnitt, wie
    `marktrang` in der Produktion. `mische=True` vertauscht die
    Funding-Werte je Tag ueber die Symbole - gleiche Fachgroesse, keine
    Information.
    """
    rng = np.random.default_rng(saat)
    aus = [dict() for _ in range(FAECHER)]
    for tag, zeilen in je_funding.items():
        if len(zeilen) < FAECHER * 8:
            continue
        syms = [x["sym"] for x in zeilen]
        werte = np.array([x["kennzahl"] for x in zeilen], float)
        if mische:
            werte = rng.permutation(werte)
        r = W.rang(werte)
        for i, s in enumerate(syms):
            k = min(int(r[i] * FAECHER), FAECHER - 1)
            aus[k].setdefault(tag, set()).add(s)
    return aus


def main() -> int:
    t0 = time.time()
    reihen = B.lade()
    mom = momentum250(reihen)
    zus = zusatzquellen()
    lage = N.Lage(instrument="spot", strategie="einstieg")

    je_fu = K.baue(reihen, "funding", zus.get("funding"), horizont=HORIZONT)
    echt = funding_faecher(je_fu)
    gemischt = funding_faecher(je_fu, mische=True)

    print("=" * 112)
    print("V8 — KRITERIUM 3 mit ZWEI Faechern, auf der BEITRAGSmenge")
    print("=" * 112)
    print("  %s" % messmenge.zeile())
    print("  %s" % N.standardzeile())
    print("  ⚠️ Mengenwahl VORAB: registrierte Basis, sonst %s - NICHT "
          "die, auf der ein" % ERSATZMENGE)
    print("     Kandidat am besten dasteht (N-73).")
    print("  ⚠️⚠️ Bei ZWEI Faechern braucht das Urteil BEIDE auf der "
          "einen und KEINEN auf")
    print("     der anderen Seite - ein Fach Unterschied ist hier die "
          "Haelfte.")
    print("  Fachgroesse: %.1f Symbole je Tag"
          % (np.mean([len(v) for v in echt[0].values()]) if echt[0] else 0))

    erg = {}
    for kand in KANDIDATEN:
        try:
            je = K.baue(reihen, kand, zus.get(kand), horizont=HORIZONT)
        except Exception as exc:                              # noqa: BLE001
            print("\n  %-14s -> %s" % (kand, str(exc)[:60]))
            continue
        try:
            menge, fenster = BE.messbasis(kand)
        except KeyError:
            menge, fenster = "", ""
        registriert = bool(menge)
        menge = menge or ERSATZMENGE
        if fenster and fenster != "voll":
            je = {t: z for t, z in je.items() if str(t) >= fenster}

        print()
        print("  %s   (Menge %s%s)"
              % (kand.upper(), menge,
                 "" if registriert else " — vorab gesetzt, keine "
                                        "registrierte Basis"))
        b0 = miss(kand, je, mom, lage, menge)
        if isinstance(b0, str):
            print("     ohne Schichtung  -> %s" % b0)
            continue
        print("     %-18s %+9.4f [%+.4f .. %+.4f]  %s"
              % ("ohne Schichtung", b0.wirkung, b0.unten, b0.oben,
                 b0.urteil.split(" (")[0][:38]), flush=True)

        for wie, faecher in (("echt", echt), ("GEMISCHT", gemischt)):
            traeger, werte = 0, []
            for k in range(FAECHER):
                b = miss(kand, je, mom, lage, menge, nur=faecher[k])
                if isinstance(b, str):
                    continue
                werte.append(b.wirkung)
                if traegt_wirklich(b):
                    traeger += 1
            if not werte:
                print("     in funding %-8s nicht messbar" % wie)
                continue
            erg[(kand, wie)] = (float(np.mean(werte)), traeger, len(werte))
            print("     in funding %-7s %+9.4f (Mittel ueber %d Faecher)  "
                  "traegt in %d von %d"
                  % (wie, float(np.mean(werte)), len(werte), traeger,
                     len(werte)), flush=True)
        erg[(kand, "ohne")] = (b0.wirkung,
                               1 if traegt_wirklich(b0) else 0,
                               1)

    # ---- Die Abnahme -----------------------------------------------------
    print()
    print("=" * 112)
    print("DIE ABNAHME")
    print("=" * 112)
    zf = erg.get(("zufall", "echt"))
    if zf and zf[1]:
        print("  ⚠️⚠️⚠️ `zufall` traegt in %d von %d Faechern - der Lauf "
              "gilt NICHT." % (zf[1], zf[2]))
    elif zf:
        print("  ✔ `zufall` traegt in keinem Fach.")
    print()
    print("     %-14s %10s %10s %10s  %s"
          % ("Kandidat", "ohne", "echt", "GEMISCHT", "Urteil"))
    entscheidbar = 0
    for kand in KANDIDATEN:
        o, e, g = (erg.get((kand, x)) for x in ("ohne", "echt", "GEMISCHT"))
        if not (o and e and g):
            continue
        if not o[1]:
            urteil = "— traegt schon ohne Schichtung nicht, keine Aussage"
        elif e[1] == FAECHER and g[1] == 0:
            urteil = "✔ UNABHAENGIG von `funding` (%d gegen 0)" % e[1]
            entscheidbar += 1
        elif e[1] == 0 and g[1] == 0:
            urteil = ("⚠️ traegt in KEINEM Fach, auch nicht gemischt - "
                      "die SCHICHTUNG kostet")
        elif e[1] < g[1]:
            urteil = ("⚠️⚠️ `funding` erklaert einen Teil mit (%d gegen "
                      "%d)" % (e[1], g[1]))
            entscheidbar += 1
        else:
            urteil = ("— %d gegen %d Faecher: bei zwei Faechern ist das "
                      "kein Unterschied" % (e[1], g[1]))
        print("     %-14s %+10.4f %+10.4f %+10.4f  %s"
              % (kand, o[0], e[0], g[0], urteil))
    print()
    print("  ⚠️ Der Vergleich ist ECHT gegen GEMISCHT - nur so ist der "
          "Verlust herausgerechnet,")
    print("     den die kleineren Faecher ohnehin verursachen.")
    if entscheidbar <= 1:
        print("  ⚠️⚠️⚠️ HOECHSTENS EIN Urteil gedeckt - dann ist Kriterium "
              "3 mit den vorhandenen")
        print("     Daten NICHT erfuellbar. Das waere ein Befund ueber die "
              "DATENLAGE, kein Urteil")
        print("     ueber die Kandidaten - und die Vorgabe ,kein Beitrag "
              "faellt ohne Loesung' waere")
        print("     dann auf eine ANDERE Konstruktion zu richten, nicht "
              "auf mehr Faecher.")
    print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
