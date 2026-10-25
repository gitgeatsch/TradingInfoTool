"""P89 MESSPLAN L-1 (Voranalyse_L1_L2_Asset_Filter_Hebel_25_10.md §8.0/§8.1, vorab 43772659): Asset-Filter fuer die Altcoins auf CMC-Wochen.

    python -X utf8 Basisinfos/Rechenkern_02_10/p89_l1_cmc.py --bruecke        Teil 1 (zuerst, zur Abstimmung)

Wert nachgebaut wie as_messung.merkmale / wl_messung.wert ohne F9: F1 = Preis / bisheriges Hoch - 1 (tiefer besser), F2 = Tage seit dem Hoch
(laenger besser), F8 = Tage seit dem ersten Erscheinen in cmc_woche (aelter besser); F1/F2 ab 26 beobachteten Wochen; Wert = Mittel der
Perzentile in der Zelle (Woche x Klasse), Merkmal zaehlt in Zellen mit >= 10 Coins. Universum: CMC Top 200 je Woche ohne BTC, ETH, SOL,
spot_abbau.SONDER und Stablecoins (Median |Wochenrendite| < 1 %). Klasse nach CMC-Rang unter den Altcoins: H <= 30, M <= 100, S Rest.
Kern BTC/ETH/SOL ist fuer REGEL0, Hebel und Spot IMMER zugelassen (§8.0) - er gehoert nur nicht in diese Ordnung.
Nur lesend.
"""
import os
import sqlite3
import sys

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(os.path.dirname(HIER))
sys.path.insert(0, os.path.join(WURZEL, "Basisinfos", "Spot_Voranalyse_04_10"))
sys.path.insert(0, HIER)
sys.path.insert(0, WURZEL)
os.chdir(WURZEL)
sys.stdout.reconfigure(encoding="utf-8")
import warnings  # noqa: E402

warnings.filterwarnings("ignore", category=RuntimeWarning)
from agent import spot_abbau as AB  # noqa: E402

KERN = ("BTC", "ETH", "SOL")


def lade():
    c = sqlite3.connect("file:data/_spot/o47_cm.db?mode=ro", uri=True)
    W = pd.read_sql("SELECT stichtag, id, rang, symbol, preis, cap FROM cmc_woche", c, parse_dates=["stichtag"])
    c.close()
    W["symbol"] = W.symbol.str.upper()
    W = W[W.preis > 0].sort_values(["id", "stichtag"]).reset_index(drop=True)
    r = W.groupby("id").preis.pct_change()
    stabil = set(W.assign(r=r.abs()).groupby("id").r.median().loc[lambda x: x < 0.01].index)
    W = W[~W.id.isin(stabil) & ~W.symbol.isin(set(KERN) | AB.SONDER)].copy()
    return W


def merkmale(W):
    W = W.sort_values(["id", "stichtag"]).copy()
    g = W.groupby("id")
    W["hoch"] = g.preis.cummax()
    W["n_beob"] = g.cumcount() + 1
    W["erst"] = g.stichtag.transform("min")
    # Datum des bisherigen Hochs: letzter Zeitpunkt, an dem preis == cummax
    W["hoch_am"] = W.stichtag.where(W.preis >= W.hoch).groupby(W.id).ffill()
    W["F1"] = np.where(W.n_beob >= 26, W.preis / W.hoch - 1, np.nan)
    W["F2"] = np.where(W.n_beob >= 26, (W.stichtag - W.hoch_am).dt.days, np.nan)
    W["F8"] = (W.stichtag - W.erst).dt.days.astype(float)
    W["arang"] = W.groupby("stichtag").cap.rank(ascending=False, method="first")
    W["kl"] = np.where(W.arang <= 30, "H", np.where(W.arang <= 100, "M", "S"))
    return W


def wert(W):
    teile = []
    for (t, k), z in W.groupby(["stichtag", "kl"]):
        P = []
        for f, oben in (("F1", False), ("F2", True), ("F8", True)):
            ok = z[f].notna()
            if ok.sum() >= 10:
                p = z[f].rank(pct=True)
                P.append(p if oben else 1 - p + 1.0 / ok.sum())        # wie 1 - pct_in_zelle (Rang umgedreht)
        if not P:
            continue
        m = pd.concat(P, axis=1).mean(axis=1)
        zz = z[["stichtag", "id", "symbol", "kl", "arang"]].copy()
        zz["w"] = m
        teile.append(zz)
    T = pd.concat(teile)
    T["p"] = T.groupby(["stichtag", "kl"]).w.rank(pct=True)
    T["f"] = np.ceil(T.p * 5).clip(1, 5)
    return T


def bruecke(T):
    import p85_atlas_voranalyse as P85
    B = P85.wert_tabelle(1)
    B["f"] = np.ceil(B.p * 5).clip(1, 5)
    wochen = np.sort(T.stichtag.unique())
    rk, ueb, n_zellen, n_coins = [], [], 0, []
    zeilen = []
    for t in sorted(B.t.unique()):
        if t < pd.Timestamp("2019-01-01"):
            continue
        i = np.searchsorted(wochen, np.datetime64(t), side="right") - 1      # letzte CMC-Woche am oder vor dem Stichtag
        if i < 0:
            continue
        w = wochen[i]
        C = T[T.stichtag == w]
        C = C[~C.symbol.duplicated(keep=False)]                                   # nur eindeutige Symbole
        b = B[B.t == t]
        m = b.merge(C[["symbol", "p", "f"]], left_on="sym", right_on="symbol", suffixes=("_b", "_c"))
        m = m[m.p_b.notna() & m.p_c.notna()]
        n_coins.append(len(m))
        for k, z in m.groupby("kl"):
            if len(z) >= 10:
                rk.append(z.p_b.rank().corr(z.p_c.rank()))
                n_zellen += 1
        o = m[m.f_b == 5]
        if len(o):
            ueb.append(float((o.f_c == 5).mean()))
        zeilen.append((pd.Timestamp(t).date(), len(m), np.nanmean(rk[-3:]) if rk else np.nan))
    r_mittel = float(np.nanmean(rk))
    u_mittel = float(np.mean(ueb))
    ok = r_mittel >= 0.8 and u_mittel >= 0.5
    print("TEIL 1 BRUECKE (Monatsstichtage 2019-01..2026-09, CMC-Woche am oder vor dem Stichtag, gemeinsame Coins je Klasse):")
    print("  Zellen (Stichtag x Klasse, >= 10 gemeinsame Coins) %d · gemeinsame Coins je Stichtag im Mittel %.0f" % (n_zellen, np.mean(n_coins)))
    print("  Rangkorrelation CMC-Wert gegen Binance-Wert im Mittel %.3f (Soll >= 0,8) · Median %.3f · 10. Perz. %.3f" % (
        r_mittel, float(np.nanmedian(rk)), float(np.nanpercentile(rk, 10))))
    print("  oberes Fuenftel Binance auch oberes Fuenftel CMC: %.0f %% im Mittel (Soll >= 50 %%)" % (100 * u_mittel))
    j = pd.DataFrame(zeilen, columns=["t", "n", "rk"])
    j["jahr"] = pd.to_datetime(j.t).dt.year
    print("  je Jahr Rangkorrelation (Mittel der Zellen): " + " · ".join("%d %.2f" % (a, g.rk.mean()) for a, g in j.groupby("jahr")))
    print("  -> BRUECKE %s" % ("HAELT" if ok else "HAELT NICHT - Ursache und Loesung, keine Bestaetigung (§8.1)"))
    return ok


def main():
    W = merkmale(lade())
    T = wert(W)
    print("P89 MESSPLAN L-1 · CMC-Wochen %s..%s · Coins im Universum %d · Wochen %d\n" % (
        W.stichtag.min().date(), W.stichtag.max().date(), W.id.nunique(), W.stichtag.nunique()))
    if "--bruecke" in sys.argv:
        bruecke(T)
        return 0
    print("Teil 2 erst nach der Abstimmung ueber Teil 1 (§8.1).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
