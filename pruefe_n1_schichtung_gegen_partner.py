# -*- coding: utf-8 -*-
"""N1 GEGENPRUEFUNG - kostet die SCHICHTUNG oder erklaert der PARTNER?

`vola in turnover` gab +0,00281 (gegen +0,00327 ohne Schichtung) und wurde
"nicht trennbar" - die Trennschaerfe fiel von 0,05 R auf 0,20 R.

Zwei Deutungen, und sie sind zu trennen:
  A  `turnover` erklaert `vola` mit          -> Redundanz
  B  die Schichtung an sich kostet Schaerfe  -> ein Messproblem

DIE KONTROLLE: dieselbe Schichtung, aber mit einem BEDEUTUNGSLOSEN
Partner - die Schichtwerte werden je Tag ueber die Symbole GEMISCHT. Die
Faecher sind dann genauso klein, tragen aber keine Information.

  Bleibt `vola` auch dort bei rund +0,0028 mit breitem Band, ist es die
  SCHICHTUNG. Steigt es zurueck auf +0,0033 mit engem Band, hat `turnover`
  tatsaechlich etwas erklaert.
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

H, ST = 5, (0.02, 0.05, 0.10, 0.20)


def _schicht(je_tag):
    return {t: {x["sym"]: x["kennzahl"] for x in z} for t, z in je_tag.items()}


def _gemischt(schicht, saat):
    """Dieselben Werte, aber den falschen Symbolen zugeordnet - je Tag."""
    rng = np.random.default_rng(saat)
    aus = {}
    for t, d in schicht.items():
        syms = list(d)
        werte = [d[s] for s in syms]
        rng.shuffle(werte)
        aus[t] = dict(zip(syms, werte))
    return aus


def _z(f):
    return ("%+9.5f [%+.5f .. %+.5f] · Null %+.5f · Trennsch. %s · %s"
            % (f.wirkung, f.unten, f.oben, f.nullpunkt,
               ("%.2f R" % f.trennschaerfe_in_r) if f.trennschaerfe_in_r
               else "KEINE",
               "TRAEGT" if f.traegt else f.urteil.split(" ")[0].lower()))


def main() -> int:
    L = Lage("spot", "einstieg")
    reihen = B.lade()
    fu = F.lade_funding()
    tu = MB.reihe("data/onchain_historie.db", "splycur")
    vola = K.baue(reihen, "vola", None, horizont=H)
    s_fu = _schicht(K.baue(reihen, "funding", fu, horizont=H))
    s_tu = _schicht(K.baue(reihen, "turnover", tu, horizont=H))

    print("=" * 100)
    print("KOSTET DIE SCHICHTUNG, ODER ERKLAERT DER PARTNER?  (vola, "
          "Rand > +2 R, H%d)" % H)
    print("=" * 100)
    faelle = [("ohne Schichtung          ", None),
              ("in funding (echt)        ", s_fu),
              ("in funding GEMISCHT      ", _gemischt(s_fu, 101)),
              ("in turnover (echt)       ", s_tu),
              ("in turnover GEMISCHT     ", _gemischt(s_tu, 202))]
    for lab, sch in faelle:
        rng = np.random.default_rng(N.SAAT)
        if sch is None:
            f = R.pruefe_rand("vola", vola, lage=L, menge="frei", rng=rng,
                              marke=2.0, horizont=H, staerken=ST)
        else:
            f = R.pruefe_geschichtet("vola", vola, sch, lage=L, menge="frei",
                                     rng=rng, marke=2.0, horizont=H,
                                     staerken=ST)
        print("  %s %s" % (lab, _z(f)), flush=True)
    print()
    print("  ⚠️ Liegt 'GEMISCHT' beim selben Wert und derselben Breite wie")
    print("     'echt', dann kostet die SCHICHTUNG - der Partner erklaert")
    print("     nichts. Das ist der Unterschied zwischen einem Messproblem")
    print("     und einem Befund ueber Redundanz.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
