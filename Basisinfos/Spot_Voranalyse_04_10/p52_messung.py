"""P52 MESSUNG Ordnung x Regime (Spot §52.1, Messplan vorab ec728193) - nur lesend.

    python Basisinfos/Spot_Voranalyse_04_10/p52_messung.py

24 Pruefungen = 2 Auswahlen (oberes/unteres Fuenftel gegen die eigene Zelle) x 2 Zielgroessen (Z1 typische Muenze = mittlerer log-Ertrag,
Z2 Halter-Korb = log des gleichgewichteten einfachen Mittels) x 6 Regimezellen (BTC ueber/unter 200T, BTC 90T steigt/faellt, E2, E3).
Nullwelt: bestaendige Zufallszahl je Coin, Fuenftel je Zelle, 2.000 Ziehungen, p je Seite (c+1)/(n+1). Bonferroni 0,025/24 je Seite.
Interaktion je Regimepaar (Auskunft): Differenz der Abstaende, Schwelle 0,025/6 je Seite.
Selbsttest (a) 200 AR(1)-Merkmale je Coin (rho aus dem echten p9) gegen dieselbe Nullwelt; (b) Pflanzung als Aufloesungskurve.
"""
import os
import sys
import time

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
import s1_messung as S1   # noqa: E402

NZ = 2000
A_B = 0.025 / 24
A_I = 0.025 / 6
REGIME = ["BTC ueber 200T", "BTC unter 200T", "BTC 90T steigt", "BTC 90T faellt", "E2", "E3"]
PAARE = [("BTC ueber 200T", "BTC unter 200T"), ("BTC 90T steigt", "BTC 90T faellt"), ("E2", "E3")]
AUSKUNFT = ["E1"]


class Basis:
    def __init__(self):
        D = pd.read_csv(os.path.join("data", "_spot", "b4_vormessung.csv"), sep=";", parse_dates=["t"])
        D = D[D.p9.notna()].reset_index(drop=True)
        K, _ = S1.lade()
        btc = K["BTC"].ffill()
        s200 = btc.rolling(200).mean()
        tage = pd.DatetimeIndex(sorted(D.t.unique()))
        ueber = pd.Series(btc.reindex(tage).values > s200.reindex(tage).values, index=tage)
        steigt = pd.Series((btc / btc.shift(90)).reindex(tage).values > 1, index=tage)
        self.D = D
        self.cell = D.groupby(["t", "kl"]).ngroup().values
        self.C = self.cell.max() + 1
        ct = D.groupby(self.cell).t.first()
        cep = D.groupby(self.cell).ep.first()
        self.rmask = {}
        for r in REGIME + AUSKUNFT:
            if r == "BTC ueber 200T":
                m = ueber.reindex(ct).values
            elif r == "BTC unter 200T":
                m = ~ueber.reindex(ct).values
            elif r == "BTC 90T steigt":
                m = steigt.reindex(ct).values
            elif r == "BTC 90T faellt":
                m = ~steigt.reindex(ct).values
            else:
                m = (cep == r).values
            self.rmask[r] = m.astype(bool)
        self.ylog = np.log(D.ende.clip(lower=1e-6).values)
        self.ende = D.ende.values.astype(float)
        self.n_cell = np.bincount(self.cell, minlength=self.C)
        self.sym_code = pd.Series(np.arange(D.sym.nunique()), index=D.sym.unique())[D.sym].values
        self.nsym = D.sym.nunique()
        self.t_code = pd.Series(np.arange(len(tage)), index=tage)[D.t].values
        self.ct, self.cep, self.tage, self.btc = ct, cep, tage, btc
        # Rang in der Zelle fuer beliebige Werte: lexsort einmal je Aufruf
        self.order_cell = None

    def q_in_zelle(self, v):
        """Perzentil (Rang/Anzahl) von v innerhalb der Zelle, ohne Bindungen."""
        o = np.lexsort((v, self.cell))
        r = np.empty(len(v))
        start = np.concatenate([[0], np.cumsum(self.n_cell)[:-1]])
        pos = np.arange(len(v)) - np.repeat(start, self.n_cell)
        r[o] = (pos + 1) / np.repeat(self.n_cell, self.n_cell)
        return r

    def zell_werte(self, sel, ylog, ende):
        """je Zelle Z1 und Z2 der Auswahl gegen die Zelle (NaN, wenn keine Auswahl in der Zelle)."""
        ns = np.bincount(self.cell, weights=sel, minlength=self.C)
        s1 = np.bincount(self.cell, weights=sel * ylog, minlength=self.C)
        s2 = np.bincount(self.cell, weights=sel * ende, minlength=self.C)
        m1 = np.bincount(self.cell, weights=ylog, minlength=self.C) / self.n_cell
        m2 = np.bincount(self.cell, weights=ende, minlength=self.C) / self.n_cell
        with np.errstate(invalid="ignore", divide="ignore"):
            z1 = s1 / ns - m1
            z2 = np.log(s2 / ns) - np.log(m2)
        z1[ns == 0] = np.nan
        z2[ns == 0] = np.nan
        return z1, z2

    def statistik(self, q, ylog=None, ende=None):
        """dict (auswahl, ziel, regime) -> Abstand, fuer q = Perzentil in der Zelle."""
        ylog = self.ylog if ylog is None else ylog
        ende = self.ende if ende is None else ende
        aus = {}
        for name, sel in (("oben", (q > 0.8).astype(float)), ("unten", (q <= 0.2).astype(float))):
            z1, z2 = self.zell_werte(sel, ylog, ende)
            for zn, z in (("Z1", z1), ("Z2", z2)):
                for r, m in self.rmask.items():
                    aus[(name, zn, r)] = float(np.nanmean(z[m]))
        return aus

    def nullwelt(self, n, rng, ylog=None, ende=None):
        keys, rows = None, []
        for _ in range(n):
            z = rng.random(self.nsym)[self.sym_code]
            st = self.statistik(self.q_in_zelle(z), ylog, ende)
            if keys is None:
                keys = list(st)
            rows.append([st[k] for k in keys])
        return keys, np.array(rows)


def p_seiten(a, null):
    return (np.sum(null >= a) + 1) / (len(null) + 1), (np.sum(null <= a) + 1) / (len(null) + 1)


def urteil(auswahl, p_hoch, p_tief):
    erwartet_hoch = auswahl == "oben"
    if (p_hoch if erwartet_hoch else p_tief) <= A_B:
        return "TRAEGT"
    if (p_tief if erwartet_hoch else p_hoch) <= A_B:
        return "KEHRT UM"
    return "nicht entscheidbar"


def ar1_merkmal(B, rho, rng):
    T = len(B.tage)
    x = np.empty((B.nsym, T))
    x[:, 0] = rng.normal(size=B.nsym)
    e = rng.normal(size=(B.nsym, T))
    for t in range(1, T):
        x[:, t] = rho * x[:, t - 1] + np.sqrt(1 - rho ** 2) * e[:, t]
    return x[B.sym_code, B.t_code]


def main():
    t0 = time.time()
    rng = np.random.default_rng(20261057)
    B = Basis()
    D = B.D
    echt = B.statistik(D.p9.values)
    keys, null = B.nullwelt(NZ, rng)
    print("P52 MESSUNG Ordnung x Regime (§52.1) · Stichtage %s bis %s · %d Anker · %d Zellen · Nullwelt %d bestaendige Ziehungen · Bonferroni %.5f je Seite\n" % (
        D.t.min().date(), D.t.max().date(), len(D), B.C, NZ, A_B))
    print("  %-6s %-3s %-16s %6s | %9s | %-30s | %s" % ("Auswahl", "Z", "Regime", "Zellen", "Abstand", "p hoch / p tief", "Urteil"))
    zaehl = {"TRAEGT": 0, "KEHRT UM": 0, "nicht entscheidbar": 0}
    for j, k in enumerate(keys):
        a = echt[k]
        ph, pt = p_seiten(a, null[:, j])
        ausk = k[2] in AUSKUNFT
        u = urteil(k[0], ph, pt)
        if not ausk:
            zaehl[u] += 1
        print("  %-7s %-3s %-16s %6d | %+7.1f Pp | %.4f / %.4f | %s%s" % (k[0], k[1], k[2], int(B.rmask[k[2]].sum()), 100 * a, ph, pt,
                                                                     "(Auskunft) " if ausk else "", u))
    print("\n  => von 24 Pruefungen: TRAEGT %d · KEHRT UM %d · nicht entscheidbar %d" % (zaehl["TRAEGT"], zaehl["KEHRT UM"], zaehl["nicht entscheidbar"]))

    print("\nINTERAKTION (Auskunft): Unterschied des Abstands zwischen den Zellen eines Regimepaars, zweiseitig, Schwelle %.4f je Seite" % A_I)
    for auswahl in ("oben", "unten"):
        for zn in ("Z1", "Z2"):
            for r1, r2 in PAARE:
                j1, j2 = keys.index((auswahl, zn, r1)), keys.index((auswahl, zn, r2))
                d = echt[(auswahl, zn, r1)] - echt[(auswahl, zn, r2)]
                nd = null[:, j1] - null[:, j2]
                ph, pt = p_seiten(d, nd)
                print("  %-6s %s  %-15s - %-15s %+7.1f Pp · p %.4f / %.4f%s" % (auswahl, zn, r1, r2, 100 * d, ph, pt,
                                                                           "  <-- Regime veraendert die Ordnung" if min(ph, pt) <= A_I else ""))

    print("\nAUSKUNFT NIVEAU (Regime = wie viel): mittlerer 12-M-Ertrag der Zelle je Regime (Dollar, einfach) und BTC")
    zm = np.bincount(B.cell, weights=B.ende, minlength=B.C) / B.n_cell
    bt = pd.Series(D.ende_b.values).groupby(B.cell).first().values
    for r in REGIME + AUSKUNFT:
        m = B.rmask[r]
        print("  %-16s Zellen %3d · Watchlist-Zelle %+6.1f %% · BTC %+6.1f %%" % (r, m.sum(), 100 * (np.mean(zm[m]) - 1), 100 * (np.mean(bt[m]) - 1)))

    # Selbsttest (a)
    sub = D[["sym", "t", "p9"]].sort_values(["sym", "t"])
    vor = sub.groupby("sym").p9.shift(1)
    gleich = sub.t - sub.groupby("sym").t.shift(1) <= pd.Timedelta(days=31)
    rho = float(np.corrcoef(sub.p9[gleich & vor.notna()], vor[gleich & vor.notna()])[0, 1])
    print("\nSELBSTTEST (a): 200 AR(1)-Merkmale je Coin, rho = %.3f (gemessen am echten p9, Monat zu Monat) · gegen dieselbe bestaendige Nullwelt" % rho)
    al_b, al_25, n_t = 0, 0, 0
    for i in range(200):
        st = B.statistik(B.q_in_zelle(ar1_merkmal(B, rho, rng)))
        for j, k in enumerate(keys):
            if k[2] in AUSKUNFT:
                continue
            ph, pt = p_seiten(st[k], null[:, j])
            n_t += 1
            al_b += int(min(ph, pt) <= A_B)
            al_25 += int(min(ph, pt) <= 0.025)
    for name, al, a in (("Bonferroni", al_b, A_B), ("0,025 je Seite", al_25, 0.025)):
        soll = 2 * (np.floor(a * (NZ + 1) - 1) + 1) / (NZ + 1)
        g = n_t * soll + 2 * np.sqrt(n_t * soll * (1 - soll))
        print("  %-15s Fehlalarme %4d von %d (Soll %.1f, Grenze %.1f) %s" % (name, al, n_t, n_t * soll, g, "ok" if al <= g else "UEBER"))

    # Selbsttest (b) Aufloesung
    print("\nSELBSTTEST (b): Pflanzung y_log + beta*sd*z(AR-Merkmal) (Ende entsprechend), 30 Welten je Staerke, Nullwelt je Welt 1.000 Ziehungen; Fund = TRAEGT")
    sd = float(np.std(B.ylog))
    for beta in (0.05, 0.1, 0.2):
        fund = {}
        abst = {}
        for w in range(30):
            x = ar1_merkmal(B, rho, rng)
            zx = (x - x.mean()) / x.std()
            yl = B.ylog + beta * sd * zx
            en = B.ende * np.exp(beta * sd * zx)
            st = B.statistik(B.q_in_zelle(x), yl, en)
            kk, nl = B.nullwelt(1000, rng, yl, en)
            for j, k in enumerate(kk):
                if k[2] not in ("E3", "BTC unter 200T"):
                    continue
                ph, pt = p_seiten(st[k], nl[:, j])
                fund.setdefault(k, []).append(urteil(k[0], ph, pt) == "TRAEGT")
                abst.setdefault(k, []).append(st[k])
        print("  beta %.2f: %s" % (beta, " · ".join("%s %s %s %+5.1f Pp %3.0f %%" % (k[0], k[1], k[2], 100 * np.median(abst[k]), 100 * np.mean(v)) for k, v in fund.items())))
    print("\nLaufzeit %.0f s" % (time.time() - t0))


if __name__ == "__main__":
    main()
