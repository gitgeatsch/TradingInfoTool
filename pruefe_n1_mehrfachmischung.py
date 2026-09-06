# -*- coding: utf-8 -*-
"""N1 - DIE KONTROLLE DER KONTROLLE (06.09.2026)

Der erste Lauf verglich `vola in turnover` gegen EINE gemischte Fassung
und schloss daraus, `turnover` erklaere rund ein Viertel. ⚠️ Eine Ziehung
ist kein Nullpunkt (Methodik 2.104) - genau der Fehler, den das Projekt
schon einmal gemacht hat.

Hier mehrere Mischungen je Partner. Gesucht ist, ob der ECHTE Wert
AUSSERHALB der Streuung der gemischten liegt.
"""
from __future__ import annotations
import sys
import numpy as np
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import messe_bewertungskennzahl as MB                        # noqa: E402
import messe_eigenschaft_beitrag as B                        # noqa: E402
import messe_funding_niveau as F                             # noqa: E402
import messe_kandidaten_als_regel as K                       # noqa: E402
import messnorm as N                                         # noqa: E402
import messnorm_rand as R                                    # noqa: E402
from messnorm import Lage                                    # noqa: E402

H, MARKE = 5, 2.0


def _schicht(je_tag):
    return {t: {x["sym"]: x["kennzahl"] for x in z} for t, z in je_tag.items()}


def _gemischt(schicht, saat):
    rng = np.random.default_rng(saat)
    aus = {}
    for t, d in schicht.items():
        syms = list(d)
        werte = [d[s] for s in syms]
        rng.shuffle(werte)
        aus[t] = dict(zip(syms, werte))
    return aus


def main() -> int:
    L = Lage("spot", "einstieg")
    reihen = B.lade()
    fu = F.lade_funding()
    tu = MB.reihe("data/onchain_historie.db", "splycur")
    vola = K.baue(reihen, "vola", None, horizont=H)
    partner = {"funding": _schicht(K.baue(reihen, "funding", fu, horizont=H)),
               "turnover": _schicht(K.baue(reihen, "turnover", tu, horizont=H))}
    rng0 = np.random.default_rng(N.SAAT)
    roh = R.pruefe_rand("vola", vola, lage=L, menge="frei", rng=rng0,
                        marke=MARKE, horizont=H, staerken=(0.05,))
    print("=" * 92)
    print("MEHRERE MISCHUNGEN JE PARTNER  (vola, Rand > +%g R, H%d)"
          % (MARKE, H))
    print("=" * 92)
    print("  ohne Schichtung: %+.5f" % roh.wirkung)
    print()
    # nur die WIRKUNG rechnen - kein Band je Mischung noetig, die
    # Streuung UEBER die Mischungen ist der Massstab
    for name, sch in partner.items():
        echt = float(np.mean(list(R.geschichtet(
            vola, sch, marke=MARKE).values())))
        werte = []
        for saat in (101, 202, 303, 404, 505, 606, 707):
            v = R.geschichtet(vola, _gemischt(sch, saat), marke=MARKE)
            werte.append(float(np.mean(list(v.values()))))
        w = np.array(werte)
        mi, sd = w.mean(), w.std(ddof=1)
        z = (echt - mi) / sd if sd > 1e-12 else float("nan")
        print("  %-9s  ECHT %+.5f" % (name.upper(), echt))
        print("             GEMISCHT (7 Ziehungen)  Mittel %+.5f · "
              "Streuung %.5f" % (mi, sd))
        print("             Spanne [%+.5f .. %+.5f]" % (w.min(), w.max()))
        print("             Abstand des echten Werts: %+.2f Streuungen  %s"
              % (z, "⚠️ AUSSERHALB - der Partner erklaert etwas"
                 if abs(z) > 2 else "innerhalb - der Partner erklaert nichts"))
        print()
    print("  ⚠️ Nur wenn der ECHTE Wert deutlich ausserhalb der Streuung")
    print("     der GEMISCHTEN liegt, hat der Partner etwas erklaert.")
    print("     Eine einzelne Mischung kann jeden Eindruck erzeugen.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
