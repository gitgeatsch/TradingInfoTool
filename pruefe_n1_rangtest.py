# -*- coding: utf-8 -*-
"""N1 - DER RANGTEST, verteilungsfrei (06.09.2026)

Sieben Mischungen erlauben bestenfalls p = 1/8 = 0,125 - nicht genug fuer
ein Urteil. Und der z-Wert setzt eine Normalverteilung voraus, die aus
sieben Ziehungen nicht erkennbar ist.

Hier 39 Mischungen je Partner. Der Test ist VERTEILUNGSFREI: unter der
Nullhypothese (der Partner traegt keine Information) ist der echte Wert
mit den gemischten austauschbar. Sein RANG unter allen 40 gibt den
p-Wert direkt.

    Rang 1 von 40  ->  p = 1/40 = 0,025   einseitig
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

H, MARKE, ZIEH = 5, 2.0, 39


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
    reihen = B.lade()
    fu = F.lade_funding()
    tu = MB.reihe("data/onchain_historie.db", "splycur")
    vola = K.baue(reihen, "vola", None, horizont=H)
    partner = {"funding": _schicht(K.baue(reihen, "funding", fu, horizont=H)),
               "turnover": _schicht(K.baue(reihen, "turnover", tu, horizont=H))}

    print("=" * 92)
    print("RANGTEST — verteilungsfrei, %d Mischungen je Partner" % ZIEH)
    print("=" * 92)
    for name, sch in partner.items():
        echt = float(np.mean(list(R.geschichtet(vola, sch,
                                                marke=MARKE).values())))
        w = []
        for i in range(ZIEH):
            v = R.geschichtet(vola, _gemischt(sch, 9000 + 17 * i), marke=MARKE)
            w.append(float(np.mean(list(v.values()))))
        w = np.array(w)
        alle = np.concatenate(([echt], w))
        rang = int((alle <= echt).sum())        # 1 = kleinster
        p = rang / len(alle)
        print("  %-9s ECHT %+.5f · gemischt Mittel %+.5f (Spanne %+.5f .. "
              "%+.5f)" % (name.upper(), echt, w.mean(), w.min(), w.max()))
        print("            Rang %d von %d  ->  p = %.3f  einseitig   %s"
              % (rang, len(alle), p,
                 "⚠️ der Partner erklaert etwas" if p <= 0.05
                 else "kein Beleg fuer Erklaerung"))
        print("            Anteil, den der Partner erklaert: %.0f %%"
              % (100 * (w.mean() - echt) / w.mean() if w.mean() else 0))
        print()
    print("  ⚠️ p ist hier die Austauschbarkeit: wie oft erreicht eine")
    print("     BEDEUTUNGSLOSE Schichtung einen mindestens so niedrigen")
    print("     Wert wie die echte?")
    return 0


if __name__ == "__main__":
    sys.exit(main())
