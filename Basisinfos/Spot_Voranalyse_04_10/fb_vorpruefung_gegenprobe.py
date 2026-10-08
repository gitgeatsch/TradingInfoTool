"""Gegenprobe der Vorpruefung Teil B (Spot §31.1) und Machbarkeit des Messplans §31.3 - eigener Rechenweg, nur lesend.

    python Basisinfos/Spot_Voranalyse_04_10/fb_vorpruefung_gegenprobe.py

  G1 Erreichen von ATH, Z1 x2, Z4 2 s an 40 Ankern mit pandas neu (cummax-freier Weg: max der Zukunftsreihe) - gleich, auch der Tag
  G2 Z3 +50 % (Vorsprung gegen BTC) an 30 Ankern neu - gleich
  G3 Einstand-Stellvertreter: nur Anker, deren Kurs vor 12 M UEBER dem Start lag, tragen einen Wert (Korrektur vor der Auswertung)
  G4 Anteile der Ausgabe (ATH ab 2024 alle / L-Kandidaten) aus den Ankern neu = Ausgabe
  G5 ab 2024 keine Kandidaten-Kennzahl in der Ausgabe (Wahl unberuehrt)
  G6 MACHBARKEIT (nur Anzahlen): L ab 2024 >= 20 Faelle an >= 6 Starttagen; K-Stellvertreter-Einstieg (Coin/BTC >= 1,3 x 30-T-Tief,
     30 T Sperre) 2023 und ab 2024 >= 20 Faelle in >= 6 Monaten
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

K, POS, BTCV, IDX = M.K, M.POS, M.BTCV, M.IDX
R = pd.read_csv(os.path.join("data", "_spot", "fb_vorpruefung_anker.csv"), sep=";", parse_dates=["t"])
TXT = open(os.path.join(HIER, "fb_vorpruefung.txt"), encoding="utf-8").read()
ok = n = 0


def pruefe(name, gut, info):
    global ok, n
    n += 1; ok += bool(gut)
    print("%-3s %s  %s" % (name, "gleich" if gut else "ABWEICHUNG", info), flush=True)


def zukunft(s, i):
    x = pd.Series(K[s].values[i + 1:i + 366])
    return x[:x.notna().values.argmin()] if not x.notna().all() else x


for r in R.sample(40, random_state=21).itertuples():
    i = POS[r.t]
    s = pd.Series(K[r.sym].values[:i + 1])
    p0, ath = s.iloc[-1], s.max()
    sig = np.log(s.iloc[-91:]).diff().std(ddof=0) * np.sqrt(90)
    x = zukunft(r.sym, i)
    gut = True
    for k, ziel in (("ATH", ath), ("Z1 x2", 2 * p0), ("Z4 2 s", p0 * np.exp(2 * sig))):
        hit = np.where(x.values >= ziel)[0]
        neu = len(hit) > 0
        alt = getattr(r, k.replace(" ", "_").replace(",", "_"), None) if False else R.loc[r.Index, k]
        tag = hit[0] + 1 if neu else np.nan
        gut &= (bool(alt) == neu) and (np.isnan(tag) and np.isnan(R.loc[r.Index, k + "_t"]) or tag == R.loc[r.Index, k + "_t"])
    pruefe("G1", gut, "%s %s ATH/x2/2s" % (r.sym, r.t.date()))

fx = 0
for r in R.sample(30, random_state=22).itertuples():
    i = POS[r.t]
    x = zukunft(r.sym, i)
    rel = (x.values / K[r.sym].values[i]) / (BTCV[i + 1:i + 1 + len(x)] / BTCV[i])
    fx += (rel >= 1.5).any() != bool(R.loc[r.Index, "Z3 +50 %"])
pruefe("G2", fx == 0, "Z3 +50 %% an 30 Ankern, Abweichungen %d" % fx)

bad = 0
for r in R.sample(300, random_state=23).itertuples():
    i = POS[r.t]
    if i < 365:
        continue
    vor = K[r.sym].values[i - 365]
    hat = not pd.isna(R.loc[r.Index, "E12"])
    bad += hat != (np.isfinite(vor) and vor > K[r.sym].values[i])
pruefe("G3", bad == 0, "Einstand-Stellvertreter nur bei Position im Minus, Abweichungen %d von 300" % bad)

for sub, g in (("alle", R[R.jahr >= 2024]), ("L-Kandidaten", R[(R.jahr >= 2024) & R.fuenftel])):
    m = re.search(r"ab 2024 \(Urteil\)  %s +n +(\d+) · ATH +(\d+\.\d) %%" % re.escape(sub), TXT)
    pruefe("G4", m and int(m.group(1)) == len(g) and abs(100 * g.ATH.mean() - float(m.group(2))) < 0.06, "%s ATH %.2f %% n %d · Ausgabe %s" % (
        sub, 100 * g.ATH.mean(), len(g), m.groups() if m else None))

teil_b = TXT.split("B) KANDIDATEN")[1].split("C) FALLZAHL")[0]
pruefe("G5", "2024" not in teil_b and "ab 2024" not in TXT.split("C) FALLZAHL")[1].split("·")[0].replace("ab 2024 (nur Anzahlen", ""),
       "Kandidatenteil nur 2023; Fallzahlteil nur Anzahlen")

l24 = R[(R.jahr >= 2024) & R.fuenftel]
pruefe("G6", len(l24) >= 20 and l24.t.nunique() >= 6, "L ab 2024: %d L-Kandidaten an %d Starttagen" % (len(l24), l24.t.nunique()))
uni = sorted(set(R.sym))
ende = len(IDX) - 1 - 180
anker = []
for s in uni:
    v = K[s].values
    rel = v / BTCV
    sperre = -1
    for i in range(POS[pd.Timestamp("2023-01-01")], ende):
        if i <= sperre or not np.isfinite(rel[i]):
            continue
        tief = np.nanmin(rel[i - 30:i + 1])
        if np.isfinite(tief) and tief > 0 and rel[i] >= 1.3 * tief:
            anker.append((IDX[i], s))
            sperre = i + 30
A = pd.DataFrame(anker, columns=["t", "sym"])
for nm, g in (("2023", A[A.t.dt.year == 2023]), ("ab 2024", A[A.t.dt.year >= 2024])):
    mon = g.t.dt.to_period("M").nunique()
    pruefe("G6", len(g) >= 20 and mon >= 6, "K-Stellvertreter %s: %d Einstiege in %d Monaten (%d Coins)" % (nm, len(g), mon, g.sym.nunique()))
print("\n%d von %d gleich" % (ok, n))
