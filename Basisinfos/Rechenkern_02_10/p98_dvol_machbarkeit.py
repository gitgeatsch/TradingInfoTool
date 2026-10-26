"""P98 DVOL / ANGSTMASS STUFE 0 - MACHBARKEIT (Voranalyse_DVOL_Angstmass_26_10.md §1, vorab d3ef63b1). Kein Ergebnis, nur Pruefstand.

    python -X utf8 Basisinfos/Rechenkern_02_10/p98_dvol_machbarkeit.py

Zustaende am VORTAG: D1 DVOL im oberen Fuenftel des ROLLENDEN 365-T-Fensters (>= 180 T; Fassung 1b, §2) · D2 Angstpraemie (DVOL - gemessene 30-T-Schwankung,
aufs Jahr in %) im oberen Fuenftel · D3 Fear & Greed < 25 (Atlas-Zustand p75). Teil A: BTC/ETH-Ertrag 7 T / 30 T. Teil B: Tagesmittel
des 24-h-Ertrags der REGEL0-Einstiege (Referenz, Lauf A) unter dem Zustand des Vortags. Orakel, Fehlalarm, Aufloesung wie p91/p96.
Nur lesend (data/_dvol/dvol.csv einmal geladen).
"""
import os
import sys

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
import p91_l2a_voranalyse as P91  # noqa: E402  (setzt Pfad und Arbeitsordner)
import p95_v1_groesse_atr as P95  # noqa: E402

RNG = np.random.default_rng(98)


def dvol():
    d = pd.read_csv(os.path.join("data", "_dvol", "dvol.csv"), sep=";", parse_dates=["tag"])
    return {w.lower(): g.set_index("tag").dvol.asfreq("D") for w, g in d.groupby("waehrung")}


def oben(x):
    # FASSUNG 1b (§2): ROLLENDES Fenster 365 T statt wachsend - die DVOL ist seit 2021 strukturell gefallen (Fassung 1: 1 % an)
    p = x.rolling(365, min_periods=180).rank(pct=True)
    return (p > 0.8).astype(float).where(p.notna())


def zustaende(K, D):
    fg = pd.read_csv(os.path.join("data", "_ra", "p75_zustaende.csv"), sep=None, engine="python")
    fg = pd.Series(fg["Fear & Greed"].to_numpy(), index=pd.to_datetime(fg.iloc[:, 0]))
    Z = {}
    for a in ("btc", "eth"):
        rv = np.log(K[a]).diff().rolling(30, min_periods=25).std() * np.sqrt(365) * 100
        vrp = D[a] - rv.reindex(D[a].index)
        Z[a] = {"D1 DVOL oberes Fuenftel": oben(D[a]).shift(1),
                "D2 Angstpraemie oberes Fuenftel": oben(vrp.dropna()).reindex(D[a].index).shift(1),
                "D3 Fear & Greed < 25": (fg == 1).astype(float).where(fg.notna()).shift(1)}
    return Z


def pruefe(z, y, staerken, rng):
    """-> Anteil an, Strecken, Orakel-Rang, Fehlalarm, Fund je Staerke, X."""
    orakel = (pd.Series(y).rolling(31, center=True, min_periods=10).mean() > 0).astype(int).to_numpy()
    r_o = P91.rang(orakel, y, rng, 300)
    fa = np.mean([P91.rang(P91.permutiere(z, rng), y, rng, 200) >= 0.95 for _ in range(100)])
    fund = {}
    for d in staerken:
        n = 0
        for _ in range(100):
            zp = P91.permutiere(z, rng)
            n += P91.rang(zp, y + d * zp, rng, 200) >= 0.95
        fund[d] = n / 100
    x = next((d for d in staerken if fund[d] >= 0.8), None)
    return z.mean(), len(P91.strecken(z)), r_o, fa, fund, x


def strecken_schleife(z):
    n, vor = 0, None
    for v in z:
        if v != vor:
            n += 1
            vor = v
    return n


def zeile(name, n, res, grenze):
    an, st, ro, fa, fund, x = res
    ok = fa <= 0.05 and x is not None and x <= grenze
    return ok, "%-34s %5d Tage · an %3.0f %% · %4d Strecken · Orakel %.3f · Fehlalarm %3.0f %% · Fund %s · X %s -> %s" % (
        name, n, 100 * an, st, ro, 100 * fa, " ".join("%+.2f:%.0f%%" % (100 * d, 100 * f) for d, f in fund.items()),
        "%.2f Pp" % (100 * x) if x else "keine", "MESSBAR" if ok else "nicht messbar")


def main():
    K = P91.kurse()
    D = dvol()
    Z = zustaende(K, D)
    print("P98 DVOL / ANGSTMASS STUFE 0 · DVOL %s..%s · Zustaende am Vortag\n" % (D["btc"].index[0].date(), D["btc"].index[-1].date()))
    print("TEIL A - Lage BTC/ETH (Ertrag ab Schluss t; Grenze X <= 2 Pp je 7 T):")
    for a in ("btc", "eth"):
        for name, z_all in Z[a].items():
            for h, st_ in ((7, (0.005, 0.01, 0.02, 0.03)), (30, (0.02, 0.04, 0.08))):
                y_all = (K[a].shift(-h) / K[a] - 1)
                tage = y_all.index[y_all.notna()]
                z = z_all.reindex(tage)
                ok = z.notna().to_numpy()
                zz, y = z[ok].astype(int).to_numpy(), y_all.reindex(tage)[ok].to_numpy()
                if len(y) < 365:
                    continue
                assert strecken_schleife(zz) == len(P91.strecken(zz))          # Gegenpruefung Streckenzahl
                res = pruefe(zz, y, st_, RNG)
                _, txt = zeile("%s %s %d T" % (a.upper(), name, h), len(y), res, 0.02 if h == 7 else 9)
                print("  " + txt + ("" if h == 7 else " (30 T: nur Auskunft)"))
    print("\nTEIL B - Umfeld der REGEL0-Einstiege aller Assets (Tagesmittel 24 h; Grenze X <= 0,5 Pp; Zustand BTC-DVOL bzw. F&G):")
    ergebnis_b = {}
    for menge, pfad in P95.MENGEN.items():
        e = P95.handel(pfad)
        tm = e.groupby(e.zeit.dt.normalize()).r.mean()
        for name, z_all in Z["btc"].items():
            z = z_all.reindex(tm.index)
            ok = z.notna().to_numpy()
            zz, y = z[ok].astype(int).to_numpy(), tm[ok].to_numpy()
            assert strecken_schleife(zz) == len(P91.strecken(zz))
            res = pruefe(zz, y, (0.0025, 0.005, 0.01), RNG)
            m, txt = zeile("%s %s" % (menge, name), len(y), res, 0.005)
            ergebnis_b[(menge, name)] = m
            print("  " + txt)
    print("\nTEIL B messbar in BEIDEN Mengen: " + " · ".join(
        "%s %s" % (n.split()[0], "ja" if ergebnis_b[("Referenz", n)] and ergebnis_b[("Lauf A", n)] else "nein") for n in Z["btc"]))


if __name__ == "__main__":
    main()
