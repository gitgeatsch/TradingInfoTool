"""P51 K10 "Vertrauen in Fiat" (Spot §51.9, Messplan vorab 06dc150b) - nur lesend.

    python Basisinfos/Spot_Voranalyse_04_10/p51_k10.py --stufe 1     # Vorpruefung, 200 Surrogate
    python Basisinfos/Spot_Voranalyse_04_10/p51_k10.py --stufe 2     # Messung, 1.000 Surrogate + Selbsttest + Aufloesung

K10a Rest der rollierenden 5-J-Regression log(Gold) ~ DFII10 (nur Vergangenheit); lang Niveau, kurz 3-M-Aenderung.
K10b log(Gold x Dollar-Index) = Gold in den Fremdwaehrungen; lang 52-W-, kurz 13-W-Aenderung.
Nullwelt N2 (R-R14): gemeinsame Phasen-Randomisierung der vier K10-Reihen. Bonferroni ueber 11 Kanaele: 0,025/11 je Seite.
Rechenkern (pruefe, urteil, Surrogate, synthetische Ziele) aus p51_messung_n2.py.
"""
import argparse
import os
import sys
import time

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
import p51_vorpruefung as V   # noqa: E402
import p51_messung_n2 as N    # noqa: E402

A = 0.025 / 11
RNG = np.random.default_rng(20261054)
N.RNG = RNG


def k10_reihen():
    gold = V.taeglich(V.yf_close("GC=F").shift(1, freq="D"))          # Verzug 1 T
    real = V.taeglich(V.fred("DFII10", 1))
    dollar = V.taeglich(V.fred("DTWEXBGS", 1))
    lg = np.log(gold)
    w = V.FENSTER
    mg, mr = lg.rolling(w, min_periods=V.MINDEST).mean(), real.rolling(w, min_periods=V.MINDEST).mean()
    beta = lg.rolling(w, min_periods=V.MINDEST).cov(real) / real.rolling(w, min_periods=V.MINDEST).var()
    rest = lg - (mg + beta * (real - mr))
    welt = lg + np.log(dollar)
    sp = {
        "K10a Gold ueber Realzins lang": (rest, +1),
        "K10a Gold ueber Realzins kurz": (rest - V.vor(rest, 91), +1),
        "K10b Gold in Weltwaehrung lang": (welt - V.vor(welt, 364), +1),
        "K10b Gold in Weltwaehrung kurz": (welt - V.vor(welt, 91), +1),
    }
    return sp, {"gold": gold, "real": real, "dollar": dollar, "beta": beta}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stufe", type=int, default=1)
    stufe = ap.parse_args().stufe
    nz = 200 if stufe == 1 else 1000
    t0 = time.time()
    D = N.eingang()
    Z = {k: v for k, v in D["Z"].items() if k[0] in "TM" and k != "M1 Nasdaq/SPX 90T" and k != "M2 Russell/SPX 90T"}
    sp, roh = k10_reihen()
    start = max(r.first_valid_index() for r, _ in sp.values())
    idx = V.IDX[V.IDX >= start]
    X = pd.DataFrame({n: r.reindex(idx).ffill() for n, (r, _) in sp.items()})
    assert not X.isna().any().any()
    stich = np.where(idx.day == 1)[0]
    sd = idx[stich]
    ep = np.array([V.epoche(d) for d in sd])
    namen = list(sp)
    echt = np.array([V.score(X[n], sp[n][1]).values[stich] for n in namen])
    bank = np.full((nz, len(namen), len(stich)), np.nan, dtype=np.float32)
    for i in range(nz):
        Xs = N.surrogat_matrix(X.values)
        for j, n in enumerate(namen):
            bank[i, j] = V.score(pd.Series(Xs[:, j], index=idx), sp[n][1]).values[stich]
    print("P51 K10 Vertrauen in Fiat · Stufe %d · Zeitraum %s bis %s · %d Stichtage · %d Surrogate (N2) · Bonferroni %.4f je Seite\n"
          % (stufe, idx[0].date(), idx[-1].date(), len(stich), nz, A))
    print("Beta Gold~Realzins (5 J rollierend): 2012 %.2f · 2018 %.2f · 2022-01 %.2f · 2024-01 %.2f · heute %.2f (log-Punkte je Prozentpunkt Realzins)" % tuple(
        roh["beta"][:d].dropna().iloc[-1] for d in ("2012-01-01", "2018-01-01", "2022-01-01", "2024-01-01", str(idx[-1].date()))))
    weiter, urteile = [], []
    for zn, (y, ab) in Z.items():
        rolle = N.ROLLE[zn[0]]
        yv = y.reindex(sd).values.astype(float)
        yv[sd < pd.Timestamp(ab)] = np.nan
        print("=" * 170)
        print("%s  [%s]" % (zn, rolle))
        for j, n in enumerate(namen):
            r = N.pruefe(echt[j], yv, ep, bank[:, j])
            print(N.zeile(n, r, A, rolle))
            if r is None or rolle != "Urteil":
                continue
            p = min(r["p_hoch"], r["p_tief"])
            e3 = r["ep"]["E3"]
            if p <= 0.10 and e3 == e3 and np.sign(e3) == np.sign(r["a"]):
                weiter.append("%s %s %+.1f %% (p %.3f)" % (zn, n, 100 * r["a"], p))
            urteile.append((zn, n, N.urteil(r, A), r))
    print("\n" + "=" * 170)
    if stufe == 1:
        print("ENTSCHEIDUNG Vorpruefung (§51.9): %s" % ("WEITER zur Messung - %s" % "; ".join(weiter) if weiter else
                                                       "KEIN K10-Kanal im aeusseren Zehntel mit E3 gleich -> Bericht, keine lange Messung"))
    else:
        print("URTEILE: " + " · ".join("%s %s -> %s" % (zn, n, u) for zn, n, u, _ in urteile if u in ("TRAEGT", "SCHADET")) or "URTEILE: keines")
        print("  => TRAEGT %d · SCHADET %d · von %d" % (sum(u == "TRAEGT" for *_, u, _ in urteile), sum(u == "SCHADET" for *_, u, _ in urteile), len(urteile)))
        # Selbsttest: echte K10 gegen synthetische Ziele
        ziele_t = {"T1 BTC 90T": ("BTC", 90, "2013-01-01"), "T2 Altkorb/BTC 90T": ("Korb/BTC", 90, "2019-01-01")}
        print("\nSELBSTTEST: echte K10-Reihen gegen 200 synthetische Ziele")
        for zn, (pn, h, ab) in ziele_t.items():
            al, n_t, synth = 0, 0, []
            for i in range(200):
                yv = N.ziel_aus_preis(N.synth_preis(D["preise"][pn]), h, idx).reindex(sd).values.astype(float)
                yv[sd < pd.Timestamp(ab)] = np.nan
                synth.append(yv)
                for j in range(len(namen)):
                    r = N.pruefe(echt[j], yv, ep, bank[:, j])
                    if r and r["a"] == r["a"]:
                        n_t += 1
                        al += int(min(r["p_hoch"], r["p_tief"]) <= 0.025)
            soll = 2 * (np.floor(0.025 * (nz + 1) - 1) + 1) / (nz + 1)
            print("  %-20s Pruefungen %d · Fehlalarm bei 0,025 je Seite %d (Soll %.1f, Grenze %.1f)" % (
                zn, n_t, al, n_t * soll, n_t * soll + 2 * np.sqrt(n_t * soll * (1 - soll))))
            teile = []
            for b in (0.2, 0.3, 0.5):
                f, ab_l = 0, []
                for i, yv in enumerate(synth[:60]):
                    j = int(RNG.integers(len(namen)))
                    x = X[namen[j]].values[stich]
                    zx = (x - np.nanmean(x)) / np.nanstd(x)
                    r = N.pruefe(echt[j], yv + b * np.nanstd(yv) * zx, ep, bank[:, j])
                    if r and r["a"] == r["a"]:
                        ab_l.append(r["a"])
                        f += int(r["p_hoch"] <= A)
                teile.append("beta %.1f: Abstand %+5.1f %% Fund %3.0f %%" % (b, 100 * np.median(ab_l), 100 * f / max(len(ab_l), 1)))
            print("    Aufloesung: " + " · ".join(teile))
    heute = {n: {1.0: "+", -1.0: "-", 0.0: "0"}.get(V.score(X[n], sp[n][1]).dropna().iloc[-1], "?") for n in namen}
    print("\nSTAND HEUTE (%s): %s" % (idx[-1].date(), " · ".join("%s %s" % (n, v) for n, v in heute.items())))
    # Auskunft Euro
    eu = V.fred("DEXUSEU", 0)
    hicp = V.fred("CP0000EZ19M086NEST", 0)
    estr = V.fred("ECBESTRVOLWGTTRMDMNRT", 0)
    g = roh["gold"].dropna()
    ge = (g / eu.reindex(g.index).ffill()).dropna()
    yoy = 100 * (hicp.iloc[-1] / hicp.iloc[-13] - 1)
    print("AUSKUNFT EURO: Gold in Euro %.0f (52 W %+.1f %%) · HICP J/J %.1f %% (%s) · ESTR %.2f %% · Sparer-Realzins ESTR-HICP %+.1f Pp"
          % (ge.iloc[-1], 100 * (ge.iloc[-1] / ge[:ge.index[-1] - pd.Timedelta(days=364)].iloc[-1] - 1), yoy, hicp.index[-1].strftime("%m/%Y"),
             estr.iloc[-1], estr.iloc[-1] - yoy))
    print("Laufzeit %.0f s" % (time.time() - t0))


if __name__ == "__main__":
    main()
