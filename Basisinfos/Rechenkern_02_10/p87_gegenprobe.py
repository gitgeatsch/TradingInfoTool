"""P87 GEGENPROBE Messplan A Teil A2 (25.10.2026): zweiter Weg zu D und zur Urteilsstufe.

    python -X utf8 Basisinfos/Rechenkern_02_10/p87_gegenprobe.py

G1  D je Handel ueber pandas groupby (oben gegen uebrige) statt ueber Tagesaggregate - gleich p87 (+-0,001 Pp)
G2  D je Tag (Tagesklammer) ueber eine Tagestabelle (pivot je Tag und Gruppe, nur Tage mit beiden) - gleich p87 (+-0,001 Pp)
G3  Band mit 30-Tage-Bloecken (doppelte Blocklaenge) - gleiche Stufe (Rang >= 0,95 ja/nein) wie p87, je Weg und Gewichtung
"""
import os
import re
import sys

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
os.chdir(os.path.dirname(os.path.dirname(HIER)))
sys.stdout.reconfigure(encoding="utf-8")
import warnings  # noqa: E402

warnings.filterwarnings("ignore", category=RuntimeWarning)
import p87_a2_auswahl_einstieg as P  # noqa: E402


def main():
    txt = open(os.path.join(HIER, "p87_a2_auswahl_einstieg.txt"), encoding="utf-8").read()
    T1 = P.P85.wert_tabelle(1)
    K = P.P85.Kurse()
    ok = [True, True, True]
    rng = np.random.default_rng(871)
    for weg, pfad in list(P.WEGE.items())[:2]:
        x = P.P85.einstiege(pfad, T1, K)
        x = x[x.f.notna() & x["z_24 h"].notna()].reset_index(drop=True)
        x["oben"] = x.f == 5
        g = x.groupby("oben")["z_24 h"].mean()
        dh = g[True] - g[False]
        tab = x.pivot_table(index="tag", columns="oben", values="z_24 h", aggfunc="mean").dropna()
        dt = (tab[True] - tab[False]).mean()
        blk = re.search(re.escape(weg) + r".*?je Handel: D ([+-][\d.]+) Pp.*?Rang ([\d.]+).*?je Tag   : D ([+-][\d.]+) Pp.*?Rang ([\d.]+)", txt, flags=re.S)
        ph, rh, pt, rt = (float(blk.group(i)) for i in (1, 2, 3, 4))
        g1 = abs(100 * dh - ph) < 0.001
        g2 = abs(100 * dt - pt) < 0.001
        T = P.Tage(x, x["z_24 h"].to_numpy(), x.oben.to_numpy())
        P.BLOCK, alt = 30, P.BLOCK
        bh, bt = T.d(T.bloecke(rng=rng))
        P.BLOCK = alt
        r30 = (float(np.mean(bh > 0.0)), float(np.mean(bt > 0.0)))
        g3 = (r30[0] >= 0.95) == (rh >= 0.95) and (r30[1] >= 0.95) == (rt >= 0.95)
        ok = [ok[0] and g1, ok[1] and g2, ok[2] and g3]
        print("%-14s G1 je Handel groupby %+.3f (p87 %+.3f) %s · G2 Tagesklammer pivot %+.3f (p87 %+.3f, %d Tage) %s · "
              "G3 Rang 30-T-Bloecke %.3f/%.3f (p87 15 T %.3f/%.3f) %s" % (
                  weg, 100 * dh, ph, "ok" if g1 else "NICHT OK", 100 * dt, pt, len(tab), "ok" if g2 else "NICHT OK",
                  r30[0], r30[1], rh, rt, "gleiche Stufe" if g3 else "ANDERE STUFE"))
    print("ERGEBNIS G1 %s · G2 %s · G3 %s -> %d von 3" % (*("ok" if o else "NICHT OK" for o in ok), sum(ok)))


if __name__ == "__main__":
    main()
