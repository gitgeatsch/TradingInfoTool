"""P90 GEGENPROBE Messplan L-2 (25.10.2026): zweiter Weg zu netto, gepaartem Vergleich und Stufe.

    python -X utf8 Basisinfos/Rechenkern_02_10/p90_gegenprobe.py

G1  netto je Handel ueber eine EINZELSCHLEIFE mit SQL-Abfrage je Einstieg (Schluss t und t+H aus der Datenbank) - gleich p90 (+-0,01 Pp)
G2  gepaart netto(168 h) - netto(24 h) ueber merge der beiden Einstiegsmengen - gleich p90 (+-0,01 Pp)
G3  Band netto je Handel mit doppelter Blocklaenge - gleiche Aussage, ob 0 im Band liegt
"""
import os
import re
import sqlite3
import sys
from datetime import timedelta

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
sys.path.insert(0, os.path.dirname(os.path.dirname(HIER)))
os.chdir(os.path.dirname(os.path.dirname(HIER)))
sys.stdout.reconfigure(encoding="utf-8")
import warnings  # noqa: E402

warnings.filterwarnings("ignore", category=RuntimeWarning)
import messnorm  # noqa: E402
import p90_l2_kern_halten as P  # noqa: E402


def main():
    txt = open(os.path.join(HIER, "p90_l2_kern_halten.txt"), encoding="utf-8").read()
    c = sqlite3.connect("file:data/_hist/stundenkurse.db?mode=ro", uri=True)
    ok = [True, True, True]
    rng = np.random.default_rng(901)
    R = {s: P.Reihe(s) for s in P.KERN}
    for weg in ("Referenz", "Lauf A (lang)"):
        e = pd.read_csv(P.WEGE[weg], sep=";")
        e = e[e.symbol.isin(P.KERN)]
        e = e[(P.B0 + pd.to_timedelta(e.stunde, unit="h")).dt.year >= 2024]
        abschnitt = txt.split(weg + ":")[1].split("\n\n")[0]
        for name, h in P.HS.items():
            v = []
            for s, st in zip(e.symbol, e.stunde):
                t = P.B0.to_pydatetime() + timedelta(hours=int(st))
                a = c.execute("SELECT close FROM stundenkurse WHERE symbol=? AND stunde=?", (s, t.strftime("%Y-%m-%d %H:%M"))).fetchone()
                b = c.execute("SELECT close FROM stundenkurse WHERE symbol=? AND stunde=?", (s, (t + timedelta(hours=h)).strftime("%Y-%m-%d %H:%M"))).fetchone()
                if a and b:
                    v.append(b[0] / a[0] - 1 - P.kosten(h))
            m = re.search(re.escape(name) + r"\s+netto je Handel ([+-][\d.]+) % \[([+-][\d.]+); ([+-][\d.]+)\]", abschnitt)
            p90 = float(m.group(1))
            g1 = abs(100 * np.mean(v) - p90) < 0.01
            ok[0] &= g1
            X = P.daten(e, R, name)
            T = P.Tage(X, "netto")
            blk = 2 * messnorm._block(max(1, h // 24))
            bn, _ = T.boot(blk, 1000, rng)
            lo, hi = np.percentile(bn, [2.5, 97.5])
            g3 = (lo <= 0 <= hi) == (float(m.group(2)) <= 0 <= float(m.group(3)))
            ok[2] &= g3
            print("%-14s %-6s G1 Einzelschleife netto %+.2f %% (p90 %+.2f, n %d) %s · G3 Band Block %d T [%+.2f; %+.2f] (p90 [%s; %s]) %s" % (
                weg, name, 100 * np.mean(v), p90, len(v), "ok" if g1 else "NICHT OK", blk, 100 * lo, 100 * hi, m.group(2), m.group(3),
                "gleiche Aussage" if g3 else "ANDERE AUSSAGE"))
        a24 = P.daten(e, R, "24 h").set_index(["tag", "symbol"]).netto
        a168 = P.daten(e, R, "168 h").set_index(["tag", "symbol"]).netto
        g = (a168 - a24).dropna().mean()
        m = re.search(r"168 h\s+netto.*?\n\s+Auskunft: gepaart gegen 24 h ([+-][\d.]+) Pp", abschnitt)
        g2 = abs(100 * g - float(m.group(1))) < 0.01
        ok[1] &= g2
        print("%-14s G2 gepaart 168 h - 24 h ueber merge %+.2f Pp (p90 %s) %s" % (weg, 100 * g, m.group(1), "ok" if g2 else "NICHT OK"))
    print("ERGEBNIS G1 %s · G2 %s · G3 %s -> %d von 3" % (*("ok" if o else "NICHT OK" for o in ok), sum(ok)))


if __name__ == "__main__":
    main()
