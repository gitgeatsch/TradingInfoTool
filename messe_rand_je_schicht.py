# -*- coding: utf-8 -*-
"""Hat ein GEFALLENES Asset Potential auf KURZER Zeitachse? (06.09.2026)

Nutzereinwand: *"das sind Fakten, aber diese wirken sich unterschiedlich
aus - auch ein gefallenes Asset hat Hebelpotential auf kurzer Zeitachse."*

⚠️ Und er trifft die eigene Vormessung: 2.113/2.114 bewerteten die
Rangschichten am MITTELWERT - genau der Massstab, den 2.112 als falsch
belegt hat. Hier derselbe Schnitt mit dem RANDMASS.

  Zielgroesse   Anteil der Asset-Tage mit mehr als +2 R bzw. +3 R
  Horizonte     1, 3, 5 Tage - die kurze Zeitachse
  Schnitt       Rangschicht x Rangtrend
"""
from __future__ import annotations
import sys
import numpy as np
if hasattr(sys.stdout, "reconfigure"):        # ⚠️ Suite ersetzt stdout
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import messe_eigenschaft_beitrag as B                       # noqa: E402

BRUCH, RB, ZURUECK = 5.0, 252, 180
HORIZONTE = (1, 3, 5)


def gleit(x, n):
    c = np.concatenate(([0.0], np.cumsum(x)))
    a = np.full(len(x), np.nan)
    a[n:] = (c[n:-1] - c[:-n - 1]) / n
    return a


def main() -> int:
    print("Lade Reihen ...", flush=True)
    reihen = B.lade()
    daten: dict = {}                    # tag -> [(sym, umsatz, {H: r})]
    for sym, z in reihen.items():
        tage = [x[0] for x in z]
        c = np.array([x[1] for x in z]); h = np.array([x[2] for x in z])
        t = np.array([x[3] for x in z]); v = np.array([x[4] for x in z])
        br = B.spanne(h, t, c, B.SCHWANKUNG)
        u = gleit(v * c, RB)
        vh = c[1:] / np.maximum(c[:-1], 1e-12)
        bruch = (vh > BRUCH) | (vh < 1.0 / BRUCH)
        mx = max(HORIZONTE)
        for i in range(RB, len(c) - mx):
            if not np.isfinite(br[i]) or br[i] <= 0 or not np.isfinite(u[i]):
                continue
            if u[i] <= 0 or bruch[i:i + mx].any():
                continue
            daten.setdefault(tage[i], []).append(
                (sym, float(u[i]),
                 {H: float((c[i + H] - c[i]) / br[i]) for H in HORIZONTE}))
    tage = sorted(t for t, w in daten.items() if len(w) >= 50)
    rang = {t: {q[0]: r for r, q in
                enumerate(sorted(daten[t], key=lambda x: -x[1]))}
            for t in tage}
    idx = {t: i for i, t in enumerate(tage)}
    print("  %d Tage" % len(tage))

    SCHICHT = (("Rang 1-20", 0, 20), ("Rang 21-100", 20, 100),
               ("ab Rang 101", 100, 10**6))
    TREND = (("aufgestiegen", -10**9, -20), ("stabil", -20, 20),
             ("GEFALLEN", 20, 10**9))

    for marke in (2.0, 3.0):
        print()
        print("=" * 92)
        print("ANTEIL DER ASSET-TAGE MIT MEHR ALS +%.0f R   (Mittel ueber die Tage)"
              % marke)
        print("=" * 92)
        print("  %-13s %-14s %8s %9s %9s %9s"
              % ("Schicht", "Rangtrend", "Tage", "H=1", "H=3", "H=5"))
        for sn, lo, hi in SCHICHT:
            for tn, tlo, thi in TREND:
                proTag = {H: [] for H in HORIZONTE}
                for t in tage:
                    i = idx[t]
                    if i < ZURUECK:
                        continue
                    alt = rang[tage[i - ZURUECK]]
                    w = sorted(daten[t], key=lambda x: -x[1])[lo:hi]
                    x = {H: [] for H in HORIZONTE}
                    for q in w:
                        if q[0] not in alt:
                            continue
                        d = rang[t][q[0]] - alt[q[0]]
                        if not (tlo <= d < thi):
                            continue
                        for H in HORIZONTE:
                            x[H].append(q[2][H])
                    if len(x[1]) >= 5:
                        for H in HORIZONTE:
                            proTag[H].append(
                                float((np.array(x[H]) > marke).mean()))
                n = len(proTag[1])
                if n < 100:
                    print("  %-13s %-14s %8d   zu wenige Tage" % (sn, tn, n))
                    continue
                print("  %-13s %-14s %8d %8.2f%% %8.2f%% %8.2f%%"
                      % (sn, tn, n,
                         *[100 * np.mean(proTag[H]) for H in HORIZONTE]))
            print()
    print("  ⚠️ Noch kein Befund - Randanteile je Tag, ohne Band. Ein")
    print("     Urteil braucht Blockbootstrap und Trennschaerfe.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
