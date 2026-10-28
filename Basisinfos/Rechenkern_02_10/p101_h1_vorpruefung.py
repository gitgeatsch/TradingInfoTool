"""P101 Vorpruefung zu Messplan H-1 Fassung 2 (28.10.2026). Nur lesend, KEIN Ergebnis je Zustand.

    python -X utf8 Basisinfos/Rechenkern_02_10/p101_h1_vorpruefung.py [--neu]

1. R-R11: H24/H72/H120 brutto 2025-26 je Menge muss p62 (18.10.) reproduzieren (gleiche Einstiege mit 168 h).
2. Fallzahlen je Zustand (a, b, c, extrem), Jahr und Menge; Klammertage (Tage mit beiden Zustaenden) und Bloecke a 15 T.
3. Abdeckung: Einstiege ohne Tageszustand, ohne ATR (Fuehrung F), ohne Extrem-Merkmal.
4. Seiteneffekt: Produktionsdatei vorher/nachher gleich.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p101_h1_basis as B  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass

P62 = {"bestand": (10725, 0.545, -0.373, -0.849), "unverzerrt_1": (11151, 0.304, -0.302, -0.794),
       "unverzerrt_2": (10447, 0.312, -0.342, -1.018), "unverzerrt_3": (10767, 0.310, -0.386, -0.828)}


def main():
    vorher = B.fingerabdruck()
    neu = "--neu" in sys.argv
    print("P101 VORPRUEFUNG H-1 (Fassung 2) · nur Zaehlungen und R-R11, kein Ergebnis je Zustand\n")
    fehl = 0
    for menge in B.MENGEN:
        D = B.tabelle(menge, neu=neu)
        U = D[D.jahr >= 2025]
        n0, h24, h72, h120 = P62[menge]
        ist = (len(D), 100 * U.r24.mean(), 100 * U.r72.mean(), 100 * U.r120.mean())
        ok = ist[0] == n0 and all(abs(a - b) < 0.0015 for a, b in zip(ist[1:], (h24, h72, h120)))
        fehl += not ok
        print("=" * 110)
        print("%s: %d Einstiege mit 168 h (p62 %d) · brutto 2025-26 H24 %+.3f %% (p62 %+.3f) · H72 %+.3f (%+.3f) · H120 %+.3f (%+.3f)"
              " -> R-R11 %s" % (menge, ist[0], n0, ist[1], h24, ist[2], h72, ist[3], h120, "✔" if ok else "✖ ABWEICHUNG"))
        print("   Abdeckung: ohne a %d · ohne b %d · ohne c %d · ohne ATR (F) %d · ohne Extrem-Merkmal %d" % (
            D.a.isna().sum(), D.b.isna().sum(), D.c.isna().sum(), D.rF.isna().sum(), D.extrem.isna().sum()))
        print("   %-7s %-5s %9s %9s %11s %12s %9s" % ("Zustand", "Jahr", "Einstiege", "Anteil=1", "Klammertage", "Einst. dort", "Bloecke"))
        for k in ("a", "b", "c", "extrem"):
            for j, g in [(str(j), D[D.jahr == j]) for j in (2024, 2025, 2026)] + [("25-26", U)]:
                g = g[g[k].notna()]
                z = g[k].to_numpy(float)
                tg, _dt = B.je_tag(g.tag.to_numpy(), z, np.zeros(len(g)))
                nb = len(np.unique((tg - tg.min()) // B.N._block(5))) if len(tg) else 0
                print("   %-7s %-5s %9d %8.1f%% %11d %12d %9d%s" % (
                    k, j, len(g), 100 * z.mean() if len(z) else np.nan, len(tg), int(g.tag.isin(tg).sum()), nb,
                    "   ⚠ unter 20 Bloecken" if nb < 20 else ""))
    nachher = B.fingerabdruck()
    print("\nSeiteneffekt Produktionsdatei: %s" % ("✔ unveraendert" if vorher == nachher else "✖ VERAENDERT %s -> %s" % (vorher, nachher)))
    print("R-R11 gesamt: %s" % ("✔ alle vier Mengen reproduziert" if not fehl else "✖ %d Mengen weichen ab - NICHT weiter" % fehl))
    return 1 if (fehl or vorher != nachher) else 0


if __name__ == "__main__":
    sys.exit(main())
