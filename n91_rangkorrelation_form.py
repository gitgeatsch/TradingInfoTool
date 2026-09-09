# -*- coding: utf-8 -*-
"""N-91 — Die FORM über die Rangkorrelation, nicht über Fünftel

## Warum die Fünftel nicht taugen

N-90 ist an der Statistik gescheitert: `median(Fuenftel) - median(alle)`
bei rund 9 Ankern je Tag und Fuenftel ist zu verrauscht. Die **Kontrolle**
erzeugte Stufen von -33,89 bis +90,85 Punkten, waehrend die ganze
Beitragsskala bei +-5 liegt.

> **Ein Verfahren, dessen Kontrolle wilder ausschlaegt als der Kandidat,
> beantwortet die Frage nicht.**

Die Rangkorrelation hat dieses Problem nicht: sie benutzt **alle** Anker
eines Tages statt fuenf Gruppenmediane.

## ⚠️⚠️ Die Falle, und wie sie umgangen wird

**Ein BUCKEL und 'gar kein Zusammenhang' geben BEIDE eine
Rangkorrelation nahe null.** Spearman allein kann das nicht trennen -
die steigende und die fallende Haelfte heben sich auf.

Deshalb werden **zwei Haelften getrennt** gemessen:

    monoton    untere und obere Haelfte haben DASSELBE Vorzeichen
    Buckel     sie haben ENTGEGENGESETZTE Vorzeichen
    nichts     beide nahe null

Das trennt die drei Faelle sauber, und es ist vorab festgelegt.

## Der Aufbau

    je Kalendertag   Spearman(Rang der Kennzahl, in_r) ueber die
                     GEWAEHLTEN Anker - die Tagesklammer ist Pflicht,
                     gepoolt mischten sich die Marktphasen
    Haelften         derselbe Wert, getrennt fuer Rang < 0,5 und >= 0,5
    Band             Blockbootstrap ueber die Tagesreihe, Block 3 x H
    Auswahl          Momentum gegen FUENF Zufallsauswahlen gleicher Groesse
    Kontrolle        `zufall` - dort muessen alle drei Zahlen null sein

⚠️ Eine Entzerrung braucht es hier NICHT: unter gemischten Raengen ist
der Erwartungswert einer Rangkorrelation exakt null. Die Kontrolle
prueft genau das.

## Die Vorhersage, VOR dem Lauf (Methodik 2.80)

    Momentum   die Haelften zeigen ENTGEGENGESETZTE Vorzeichen - der
               Buckel ist dort real (dreimal gemessen)
    Zufall     sie zeigen DASSELBE Vorzeichen - dann war der Buckel
               ein Auswahl-Artefakt, und `schnitt` ist als Regler
               brauchbar
    Kontrolle  alles nahe null

⚠️ Zeigen die Haelften auch zufaellig entgegengesetzte Vorzeichen, ist
der Buckel die Form der Sache. Dann ist `schnitt` als REGLER endgueltig
ungeeignet - die SPERRE braucht aber keine Monotonie.

    python n91_rangkorrelation_form.py
"""
from __future__ import annotations

import sys
import time

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_beitrag_auf_auswahl as A                        # noqa: E402
import messe_eigenschaft_beitrag as B                        # noqa: E402
import messe_kandidaten_als_regel as K                       # noqa: E402
import messe_regel_wirksamkeit as W                          # noqa: E402
import messmenge                                              # noqa: E402
from messe_alle_kandidaten import HORIZONT, zusatzquellen    # noqa: E402
from messe_beitrag_auf_auswahl import momentum250            # noqa: E402
from messnorm import _block                                   # noqa: E402
from messnorm_auswahl import MENGEN                           # noqa: E402

MENGE = "20%"
SAATEN = (91001, 91002, 91003, 91004, 91005)
MIND_JE_HAELFTE = 8


def _spearman(a, b) -> float:
    """Rangkorrelation - Pearson auf den Raengen, ohne scipy."""
    if len(a) < 4:
        return float("nan")
    ra = np.argsort(np.argsort(a)).astype(float)
    rb = np.argsort(np.argsort(b)).astype(float)
    if ra.std() == 0 or rb.std() == 0:
        return float("nan")
    return float(np.corrcoef(ra, rb)[0, 1])


def reihen_je_tag(je_tag, mom, anteil, auswahl_saat=None):
    """Drei Tagesreihen: gesamt, untere Haelfte, obere Haelfte."""
    ganz, unten, oben = {}, {}, {}
    for tag, zeilen in je_tag.items():
        if len(zeilen) < 12:
            continue
        kz = np.array([x["kennzahl"] for x in zeilen], float)
        r = W.rang(kz)
        y = np.array([x["in_r"] for x in zeilen], float)
        m = A._auswahl_maske(
            zeilen, mom.get(tag) or {}, anteil,
            None if auswahl_saat is None
            else np.random.default_rng(int(auswahl_saat)))
        if m is None or not m.any():
            continue
        rw, yw = r[m], y[m]
        s = _spearman(rw, yw)
        if np.isfinite(s):
            ganz[tag] = s
        # ⚠️ Die Haelften werden am Rang der GEWAEHLTEN geteilt, nicht am
        # Marktrang - sonst liegt bei schmalen Mengen alles in einer.
        rr = np.argsort(np.argsort(rw)) / max(len(rw) - 1, 1)
        for name, maske in (("u", rr < 0.5), ("o", rr >= 0.5)):
            if maske.sum() >= MIND_JE_HAELFTE:
                s2 = _spearman(rw[maske], yw[maske])
                if np.isfinite(s2):
                    (unten if name == "u" else oben)[tag] = s2
    return ganz, unten, oben


def band(reihe, block, zieh=2000, saat=20260909):
    """Blockbootstrap ueber die Tagesreihe -> (Mittel, unten, oben)."""
    t = sorted(reihe)
    if len(t) < 4 * block:
        return None
    v = np.array([reihe[x] for x in t], float)
    bl = [v[i:i + block] for i in range(0, len(v), block)]
    bl = [b for b in bl if len(b) > 0]
    if len(bl) < 20:
        return None
    mit = np.array([b.mean() for b in bl])
    rng = np.random.default_rng(saat)
    n = len(mit)
    boot = np.array([mit[rng.integers(0, n, n)].mean() for _ in range(zieh)])
    return (float(mit.mean()), float(np.percentile(boot, 2.5)),
            float(np.percentile(boot, 97.5)), len(bl))


def form(u, o):
    """Urteil aus den beiden Haelften - vorab festgelegt."""
    if u is None or o is None:
        return "nicht messbar"
    tu = not (u[1] <= 0.0 <= u[2])
    to = not (o[1] <= 0.0 <= o[2])
    if not tu and not to:
        return "kein Zusammenhang (beide Baender enthalten null)"
    if tu and to:
        return ("✔ MONOTON, beide %s" % ("positiv" if u[0] > 0 else "negativ")
                if np.sign(u[0]) == np.sign(o[0])
                else "⚠️ BUCKEL - Haelften GEGENLAEUFIG")
    return ("nur %s trennbar (%s)"
            % ("die untere" if tu else "die obere",
               "%+.4f" % (u[0] if tu else o[0])))


def main() -> int:
    t0 = time.time()
    reihen = B.lade()
    mom = momentum250(reihen)
    zus = zusatzquellen()
    block = _block(HORIZONT)
    anteil = MENGEN[MENGE]

    print("=" * 108)
    print("N-91 — die FORM ueber die Rangkorrelation, je Tag")
    print("=" * 108)
    print("  %s" % messmenge.zeile())
    print("  Menge %s · Block %d · Spearman je Kalendertag ueber ALLE "
          "gewaehlten Anker" % (MENGE, block))
    print("  ⚠️ Ein Buckel und 'kein Zusammenhang' geben BEIDE ~0 -")
    print("     deshalb die Haelften getrennt: gleiches Vorzeichen = "
          "monoton, gegenlaeufig = Buckel.")

    for kand in ("schnitt", "funding", "zufall"):
        je = K.baue(reihen, kand, zus.get(kand), horizont=HORIZONT)
        print()
        print("  %s" % kand.upper())
        print("     %-10s %22s %22s %22s  %s"
              % ("Auswahl", "gesamt", "untere Haelfte", "obere Haelfte",
                 "Form"))
        for name, saat in [("Momentum", None)] + \
                          [("Zufall %d" % (i + 1), s)
                           for i, s in enumerate(SAATEN)]:
            g, u, o = reihen_je_tag(je, mom, anteil, auswahl_saat=saat)
            bg, bu, bo = band(g, block), band(u, block), band(o, block)
            def z(b):
                return ("%+.4f [%+.3f..%+.3f]" % (b[0], b[1], b[2])
                        if b else "nicht messbar")
            print("     %-10s %22s %22s %22s  %s"
                  % (name, z(bg), z(bu), z(bo), form(bu, bo)), flush=True)

    print()
    print("=" * 108)
    print("WAS DAS HEISST")
    print("=" * 108)
    print("  ⚠️ Entscheidend: zeigen die Haelften bei ZUFAELLIGER Auswahl")
    print("     dasselbe Vorzeichen, war der Buckel ein Auswahl-Artefakt")
    print("     und `schnitt` waere als Regler brauchbar.")
    print("  ⚠️ Bleiben sie gegenlaeufig, ist der Buckel die Form der "
          "Sache -")
    print("     dann ist `schnitt` als REGLER ungeeignet, die SPERRE aber "
          "unberuehrt.")
    print("  ⚠️⚠️ Und die Kontrolle `zufall` muss ueberall null zeigen, "
          "sonst gilt nichts davon.")
    print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
