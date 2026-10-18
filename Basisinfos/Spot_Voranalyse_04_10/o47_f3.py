"""O47 Fassung 3 (F3) - Messung nach Spot §59.10 (vorab 82a0bd9a): A1 nur Auskunft, Entscheid allein am Holdout 2017-01..2019-03.

    python Basisinfos/Spot_Voranalyse_04_10/o47_f3.py

A1 und A2 mit dem Code von o47_f2a (unveraendert, geprueft); neu: H4 (Season-Anteil je geltender Stufe am Holdout, Auskunft) und der
taegliche CoinMetrics-Korb 2018-01..2019-03 als Probe der Wochenkoernung (Auskunft).
"""
import math
import os
import sqlite3
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import o47_f2a as F  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass
STABLE_CM = ("usdt", "usdc", "pax", "tusd", "gusd", "busd", "dai", "husd", "usdk", "sai")


def wilson(k, n, z=1.96):
    if n == 0:
        return float("nan"), float("nan")
    p = k / n
    m = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    c = (p + z * z / (2 * n)) / (1 + z * z / n)
    return c - m, c + m


def h4():
    A2 = pd.read_csv("data/_spot/o47_f2a_A2.csv", sep=";", parse_dates=[0], index_col=0)
    Kb = pd.read_csv("data/_spot/o47_f2a_A2_korb.csv", sep=";", parse_dates=[0], index_col=0)
    so = [t for t in Kb.index if pd.Timestamp("2017-01-01") <= t <= pd.Timestamp("2019-03-31") and Kb.rel13[t] == Kb.rel13[t]]
    g = pd.DataFrame({"stufe": [A2.geltend.asof(t) for t in so], "w": [Kb.rel13[t] >= 0.25 for t in so]}, index=so)
    basis = g.w.mean()
    print("\nH4 (Auskunft) Season-Anteil je geltender Stufe an %d Holdout-Sonntagen (Basis %.1f %%):" % (len(g), 100 * basis))
    for s, x in g.groupby("stufe"):
        lo, hi = wilson(int(x.w.sum()), len(x))
        print("   %-13s %3d So · Season %2d = %5.1f %% [95 %%: %.1f..%.1f]" % (s, len(x), int(x.w.sum()), 100 * x.w.mean(), 100 * lo, 100 * hi))
    sk = g[g.stufe.isin(["Season-Klima", "Ueberhitzung"])]
    ka = g[g.stufe == "kalt"]
    if len(sk) and len(ka):
        print("   -> Season-Klima + Ueberhitzung %.1f %% (%d So) gegen kalt %.1f %% (%d So): %s" % (
            100 * sk.w.mean(), len(sk), 100 * ka.w.mean(), len(ka), "hoeher" if sk.w.mean() > ka.w.mean() else "NICHT hoeher"))
    else:
        print("   -> nicht vergleichbar (Season-Klima %d So, kalt %d So)" % (len(sk), len(ka)))


def cm_tageskorb():
    c = sqlite3.connect("file:data/_spot/o47_cm.db?mode=ro", uri=True, timeout=30)
    D = pd.read_sql("SELECT asset, tag, PriceUSD, CapMrktCurUSD FROM tag WHERE PriceUSD IS NOT NULL AND CapMrktCurUSD IS NOT NULL AND tag>='2017-10-01' "
                    "AND tag<='2019-07-01'", c, parse_dates=["tag"])
    c.close()
    D = D[(D.asset != "btc") & ~D.asset.isin(STABLE_CM) & ~D.asset.str.startswith("usdt")]
    P = D.pivot(index="tag", columns="asset", values="PriceUSD").sort_index().asfreq("D")
    C = D.pivot(index="tag", columns="asset", values="CapMrktCurUSD").sort_index().asfreq("D")
    ret = P.pct_change(fill_method=None)
    cm = sqlite3.connect("file:data/_spot/coinmetrics.db?mode=ro", uri=True)
    b = pd.read_sql("SELECT tag, PriceUSD FROM tag WHERE asset='btc'", cm, parse_dates=["tag"]).set_index("tag").PriceUSD.reindex(P.index)
    cm.close()
    idx = P.index[P.index >= "2018-01-01"]
    kr = pd.Series(0.0, index=idx)
    for m in pd.date_range("2018-01-01", idx[-1], freq="MS"):
        top = C.loc[m].dropna().sort_values(ascending=False).index[:50]
        sl = (idx >= m) & (idx < m + pd.offsets.MonthBegin(1))
        kr[idx[sl]] = ret.loc[idx[sl], top].fillna(0.0).mean(axis=1)
    ki = (1 + kr).cumprod()
    bi = b.reindex(idx)
    rel = (ki.shift(-90) / ki) / (bi.shift(-90) / bi) - 1
    Kb = pd.read_csv("data/_spot/o47_f2a_A2_korb.csv", sep=";", parse_dates=[0], index_col=0)
    so = [t for t in Kb.index if pd.Timestamp("2018-01-01") <= t <= pd.Timestamp("2019-03-31") and Kb.rel13[t] == Kb.rel13[t] and rel.get(t) == rel.get(t)]
    a = pd.Series([rel[t] >= 0.25 for t in so], index=so)
    w = pd.Series([Kb.rel13[t] >= 0.25 for t in so], index=so)
    print("\nAuskunft: taeglicher CoinMetrics-Korb (Top 50 Marktwert) gegen den Wochenkorb, 2018-01..2019-03, %d Sonntage: gleich %.1f %% · "
          "Season-Wochen CM %d, Wochenkorb %d" % (len(so), 100 * float((a == w).mean()), int(a.sum()), int(w.sum())))


def main():
    print("O47 FASSUNG 3 (F3) · Messplan §59.10 (vorab 82a0bd9a) · A1 nur Auskunft, Entscheid am Holdout\n")
    F.a1()
    print("   (A1 ist in F3 nur Auskunft und entscheidet nicht)")
    urteil = F.a2()
    h4()
    cm_tageskorb()
    print("\nURTEIL F3 (allein am Holdout, §59.7/§59.10): %s" % urteil)


if __name__ == "__main__":
    main()
