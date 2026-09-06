# -*- coding: utf-8 -*-
"""KATEGORIEN und HORIZONT dimensionieren (06.09.2026).

Nutzerauftrag: *"der Zeithorizont muss auf die korrekte Ebene angepasst
werden - ich bin nicht der Experte, das musst du pruefen und dimensionieren.
Muessen wir die Assets kategorisieren fuer bessere Ergebnisse?"*

## Warum nicht die rohe Randquote je Horizont

Der Anteil > +2 R waechst mit H schon deshalb, weil mehr Zeit vergeht
(Zufallsweg: rund Wurzel-H). Ein Vergleich ueber Horizonte braucht ein Mass,
das das herauskuerzt. Genommen wird die ASYMMETRIE:

    Anteil > +x R   geteilt durch   Anteil < -x R

Beide Seiten skalieren mit H gleich - was uebrig bleibt, ist Potential.
Ein Wert von 1,00 heisst: kein Vorteil, nur Rauschen.
"""
from __future__ import annotations
import sys
import numpy as np
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import messe_eigenschaft_beitrag as B                       # noqa: E402

BRUCH, RB = 5.0, 252
HOR = (1, 2, 3, 5, 10, 20)
EIMER = (("Rang 1-5", 0, 5), ("Rang 6-20", 5, 20), ("Rang 21-50", 20, 50),
         ("Rang 51-100", 50, 100), ("Rang 101-200", 100, 200),
         ("ab Rang 201", 200, 10**6))


def gleit(x, n):
    c = np.concatenate(([0.0], np.cumsum(x)))
    a = np.full(len(x), np.nan)
    a[n:] = (c[n:-1] - c[:-n - 1]) / n
    return a


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
    tage = sorted(t for t, w in daten.items() if len(w) >= 50)
    # nur der vergleichbare Abschnitt - Methodik 2.111
    tage = [t for t in tage if t >= "2024-01-01"]
    print("  %d Tage ab 2024" % len(tage))

    sortiert = {t: sorted(daten[t], key=lambda x: -x[0]) for t in tage}

    for marke in (2.0, 3.0):
        print()
        print("=" * 94)
        print("ASYMMETRIE  Anteil > +%.0f R  /  Anteil < -%.0f R    (ab 2024)"
              % (marke, marke))
        print("=" * 94)
        print("  %-14s %7s" % ("Kategorie", "n/Tag")
              + "".join("%9s" % ("H=%d" % H) for H in HOR))
        for name, lo, hi in EIMER:
            oben = np.zeros(len(HOR)); unten = np.zeros(len(HOR)); anz = []
            for t in tage:
                w = sortiert[t][lo:hi]
                if len(w) < 3:
                    continue
                x = np.array([q[1] for q in w])          # (n, len(HOR))
                oben += (x > marke).mean(axis=0)
                unten += (x < -marke).mean(axis=0)
                anz.append(len(w))
            if not anz:
                print("  %-14s   -" % name); continue
            v = oben / np.maximum(unten, 1e-9)
            print("  %-14s %7.1f" % (name, np.mean(anz))
                  + "".join("%9.2f" % z for z in v))
        print("  %-14s %7s" % ("(1,00 = kein Vorteil)", ""))

    # Wo liegt der BRUCH? Randquote je Eimer bei H=5
    print()
    print("=" * 94)
    print("WO LIEGT DER BRUCH?   Anteil > +2 R ueber 5 Tage, feine Raenge")
    print("=" * 94)
    j = HOR.index(5)
    fein = [(0, 3), (3, 10), (10, 20), (20, 35), (35, 50), (50, 75),
            (75, 100), (100, 150), (150, 200), (200, 300), (300, 10**6)]
    for lo, hi in fein:
        q = []
        for t in tage:
            w = sortiert[t][lo:hi]
            if len(w) < 3:
                continue
            q.append(float((np.array([x[1][j] for x in w]) > 2.0).mean()))
        if q:
            n = 100 * np.mean(q)
            print("  Rang %4d-%-6s %6.2f%%  %s"
                  % (lo + 1, ("%d" % hi) if hi < 10**5 else "Ende", n,
                     "#" * int(round(n * 4))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
