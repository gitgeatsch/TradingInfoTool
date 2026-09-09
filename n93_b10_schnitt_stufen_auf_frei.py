# -*- coding: utf-8 -*-
"""N-93 (B10) — `schnitt`s Stufen auf DERSELBEN Basis wie `funding`

## Die Einsicht, die N-92 geliefert hat

    `funding`s Stufen  ->  Menge `frei`,  Fuenftel 30/29/30/29/30
    `schnitt`s Buckel  ->  Menge 20 %,    Fuenftel 1,5 / 2,2 / 3,7 / 8,5 / 29,7

> **Die beiden waren nie vergleichbar.** `schnitt` wurde an einer Huerde
> gemessen, die `funding` nie nehmen musste - auf einer Menge, auf der
> das unterste Fuenftel praktisch leer ist.

Und N-90 hat gezeigt, was das anrichtet: dort schlug die KONTROLLE mit
-33,89 bis +90,85 Punkten aus, waehrend die Beitragsskala bei +-5 liegt.

## Die Frage

**Wird `schnitt` auf `frei` monoton?** Bevor ein neues Verfahren gebaut
wird, gehoert die einfache Antwort geprueft: dieselbe Ableitung wie bei
`funding`, auf derselben Menge.

## Der Aufbau

    1  Die Stufen mit der LIVE-Ableitung (`rechne_funding_beitrag.py`:
       Fuenftel je Tag, Median je Fuenftel, Mittel ueber die Tage, minus
       dem Mittel der fuenf, mal 1/(1+CRV), halbiert) - auf `frei` UND
       auf 20 %, damit der Unterschied sichtbar wird
    2  Die BESETZUNG je Fuenftel - traegt die Statistik dort ueberhaupt?
    3  Die Monotonie
    4  ⚠️ Und eine ZWEITE Ableitung als Gegenprobe: dieselben Stufen aus
       dem MITTEL statt dem Median. Stimmen beide ueberein, haengt das
       Ergebnis nicht am Schaetzer

    Kontrolle   `zufall` an jeder Stelle - seine Stufen muessen FLACH
                sein, und in N-92 waren sie es auf `frei` (Spanne 0,28
                gegen `funding`s 3,15)

## Die Vorhersage, VOR dem Lauf (Methodik 2.80)

Die Rangkorrelation (N-91) hat gezeigt, dass `schnitt` MONOTON ist -
beide Haelften negativ, auf Momentum wie auf Zufall.

    Erwartung   auf `frei` sind die Fuenftel ausgeglichen und die Stufen
                monoton FALLEND: tief unter dem Schnitt ist am besten
    Gegenthese  der Buckel bleibt auch dort - dann liegt es nicht an der
                Besetzung, und `schnitt` braucht ein anderes Verfahren

⚠️ Wird er monoton, ist B10 geloest OHNE neues Verfahren - und die Kette
bekaeme einen dritten Beitrag mit 100 % Abdeckung. Dann greift R-R9.

    python n93_b10_schnitt_stufen_auf_frei.py
"""
from __future__ import annotations

import statistics as st
import sys
import time

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_beitrag_auf_auswahl as A                        # noqa: E402
import messe_eigenschaft_beitrag as B                        # noqa: E402
import messe_kandidaten_als_regel as K                       # noqa: E402
import messmenge                                              # noqa: E402
from messe_alle_kandidaten import HORIZONT, zusatzquellen    # noqa: E402
from messe_beitrag_auf_auswahl import momentum250            # noqa: E402
from messnorm_auswahl import MENGEN                           # noqa: E402
from n92_b9_funding_buckel_auf_frei import monoton            # noqa: E402

CRV = 2.0


def stufen(je_tag, mom, anteil, lage="median"):
    """Die LIVE-Ableitung, mit waehlbarem Lagemass.

    ⚠️ `lage="mittel"` ist die GEGENPROBE - nicht die Vorgabe. Stimmen
    Median und Mittel ueberein, haengt das Ergebnis nicht am Schaetzer.
    """
    f = np.median if lage == "median" else np.mean
    sammel = {k: [] for k in range(5)}
    besetzt = {k: [] for k in range(5)}
    for tag, zeilen in je_tag.items():
        if len(zeilen) < 15:
            continue
        w = np.array([x["kennzahl"] for x in zeilen], float)
        y = np.array([x["in_r"] for x in zeilen], float)
        m0 = A._auswahl_maske(zeilen, mom.get(tag) or {}, anteil, None)
        if m0 is None or m0.sum() < 15:
            continue
        w, y = w[m0], y[m0]
        r = np.argsort(np.argsort(w)) / max(len(w) - 1, 1)
        for k in range(5):
            m = (r >= k / 5) & ((r < (k + 1) / 5) if k < 4 else (r <= 1.0))
            besetzt[k].append(int(m.sum()))
            if m.sum() >= 2:
                sammel[k].append(float(f(y[m])))
    if any(not sammel[k] for k in range(5)):
        return None, None
    werte = [st.mean(sammel[k]) for k in range(5)]
    mittel = st.mean(werte)
    faktor = 1.0 / (1.0 + CRV)
    return ([100.0 * (werte[k] - mittel) * faktor / 2.0 for k in range(5)],
            [float(np.mean(besetzt[k])) for k in range(5)])


def main() -> int:
    t0 = time.time()
    reihen = B.lade()
    mom = momentum250(reihen)
    zus = zusatzquellen()

    print("=" * 108)
    print("N-93 (B10) — `schnitt`s Stufen auf DERSELBEN Basis wie `funding`")
    print("=" * 108)
    print("  %s" % messmenge.zeile())
    print("  Ableitung wie live (`rechne_funding_beitrag.py`), CRV %.1f, "
          "halbiert (in-sample)" % CRV)
    print("  ⚠️ Bekannt: `funding` auf `frei` hat 30/29/30/29/30 Anker je "
          "Fuenftel,")
    print("     `schnitt` auf 20 % hat 1,5 / 2,2 / 3,7 / 8,5 / 29,7 - das "
          "war die Ursache in N-90.")

    for kand in ("schnitt", "funding", "zufall"):
        je = K.baue(reihen, kand, zus.get(kand), horizont=HORIZONT)
        print()
        print("  %s" % kand.upper())
        print("     %-6s %-8s %42s  %s"
              % ("Menge", "Lagemass", "Punkte (Fuenftel 0..4)", "Form"))
        for menge in ("frei", "20%"):
            for lage in ("median", "mittel"):
                p, bes = stufen(je, mom, MENGEN[menge], lage)
                if p is None:
                    print("     %-6s %-8s nicht messbar" % (menge, lage))
                    continue
                print("     %-6s %-8s %42s  %s"
                      % (menge, lage, " ".join("%+7.2f" % x for x in p),
                         monoton(p)), flush=True)
                if lage == "median":
                    print("     %-6s %-8s %42s  Besetzung: %s · Spanne %.2f"
                          % ("", "", "",
                             " ".join("%.0f" % b for b in bes),
                             max(p) - min(p)))

    print()
    print("=" * 108)
    print("WAS DAS HEISST")
    print("=" * 108)
    print("  ⚠️ Entscheidend ist `schnitt` auf `frei`:")
    print("     ist die BESETZUNG ausgeglichen UND die Form monoton, ist "
          "B10 geloest -")
    print("     ohne neues Verfahren, auf derselben Basis wie `funding`.")
    print("  ⚠️ Und die GEGENPROBE: stimmen Median und Mittel ueberein, "
          "haengt es nicht am Schaetzer.")
    print("  ⚠️⚠️ Die Kontrolle `zufall` muss FLACH bleiben - in N-92 "
          "war ihre Spanne 0,28")
    print("     gegen `funding`s 3,15. Ist sie hier gross, gilt nichts "
          "davon.")
    print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
