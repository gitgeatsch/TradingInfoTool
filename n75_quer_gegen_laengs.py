# -*- coding: utf-8 -*-
"""N-75 — QUERSCHNITT gegen ZEITREIHE: misst die Kette die falsche Frage? (07.09.)

## Der Verdacht, und woher er kommt

`messe_h_als_filter.py` zitiert im eigenen Kopf die Lehrmeinung:

> *"You should not ask a CS signal to forecast absolute direction, and
> should not ask a TS signal to explain cross-sectional premia."*

⚠️ **Die gesamte Beitragsmaschinerie rangt INNERHALB DES TAGES.**
`messe_regel_wirksamkeit.rang` bildet den Rang ueber die Symbole eines
Kalendertages - sie ist rein querschnittlich (CS). Jeder Kandidat, der je
durch `messe_kandidaten_als_regel.baue` + `pruefe_auswahl` gelaufen ist,
wurde als CS-Signal gemessen.

**Mehrere gefallene Kandidaten sind ihrer Natur nach ZEITREIHEN-Signale:**

    H        "Weg frei UND Stop gedeckt" - absolut je Asset, kein Vergleich
    rsi      ueberkauft/ueberverkauft - klassisch je Reihe, nicht quer
    schnitt  "bin ich unter MEINEM Schnitt" - der Bezug ist die eigene
             Geschichte, nicht der Nachbar

> **Wenn das stimmt, sagt ihre Ablehnung nichts ueber sie aus - nur
> darueber, dass sie mit dem falschen Instrument gemessen wurden.**

## ⚠️ Und ein Hinweis, dass es stimmt, liegt schon vor

Das Akkumulationsmass (`messe_akkumulationsmass.py`) rangt **innerhalb
der eigenen Reihe** - es ist das einzige TS-Werkzeug im Bestand. Und dort
TRAEGT dieselbe Groesse: `UNTER_SMA` +0,0292 (p 0,000), im flachsten
Tiefen-Fuenftel sogar +0,0481.

**Dieselbe Achse, zwei Instrumente, zwei Ergebnisse.** Bisher standen die
beiden Befunde unverbunden nebeneinander (2.157).

## Was hier gemessen wird — beides auf DEMSELBEN Erfolgsmass

Der einzige Unterschied ist die Achse, auf der der Rang gebildet wird:

    QUER (CS)    Rang ueber die Symbole DESSELBEN TAGES
    LAENGS (TS)  Rang ueber die eigene Geschichte des Symbols
                 - nur Vergangenheit, kein Blick nach vorn

    Regel        oberstes Fuenftel sperren (wie bisher)
    Zielgroesse  bewegung_r, H20 - dieselbe wie ueberall
    Statistik    median(frei) - median(alle) JE KALENDERTAG, entzerrt

⚠️ **Das LAENGS-Mass darf NUR Vergangenheit sehen.** Ein Perzentilrang
ueber die ganze Reihe waere Lookahead: er wuesste 2019 schon, wie hoch
der Kurs 2025 steht. Deshalb nachlaufend ueber ein Fenster.

## Die Kontrollen

    zufall   auf BEIDEN Achsen - er darf nirgends tragen
    funding  auf beiden - er ist ein CS-Signal (Rang gegen andere Assets)
             und sollte QUER besser abschneiden als LAENGS. Tut er das
             nicht, misst die Laengs-Achse etwas anderes als gedacht.

    python n75_quer_gegen_laengs.py
"""
from __future__ import annotations

import sys
import time

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_bewertungskennzahl as MB                        # noqa: E402
import messe_eigenschaft_beitrag as B                        # noqa: E402
import messe_funding_niveau as F                             # noqa: E402
import messe_kandidaten_als_regel as K                       # noqa: E402
import messe_regel_wirksamkeit as RW                         # noqa: E402
from messe_beitrag_auf_auswahl import (_auswahl_maske,       # noqa: E402
                                       momentum250)
from messnorm import _block                                   # noqa: E402
from messnorm_auswahl import MENGEN                           # noqa: E402
from n64_schnitt_stufen import band                           # noqa: E402

HORIZONT = 20
FENSTER = 250            # nachlaufendes Fenster fuer den Laengs-Rang
ZIEH, SAAT = 20, 20260907
KANDIDATEN = ("schnitt", "rsi", "vola", "amihud", "funding", "zufall")


def laengs_rang(je_tag: dict) -> dict:
    """Rang JE SYMBOL ueber die eigene Vergangenheit - nachlaufend.

    ⚠️ NUR VERGANGENHEIT. Ein Rang ueber die ganze Reihe waere Lookahead:
    er wuesste am ersten Tag schon, wie hoch die Werte am letzten stehen.
    Hier zaehlt je Tag, wieviele der letzten FENSTER eigenen Werte
    KLEINER waren - das ist am Tag selbst berechenbar.
    """
    # nach Symbol umsortieren, Zeit aufsteigend
    je_sym: dict = {}
    for tag, z in je_tag.items():
        for x in z:
            je_sym.setdefault(x["sym"], []).append((tag, x["kennzahl"]))
    rang: dict = {}
    for sym, folge in je_sym.items():
        folge.sort()
        v = np.array([w for _t, w in folge], float)
        for i in range(len(v)):
            a = max(0, i - FENSTER)
            fenster = v[a:i]                    # ⚠️ OHNE den heutigen Wert
            if len(fenster) < 60:
                continue
            rang.setdefault(folge[i][0], {})[sym] = \
                float((fenster < v[i]).mean())
    return rang


def wirkung(je_tag, mom, anteil, achse, lr=None, mische=None):
    """median(frei) - median(alle) je Kalendertag - auf QUER oder LAENGS."""
    aus, besetzt = {}, []
    for tag, z in je_tag.items():
        if len(z) < 12:
            continue
        y = np.array([x["in_r"] for x in z], float)
        if achse == "quer":
            r = RW.rang(np.array([x["kennzahl"] for x in z], float))
            gut = np.ones(len(z), bool)
        else:
            lt = (lr or {}).get(tag) or {}
            r = np.array([lt.get(x["sym"], np.nan) for x in z], float)
            gut = np.isfinite(r)
            if gut.sum() < 12:
                continue
            r = np.where(gut, r, 0.0)
        if mische is not None:
            r = mische.permutation(r)
        m = _auswahl_maske(z, mom.get(tag) or {}, anteil, None)
        if m is None:
            continue
        m = m & gut
        if m.sum() < 6:
            continue
        oben = r >= RW.GRENZE
        if (oben & m).sum() < 1 or ((~oben) & m).sum() < 3:
            continue
        besetzt.append(int(m.sum()))
        aus[tag] = float(np.median(y[m & ~oben])) - float(np.median(y[m]))
    return aus, besetzt


def entzerrt(je_tag, mom, anteil, achse, lr, block):
    echt, besetzt = wirkung(je_tag, mom, anteil, achse, lr)
    e = band(echt, block)
    if e is None:
        return None
    null = []
    for z in range(ZIEH):
        n, _ = wirkung(je_tag, mom, anteil, achse, lr,
                       mische=np.random.default_rng(SAAT + z))
        nb = band(n, block, zieh=300, saat=SAAT + z)
        if nb:
            null.append(nb[0])
    nw = float(np.mean(null)) if null else 0.0
    return {"roh": e[0], "unten": e[1], "oben": e[2], "tage": e[3],
            "null": nw, "wirkung": e[0] - nw,
            "anker": float(np.mean(besetzt)) if besetzt else 0.0}


def main() -> int:
    t0 = time.time()
    print("=" * 100)
    print("N-75 — QUERSCHNITT gegen ZEITREIHE: dieselbe Groesse, zwei Achsen")
    print("=" * 100)
    reihen = B.lade()
    mom = momentum250(reihen)
    block = _block(HORIZONT)
    anteil = MENGEN["20%"]
    zus = {"funding": F.lade_funding(),
           "turnover": MB.reihe("data/onchain_historie.db", "splycur")}
    print("  %d Reihen . H%d . Menge 20%% . Laengs-Fenster %d Tage"
          % (len(reihen), HORIZONT, FENSTER))
    print()
    print("  %-9s %-7s %9s %22s %9s %8s   %s"
          % ("Kandidat", "Achse", "Wirkung", "Band", "entzerrt", "Anker",
             "Urteil"))
    erg = {}
    for a in KANDIDATEN:
        try:
            je = K.baue(reihen, a, zus.get(a), horizont=HORIZONT)
        except Exception as exc:                             # noqa: BLE001
            print("     %-9s -> %s" % (a, str(exc)[:60]))
            continue
        if not je:
            continue
        lr = laengs_rang(je)
        for achse in ("quer", "laengs"):
            r = entzerrt(je, mom, anteil, achse, lr, block)
            if r is None:
                print("     %-9s %-7s  zu wenige Tage" % (a, achse))
                continue
            erg[(a, achse)] = r
            # ⚠️ Das Band ROH gegen den Nullwert - so wie in N-67.
            traegt = r["unten"] > r["null"]
            print("     %-9s %-7s %+9.4f [%+.4f .. %+.4f] %+9.4f %8.1f   %s"
                  % (a, achse, r["roh"], r["unten"], r["oben"],
                     r["wirkung"], r["anker"],
                     "TRAEGT" if traegt else "traegt nicht"), flush=True)
        print()

    # ---- Urteil ---------------------------------------------------------
    print("=" * 100)
    print("WAS DAS HEISST")
    print("=" * 100)
    zq, zl = erg.get(("zufall", "quer")), erg.get(("zufall", "laengs"))
    for lab, z in (("quer", zq), ("laengs", zl)):
        if z and z["unten"] > z["null"]:
            print("  ⚠️⚠️ `zufall` traegt auf der %s-Achse - der Aufbau ist"
                  % lab)
            print("     kaputt, alles Weitere wertlos.")
            return 1
    print("  ✔ `zufall` traegt auf keiner Achse.")
    fq, fl = erg.get(("funding", "quer")), erg.get(("funding", "laengs"))
    if fq and fl:
        print("  Kontrolle `funding` (ein CS-Signal): quer %+.4f · laengs %+.4f"
              % (fq["wirkung"], fl["wirkung"]))
        print("     %s"
              % ("✔ quer staerker, wie erwartet"
                 if fq["wirkung"] > fl["wirkung"] else
                 "⚠️ laengs staerker - dann misst die Laengs-Achse etwas "
                 "anderes als gedacht"))
    print()
    for a in ("schnitt", "rsi", "vola", "amihud"):
        q, l = erg.get((a, "quer")), erg.get((a, "laengs"))
        if not (q and l):
            continue
        tq = q["unten"] > q["null"]
        tl = l["unten"] > l["null"]
        print("  %-9s quer %+.4f %-12s laengs %+.4f %-12s   %s"
              % (a, q["wirkung"], "(traegt)" if tq else "(traegt nicht)",
                 l["wirkung"], "(traegt)" if tl else "(traegt nicht)",
                 "⚠️⚠️ NUR LAENGS - mit dem falschen Instrument gemessen"
                 if tl and not tq else
                 "nur quer" if tq and not tl else
                 "beide" if tq and tl else "keine Achse"))
    print()
    print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
