"""Gegenprobe §33 - eigener Rechenweg, nur lesend (keine Abrufe).

    python Basisinfos/Spot_Voranalyse_04_10/e33_gegenprobe.py

  P1 Signale bei 8,7 %: BTCDOM-Tagesschluss direkt aus SQL, eigene Signal-Suche - gleiche Tage
  P2 Treffer: eigene Zuordnung zu den Rally-Tiefs - gleich
  P3 Zeitpunkttreue: kein Wert der Einordnung stammt aus der Zukunft (BTC 90T, ETH/BTC 30T an 3 Signalen neu; Fear & Greed <= Signaltag)
  P4 Paar-Suche: bestes Youden aus der Ablage mit eigener Rechnung = Ausgabe
  P5 Teil 3: Kosten je Jahr aus fb_messung_l.csv neu = Ausgabe
"""
import itertools
import os
import re
import sqlite3
import sys

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
os.chdir(os.path.dirname(os.path.dirname(HIER)))
import as_messung as M      # noqa: E402

K, IDX, BTCV = M.K, M.IDX, M.BTCV
TXT = open(os.path.join(HIER, "e33_analyse.txt"), encoding="utf-8").read()
S = pd.read_csv(os.path.join("data", "_spot", "e33_signale.csv"), sep=";", index_col=0, parse_dates=True)
ok = n = 0


def pruefe(name, gut, info):
    global ok, n
    n += 1; ok += bool(gut)
    print("%-3s %s  %s" % (name, "gleich" if gut else "ABWEICHUNG", info), flush=True)


c = sqlite3.connect("file:data/richtung_historie.db?mode=ro", uri=True)
d = pd.read_sql("select substr(stunde,1,10) tag, close from btcdom where stunde in (select max(stunde) from btcdom group by substr(stunde,1,10))", c)
dom = pd.Series(d.close.values, index=pd.to_datetime(d.tag)).sort_index()
ch = dom / dom.shift(30) - 1
sig, letzt = [], None
for t in ch[ch >= 0.087].index:
    if letzt is None or (t - letzt).days >= 14:
        sig.append(t)
    letzt = t
pruefe("P1", [x.date() for x in sig] == [x.date() for x in S.index], "eigene Signale %d · Ablage %d" % (len(sig), len(S)))

tiefs = [pd.Timestamp(x) for x in re.search(r"Rally-Tiefs ([\d\-, ]+)", TXT).group(1).split(", ")]
tr = [any(-10 <= (t - s).days <= 45 for t in tiefs) for s in S.index]
pruefe("P2", tr == list(S.Treffer.astype(bool)), "Treffer eigene %d · Ablage %d" % (sum(tr), int(S.Treffer.sum())))

bad = 0
for s in S.index[::max(1, len(S) // 3)][:3]:
    i = int(np.searchsorted(IDX, s, side="right")) - 1
    b90 = BTCV[i] / BTCV[i - 90] - 1
    e30 = (K["ETH"].values[i] / K["ETH"].values[i - 30]) / (BTCV[i] / BTCV[i - 30]) - 1
    bad += abs(b90 - S.loc[s, "BTC 90T"]) > 1e-9 or abs(e30 - S.loc[s, "ETH/BTC 30T"]) > 1e-9 or IDX[i] > s
fg = pd.read_sql("select date, fear_greed_value from macro_snapshot where fear_greed_value is not null", sqlite3.connect("file:data/tradinginfotool.db?mode=ro", uri=True), parse_dates=["date"])
for s in S.index[:5]:
    w = fg[fg.date <= s].sort_values("date")
    bad += len(w) and abs(w.groupby("date").fear_greed_value.mean().iloc[-1] - S.loc[s, "Fear&Greed"]) > 1e-9
pruefe("P3", bad == 0, "Zeitpunkttreue an 3 + 5 Signalen, Verstoesse %d" % bad)

sp = ["BTC 90T", "BTC unter Hoch", "ETH/BTC 30T", "Breite", "Funding Alts", "OI Alts 30T", "Fear&Greed", "Netto-Liq 13W", "Stablecoins 30T", "Zins 90T", "Dollar 30T", "S&P 30T", "US10J 30T"]
y = S.Treffer.astype(bool)
X = S[sp].astype(float)
med = X.median()
best = -9
for a, b in itertools.combinations(sp, 2):
    for va in (0, 1):
        for vb in (0, 1):
            ma = (X[a] >= med[a]) if va else (X[a] < med[a])
            mb = (X[b] >= med[b]) if vb else (X[b] < med[b])
            m = ma & mb & X[a].notna() & X[b].notna()
            best = max(best, (m & y).sum() / y.sum() - (m & ~y).sum() / (~y).sum())
mm = re.search(r"bestes Youden (\d\.\d\d)", TXT)
pruefe("P4", mm and abs(best - float(mm.group(1))) < 0.006, "bestes Youden neu %.3f · Ausgabe %s" % (best, mm.group(1) if mm else None))

L = pd.read_csv(os.path.join("data", "_spot", "fb_messung_l.csv"), sep=";", parse_dates=["t"])
ch_ = -L.groupby("t").halten_btc.mean().mean()
mm = re.search(r"halten (\d+) % · mit Mitnahme x3 (\d+) %", TXT)
pruefe("P5", mm and abs(100 * ch_ - float(mm.group(1))) < 0.6, "Kosten halten neu %.1f %% · Ausgabe %s" % (100 * ch_, mm.groups() if mm else None))
print("\n%d von %d gleich" % (ok, n))

# P6 Basisrate eigene Rechnung: Anteil aller Tage (ab Tag 31, bis 45 T vor Ende) mit Rally-Tief in [-10, +45] T; Signalquote; Lift
alle = dom.index[(dom.index >= dom.index[30]) & (dom.index <= dom.index[-1] - pd.Timedelta(days=45))]
treffer_tag = pd.Series([any(-10 <= (t - x).days <= 45 for t in tiefs) for x in alle], index=alle)
b = treffer_tag.mean()
q = np.mean(tr)
mm = re.search(r"BASISRATE: ein beliebiger Tag liegt in (\d+) % .*?Dominanz-Spitze (\d+) % \(Lift (\d\.\d\d)\)", TXT)
pruefe("P6", mm and abs(100 * b - float(mm.group(1))) < 0.6 and abs(100 * q - float(mm.group(2))) < 0.6 and abs(q / b - float(mm.group(3))) < 0.006,
       "Basisrate neu %.1f %% · Signalquote %.1f %% · Lift %.3f · Ausgabe %s" % (100 * b, 100 * q, q / b, mm.groups() if mm else None))
print("%d von %d gleich (mit P6)" % (ok, n))
