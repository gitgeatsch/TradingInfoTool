# -*- coding: utf-8 -*-
"""Ist die Spiegelung TREU? — vor dem Gebrauch (06.09.2026)

Stehende Vorgabe: *ein Test muss die ECHTE Funktion rufen, nie eine
Kopie.* `messnorm_rand.geschichtet` IST eine Kopie von
`messe_kandidaten_als_regel.geschichtet` - also ist zu beweisen, dass sie
mit `marke=None` BITGENAU dasselbe liefert. Sonst misst N1 eine
Nachbildung.
"""
from __future__ import annotations
import sys
import numpy as np
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import messe_bewertungskennzahl as MB                        # noqa: E402
import messe_eigenschaft_beitrag as B                        # noqa: E402
import messe_funding_niveau as F                             # noqa: E402
import messe_kandidaten_als_regel as K                       # noqa: E402
import messnorm_rand as R                                    # noqa: E402


def main() -> int:
    reihen = B.lade()
    fu = F.lade_funding()
    vola = K.baue(reihen, "vola", None, horizont=5)
    fund = K.baue(reihen, "funding", fu, horizont=5)
    schicht = {t: {x["sym"]: x["kennzahl"] for x in z} for t, z in fund.items()}

    print("=" * 84)
    print("T1  BITGENAUE UEBEREINSTIMMUNG mit dem Original (marke=None)")
    print("=" * 84)
    a = K.geschichtet(vola, schicht)
    b = R.geschichtet(vola, schicht, marke=None)
    gleich = (set(a) == set(b)
              and all(a[t] == b[t] for t in a))          # exakt, nicht nah
    print("  Original %d Tage · Spiegelung %d Tage" % (len(a), len(b)))
    if a:
        d = max(abs(a[t] - b[t]) for t in a) if set(a) == set(b) else float("nan")
        print("  groesste Abweichung: %.3e" % d)
    print("  %s" % ("✔ BITGENAU IDENTISCH" if gleich else "⚠️ WEICHT AB"))

    print()
    print("=" * 84)
    print("T2  auch mit MISCHUNG (derselbe Zufall, dieselbe Folge)")
    print("=" * 84)
    a2 = K.geschichtet(vola, schicht, mische=np.random.default_rng(7))
    b2 = R.geschichtet(vola, schicht, marke=None,
                       mische=np.random.default_rng(7))
    g2 = set(a2) == set(b2) and all(a2[t] == b2[t] for t in a2)
    print("  %s" % ("✔ BITGENAU IDENTISCH" if g2 else "⚠️ WEICHT AB"))

    print()
    print("=" * 84)
    print("T3  DIE PFLANZUNG WIRKT - und in die richtige Richtung")
    print("=" * 84)
    roh = float(np.mean(list(R.geschichtet(vola, schicht, marke=None).values())))
    for s in (0.0, 0.05, 0.20):
        v = R.geschichtet(vola, schicht, marke=None, pflanze=s)
        print("  Median-Massstab · gepflanzt %.2f R -> %+.5f" 
              % (s, float(np.mean(list(v.values())))))
    for s in (0.0, 0.05, 0.20):
        v = R.geschichtet(vola, schicht, marke=2.0, pflanze=s)
        print("  Rand-Massstab   · gepflanzt %.2f R -> %+.5f"
              % (s, float(np.mean(list(v.values())))))
    print()
    print("  ⚠️ Steigt der Wert NICHT mit der Pflanzung, ist die")
    print("     Positivkontrolle wirkungslos und jeder Nullbefund wertlos.")

    print()
    print("=" * 84)
    print("T4  DIE FAECHER HALTEN DIE SCHICHT WIRKLICH FEST")
    print("=" * 84)
    # Kontrolle: die Schichtgroesse der Gesperrten und der Behaltenen muss
    # innerhalb der Faecher dieselbe Verteilung haben
    import collections
    diff = []
    for tag, z in list(vola.items())[:400]:
        s = schicht.get(tag)
        if not s:
            continue
        w = np.array([x["kennzahl"] for x in z], float)
        sw = np.array([s.get(x["sym"], np.nan) for x in z], float)
        gut = np.isfinite(sw)
        if gut.sum() < K.MIND_JE_TAG:
            continue
        w, sw = w[gut], sw[gut]
        fach = np.minimum((K.W.rang(sw) * 5).astype(int), 4)
        frei = np.ones(len(w), bool); gen = np.zeros(len(w), bool)
        for f in range(5):
            m = fach == f
            if m.sum() < 4:
                continue
            lok = K.W.rang(w[m]) < K.W.GRENZE
            if lok.sum() < 3 or (~lok).sum() < 1:
                continue
            idx = np.flatnonzero(m); frei[idx] = lok; gen[idx] = True
        if gen.sum() < K.MIND_JE_TAG:
            continue
        r_s = K.W.rang(sw)
        diff.append(float(np.mean(r_s[gen & frei]) - np.mean(r_s[gen & ~frei])))
    print("  mittlerer Schicht-Rang: behalten minus gesperrt = %+.4f"
          % np.mean(diff))
    print("  (nahe NULL heisst: die Schicht ist tatsaechlich festgehalten -")
    print("   die Regel sortiert nicht heimlich nach der zweiten Groesse)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
