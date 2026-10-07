"""Gegenprobe A1 (python Basisinfos/Rechenkern_02_10/a1_gegenprobe.py) - eigener Rechenweg, nur lesend, keine Aufrufe.

  G1 Mehrheitsurteile je Anker selbst gezaehlt (ohne n4_auswertung.urteile) gegen den Bericht: 130 dagegen / 100 neutral / 16 stuetzt / 3 uneinig
  G2 Zahlenzerlegung: 10 zufaellige Anker, Abstand zum 200-T-Schnitt und Umsatzfaktor mit einer ZWEITEN Zerlegung (Satz suchen, Zahl davor)
  G3 Rangkorrelation Urteil-Saldo gegen abst200 und struktur_hoch mit scipy.stats.spearman statt pandas
  G4 Anteil 'dagegen' beim Trend-Fakt aus dem ROHTEXT gezaehlt (Teilzeichenkette), ohne JSON-Zerlegung
"""
import json
import os
import random
import re
import sqlite3
import sys

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
import a1_woran as W  # noqa: E402

c = sqlite3.connect("file:%s?mode=ro" % W.ABLAGE, uri=True)
st = pd.read_sql("SELECT pos, urteil, gueltig, roh FROM stimme WHERE teil='T'", c)
ok = n = 0


def pruefe(name, gut, info):
    global ok, n
    n += 1; ok += bool(gut)
    print("%-4s %s  %s" % (name, "gleich" if gut else "ABWEICHUNG", info))


zaehl = {"spricht_dagegen": 0, "neutral": 0, "stuetzt": 0, "uneinig": 0}
for p, g in st[st.gueltig == 1].groupby("pos"):
    w = g.urteil.value_counts()
    zaehl[w.index[0] if w.iloc[0] * 2 > len(g) else "uneinig"] += 1
pruefe("G1", zaehl == {"spricht_dagegen": 130, "neutral": 100, "stuetzt": 16, "uneinig": 3}, str(zaehl))

e = pd.read_sql("SELECT pos, eingabe FROM eingabe", c).set_index("pos")
random.seed(8)
for p in random.sample(sorted(st.pos.unique()), 10):
    txt = " ".join(json.loads(e.at[p, "eingabe"]).get("lage_des_werts", []))
    satz = next((s for s in txt.split(".") if "200-Tage-Schnitt" in s), "")
    zz = re.findall(r"(\d+,\d+) Schwankungsbreiten", satz)
    eigen = (float(zz[0].replace(",", ".")) * (-1 if "unter dem 200" in satz else 1)) if zz else np.nan
    satz_u = next((s for s in txt.split(". ") if "Umsatz liegt beim" in s), "")
    zu = re.findall(r"beim (\d+,\d+)", satz_u)
    eigen_u = float(zu[0].replace(",", ".")) if zu else np.nan
    m = W.zahlen(e.at[p, "eingabe"])
    gleich = (np.isnan(eigen) and np.isnan(m["abst200"]) or abs(eigen - m["abst200"]) < 1e-9) and \
             (np.isnan(eigen_u) and np.isnan(m["umsatz"]) or abs(eigen_u - m["umsatz"]) < 1e-9)
    pruefe("G2", gleich, "pos %d abst200 %s / %s · umsatz %s / %s" % (p, eigen, m["abst200"], eigen_u, m["umsatz"]))

d = W.NA.urteile(c, "T")
Z = pd.DataFrame([dict(pos=p, **W.zahlen(e.at[p, "eingabe"])) for p in d.pos]).set_index("pos")
d = d.join(Z, on="pos")
for k, soll in (("abst200", {"2025": 0.401, "2026": 0.241}), ("struktur_hoch", {"2025": 0.501, "2026": 0.468})):
    for j in ("2025", "2026"):
        x = d[(d.jahr.astype(str) == j) & d[k].notna()]
        r = spearmanr(x[k], x.saldo).correlation
        pruefe("G3", abs(r - soll[j]) < 0.0015, "%s %s scipy %+.4f gegen Bericht %+.3f" % (k, j, r, soll[j]))

tr = da = 0
for roh in st[st.gueltig == 1].roh:
    for m_ in re.finditer(r'"fakt":\s*"([^"]*)",\s*"richtung":\s*"(\w+)"', roh.replace('\\"', '"')):
        f = m_.group(1).lower()
        if any(w in f for w in ("200-tage", "60 tage", "lange sicht", "langen sicht")):
            tr += 1; da += m_.group(2) == "dagegen"
pruefe("G4", tr > 0 and abs(da / tr - 0.75) < 0.02, "Trend-Fakt %d Belege, dagegen %.1f %% (Bericht 75 %%)" % (tr, 100 * da / max(tr, 1)))
print("\n%d von %d gleich" % (ok, n))
