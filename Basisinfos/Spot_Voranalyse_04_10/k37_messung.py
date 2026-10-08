"""MESSUNG K-H1 - Momentum-Einstieg je Klasse (Spot §37.2, vorab Commit d6ffd7c) - nur lesend, keine Aufrufe.

    python Basisinfos/Spot_Voranalyse_04_10/k37_messung.py

Signal rs30 oberes Fuenftel je Klasse (H Haupt, M zweite Pruefung), Kauf d+1, Zeitgrenze 30 T, Sperre je Coin; gegen BTC brutto;
Korb je Monat; Bonferroni 0,975; Nullwelt zufaellige Coins derselben Klasse ohne Signal am selben Tag (200); Spiegelprobe; Mindestzahl;
Selbsttest (a) Zufalls-Signal 100 Welten <= 2,5 % / (b) gepflanzt; Kosten getrennt (H 0,72 %, M 1,76 %, S 6,4 % Hin+Rueck).
Teil 0: Vorpruefung §35 (H 1,838 / M 1,050) wird in k37_machbarkeit reproduziert; hier erneut geprueft, Abweichung -> Abbruch.
"""
import os
import sys

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
os.chdir(os.path.dirname(os.path.dirname(HIER)))
import k37_machbarkeit as KM  # noqa: E402
import tc_vorpruefung as T   # noqa: E402

K, IDX, BTCV = T.K, T.IDX, T.BTCV
KF = K.ffill()                                   # Ausstiegskurs: letzter gueltiger Kurs (eingestellt -> letzter Kurs)
RNG = np.random.default_rng(20261037)
KOSTEN = {"H": 0.0072, "M": 0.0176, "S": 0.064}
SCHWELLE = 0.975


def boot(vals, n=2000):
    vals = np.asarray(vals)
    if len(vals) < 2:
        return float("nan")
    bs = []
    for _ in range(n):
        st = RNG.integers(0, max(len(vals) - 2, 1), size=int(np.ceil(len(vals) / 3)))
        bs.append(np.concatenate([vals[k:k + 3] for k in st])[:len(vals)].mean())
    return float(np.mean(np.array(bs) > 0))


def ex(sym, i_kauf, i_aus):
    k0, k1 = K[sym].values[i_kauf], KF[sym].values[i_aus]
    return (k1 / k0) / (BTCV[i_aus] / BTCV[i_kauf]) - 1


def bewerte(E, up, down):
    E = E.copy()
    E["ex"] = [ex(r.sym, r.i_kauf, r.i_aus) for r in E.itertuples()]
    E["lauf"] = [bool(up.iat[r.i_kauf, up.columns.get_loc(r.sym)]) for r in E.itertuples()]
    E["absturz"] = [bool(down.iat[r.i_kauf, down.columns.get_loc(r.sym)]) for r in E.itertuples()]
    E["mon"] = E.signal.dt.to_period("M")
    return E


def korb(E):
    return E.groupby("mon").ex.mean().sort_index()


def kandidaten(E, pct, kl, m, k):
    """je Signaltag: Coins derselben Klasse in der Grundgesamtheit OHNE Signal, mit Kurs am Kauftag."""
    out = {}
    for d in E.signal.unique():
        i = IDX.get_loc(d)
        zeile = (kl.loc[d] == k) & m.loc[d] & ~(pct.loc[d] >= 0.8) & K.iloc[i + 1].notna()
        out[d] = list(zeile.index[zeile.values])
    return out


def null(E, kand, nz=NZ if (NZ := 200) else 200):
    je_tag = E.groupby("signal").size()
    i_k = dict(zip(E.signal, E.i_kauf))
    i_a = dict(zip(E.signal, E.i_aus))
    mon = {d: d.to_period("M") for d in je_tag.index}
    vorrat = {d: np.array([ex(s, i_k[d], i_a[d]) for s in kand[d]]) for d in je_tag.index}
    out = []
    for _ in range(nz):
        werte = {}
        for d, n in je_tag.items():
            v = vorrat[d]
            if not len(v):
                continue
            werte.setdefault(mon[d], []).extend(RNG.choice(v, size=n, replace=len(v) < n))
        out.append(np.mean([np.mean(x) for x in werte.values()]))
    return np.array(out), vorrat


def spiegel(E, kand, up, down):
    lauf_n = abst_n = gew = 0.0
    for d, g in E.groupby("signal"):
        i = E.loc[g.index[0], "i_kauf"]
        ks = kand[d]
        if not ks:
            continue
        cols = [up.columns.get_loc(s) for s in ks]
        lauf_n += len(g) * up.iloc[i, cols].astype(float).mean()
        abst_n += len(g) * down.iloc[i, cols].astype(float).mean()
        gew += len(g)
    re = E.lauf.mean() / max(E.absturz.mean(), 1e-9)
    rn = (lauf_n / gew) / max(abst_n / gew, 1e-9)
    return re / rn, E.lauf.mean(), E.absturz.mean(), lauf_n / gew, abst_n / gew


def urteil(E, kand, up, down, nz=200):
    jk = korb(E)
    b = boot(jk.values)
    nl, _ = null(E, kand, nz)
    rang = float(np.mean(nl < jk.mean()))
    sp = spiegel(E, kand, up, down)
    genug = len(E) >= 20 and E.mon.nunique() >= 6
    if not genug:
        u = "NICHT ENTSCHEIDBAR"
    elif jk.mean() > 0 and b >= SCHWELLE and rang >= SCHWELLE and sp[0] > 1:
        u = "TRAEGT"
    elif jk.mean() < 0 and b <= 1 - SCHWELLE:
        u = "SCHADET"
    else:
        u = "TRAEGT NICHT"
    return u, jk, b, rang, sp, nl


def main():
    rel, F = T.merkmale()
    up, down, end, fertig = T.ziele(rel)
    m, kl = T.maske()
    m = m & fertig
    def perz(name):
        X = F[name].where(m)
        p = X.rank(axis=1, pct=True)
        p.loc[X.notna().sum(axis=1) < 30] = np.nan
        return p
    pct = perz("rs30")
    w = (IDX >= "2023-01-01") & (IDX <= "2023-12-01")
    soll = {"H": 1.84, "M": 1.05}
    for k in "HM":
        mk = (kl[w] == k) & m[w]
        basis, sel = pct[w].notna() & mk, (pct[w] >= 0.8) & mk
        r = (up[w][sel].stack().mean() / up[w][basis].stack().mean()) / (down[w][sel].stack().mean() / down[w][basis].stack().mean())
        if abs(r - soll[k]) >= 0.02:
            print("TEIL 0 FEHLGESCHLAGEN (%s %.3f statt %.2f) - Abbruch" % (k, r, soll[k])); return
    print("MESSUNG K-H1 (§37.2) · Kurse bis %s\n\nTEIL 0 (R-R11): Vorpruefung §35 reproduziert (H 1,84 / M 1,05) - bestanden\n" % T.M.ENDE.date())
    ab, bis = pd.Timestamp("2024-01-01"), T.M.ENDE
    alle = {}
    for k in ("H", "M"):
        E = bewerte(KM.einstiege(pct, kl, m, k, ab, bis), up, down)
        kand = kandidaten(E, pct, kl, m, k)
        u, jk, b, rang, sp, nl = urteil(E, kand, up, down)
        alle[k] = (E, kand)
        print("K-H1-%s ab 2024: Einstiege %d an %d Monaten (%d Coins) · Korb %+.2f Pp gegen BTC (Median der Monate %+.2f) · Bootstrap %.3f · Rang gegen Nullwelt %.3f "
              "(Nullwelt-Mittel %+.2f Pp) · Spiegel %.2f (Lauf %.0f %% / Absturz %.0f %%, Nullwelt %.0f / %.0f %%)  ->  %s" % (
                  k, len(E), E.mon.nunique(), E.sym.nunique(), 100 * jk.mean(), 100 * jk.median(), b, rang, 100 * nl.mean(), sp[0],
                  100 * sp[1], 100 * sp[2], 100 * sp[3], 100 * sp[4], u))
        print("   nach Kosten (%.2f %% Hin+Rueck): Korb %+.2f Pp -> %s" % (100 * KOSTEN[k], 100 * (jk.mean() - KOSTEN[k]), "LOHNT" if jk.mean() - KOSTEN[k] > 0 else "lohnt nicht"))
    print("\nSELBSTTEST (je Klasse):")
    for k in ("H", "M"):
        E, kand = alle[k]
        je = E.groupby("signal").size()
        fehl = 0
        for _ in range(100):
            z = []
            for d, n in je.items():
                i = IDX.get_loc(d)
                pool = [s for s in kand[d]] + list(E[E.signal == d].sym)
                for s in RNG.choice(pool, size=min(n, len(pool)), replace=False):
                    z.append((d, s, i + 1, i + 31))
            Z = bewerte(pd.DataFrame(z, columns=["signal", "sym", "i_kauf", "i_aus"]), up, down)
            kz = {d: [s for s in kand[d] + list(E[E.signal == d].sym) if s not in set(Z[Z.signal == d].sym)] for d in je.index}
            uz = urteil(Z, kz, up, down, nz=50)
            fehl += uz[0] == "TRAEGT"
        P = E[E.ex >= 0.10]
        up_ = urteil(P, kand, up, down, nz=50)
        print("  %s (a) Zufalls-Signal 100 Welten: Fehlalarm %d %% (Soll <= 2,5 %%) -> %s · (b) gepflanzt (nur Einstiege mit >= +10 %%, n %d): %s" % (
            k, fehl, "bestanden" if fehl <= 2.5 else "NICHT bestanden", len(P), "erkannt" if up_[0] == "TRAEGT" else "NICHT erkannt (%s)" % up_[0]))

    print("\nAUSKUNFT (nach dem Urteil):")
    try:
        import sqlite3
        dom = pd.read_sql("select substr(stunde,1,10) tag, close from btcdom where stunde in (select max(stunde) from btcdom group by substr(stunde,1,10))",
                          sqlite3.connect("file:data/richtung_historie.db?mode=ro", uri=True))
        dom = pd.Series(dom.close.values, index=pd.to_datetime(dom.tag)).sort_index()
        spitze = (dom / dom.shift(30) - 1 >= 0.087)
    except Exception:
        spitze = pd.Series(dtype=bool)
    kat = set(pd.read_csv(os.path.join("data", "_spot", "bitpanda_katalog_krypto_2026-10-08.csv"), sep=";").symbol.str.upper())
    B = pd.Series(BTCV, index=IDX)
    for k in ("H", "M"):
        E, kand = alle[k]
        jahre = " · ".join("%d %+.1f Pp (n %d)" % (j, 100 * korb(g).mean(), len(g)) for j, g in E.groupby(E.signal.dt.year))
        btc = (B / B.shift(90) - 1).reindex(E.signal).values > 0
        lage = "BTC 90T steigt %+.1f Pp (n %d) / faellt %+.1f Pp (n %d)" % (100 * korb(E[btc]).mean(), int(btc.sum()), 100 * korb(E[~btc]).mean(), int((~btc).sum()))
        sp = spitze.reindex(E.signal).fillna(False).values.astype(bool)
        dz = "Dominanz-Spitze %+.1f Pp (n %d) / sonst %+.1f Pp" % (100 * korb(E[sp]).mean() if sp.any() else float("nan"), int(sp.sum()), 100 * korb(E[~sp]).mean())
        top = E.groupby("sym").ex.sum().sort_values(ascending=False).head(5).index
        bp = E[E.sym.isin(kat)]
        print("  %s je Jahr: %s\n    %s · %s\n    Weglassprobe ohne %s: %+.1f Pp · nur Bitpanda-handelbar (n %d): %+.1f Pp" % (
            k, jahre, lage, dz, ",".join(top), 100 * korb(E[~E.sym.isin(top)]).mean(), len(bp), 100 * korb(bp).mean()))
        for halte in (15, 60):
            Eh = bewerte(KM.einstiege(pct, kl, m, k, ab, bis, halte=halte), up, down)
            print("    Zeitgrenze %d T: n %d · Korb %+.1f Pp" % (halte, len(Eh), 100 * korb(Eh).mean()))
        for name in ("umsatz_schub", "hoch90"):
            Ef = bewerte(KM.einstiege(perz(name), kl, m, k, ab, bis), up, down)
            print("    Merkmal %s statt rs30: n %d · Korb %+.1f Pp" % (name, len(Ef), 100 * korb(Ef).mean()))
        E.to_csv(os.path.join("data", "_spot", "k37_messung_%s.csv" % k), sep=";", index=False)
    Es = bewerte(KM.einstiege(pct, kl, m, "S", ab, bis), up, down)
    ks = kandidaten(Es, pct, kl, m, "S")
    us = urteil(Es, ks, up, down, nz=100)
    print("  S (Gegenprobe der Richtung, erwartet: traegt nicht/schadet): n %d · Korb %+.1f Pp · Bootstrap %.3f · Rang %.3f · Spiegel %.2f -> %s" % (
        len(Es), 100 * us[1].mean(), us[2], us[3], us[4][0], us[0]))


if __name__ == "__main__":
    main()
