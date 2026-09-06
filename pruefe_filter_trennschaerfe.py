# -*- coding: utf-8 -*-
"""MACHT DER FILTER DIE MESSUNG SCHAERFER? (06.09.2026)

Nutzervorgabe: *"den Datenmuell von guten Daten trennen - wir kappen und
kalibrieren auf ECHTEN Werten."*

Der Filter kostet Symbole (469 -> 323) und damit Praezision. Er lohnt sich
nur, wenn er MEHR Rauschen entfernt als Information. Das wird gemessen,
nicht geglaubt:

  TRENNSCHAERFE   Ein Effekt bekannter Groesse s wird in die oberen 20 %
                  einer Kennzahl gepflanzt. Gesucht ist das kleinste s,
                  bei dem das Band die Null ausschliesst.
                  Kleineres s = schaerferes Werkzeug.

  Verglichen:     UNGEFILTERT (469 Reihen) gegen GEFILTERT (323).
"""
from __future__ import annotations
import sys
import numpy as np
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import messe_eigenschaft_beitrag as B                       # noqa: E402

BRUCH, H, RB = 5.0, 5, 252
GRID = (0.000, 0.010, 0.020, 0.030, 0.050, 0.080)


def gleit(x, n):
    c = np.concatenate(([0.0], np.cumsum(x)))
    a = np.full(len(x), np.nan)
    a[n:] = (c[n:-1] - c[:-n - 1]) / n
    return a


def band(d, block=15, zieh=2000, saat=20260906):
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

    je_tag: dict = {}
    for sym, r in reihen.items():
        tage = [x[0] for x in r]
        c = np.array([x[1] for x in r]); h = np.array([x[2] for x in r])
        t = np.array([x[3] for x in r]); v = np.array([x[4] for x in r])
        br = B.spanne(h, t, c, B.SCHWANKUNG)
        vola = gleit(np.abs(np.diff(c, prepend=c[0]) / np.maximum(c, 1e-12)), 30)
        vh = c[1:] / np.maximum(c[:-1], 1e-12)
        bruch = (vh > BRUCH) | (vh < 1.0 / BRUCH)
        for i in range(RB, len(c) - H):
            if not np.isfinite(br[i]) or br[i] <= 0 or not np.isfinite(vola[i]):
                continue
            if bruch[i:i + H].any() or tage[i] < "2024-01-01":
                continue
            je_tag.setdefault(tage[i], []).append(
                (sym, float(vola[i]), float((c[i + H] - c[i]) / br[i])))

    def lauf(nur_gut, s, rng_saat=3):
        d = []
        for tag, w in je_tag.items():
            if nur_gut:
                w = [q for q in w if q[0] in gut]
            if len(w) < 20:
                continue
            k = np.array([q[1] for q in w]); y = np.array([q[2] for q in w])
            g = np.argsort(np.argsort(k)) >= int(0.8 * len(w))
            y = y + s * g                       # Effekt in die oberen 20 %
            d.append(float(y[g].mean() - y[~g].mean()))
        return np.array(d)

    print()
    print("=" * 86)
    print("TRENNSCHAERFE  -  kleinstes erkennbares s (Effekt in R)")
    print("=" * 86)
    print("  %-8s %-14s %8s %10s %24s  %s"
          % ("Welt", "Reihen/Tag", "s", "Wert", "Band", "erkannt"))
    erst = {}
    for lab, nur in (("ALLE", False), ("GEFILT", True)):
        n_tag = np.mean([len([q for q in w if not nur or q[0] in gut])
                         for w in je_tag.values()])
        for s in GRID:
            d = lauf(nur, s)
            lo, hi = band(d)
            ok = lo > 0
            if ok and lab not in erst:
                erst[lab] = s
            print("  %-8s %-14.1f %8.3f %10.4f   [%+.4f , %+.4f]  %s"
                  % (lab, n_tag, s, d.mean(), lo, hi, "JA" if ok else "nein"))
        print()
    print("  Kleinstes erkanntes s:  ALLE %s   ·   GEFILTERT %s"
          % (erst.get("ALLE", "> 0,080"), erst.get("GEFILT", "> 0,080")))
    print()
    print("  ⚠️ s = 0,000 MUSS 'nein' liefern - sonst misst das Verfahren")
    print("     sich selbst.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
