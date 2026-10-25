"""P91 VORANALYSE L2-a (25.10.2026, Nutzer: *"ja ... L2-a ... starten"*): Regime-Hebel auf dem Kern - MACHBARKEIT, kein Kandidaten-Ergebnis.

    python -X utf8 Basisinfos/Rechenkern_02_10/p91_l2a_voranalyse.py

Kern BTC/ETH Tagesschluss aus CoinMetrics (data/_spot/coinmetrics.db, frei), SOL aus den Binance-Stundenkursen (data/_hist, 23:00). Ziel: Ertrag 7 T (neutral,
ohne Kosten) ab jedem Tag. Je Regime-Kandidat (aus dem bestehenden Schema, keine neue Suche): Anteil 'an', Zahl der Strecken (an/aus-Wechsel)
2015-2026. Aufloesung wie F-1: ORAKEL-Regime (zentrierter kuenftiger 30-T-Mittelwert des 7-T-Ertrags > 0) gegen Strecken-Permutation ->
Rang; dazu Rang eines ZUFALLS-Regimes mit der Streckenstruktur jedes Kandidaten (Fehlalarm-Probe). Der echte Kandidat wird NICHT bewertet.
Nur lesend.
"""
import os
import sqlite3
import sys

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(os.path.dirname(HIER))
sys.path.insert(0, HIER)
sys.path.insert(0, WURZEL)
os.chdir(WURZEL)
sys.stdout.reconfigure(encoding="utf-8")
import warnings  # noqa: E402

warnings.filterwarnings("ignore", category=RuntimeWarning)
RNG = np.random.default_rng(91)


def kurse():
    c = sqlite3.connect("file:data/_spot/coinmetrics.db?mode=ro", uri=True)
    d = pd.read_sql("SELECT asset, tag, PriceUSD FROM tag WHERE asset IN ('btc','eth','sol') AND PriceUSD IS NOT NULL", c, parse_dates=["tag"])
    c.close()
    K = d.pivot(index="tag", columns="asset", values="PriceUSD").asfreq("D")
    # SOL fehlt in coinmetrics.db -> Tagesschluss aus den Binance-Stundenkursen (data/_hist, letzte Stunde des Tages), nur lesend
    h = sqlite3.connect("file:data/_hist/stundenkurse.db?mode=ro", uri=True)
    s = pd.read_sql("SELECT stunde, close FROM stundenkurse WHERE symbol='SOL' AND stunde LIKE '%23:00'", h)
    h.close()
    s.index = pd.to_datetime(s.stunde.str[:10])
    K["sol"] = s.close.reindex(K.index)
    return K


def strecken(z):
    z = np.asarray(z)
    return np.split(z, np.flatnonzero(np.diff(z)) + 1)


def permutiere(z, rng):
    st = strecken(z)
    rng.shuffle(st)
    return np.concatenate(st)


def rang(z, y, rng, k=1000):
    """Vorsprung = Mittel y an 'an'-Tagen minus Mittel y gesamt; Rang gegen Strecken-Permutation."""
    z = z.astype(bool)
    echt = y[z].mean() - y.mean()
    null = np.empty(k)
    for i in range(k):
        zp = permutiere(z, rng).astype(bool)
        null[i] = y[zp].mean() - y.mean()
    return float(np.mean(null < echt))


def kandidaten(K):
    idx = K.index
    btc = K.btc
    Z = pd.DataFrame(index=idx)
    Z["R1 BTC ueber 200-T-Schnitt (Vortag)"] = (btc > btc.rolling(200).mean()).shift(1)
    Z["R2 BTC 91 T > +20 % (Season B1, Vortag)"] = (btc / btc.shift(91) - 1 > 0.20).shift(1)
    import agent.season_ampel as SA
    A = pd.read_csv(os.path.join("data", "_spot", "am_kalibrierung.csv"), sep=";", parse_dates=["date"]).set_index("date")
    st = SA.geltend(SA.stufen(A))
    Z["R3 Season-Ampel nicht kalt (Vortag)"] = (st.reindex(idx).shift(1) != "kalt").where(st.reindex(idx).shift(1).notna())
    E = pd.read_csv(os.path.join("data", "_ra", "p79_e133.csv"), index_col=0, parse_dates=True)
    Z["R4 Makro Gesamt kurz nicht Gegenwind (Vortag)"] = E["F1 Makro Gesamt kurz"].reindex(idx).astype(float)   # dort schon Vortag
    return Z


def main():
    K = kurse()
    print("P91 VORANALYSE L2-a Regime-Hebel Kern · CoinMetrics Tagesschluss: " + " · ".join(
        "%s ab %s" % (a.upper(), K[a].first_valid_index().date()) for a in ("btc", "eth", "sol")) + "\n")
    Z = kandidaten(K)
    for a in ("btc", "eth", "sol"):
        y_all = (K[a].shift(-7) / K[a] - 1)
        ab = max(pd.Timestamp("2015-01-01"), K[a].first_valid_index() + pd.Timedelta(days=200))
        tage = y_all.index[(y_all.index >= ab) & y_all.notna()]
        y = y_all.reindex(tage).to_numpy()
        orakel = (pd.Series(y, index=tage).rolling(31, center=True, min_periods=10).mean() > 0).astype(int).to_numpy()
        r_o = rang(orakel, y, RNG, 1000)
        print("%s 7-T-Ertraege %s..%s (%d Tage) · Orakel-Regime: Anteil an %.0f %%, %d Strecken, Rang %.3f (messbar, wenn >= 0,95)" % (
            a.upper(), tage[0].date(), tage[-1].date(), len(tage), 100 * orakel.mean(), len(strecken(orakel)), r_o))
        for name in Z.columns:
            z = Z[name].reindex(tage)
            ok = z.notna().to_numpy()
            if ok.sum() < 365:
                print("   %-46s zu kurz (%d Tage)" % (name, ok.sum()))
                continue
            zz = z[ok].astype(int).to_numpy()
            yy = y[ok]
            fa = sum(rang(permutiere(zz, RNG), yy, RNG, 200) >= 0.95 for _ in range(100))
            # Orakel auf demselben Zeitraum
            oo = orakel[ok]
            print("   %-46s %s..%s · Anteil an %3.0f %% · %3d Strecken · Fehlalarm Zufallsregime mit dieser Struktur %d %% · Orakel auf dem Zeitraum Rang %.3f" % (
                name, z[ok].index[0].date(), z[ok].index[-1].date(), 100 * zz.mean(), len(strecken(zz)), fa, rang(oo, yy, RNG, 500)))
        print()


if __name__ == "__main__":
    main()
