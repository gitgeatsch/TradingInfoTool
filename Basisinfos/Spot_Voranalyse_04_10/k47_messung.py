"""MESSUNG U2/U1 (Spot §46.2, vorab Commit 81bb3ef) - Einstieg je Asset aus Gebuehren-Wachstum (U2 oben, Haupt) und Stablecoins je Kette
(U1 unten). Nur lesend.

    python Basisinfos/Spot_Voranalyse_04_10/k47_messung.py

Einstiege = Ablage k47_einstiege_<h>_U (k47_machbarkeit, Gegenprobe 6/6): Signal d, Kauf d+1, Zeitgrenze 30 T, eine Sperre je Coin.
Zielgroesse gegen BTC brutto (k37_messung.ex, Ausstieg letzter gueltiger Kurs). Korb je Monat, Mittel ueber die Monate.
Nullwelt HAUPT: je (Signaltag, Klasse) gleich viele zufaellige Coins derselben Klasse MIT Merkmal und OHNE Signal, Kurs am Kauftag,
1.000 Ziehungen mit Zuruecklegen. TRAEGT: Korb > 0, Bootstrap (Monate, Bloecke 3, 2.000) >= 0,975, Rang >= 0,975, Spiegel > 1, >= 20 an >= 6 Monaten.
SCHADET: Korb < 0 und Bootstrap <= 0,025. Lohnt: Korb - Kosten der Klasse > 0.
Selbsttest (a) 200 Zufalls-Signale (je Tag und Klasse gleich viele zufaellige Coins MIT Merkmal), je 1.000 Ziehungen: Fehlalarm TRAEGT <= 5 %.
           (b) Aufloesung: Ertraege der Einstiege ersetzt durch Stichprobe des Nullwelt-Vorrats + x Pp, x = 2/5/10, je 50: x = 5 in >= 80 % TRAEGT.
AUSLEGUNG (vor dem Lauf): (a) zieht die Zufalls-Signale ohne Sperre; die Nullwelt eines Zufalls-Signals schliesst dessen eigene Coins aus.
"""
import os
import sys

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
import kp46_vorpruefung as V  # noqa: E402
import k37_messung as K7      # noqa: E402
import k37_machbarkeit as KM  # noqa: E402

T, K, IDX = V.T, V.K, V.IDX
KV, KFV, BT = K.values, K7.KF.values, K7.BTCV
COL = {s: i for i, s in enumerate(K.columns)}
RNG = np.random.default_rng(20261047)
KOSTEN = {"H": 0.0072, "M": 0.0176, "S": 0.064}
HYP = {"U2": ("gebuehr90", "oben"), "U1": ("stab90", "unten")}
NZ = 1000


def exv(c, i, j):
    return (KFV[j, c] / KV[i, c]) / (BT[j] / BT[i]) - 1


class Lage:
    def __init__(self, X, pv, m, kl, up, down):
        self.Xv, self.pv, self.M, self.KL = X.values, pv.values, m.values, kl.values
        self.U, self.D = up.values, down.values

    def vorrat(self, i, k, ausschluss, mit_merkmal=True):
        ok = self.M[i] & (self.KL[i] == k) & ~np.isnan(KV[i + 1])
        if mit_merkmal:
            ok &= ~np.isnan(self.Xv[i])
        ok &= ~ausschluss
        return np.where(ok)[0]


def gruppen(E, lage, mit_merkmal=True, ausschluss_fn=None):
    """je (Signaltag, Klasse): Monat, Anzahl, Vorrats-Ertraege, Vorrats-Lauf/Absturz."""
    G = []
    for (d, k), g in E.groupby(["signal", "kl"]):
        i = IDX.get_loc(d)
        aus = ausschluss_fn(i, g) if ausschluss_fn else (lage.pv[i] >= 0.8)
        aus = np.nan_to_num(aus, nan=0).astype(bool)
        v = lage.vorrat(i, k, aus, mit_merkmal)
        ia = int(g.i_aus.iloc[0])
        G.append(dict(mon=d.to_period("M"), n=len(g), ex=exv(v, i + 1, ia) if len(v) else np.array([]),
                      lauf=lage.U[i + 1, v] if len(v) else np.array([]), abst=lage.D[i + 1, v] if len(v) else np.array([]), idx=g.index.values))
    return G


def null_korb(G, nz, rng):
    S, N = {}, {}
    for g in G:
        if not len(g["ex"]):
            continue
        z = g["ex"][rng.integers(0, len(g["ex"]), size=(nz, g["n"]))]
        S[g["mon"]] = S.get(g["mon"], 0) + z.sum(axis=1)
        N[g["mon"]] = N.get(g["mon"], 0) + g["n"]
    return np.mean([S[mo] / N[mo] for mo in S], axis=0)


def spiegel(E, G):
    la = ab = n = 0.0
    for g in G:
        if len(g["ex"]):
            la += g["n"] * np.nanmean(g["lauf"].astype(float))
            ab += g["n"] * np.nanmean(g["abst"].astype(float))
            n += g["n"]
    re = E.lauf.mean() / max(E.absturz.mean(), 1e-9)
    rn = (la / n) / max(ab / n, 1e-9)
    return re / rn, E.lauf.mean(), E.absturz.mean(), la / n, ab / n


def urteil(E, G, nz=NZ, rng=RNG):
    jk = E.groupby("mon").ex.mean()
    b = K7.boot(jk.values)
    nl = null_korb(G, nz, rng)
    rang = float(np.mean(nl < jk.mean()))
    sp = spiegel(E, G)
    genug = len(E) >= 20 and E.mon.nunique() >= 6
    if genug and jk.mean() > 0 and b >= 0.975 and rang >= 0.975 and sp[0] > 1:
        u = "TRAEGT"
    elif jk.mean() < 0 and b <= 0.025:
        u = "SCHADET"
    elif not genug:
        u = "NICHT ENTSCHEIDBAR"
    else:
        u = "TRAEGT NICHT"
    return u, jk, b, rang, sp, nl


def bewerte(E, up, down):
    E = E.copy()
    c = E.sym.map(COL).values
    E["ex"] = exv(c, E.i_kauf.values, E.i_aus.values)
    E["lauf"] = up.values[E.i_kauf.values, c]
    E["absturz"] = down.values[E.i_kauf.values, c]
    E["mon"] = E.signal.dt.to_period("M")
    return E


def main():
    rel = K.div(T.B, axis=0)
    up, down, end, fertig = T.ziele(rel)
    m, kl = T.maske()
    m = m & fertig
    F = V.merkmale()
    kat = set(pd.read_csv(os.path.join("data", "_spot", "bitpanda_katalog_krypto_2026-10-08.csv"), sep=";").symbol.str.upper())
    print("MESSUNG U2/U1 (§46.2) · Kurse bis %s · Urteil ab 2024 · Nullwelt mit Merkmal, %d Ziehungen\n" % (T.M.ENDE.date(), NZ))
    for h, (name, seite) in HYP.items():
        X = F[name]
        Xm = X.where(m)
        p = Xm.rank(axis=1, pct=True)
        p.loc[Xm.notna().sum(axis=1) < 30] = np.nan
        pv = p if seite == "oben" else 1 - p
        lage = Lage(X, pv, m, kl, up, down)
        E = bewerte(pd.read_csv(os.path.join("data", "_spot", "k47_einstiege_%s_U.csv" % h), sep=";", parse_dates=["signal"]), up, down)
        G = gruppen(E, lage)
        u, jk, b, rang, sp, nl = urteil(E, G)
        klein = sum(g["n"] for g in G if len(g["ex"]) < 5) / len(E)

        # Selbsttest (a)
        fa = 0
        for _ in range(200):
            Z = []
            for g in G:
                d = E.signal[g["idx"][0]]
                i = IDX.get_loc(d)
                k = E.kl[g["idx"][0]]
                pool = lage.vorrat(i, k, np.zeros(len(K.columns), dtype=bool))
                if len(pool) < g["n"]:
                    continue
                pick = RNG.choice(pool, g["n"], replace=False)
                for c in pick:
                    Z.append((d, K.columns[c], k, i + 1, int(E.i_aus[g["idx"][0]])))
            Ez = bewerte(pd.DataFrame(Z, columns=["signal", "sym", "kl", "i_kauf", "i_aus"]), up, down)
            picks = Ez.groupby(["signal", "kl"]).sym.apply(lambda s: set(s.map(COL)))

            def aus_fn(i, g, picks=picks):
                a = np.zeros(len(K.columns), dtype=bool)
                a[list(picks[(g.signal.iloc[0], g.kl.iloc[0])])] = True
                return a
            Gz = gruppen(Ez, lage, ausschluss_fn=aus_fn)
            fa += urteil(Ez, Gz)[0] == "TRAEGT"
        # Selbsttest (b)
        aufl = {}
        for x in (0.02, 0.05, 0.10):
            f = 0
            for _ in range(50):
                Eb = E.copy()
                for g in G:
                    if len(g["ex"]):
                        Eb.loc[g["idx"], "ex"] = RNG.choice(g["ex"], g["n"]) + x
                f += urteil(Eb, G)[0] == "TRAEGT"
            aufl[x] = f / 50
        st_a, st_b = fa / 200 <= 0.05, aufl[0.05] >= 0.80
        gilt = u if (st_a and st_b) else ("nicht entscheidbar - Aufloesung reicht nicht" if not st_b else "Urteil gilt nicht (Selbsttest a)")
        kosten = E.kl.map(KOSTEN).mean()

        print("%s %s %s: Einstiege %d an %d Monaten, %d Coins (H %d · M %d · S %d) · Vorrat < 5 bei %.0f %% der Einstiege" % (
            h, name, seite, len(E), E.mon.nunique(), E.sym.nunique(), (E.kl == "H").sum(), (E.kl == "M").sum(), (E.kl == "S").sum(), 100 * klein))
        print("   Korb gegen BTC %+.2f Pp (Median der Monate %+.2f) · Bootstrap %.3f · Nullwelt mit Merkmal %+.2f Pp, 2,5./97,5. %+.2f / %+.2f · Rang %.3f" % (
            100 * jk.mean(), 100 * jk.median(), b, 100 * nl.mean(), 100 * np.percentile(nl, 2.5), 100 * np.percentile(nl, 97.5), rang))
        print("   Spiegel %.2f (Lauf %.0f %% / Absturz %.0f %%; Nullwelt %.0f / %.0f %%) · nach Kosten (Mittel %.2f %%) %+.2f Pp" % (
            sp[0], 100 * sp[1], 100 * sp[2], 100 * sp[3], 100 * sp[4], 100 * kosten, 100 * (jk.mean() - kosten)))
        print("   SELBSTTEST (a) Fehlalarm TRAEGT %d von 200 (%.1f %%, Soll <= 5 %%) -> %s · (b) Aufloesung +2 Pp %.0f %% · +5 Pp %.0f %% · +10 Pp %.0f %% -> %s" % (
            fa, 100 * fa / 200, "bestanden" if st_a else "NICHT bestanden", 100 * aufl[0.02], 100 * aufl[0.05], 100 * aufl[0.10],
            "reicht" if st_b else "reicht NICHT"))
        print("   => URTEIL %s  =>  GILT: %s" % (u, gilt))

        # Auskunft
        Ga = gruppen(E, lage, mit_merkmal=False)
        na = null_korb(Ga, NZ, RNG)
        print("   AUSKUNFT Nullwelt alle der Klasse %+.2f Pp · Rang %.3f" % (100 * na.mean(), float(np.mean(na < jk.mean()))))
        z = []
        for k in "HMS":
            Ek = E[E.kl == k]
            if len(Ek):
                jkk = Ek.groupby("mon").ex.mean().mean()
                z.append("%s n %d %+.2f Pp (nach Kosten %+.2f)" % (k, len(Ek), 100 * jkk, 100 * (jkk - KOSTEN[k])))
        print("   je Klasse: %s" % " · ".join(z))
        print("   je Jahr: %s" % " · ".join("%d %+.2f Pp (n %d)" % (j, 100 * g.groupby("mon").ex.mean().mean(), len(g)) for j, g in E.groupby(E.signal.dt.year)))
        ohne = jk.drop(jk.idxmax())
        top = E.groupby("sym").ex.sum().sort_values(ascending=False).head(5).index
        print("   ohne den staerksten Monat (%s) %+.2f Pp · Weglassprobe ohne %s %+.2f Pp · nur Bitpanda (n %d) %+.2f Pp" % (
            jk.idxmax(), 100 * ohne.mean(), ",".join(top), 100 * E[~E.sym.isin(top)].groupby("mon").ex.mean().mean(),
            E.sym.isin(kat).sum(), 100 * E[E.sym.isin(kat)].groupby("mon").ex.mean().mean()))
        for hl in (15, 60):
            Eh = bewerte(KM.einstiege_alle(pv, kl, m, pd.Timestamp("2024-01-01"), T.M.ENDE, halte=hl), up, down)
            print("   Zeitgrenze %d T: n %d · %+.2f Pp" % (hl, len(Eh), 100 * Eh.groupby("mon").ex.mean().mean()))
        E.to_csv(os.path.join("data", "_spot", "k47_messung_%s.csv" % h), sep=";", index=False)
        print()


if __name__ == "__main__":
    main()
