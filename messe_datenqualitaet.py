# -*- coding: utf-8 -*-
"""DATENMUELL im Messuniversum - wie viel und woran erkennbar? (06.09.2026)

Nutzervorgabe: *"das Rauschen und Fehler vermeiden - den Datenmuell von
guten Daten trennen. Wir kappen und kalibrieren auf ECHTEN Werten."*

⚠️ ABGRENZUNG: das Kriterium ist DATENQUALITAET, kein Werturteil ueber das
Asset. "Tote Tage", "kein Umsatz", "Rundungsrauschen" sind messbare
Eigenschaften der REIHE. "Shitcoin" waere ein Urteil ueber den WERT und
verstiesse gegen CLAUDE.md Regel 3.
"""
from __future__ import annotations
import sys
import numpy as np
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import messe_eigenschaft_beitrag as B                       # noqa: E402


def main() -> int:
    print("Lade Reihen ...", flush=True)
    reihen = B.lade()
    z = []
    for sym, r in reihen.items():
        c = np.array([x[1] for x in r], float)
        h = np.array([x[2] for x in r], float)
        t = np.array([x[3] for x in r], float)
        v = np.array([x[4] for x in r], float)
        # nur der vergleichbare Abschnitt
        tage = [x[0] for x in r]
        m = np.array([x >= "2024-01-01" for x in tage])
        if m.sum() < 120:
            continue
        c2, v2, h2, t2 = c[m], v[m], h[m], t[m]
        tot = float(np.mean(np.diff(c2) == 0.0))          # Kurs unveraendert
        kein = float(np.mean(v2 <= 0))                    # kein Umsatz
        flach = float(np.mean((h2 - t2) <= 0))            # keine Tagesspanne
        u = float(np.median(v2 * c2))
        z.append((sym, tot, kein, flach, u, float(np.median(c2)), int(m.sum())))

    print("  %d Reihen mit >= 120 Tagen ab 2024" % len(z))
    tot = np.array([x[1] for x in z]); kein = np.array([x[2] for x in z])
    flach = np.array([x[3] for x in z]); u = np.array([x[4] for x in z])
    pr = np.array([x[5] for x in z])

    print()
    print("=" * 84)
    print("WIE VIEL MUELL? Verteilung ueber die Reihen")
    print("=" * 84)
    for lab, a in (("Anteil TOTER Tage (Kurs unveraendert)", tot),
                   ("Anteil Tage OHNE Umsatz", kein),
                   ("Anteil Tage ohne Tagesspanne", flach)):
        print("  %-38s p50 %6.2f%%  p90 %6.2f%%  max %6.2f%%"
              % (lab, 100 * np.median(a), 100 * np.percentile(a, 90),
                 100 * a.max()))
    print()
    print("  Taeglicher Umsatz (Median je Reihe):")
    for g, lab in ((1e8, "> 100 Mio"), (1e7, "> 10 Mio"), (1e6, "> 1 Mio"),
                   (1e5, "> 100 Tsd"), (0, "alle")):
        print("    %-12s %4d Reihen" % (lab, int((u > g).sum())))
    print()
    print("  Kursniveau (Median je Reihe):")
    for g, lab in ((1.0, "> 1 USD"), (0.01, "> 1 Cent"),
                   (0.0001, "> 0,01 Cent"), (0, "alle")):
        print("    %-14s %4d Reihen" % (lab, int((pr > g).sum())))

    print()
    print("=" * 84)
    print("EIN VORSCHLAG FUER 'ECHTE WERTE' - drei Datenkriterien")
    print("=" * 84)
    for lab, maske in (
            ("A  tote Tage < 5 %", tot < 0.05),
            ("B  Umsatz-Median > 1 Mio USD", u > 1e6),
            ("C  Kurs > 1 Cent (Rundungsrauschen)", pr > 0.01),
            ("A und B", (tot < 0.05) & (u > 1e6)),
            ("A und B und C", (tot < 0.05) & (u > 1e6) & (pr > 0.01))):
        print("  %-38s %4d von %d Reihen  (%5.1f %%)"
              % (lab, int(maske.sum()), len(z), 100 * maske.mean()))

    behalten = [x[0] for x, m in zip(z, (tot < 0.05) & (u > 1e6) & (pr > 0.01))
                if m]
    weg = [x[0] for x, m in zip(z, ~((tot < 0.05) & (u > 1e6) & (pr > 0.01)))
           if m]
    print()
    print("  BEHALTEN (Auszug): %s" % ", ".join(sorted(behalten)[:22]))
    print("  ENTFERNT (Auszug): %s" % ", ".join(sorted(weg)[:22]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
