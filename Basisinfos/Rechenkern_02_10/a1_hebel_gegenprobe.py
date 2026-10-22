"""Gegenprobe A1 HEBEL-RECHNUNG (zweite Wege) - Bestandsaufnahme 22.10. (nicht verwechseln mit a1_gegenprobe.py, Schritt7 §23.14).

    python Basisinfos/Rechenkern_02_10/a1_hebel_gegenprobe.py

G1 24-h-Ertrag fuer 300 zufaellige Einstiege direkt per SQL aus den Stundenkursen (ohne p64.reihe) = a1_einstiege_bestand.csv
G2 N24 fuer 300 zufaellige Einstiege durch Abzaehlen (ohne searchsorted) = a1
G3 Tagesblock-Breite: geschlossene cluster-robuste Formel (Summe je Tag) gegen den Bootstrap von a1 - aehnlich (+-20 %)?
G4 Mittel ohne Sperre bestand 2025-26 = Referenz +0,55 % (R-R11, zweiter Weg ueber die Datei)
"""
import os
import re
import sqlite3
import subprocess
import sys

import numpy as np
import pandas as pd

os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass
ok = []


def pruefe(name, bed, info=""):
    ok.append(bool(bed))
    print("  %s  %s%s" % ("OK  " if bed else "FEHL", name, ("  (%s)" % info) if info else ""))


print("A1 GEGENPROBE\n")
out = subprocess.run([sys.executable, "-X", "utf8", os.path.join("Basisinfos", "Rechenkern_02_10", "a1_hebel_rechnung.py")],
                     capture_output=True, text=True, encoding="utf-8").stdout
E = pd.read_csv(os.path.join("data", "_vergleich", "a1_einstiege_bestand.csv"), sep=";")
cons = [sqlite3.connect("file:data/%s?mode=ro" % d, uri=True) for d in ("stundenkurse.db", "stundenkurse_alle.db", "eingestellt_historie.db")
        if os.path.exists(os.path.join("data", d))]
B0 = pd.Timestamp("2020-01-01")


def schluss(sym, st):
    ts = (B0 + pd.Timedelta(hours=int(st))).strftime("%Y-%m-%d %H:%M")
    for c in cons:
        r = c.execute("SELECT close FROM stundenkurse WHERE symbol=? AND stunde=?", (sym, ts)).fetchone()
        if r:
            return r[0]
    return None


rng = np.random.default_rng(4)
S = E.iloc[rng.choice(len(E), 300, replace=False)]
gleich = 0
for r in S.itertuples():
    a, b = schluss(r.symbol, r.stunde), schluss(r.symbol, r.stunde + 24)
    gleich += int(a is not None and b is not None and abs((b / a - 1) - r.r24) < 1e-9)
pruefe("G1 24-h-Ertrag direkt per SQL", gleich == 300, "%d von 300 gleich" % gleich)

st = E.stunde.to_numpy()
g2 = sum(int(((st >= r.stunde - 24) & (st < r.stunde)).sum() == r.n24) for r in S.itertuples())
pruefe("G2 N24 durch Abzaehlen", g2 == 300, "%d von 300 gleich" % g2)

g = E.groupby("tag").r24.agg(["sum", "count"])
m = g["sum"].sum() / g["count"].sum()
var = ((g["sum"] - m * g["count"]) ** 2).sum() / g["count"].sum() ** 2
hb_formel = 1.96 * np.sqrt(var)
mo = re.search(r"bestand: .*?\n  24 h Mittel ([-+0-9.]+) % \[Tagesblock ([-+0-9.]+); ([-+0-9.]+)\]", out, re.S)
hb_boot = (float(mo.group(3)) - float(mo.group(2))) / 2 / 100 if mo else float("nan")
pruefe("G3 Tagesblock-Breite Formel gegen Bootstrap (+-20 %)", mo and abs(hb_formel / hb_boot - 1) < 0.2,
       "Formel +-%.2f Pp · Bootstrap +-%.2f Pp" % (100 * hb_formel, 100 * hb_boot))
ref = E[E.jahr.isin([2025, 2026])].r24.mean()
pruefe("G4 R-R11 Referenz +0,55 %", abs(100 * ref - 0.55) < 0.015, "%+.3f %%" % (100 * ref))
print("\n%d Pruefungen, %s" % (len(ok), "ALLE BESTANDEN" if all(ok) else "%d FEHLGESCHLAGEN" % ok.count(False)))
