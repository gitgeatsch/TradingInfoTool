# -*- coding: utf-8 -*-
"""N23 — WELCHE FORM HABEN DIE BEITRÄGE WIRKLICH? (06.09.2026)

## Die Frage, praeziser gestellt

Nicht *„Schalter oder Regler"* - das sind nur zwei von vier moeglichen
Formen. Gefragt ist: **welche Aufteilung ist die GROEBSTE, die noch belegt
ist?**

    SCHALTER      genau EIN Fach hebt sich ab       -> Trichterstufe
    ZWEITEILUNG   oben gegen unten belegt, Mitte nicht
    DREITEILUNG   unten / Mitte / oben paarweise getrennt
    REGLER        alle vier Nachbarpaare der Fuenftel getrennt

Der Praezedenzfall: **H-4c (02.09.)** entschied `oi_aenderung` als
SCHALTER, weil *„die vorab gesetzte Monotoniebedingung fiel - belastbar ist
allein Fuenftel 4"*. Daraus wurde eine **Trichterstufe statt eines
Beitrags**. Dieselbe Entscheidung steht jetzt fuer `funding` und
`turnover` an.

## Der Hinweis aus N19-E

    funding  H20   -0,661  +1,053  +0,433  -0,130  -0,617
                   nur Fuenftel 1 mit Band ohne Null  -> Schalter?
    turnover H20   +1,690  +0,578  -1,127  +0,101  -1,311
                   Fuenftel 0 UND 4 belegt, Mitte nicht -> Zweiteilung?
    vola     H5    4 von 4 Nachbarpaaren getrennt      -> Regler

## ⚠️ Die Lehre aus N22 ist eingebaut

Jede Kontrolle laeuft mit **fuenf Mischungen**, und die Erwartung wird
VORHER genannt:

    Zellen x Irrtumsschwelle = erwartete Fehlalarme

    python n23_form_der_beitraege.py
"""
from __future__ import annotations

import sys
import time

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_bewertungskennzahl as MB                        # noqa: E402
import messe_eigenschaft_beitrag as B                        # noqa: E402
import messe_funding_niveau as F                             # noqa: E402
import messe_regel_wirksamkeit as W                          # noqa: E402

CRV, BRUCH = 2.0, 5.0
MISCHUNGEN = 5


def baue(reihen, zusatz, art, horizont):
    je_tag: dict = {}
    for sym, z in reihen.items():
        tage = [x[0] for x in z]
        c = np.array([x[1] for x in z], float)
        h = np.array([x[2] for x in z], float)
        t = np.array([x[3] for x in z], float)
        br = B.spanne(h, t, c, B.SCHWANKUNG)
        vh = c[1:] / np.maximum(c[:-1], 1e-12)
        bruch = (vh > BRUCH) | (vh < 1.0 / BRUCH)
        je_sym = (zusatz or {}).get(sym.upper()) or {}
        for i in range(B.SCHWANKUNG, len(c) - horizont):
            if not np.isfinite(br[i]) or br[i] <= 0 or bruch[i:i + horizont].any():
                continue
            if art == "vola":
                if i < 260:
                    continue
                kz = float(br[i] / np.median(br[i - 250:i + 1]))
            else:
                w = je_sym.get(tage[i])
                if w is None:
                    continue
                kz = float(w)
            ziel, stop = c[i] + CRV * br[i], c[i] - 1.0 * br[i]
            aus = 0
            for j in range(i + 1, i + horizont + 1):
                if t[j] <= stop:
                    aus = -1
                    break
                if h[j] >= ziel:
                    aus = +1
                    break
            je_tag.setdefault(tage[i], []).append(
                {"kennzahl": kz, "treffer": 1.0 if aus > 0 else 0.0})
    return {t: z for t, z in je_tag.items() if len(z) >= 20}


def faecher(je_tag, k, mische=None):
    """Je Tag der Ueberschuss je Fach, bei k Faechern."""
    reihen = [dict() for _ in range(k)]
    for tag, z in je_tag.items():
        w = np.array([x["kennzahl"] for x in z], float)
        y = np.array([x["treffer"] for x in z], float)
        r = W.rang(w)
        if mische is not None:
            r = mische.permutation(r)
        f = np.minimum((r * k).astype(int), k - 1)
        basis = float(y.mean())
        for i in range(k):
            m = f == i
            if m.sum() >= 3:
                reihen[i][tag] = float(y[m].mean()) - basis
    return reihen


def band(d, block, zieh=1500, saat=20260906):
    rng = np.random.default_rng(saat)
    x = np.array([d[q] for q in sorted(d)], float)
    n = len(x)
    if n < block + 30:
        return None
    nb = max(1, n // block)
    st = np.arange(n - block + 1)
    aus = np.empty(zieh)
    for j in range(zieh):
        s = rng.choice(st, nb)
        aus[j] = np.concatenate([x[i:i + block] for i in s]).mean()
    return (float(x.mean()), float(np.percentile(aus, 2.5)),
            float(np.percentile(aus, 97.5)))


def bewerte(je_tag, k, block):
    """Wieviele Faecher sind von NULL getrennt, wieviele Nachbarn voneinander?"""
    b = [band(d, block) for d in faecher(je_tag, k)]
    if any(x is None for x in b):
        return None
    ohne_null = sum(1 for x in b if x[1] > 0 or x[2] < 0)
    nachbarn = sum(1 for i in range(k - 1)
                   if b[i][1] > b[i + 1][2] or b[i][2] < b[i + 1][1])
    # Kontrolle mit MEHREREN Mischungen (Lehre aus N22)
    falsch = 0
    for s in range(MISCHUNGEN):
        nb = [band(d, block) for d in
              faecher(je_tag, k, np.random.default_rng(7000 + s))]
        falsch += sum(1 for x in nb if x and (x[1] > 0 or x[2] < 0))
    return b, ohne_null, nachbarn, falsch


def main() -> int:
    t0 = time.time()
    print("Lade Reihen ...", flush=True)
    reihen = B.lade()
    quellen = {"funding": F.lade_funding(),
               "turnover": MB.reihe("data/onchain_historie.db", "splycur"),
               "vola": None}

    for horizont in (20, 5):
        block = max(15, 3 * horizont)
        print()
        print("#" * 100)
        print("# HORIZONT %d · Block %d" % (horizont, block))
        print("#" * 100)
        for art, zusatz in quellen.items():
            je_tag = baue(reihen, zusatz, art, horizont)
            if len(je_tag) < 300:
                print("  %-10s zu wenige Tage" % art); continue
            print()
            print("  %s — %d Tage" % (art.upper(), len(je_tag)))
            print("    %-14s %-34s %9s %10s  %s"
                  % ("Aufteilung", "Faecher", "ohne Null", "Nachbarn",
                     "Kontrolle (erwartet)"))
            beste = None
            for k, lab in ((2, "ZWEITEILUNG"), (3, "DREITEILUNG"),
                           (5, "FUENFTEILUNG")):
                e = bewerte(je_tag, k, block)
                if e is None:
                    print("    %-14s   zu wenige Tage" % lab); continue
                b, ohne, nach, falsch = e
                erwartet = 0.05 * k * MISCHUNGEN
                werte = " ".join("%+6.2f" % (100 * x[0]) for x in b)
                print("    %-14s %-34s %6d/%d %7d/%d  %d von %d (%.1f)"
                      % (lab, werte, ohne, k, nach, k - 1,
                         falsch, k * MISCHUNGEN, erwartet), flush=True)
                if nach == k - 1 and falsch <= erwartet * 2:
                    beste = lab
            # Die Form
            e2 = bewerte(je_tag, 5, block)
            if e2:
                b, ohne, nach, _f = e2
                if nach == 4:
                    form = "REGLER (alle Nachbarn getrennt)"
                elif ohne == 1:
                    form = "SCHALTER (genau EIN Fach von null getrennt)"
                elif ohne >= 2 and nach <= 1:
                    form = "ZWEI POLE (Extreme belegt, Mitte nicht)"
                elif ohne == 0:
                    form = "⚠️ KEINE Form belegt"
                else:
                    form = "unbestimmt"
                print("    -> FORM: %s%s"
                      % (form, "  · groebste belegte Aufteilung: %s" % beste
                         if beste else ""))
    print()
    print("  ⚠️ SCHALTER gehoert als TRICHTERSTUFE gebaut (Praezedenzfall")
    print("     H-4c/N-14), REGLER als abgestufter Beitrag. Zwei Pole sind")
    print("     eine Zweiteilung - also auch ein Schalter, nur mit zwei")
    print("     Richtungen.")
    print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
