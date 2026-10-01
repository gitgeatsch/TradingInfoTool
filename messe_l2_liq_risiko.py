"""L2 (Basisinfos/Voranalyse_L_Liquiditaet_01_10.md Abschnitt 3): traegt die LIQUIDITAET Risiko UEBER die ATR hinaus? - NUR AUSKUNFT.

Verbindet die Spur ``messe_k6_hebelstufe.py --simulation 24,ohne,0.02 --spur-regel0 <csv> --spur-alle`` (je Handel Hebelstufe,
Liquidation, Spot) mit ``data/_vergleich/l_liq_<menge>.csv`` (Liquiditaet und ATR je Einstieg aus ``messe_losfahren.py --liq``) und zeigt
fuer ein Jahr die Liquidationsrate und den Spot-Vorteil je Liquiditaetsstufe INNERHALB jeder Hebelstufe und jedes ATR-Drittels.

    python messe_l2_liq_risiko.py <spur.csv> <l_liq.csv> [jahr]
"""
import csv
import sys
from collections import defaultdict

import numpy as np

STUF = [(0.0, 2e6, "< 2 Mio"), (2e6, 10e6, "2-10 Mio"), (10e6, np.inf, ">= 10 Mio")]


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:                                         # noqa: BLE001
        pass
    sp, lq = sys.argv[1], sys.argv[2]
    jahr = sys.argv[3] if len(sys.argv) > 3 else "2024"
    liq = {}
    with open(lq, encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter=";"):
            liq[(r["symbol"], r["stunde"])] = (float(r["liq_usd"]), float(r["atr"]))
    z = []
    with open(sp, encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter=";"):
            if r["jahr"] == jahr and (r["symbol"], r["std"]) in liq:
                l_, a_ = liq[(r["symbol"], r["std"])]
                z.append((int(r["stufe"]), l_, a_, int(r["liq"]), float(r["spot"]) + 0.003))
    print("L2 · LIQUIDATION UND SPOT JE LIQUIDITAETSSTUFE innerhalb Hebelstufe und ATR-Drittel · Jahr %s · %d Handel mit Liquiditaet (Auskunft)" % (jahr, len(z)))
    if not z:
        print("SCHLUSS: vollstaendig")
        return 0
    at = np.array([x[2] for x in z]); k1, k2 = np.nanpercentile(at, [100 / 3.0, 200 / 3.0])
    g = defaultdict(list)
    for st, l_, a_, li, ro in z:
        d = "ATR niedrig" if a_ < k1 else ("ATR mittel" if a_ < k2 else "ATR hoch")
        s = [n for lo, hi, n in STUF if lo <= l_ < hi][0]
        g[("%dx" % st, d, s)].append((li, ro))
    for key in sorted(g):
        v = g[key]
        print("    %-3s · %-11s · %-9s · %5d Handel · Liquidationen %3d (%.2f %%) · Spot ohne Kosten %+.3f %%" % (
            *key, len(v), sum(x[0] for x in v), 100.0 * sum(x[0] for x in v) / len(v), 100.0 * float(np.mean([x[1] for x in v]))))
    print("SCHLUSS: vollstaendig")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
