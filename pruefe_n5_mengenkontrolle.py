# -*- coding: utf-8 -*-
"""N5 GEGENPRUEFUNG - ist ODERs Gewinn nur ein MENGENeffekt? (06.09.2026)

ODER sperrt 36,1 %, die Einzelgroessen 20,4 bzw. 21,3 %. Die anteil-
gewichtete Wirkung steigt mechanisch, wenn mehr gesperrt wird. Die
Reinheit spricht dagegen - sie ist mengenunabhaengig und steigt ebenfalls -
aber das ist ein Indiz, kein Beweis.

DER SAUBERE TEST: die Einzelgroessen auf DIESELBE Sperrmenge aufziehen.
Bei Grenze 0,639 sperrt eine Einzelgroesse rund 36 %.

  Bleibt ODER dann vorn  -> die KOMBINATION traegt, nicht die Menge
  Holen die Einzelnen auf -> es war die Menge, und ODER ist nur eine
                             strengere Einzelregel mit Zusatzaufwand
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


def main() -> int:
    t0 = time.time()
    L = Lage("spot", "einstieg")
    reihen = B.lade()
    tu = MB.reihe("data/onchain_historie.db", "splycur")
    vola = K.baue(reihen, "vola", None, horizont=H)
    turn = K.baue(reihen, "turnover", tu, horizont=H)
    z_turn = {t: {x["sym"]: x["kennzahl"] for x in z} for t, z in turn.items()}

    print("=" * 108)
    print("MENGENKONTROLLIERTER VERGLEICH — alle auf rund 36 % Sperrmenge")
    print("=" * 108)
    print("  %-30s %9s %9s %8s %5s  %s"
          % ("Form", "WIRKUNG", "Reinheit", "gesperrt", "Blk", "Urteil"))
    faelle = (
        ("ODER (Bezug)", vola, z_turn, "oder", None),
        ("vola allein, Grenze 0,639", vola, None, "einzeln", 0.639),
        ("turnover allein, Grenze 0,639", turn, None, "einzeln", 0.639),
        ("SUMME, Grenze 0,639", vola, z_turn, "summe", 0.639),
        # und zur Gegenrichtung: alle auf 20 %
        ("ODER, Grenze 0,894 (~20 %)", vola, z_turn, "oder", 0.894),
    )
    for lab, basis, zweit, modus, gr in faelle:
        d, anteil, gesperrt, uebrig = R.wirkung_rand(
            basis, True, marke=MARKE, zweit=zweit, modus=modus, grenze=gr)
        if not d:
            print("  %-30s   keine Tage" % lab); continue
        ant = float(np.mean(anteil))
        rein = float(np.mean(uebrig)) - float(np.mean(gesperrt))
        rng = np.random.default_rng(N.SAAT)
        f = R.pruefe_rand(lab, basis, lage=L, menge="frei", rng=rng,
                          marke=MARKE, horizont=H, staerken=ST,
                          zweit=zweit, modus=modus, grenze=gr)
        u = ("TRAEGT" if f.traegt else
             "kein Befund" if f.trennschaerfe_in_r is None else
             "nicht trennbar" if abs(f.wirkung) >= (f.trennschaerfe or 0)
             else "traegt nicht")
        print("  %-30s %+9.5f %+9.5f %7.2f%% %5d  [%+.5f..%+.5f] %s"
              % (lab, f.wirkung, rein, 100 * ant, f.n_bloecke,
                 f.unten, f.oben, u), flush=True)
    print()
    print("  ⚠️ Bleibt ODER bei GLEICHER Sperrmenge vorn, traegt die")
    print("     Kombination. Holen die Einzelgroessen auf, war es die Menge.")
    print()
    print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
