"""Messung L1-L4 (Voranalyse_Spot_Neubau_04_10.md §16.3, vorab Commit 41cb8e0): Liquiditaet und Verwaesserung - nur als GEWICHT.

    python Basisinfos/Spot_Voranalyse_04_10/l_messung.py

Liest FRED (WALCL, WTREGEN, RRPONTSYD; ohne Schluessel) und DefiLlama (Stablecoins) live, sonst nur lesend (mode=ro). Schreibt nichts.

AUSLEGUNG, vor dem ersten Lauf festgelegt:
  - Netto-Liquiditaet = WALCL - WTREGEN - RRPONTSYD (Mittwochswert; RRP taeglich, letzter Wert der Woche). Bekannt ab Freitag (Mittwoch + 2 T).
    Zustand am Tag t = Vorzeichen der 13-W-Aenderung des zuletzt BEKANNTEN Wochenwerts. Verzoegerung 13 W (Auskunft): Zustand von 13 W frueher
  - Zirkulaere Nullwelt: Zustandsreihe der Wochen um k Wochen rotiert, k gleichverteilt in [26, Wochen-26], 200 Ziehungen;
    Rang = Anteil der Ziehungen mit kleinerem Unterschied als dem echten - je Epoche
  - L1/L3 Statistik je Epoche: Tagesklammer-Mittel (Mittel je Einstiegstag, dann Mittel ueber die Tage) Gruppe A minus Gruppe B
  - L1: Klassen H/M/S gepoolt (Ereignis ohne Klasse entfaellt, wie in a3_messung)
  - L3: Umlaufmenge zuerst Coin Metrics (onchain_historie.splycur), sonst CoinGecko (umlaufmenge_cg, nur urteil='ok'); Wert = letzter Wert <= t
    bzw. <= t-180 (hoechstens 7 T alt); Datenfehler = Wachstum > +300 % oder ein Tagessprung > 50 % im Fenster -> ausgeschlossen, gezaehlt.
    Haelften am Median des Wachstums JE EPOCHE; Nullwelt = Wachstum innerhalb der Epoche permutiert (200)
  - L4: BTC-Schluss aus derselben Tabelle wie a2/a3; Folgeertrag = Kauf Schluss t+1, Verkauf Schluss t+181; Klima-Drittel nach q (< 1/3, < 2/3, sonst);
    Zelle braucht >= 30 Tage je Zustand, sonst 'nicht beurteilbar' (= traegt nicht); E3 nur Tage mit vollem Folgefenster
"""
import io
import os
import sqlite3
import sys

import numpy as np
import pandas as pd
import requests

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
import a3_messung as M  # noqa: E402
A = M.A
K, IDX, POS, ENDE = A.K, A.IDX, A.POS, A.ENDE
RNG = np.random.default_rng(20261008)
NZ = 200


def fred(s):
    r = requests.get("https://fred.stlouisfed.org/graph/fredgraph.csv?id=" + s, timeout=60)
    d = pd.read_csv(io.StringIO(r.text)); d.columns = ["datum", s]
    d["datum"] = pd.to_datetime(d["datum"]); d[s] = pd.to_numeric(d[s], errors="coerce")
    return d.set_index("datum")[s].dropna()


def liquiditaet():
    w = pd.concat([fred("WALCL"), fred("WTREGEN"), fred("RRPONTSYD").resample("W-WED").last()], axis=1).dropna()
    netto = (w["WALCL"] - w["WTREGEN"] - w["RRPONTSYD"] * 1000) / 1e6
    zust = (netto / netto.shift(13) - 1 > 0).astype(float).where(netto.shift(13).notna())
    zust = zust.dropna()
    bekannt = zust.index + pd.Timedelta(days=2)
    return netto, zust.values.astype(bool), bekannt


NETTO, ZW, BEKANNT = liquiditaet()


def woche(t):
    """Index der zuletzt bekannten Woche am Tag t (-1, falls keine)."""
    return int(np.searchsorted(BEKANNT.values, np.datetime64(t), side="right")) - 1


def stable():
    j = requests.get("https://stablecoins.llama.fi/stablecoincharts/all", timeout=60).json()
    s = pd.Series({pd.Timestamp(int(x["date"]), unit="s").normalize(): x["totalCirculatingUSD"].get("peggedUSD", 0) for x in j}).sort_index()
    return (s / s.shift(91) - 1 > 0).where(s.shift(91).notna())


def tk(d, maske):
    x = d[maske]
    return x.groupby("einstieg")["vorteil"].mean().mean() if len(x) else np.nan


def ereignisse(art):
    z = []
    for t, s in A.mit_ruhe(A.A1):
        kl = A.klassen(t.replace(day=1))[0].get(s)
        i0 = POS[t] + 1
        if kl not in ("H", "M", "S") or i0 >= len(IDX):
            continue
        e = M.handel3(s, i0, art)
        if e is not None:
            z.append(dict(t=t, sym=s, kl=kl, ep=A.epoche(t), einstieg=IDX[i0], vorteil=e["vorteil"], wi=woche(t)))
    return pd.DataFrame(z)


def unterschied(d, st):
    return tk(d, st) - tk(d, ~st)


# ---------------------------------------------------------------- L1
def L1(art):
    d = ereignisse(art)
    d = d[d["wi"] >= 13].reset_index(drop=True)
    wi = d["wi"].values
    erg, traegt = {}, True
    n = len(ZW)
    ks = RNG.integers(26, n - 26, size=NZ)
    for ep in ("E1", "E2", "E3"):
        x = d[d["ep"] == ep].reset_index(drop=True)
        if len(x) < 10:
            erg[ep] = None; continue
        w = x["wi"].values
        st = ZW[w]
        u = unterschied(x, st)
        nul = np.array([unterschied(x, np.roll(ZW, k)[w]) for k in ks])
        rang = float(np.mean(nul < u))
        lag = ZW[np.maximum(w - 13, 0)]
        kl = {k: unterschied(x[x["kl"] == k], st[x["kl"].values == k]) for k in ("H", "M", "S")}
        erg[ep] = dict(n=len(x), n_st=int(st.sum()), m_st=tk(x, st), m_fa=tk(x, ~st), u=u, rang=rang, u_lag=unterschied(x, lag), kl=kl)
        if ep in ("E2", "E3"):
            traegt &= (u > 0) and (rang >= 0.95)
    for ep in ("E2", "E3"):
        traegt &= erg.get(ep) is not None
    return erg, traegt, d


# ---------------------------------------------------------------- L2 (Auskunft)
def L2(d):
    sc = stable()
    st = sc.reindex(d["t"].values).values
    out = {}
    for ep in ("E2", "E3"):
        m = (d["ep"] == ep).values & ~pd.isna(st)
        x = d[m]; s = st[m].astype(bool)
        out[ep] = (len(x), int(s.sum()), tk(x, s), tk(x, ~s))
    return out


# ---------------------------------------------------------------- L3
def umlauf():
    c = sqlite3.connect("file:data/onchain_historie.db?mode=ro", uri=True)
    cm = pd.read_sql("SELECT symbol, datum, wert FROM splycur", c, parse_dates=["datum"])
    c2 = sqlite3.connect("file:data/umlaufmenge_cg.db?mode=ro", uri=True)
    ok = {s for s, in c2.execute("SELECT symbol FROM abruf_symbol WHERE urteil='ok'")}
    cg = pd.read_sql("SELECT symbol, datum, wert FROM umlaufmenge", c2, parse_dates=["datum"])
    cg = cg[cg["symbol"].isin(ok)]
    return {s: g.set_index("datum")["wert"].sort_index() for s, g in cm.groupby("symbol")}, {s: g.set_index("datum")["wert"].sort_index() for s, g in cg.groupby("symbol")}


CM, CG = umlauf()


def wachstum(sym, t):
    for quelle, q in (("CM", CM), ("CG", CG)):
        r = q.get(sym)
        if r is None:
            continue
        a, b = r[:t], r[:t - pd.Timedelta(days=180)]
        if not len(a) or not len(b) or (t - a.index[-1]).days > 7 or (t - pd.Timedelta(days=180) - b.index[-1]).days > 7:
            continue
        fenster = r[b.index[-1]:a.index[-1]]
        sprung = (fenster / fenster.shift(1) - 1).abs().max()
        g = a.iloc[-1] / b.iloc[-1] - 1
        fehler = (g > 3.0) or (sprung > 0.5) or b.iloc[-1] <= 0
        return g, quelle, fehler
    return None, None, False


def L3(art, d):
    g = [wachstum(s, t) for s, t in zip(d["sym"], d["t"])]
    d = d.assign(g=[x[0] for x in g], q=[x[1] for x in g], fehler=[x[2] for x in g])
    erg, traegt = {}, True
    for ep in ("E2", "E3"):
        x = d[(d["ep"] == ep) & d["g"].notna()]
        fe = int(x["fehler"].sum()); x = x[~x["fehler"]].reset_index(drop=True)
        if len(x) < 20:
            erg[ep] = dict(n=len(x), fehler=fe); traegt = False; continue
        med = x["g"].median()
        nied = (x["g"] <= med).values
        u = unterschied(x, nied)
        nul = []
        for _ in range(NZ):
            p = RNG.permutation(x["g"].values)
            nul.append(unterschied(x, p <= np.median(p)))
        rang = float(np.mean(np.array(nul) < u))
        erg[ep] = dict(n=len(x), fehler=fe, med=med, g_lo=x["g"][nied].median(), g_hi=x["g"][~nied].median(), m_lo=tk(x, nied), m_hi=tk(x, ~nied),
                       u=u, rang=rang, quelle=x["q"].value_counts().to_dict(), kl=x["kl"].value_counts().to_dict())
        traegt &= (u > 0) and (rang >= 0.95)
    return erg, traegt


# ---------------------------------------------------------------- L4
def L4():
    b = K["BTC"]
    fe = b.shift(-181) / b.shift(-1) - 1
    q = pd.Series(M.QV, index=IDX)
    tage = IDX[(IDX >= "2019-01-01") & fe.notna().values & q.notna().values]
    wi = np.array([woche(t) for t in tage])
    m = wi >= 0
    tage, wi = tage[m], wi[m]
    f, qq = fe.reindex(tage).values, q.reindex(tage).values
    drittel = np.where(qq < 1 / 3, 0, np.where(qq < 2 / 3, 1, 2))
    ep = np.array([A.epoche(t) for t in tage])
    ks = RNG.integers(26, len(ZW) - 26, size=NZ)
    erg, traegt = {}, True
    for e in ("E1", "E2", "E3"):
        for dr in (0, 1, 2):
            sel = (ep == e) & (drittel == dr)
            st = ZW[wi[sel]]; x = f[sel]
            if st.sum() < 30 or (~st).sum() < 30:
                erg[(e, dr)] = dict(n=int(sel.sum()), n_st=int(st.sum()), ok=False)
                if e in ("E2", "E3"):
                    traegt = False
                continue
            u = x[st].mean() - x[~st].mean()
            nul = []
            for k in ks:
                s2 = np.roll(ZW, k)[wi[sel]]
                nul.append(x[s2].mean() - x[~s2].mean() if s2.sum() and (~s2).sum() else np.nan)
            nul = np.array(nul); nul = nul[~np.isnan(nul)]
            rang = float(np.mean(nul < u))
            erg[(e, dr)] = dict(n=int(sel.sum()), n_st=int(st.sum()), m_st=x[st].mean(), m_fa=x[~st].mean(), u=u, rang=rang, ok=True)
            if e in ("E2", "E3"):
                traegt &= (u > 0) and (rang >= 0.95)
    return erg, traegt


def pz(x):
    return "%+6.1f %%" % (100 * x) if x is not None and not pd.isna(x) else "   -   "


def main():
    print("Messung L1-L4 (Voranalyse_Spot §16.3) · Kursdaten bis %s · Netto-Liquiditaet bis %s (%.2f Bio. USD)" % (ENDE.date(), NETTO.index[-1].date(), NETTO.iloc[-1]))
    print("Vorab: traegt = Unterschied > 0 in E2 UND E3 und Rang >= 0,95 (L1/L4 zirkulaere Verschiebung, L3 Permutation), je %d Ziehungen" % NZ)
    gesamt = []
    for art in ("X4", "X5"):
        erg, tr, d = L1(art)
        gesamt.append(("L1 Liquiditaet x A1 · %s" % art, tr))
        print("\nL1 · A1 Boden + Wende · %s · Vorteil gg. BTC bei steigender gegen fallende Netto-Liquiditaet (Klassen gepoolt)  ->  %s" % (art, "TRAEGT" if tr else "traegt nicht"))
        for ep in ("E1", "E2", "E3"):
            o = erg.get(ep)
            if not o:
                print("  %s  zu wenige" % ep); continue
            print("  %s  n %4d (steigend %4d) | steigend %s · fallend %s · Unterschied %s · Rang %.2f | Auskunft: Verzoegerung 13 W %s · je Klasse H %s M %s S %s" % (
                ep, o["n"], o["n_st"], pz(o["m_st"]), pz(o["m_fa"]), pz(o["u"]), o["rang"], pz(o["u_lag"]), pz(o["kl"]["H"]), pz(o["kl"]["M"]), pz(o["kl"]["S"])))
        if art == "X4":
            print("  L2 Auskunft Stablecoin-Umlauf (91-T-Aenderung) · X4:")
            for ep, (n, ns, ms, mf) in L2(d).items():
                print("    %s  n %4d (steigend %4d) | steigend %s · fallend %s" % (ep, n, ns, pz(ms), pz(mf)))
        erg3, tr3 = L3(art, d)
        gesamt.append(("L3 Verwaesserung · %s" % art, tr3))
        print("\nL3 · A1 · %s · Vorteil gg. BTC bei GERINGER gegen HOHE Verwaesserung (Umlaufwachstum 180 T vor dem Ereignis)  ->  %s" % (art, "TRAEGT" if tr3 else "traegt nicht"))
        for ep in ("E2", "E3"):
            o = erg3[ep]
            if "u" not in o:
                print("  %s  zu wenige (n %d, Datenfehler %d)" % (ep, o["n"], o["fehler"])); continue
            print("  %s  n %4d (Datenfehler aus %d) · Wachstum Median %s (gering %s / hoch %s) | gering %s · hoch %s · Unterschied %s · Rang %.2f | Quelle %s · Klassen %s" % (
                ep, o["n"], o["fehler"], pz(o["med"]), pz(o["g_lo"]), pz(o["g_hi"]), pz(o["m_lo"]), pz(o["m_hi"]), pz(o["u"]), o["rang"], o["quelle"], o["kl"]))
    erg4, tr4 = L4()
    gesamt.append(("L4 Kern Liquiditaet x Klima", tr4))
    print("\nL4 · Kern BTC · Folgeertrag 180 T bei steigender gegen fallende Netto-Liquiditaet, je Klima-Drittel  ->  %s" % ("TRAEGT" if tr4 else "traegt nicht"))
    for (e, dr), o in erg4.items():
        name = ("q < 1/3 (Zone billig)", "q Mitte", "q >= 2/3 (teuer)")[dr]
        if not o["ok"]:
            print("  %s %-22s Tage %4d (steigend %4d)  nicht beurteilbar (< 30 Tage je Zustand)" % (e, name, o["n"], o["n_st"])); continue
        print("  %s %-22s Tage %4d (steigend %4d) | steigend %s · fallend %s · Unterschied %s · Rang %.2f" % (e, name, o["n"], o["n_st"], pz(o["m_st"]), pz(o["m_fa"]), pz(o["u"]), o["rang"]))
    print("\nGESAMT (vorab §16.3):")
    for n, t in gesamt:
        print("  %-30s %s" % (n, "TRAEGT" if t else "-"))


if __name__ == "__main__":
    main()
