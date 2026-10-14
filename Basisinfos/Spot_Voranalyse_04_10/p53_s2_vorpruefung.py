"""P53 VORPRUEFUNG S2 Angebot (Spot §53.2, Plan vorab b4aec894) - nur lesend.

    python Basisinfos/Spot_Voranalyse_04_10/p53_s2_vorpruefung.py

Merkmal: 90-T-Angebotswachstum log(Free Float t / t-90) aus data/umlaufmenge_cg.db (CoinGecko Marktwert/Preis, urteil 'ok').
Ziel: 90-T-log-Ertrag ab t+1 (data/messdaten.db, USD) gegen die eigene Zelle (Stichtag x Marktwert-Drittel).
Stichtage 01/2026 bis 06/2026. Ohne BTC, ETH und Stablecoins.
Oberes Fuenftel = staerkste Verwaesserung (erwartet schlechter), unteres = geringste (erwartet besser); zweiseitig.
Nullwelt: bestaendige Zufallszahl je Coin, 2.000 Ziehungen. Weiter, wenn p <= 0,10 und Vorzeichen in >= 4 von 6 Stichtagen gleich.
Auskunft: Sprungtage (Angebot >= +5 % an einem Tag in den 90 T davor).
"""
import os
import sqlite3
import sys

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
import s1_messung as S1   # noqa: E402

RNG = np.random.default_rng(20261058)
NZ = 2000
STICH = pd.date_range("2026-01-01", "2026-06-01", freq="MS")


def lade():
    c = sqlite3.connect("file:data/umlaufmenge_cg.db?mode=ro", uri=True)
    ok = pd.read_sql("SELECT symbol FROM abruf_symbol WHERE urteil='ok'", c).symbol
    u = pd.read_sql("SELECT symbol, datum, wert FROM umlaufmenge", c, parse_dates=["datum"])
    c.close()
    u = u[u.symbol.isin(ok)]
    S = u.pivot(index="datum", columns="symbol", values="wert").sort_index().asfreq("D")
    K, _ = S1.lade()
    K = K.loc["2025-06-01":]
    return S, K


def main():
    S, K = lade()
    ret = K.pct_change(fill_method=None)
    stable = {s for s in K.columns if ret[s].abs().median() < 0.002}
    syms = [s for s in S.columns if s in K.columns and s not in stable and s not in ("BTC", "ETH")]
    Sf = S[syms].ffill(limit=3)
    Kf = K[syms].ffill(limit=3)
    zeilen = []
    for t in STICH:
        s0, s1 = Sf.loc[t - pd.Timedelta(days=90)], Sf.loc[t]
        g = np.log(s1 / s0)
        tag = Sf.loc[t - pd.Timedelta(days=90):t].pct_change(fill_method=None)
        sprung = (tag >= 0.05).sum()
        p0, p1 = Kf.loc[t + pd.Timedelta(days=1)], Kf.loc[t + pd.Timedelta(days=91)]
        y = np.log(p1 / p0)
        mw = s1 * Kf.loc[t]
        d = pd.DataFrame(dict(t=t, sym=syms, g=g.values, sprung=sprung.values, y=y.values, mw=mw.values)).dropna()
        d = d[np.isfinite(d.g) & np.isfinite(d.y)]
        d["kl"] = pd.qcut(d.mw.rank(method="first"), 3, labels=["S", "M", "H"]).astype(str)
        zeilen.append(d)
    D = pd.concat(zeilen, ignore_index=True)
    D["cell"] = D.groupby(["t", "kl"]).ngroup()
    D["q"] = D.groupby("cell").g.rank(pct=True, method="average")
    code = pd.Series(np.arange(D.sym.nunique()), index=D.sym.unique())[D.sym].values
    cell = D.cell.values
    C = cell.max() + 1
    ncell = np.bincount(cell, minlength=C)
    y = D.y.values
    m_cell = np.bincount(cell, weights=y, minlength=C) / ncell
    t_cell = D.groupby("cell").t.first().values

    def abstand(q, oben):
        sel = (q > 0.8) if oben else (q <= 0.2)
        ns = np.bincount(cell, weights=sel, minlength=C)
        z = np.bincount(cell, weights=sel * y, minlength=C) / np.maximum(ns, 1) - m_cell
        z[ns == 0] = np.nan
        return float(np.nanmean(z)), z

    def q_zufall():
        z = RNG.random(code.max() + 1)[code]
        return pd.Series(z).groupby(cell).rank(pct=True).values

    nulls = {True: [], False: []}
    for _ in range(NZ):
        q = q_zufall()
        for oben in (True, False):
            nulls[oben].append(abstand(q, oben)[0])
    print("P53 VORPRUEFUNG S2 Angebot · Stichtage %s bis %s · %d Coins x Stichtag · %d verschiedene Coins · Nullwelt %d bestaendige Ziehungen\n" % (
        STICH[0].date(), STICH[-1].date(), len(D), D.sym.nunique(), NZ))
    print("  Angebotswachstum 90 T: Median %+.1f %% · oberes Fuenftel ab %+.1f %% · Anteil mit Sprungtag %.0f %%" % (
        100 * np.expm1(D.g.median()), 100 * np.expm1(D.g.quantile(0.8)), 100 * (D.sprung > 0).mean()))
    weiter = []
    for oben, name, erwartet in ((True, "OBERES Fuenftel (staerkste Verwaesserung)", -1), (False, "UNTERES Fuenftel (geringste Verwaesserung)", +1)):
        a, z = abstand(D.q.values, oben)
        nl = np.array(nulls[oben])
        p_hoch = (np.sum(nl >= a) + 1) / (NZ + 1)
        p_tief = (np.sum(nl <= a) + 1) / (NZ + 1)
        je = pd.Series(z).groupby(t_cell).mean()
        vz = int((np.sign(je) == np.sign(a)).sum())
        p_erw = p_tief if erwartet < 0 else p_hoch
        print("  %-44s Abstand %+6.1f log-Pp gg. Zelle · p hoch %.4f / tief %.4f · gleiches Vorzeichen %d von %d Stichtagen · je Stichtag %s" % (
            name, 100 * a, p_hoch, p_tief, vz, len(je), " ".join("%+.0f" % (100 * v) for v in je.values)))
        if min(p_hoch, p_tief) <= 0.10 and vz >= 4:
            weiter.append("%s %+.1f Pp (p %.3f, %s erwartet)" % (name, 100 * a, min(p_hoch, p_tief), "wie" if np.sign(a) == erwartet else "GEGEN"))
    # Auskunft Sprungtage
    mit = D.sprung.values > 0
    zs = pd.DataFrame(dict(cell=cell, y=y, mit=mit))
    ab = zs.groupby("cell").apply(lambda g: g.y[g.mit].mean() - g.y.mean() if g.mit.any() else np.nan).mean()
    print("\n  AUSKUNFT Sprungtage: Coins mit >= 1 Tag Angebot +5 %% in den 90 T davor: %d · Abstand gg. Zelle %+.1f log-Pp" % (mit.sum(), 100 * ab))
    # Pruefung 1: Selbsttest - AR(1)-Merkmale mit der Traegheit des echten Rangs gegen dieselbe bestaendige Nullwelt
    piv = D.pivot_table(index="sym", columns="t", values="q")
    a_, b_ = piv.iloc[:, :-1].values.ravel(), piv.iloc[:, 1:].values.ravel()
    okk = ~np.isnan(a_) & ~np.isnan(b_)
    rho = float(np.corrcoef(a_[okk], b_[okk])[0, 1])
    tix = pd.Series(np.arange(len(STICH)), index=STICH)[D.t].values
    al, al_b = 0, 0
    for _ in range(200):
        x = np.empty((code.max() + 1, len(STICH)))
        x[:, 0] = RNG.normal(size=x.shape[0])
        for k in range(1, len(STICH)):
            x[:, k] = rho * x[:, k - 1] + np.sqrt(1 - rho ** 2) * RNG.normal(size=x.shape[0])
        q = pd.Series(x[code, tix]).groupby(cell).rank(pct=True).values
        for oben in (True, False):
            a = abstand(q, oben)[0]
            nl = np.array(nulls[oben])
            p = min((np.sum(nl >= a) + 1), (np.sum(nl <= a) + 1)) / (NZ + 1)
            al += int(p <= 0.05)
            al_b += int(p <= 0.0025)
    print("\n  SELBSTTEST: 200 AR(1)-Merkmale (rho %.3f = Monatstraegheit des echten Rangs), 400 Pruefungen: p <= 0,05 je Seite %d (Soll 40, Grenze 52)"
          " / p <= 0,0025 %d (Soll 2, Grenze 4,8) -> %s" % (rho, al, al_b, "bestanden" if al <= 52 and al_b <= 4.8 else "NICHT bestanden"))
    # Pruefung 2: Ist es nur das ALTER? (junge Token geben am meisten aus) - Effekt innerhalb von Alters-Dritteln
    K0, _ = S1.lade()
    erst = K0[syms].apply(lambda s: s.first_valid_index())
    D["alter"] = (D.t - D.sym.map(erst)).dt.days
    D["ad"] = D.groupby("t").alter.transform(lambda a: pd.qcut(a.rank(method="first"), 3, labels=["jung", "mittel", "alt"])).astype(str)
    print("  ALTER: Spearman Angebotswachstum ~ Alter %+.2f (je Stichtag gemittelt; Alter ab erstem Kurs in messdaten, fruehestens 2018-09)"
          % D.groupby("t").apply(lambda g: g.g.corr(g.alter, method="spearman")).mean())
    for ad in ("jung", "mittel", "alt"):
        g = D[D.ad == ad].copy()
        g["c2"] = g.groupby(["t", "kl"]).ngroup()
        g["q2"] = g.groupby("c2").g.rank(pct=True)
        mc = g.groupby("c2").y.transform("mean")
        o = (g.y - mc)[g.q2 > 0.8].groupby(g.c2[g.q2 > 0.8]).mean().mean()
        u = (g.y - mc)[g.q2 <= 0.2].groupby(g.c2[g.q2 <= 0.2]).mean().mean()
        print("    %-6s n %4d / Alter Median %4d T / oberes Fuenftel %+6.1f / unteres %+6.1f log-Pp gg. Zelle (Zelle = Stichtag x Klasse x Altersdrittel)" % (
            ad, len(g), g.alter.median(), 100 * o, 100 * u))
    # Pruefung 3: Ist es nur die vergangene KURSBEWEGUNG? (Menge = Marktwert / Preis - ein Rechenartefakt waere an den Kurs gekoppelt)
    D["vor"] = [np.log(Kf.at[t, s] / Kf.at[t - pd.Timedelta(days=90), s]) for t, s in zip(D.t, D.sym)]
    print("  KURS: Spearman Angebotswachstum ~ Kursertrag der 90 T davor %+.2f (je Stichtag gemittelt)"
          % D.groupby("t").apply(lambda g: g.g.corr(g.vor, method="spearman")).mean())
    D["md"] = D.groupby("t").vor.transform(lambda a: pd.qcut(a.rank(method="first"), 3, labels=["fiel", "mitte", "stieg"])).astype(str)
    for md in ("fiel", "mitte", "stieg"):
        g = D[D.md == md].copy()
        g["c2"] = g.groupby(["t", "kl"]).ngroup()
        g["q2"] = g.groupby("c2").g.rank(pct=True)
        mc = g.groupby("c2").y.transform("mean")
        o = (g.y - mc)[g.q2 > 0.8].groupby(g.c2[g.q2 > 0.8]).mean().mean()
        u = (g.y - mc)[g.q2 <= 0.2].groupby(g.c2[g.q2 <= 0.2]).mean().mean()
        print("    Kurs 90 T davor %-5s n %4d / oberes Fuenftel %+6.1f / unteres %+6.1f log-Pp gg. Zelle (Zelle = Stichtag x Klasse x Kursdrittel)" % (
            md, len(g), 100 * o, 100 * u))
    print("\nENTSCHEIDUNG Vorpruefung (§53.2): %s" % ("WEITER - " + "; ".join(weiter) + " -> volle Messung erst bei ausreichender Datenlage (ab 10/2027)"
                                                 if weiter else "KEINE Auswahl erfuellt die Bedingung -> Bericht"))


if __name__ == "__main__":
    main()
