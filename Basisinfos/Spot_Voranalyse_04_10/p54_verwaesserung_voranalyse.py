"""P54 VORANALYSE Verwaesserung in Mail und Statusseite (Spot §54, Nutzer 15.10.: "Ja, Voranalyse vorbereiten, pruefen und gegenpruefen").

    python Basisinfos/Spot_Voranalyse_04_10/p54_verwaesserung_voranalyse.py

Nur lesend (Desktop: data/messdaten.db Messbasis, data/umlaufmenge_cg.db voll; Austauschordner: NB-Kopie 22.09.).

TEIL 1  GEGENPRUEFUNG IN BETRIEBSFORM: Gilt der Befund §53.3 auch im B4-Universum und in den B4-Klassen (agent.spot_abbau.Wert,
        derselbe Code wie im Betrieb: Marktwert-Rang H <= 30 / M <= 100 / S)? Verwaesserung = log(Umlauf t / Umlauf t-90) mit
        derselben Lesegrenze wie B4 (_asof, hoechstens 7 T alt). Fuenftel je B4-Klasse (>= 10 Coins mit Wert), Ziel 90-T-log-Ertrag
        ab t+1 gegen die Klasse, Nullwelt bestaendig 2.000. Zwei Rechenwege: (a) vektoriell, (b) Schleife je Zelle.
TEIL 2  ABDECKUNG: Watchlist (config.yaml Grundliste) und B4-Erstliste - wer hat eine Mengenreihe, wer ist im Universum?
TEIL 3  DATENLAGE AM NB: erster Tag der NB-Reihe -> ab wann gibt es 90 T?
"""
import os
import sqlite3
import sys

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
import s1_messung as S1   # noqa: E402  (chdir Projektwurzel)

sys.path.insert(0, os.getcwd())
from agent import spot_abbau as SA   # noqa: E402

RNG = np.random.default_rng(20261059)
NZ = 2000
STICH = pd.date_range("2026-01-01", "2026-06-01", freq="MS")
ERSTLISTE = ["HYPE", "KAIA", "MORPHO", "PLUME", "QNT", "SUI", "TAO", "XDC"]
NB_KOPIE = "K:/My Drive/Claude_Austauschordner/umlaufmenge_cg.db"


def umlauf_reihen(pfad):
    c = sqlite3.connect("file:%s?mode=ro" % pfad, uri=True)
    ok = set(pd.read_sql("SELECT symbol FROM abruf_symbol WHERE urteil='ok'", c).symbol)
    d = pd.read_sql("SELECT symbol, datum, wert FROM umlaufmenge", c)
    c.close()
    d["datum"] = pd.to_datetime(d.datum.str[:10])
    return {s: g.set_index("datum")["wert"].sort_index() for s, g in d.groupby("symbol") if s in ok}


def verwaesserung(r, t):
    if r is None:
        return np.nan
    a, b = SA._asof(r, t), SA._asof(r, t - pd.Timedelta(days=90))
    return np.log(a / b) if a and b else np.nan


def main():
    K, U = S1.lade()
    cgh = umlauf_reihen("data/umlaufmenge_cg.db")
    n_kerzen = K.notna().cumsum()
    ret = K.pct_change(fill_method=None)
    stabil = {s for s in K.columns if ret[s].abs().median() < SA.STABIL}

    def umlauf(s, m):
        r = cgh.get(s)
        if r is None:
            return np.nan
        h = SA._asof(r, m)
        if h is None:
            h = SA._asof(r, umlauf.t)
        return h if h is not None else np.nan

    zeilen = []
    for t in STICH:
        umlauf.t = t
        jung = set(n_kerzen.columns[(n_kerzen.loc[t] < SA.MIN_KERZEN).values])
        W = SA.Wert(K.loc[:t], U.loc[:t], set(SA.SONDER) | stabil | jung, umlauf)
        z = W.fuenftel(t)
        z = z[z.q.notna()].copy()
        z["v"] = [verwaesserung(cgh.get(s), t) for s in z.sym]
        p0 = K.loc[t + pd.Timedelta(days=1), z.sym].values
        p1 = K.loc[t + pd.Timedelta(days=91), z.sym].values
        z["y"] = np.log(p1 / p0)
        z["t"] = t
        zeilen.append(z)
    D = pd.concat(zeilen, ignore_index=True)
    print("P54 VORANALYSE Verwaesserung · Stichtage %s bis %s\n" % (STICH[0].date(), STICH[-1].date()))
    print("TEIL 1  GEGENPRUEFUNG IN BETRIEBSFORM (B4-Universum, B4-Klassen, Lesegrenze _asof)")
    print("  B4-Universum je Stichtag: %s · davon mit Verwaesserung: %s" % (
        " ".join(str(int((D.t == t).sum())) for t in STICH), " ".join(str(int(((D.t == t) & D.v.notna()).sum())) for t in STICH)))
    E = D[D.v.notna() & np.isfinite(D.y)].copy()
    E["cell"] = E.groupby(["t", "kl"]).ngroup()
    groesse = E.groupby("cell").sym.transform("size")
    E = E[groesse >= 10].copy()
    E["cell"] = E.groupby(["t", "kl"]).ngroup()
    E["qv"] = E.groupby("cell").v.rank(pct=True)
    cell = E.cell.values
    C = cell.max() + 1
    nc = np.bincount(cell, minlength=C)
    y = E.y.values
    mc = np.bincount(cell, weights=y, minlength=C) / nc
    tc = E.groupby("cell").t.first().values
    kc = E.groupby("cell").kl.first().values

    def abst(q, oben):
        sel = (q > 0.8) if oben else (q <= 0.2)
        ns = np.bincount(cell, weights=sel, minlength=C)
        zz = np.bincount(cell, weights=sel * y, minlength=C) / np.maximum(ns, 1) - mc
        zz[ns == 0] = np.nan
        return float(np.nanmean(zz)), zz

    code = pd.Series(np.arange(E.sym.nunique()), index=E.sym.unique())[E.sym].values
    nl = {True: [], False: []}
    for _ in range(NZ):
        q = pd.Series(RNG.random(code.max() + 1)[code]).groupby(cell).rank(pct=True).values
        for o in (True, False):
            nl[o].append(abst(q, o)[0])
    print("  Zellen mit >= 10 Coins: %d (H %d · M %d · S %d) · Coin-Stichtage %d · Grenze oberes Fuenftel ab %+.1f %% in 90 T" % (
        C, (kc == "H").sum(), (kc == "M").sum(), (kc == "S").sum(), len(E), 100 * np.expm1(E.v.quantile(0.8))))
    erg = {}
    for o, name in ((True, "staerkste Verwaesserung (oberes Fuenftel)"), (False, "geringste Verwaesserung (unteres Fuenftel)")):
        a, zz = abst(E.qv.values, o)
        n = np.array(nl[o])
        ph, pt = (np.sum(n >= a) + 1) / (NZ + 1), (np.sum(n <= a) + 1) / (NZ + 1)
        je = pd.Series(zz).groupby(tc).mean()
        jk = pd.Series(zz).groupby(kc).mean()
        erg[o] = a
        print("  (a) %-44s %+6.1f log-Pp gg. Klasse · p hoch %.4f / tief %.4f · je Stichtag %s · je Klasse %s" % (
            name, 100 * a, ph, pt, " ".join("%+.0f" % (100 * v) for v in je.values), " ".join("%s %+.1f" % (k, 100 * v) for k, v in jk.items())))
    # (b) zweiter Rechenweg: Schleife je Zelle mit pandas
    w = []
    for _, g in E.groupby(["t", "kl"]):
        r = g.v.rank(pct=True)
        w.append(((g.y[r > 0.8].mean() - g.y.mean()) if (r > 0.8).any() else np.nan,
                  (g.y[r <= 0.2].mean() - g.y.mean()) if (r <= 0.2).any() else np.nan))
    w = np.array(w)
    ob, ub = np.nanmean(w[:, 0]), np.nanmean(w[:, 1])
    print("  (b) Schleife je Zelle: oben %+6.2f · unten %+6.2f log-Pp -> %s" % (
        100 * ob, 100 * ub, "gleich (a)" if abs(ob - erg[True]) < 1e-9 and abs(ub - erg[False]) < 1e-9 else "ABWEICHUNG"))
    # Zusammenhang mit dem B4-Wert: ist Verwaesserung nur ein anderes Wort fuer das untere Fuenftel?
    print("  Ueberschneidung mit B4: Spearman Verwaesserung ~ B4-Perzentil %+.2f · im B4-unteren Fuenftel liegen %.0f %% des staerksten "
          "Verwaesserungs-Fuenftels (Zufall 20 %%)" % (E.groupby("t").apply(lambda g: g.v.corr(g.p, method="spearman")).mean(),
                                                    100 * (E.q[E.qv > 0.8] == 1).mean()))
    for name, maske in (("B4 unteres Fuenftel", E.q == 1), ("B4 uebrige", E.q > 1)):
        g = E[maske]
        o = (g.y - g.cell.map(pd.Series(mc)))[g.qv > 0.8].mean()
        print("    innerhalb %-20s staerkste Verwaesserung %+6.1f log-Pp gg. Klasse (n %d)" % (name, 100 * o, int((g.qv > 0.8).sum())))

    # Zerlegung: liegt der Unterschied zu §53.3 am UNIVERSUM oder an den KLASSEN? (B4-Universum, aber Marktwert-Drittel wie §53)
    E["mw"] = [umlauf_wert * K.at[t, s] if (umlauf_wert := (SA._asof(cgh[s], t) if s in cgh else None)) else np.nan for s, t in zip(E.sym, E.t)]
    F = E[E.mw.notna()].copy()
    F["kl3"] = F.groupby("t").mw.transform(lambda a: pd.qcut(a.rank(method="first"), 3, labels=["S", "M", "H"])).astype(str)
    F["c3"] = F.groupby(["t", "kl3"]).ngroup()
    F["q3"] = F.groupby("c3").v.rank(pct=True)
    m3 = F.groupby("c3").y.transform("mean")
    o3 = (F.y - m3)[F.q3 > 0.8].groupby(F.c3[F.q3 > 0.8]).mean().mean()
    u3 = (F.y - m3)[F.q3 <= 0.2].groupby(F.c3[F.q3 <= 0.2]).mean().mean()
    print("  ZERLEGUNG: B4-Universum mit Marktwert-DRITTELN (Zellen wie §53): oben %+6.1f · unten %+6.1f log-Pp (§53.3: -7,4 / +6,4; B4-Klassen: %+.1f / %+.1f)" % (
        100 * o3, 100 * u3, 100 * erg[True], 100 * erg[False]))
    print("  Was das B4-Universum gegenueber §53 weglaesst: < 400 Kerzen, < 30 T Umsatz in 90 T, ausserhalb Binance-Spot, Sonderwerte")

    print("\nTEIL 2  ABDECKUNG")
    import yaml
    cfg = yaml.safe_load(open("Basisinfos/config.yaml", encoding="utf-8"))
    wl = [a.get("symbol") for a in cfg.get("watchlist", []) if str(a.get("asset_class", a.get("assetklasse", "krypto"))).lower() in ("krypto", "crypto")]
    wl = [s for s in wl if s] or [a.get("symbol") for a in cfg.get("watchlist", [])]
    letzt = D[D.t == STICH[-1]]
    for name, liste in (("Watchlist-Grundliste", wl), ("B4-Erstliste 14.10.", ERSTLISTE)):
        mit = [s for s in liste if s in cgh]
        uni = [s for s in liste if s in set(letzt.sym)]
        print("  %-22s %3d Coins · mit Mengenreihe %d · im B4-Universum (06/2026) %d · ohne Reihe: %s" % (
            name, len(liste), len(mit), len(uni), ", ".join(sorted(set(liste) - set(mit))) or "-"))
    v_heute = {s: verwaesserung(cgh.get(s), pd.Timestamp("2026-09-20")) for s in ERSTLISTE}
    print("  Erstliste, Verwaesserung 90 T bis 20.09.2026 (Desktop-Reihe): %s" % " · ".join(
        "%s %+.1f %%" % (s, 100 * np.expm1(v)) if v == v else "%s -" % s for s, v in v_heute.items()))

    print("\nTEIL 3  DATENLAGE AM NB")
    if os.path.exists(NB_KOPIE):
        c = sqlite3.connect("file:%s?mode=ro" % NB_KOPIE, uri=True)
        a, b, n = c.execute("SELECT MIN(datum), MAX(datum), COUNT(DISTINCT symbol) FROM umlaufmenge").fetchone()
        marke = c.execute("SELECT name FROM sqlite_master WHERE name='_nur_betrieb'").fetchone()
        c.close()
        erst = pd.Timestamp(a[:10])
        voll = erst + pd.Timedelta(days=90)
        naechster = (voll + pd.offsets.MonthBegin(1)).normalize() if voll.day != 1 else voll
        print("  USB-Kopie 22.09.: %s bis %s, %d Symbole, Marke _nur_betrieb %s · NB schreibt seither taeglich fort (Diagnose 14.10.: Datenstand 2026-10-14)" % (
            a[:10], b[:10], n, "ja" if marke else "NEIN"))
        print("  -> 90 T Historie am NB ab %s · erster B4-Stichtag mit Verwaesserung: %s (ohne Ergaenzung)" % (voll.date(), naechster.date()))
        dc = sqlite3.connect("file:data/umlaufmenge_cg.db?mode=ro", uri=True)
        da, db_, dn = dc.execute("SELECT MIN(datum), MAX(datum), COUNT(*) FROM umlaufmenge WHERE datum < ?", (a[:10],)).fetchone()
        dc.close()
        print("  Ergaenzung moeglich: Desktop-Reihe %s bis %s (%d Zeilen vor dem NB-Beginn) -> mit ihr gaebe es 90 T sofort" % (da[:10], db_[:10], dn))


if __name__ == "__main__":
    main()
