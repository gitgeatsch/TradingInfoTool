# -*- coding: utf-8 -*-
"""E2h-Probe: haengt das funding-Urteil an der STARTSTUNDE der Episoden?

**27.09.2026.** Gegenpruefung von E2h (2.666): im Pruefjahr 2022 stand
funding <= P5 bei Dq -0,040, mit dem Merkmal 1 h aelter (P2) bei +0,037 und
mit vertauschten Ausgaengen (P4) ebenfalls bei +0,037 - fuer ein
Tagesmerkmal, das sich nur um 00:00 UTC aendert, darf das nicht sein.

Ursache: `funding_vortag` wechselt um Mitternacht, also beginnt JEDE
Episode (1 je Asset in 24 h) um 00:00 UTC. Das Urteil misst dann nur den
Tagesbeginn. Hier beginnen die Episoden frueher oder spaeter (Stunde 0, 2,
... 22 des UTC-Tages als fruehester Beginn) - Schwellen, Bezug und Menge
bleiben wie in E2h.

NUR LESEND (`mode=ro`). Keine Gebuehren (Regel 2).
"""
from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import messe_e2_beitraege as E2                                   # noqa: E402
import messe_e2h_funding_2022 as W                                # noqa: E402
from messe_e3_vorwaerts import monat_von                          # noqa: E402


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:                                         # noqa: BLE001
        pass
    D = E2.lade()
    SYM, STD = D["SYM"], D["STD"]
    FU = D["F"]["funding_vortag"]
    A = D["Z"][24]["auf5"]; B = D["Z"][24]["ab5"]
    del D
    MON = monat_von(STD); n = len(SYM)
    pr = (STD >= W.PRUEF[0]) & (STD < W.PRUEF[1])
    su = (STD >= W.SUCHE[0]) & (STD < W.SUCHE[1])
    sw5 = np.nanpercentile(FU[su], 5); sw95 = np.nanpercentile(FU[su], 95)
    SM = SYM.astype(np.int64) * 1000 + (MON - MON.min())
    _u, si = np.unique(SM, return_inverse=True)
    o = np.lexsort((STD, SYM))

    def ep(m, ab):
        idx = o[m[o]]
        aus = np.zeros(n, bool); ls, lt = -1, -10 ** 9
        for i in idx:
            if STD[i] % 24 < ab:
                continue
            if SYM[i] != ls or STD[i] - lt >= 24:
                aus[i] = True; ls, lt = SYM[i], STD[i]
        return aus

    print("=" * 110)
    print("E2h-PROBE - Dq (q5, streng) je fruehester Startstunde der Episoden "
          "(UTC), Schwellen aus 2023-01 bis 2026-08")
    print("=" * 110)
    for zname, zeit in (("SUCHE 2023-26", su), ("PRUEF 2022", pr)):
        c = np.maximum(np.bincount(si, weights=zeit.astype(float)), 1)
        a0 = np.bincount(si, weights=A * zeit) / c
        b0 = np.bincount(si, weights=B * zeit) / c
        for name, m in (("F5 ", zeit & np.isfinite(FU) & (FU <= sw5)),
                        ("F95", zeit & np.isfinite(FU) & (FU >= sw95))):
            z = []
            for v in range(0, 24, 2):
                e = ep(m, v)
                if e.sum() < 50:
                    continue
                qa = A[e].mean() / (A[e].mean() + B[e].mean())
                q0 = a0[si[e]].mean() / (a0[si[e]].mean() + b0[si[e]].mean())
                z.append((v, int(e.sum()), qa - q0))
            if not z:
                print("  %-13s %s  zu wenige Episoden" % (zname, name))
                continue
            d = [x for _v, _k, x in z]
            print("  %-13s %s %s" % (zname, name, " ".join(
                "h%02d %+.3f" % (v, x) for v, _k, x in z)))
            print("  %-13s     Mittel %+.3f · Spanne %+.3f bis %+.3f · positiv "
                  "%d von %d · ~%d Episoden" % ("", np.mean(d), min(d), max(d),
                                                sum(x > 0 for x in d), len(d), z[0][1]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
