# -*- coding: utf-8 -*-
"""N22 — WARUM IST DIE ZUFALLSKONTROLLE BEI `funding` NICHT FLACH? (06.09.)

## Der Befund aus N19-E

    funding H20  Fuenftel 4   +0,321 [+0,088 .. +0,589]   Band ohne Null
    funding H5   Fuenftel 4   +0,276 [+0,034 .. +0,567]   Band ohne Null
    turnover H5  Fuenftel 1   -0,344 [-0,739 .. -0,005]   Band ohne Null

Eine Zufallskontrolle MUSS flach liegen. Tut sie es nicht, misst das
Verfahren sich selbst - und alle Befunde des Laufs waeren ungueltig.

## ⚠️ Der erste Verdaechtige ist die KONTROLLE SELBST

Drei Hypothesen, in dieser Reihenfolge:

  H1  EINE ZIEHUNG. Die Kontrolle lief mit EINER Mischung (Saat 4242).
      Bei 5 Fuenfteln x 3 Kandidaten x 2 Horizonten = 30 Zellen und einem
      95-%-Band sind rund 1,5 Fehlalarme zu ERWARTEN. Beobachtet wurden 3.
      ⚠️ Derselbe Fehler wie am 06.09. schon zweimal - "eine Ziehung ist
      kein Nullpunkt" (Methodik 2.104).

  H2  GEBUNDENE WERTE. `W.rang` bricht Bindungen ueber die Feldreihenfolge
      (doppeltes argsort). Hat `funding` viele identische Werte je Tag,
      ist der Rang dort faktisch die SYMBOLREIHENFOLGE - eine feste
      Struktur, die eine Mischung zwar zerstoert, die aber ungleiche
      Fuenftel erzeugt.

  H3  UNGLEICHE FUENFTEL. Sind die Faecher verschieden gross, wird die
      Bedingung `m.sum() >= 3` fuer manche systematisch verletzt.

    python n22_kontrolle_bei_funding.py
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

CRV, BRUCH, FAECHER, HORIZONT = 2.0, 5.0, 5, 20
BLOCK = 60


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
    return {t: z for t, z in je_tag.items() if len(z) >= 3 * FAECHER}


def stufen(je_tag, mische=None):
    reihen = [dict() for _ in range(FAECHER)]
    groessen = [[] for _ in range(FAECHER)]
    for tag, z in je_tag.items():
        w = np.array([x["kennzahl"] for x in z], float)
        y = np.array([x["treffer"] for x in z], float)
        r = W.rang(w)
        if mische is not None:
            r = mische.permutation(r)
        f = np.minimum((r * FAECHER).astype(int), FAECHER - 1)
        basis = float(y.mean())
        for i in range(FAECHER):
            m = f == i
            groessen[i].append(int(m.sum()))
            if m.sum() >= 3:
                reihen[i][tag] = float(y[m].mean()) - basis
    return reihen, groessen


def band(d, zieh=1500, saat=20260906):
    rng = np.random.default_rng(saat)
    x = np.array([d[k] for k in sorted(d)], float)
    n = len(x)
    if n < BLOCK + 30:
        return None
    nb = max(1, n // BLOCK)
    st = np.arange(n - BLOCK + 1)
    aus = np.empty(zieh)
    for k in range(zieh):
        s = rng.choice(st, nb)
        aus[k] = np.concatenate([x[i:i + BLOCK] for i in s]).mean()
    return (float(x.mean()), float(np.percentile(aus, 2.5)),
            float(np.percentile(aus, 97.5)))


def main() -> int:
    t0 = time.time()
    print("Lade Reihen ...", flush=True)
    reihen = B.lade()
    quellen = {"funding": F.lade_funding(),
               "turnover": MB.reihe("data/onchain_historie.db", "splycur")}

    for art, zusatz in quellen.items():
        je_tag = baue(reihen, zusatz, art)
        print()
        print("=" * 96)
        print("%s — H%d · %d Tage" % (art.upper(), HORIZONT, len(je_tag)))
        print("=" * 96)

        # ---- H2/H3  gebundene Werte und Faechergroessen ------------------
        band_anteil, gr_spanne = [], []
        for tag, z in list(je_tag.items())[:600]:
            w = np.array([x["kennzahl"] for x in z], float)
            band_anteil.append(1.0 - len(np.unique(w)) / len(w))
        _r, gr = stufen(je_tag)
        for i in range(FAECHER):
            gr_spanne.append(float(np.mean(gr[i])))
        print("  H2  Anteil GEBUNDENER Werte je Tag: %.1f %% (Median %.1f %%)"
              % (100 * np.mean(band_anteil), 100 * np.median(band_anteil)))
        print("  H3  mittlere Faechergroesse: %s"
              % " · ".join("%.1f" % g for g in gr_spanne))
        ungleich = max(gr_spanne) / max(min(gr_spanne), 1e-9)
        print("      Verhaeltnis groesstes/kleinstes Fach: %.2f  %s"
              % (ungleich, "✔ gleichmaessig" if ungleich < 1.3
                 else "⚠️ UNGLEICH"))

        # ---- H1  mehrere Mischungen --------------------------------------
        print()
        print("  H1  ZEHN Mischungen statt einer — bleibt die Kontrolle")
        print("      bei denselben Fuenfteln unruhig?")
        treffer = [0] * FAECHER
        werte = [[] for _ in range(FAECHER)]
        for k, saat in enumerate(range(4242, 4252)):
            rr, _g = stufen(je_tag, np.random.default_rng(saat))
            for i in range(FAECHER):
                b = band(rr[i])
                if b is None:
                    continue
                werte[i].append(b[0])
                if b[1] > 0 or b[2] < 0:
                    treffer[i] += 1
        print("      %-9s %10s %12s  %s"
              % ("Fuenftel", "Mittel", "Streuung", "Baender OHNE Null"))
        for i in range(FAECHER):
            v = np.array(werte[i], float)
            marke = ("⚠️ systematisch" if treffer[i] >= 7 else
                     "Zufall" if treffer[i] <= 2 else "unklar")
            print("      %-9d %+10.4f %12.4f  %d von 10   %s"
                  % (i, 100 * v.mean(), 100 * v.std(ddof=1),
                     treffer[i], marke))
        ges = sum(treffer)
        print()
        print("      ⚠️ Erwartung bei reinem Zufall: rund 5 %% von 50 "
              "Zellen = 2,5")
        print("      beobachtet: %d von 50  ->  %s"
              % (ges, "✔ im Rahmen" if ges <= 6 else
                 "⚠️ MEHR als Zufall - die Kontrolle hat ein Problem"))
    print()
    print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
