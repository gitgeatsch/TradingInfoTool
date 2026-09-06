# -*- coding: utf-8 -*-
"""BAND auf den Randbefund: gefallen gegen aufgestiegen (06.09.2026).

Gepaart am SELBEN Tag, in derselben Schicht - damit ist die Marktlage
konstant gehalten. Blockbootstrap Block 15, wie in der Norm.
Zusaetzlich eine ZUFALLSKONTROLLE: dieselbe Rechnung mit gemischter
Gruppenzuordnung muss die Null enthalten.
"""
from __future__ import annotations
import sys
import numpy as np
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import messe_eigenschaft_beitrag as B                       # noqa: E402

BRUCH, RB, ZURUECK, H, MARKE = 5.0, 252, 180, 5, 3.0


def gleit(x, n):
    c = np.concatenate(([0.0], np.cumsum(x)))
    a = np.full(len(x), np.nan)
    a[n:] = (c[n:-1] - c[:-n - 1]) / n
    return a


def band(d, block=15, zieh=4000, saat=20260906):
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
    for sym, z in reihen.items():
        tage = [x[0] for x in z]
        c = np.array([x[1] for x in z]); h = np.array([x[2] for x in z])
        t = np.array([x[3] for x in z]); v = np.array([x[4] for x in z])
        br = B.spanne(h, t, c, B.SCHWANKUNG)
        u = gleit(v * c, RB)
        vh = c[1:] / np.maximum(c[:-1], 1e-12)
        bruch = (vh > BRUCH) | (vh < 1.0 / BRUCH)
        for i in range(RB, len(c) - H):
            if not np.isfinite(br[i]) or br[i] <= 0 or not np.isfinite(u[i]):
                continue
            if u[i] <= 0 or bruch[i:i + H].any():
                continue
            daten.setdefault(tage[i], []).append(
                (sym, float(u[i]), float((c[i + H] - c[i]) / br[i])))
    tage = sorted(t for t, w in daten.items() if len(w) >= 50)
    rang = {t: {q[0]: r for r, q in
                enumerate(sorted(daten[t], key=lambda x: -x[1]))}
            for t in tage}
    idx = {t: i for i, t in enumerate(tage)}

    def paare(mische, saat=7):
        rng = np.random.default_rng(saat)
        d = []
        for t in tage:
            i = idx[t]
            if i < ZURUECK:
                continue
            alt = rang[tage[i - ZURUECK]]
            w = [q for q in sorted(daten[t], key=lambda x: -x[1])[100:]
                 if q[0] in alt]
            if len(w) < 20:
                continue
            dd = np.array([rang[t][q[0]] - alt[q[0]] for q in w])
            y = np.array([q[2] for q in w]) > MARKE
            if mische:
                dd = dd[rng.permutation(len(dd))]
            g, a = y[dd >= 20], y[dd < -20]
            if len(g) >= 5 and len(a) >= 5:
                d.append(float(g.mean() - a.mean()))
        return np.array(d, float)

    print()
    print("=" * 80)
    print("GEFALLEN minus AUFGESTIEGEN, ab Rang 101, Anteil > +%.0f R ueber %d Tage"
          % (MARKE, H))
    print("=" * 80)
    for lab, mische in (("ECHT           ", False),
                        ("Zufallskontrolle", True)):
        d = paare(mische)
        lo, hi = band(d)
        urteil = ("Band schliesst Null aus" if lo > 0 or hi < 0
                  else "Band enthaelt die Null")
        print("  %s  %d Tage · %+.4f  Band [%+.4f , %+.4f]  -> %s"
              % (lab, len(d), d.mean(), lo, hi, urteil))
    print()
    print("  Die Zufallskontrolle MUSS die Null enthalten - sonst misst das")
    print("  Verfahren sich selbst.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
