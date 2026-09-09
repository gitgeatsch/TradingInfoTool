# -*- coding: utf-8 -*-
"""N-90 — Ist `schnitt`s BUCKEL dasselbe Artefakt? (09.09.2026)

## Die Frage

`schnitt` ist an zwei Huerden gescheitert:

    Zeitstabilitaet   ✔ GELOEST (N-89): es war Kollinearitaet mit der
                        Momentum-Auswahl. Auf Zufallsmengen verschwindet
                        sie (-0,431 -> -0,013 bei 5 %, 0 von 5 trennbar)
    FORM              ⚠️ der Buckel +4,07 / +5,55 / +9,49 / +1,71 / -4,65
                        mit Hochpunkt bei Fuenftel 2 statt bei 0

**Beide wurden auf der SELEKTIERTEN Menge gemessen.** Wenn die erste
Kollinearitaet war, liegt die Frage nahe, ob die zweite es auch ist.

## ⚠️ Ein Hinweis stand schon in N-64 und wurde nicht verfolgt

    Fuenftel 0 (tief unter dem Schnitt)    1,49 Anker/Tag
    Fuenftel 4 (ueber dem Schnitt)        29,35 Anker/Tag

**Zwanzigmal so viele.** Auf der Momentumspitze liegen fast alle Werte
ueber ihrem eigenen Schnitt - das unterste Fuenftel ist praktisch leer.
Eine Stufentabelle aus 1,49 Ankern je Tag ist kaum mehr als Rauschen, und
N-65 hat genau dafuer die Entzerrung gebaut.

> **Auf einer Zufallsmenge muessten die Fuenftel ausgeglichen sein.**

## Was gemessen wird

Dieselbe Stufenrechnung wie N-65 - entzerrt, mit denselben Funktionen -
einmal auf der Momentum-Auswahl und einmal auf **fuenf Zufallsauswahlen**
gleicher Groesse.

    Besetzung   wie viele Anker je Tag in jedem Fuenftel?
    Stufen      entzerrt, in Punkten
    Monotonie   die Vorabfestlegung verlangt sie fuer 'nutzbar'

⚠️ FUENF Ziehungen, nicht eine. Und die Kontrolle `zufall` laeuft mit:
bei ihr muessen die Stufen FLACH sein, egal auf welcher Menge.

## Die Vorhersage, VOR dem Lauf (Methodik 2.80)

    Erwartung   auf Zufallsmengen sind die Fuenftel ausgeglichen, und
                die Stufen werden MONOTON (oder zumindest ohne
                Hochpunkt in der Mitte)
    Gegenthese  der Buckel bleibt - dann ist er die Form der Sache, und
                `schnitt` ist als Regler endgueltig ungeeignet

⚠️ Bleibt der Buckel, ist das ein sauberer Nullbefund und `schnitt`
bleibt als Regler draussen - aber die Sperre (oberstes Fuenftel) waere
davon unberuehrt, denn sie braucht keine Monotonie.

    python n90_buckel_oder_artefakt.py
"""
from __future__ import annotations

import sys
import time

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_eigenschaft_beitrag as B                        # noqa: E402
import messe_kandidaten_als_regel as K                       # noqa: E402
import messmenge                                              # noqa: E402
from messe_alle_kandidaten import HORIZONT, zusatzquellen    # noqa: E402
from messe_beitrag_auf_auswahl import momentum250            # noqa: E402
from messnorm import _block                                   # noqa: E402
from messnorm_auswahl import MENGEN                           # noqa: E402
# ⚠️ DIE ECHTEN Funktionen aus N-64/N-65 - keine Kopie.
from n64_schnitt_stufen import band, je_fuenftel              # noqa: E402

MENGE = "20%"
ZIEH, SAAT = 20, 20260907
SAATEN = (90001, 90002, 90003, 90004, 90005)
PUNKT_JE_R = 100.0 / 3.0     # wie in N-65: d(quote) = d(Potential)/(1+CRV)


def stufen(je_tag, mom, anteil, block, auswahl_saat=None):
    """Entzerrte Stufen + Besetzung - genau wie N-65, nur mit Auswahl."""
    aus, besetzt, _g = je_fuenftel(je_tag, mom, anteil,
                                   auswahl_saat=auswahl_saat)
    echt = []
    for k in range(5):
        e = band(aus[k], block)
        echt.append(e[0] if e else None)
    null = {k: [] for k in range(5)}
    for z in range(ZIEH):
        a2, _b, _c = je_fuenftel(je_tag, mom, anteil,
                                 mische=np.random.default_rng(SAAT + z),
                                 auswahl_saat=auswahl_saat)
        for k in range(5):
            e = band(a2[k], block, zieh=300, saat=SAAT + z)
            if e:
                null[k].append(e[0])
    ent = []
    for k in range(5):
        if echt[k] is None or not null[k]:
            ent.append(None)
        else:
            ent.append(echt[k] - float(np.mean(null[k])))
    bes = [float(np.mean(besetzt[k])) if besetzt[k] else 0.0
           for k in range(5)]
    return ent, bes


def urteil_form(p):
    if any(x is None for x in p):
        return "nicht messbar"
    fallend = all(p[i] >= p[i + 1] - 1e-9 for i in range(4))
    steigend = all(p[i] <= p[i + 1] + 1e-9 for i in range(4))
    if fallend:
        return "✔ MONOTON FALLEND"
    if steigend:
        return "✔ MONOTON STEIGEND"
    hoch = int(np.argmax(p))
    return "⚠️ BUCKEL, Hochpunkt bei Fuenftel %d" % hoch


def main() -> int:
    t0 = time.time()
    reihen = B.lade()
    mom = momentum250(reihen)
    zus = zusatzquellen()
    block = _block(HORIZONT)
    anteil = MENGEN[MENGE]

    print("=" * 104)
    print("N-90 — ist `schnitt`s BUCKEL dasselbe Artefakt wie die "
          "Zeitinstabilitaet?")
    print("=" * 104)
    print("  %s" % messmenge.zeile())
    print("  Menge %s · Block %d · %d Nullziehungen · entzerrt"
          % (MENGE, block, ZIEH))
    print("  Bekannt (N-65, Momentum): +4,07 / +5,55 / +9,49 / +1,71 / "
          "-4,65 - Buckel bei 2")
    print("  ⚠️ Und die Besetzung dort: 1,49 gegen 29,35 Anker je Tag "
          "(Fuenftel 0 gegen 4)")

    for kand in ("schnitt", "zufall"):
        je = K.baue(reihen, kand, zus.get(kand), horizont=HORIZONT)
        print()
        print("  %s" % kand.upper())
        print("     %-10s %38s   %s"
              % ("Auswahl", "Stufen in Punkten (Fuenftel 0..4)", "Form"))
        for name, saat in [("Momentum", None)] + \
                          [("Zufall %d" % (i + 1), s)
                           for i, s in enumerate(SAATEN)]:
            ent, bes = stufen(je, mom, anteil, block, auswahl_saat=saat)
            p = [None if x is None else x * PUNKT_JE_R for x in ent]
            txt = " ".join("%+7.2f" % x if x is not None else "   n/a"
                           for x in p)
            print("     %-10s %38s   %s" % (name, txt, urteil_form(p)),
                  flush=True)
            print("     %-10s %38s   Besetzung: %s"
                  % ("", "",
                     " ".join("%.1f" % b for b in bes)))

    print()
    print("=" * 104)
    print("WAS DAS HEISST")
    print("=" * 104)
    print("  ⚠️ Entscheidend sind ZWEI Dinge nebeneinander:")
    print("     1. wird die BESETZUNG auf Zufallsmengen ausgeglichen?")
    print("     2. verschwindet der BUCKEL?")
    print("  Nur wenn beides zutrifft, war er ein Auswahl-Artefakt.")
    print("  ⚠️ Bleibt er, ist `schnitt` als REGLER endgueltig ungeeignet -")
    print("     die SPERRE (oberstes Fuenftel) braucht aber keine "
          "Monotonie.")
    print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
