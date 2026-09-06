# -*- coding: utf-8 -*-
"""N10 — BARRIEREN-QUOTE GEGEN HORIZONT-QUOTE, gemessen (06.09.2026)

## Die Lücke

`messnorm` unterscheidet zwei Zielgroessen:

    bewegung_r   barrierenfrei, Rendite nach H Tagen   - ALLE Lagen
    barriere     Ziel vor Stop                          - nur wo ein Stop
                                                          den Trade BEENDET
    STOP_BEENDET = {("hebel","einstieg"), ("hebel","swing")}

**Fuer `hebel x einstieg` ist die Barriere die zutreffende Groesse.** Und
`r(q)` - die Hebelleiter - betrifft genau den Hebel. K1 braucht also die
BARRIEREN-Quote.

## ⚠️ Die Annahme, die heute schon drinsteckt

Die registrierten Beitraege sind auf `bewegung_r` gemessen und ueber

    d(quote) = d(Potential) / (1 + CRV)

in Quotenpunkte umgerechnet. Die Potentialformel `q*CRV - (1-q)` ist aber
eine BARRIEREN-Formel. **Eine bewegungsbasierte Wirkung wird in eine
Barrieren-Quote uebersetzt - das ist eine Annahme, keine Messung.**

Mein Randmass hat dieselbe Luecke: "Anteil ueber +2R nach H Tagen" ist eine
Quote, aber eine HORIZONT-Quote.

## Was hier gemessen wird

Fuer DIESELBEN Anker beide Groessen:

    BARRIERE    laeuft der Pfad zuerst auf +CRV*spanne oder auf -1*spanne?
                ⚠️ Werden beide am selben Tag beruehrt, zaehlt der VERLUST -
                   die vorsichtige Lesart, weil die Reihenfolge innerhalb
                   des Tages aus Tagesbalken nicht bestimmbar ist.
    HORIZONT    ist c[i+H] - c[i] groesser als +CRV*spanne?

Dann je `vola`-Fuenftel BEIDE Quoten - verschiebt die Groesse beide gleich?

    UEBERTRAEGT SICH   die Randmessung darf in die Kelly-Formel
    NICHT              dann ist die Uebersetzung eine offene Baustelle,
                       und zwar AUCH fuer die registrierten Beitraege

    python n10_barriere_gegen_horizont.py
"""
from __future__ import annotations

import sys
import time

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_eigenschaft_beitrag as B                        # noqa: E402
import messe_regel_wirksamkeit as W                          # noqa: E402
import messnorm as N                                         # noqa: E402

CRV, BRUCH, FAECHER = 2.0, 5.0, 5
HORIZONTE = (5, 20)


def baue(reihen, horizont):
    """Je Kalendertag: vola-Kennzahl, BARRIERE und HORIZONT fuer denselben Anker."""
    je_tag: dict = {}
    for sym, z in reihen.items():
        tage = [x[0] for x in z]
        c = np.array([x[1] for x in z], float)
        h = np.array([x[2] for x in z], float)
        t = np.array([x[3] for x in z], float)
        br = B.spanne(h, t, c, B.SCHWANKUNG)
        vh = c[1:] / np.maximum(c[:-1], 1e-12)
        bruch = (vh > BRUCH) | (vh < 1.0 / BRUCH)
        for i in range(B.SCHWANKUNG, len(c) - horizont):
            if not np.isfinite(br[i]) or br[i] <= 0:
                continue
            if bruch[i:i + horizont].any():
                continue
            ziel = c[i] + CRV * br[i]
            stop = c[i] - 1.0 * br[i]
            # ⚠️ Pfad Tag fuer Tag. Beruehrt ein Tag BEIDE Marken, zaehlt
            # der Verlust - die Reihenfolge innerhalb des Tages ist aus
            # Tagesbalken nicht bestimmbar, und die vorsichtige Lesart ist
            # hier die richtige.
            treffer = 0
            for j in range(i + 1, i + horizont + 1):
                if t[j] <= stop:
                    treffer = -1
                    break
                if h[j] >= ziel:
                    treffer = +1
                    break
            je_tag.setdefault(tage[i], []).append({
                "sym": sym,
                "kennzahl": float(br[i] / np.median(br[max(0, i - 250):i + 1])
                                  if i > 30 else 1.0),
                "barriere": 1.0 if treffer > 0 else 0.0,
                "offen": 1.0 if treffer == 0 else 0.0,
                "horizont": 1.0 if (c[i + horizont] - c[i]) > CRV * br[i]
                            else 0.0})
    return {t: z for t, z in je_tag.items() if len(z) >= 3 * FAECHER}


def stufen(je_tag, feld):
    """Je Fuenftel der Ueberschuss gegenueber dem Tagesmittel, je Tag."""
    reihen = [dict() for _ in range(FAECHER)]
    for tag, z in je_tag.items():
        w = np.array([x["kennzahl"] for x in z], float)
        y = np.array([x[feld] for x in z], float)
        f = np.minimum((W.rang(w) * FAECHER).astype(int), FAECHER - 1)
        basis = float(y.mean())
        for i in range(FAECHER):
            m = f == i
            if m.sum() >= 3:
                reihen[i][tag] = float(y[m].mean()) - basis
    return reihen


def band(d, block=15, zieh=2000, saat=20260906):
    rng = np.random.default_rng(saat)
    x = np.array([d[k] for k in sorted(d)], float)
    n = len(x)
    if n < block + 30:
        return None
    nb = max(1, n // block)
    st = np.arange(n - block + 1)
    aus = np.empty(zieh)
    for k in range(zieh):
        s = rng.choice(st, nb)
        aus[k] = np.concatenate([x[i:i + block] for i in s]).mean()
    return (float(x.mean()), float(np.percentile(aus, 2.5)),
            float(np.percentile(aus, 97.5)))


def main() -> int:
    t0 = time.time()
    print("Lade Reihen ...", flush=True)
    reihen = B.lade()

    for horizont in HORIZONTE:
        print()
        print("=" * 100)
        print("HORIZONT %d · CRV %.1f  —  Ziel +%.0f R, Stop -1 R"
              % (horizont, CRV, CRV))
        print("=" * 100)
        je_tag = baue(reihen, horizont)
        alle = [x for z in je_tag.values() for x in z]
        n = len(alle)
        b = float(np.mean([x["barriere"] for x in alle]))
        o = float(np.mean([x["offen"] for x in alle]))
        hz = float(np.mean([x["horizont"] for x in alle]))
        print("  %d Anker · %d Tage" % (n, len(je_tag)))
        print("  BARRIERE  Ziel vor Stop  %.2f %%   (offen geblieben %.2f %%)"
              % (100 * b, 100 * o))
        print("  HORIZONT  ueber +%.0f R   %.2f %%" % (CRV, 100 * hz))
        print("  ⚠️ Erwartung fuer die Barriere auf driftfreiem Pfad: "
              "1/(1+CRV) = %.2f %%" % (100 / (1 + CRV)))
        print()
        print("  Die Fuenftel — verschiebt `vola` BEIDE Quoten gleich?")
        print("  %-10s %26s %26s" % ("", "BARRIERE", "HORIZONT"))
        bs, hs = [], []
        for feld, ziel in (("barriere", bs), ("horizont", hs)):
            for i, d in enumerate(stufen(je_tag, feld)):
                ziel.append(band(d))
        for i in range(FAECHER):
            zb, zh = bs[i], hs[i]
            if zb is None or zh is None:
                print("  Fuenftel %d   zu wenige Tage" % i); continue
            print("  Fuenftel %d  %+7.3f [%+7.3f..%+7.3f]  %+7.3f [%+7.3f..%+7.3f]"
                  % (i, 100 * zb[0], 100 * zb[1], 100 * zb[2],
                     100 * zh[0], 100 * zh[1], 100 * zh[2]), flush=True)
        # Uebertraegt sich die Richtung?
        rb = np.array([z[0] for z in bs if z])
        rh = np.array([z[0] for z in hs if z])
        if len(rb) == FAECHER and len(rh) == FAECHER:
            r = float(np.corrcoef(rb, rh)[0, 1])
            spanne_b = float(rb.max() - rb.min())
            spanne_h = float(rh.max() - rh.min())
            print()
            print("  Spanne BARRIERE %.3f Punkte · HORIZONT %.3f Punkte · "
                  "Verhaeltnis %.2f" % (100 * spanne_b, 100 * spanne_h,
                                        spanne_b / spanne_h if spanne_h else 0))
            print("  Korrelation der Stufenreihen: %+.3f" % r)
            print("  -> %s" % ("die Richtung UEBERTRAEGT sich" if r > 0.8
                               else "⚠️ die Richtung uebertraegt sich NICHT"))
    print()
    print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
