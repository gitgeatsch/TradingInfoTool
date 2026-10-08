"""Gegenprobe Vorpruefung Teil C (Spot §35.2) - eigener Rechenweg, nur lesend.

    python Basisinfos/Spot_Voranalyse_04_10/tc_gegenprobe.py

  T1 Zielgroesse: an 40 zufaelligen Coin-Tagen 2023 Lauf/Absturz mit einer Schleife ueber die 30 Folgetage neu - gleich
  T2 rs30 oberes Fuenftel 2023: Lift Lauf, Lift Absturz, Richtung im LANGFORMAT (groupby je Tag) neu = Ausgabe
  T3 Klasse H, rs30 oberes Fuenftel: Richtung neu = Ausgabe
  T4 ab 2024 nur Anzahlen in der Ausgabe (keine Lift-Zahl fuer 2024)
"""
import os
import re
import sys

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
os.chdir(os.path.dirname(os.path.dirname(HIER)))
import tc_vorpruefung as T  # noqa: E402

K, IDX, BTCV = T.K, T.IDX, T.BTCV
TXT = open(os.path.join(HIER, "tc_vorpruefung.txt"), encoding="utf-8").read()
ok = n = 0
RNG = np.random.default_rng(7)


def pruefe(name, gut, info):
    global ok, n
    n += 1; ok += bool(gut)
    print("%-3s %s  %s" % (name, "gleich" if gut else "ABWEICHUNG", info), flush=True)


rel, F = T.merkmale()
up, down, end, fertig = T.ziele(rel)
m, kl = T.maske()
m = m & fertig
w = (IDX >= "2023-01-01") & (IDX <= "2023-12-01")
paare = [(d, s) for d, s in m[w].stack()[lambda x: x].index]
fx = 0
for k in RNG.choice(len(paare), 40, replace=False):
    d, s = paare[k]
    i = IDX.get_loc(d)
    r0 = K[s].values[i] / BTCV[i]
    f = [K[s].values[j] / BTCV[j] / r0 for j in range(i + 1, i + 31)]
    f = [x for x in f if x == x]
    fx += (max(f) >= 1.3) != bool(up.loc[d, s]) or (min(f) <= 1 / 1.3) != bool(down.loc[d, s])
pruefe("T1", fx == 0, "Lauf/Absturz an 40 Coin-Tagen, Abweichungen %d" % fx)

lang = pd.DataFrame({"x": F["rs30"][w].where(m[w]).stack(), "up": up[w].where(m[w]).stack(), "dn": down[w].where(m[w]).stack()}).dropna()
lang["tag"] = lang.index.get_level_values(0)
lang = lang[lang.groupby("tag").x.transform("count") >= 30]
lang["p"] = lang.groupby("tag").x.rank(pct=True)
top = lang[lang.p >= 0.8]
lu, ld = top.up.mean() / lang.up.mean(), top.dn.mean() / lang.dn.mean()
mm = re.search(r"rs30 +\d+ % / +\d+ % +\| +(\d\.\d\d) · +(\d\.\d\d) · +(\d\.\d\d)", TXT)
pruefe("T2", mm and abs(lu - float(mm.group(1))) < 0.006 and abs(ld - float(mm.group(2))) < 0.006, "rs30 oben: Lift Lauf %.3f · Absturz %.3f · Richtung %.3f · Ausgabe %s" % (
    lu, ld, lu / ld, mm.groups() if mm else None))

lang["kl"] = [kl.loc[d, s] for d, s in lang.index]
h = lang[lang.kl == "H"]
th = h[h.p >= 0.8]
rh = (th.up.mean() / h.up.mean()) / (th.dn.mean() / h.dn.mean())
mm = re.search(r"H: rs7 \d\.\d\d · rs30 (\d\.\d\d)", TXT)
pruefe("T3", mm and abs(rh - float(mm.group(1))) < 0.006, "Klasse H rs30 oben: Richtung %.3f · Ausgabe %s" % (rh, mm.group(1) if mm else None))

z24 = [z for z in TXT.splitlines() if z.strip().startswith("AB 2024")]
kombi = TXT.split("STUFE 1b")[1] if "STUFE 1b" in TXT else ""
gut = len(z24) == 1 and not re.search(r"Lift|Richtung|Ende", z24[0]) and "2024" not in kombi
pruefe("T4", gut, "Zeile AB 2024 nur Anzahlen: %s · Kombinationsteil ohne 2024: %s" % (bool(z24) and not re.search(r"Lift|Richtung|Ende", z24[0]), "2024" not in kombi))
print("\n%d von %d gleich" % (ok, n))
