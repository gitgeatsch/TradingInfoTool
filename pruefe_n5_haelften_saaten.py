# -*- coding: utf-8 -*-
"""N5 - HAELFTEN UND SAATEN (06.09.2026)

Die Pruefung, die in diesem Projekt jeder tragende Beitrag bestanden hat:
traegt der Befund in BEIDEN Historienhaelften einzeln, und haelt er ueber
mehrere Saaten? Ein Effekt, der nur in einer Haelfte steckt, ist
episodisch - und in-sample kalibriert waere er wertlos.

Zusaetzlich der SUCHPREIS: fuenf Formen wurden geprueft (Methodik 2.49).
"""
from __future__ import annotations
import sys
import time
import numpy as np
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import messe_bewertungskennzahl as MB                        # noqa: E402
import messe_eigenschaft_beitrag as B                        # noqa: E402
import messe_kandidaten_als_regel as K                       # noqa: E402
import messnorm as N                                         # noqa: E402
import messnorm_rand as R                                    # noqa: E402
from messnorm import Lage                                    # noqa: E402

H, MARKE = 5, 2.0
ST = (0.02, 0.05, 0.10, 0.20, 0.40)


def _z(f, rein, ant):
    u = ("TRAEGT" if f.traegt else
         "kein Befund" if f.trennschaerfe_in_r is None else
         "nicht trennbar" if abs(f.wirkung) >= (f.trennschaerfe or 0)
         else "traegt nicht")
    return ("%+9.5f %+9.5f %7.2f%% %5d  [%+.5f..%+.5f] %s"
            % (f.wirkung, rein, 100 * ant, f.n_bloecke, f.unten, f.oben, u))


def main() -> int:
    t0 = time.time()
    L = Lage("spot", "einstieg")
    reihen = B.lade()
    tu = MB.reihe("data/onchain_historie.db", "splycur")
    vola = K.baue(reihen, "vola", None, horizont=H)
    turn = K.baue(reihen, "turnover", tu, horizont=H)
    zt = {t: {x["sym"]: x["kennzahl"] for x in z} for t, z in turn.items()}

    tage = sorted(set(vola) & set(zt))
    mitte = tage[len(tage) // 2]
    print("=" * 100)
    print("H1  BEIDE HISTORIENHAELFTEN — traegt ODER in jeder einzeln?")
    print("=" * 100)
    print("  Schnitt bei %s" % mitte)
    print("  %-24s %9s %9s %8s %5s  %s"
          % ("Abschnitt", "WIRKUNG", "Reinheit", "gesperrt", "Blk", "Urteil"))
    for lab, filt in (("ganze Historie", lambda t: True),
                      ("erste Haelfte", lambda t: t < mitte),
                      ("zweite Haelfte", lambda t: t >= mitte)):
        teil = {t: z for t, z in vola.items() if filt(t)}
        d, ant, ges, ueb = R.wirkung_rand(teil, True, marke=MARKE,
                                          zweit=zt, modus="oder")
        if not d:
            print("  %-24s   keine Tage" % lab); continue
        rng = np.random.default_rng(N.SAAT)
        f = R.pruefe_rand("oder", teil, lage=L, menge="frei", rng=rng,
                          marke=MARKE, horizont=H, staerken=ST,
                          zweit=zt, modus="oder")
        print("  %-24s %s" % (lab, _z(f, float(np.mean(ueb)) -
                                      float(np.mean(ges)),
                                      float(np.mean(ant)))), flush=True)

    print()
    print("=" * 100)
    print("H2  SAATSTABILITAET — drei Saaten")
    print("=" * 100)
    for saat in (20260906, 12345, 987654321):
        alt_n, alt_r = N.SAAT, R.SAAT
        N.SAAT = R.SAAT = saat
        try:
            rng = np.random.default_rng(saat)
            f = R.pruefe_rand("oder", vola, lage=L, menge="frei", rng=rng,
                              marke=MARKE, horizont=H, staerken=ST,
                              zweit=zt, modus="oder")
        finally:
            N.SAAT, R.SAAT = alt_n, alt_r
        print("  Saat %-11d %+9.5f [%+.5f..%+.5f] · Null [%+.5f..%+.5f] · "
              "Trennsch. %s · %s"
              % (saat, f.wirkung, f.unten, f.oben, f.null_unten, f.null_oben,
                 ("%.2f R" % f.trennschaerfe_in_r)
                 if f.trennschaerfe_in_r else "KEINE",
                 "TRAEGT" if f.traegt else "nein"), flush=True)

    print()
    print("  ⚠️ SUCHPREIS (2.49): fuenf Formen wurden geprueft. Bei fuenf")
    print("     Zellen und 5 %% Irrtumsschwelle ist ein Zufallstreffer in")
    print("     rund 23 %% der Faelle zu erwarten. Der Befund muss deshalb")
    print("     in BEIDEN Haelften und ueber die Saaten halten - sonst")
    print("     ist er im Suchpreis untergegangen.")
    print()
    print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
