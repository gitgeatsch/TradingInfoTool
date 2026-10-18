"""Gegenprobe P63 (18.10.2026) - die Streuungen auf ANDEREN Rechenwegen.

    python Basisinfos/Rechenkern_02_10/p63_gegenprobe.py

G1 R-R11: Niveau und SE gegen p61 (unabhaengiger Lauf vom 17.10.: +0,545 %, 95 %-Halbbreite +-0,50 Pp ueber 497 Tage)
G2 Filter 50 %: SE ohne Tagesbootstrap - Tage FEST, nur die Zufallsteilmengen neu gezogen (2.000 Ziehungen); Soll: innerhalb 20 % von p63
G3 Ausstieg 48 h - 24 h: SE per Tagesblock-Bootstrap (2.000) statt Formel; Soll: innerhalb 10 %
G4 Schalter-Assets: alle 21 in der Referenz 2025-26 vertreten?
"""
import os
import re
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p63_o21s2_vorpruefung as P  # noqa: E402  (nur die Kursreihe; die Streuungen werden hier anders gerechnet)

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass
ok = []


def pruefe(name, bed, info=""):
    ok.append(bool(bed))
    print("  %s  %s%s" % ("OK  " if bed else "FEHL", name, ("  (%s)" % info) if info else ""))


txt = open(os.path.join("Basisinfos", "Rechenkern_02_10", "p63_o21s2_vorpruefung.txt"), encoding="utf-8").read()
se_v2 = float(re.search(r"Teilmenge 50 % der Signale\s+SE ([0-9.]+) Pp", txt).group(1)) / 100
se_v3 = float(re.search(r"48 h - 24 h .*?SE ([0-9.]+) Pp", txt).group(1)) / 100
E = pd.read_csv(os.path.join("data", "_vergleich", "kern48jbz_einstiege_bestand.csv"), sep=";")
E = E[E.jahr >= 2025].copy()
z24, z48 = [], []
for r in E.itertuples():
    x = P.reihe(r.symbol)
    if x is None:
        z24.append(np.nan); z48.append(np.nan); continue
    a, C = x
    i = int(r.stunde) - a
    p0 = C[i] if 0 <= i < len(C) else np.nan
    z24.append(C[i + 24] / p0 - 1 if i + 24 < len(C) and p0 == p0 else np.nan)
    z48.append(C[i + 48] / p0 - 1 if i + 48 < len(C) and p0 == p0 else np.nan)
E["e24"], E["e48"] = z24, z48
E["tag"] = (P.B0 + pd.to_timedelta(E.stunde, unit="h")).dt.date
D = E[E.e24.notna()]
print("P63 GEGENPROBE · %d Einstiege an %d Tagen\n" % (len(D), D.tag.nunique()))
tm = D.groupby("tag").e24.agg(["sum", "count"])
m = D.e24.mean()
se1 = np.sqrt(((tm["sum"] - tm["count"] * m) ** 2).sum()) / len(D) * np.sqrt(len(tm) / (len(tm) - 1))
pruefe("G1 Niveau +0,545 % und 95 %-Halbbreite +-0,50 Pp wie p61", abs(100 * m - 0.545) < 0.0006 and abs(1.96 * 100 * se1 - 0.50) < 0.02,
       "Mittel %+.4f %%, Halbbreite %.3f Pp" % (100 * m, 1.96 * 100 * se1))
rng = np.random.default_rng(7)
v = D.e24.to_numpy()
t = D.tag.to_numpy()
diffs = []
for _ in range(2000):
    mk = rng.random(len(v)) < 0.5
    diffs.append(v[mk].mean() - v.mean())
se2 = float(np.std(diffs, ddof=1))
pruefe("G2 Filter 50 %: SE bei festen Tagen innerhalb 20 % von p63", abs(se2 / se_v2 - 1) < 0.20, "fest %.4f Pp gegen Bootstrap %.4f Pp" % (100 * se2, 100 * se_v2))
P3 = D[D.e48.notna()]
d3 = (P3.e48 - P3.e24).to_numpy()
t3 = P3.tag.to_numpy()
tage = np.unique(t3)
grp = {k: d3[t3 == k] for k in tage}
bs = []
for _ in range(2000):
    zt = rng.choice(tage, size=len(tage), replace=True)
    s = np.concatenate([grp[k] for k in zt])
    bs.append(s.mean())
se3 = float(np.std(bs, ddof=1))
pruefe("G3 Ausstieg 48-24 h: Bootstrap-SE innerhalb 10 % der Formel", abs(se3 / se_v3 - 1) < 0.10, "Bootstrap %.4f Pp gegen Formel %.4f Pp" % (100 * se3, 100 * se_v3))
sch = ("AKT", "ALGO", "AVAX", "BEAMX", "BNB", "BTC", "ETH", "HYPE", "KAIA", "KAITO", "LINK", "MORPHO", "NEAR", "ONDO", "QNT", "SEI", "SOL", "SUI", "TAO",
       "TURBO", "VIRTUAL")
da = sorted(set(D.symbol) & set(sch))
pruefe("G4 Schalter-Assets in der Referenz 2025-26", len(da) >= 19, "%d von 21, fehlen: %s" % (len(da), ", ".join(sorted(set(sch) - set(da))) or "keine"))
print("\n%d Pruefungen, %s" % (len(ok), "ALLE BESTANDEN" if all(ok) else "%d FEHLGESCHLAGEN" % ok.count(False)))
