"""Gegenprobe Machbarkeit §37 - zweite Umsetzung der Einstiegsregel (Tag fuer Tag statt Coin fuer Coin), nur lesend, nur Anzahlen.

    python Basisinfos/Spot_Voranalyse_04_10/k37_gegenprobe.py

  G1 Einstiege H und M, 2023 und ab 2024: Tagesschleife mit 'frei ab'-Buch je Coin = Ablage (gleiche Paare Signal/Coin)
  G2 Sperre: kein Coin hat zwei Einstiege, deren Haltezeiten sich ueberlappen
  G3 jeder Einstieg: am Signaltag rs30 im oberen Fuenftel und Klasse stimmt
"""
import os
import sys

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
os.chdir(os.path.dirname(os.path.dirname(HIER)))
import tc_vorpruefung as T  # noqa: E402

IDX = T.IDX
ok = n = 0


def pruefe(name, gut, info):
    global ok, n
    n += 1; ok += bool(gut)
    print("%-3s %s  %s" % (name, "gleich" if gut else "ABWEICHUNG", info), flush=True)


rel, F = T.merkmale()
up, down, end, fertig = T.ziele(rel)
m, kl = T.maske()
m = m & fertig
X = F["rs30"].where(m)
pct = X.rank(axis=1, pct=True)
pct.loc[X.notna().sum(axis=1) < 30] = np.nan
for k in ("H", "M"):
    for ep, ab, bis in (("W", "2023-01-01", "2023-12-01"), ("U", "2024-01-01", str(T.M.ENDE.date()))):
        A = pd.read_csv(os.path.join("data", "_spot", "k37_einstiege_%s_%s.csv" % (k, ep)), sep=";", parse_dates=["signal"])
        frei = {}
        neu = []
        for i, d in enumerate(IDX):
            if d < pd.Timestamp(ab) or d > pd.Timestamp(bis) or i + 31 > len(IDX) - 1:
                continue
            zeile = pct.iloc[i]
            for s in zeile.index[(zeile.values >= 0.8)]:
                if kl.iat[i, kl.columns.get_loc(s)] != k or not m.iat[i, m.columns.get_loc(s)]:
                    continue
                if frei.get(s, -1) >= i:
                    continue
                neu.append((d, s))
                frei[s] = i + 31
        a = set(zip(A.signal, A.sym))
        pruefe("G1", set(neu) == a, "%s %s: eigene %d · Ablage %d · nur eigene %d · nur Ablage %d" % (k, ep, len(neu), len(a), len(set(neu) - a), len(a - set(neu))))
        ueber = 0
        for s, g in A.sort_values("i_kauf").groupby("sym"):
            ueber += int((g.i_kauf.values[1:] <= g.i_aus.values[:-1]).sum())
        pruefe("G2", ueber == 0, "%s %s: ueberlappende Haltezeiten %d" % (k, ep, ueber))
        fx = sum(not (pct.at[r.signal, r.sym] >= 0.8 and kl.at[r.signal, r.sym] == k) for r in A.itertuples())
        pruefe("G3", fx == 0, "%s %s: Signaltag-Bedingung verletzt %d" % (k, ep, fx))
print("\n%d von %d gleich" % (ok, n))
