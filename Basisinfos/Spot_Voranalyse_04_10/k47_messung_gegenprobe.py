"""MESSUNG U2/U1 (Spot §46.2) - GEGENPROBE mit eigenem Rechenweg. Nur lesend.

    python Basisinfos/Spot_Voranalyse_04_10/k47_messung_gegenprobe.py

  G1 Ertrag gegen BTC je Einstieg aus ROHKURSEN (messdaten-SQL): Kauf = Schluss am Kauftag, Ausstieg = letzter Schluss <= Ausstiegstag
  G2 Korb als eigene Monatsrechnung aus G1 - gegen den Korb der Messung (Ablage k47_messung_<h>.csv)
  G3 Nullwelt ANALYTISCH: je (Tag, Klasse) der Mittelwert des Vorrats (eigene Auswahl: Klasse, Maske, Merkmal da, nicht im Fuenftel,
     Kurs am Kauftag), dann Monatskorb - gegen das Mittel der gezogenen Nullwelt (+-0,15 Pp)
  G4 Lauf/Absturz an 60 zufaelligen Einstiegen aus eigener Relativreihe (Rohkurse) - gegen die Ablage
"""
import os
import re
import sqlite3
import sys

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
import kp46_vorpruefung as V  # noqa: E402
import k37_messung as K7      # noqa: E402

T, K, IDX = V.T, V.K, V.IDX
ERG = []


def pruefe(k, ok, text):
    ERG.append(bool(ok))
    print("%-3s %-10s %s" % (k, "gleich" if ok else "ABWEICHUNG", text))


txt = open(os.path.join(HIER, "k47_messung.txt"), encoding="utf-8").read()
md = sqlite3.connect("file:data/messdaten.db?mode=ro", uri=True)


def schluss(s, d, letzter=False):
    q = ("SELECT close FROM price_history_ohlc WHERE symbol=? AND currency='USD' AND assetklasse='krypto' AND date %s ? ORDER BY date DESC LIMIT 1"
         % ("<=" if letzter else "="))
    r = md.execute(q, (s, d.strftime("%Y-%m-%d"))).fetchone()
    return r[0] if r else np.nan


rel = K.div(T.B, axis=0)
up, down, end, fertig = T.ziele(rel)
m, kl = T.maske()
m = m & fertig
F = V.merkmale()
KV, KFV, BT = K.values, K7.KF.values, K7.BTCV
for h, name, seite in (("U2", "gebuehr90", "oben"), ("U1", "stab90", "unten")):
    E = pd.read_csv(os.path.join("data", "_spot", "k47_messung_%s.csv" % h), sep=";", parse_dates=["signal"])
    ek = IDX[E.i_kauf.values]
    ea = IDX[E.i_aus.values]
    roh = [(schluss(r.sym, a, True) / schluss(r.sym, k)) / (schluss("BTC", a, True) / schluss("BTC", k)) - 1 for r, k, a in zip(E.itertuples(), ek, ea)]
    E["ex2"] = roh
    d = np.nanmax(np.abs(E.ex2 - E.ex))
    pruefe("G1", d < 1e-9 and E.ex2.notna().all(), "%s Ertrag aus Rohkursen an %d Einstiegen, groesste Abweichung %.1e" % (h, len(E), d))
    korb = E.groupby(E.signal.dt.strftime("%Y-%m")).ex2.mean().mean()
    mo = re.search(r"%s %s %s:.*?\n\s+Korb gegen BTC ([+-][\d.]+) Pp" % (h, name, seite), txt)
    soll = float(mo.group(1)) if mo else np.nan
    pruefe("G2", abs(100 * korb - soll) < 0.01, "%s Korb eigene Monatsrechnung %+.2f Pp (Messung %+.2f)" % (h, 100 * korb, soll))
    Xv = F[name].values
    M_, KL = m.values, kl.values
    S, N = {}, {}
    for (sd, k), g in E.groupby(["signal", "kl"]):
        i = IDX.get_loc(sd)
        j = np.where(M_[i] & ~np.isnan(Xv[i]))[0]
        if len(j) < 30:
            continue
        p = pd.Series(Xv[i, j]).rank(pct=True).values
        sig = set(j[p >= 0.8] if seite == "oben" else j[p <= 0.2])
        v = [c for c in j if KL[i, c] == k and c not in sig and not np.isnan(KV[i + 1, c])]
        if not v:
            continue
        ia = int(g.i_aus.iloc[0])
        mu = np.mean([(KFV[ia, c] / KV[i + 1, c]) / (BT[ia] / BT[i + 1]) - 1 for c in v])
        key = sd.strftime("%Y-%m")
        S[key] = S.get(key, 0) + mu * len(g)
        N[key] = N.get(key, 0) + len(g)
    analyt = np.mean([S[x] / N[x] for x in S])
    mo = re.search(r"%s %s %s:.*?\n.*?Nullwelt mit Merkmal ([+-][\d.]+) Pp" % (h, name, seite), txt, re.S)
    soll = float(mo.group(1)) if mo else np.nan
    pruefe("G3", abs(100 * analyt - soll) < 0.15, "%s Nullwelt analytisch %+.2f Pp (gezogen %+.2f)" % (h, 100 * analyt, soll))
    S_ = E.sample(60, random_state=47)
    abw = 0
    for r in S_.itertuples():
        k0 = IDX[r.i_kauf]
        r0 = schluss(r.sym, k0) / schluss("BTC", k0)
        fut = [schluss(r.sym, k0 + pd.Timedelta(days=t)) / schluss("BTC", k0 + pd.Timedelta(days=t)) for t in range(1, 31)]
        abw += (np.nanmax(fut) / r0 >= 1.3) != bool(r.lauf) or (np.nanmin(fut) / r0 <= 1 / 1.3) != bool(r.absturz)
    pruefe("G4", abw == 0, "%s Lauf/Absturz an 60 Einstiegen aus eigener Relativreihe, Abweichungen %d" % (h, abw))
print("\n%d von %d gleich" % (sum(ERG), len(ERG)))
