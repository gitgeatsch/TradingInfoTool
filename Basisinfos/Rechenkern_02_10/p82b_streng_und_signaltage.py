"""P82b (24.10.2026, Voranalyse_REGEL0_Robustheit_24_10.md §3.3/§3.4): Einstiege der 23 Symbole mit streng gleicher Kursreihe und die
Aufteilung der Differenz Referenz/lang nach Signalen je Tag. Nur lesend.

    python -X utf8 Basisinfos/Rechenkern_02_10/p82b_streng_und_signaltage.py
"""
import os
import sqlite3
import sys

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
os.chdir(os.path.dirname(os.path.dirname(HIER)))
sys.stdout.reconfigure(encoding="utf-8")
import p79_f1_fg_gier as P  # noqa: E402

ca = sqlite3.connect("file:data/stundenkurse.db?mode=ro", uri=True)
cb = sqlite3.connect("file:data/_hist/stundenkurse.db?mode=ro", uri=True)
e = dict(ca.execute("SELECT symbol, MIN(stunde) FROM stundenkurse GROUP BY symbol").fetchall())
l_ = dict(cb.execute("SELECT symbol, MIN(stunde) FROM stundenkurse GROUP BY symbol").fetchall())
streng = {s for s in e if l_[s] == e[s]}
a = pd.read_csv("data/_hist/einstiege_A.csv", sep=";")
b = pd.read_csv("data/_vergleich/kern48jbz_einstiege_bestand.csv", sep=";")
m = a.merge(b, on=["symbol", "stunde"], how="outer", indicator=True)
x = m[m.symbol.isin(streng)]
print("%d streng unveraenderte Symbole: Einstiege gemeinsam %d, nur lang %d, nur Referenz %d -> gleich %.1f %%" % (
    len(streng), (x._merge == "both").sum(), (x._merge == "left_only").sum(), (x._merge == "right_only").sum(), 100 * (x._merge == "both").mean()))
P.TAGE = pd.date_range("2024-01-01", "2026-08-31", freq="D")
sr, nr, _ = P.tagesreihe(b)
sl, nl, _ = P.tagesreihe(a)
n = np.maximum(nr, nl)
gesamt = sl.sum() - sr.sum() * nl.sum() / nr.sum()           # Differenz der Summen bei gleicher Handelszahl wie lang
for lo, hi in ((1, 5), (6, 20), (21, 60), (61, 10 ** 6)):
    k = (n >= lo) & (n <= hi)
    print("Tage mit %d-%s Signalen: %d Tage · Referenz %d Handel %+.3f %% · lang %d Handel %+.3f %% · Anteil an der Differenz %.0f %%" % (
        lo, hi if hi < 10 ** 6 else "", k.sum(), nr[k].sum(), 100 * sr[k].sum() / max(nr[k].sum(), 1), nl[k].sum(),
        100 * sl[k].sum() / max(nl[k].sum(), 1), 100 * (sl[k].sum() - sr[k].sum() * nl.sum() / nr.sum()) / gesamt))
