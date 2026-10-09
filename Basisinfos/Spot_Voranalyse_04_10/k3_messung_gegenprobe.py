"""Gegenprobe Messung §40 K-3 - zweiter Rechenweg gegen die Ablage data/_spot/k3_messung.csv, nur lesend.

    python Basisinfos/Spot_Voranalyse_04_10/k3_messung_gegenprobe.py

  G1 Einstiege der Messung = Einstiege der Machbarkeit (k3_einstiege_*_U.csv, dort 18/18 gegengeprueft)
  G2 Ertrag gegen BTC aus Rohkursen (eigene Schleife: letzter gueltiger Kurs bis zum Ausstieg) = Ablage
  G3 Korb je Monat (eigene Rechnung, Wörterbuch) = Ausgabe der Messung
  G4 Nullwelt: ANALYTISCHER Erwartungswert (Mittel der Kandidaten je Tag und Klasse, eigene Perzentile) gegen das Mittel der 200 Ziehungen
  G5 Lauf x1,3 / Absturz <= 1/1,3 binnen 30 T aus eigener Relativreihe = Ablage; Spiegel aus eigener Rechnung = Ausgabe
  G6 nach Kosten (mittlere Kosten je Klasse) = Ausgabe · G7 Zahlen je Klasse = Ausgabe
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
KOSTEN = {"H": 0.0072, "M": 0.0176, "S": 0.064}
ok = n = 0


def pruefe(name, gut, info):
    global ok, n
    n += 1; ok += bool(gut)
    print("%-3s %s  %s" % (name, "gleich" if gut else "ABWEICHUNG", info), flush=True)


def ertrag(s, i0, i1):
    x = K[s].values
    j = i1
    while j > i0 and not np.isfinite(x[j]):
        j -= 1
    return (x[j] / x[i0]) / (BTCV[i1] / BTCV[i0]) - 1


aus = open(os.path.join("Basisinfos", "Spot_Voranalyse_04_10", "k3_messung.txt"), encoding="utf-8").read()
E = pd.read_csv(os.path.join("data", "_spot", "k3_messung.csv"), sep=";", parse_dates=["signal"])
A = pd.concat([pd.read_csv(os.path.join("data", "_spot", "k3_einstiege_%s_U.csv" % k), sep=";", parse_dates=["signal"]).assign(kl=k) for k in "HMS"])
pruefe("G1", set(zip(E.signal, E.sym, E.kl)) == set(zip(A.signal, A.sym, A.kl)), "Messung %d · Machbarkeit %d Einstiege" % (len(E), len(A)))

eig = np.array([ertrag(r.sym, r.i_kauf, r.i_aus) for r in E.itertuples()])
pruefe("G2", np.allclose(eig, E.ex.values, rtol=0, atol=1e-12), "groesste Abweichung %.2e" % np.nanmax(np.abs(eig - E.ex.values)))

mon = {}
for r, x in zip(E.itertuples(), eig):
    mon.setdefault((r.signal.year, r.signal.month), []).append(x)
korb = np.mean([np.mean(v) for v in mon.values()])
k_aus = float(re.search(r"Korb ([+-][\d.]+) Pp gegen BTC", aus).group(1))
pruefe("G3", abs(100 * korb - k_aus) < 0.006, "eigener Korb %+.3f Pp · Messung %+.2f Pp · Monate %d" % (100 * korb, k_aus, len(mon)))

m, kl = T.maske()
rel_, F = T.merkmale()
fertig = T.ziele(rel_)[3]
m = m & fertig
S90, TI = F["schwankung90"].where(m), F["tiefe"].where(m)
rel = K.div(BTCV, axis=0)
mu_m, var_m, lauf_n, abst_n, g = {}, {}, 0.0, 0.0, 0
for (d, k), gg in E.groupby(["signal", "kl"]):
    i = IDX.get_loc(d)
    ra, rb = S90.iloc[i].dropna().rank(pct=True), TI.iloc[i].dropna().rank(pct=True)
    ks = [s for s in K.columns if kl.iat[i, kl.columns.get_loc(s)] == k and m.iat[i, m.columns.get_loc(s)]
          and not (ra.get(s, 1) <= 0.2 and rb.get(s, 1) <= 0.2) and np.isfinite(K[s].values[i + 1])]
    x = np.array([ertrag(s, i + 1, gg.iloc[0].i_aus) for s in ks])
    key = (d.year, d.month)
    a, b = mu_m.get(key, (0.0, 0)), var_m.get(key, 0.0)
    mu_m[key] = (a[0] + len(gg) * x.mean(), a[1] + len(gg))
    var_m[key] = b + len(gg) * x.var()
    r0 = rel[ks].values[i + 1]
    fen = rel[ks].values[i + 2:i + 32]
    voll = np.isfinite(fen).all(axis=0)                  # wie T.ziele: rolling(30, min_periods=30) -> alle 30 Tage mit Kurs
    lauf_n += len(gg) * np.mean(voll & (np.max(fen, axis=0) / r0 >= 1.3))
    abst_n += len(gg) * np.mean(voll & (np.min(fen, axis=0) / r0 <= 1 / 1.3))
    g += len(gg)
erw = np.mean([s / c for s, c in mu_m.values()])
se = np.sqrt(sum(var_m[key] / mu_m[key][1] ** 2 for key in mu_m)) / len(mu_m) / np.sqrt(200)
n_aus = float(re.search(r"Nullwelt ([+-][\d.]+) Pp\)", aus).group(1))
pruefe("G4", abs(100 * erw - n_aus) < max(4 * 100 * se, 0.006), "analytisch %+.3f Pp (SE der 200 Ziehungen %.3f) · Messung %+.2f Pp" % (100 * erw, 100 * se, n_aus))

la, ab = [], []
for r in E.itertuples():
    r0 = rel[r.sym].values[r.i_kauf]
    f = rel[r.sym].values[r.i_kauf + 1:r.i_kauf + 31]
    la.append(bool(np.isfinite(f).all() and f.max() / r0 >= 1.3))
    ab.append(bool(np.isfinite(f).all() and f.min() / r0 <= 1 / 1.3))
pruefe("G5a", (np.array(la) == E.lauf.values).all() and (np.array(ab) == E.absturz.values).all(),
       "Lauf %d / Absturz %d eigene · Ablage %d / %d" % (sum(la), sum(ab), E.lauf.sum(), E.absturz.sum()))
sp = (np.mean(la) / max(np.mean(ab), 1e-9)) / ((lauf_n / g) / max(abst_n / g, 1e-9))
s_aus = float(re.search(r"Spiegel ([\d.]+) \(", aus).group(1))
pruefe("G5b", abs(sp - s_aus) < 0.006, "eigener Spiegel %.3f (Nullwelt Lauf %.1f %% / Absturz %.1f %%) · Messung %.2f" % (sp, 100 * lauf_n / g, 100 * abst_n / g, s_aus))

kost = np.mean([KOSTEN[k] for k in E.kl])
nk_aus = float(re.search(r"nach Kosten .*?Korb ([+-][\d.]+) Pp", aus).group(1))
pruefe("G6", abs(100 * (korb - kost) - nk_aus) < 0.006, "eigene %+.3f Pp (Kosten %.3f %%) · Messung %+.2f Pp" % (100 * (korb - kost), 100 * kost, nk_aus))
zk = re.search(r"H (\d+) · M (\d+) · S (\d+)", aus)
pruefe("G7", tuple(int(x) for x in zk.groups()) == tuple(int((E.kl == k).sum()) for k in "HMS"), "je Klasse %s" % dict(E.kl.value_counts()))
print("\n%d von %d gleich" % (ok, n))
