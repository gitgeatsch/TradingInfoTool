"""P19 GEGENPROBE (Spot §49) - die Zahlen der Voranalyse auf einem ZWEITEN Weg. Nur lesend.

    python Basisinfos/Spot_Voranalyse_04_10/p19_gegenprobe.py <Prod-Sicherung tradinginfotool.db>

  G1  Stufen vektoriell (numpy-Masken) gegen die Schleife p19_voranalyse.stufen - je Tag gleich?
  G2  Haltezeit 7 T als Lauflaengen-Rechnung gegen die Zustandsmaschine aus p19_haltezeit - gleiche Wechsel?
  G3  B1 BTC 91 T aus der Produktion gegen die Messbasis 2026 - Quellen-Unterschied und Wirkung auf die Schwelle (Folge: Bau aus der Kopie)
  G4  Ampel heute: Muster -> Stufe von Hand nach §36.5 (BTC an, M2 an, Stablecoins aus = 'ungewohnt')
"""
import os
import sqlite3
import sys

import numpy as np
import pandas as pd

PROD = os.path.abspath(sys.argv[1])
HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
os.chdir(os.path.dirname(os.path.dirname(HIER)))
import importlib.util  # noqa: E402
spec = importlib.util.spec_from_file_location("p19", os.path.join(HIER, "p19_voranalyse.py"))
P = importlib.util.module_from_spec(spec)
sys.argv = ["x", PROD]
spec.loader.exec_module(P)
ERG = []


def pruefe(k, ok, text):
    ERG.append(bool(ok))
    print("%-3s %-10s %s" % (k, "gleich" if ok else "ABWEICHUNG", text))


Z = pd.read_csv(os.path.join("data", "_spot", "am_kalibrierung.csv"), sep=";", parse_dates=["date"]).set_index("date")
s = P.stufen(Z)
# G1
a1, a2, a3 = (Z.B1 > 0.20).values, (Z.B2 > 0.05).values, (Z.B3 > 0.10).values
alle = a1 & a2 & a3
vor = pd.Series(alle.astype(int), index=Z.index).shift(1).rolling(90, min_periods=1).max().fillna(0).values > 0
v = np.where(alle & (Z.Breite.values >= 0.6), "Ueberhitzung", np.where(alle, "Season-Klima", np.where(vor, "Ende",
             np.where(~a1 & a2 & a3, "Vorlauf", np.where(a1 & a2 & ~a3, "ungewohnt", "kalt")))))
pruefe("G1", (v == s.values).all(), "Stufen vektoriell gegen Schleife: %d von %d Tagen gleich" % (int((v == s.values).sum()), len(s)))
# G2 Lauflaengen: eine Stufe gilt, sobald sie 7 T in Folge besteht
lauf = (s != s.shift(1)).cumsum()
laenge = s.groupby(lauf).transform("size")
pos = s.groupby(lauf).cumcount() + 1
akt, aus = s.iloc[0], []
for st, ln, ps in zip(s, laenge, pos):
    if st != akt and ps >= 7:
        akt = st
    aus.append(akt)
e = pd.Series(aus, index=s.index)
w = int((e != e.shift(1)).iloc[1:].sum())
pruefe("G2", w == 18, "Haltezeit 7 T als Lauflaengen-Rechnung: %d Wechsel (Zustandsmaschine: 18)" % w)
# G3
c = sqlite3.connect("file:%s?mode=ro" % PROD.replace("\\", "/"), uri=True)
pr = pd.read_sql("SELECT date, close FROM price_history_ohlc WHERE symbol='BTC' AND currency='USD' AND COALESCE(quelle,'') != 'rekonstruiert'", c)
c.close()
pr["date"] = pd.to_datetime(pr.date.str[:10])
pr = pr.drop_duplicates("date", keep="last").set_index("date").close.sort_index()
m = sqlite3.connect("file:data/messdaten.db?mode=ro", uri=True)
mb = pd.read_sql("SELECT date, close FROM price_history_ohlc WHERE symbol='BTC' AND assetklasse='krypto' AND currency='USD'", m)
m.close()
mb["date"] = pd.to_datetime(mb.date.str[:10])
mb = mb.set_index("date").close.sort_index()
b1p = (pr / pr.shift(91, freq="D").reindex(pr.index) - 1).loc["2026-01-01":"2026-09-20"]
b1m = (mb / mb.shift(91, freq="D").reindex(mb.index) - 1).loc["2026-01-01":"2026-09-20"]
d = (b1p - b1m).dropna().abs()
an_anders = int(((b1p > 0.20) != (b1m > 0.20)).loc[d.index].sum())
# ⚠️ KORREKTUR 14.10. (erster Lauf rot an MEINER Toleranz 0,01): die Produktion fuehrt BTC aus Kraken (USD), die Messung aus Binance (USDT) -
# die 91-T-Rendite weicht bis 1,2 Pp ab. Entscheidend ist die Schwelle 20 %: an keinem Tag eine andere Seite. FOLGE fuer den Bau: B1 am NB aus der
# BETRIEBSKOPIE (Binance, dieselbe Quelle wie die Messung), nicht aus der Produktion
pruefe("G3", an_anders == 0, "B1 Produktion (Kraken) gegen Messbasis (Binance) 2026: %d Tage, groesste Abweichung %.4f (Quellen-Unterschied), "
       "andere Seite der Schwelle 20 %%: %d -> der Bau nimmt die Betriebskopie" % (len(d), d.max(), an_anders))
# G4
pruefe("G4", P.stufe(0.285, 0.057, 0.015, 0.53, False) == "ungewohnt" and P.stufe(0.10, 0.06, 0.12, 0.3, False) == "Vorlauf"
       and P.stufe(0.25, 0.06, 0.12, 0.3, False) == "Season-Klima" and P.stufe(0.25, 0.06, 0.12, 0.7, False) == "Ueberhitzung"
       and P.stufe(0.05, 0.06, 0.02, 0.3, True) == "Ende", "Muster -> Stufe von Hand nach §36.5 (heute ungewohnt; Vorlauf, Season-Klima, Ueberhitzung, Ende)")
print("\n%d von %d gleich" % (sum(ERG), len(ERG)))
