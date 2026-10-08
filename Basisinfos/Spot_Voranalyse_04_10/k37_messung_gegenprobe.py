"""Gegenprobe Messung K-H1 (Spot §37) - eigener Rechenweg, nur lesend.

    python Basisinfos/Spot_Voranalyse_04_10/k37_messung_gegenprobe.py

  Q1 Ertrag gegen BTC an 40 Einstiegen je Klasse: Ausstiegskurs = letzter gueltiger Kurs bis zum Ausstiegstag (eigene Suche) - gleich
  Q2 Korb (Monate) aus der Ablage neu = Ausgabe
  Q3 Nullwelt ANALYTISCH: Erwartungswert = je Monat das nach Einstiegen gewichtete Mittel der Kandidaten-Ertraege - nahe am gezogenen Mittel
  Q4 Spiegelprobe neu (Lauf-/Absturz-Anteil der Einstiege gegen die Kandidaten) = Ausgabe
  Q5 Kostenzeile: Korb - Kosten = Ausgabe
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
TXT = open(os.path.join(HIER, "k37_messung.txt"), encoding="utf-8").read()
KOSTEN = {"H": 0.0072, "M": 0.0176}
ok = n = 0


def pruefe(name, gut, info):
    global ok, n
    n += 1; ok += bool(gut)
    print("%-3s %s  %s" % (name, "gleich" if gut else "ABWEICHUNG", info), flush=True)


def ex2(s, i0, i1):
    v = K[s].values[i0:i1 + 1]
    j = i0 + int(np.where(~np.isnan(v))[0][-1])
    return (K[s].values[j] / K[s].values[i0]) / (BTCV[i1] / BTCV[i0]) - 1


rel, F = T.merkmale()
up, down, end, fertig = T.ziele(rel)
m, kl = T.maske()
m = m & fertig
X = F["rs30"].where(m)
pct = X.rank(axis=1, pct=True)
pct.loc[X.notna().sum(axis=1) < 30] = np.nan
for k in ("H", "M"):
    E = pd.read_csv(os.path.join("data", "_spot", "k37_messung_%s.csv" % k), sep=";", parse_dates=["signal"])
    fx = sum(abs(ex2(r.sym, r.i_kauf, r.i_aus) - r.ex) > 1e-9 for r in E.sample(min(40, len(E)), random_state=3).itertuples())
    pruefe("Q1", fx == 0, "%s: 40 Einstiege, Abweichungen %d" % (k, fx))
    E["mon"] = E.signal.dt.to_period("M")
    jk = E.groupby("mon").ex.mean().mean()
    mm = re.search(r"K-H1-%s ab 2024: .*?Korb ([+-]\d+\.\d\d) Pp gegen BTC .*?Nullwelt-Mittel ([+-]\d+\.\d\d) Pp\) · Spiegel (\d+\.\d\d)" % k, TXT)
    pruefe("Q2", mm and abs(100 * jk - float(mm.group(1))) < 0.006, "%s Korb neu %+.3f Pp · Ausgabe %s" % (k, 100 * jk, mm.group(1) if mm else None))
    erw, l_n, a_n, g = {}, 0.0, 0.0, 0
    for d, gg in E.groupby("signal"):
        i = IDX.get_loc(d)
        kand = [s for s in K.columns if kl.at[d, s] == k and m.at[d, s] and not (pct.at[d, s] >= 0.8) and K[s].values[i + 1] == K[s].values[i + 1]]
        if not kand:
            continue
        v = np.mean([ex2(s, i + 1, i + 31) for s in kand])
        erw.setdefault(d.to_period("M"), []).append((len(gg), v))
        l_n += len(gg) * np.mean([bool(up.iat[i + 1, up.columns.get_loc(s)]) for s in kand])
        a_n += len(gg) * np.mean([bool(down.iat[i + 1, down.columns.get_loc(s)]) for s in kand])
        g += len(gg)
    e_null = np.mean([sum(n_ * v for n_, v in z) / sum(n_ for n_, _ in z) for z in erw.values()])
    pruefe("Q3", mm and abs(100 * e_null - float(mm.group(2))) < 0.8, "%s Nullwelt analytisch %+.2f Pp · gezogen %s" % (k, 100 * e_null, mm.group(2) if mm else None))
    sp = (E.lauf.astype(str).str.lower().eq("true").mean() / E.absturz.astype(str).str.lower().eq("true").mean()) / ((l_n / g) / (a_n / g))
    pruefe("Q4", mm and abs(sp - float(mm.group(3))) < 0.006, "%s Spiegel neu %.3f · Ausgabe %s" % (k, sp, mm.group(3) if mm else None))
    mk = re.search(r"K-H1-%s.*?\n +nach Kosten \([\d.]+ %% Hin\+Rueck\): Korb ([+-]\d+\.\d\d) Pp" % k, TXT)
    pruefe("Q5", mk and abs(100 * (jk - KOSTEN[k]) - float(mk.group(1))) < 0.006, "%s nach Kosten neu %+.2f · Ausgabe %s" % (k, 100 * (jk - KOSTEN[k]), mk.group(1) if mk else None))
print("\n%d von %d gleich" % (ok, n))
