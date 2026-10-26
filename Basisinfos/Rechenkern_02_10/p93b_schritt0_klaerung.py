"""P93b KLAERUNG Schritt 0 (26.10.2026): p93 Schritt 0 ergab TRAEGT fuer den 10-Monats-Schnitt, E-126 'traegt nicht' - woran liegt es?

    python -X utf8 Basisinfos/Rechenkern_02_10/p93b_schritt0_klaerung.py

Stufe 1 (R1) wird NICHT angesehen. Gleiche Groesse wie p93 Schritt 0 (Vorsprung an - alle, Folgemonat t+1), variiert wird je EINE Sache:
K1 Nullwelt: Strecken-Permutation (p93) gegen zirkulaere Verschiebung um 12..n-12 Monate (E-126)
K2 Waehrung: USD (p93) gegen EUR (EZB-Kurs aus E-126, data/_spot/ma_eurusd_ezb.csv)
K3 Teil A 2011-05..2016-12 (E-126 verlangte A UND B)
K4 die E-126-Groesse S1 (Mittel der Monate DRAUSSEN < 0?) auf diesem Pruefstand
K5 Selbsttest des Schritt-0-Pruefstands: Fehlalarm auf 200 Zufallsregimen (Strecken-Permutation) mit derselben Struktur
Nur lesend.
"""
import os
import sys

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
import p93_l2a_regime_hebel as P  # noqa: E402  (setzt Pfad und Arbeitsordner)

RNG = np.random.default_rng(931)


def monate(b, von, bis):
    me = b.resample("ME").last()
    stand = me > me.rolling(10).mean()
    t1 = [b.index[b.index.searchsorted(t + pd.Timedelta(days=1))] for t in me.index[:-1]]
    k1 = b.reindex(t1).to_numpy()
    r = pd.Series(k1[1:] / k1[:-1] - 1, index=me.index[:-2])
    s = stand.reindex(r.index)
    ok = (r.index >= pd.Timestamp(von)) & (r.index <= pd.Timestamp(bis)) & me.rolling(10).count().reindex(r.index).eq(10).to_numpy()
    return s[ok].astype(int).to_numpy(), r[ok].to_numpy()


def rang_verschoben(z, y):
    echt = P.vorsprung(z, y)
    nw = np.array([P.vorsprung(np.roll(z, k), y) for k in range(12, len(z) - 11)])
    return float(np.mean(nw < echt)), float(nw.mean())


def main():
    K = P.P91.kurse()
    usd = K.btc.dropna()
    e = pd.read_csv("data/_spot/ma_eurusd_ezb.csv")
    e = e.set_index(pd.to_datetime(e.iloc[:, 0])).iloc[:, -1].astype(float)
    eur = (usd / e.reindex(usd.index).ffill()).dropna()
    print("P93b KLAERUNG SCHRITT 0 · Groesse: Vorsprung an - alle, Ertrag Folgemonat (t+1), Zustand 10-Monats-Schnitt\n")
    for teil, von, bis in (("B 2017-2026", "2016-12-31", "2026-08-31"), ("A 2011-2016", "2011-04-30", "2016-11-30")):
        for wname, b in (("USD", usd), ("EUR", eur)):
            z, y = monate(b, von, bis)
            if len(y) < 24:
                continue
            u = P.urteil(z, y, 3, RNG)
            rv, nv = rang_verschoben(z, y)
            print("Teil %s %s: %d Monate · an %.0f %% · Vorsprung %+.2f Pp · Rang Strecken-Perm. %.3f · Rang zirk. Verschiebung %.3f (Nullpunkt %+.2f) · "
                  "Band [%+.2f; %+.2f] · %s · Monate an %+.1f %% / draussen %+.1f %% (S1: draussen < 0? %s)" % (
                      teil, wname, len(y), 100 * z.mean(), 100 * u["echt"], u["rang"], rv, 100 * nv, 100 * u["lo"], 100 * u["hi"], u["stufe"],
                      100 * y[z == 1].mean(), 100 * y[z == 0].mean(), "ja" if y[z == 0].mean() < 0 else "nein"))
    z, y = monate(usd, "2016-12-31", "2026-08-31")
    fa = sum(P.urteil(P.P91.permutiere(z, RNG), y, 3, RNG, 300, 500)["stufe"] == "TRAEGT" for _ in range(200)) / 200
    print("\nK5 Selbsttest Schritt-0-Pruefstand (Teil B USD): Fehlalarm %.1f %% auf 200 Zufallsregimen (Soll <= 5 %%)" % (100 * fa))


if __name__ == "__main__":
    main()
