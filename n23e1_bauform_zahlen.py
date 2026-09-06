# -*- coding: utf-8 -*-
"""N23-E1 — WAS KOSTET DIE VERGRÖBERUNG? Die Zahlen zur Entscheidung (06.09.)

## Die Lage

N23 hat gemessen: **keine der drei Größen trägt eine belegte Fünfteilung.**
Die registrierten Tabellen (`funding` fünf Stufen, `turnover` fünf Stufen)
unterstellen eine Auflösung, die die Daten nicht hergeben.

    funding   H5   belegte ZWEITEILUNG
    turnover  H5   KEINE Form belegt
    vola      H5   belegte DREITEILUNG (Kontrolle 0/15)

## Was hier gemessen wird — die Zahlen zur Entscheidung

    1  DIE KONKRETEN STUFEN je belegter Form, mit Band
       (das ist die Tabelle, die in `BEITRAEGE.stufen` stuende)

    2  DIE WIRKUNG ALS REGEL bei 2, 3 und 5 Faechern
       ⚠️ Kostet die Vergroeberung Wirkung - oder nicht?
       Eine Form, die weniger Auflösung hat, aber dieselbe Wirkung,
       ist die bessere: sie behauptet weniger.

    3  BEIDE HISTORIENHAELFTEN fuer die belegte Form
       Was ueber die Zeit nicht haelt, gehoert nicht registriert.

⚠️ Kontrollen mit FUENF Mischungen, Erwartung vorab genannt (N22).

    python n23e1_bauform_zahlen.py
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

CRV, BRUCH, HORIZONT, BLOCK = 2.0, 5.0, 5, 15
MISCHUNGEN = 5


def baue(reihen, zusatz, art):
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
        for i in range(B.SCHWANKUNG, len(c) - HORIZONT):
            if not np.isfinite(br[i]) or br[i] <= 0 or bruch[i:i + HORIZONT].any():
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
            for j in range(i + 1, i + HORIZONT + 1):
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


def regel(je_tag, k, mische=None):
    """Die WIRKUNG als Regel: bestes Fach behalten, Rest sperren.

    ⚠️ Vergleichbar ueber die Faecherzahl gemacht, indem immer DASSELBE
    gefragt wird: wieviel hebt die Regel die Trefferquote der Behaltenen
    gegenueber allen - mal dem Anteil der Behaltenen.
    """
    aus = {}
    for tag, z in je_tag.items():
        w = np.array([x["kennzahl"] for x in z], float)
        y = np.array([x["treffer"] for x in z], float)
        r = W.rang(w)
        if mische is not None:
            r = mische.permutation(r)
        f = np.minimum((r * k).astype(int), k - 1)
        frei = f < k - 1              # das oberste Fach wird gesperrt
        if frei.sum() < 3 or (~frei).sum() < 1:
            continue
        aus[tag] = (float(y[frei].mean()) - float(y.mean())) * float(frei.mean())
    return aus


def band(d, zieh=1500, saat=20260906):
    rng = np.random.default_rng(saat)
    x = np.array([d[q] for q in sorted(d)], float)
    n = len(x)
    if n < BLOCK + 30:
        return None
    nb = max(1, n // BLOCK)
    st = np.arange(n - BLOCK + 1)
    aus = np.empty(zieh)
    for j in range(zieh):
        s = rng.choice(st, nb)
        aus[j] = np.concatenate([x[i:i + BLOCK] for i in s]).mean()
    return (float(x.mean()), float(np.percentile(aus, 2.5)),
            float(np.percentile(aus, 97.5)))


def main() -> int:
    t0 = time.time()
    print("Lade Reihen ...", flush=True)
    reihen = B.lade()
    quellen = {"funding": F.lade_funding(),
               "turnover": MB.reihe("data/onchain_historie.db", "splycur"),
               "vola": None}
    welten = {a: baue(reihen, q, a) for a, q in quellen.items()}

    print()
    print("=" * 96)
    print("1  DIE KONKRETEN STUFEN je Form — Prozentpunkte auf die Quote")
    print("=" * 96)
    for art, je_tag in welten.items():
        print("  %s (%d Tage)" % (art.upper(), len(je_tag)))
        for k, lab in ((2, "Zweiteilung"), (3, "Dreiteilung")):
            b = [band(d) for d in faecher(je_tag, k)]
            if any(x is None for x in b):
                print("    %-12s   zu wenige Tage" % lab); continue
            roh = " · ".join("%+6.3f" % (100 * x[0]) for x in b)
            geschr = " · ".join("%+6.3f" % (50 * x[0]) for x in b)
            print("    %-12s roh %s" % (lab, roh))
            print("    %-12s geschrumpft (÷2) %s" % ("", geschr))
        print()

    print("=" * 96)
    print("2  DIE WIRKUNG ALS REGEL — kostet die Vergroeberung etwas?")
    print("=" * 96)
    print("  %-10s %-14s %10s %24s  %s"
          % ("Groesse", "Faecher", "Wirkung", "Band", "Kontrolle (erw. 0,25)"))
    for art, je_tag in welten.items():
        for k in (2, 3, 5):
            d = regel(je_tag, k)
            b = band(d)
            if b is None:
                print("  %-10s %-14d   zu wenige Tage" % (art, k)); continue
            falsch = 0
            for s in range(MISCHUNGEN):
                nb = band(regel(je_tag, k, np.random.default_rng(8000 + s)))
                if nb and (nb[1] > 0 or nb[2] < 0):
                    falsch += 1
            traegt = b[1] > 0
            print("  %-10s %-14s %+10.5f  [%+.5f .. %+.5f]  %d von %d %s"
                  % (art, "%d (sperrt %.0f %%)" % (k, 100.0 / k),
                     b[0], b[1], b[2], falsch, MISCHUNGEN,
                     "✔ TRAEGT" if traegt else ""), flush=True)
        print()

    print("=" * 96)
    print("3  BEIDE HISTORIENHAELFTEN — Dreiteilung")
    print("=" * 96)
    for art, je_tag in welten.items():
        tage = sorted(je_tag)
        mitte = tage[len(tage) // 2]
        print("  %s" % art.upper())
        for lab, filt in (("erste Haelfte", lambda t: t < mitte),
                          ("zweite Haelfte", lambda t: t >= mitte)):
            teil = {t: z for t, z in je_tag.items() if filt(t)}
            b = [band(d) for d in faecher(teil, 3)]
            if any(x is None for x in b):
                print("    %-16s zu wenige Tage" % lab); continue
            nach = sum(1 for i in range(2)
                       if b[i][1] > b[i + 1][2] or b[i][2] < b[i + 1][1])
            print("    %-16s %s   %d von 2 Nachbarn getrennt"
                  % (lab, " · ".join("%+6.3f" % (100 * x[0]) for x in b),
                     nach), flush=True)
        print()
    print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
