# -*- coding: utf-8 -*-
"""N-95 — Ist der KNICK stabil? (B10 und B11 in einem Zug)

## Die Frage

Auf `frei` zeigen ZWEI unabhaengige Beitraege denselben Knick an
derselben Stelle:

    schnitt   +1,28   +1,59   +0,28   -1,19   -1,96
    funding   +0,77   +1,40   +0,22   -0,64   -1,75
                       ^^^^^ Fuenftel 1 ueber Fuenftel 0

Zwei Kriterien fuer die FORM sind gescheitert: die Monotonie (sechs von
acht Kandidaten brechen sie, darunter zwei LIVE laufende) und die
Stufenspanne (sie laesst alle acht durch, auch die Nichttraeger).

> **Die richtige Frage ist nicht 'welches Kriterium', sondern: ist der
> Knick STABIL?**

    reproduziert er   -> ein MARKTEFFEKT. Die Stufentabelle ist richtig,
                         und die Monotonie-Vorgabe war schlicht falsch
    kippt er          -> Rauschen. Die Vorgabe hat ihren Sinn, und
                         `schnitt` UND `funding` muessten neu bewertet
                         werden

## Die Messgroesse

    d01 = Stufe 1 - Stufe 0      je Kalendertag, also
        = median(y[Fuenftel 1]) - median(y[Fuenftel 0])

Positiv heisst: **das Extrem ist nicht der beste Fall.**

⚠️ Gemessen wird die Tagesreihe von `d01`, mit Blockbootstrap - dieselbe
Maschinerie wie ueberall. Der Nullpunkt kommt aus gemischten Raengen; er
muss bei null liegen, weil unter gemischten Raengen kein Fuenftel besser
ist als ein anderes.

## Der Aufbau

    1  d01 auf der ganzen Reihe, mit Band, gegen den Nullpunkt
    2  d01 je HAELFTE - zeigt beide dasselbe Vorzeichen?
    3  Die Kontrolle `zufall` - bei ihr muss d01 null sein

⚠️ Und zur Einordnung laeuft `d34 = Stufe 3 - Stufe 4` mit: dort ist die
Ordnung unstrittig (beide Beitraege fallen dort sauber). Wenn d34 klar
positiv und trennbar ist, arbeitet die Maschinerie - und ein Nullbefund
bei d01 ist dann eine Aussage, keine Untermacht.

## Die Vorhersage, VOR dem Lauf (Methodik 2.80)

    Erwartung   d01 ist bei beiden POSITIV und trennbar, und in beiden
                Haelften gleichsinnig - der Knick ist real
    Gegenthese  das Band schliesst die Null ein oder die Haelften
                kippen - dann ist es Rauschen

⚠️ Faellt es auf Rauschen hinaus, ist das KEIN Argument gegen `funding`
oder `schnitt` als Beitraege - nur gegen die Stufe 0 und 1 als getrennte
Stufen. Man koennte sie dann zusammenlegen.

    python n95_ist_der_knick_stabil.py
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
from messnorm import _block                                   # noqa: E402
from n91_rangkorrelation_form import band                     # noqa: E402

NULL_ZIEH = 40
SAAT = 20260909
KANDIDATEN = ("schnitt", "funding", "turnover", "oi_aenderung", "zufall")


def paar_je_tag(je_tag, a, b, mische=None):
    """Tagesreihe von median(Fuenftel a) - median(Fuenftel b)."""
    aus = {}
    for tag, zeilen in je_tag.items():
        if len(zeilen) < 15:
            continue
        w = np.array([x["kennzahl"] for x in zeilen], float)
        y = np.array([x["in_r"] for x in zeilen], float)
        r = np.argsort(np.argsort(w)) / max(len(w) - 1, 1)
        if mische is not None:
            r = mische.permutation(r)
        def f(k):
            m = (r >= k / 5) & ((r < (k + 1) / 5) if k < 4 else (r <= 1.0))
            return float(np.median(y[m])) if m.sum() >= 2 else None
        va, vb = f(a), f(b)
        if va is not None and vb is not None:
            aus[tag] = va - vb
    return aus


def nullpunkt(je_tag, a, b, block):
    """Der Nullpunkt: Mittel ueber Ziehungen mit gemischten Raengen."""
    w = []
    for z in range(NULL_ZIEH):
        r = paar_je_tag(je_tag, a, b, np.random.default_rng(SAAT + z))
        bb = band(r, block, zieh=300, saat=SAAT + z)
        if bb:
            w.append(bb[0])
    return float(np.mean(w)) if w else float("nan")


def main() -> int:
    t0 = time.time()
    reihen = B.lade()
    zus = zusatzquellen()
    block = _block(HORIZONT)

    print("=" * 104)
    print("N-95 — ist der KNICK stabil? d01 = Stufe 1 minus Stufe 0")
    print("=" * 104)
    print("  %s" % messmenge.zeile())
    print("  Menge `frei` · Block %d · %d Nullziehungen · in R, nicht in "
          "Punkten" % (block, NULL_ZIEH))
    print("  ⚠️ POSITIV heisst: das Extrem ist NICHT der beste Fall.")
    print("  ⚠️ `d34` laeuft zur Einordnung mit - dort ist die Ordnung "
          "unstrittig.")

    for kand in KANDIDATEN:
        je = K.baue(reihen, kand, zus.get(kand), horizont=HORIZONT)
        print()
        print("  %s" % kand.upper())
        print("     %-6s %-10s %10s %22s %10s  %s"
              % ("Paar", "Bereich", "Wert", "Band", "Nullpunkt", "Urteil"))
        for name, (a, b) in (("d01", (1, 0)), ("d34", (3, 4))):
            reihe = paar_je_tag(je, a, b)
            if not reihe:
                print("     %-6s nicht messbar" % name)
                continue
            n0 = nullpunkt(je, a, b, block)
            tage = sorted(reihe)
            mitte = tage[len(tage) // 2]
            for bereich, teil in (
                    ("ganz", reihe),
                    ("1. Haelfte", {t: v for t, v in reihe.items()
                                    if t < mitte}),
                    ("2. Haelfte", {t: v for t, v in reihe.items()
                                    if t >= mitte})):
                bb = band(teil, block)
                if bb is None:
                    print("     %-6s %-10s zu wenige Bloecke"
                          % (name, bereich))
                    continue
                # ⚠️ Gegen den NULLPUNKT, wie der Messstandard es verlangt.
                traegt = bb[1] > max(0.0, n0) or bb[2] < min(0.0, n0)
                print("     %-6s %-10s %+10.4f [%+.4f .. %+.4f] %+10.4f  %s"
                      % (name, bereich, bb[0], bb[1], bb[2], n0,
                         "⚠️ TRENNBAR" if traegt else "nicht trennbar"),
                      flush=True)
        print()

    print("=" * 104)
    print("WAS DAS HEISST")
    print("=" * 104)
    print("  ⚠️ Entscheidend ist `d01` bei `schnitt` UND `funding`:")
    print("     trennbar UND in beiden Haelften gleichsinnig -> der Knick "
          "ist ein MARKTEFFEKT,")
    print("     die Stufentabelle ist richtig und die Monotonie-Vorgabe "
          "war falsch.")
    print("  ⚠️ Kippt eine Haelfte oder schliesst das Band den Nullpunkt "
          "ein -> Rauschen.")
    print("     Dann waeren Stufe 0 und 1 ZUSAMMENZULEGEN, nicht die "
          "Beitraege zu verwerfen.")
    print("  ⚠️⚠️ Und `d34` zeigt, ob die Maschinerie ueberhaupt "
          "arbeitet - ist auch d34")
    print("     nicht trennbar, ist der Aufbau untermaechtig und d01 "
          "sagt nichts.")
    print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
