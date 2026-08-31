# -*- coding: utf-8 -*-
"""Die ORIGINALMESSUNG von H, frisch gerechnet - und mit Klammer (31.08.2026)

## Warum diese Messung, und warum ohne Zwischenspeicher

Nutzerauftrag 31.08.: *"Rechne und recherchiere noch einmal, wie H entstanden
ist und vermessen wurde, und ob die aktuelle Erkenntnis final und richtig
ist."* Dazu der Einwand, dass ein Cachefehler sich in jeder Wiederholung
reproduziert.

⚠️ DIESER LAUF LIEST KEINEN ZWISCHENSPEICHER. Er rechnet die Anker neu.

## Wie H entstanden ist - aus der eigenen Historie

    20.08.  Kapitel 104   "die Struktur, vorab benannt" - traegt NICHT
                          (39 Reihen, Reifeschnitt eingefuehrt)
    21.08.  Kapitel 107   breite Basis: 347 statt 39 Reihen
    21.08.  Kapitel 108   "erster bestaetigter Befund" - H TRAEGT
    21.08.  Kapitel 111   "H ist mehr als Momentum"
    danach  119/121/S3/S4 der Wert wandert von +1,3 ueber +4,5 auf +3,78

**Das Mass war von Anfang an dasselbe:** `messe_marken.bewerte()` rechnet die
Quote "Ziel vor Stop" der H-Anker gegen die Quote ALLER Anker - GEPOOLT ueber
die gesamte Historie und alle Symbole. Eine Klammer gab es nie; die
Kontrolle war eine Blockpermutation der MARKEN, nicht ein Vergleich
innerhalb eines Zeitfensters.

## Die Frage

    Bleibt der Originalbefund bestehen, wenn man dieselben Anker mit
    derselben Quote rechnet, aber den KALENDERTAG festhaelt?

Drei Klammern, ein Merkmal, dasselbe Mass:

    GEPOOLT        wie im Original (Kapitel 104-121)
    JE ZEITBLOCK   120 Tage - die Klammer dieser Arbeit
    JE KALENDERTAG die schaerfste - und die, unter der Funding und
                   Turnover getragen haben

⚠️ WENN DER BEFUND UNTER DER TAGESKLAMMER VERSCHWINDET, ist das kein neuer
Befund gegen H, sondern die Erklaerung des alten: H beschreibt dann, an
welchen TAGEN es auftritt, nicht welche Anker besser sind.

⚠️ UND WENN ER BLEIBT, ist meine Schlussfolgerung der letzten drei Tage
falsch. Beides ist ein Ergebnis.

## Vorab festgelegt

  Befund bleibt      Tagesklammer positiv und von null trennbar
  Befund ist Lage    gepoolt positiv, je Tag nicht trennbar
  Befund ist falsch  je Tag negativ

    python pruefe_h_original_reproduziert.py
"""
import math
import statistics as st
import sys
import time

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, ".")

from messe_marken import (CRV, K, MAX_TAGE, MIN_BERUEHRUNGEN,     # noqa: E402
                          _niveaus_schnell, _SwingSpeicher)
from simuliere_bremse import _reihen_roh, klassen_aus_db          # noqa: E402

DB = "data/messdaten.db"
MINDESTALTER = 250        # Reifeschnitt aus Kapitel 104.3
ZIEHUNGEN = 20000


def laufe():
    """Die Originalgroessen: frei, gedeckt, Ausgang - nichts sonst."""
    roh = _reihen_roh(DB, "krypto", klassen_aus_db(DB))
    aus = []
    t0 = letzte = time.time()
    for nr, (sym, (c, h, l, v, a, off, d)) in enumerate(roh.items(), 1):
        del v
        sp = _SwingSpeicher(h, l)
        for i in range(off + 1 + MINDESTALTER, len(c) - 1):
            atr, kurs = float(a[i - off]), float(c[i])
            if not (atr > 0 and kurs > 0):
                continue
            stop = kurs - K * atr
            if stop <= 0:
                continue
            ziel = kurs + CRV * (kurs - stop)
            n = _niveaus_schnell(sp, c, h, l, i, atr)
            frei = not any(m["beruehrungen"] >= MIN_BERUEHRUNGEN
                           and m["preis"] < ziel for m in n["oben"])
            gedeckt = any(m["beruehrungen"] >= MIN_BERUEHRUNGEN
                          and m["preis"] > stop for m in n["unten"])
            ausgang = "abgelaufen"
            for j in range(i + 1, min(i + 1 + MAX_TAGE, len(c))):
                if l[j] <= stop:
                    ausgang = "stop"
                    break
                if h[j] >= ziel:
                    ausgang = "ziel"
                    break
            aus.append({"sym": sym, "datum": d[i], "frei": frei,
                        "gedeckt": gedeckt, "h": bool(frei and gedeckt),
                        "ausgang": ausgang})
        if time.time() - letzte >= 60:
            letzte = time.time()
            print("  [%4.1f min] Reihe %d/%d - %d Anker"
                  % ((letzte - t0) / 60, nr, len(roh), len(aus)), flush=True)
    return aus


def quote(faelle):
    """Die ORIGINALGROESSE: Anteil 'Ziel vor Stop' unter den ENTSCHIEDENEN."""
    ent = [f for f in faelle if f["ausgang"] in ("ziel", "stop")]
    if len(ent) < 50:
        return float("nan"), 0
    return sum(1 for f in ent if f["ausgang"] == "ziel") / len(ent), len(ent)


def main():
    print("=" * 100)
    print("DIE ORIGINALMESSUNG VON H — FRISCH GERECHNET, DANN MIT KLAMMER")
    print("=" * 100)
    print("Lade Anker (523 Reihen, KEIN Zwischenspeicher)...", flush=True)
    faelle = laufe()
    n = len(faelle)
    n_h = sum(1 for f in faelle if f["h"])
    print("%d Anker, davon %d mit H (%.2f %%)" % (n, n_h, 100 * n_h / n))

    # ------------------------------------------------------ 1 GEPOOLT
    print()
    print("-" * 100)
    print("1 GEPOOLT — genau wie Kapitel 104 bis 121")
    print("-" * 100)
    q_alle, n_alle = quote(faelle)
    print("  %-40s %9s %10s" % ("Gruppe", "Faelle", "Quote"))
    for name, wo in (("alle Anker", lambda f: True),
                     ("A  freier Weg", lambda f: f["frei"]),
                     ("B  Stop gedeckt", lambda f: f["gedeckt"]),
                     ("H  A UND B", lambda f: f["h"])):
        q, nn = quote([f for f in faelle if wo(f)])
        if math.isnan(q):
            continue
        print("  %-40s %9d %9.2f %%   %+.2f Punkte gegen alle"
              % (name, nn, 100 * q, 100 * (q - q_alle)))

    # ------------------------------------------- 2 JE ZEITBLOCK / 3 JE TAG
    for klammer, block in (("2 JE ZEITBLOCK (120 Tage)", 120),
                           ("3 JE KALENDERTAG", 1)):
        print()
        print("-" * 100)
        print("%s" % klammer)
        print("-" * 100)
        tage = sorted({f["datum"] for f in faelle})
        zu = {t: i // block for i, t in enumerate(tage)}
        for name, wo in (("A  freier Weg", lambda f: f["frei"]),
                         ("B  Stop gedeckt", lambda f: f["gedeckt"]),
                         ("H  A UND B", lambda f: f["h"])):
            eimer = {}
            for f in faelle:
                if f["ausgang"] not in ("ziel", "stop"):
                    continue
                eimer.setdefault(zu[f["datum"]], ([], []))[0 if wo(f) else 1] \
                    .append(1.0 if f["ausgang"] == "ziel" else 0.0)
            mind = 30 if block > 1 else 5
            w = [float(np.mean(m)) - float(np.mean(o))
                 for m, o in eimer.values()
                 if len(m) >= mind and len(o) >= mind]
            if len(w) < 5:
                print("  %-40s zu wenige Einheiten" % name)
                continue
            b = np.array(w)
            r = np.random.default_rng(20260831)
            boot = np.array([b[r.integers(0, len(b), len(b))].mean()
                             for _ in range(ZIEHUNGEN)])
            u, o_ = np.quantile(boot, [0.025, 0.975])
            print("  %-40s %+7.2f Punkte  [%+.2f .. %+.2f]  %4d Einheiten  %s"
                  % (name, 100 * b.mean(), 100 * u, 100 * o_, len(b),
                     "TRAEGT" if u > 0 else
                     ("UMGEKEHRT" if o_ < 0 else "nicht trennbar")))

    print()
    print("=" * 100)
    print("LESART")
    print("=" * 100)
    print("  Steht H gepoolt im Plus und ist je Kalendertag nicht mehr von")
    print("  null zu trennen, dann misst der Originalbefund die LAGE, in der")
    print("  H auftritt - nicht die Guete der Anker, die es auswaehlt.")


if __name__ == "__main__":
    main()
