"""Gegenprobe des Lagebilds 2023 bis heute (Spot §30.1) - eigener Rechenweg, nur lesend.

    python Basisinfos/Spot_Voranalyse_04_10/lage_e3_gegenprobe.py

  Q1 Verhaeltnis-Pfad Coin/BTC an 40 zufaelligen Ankern mit pandas neu (Hoch, Ende) - gleich
  Q2 Ausbruchsquote ab 2024 und je Klasse aus den Ankern neu gezaehlt = Ausgabe
  Q3 Altindex gleichgewichtet an 4 Stichtagen: Top 100 nach eigenem Rang (Umlauf x Kurs), 30-T-Ertrag gegen BTC = Ablage
  Q4 Breite an 6 Stichtagen mit eigener Rechnung = Ablage
  Q5 Fuehrung X2 (180 T) an 30 Ankern mit zweiter Umsetzung der Marke (cummax) = Ablage
  Q6 Lift der Watchlist ab 2024 aus den Ankern neu = Ausgabe
  Q7 Universum: keine Stablecoins/gewickelten Coins (Schwankung 90 T > 0,5 % je Tag bei allen Top-100 an 4 Stichtagen)
"""
import os
import re
import sys

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
os.chdir(os.path.dirname(os.path.dirname(HIER)))
import as_messung as M      # noqa: E402
import mk_messung as MK     # noqa: E402

K, POS, BTCV = M.K, M.POS, M.BTCV
R = pd.read_csv(os.path.join("data", "_spot", "lage_e3_anker.csv"), sep=";", parse_dates=["t"])
L = pd.read_csv(os.path.join("data", "_spot", "lage_e3_markt.csv"), sep=";", parse_dates=["t"])
TXT = open(os.path.join(HIER, "lage_e3.txt"), encoding="utf-8").read()
ok = n = 0


def pruefe(name, gut, info):
    global ok, n
    n += 1; ok += bool(gut)
    print("%-3s %s  %s" % (name, "gleich" if gut else "ABWEICHUNG", info), flush=True)


for r in R.sample(40, random_state=11).itertuples():
    i0 = POS[r.t] + 1
    c = pd.Series(K[r.sym].values[i0:i0 + 181])
    b = pd.Series(BTCV[i0:i0 + 181])
    c = c[:c.notna().values.argmin()] if not c.notna().all() else c
    v = (c / c.iloc[0]) / (b[:len(c)] / b.iloc[0])
    pruefe("Q1", abs(v.max() - 1 - r.hoch) < 1e-9 and abs(v.iloc[-1] - 1 - r.ende) < 1e-9, "%s %s Hoch %+.3f Ende %+.3f" % (r.sym, r.t.date(), v.max() - 1, v.iloc[-1] - 1))

g = R[R.t >= "2024-01-01"]
q = (g.hoch >= 1).mean()
m = re.search(r"ab 2024 +Ausbruchsquote (\d+\.\d) % \(H (\d+\.\d) · M (\d+\.\d) · S (\d+\.\d) %\)", TXT)
pruefe("Q2", m and abs(100 * q - float(m.group(1))) < 0.06 and all(abs(100 * (g[g.kl == k].hoch >= 1).mean() - float(m.group(j + 2))) < 0.06 for j, k in enumerate("HMS")),
       "Quote neu %.2f %% · Ausgabe %s" % (100 * q, m.groups() if m else None))

for t in [pd.Timestamp(x) for x in ("2024-02-01", "2024-11-01", "2025-05-01", "2026-01-01")]:
    if t not in set(L.t):
        continue
    i = POS[t]
    kl = MK.klassen_mw(t)[2]
    mw = pd.Series({s: MK.umlauf(s, t) * K[s].values[i] for s in kl}).dropna()
    mw = mw[mw > 0].drop("BTC", errors="ignore").sort_values(ascending=False).head(100)
    b30 = BTCV[i + 30] / BTCV[i]
    x = [(K[s].values[i + 30] / K[s].values[i]) / b30 - 1 for s in mw.index if K[s].values[i + 30] == K[s].values[i + 30]]
    soll = L[L.t == t].alt_gl.iloc[0]
    pruefe("Q3", abs(np.mean(x) - soll) < 1e-9, "%s Altindex gleichgew. neu %+.4f · Ablage %+.4f" % (t.date(), np.mean(x), soll))

for t in L.t.iloc[::7]:
    i = POS[t]
    _, rg = MK.rang_mw(t)
    top = [s for s in rg.sort_values().index[:50] if s != "BTC"]
    b90 = BTCV[i] / BTCV[i - 90]
    eig = np.mean([K[s].values[i] / K[s].values[i - 90] > b90 for s in top if K[s].values[i - 90] > 0])
    pruefe("Q4", abs(eig - L[L.t == t].breite.iloc[0]) < 1e-12, "%s Breite %.3f" % (t.date(), eig))


def marke2(s, i0, h=180):
    x = pd.Series(K[s].values[i0:i0 + h + 1])
    if not x.notna().all():
        x = x[:x.notna().values.argmin()]
    hoch = x.cummax()
    unter = np.where((x.values < np.maximum(0.65 * hoch, 0.5 * x.iloc[0]).values) & (np.arange(len(x)) > 0))[0]
    j = int(unter[0]) + 1 if len(unter) and unter[0] + 1 < len(x) else len(x) - 1
    return (x.iloc[j] / x.iloc[0]) / (BTCV[i0 + j] / BTCV[i0]) - 1


fx = 0
for r in R[R.x2.notna()].sample(30, random_state=12).itertuples():
    fx += abs(marke2(r.sym, POS[r.t] + 1) - r.x2) > 1e-9
pruefe("Q5", fx == 0, "X2 (180 T) an 30 Ankern, Abweichungen %d" % fx)

g = R[(R.t >= "2024-01-01") & R.fuenftel.notna()]
f = g.fuenftel.astype(bool)
lift = (g[f].hoch >= 1).mean() / (g[~f].hoch >= 1).mean()
m = re.search(r"ab 2024 +Quote im Fuenftel .*?\(Lift (\d+\.\d+)\)", TXT)
pruefe("Q6", m and abs(lift - float(m.group(1))) < 0.006, "Lift neu %.3f · Ausgabe %s" % (lift, m.group(1) if m else None))

low = []
for t in L.t.iloc[::9]:
    i = POS[t]
    _, rg = MK.rang_mw(t)
    for s in [x for x in rg.sort_values().index[:101] if x != "BTC"][:100]:
        sd = np.nanstd(np.diff(np.log(K[s].values[i - 90:i + 1])))
        if sd < 0.005:
            low.append((t.date(), s, sd))
pruefe("Q7", not low, "Top-100 mit Tagesschwankung < 0,5 %%: %s" % (low or "keine"))
print("\n%d von %d gleich" % (ok, n))
