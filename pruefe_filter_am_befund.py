# -*- coding: utf-8 -*-
"""Der Filter am ECHTEN Befund (2.115) geprueft - zweiter Test (06.09.2026).

Ein Nullbefund auf EINEM Messaufbau ist kein Urteil. Hier derselbe
Vergleich an der Messung, die einen belegten Effekt hat: gefallen gegen
aufgestiegen, ab Rang 101, Anteil > +3 R ueber 5 Tage.

Wenn der Filter etwas taugt, muss er DIESEN Effekt schaerfer zeigen -
groesserer Wert oder engeres Band.
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
    st = np.arange(n - block + 1)
    aus = np.empty(zieh)
    for k in range(zieh):
        s = rng.choice(st, nb)
        aus[k] = np.concatenate([d[i:i + block] for i in s]).mean()
    return float(np.percentile(aus, 2.5)), float(np.percentile(aus, 97.5))


def main() -> int:
    print("Lade Reihen ...", flush=True)
    reihen = B.lade()
    gut = set()
    for sym, r in reihen.items():
        tage = [x[0] for x in r]
        m = np.array([x >= "2024-01-01" for x in tage])
        if m.sum() < 120:
            continue
        c = np.array([x[1] for x in r], float)[m]
        v = np.array([x[4] for x in r], float)[m]
        if (np.mean(np.diff(c) == 0.0) < 0.05 and np.median(v * c) > 1e6
                and np.median(c) > 0.01):
            gut.add(sym)
    print("  Filter behaelt %d Reihen" % len(gut))

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

    print()
    print("=" * 88)
    print("GEFALLEN minus AUFGESTIEGEN, ab Rang 101, Anteil > +%.0f R" % MARKE)
    print("=" * 88)
    print("  %-10s %7s %8s %10s %24s  %s"
          % ("Welt", "Tage", "n/Tag", "Wert", "Band", "Urteil"))
    for lab, nur in (("ALLE", False), ("GEFILTERT", True)):
        tage = sorted(t for t, w in daten.items()
                      if len([q for q in w if not nur or q[0] in gut]) >= 50)
        rang = {t: {q[0]: r for r, q in enumerate(
            sorted([q for q in daten[t] if not nur or q[0] in gut],
                   key=lambda x: -x[1]))} for t in tage}
        idx = {t: i for i, t in enumerate(tage)}
        d, anz = [], []
        for t in tage:
            i = idx[t]
            if i < ZURUECK:
                continue
            alt = rang[tage[i - ZURUECK]]
            w = [q for q in sorted(
                [q for q in daten[t] if not nur or q[0] in gut],
                key=lambda x: -x[1])[100:] if q[0] in alt]
            if len(w) < 20:
                continue
            dd = np.array([rang[t][q[0]] - alt[q[0]] for q in w])
            y = np.array([q[2] for q in w]) > MARKE
            g, a = y[dd >= 20], y[dd < -20]
            if len(g) >= 5 and len(a) >= 5:
                d.append(float(g.mean() - a.mean())); anz.append(len(w))
        d = np.array(d)
        lo, hi = band(d)
        print("  %-10s %7d %8.1f %10.4f   [%+.4f , %+.4f]  %s"
              % (lab, len(d), np.mean(anz), d.mean(), lo, hi,
                 "TRAEGT" if lo > 0 or hi < 0 else "traegt nicht"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
