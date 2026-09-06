# -*- coding: utf-8 -*-
"""S3 GEGENGEPRUEFT: dieselbe Frage MIT Tagesklammer (06.09.2026).

S3 gab gepoolt einen Abstand von 0,102 R zwischen "in Top 100 geblieben"
und "neu in Top 100". Gepoolt erfindet auf einem Nulleffekt Punkte
(Methodik 2.86). Hier dieselbe Konstruktion, aber je Kalendertag EIN Wert -
und der Vergleich GEPAART am selben Tag.
"""
from __future__ import annotations
import sys
import numpy as np
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import messe_eigenschaft_beitrag as B                       # noqa: E402

BRUCH, H, RB, ZURUECK, GRENZE = 5.0, 5, 252, 60, 100


def gleit(x, n):
    c = np.concatenate(([0.0], np.cumsum(x)))
    a = np.full(len(x), np.nan)
    a[n:] = (c[n:-1] - c[:-n - 1]) / n
    return a


def block_band(d, block=15, zieh=2000, saat=20260906):
    """Blockbootstrap ueber die Tagesreihe der gepaarten Differenz."""
    rng = np.random.default_rng(saat)
    n = len(d)
    nb = max(1, n // block)
    start = np.arange(n - block + 1)
    aus = np.empty(zieh)
    for k in range(zieh):
        s = rng.choice(start, nb)
        aus[k] = np.concatenate([d[i:i + block] for i in s]).mean()
    return float(np.percentile(aus, 2.5)), float(np.percentile(aus, 97.5))


def main() -> int:
    print("Lade Reihen ...", flush=True)
    reihen = B.lade()
    je_tag: dict = {}
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
            je_tag.setdefault(tage[i], []).append(
                (sym, float(u[i]), float((c[i + H] - c[i]) / br[i])))
    tage = sorted(t for t, w in je_tag.items() if len(w) >= 50)
    rang = {t: {q[0]: r for r, q in
                enumerate(sorted(je_tag[t], key=lambda x: -x[1]))}
            for t in tage}
    idx = {t: i for i, t in enumerate(tage)}

    NAMEN = ["neu in Top100", "in Top100 geblieben",
             "aus Top100 gefallen", "ausserhalb geblieben"]
    proTag = {k: [] for k in NAMEN}
    gepaart = []                       # geblieben minus neu, SELBER Tag
    for t in tage:
        i = idx[t]
        if i < ZURUECK:
            continue
        alt = rang[tage[i - ZURUECK]]
        e = {k: [] for k in NAMEN}
        for q in je_tag[t]:
            if q[0] not in alt:
                continue
            a, n = alt[q[0]] < GRENZE, rang[t][q[0]] < GRENZE
            k = ("neu in Top100" if n and not a else
                 "in Top100 geblieben" if n and a else
                 "aus Top100 gefallen" if a else "ausserhalb geblieben")
            e[k].append(q[2])
        for k, v in e.items():
            if len(v) >= 5:
                proTag[k].append(float(np.mean(v)))
        if len(e["neu in Top100"]) >= 5 and len(e["in Top100 geblieben"]) >= 5:
            gepaart.append(float(np.mean(e["in Top100 geblieben"]))
                           - float(np.mean(e["neu in Top100"])))

    print()
    print("=" * 84)
    print("S3 MIT TAGESKLAMMER   (je Kalendertag ein Wert)")
    print("=" * 84)
    print("  %-22s %7s %10s %10s %8s"
          % ("Gruppe", "Tage", "Mittel R", "Streufeh.", "t"))
    for k in NAMEN:
        v = np.array(proTag[k], float)
        se = v.std(ddof=1) / np.sqrt(len(v))
        print("  %-22s %7d %10.4f %10.4f %8.2f"
              % (k, len(v), v.mean(), se, v.mean() / se if se else 0))

    d = np.array(gepaart, float)
    lo, hi = block_band(d)
    print()
    print("  GEPAART am selben Tag: geblieben minus neu")
    print("    %d Tage · Mittel %+.4f R" % (len(d), d.mean()))
    print("    Blockbootstrap (Block 15, 2000 Ziehungen): [%+.4f , %+.4f]"
          % (lo, hi))
    print("    -> %s" % ("TRAEGT (Band schliesst Null aus)"
                         if lo > 0 or hi < 0 else
                         "TRAEGT NICHT - das Band enthaelt die Null"))
    print()
    print("  Vergleich: GEPOOLT gab dieselbe Frage +0,1020 R.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
