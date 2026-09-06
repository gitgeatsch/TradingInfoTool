# -*- coding: utf-8 -*-
"""GLEICHARTIG: dieselbe Groesse (Bandkante), andere Zusammenfassung.

Der erste Versuch verglich max(Bandkante) gegen Mittel+2sd der
PUNKTSCHAETZER - zwei verschiedene Dinge. Hier wird nur die
Zusammenfassung DERSELBEN Groesse variiert:

    max      das heutige Verhalten - waechst mit der Ziehungszahl
    p90      ein Quantil - stabil, sobald genug Ziehungen da sind
    Mittel   die mittlere obere Bandkante

Nur turnover, weil nur dort das Urteil an der Schwelle haengt.
"""
from __future__ import annotations
import sys
import numpy as np
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import messe_bewertungskennzahl as MB                        # noqa: E402
import messe_eigenschaft_beitrag as B                        # noqa: E402
import messe_kandidaten_als_regel as K                       # noqa: E402
import messe_regel_wirksamkeit as W                          # noqa: E402
import messnorm as N                                         # noqa: E402


def _band(d, rng, block):
    import contextlib, io                                     # noqa: E401
    with contextlib.redirect_stdout(io.StringIO()):
        return MB.urteil_tage("x", d, rng, block)


def main() -> int:
    block = N._block(HORIZONT := 5)
    reihen = B.lade()
    tu = MB.reihe("data/onchain_historie.db", "splycur")
    g = K.baue(reihen, "turnover", tu, horizont=HORIZONT)
    je_tag = {t: z for t, z in g.items() if t >= "2024-01-01"}
    rng = np.random.default_rng(N.SAAT)
    d, _a, _g, _u = W.wirkung(je_tag, True)
    h = _band(d, rng, block)
    print("  turnover  Wirkung %+.5f  untere Bandkante %+.5f"
          % (h["mittel"], h["unten"]))

    print()
    print("=" * 88)
    print("DIESELBE GROESSE (obere Bandkante der Nullziehung), drei "
          "Zusammenfassungen")
    print("=" * 88)
    kanten = []
    print("  %9s %11s %11s %11s   %s"
          % ("Ziehungen", "max", "p90", "Mittel", "Urteil  max / p90 / Mittel"))
    for zieh in (5, 10, 20, 40, 80):
        while len(kanten) < zieh:
            m = np.random.default_rng(N.SAAT + len(kanten))
            n0, _b, _c, _e = W.wirkung(je_tag, True, mische=m)
            nb = _band(n0, rng, block)
            kanten.append(nb["oben"] if nb else 0.0)
        k = np.array(kanten[:zieh])
        mx, p90, mi = float(k.max()), float(np.percentile(k, 90)), float(k.mean())
        u = lambda s: "TRAEGT" if h["unten"] > max(0.0, s) else "nein"   # noqa: E731
        print("  %9d %11.5f %11.5f %11.5f   %-8s %-8s %s"
              % (zieh, mx, p90, mi, u(mx), u(p90), u(mi)))
    print()
    print("  ⚠️ Waechst nur `max`, waehrend p90 und Mittel stehenbleiben,")
    print("     ist die Schwelle heute vom Messaufwand abhaengig - und die")
    print("     Reparatur ist die Zusammenfassung, nicht die Groesse.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
