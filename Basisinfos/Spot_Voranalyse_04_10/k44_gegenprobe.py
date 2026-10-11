"""K-1/K-2 H-DM (Spot §44) - GEGENPROBE mit eigenem Rechenweg. Nur lesend.

    python Basisinfos/Spot_Voranalyse_04_10/k44_gegenprobe.py

  G1 Spitzen-Tage im Fenster 2023-01-01..2023-12-01 aus eigenem SQL (Datum - 30 T statt Zeilenversatz): 73 in 7 Episoden
  G2 Einstiege 2023 gleich der Ablage k37_einstiege_H_W (Signal, Coin, Kauf, Ausstieg)
  G3 Ertrag gegen BTC aus ROHKURSEN (messdaten): Kauf = Schluss Signal + 1 T, Ausstieg = letzter Schluss <= Signal + 31 T
  G4 Korb je Monat selbst gerechnet: Spitze +4,09 / uebrige -1,15 Pp
  G5 Zeitverschiebung VOLLSTAENDIG (jeder Versatz 30..305 einmal, kein Zufall): Rang gegen 0,792 (+-0,03)
"""
import os
import sqlite3
from datetime import timedelta

import numpy as np
import pandas as pd

os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
ERG = []


def pruefe(k, ok, text):
    ERG.append(bool(ok))
    print("%-3s %-10s %s" % (k, "gleich" if ok else "ABWEICHUNG", text))


c = sqlite3.connect("file:data/richtung_historie.db?mode=ro", uri=True)
sch = {}
for st, cl in c.execute("SELECT stunde, close FROM btcdom ORDER BY stunde"):
    sch[st[:10]] = cl
tage = pd.date_range("2023-01-01", "2023-12-01", freq="D")
reihe = np.array([(lambda d, v: v in sch and d in sch and sch[d] / sch[v] - 1 >= 0.087)(
    t.strftime("%Y-%m-%d"), (t - timedelta(days=30)).strftime("%Y-%m-%d")) for t in tage])
ep = int(np.sum(reihe[1:] & ~reihe[:-1]) + reihe[0])
pruefe("G1", reihe.sum() == 73 and ep == 7, "Spitzen-Tage %d in %d Episoden (Messung 73 / 7)" % (reihe.sum(), ep))

E = pd.read_csv("data/_spot/k44_einstiege_2023.csv", sep=";", parse_dates=["signal"])
W = pd.read_csv("data/_spot/k37_einstiege_H_W.csv", sep=";", parse_dates=["signal"])
gleich = (E[["signal", "sym", "i_kauf", "i_aus"]].sort_values(["signal", "sym"]).reset_index(drop=True)
          .equals(W[["signal", "sym", "i_kauf", "i_aus"]].sort_values(["signal", "sym"]).reset_index(drop=True)))
pruefe("G2", gleich and len(E) == 114, "Einstiege %d, gleich der Ablage: %s" % (len(E), gleich))

md = sqlite3.connect("file:data/messdaten.db?mode=ro", uri=True)


def schluss(sym, d, letzter=False):
    if letzter:
        r = md.execute("SELECT close FROM price_history_ohlc WHERE symbol=? AND currency='USD' AND assetklasse='krypto' AND date <= ? "
                       "ORDER BY date DESC LIMIT 1", (sym, d)).fetchone()
    else:
        r = md.execute("SELECT close FROM price_history_ohlc WHERE symbol=? AND currency='USD' AND assetklasse='krypto' AND date = ?", (sym, d)).fetchone()
    return r[0] if r else np.nan


ex = []
for r in E.itertuples():
    k = (r.signal + timedelta(days=1)).strftime("%Y-%m-%d")
    a = (r.signal + timedelta(days=31)).strftime("%Y-%m-%d")
    ex.append((schluss(r.sym, a, True) / schluss(r.sym, k)) / (schluss("BTC", a, True) / schluss("BTC", k)) - 1)
E["ex2"] = ex
d = np.nanmax(np.abs(E.ex2 - E.ex))
pruefe("G3", d < 1e-9 and E.ex2.notna().all(), "Ertrag aus Rohkursen an %d Einstiegen, groesste Abweichung %.1e" % (len(E), d))

pos = {t: i for i, t in enumerate(tage)}
ip = np.array([pos[t] for t in E.signal])
E["mon2"] = E.signal.dt.strftime("%Y-%m")


def korb(F):
    return F.groupby("mon2").ex2.mean().mean()


def abstand(r):
    s = r[ip]
    return korb(E[s]) - korb(E[~s])


sp = reihe[ip]
ks, ku = korb(E[sp]), korb(E[~sp])
pruefe("G4", abs(100 * ks - 4.09) < 0.01 and abs(100 * ku + 1.15) < 0.01 and (sp == E.spitze.values).all(),
       "Korb Spitze %+.2f / uebrige %+.2f Pp (Messung +4,09 / -1,15)" % (100 * ks, 100 * ku))
a = abstand(reihe)
nl = np.array([abstand(np.roll(reihe, o)) for o in range(30, len(tage) - 30 + 1)])
rang = float(np.mean(nl < a))
pruefe("G5", abs(rang - 0.792) <= 0.03, "Zeitverschiebung vollstaendig (%d Versaetze): Abstand %+.2f Pp · Rang %.3f (Messung 0,792) · 2,5./97,5. %+.2f / %+.2f" % (
    len(nl), 100 * a, rang, 100 * np.percentile(nl, 2.5), 100 * np.percentile(nl, 97.5)))
print("\n%d von %d gleich" % (sum(ERG), len(ERG)))
