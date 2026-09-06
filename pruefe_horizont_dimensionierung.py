# -*- coding: utf-8 -*-
"""BAND auf die Horizont-Dimensionierung (06.09.2026).

Behauptung aus der Dimensionierung:
  die RANDASYMMETRIE (Anteil > +2R minus Anteil < -2R) ist bei kurzem
  Horizont positiv und kippt mit laengerem Horizont ins Negative -
  und zwar UMSO FRUEHER, je tiefer die Rangschicht.

Geprueft je Schicht und Horizont mit Blockbootstrap, plus Zufallskontrolle
(Rangzuordnung gemischt -> alle Schichten muessen gleich aussehen).
"""
from __future__ import annotations
import sys
import numpy as np
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import messe_eigenschaft_beitrag as B                       # noqa: E402

BRUCH, RB, MARKE = 5.0, 252, 2.0
HOR = (1, 3, 5, 10, 20)
EIMER = (("Rang 1-5", 0, 5), ("Rang 6-100", 5, 100), ("ab Rang 101", 100, 10**6))


def gleit(x, n):
    c = np.concatenate(([0.0], np.cumsum(x)))
    a = np.full(len(x), np.nan)
    a[n:] = (c[n:-1] - c[:-n - 1]) / n
    return a


def band(d, block, zieh=3000, saat=20260906):
    rng = np.random.default_rng(saat)
    n = len(d); nb = max(1, n // block)
    start = np.arange(n - block + 1)
    aus = np.empty(zieh)
    for k in range(zieh):
        s = rng.choice(start, nb)
        aus[k] = np.concatenate([d[i:i + block] for i in s]).mean()
    return float(np.percentile(aus, 2.5)), float(np.percentile(aus, 97.5))


def main() -> int:
    print("Lade Reihen ...", flush=True)
    reihen = B.lade()
    daten: dict = {}
    mx = max(HOR)
    for sym, z in reihen.items():
        tage = [x[0] for x in z]
        c = np.array([x[1] for x in z]); h = np.array([x[2] for x in z])
        t = np.array([x[3] for x in z]); v = np.array([x[4] for x in z])
        br = B.spanne(h, t, c, B.SCHWANKUNG)
        u = gleit(v * c, RB)
        vh = c[1:] / np.maximum(c[:-1], 1e-12)
        bruch = (vh > BRUCH) | (vh < 1.0 / BRUCH)
        for i in range(RB, len(c) - mx):
            if not np.isfinite(br[i]) or br[i] <= 0 or not np.isfinite(u[i]):
                continue
            if u[i] <= 0 or bruch[i:i + mx].any():
                continue
            daten.setdefault(tage[i], []).append(
                (float(u[i]), np.array([(c[i + H] - c[i]) / br[i]
                                        for H in HOR])))
    tage = [t for t in sorted(daten) if len(daten[t]) >= 50 and t >= "2024-01-01"]
    print("  %d Tage ab 2024" % len(tage))
    sortiert = {t: sorted(daten[t], key=lambda x: -x[0]) for t in tage}
    rng = np.random.default_rng(11)
    gemischt = {t: [q for q in np.array(sortiert[t], dtype=object)
                    [rng.permutation(len(sortiert[t]))]] for t in tage}

    for lab, quelle in (("ECHT", sortiert), ("ZUFALLSKONTROLLE", gemischt)):
        print()
        print("=" * 92)
        print("%s   Randasymmetrie  Anteil>+2R minus Anteil<-2R" % lab)
        print("=" * 92)
        print("  %-13s %-6s %9s %22s   %s"
              % ("Schicht", "H", "Wert", "Band (Block 3xH)", "Urteil"))
        for name, lo, hi in EIMER:
            for j, H in enumerate(HOR):
                d = []
                for t in tage:
                    w = quelle[t][lo:hi]
                    if len(w) < 3:
                        continue
                    x = np.array([q[1][j] for q in w])
                    d.append(float((x > MARKE).mean() - (x < -MARKE).mean()))
                d = np.array(d)
                blk = max(15, 3 * H)
                l, u_ = band(d, blk)
                u2 = ("POSITIV" if l > 0 else "NEGATIV" if u_ < 0 else "null")
                print("  %-13s %-6d %+9.4f   [%+.4f , %+.4f]   %s"
                      % (name, H, d.mean(), l, u_, u2))
            print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
