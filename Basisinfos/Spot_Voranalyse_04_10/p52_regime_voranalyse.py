"""P52 VORANALYSE: Wirkt Auswahl (oberes Fuenftel) und Schutz (unteres Fuenftel) je REGIME? (Spot §52, Nutzer 14.10.) - nur lesend.

    python Basisinfos/Spot_Voranalyse_04_10/p52_regime_voranalyse.py

Nutzer 14.10.: "wie sollen wir statt Gewinner zu finden vor schlechten Assets schuetzen - das ist im Umkehrschluss auch nicht moeglich.
Siehe QNT - war ueber Jahre tot. Mein Hinweis geht in die Regime-Richtung fuer beides."
Daten: data/_spot/b4_vormessung.csv (Monatsstichtage 2019-2025, Wert ohne F9 in Marktwert-Zellen, 12-M-Dollar-Ertrag).
Groesse: Abstand log-Ertrag Fuenftel minus Zelle (je Stichtag x Klasse, gemittelt ueber Zellen). Nullwelt: bestaendige Zufallszahl je Coin.
Regime = zum Stichtag BEKANNT (kein Vorgriff): R-E Epoche E1/E2/E3 · R-T BTC ueber/unter 200-T-Schnitt · R-M BTC 90-T-Ertrag > 0 / <= 0.
VORANALYSE, keine registrierte Messung: viele Zellen -> Mehrfachtest; Aussage nur ueber das MUSTER, nicht ueber Einzelzellen.
"""
import os
import sys

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
import s1_messung as S1   # noqa: E402

RNG = np.random.default_rng(20261056)
NZ = 500


def main():
    D = pd.read_csv(os.path.join("data", "_spot", "b4_vormessung.csv"), sep=";", parse_dates=["t"])
    D = D[D.p9.notna()].reset_index(drop=True)
    K, _ = S1.lade()
    btc = K["BTC"].ffill()
    s200 = btc.rolling(200).mean()
    D["R_T"] = np.where(btc.reindex(D.t).values > s200.reindex(D.t).values, "BTC ueber 200T", "BTC unter 200T")
    m90 = (btc / btc.shift(90)).reindex(D.t).values
    D["R_M"] = np.where(m90 > 1, "BTC 90T steigt", "BTC 90T faellt")
    D["R_E"] = D.ep
    y = np.log(D.ende.clip(lower=1e-6).values)
    zelle = D.groupby(["t", "kl"]).ngroup().values
    zm = pd.Series(y).groupby(zelle).transform("mean").values
    ex = y - zm                                       # Abstand zur eigenen Zelle
    syms = D.sym.unique()
    code = pd.Series(np.arange(len(syms)), index=syms)[D.sym].values

    def abstand(q, maske, oben):
        sel = (q > 0.8) if oben else (q <= 0.2)
        m = maske & sel
        if m.sum() < 20:
            return np.nan
        return float(pd.Series(ex[m]).groupby(zelle[m]).mean().mean())

    nulls = []
    for _ in range(NZ):
        z = RNG.random(len(syms))[code]
        nulls.append(pd.Series(z).groupby(zelle).rank(pct=True).values)

    print("P52 VORANALYSE Regime x Auswahl/Schutz · Stichtage %s bis %s · %d Anker · Nullwelt %d bestaendige Ziehungen\n" % (
        D.t.min().date(), D.t.max().date(), len(D), NZ))
    print("  %-26s %5s | %-44s | %-44s" % ("Regime", "Tage", "OBERES Fuenftel - Zelle (log-Pp), Rang", "UNTERES Fuenftel - Zelle (log-Pp), Rang"))
    zeilen = [("alle", np.ones(len(D), bool))]
    for spalte in ("R_E", "R_T", "R_M"):
        for w in sorted(D[spalte].unique()):
            zeilen.append(("%s" % w, (D[spalte] == w).values))
    zeilen += [("E3 & BTC ueber 200T", ((D.R_E == "E3") & (D.R_T == "BTC ueber 200T")).values),
               ("E3 & BTC unter 200T", ((D.R_E == "E3") & (D.R_T == "BTC unter 200T")).values),
               ("E1+E2 & BTC unter 200T", ((D.R_E != "E3") & (D.R_T == "BTC unter 200T")).values),
               ("E1+E2 & BTC ueber 200T", ((D.R_E != "E3") & (D.R_T == "BTC ueber 200T")).values)]
    for name, m in zeilen:
        teile = []
        for oben in (True, False):
            a = abstand(D.p9.values, m, oben)
            nl = np.array([abstand(q, m, oben) for q in nulls])
            nl = nl[~np.isnan(nl)]
            rang = np.mean(nl < a) if a == a and len(nl) else np.nan
            teile.append("%+7.1f · Rang %.3f (Zufall 2,5/97,5 %+6.1f/%+6.1f)" % (100 * a, rang, 100 * np.percentile(nl, 2.5), 100 * np.percentile(nl, 97.5)) if a == a else "   -")
        print("  %-26s %5d | %-44s | %-44s" % (name, D.t[m].nunique(), teile[0], teile[1]))
    print("\nLesart: oberes Fuenftel Rang >= 0,975 = Auswahl wirkt · unteres Fuenftel Rang <= 0,025 = Schutz wirkt (die Schwachen sind sicher schwaecher).")


if __name__ == "__main__":
    main()
