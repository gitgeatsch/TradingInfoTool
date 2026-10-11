"""Stufe-1-Vorpruefung U1-U5 (Spot §45.5) - GEGENPROBE mit eigenem Rechenweg. Nur lesend.

    python Basisinfos/Spot_Voranalyse_04_10/kp46_gegenprobe.py

  G1 Merkmalswerte an je 25 zufaelligen Coin-Tagen (stab90, gebuehr90, mvrv, korr90) direkt aus den ROHQUELLEN per SQL und eigener Rechnung
  G2 Lauf/Absturz an denselben Coin-Tagen mit eigener Schleife aus Rohkursen (messdaten): max/min Coin/BTC in d+1..d+30 gegen d
  G3 Richtung der beiden Kandidaten (gebuehr90 oben, stab90 unten) mit eigener Tagesschleife: eigenes Perzentil, eigene Lifts
     - gegen die Werte der Vorpruefung (1,25 / 1,29, +-0,01)
"""
import os
import random
import sqlite3
import sys
from datetime import timedelta

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
import kp46_vorpruefung as V  # noqa: E402

T, K, IDX = V.T, V.K, V.IDX
random.seed(46)
ERG = []


def pruefe(k, ok, text):
    ERG.append(bool(ok))
    print("%-3s %-10s %s" % (k, "gleich" if ok else "ABWEICHUNG", text))


F = V.merkmale()
rel = K.div(T.B, axis=0)
up, down, end, fertig = T.ziele(rel)
m, kl = T.maske()
m = m & fertig
w = (IDX >= "2023-01-01") & (IDX <= "2023-12-01")
md = sqlite3.connect("file:data/messdaten.db?mode=ro", uri=True)


def kurs(s, d):
    r = md.execute("SELECT close FROM price_history_ohlc WHERE symbol=? AND currency='USD' AND assetklasse='krypto' AND date=?", (s, d.strftime("%Y-%m-%d"))).fetchone()
    return r[0] if r else np.nan


def roh(db, sql, *a):
    r = sqlite3.connect("file:%s?mode=ro" % db, uri=True).execute(sql, a).fetchone()
    return r[0] if r and r[0] is not None else np.nan


def mittel30(db, tab, s, d):
    """30-T-Mittel der Tagessummen bis einschliesslich d (wie rolling(30) auf der Tagesreihe, Luecken = fehlend)."""
    c = sqlite3.connect("file:%s?mode=ro" % db, uri=True)
    z = c.execute("SELECT datum, SUM(usd) FROM %s WHERE symbol=? AND datum > ? AND datum <= ? GROUP BY datum" % tab,
                  (s, (d - timedelta(days=30)).strftime("%Y-%m-%d"), d.strftime("%Y-%m-%d"))).fetchall()
    return np.mean([v for _, v in z]) if len(z) >= 20 else np.nan


def eigen(name, s, d):
    lk = np.log(kurs(s, d) / kurs(s, d - timedelta(days=90)))
    if name == "stab90":
        a = roh("data/_spot/stablecoins_kette.db", "SELECT SUM(usd) FROM bestand WHERE symbol=? AND datum=?", s, (d - timedelta(days=1)).strftime("%Y-%m-%d"))
        b = roh("data/_spot/stablecoins_kette.db", "SELECT SUM(usd) FROM bestand WHERE symbol=? AND datum=?", s, (d - timedelta(days=91)).strftime("%Y-%m-%d"))
        return np.log(a / b) - lk if a > 0 and b > 0 else np.nan
    if name == "gebuehr90":
        a, b = mittel30("data/_spot/gebuehren.db", "gebuehr", s, d - timedelta(days=1)), mittel30("data/_spot/gebuehren.db", "gebuehr", s, d - timedelta(days=91))
        return np.log(a / b) - lk if a > 0 and b > 0 else np.nan
    if name == "mvrv":
        return roh("data/_spot/coinmetrics_alt.db", "SELECT wert FROM mvrv WHERE symbol=? AND datum=?", s, (d - timedelta(days=1)).strftime("%Y-%m-%d"))
    if name == "korr90":
        tage = [d - timedelta(days=i) for i in range(90, -1, -1)]
        x = np.array([kurs(s, t) for t in tage])
        y = np.array([kurs("BTC", t) for t in tage])
        rx, ry = np.diff(np.log(x)), np.diff(np.log(y))
        ok = ~np.isnan(rx) & ~np.isnan(ry)
        return np.corrcoef(rx[ok], ry[ok])[0, 1] if ok.sum() >= 60 else np.nan


# G1 / G2
abw1, abw2, n = [], 0, 0
for name in ("stab90", "gebuehr90", "mvrv", "korr90"):
    X = F[name][w].where(m[w])
    st = X.stack().dropna()                # KORREKTUR 1. Lauf: stack() behaelt hier leere Werte - gezogen wurden Coin-Tage OHNE Merkmal
    for (d, s), v in random.sample(list(st.items()), 25):
        e = eigen(name, s, d)
        if not (abs(e - v) < 1e-6 * max(1, abs(v))):
            abw1.append((name, s, d.date(), v, e))
        r0 = kurs(s, d) / kurs("BTC", d)
        fut = [kurs(s, d + timedelta(days=i)) / kurs("BTC", d + timedelta(days=i)) for i in range(1, 31)]
        lauf, abst = np.nanmax(fut) / r0 >= 1.3, np.nanmin(fut) / r0 <= 1 / 1.3
        abw2 += (lauf != bool(up.at[d, s])) or (abst != bool(down.at[d, s]))
        n += 1
pruefe("G1", not abw1, "Merkmalswerte aus Rohquellen an %d Coin-Tagen, Abweichungen %d %s" % (n, len(abw1), abw1[:3]))
pruefe("G2", abw2 == 0, "Lauf/Absturz aus Rohkursen an %d Coin-Tagen, Abweichungen %d" % (n, abw2))

# G3
U, D_, M_ = up.values, down.values, m.values
for name, seite, soll in (("gebuehr90", "oben", 1.25), ("stab90", "unten", 1.29)):
    Xv = F[name].values
    s_up = s_dn = b_up = b_dn = s_n = b_n = 0
    for i in np.where(w)[0]:
        ok = M_[i] & ~np.isnan(Xv[i])
        j = np.where(ok)[0]
        if len(j) < 30:
            continue
        p = pd.Series(Xv[i, j]).rank(pct=True).values
        sel = j[p >= 0.8] if seite == "oben" else j[p <= 0.2]
        b_up += U[i, j].sum(); b_dn += D_[i, j].sum(); b_n += len(j)
        s_up += U[i, sel].sum(); s_dn += D_[i, sel].sum(); s_n += len(sel)
    r = ((s_up / s_n) / (b_up / b_n)) / ((s_dn / s_n) / (b_dn / b_n))
    pruefe("G3", abs(r - soll) < 0.01, "%s %s: Richtung eigene Tagesschleife %.3f (Vorpruefung %.2f), %d Coin-Tage" % (name, seite, r, soll, s_n))
print("\n%d von %d gleich" % (sum(ERG), len(ERG)))
