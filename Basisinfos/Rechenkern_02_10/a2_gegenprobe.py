"""Gegenprobe A2 Teil 2 (python Basisinfos/Rechenkern_02_10/a2_gegenprobe.py) - eigener Rechenweg, nur lesend, keine Aufrufe.

  G1 Grundraten Chance/Spiegel aus der CSV mit csv-Modul und eigener Bedingung gegen den Bericht
  G2 Merkmale an 20 zufaelligen Einstiegen der Menge bestand mit DIREKTEN SQL-Abfragen (ohne reihe/asfreq) gegen merkmale_je_symbol
  G3 Wahl-Unterschied 2024 je Merkmal mit numpy.percentile und eigener Drittelzuordnung gegen den Bericht
  G4 Nullwelt: (a) die Vertauschung erhaelt je Tag die Wertemenge und ist keine Identitaet; (b) 200 ZUFALLSMERKMALE auf bestand 2024 -
     Wahlquote muss nahe 10 % liegen (P90-Regel); (c) GEPFLANZT: Merkmal = Chance + Rauschen wird gewaehlt
"""
import csv
import os
import re
import sqlite3
import sys
from datetime import timedelta

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
import a2_messung as M  # noqa: E402

ok = n = 0
BER = open(os.path.join(HIER, "a2_messung.txt"), encoding="utf-8").read()


def pruefe(name, gut, info):
    global ok, n
    n += 1; ok += bool(gut)
    print("%-4s %s  %s" % (name, "gleich" if gut else "ABWEICHUNG", info))


# G1
with open(os.path.join(M.D, "_vergleich", "kern48jbz_einstiege_bestand.csv"), encoding="utf-8") as fh:
    z = list(csv.DictReader(fh, delimiter=";"))
for jahre, lab in (({"2024"}, "2024"), ({"2025", "2026"}, "2025-26")):
    w = [r for r in z if r["jahr"] in jahre]
    a = sum(1 for r in w if int(r["t_u"]) <= 24 and int(r["t_u"]) < int(r["t_d"])) / len(w)
    b = sum(1 for r in w if int(r["t_d"]) <= 24 and int(r["t_d"]) <= int(r["t_u"])) / len(w)
    m = re.search(r"%s ([\d.]+) / ([\d.]+)" % lab, BER)
    pruefe("G1", m and abs(float(m.group(1)) - a) < 6e-4 and abs(float(m.group(2)) - b) < 6e-4, "%s Chance %.4f Spiegel %.4f" % (lab, a, b))

# G2
C = {k: M.con(f) for k, f in (("sk", "stundenkurse.db"), ("ska", "stundenkurse_alle.db"), ("eh", "eingestellt_historie.db"),
                               ("mh", "markpreis_historie.db"), ("ma", "markpreis_alle.db"), ("tm", "terminmarkt_historie.db"),
                               ("rf", "richtung_historie.db"), ("fu", "funding_historie.db"))}
C["btc"] = M.reihe([C["sk"], C["ska"]], "stundenkurse", "BTC", "close")
E = pd.read_csv(os.path.join(M.D, "_vergleich", "kern48jbz_einstiege_bestand.csv"), sep=";")
stich = E.sample(20, random_state=8)


def eins(sql, par):
    for q in ("sk", "ska", "eh", "mh", "ma", "tm", "rf", "fu"):
        try:
            r = C[q].execute(sql, par).fetchone()
        except sqlite3.OperationalError:
            continue
        if r is not None and r[0] is not None:
            return r
    return None


for r in stich.itertuples():
    t = M.B0 + timedelta(hours=int(r.stunde))
    ts = lambda d: d.strftime("%Y-%m-%d %H:%M")  # noqa: E731
    o = M.merkmale_je_symbol(r.symbol, [t], C)[t]
    eigen = {}
    k = eins("SELECT open, high, low, close FROM stundenkurse WHERE symbol=? AND stunde=?", (r.symbol, ts(t)))
    if k:
        eigen["c_docht"] = (k[3] - k[2]) / (k[1] - k[2]) if k[1] > k[2] else np.nan
        k6 = eins("SELECT close FROM stundenkurse WHERE symbol=? AND stunde=?", (r.symbol, ts(t - timedelta(hours=6))))
        mk = eins("SELECT close FROM markpreis WHERE symbol=? AND stunde=?", (r.symbol, ts(t)))
        eigen["a_praemie"] = mk[0] / k[3] - 1 if mk else np.nan
    fl = [eins("SELECT volumen, kauf_volumen FROM fluss WHERE symbol=? AND stunde=?", (r.symbol, ts(t - timedelta(hours=i)))) for i in range(6)]
    eigen["g_kauf6"] = sum(x[1] for x in fl) / sum(x[0] for x in fl) if all(fl) else np.nan
    fu = eins("SELECT wert FROM funding WHERE symbol=? AND datum=?", (r.symbol, (t - timedelta(days=1)).strftime("%Y-%m-%d")))
    eigen["f_funding"] = fu[0] if fu else np.nan
    b0 = eins("SELECT close FROM stundenkurse WHERE symbol='BTC' AND stunde=?", (ts(t - timedelta(hours=24)),))
    b1 = eins("SELECT close FROM stundenkurse WHERE symbol='BTC' AND stunde=?", (ts(t),))
    eigen["e_btc24"] = b1[0] / b0[0] - 1 if b0 and b1 else np.nan
    gleich = all((np.isnan(v) and np.isnan(o[f])) or (np.isfinite(o[f]) and abs(v - o[f]) < 1e-9 * max(1, abs(v))) for f, v in eigen.items())
    pruefe("G2", gleich, "%s %s %s" % (r.symbol, ts(t), " ".join("%s %.5g/%.5g" % (f, v, o[f]) for f, v in eigen.items())))

# G3 / G4 auf bestand 2024
cache = {}
X = M.lade_menge("bestand", C, cache)
W = X[X.jahr == 2024]
for f in M.MERKMALE:
    w = W[W[f].notna()]
    if len(w) < 200:
        continue
    q1, q2 = np.percentile(w[f].values, [100 / 3, 200 / 3])
    a = w.A24.values
    d = a[w[f].values > q2].mean() - a[w[f].values <= q1].mean()
    m = re.search(r"%s\s+WAHL 2024: Chance oben-unten ([-+][\d.]+)" % f, BER)
    pruefe("G3", m and abs(float(m.group(1)) - d) < 6e-4, "%s numpy %+.4f Bericht %s" % (f, d, m.group(1) if m else "-"))

w = W[W.c_docht.notna()].copy()
tc = pd.factorize(w.tag.values)[0]
nach_tag = np.argsort(tc, kind="stable")
perm = np.lexsort((M.RNG.random(len(w)), tc))
g = np.empty(len(w)); g[nach_tag] = w.c_docht.values[perm]
erhalten = all(sorted(g[tc == i]) == sorted(w.c_docht.values[tc == i]) for i in range(tc.max() + 1))
pruefe("G4a", erhalten and (g != w.c_docht.values).mean() > 0.3, "Wertemenge je Tag erhalten, Anteil veraendert %.0f %%" % (100 * (g != w.c_docht.values).mean()))
rng = np.random.default_rng(5)
treffer = 0
for i in range(200):
    w["_z"] = rng.standard_normal(len(w))
    k = w._z.quantile([1 / 3, 2 / 3]).values
    dA = M.diff(w, w._z, k)[0]
    treffer += abs(dA) > np.nanpercentile(np.abs(M.null(w, "_z", k, nz=200)), 90)
pruefe("G4b", 0.05 <= treffer / 200 <= 0.16, "Zufallsmerkmale gewaehlt %d von 200 (%.1f %%, Soll ~10 %%)" % (treffer, 100 * treffer / 200))
w["_p"] = w.A24 + rng.standard_normal(len(w)) * 1.5
k = w._p.quantile([1 / 3, 2 / 3]).values
dA = M.diff(w, w._p, k)[0]
p90 = np.nanpercentile(np.abs(M.null(w, "_p", k, nz=200)), 90)
pruefe("G4c", dA > p90, "gepflanzt Chance+Rauschen(1,5): Unterschied %+.3f gegen P90 %.3f" % (dA, p90))
print("\n%d von %d gleich" % (ok, n))
