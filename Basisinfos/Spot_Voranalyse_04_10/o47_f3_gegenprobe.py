"""Gegenprobe O47 F3 Holdout (18.10.2026) - ZWEITER Weg, ohne o47_f2a/o47_schritt1/agent.season_ampel.

    python Basisinfos/Spot_Voranalyse_04_10/o47_f3_gegenprobe.py

G1 Wahrheit neu (Langformat, merge je Woche, Ausfall wie Plan) 2016-08..2019-03 -> je Sonntag gegen o47_f2a_A2_korb.csv
G2 B1/B2/B3 neu per asof aus den Rohquellen (coinmetrics.db BTC, FRED M2SL +35 T, o47_cm.db Stablecoins +1 T) -> je Tag gegen o47_f2a_A2.csv
G3 Stufe neu (if-Kette nach §36.5, Ende 90 T) + Haltezeit als Zaehler, Breite aus G1 -> geltende Stufe je Tag gegen o47_f2a_A2.csv
G4 H1/H2/Urteil neu ausgewertet (eigene Episodenrechnung)
"""
import io
import os
import sqlite3
import sys

import numpy as np
import pandas as pd
import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from o47_schritt1 import STAB  # noqa: E402  (nur die vorab festgelegte Liste)

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass
ok = []


def pruefe(name, bed, info=""):
    ok.append(bool(bed))
    print("  %s  %s%s" % ("OK  " if bed else "FEHL", name, ("  (%s)" % info) if info else ""))


c = sqlite3.connect("file:data/_spot/o47_cm.db?mode=ro", uri=True, timeout=30)
W = pd.read_sql("SELECT stichtag, id, symbol, preis, umsatz FROM cmc_woche WHERE stichtag>='2016-07-01' AND stichtag<='2019-07-31'", c,
                parse_dates=["stichtag"])
CMP = pd.read_sql("SELECT asset, tag, PriceUSD FROM tag WHERE PriceUSD IS NOT NULL AND tag>='2016-07-01' AND tag<='2019-08-01'", c, parse_dates=["tag"])
ST = pd.read_sql("SELECT asset, tag, SplyCur FROM tag WHERE SplyCur IS NOT NULL AND asset IN ('usdt','usdc','pax','tusd','gusd','busd','dai','husd','usdk','sai')",
                 c, parse_dates=["tag"])
c.close()
cmp_ = {(a, t): p for a, t, p in CMP.itertuples(index=False)}
EA = pd.read_csv("data/_spot/o47_f2a_A2.csv", sep=";", parse_dates=[0], index_col=0)
EK = pd.read_csv("data/_spot/o47_f2a_A2_korb.csv", sep=";", parse_dates=[0], index_col=0)
print("O47 F3 GEGENPROBE Holdout (zweiter Weg)\n")

# ── G1 Wahrheit
tage = sorted(W.stichtag.unique())
sym = W.sort_values("stichtag").groupby("id").symbol.last()
W = W.sort_values(["id", "stichtag"])
W["wr"] = W.groupby("id").preis.pct_change(fill_method=None)
W.loc[W.groupby("id").stichtag.diff() != pd.Timedelta(days=7), "wr"] = np.nan
med = W.groupby("id").wr.apply(lambda x: x.abs().median() if x.notna().sum() >= 4 else np.nan)
stabil = {i for i in sym.index if str(sym[i]).upper() in STAB or (med.get(i) == med.get(i) and med.get(i) < 0.005)}
btc = int(W[W.symbol == "BTC"].groupby("id").size().idxmax())
wochen = [t for t in tage if t >= pd.Timestamp("2016-08-01")]
monat, liste = {}, {}
for t in wochen:
    monat.setdefault((t.year, t.month), t)
for t0 in monat.values():
    i0 = tage.index(t0)
    jetzt = W[(W.stichtag == t0) & ~W.id.isin(stabil) & (W.id != btc)].id
    u = W[W.stichtag.isin(tage[max(0, i0 - 3):i0 + 1]) & W.id.isin(jetzt)].groupby("id").umsatz.mean().dropna()
    liste[t0] = list(u.sort_values(ascending=False).index[:50])
preis = W.pivot_table(index="stichtag", columns="id", values="preis")
idx = [1.0]
for k in range(len(wochen) - 1):
    t, t1 = wochen[k], wochen[k + 1]
    top = liste[monat[(t.year, t.month)]]
    r = []
    for i in top:
        p0, p1 = preis.loc[t].get(i), preis.loc[t1].get(i)
        if p0 == p0 and p1 == p1:
            r.append(p1 / p0 - 1)
        elif p0 == p0:
            s = str(sym[i]).lower()
            e0, e1 = cmp_.get((s, t)), cmp_.get((s, t1))
            r.append(e1 / e0 - 1 if (e0 and e1) else -1.0)
        else:
            r.append(0.0)
    idx.append(idx[-1] * (1 + np.mean(r)))
ki = pd.Series(idx, index=wochen)
bp = preis[btc].reindex(wochen)
rel = (ki.shift(-13) / ki) / (bp.shift(-13) / bp) - 1
so = [t for t in wochen if pd.Timestamp("2017-01-01") <= t <= pd.Timestamp("2019-03-31") and rel[t] == rel[t]]
wahr = pd.Series([rel[t] >= 0.25 for t in so], index=so)
pruefe("G1 Wahrheit je Holdout-Sonntag gleich", all(wahr[t] == (EK.rel13[t] >= 0.25) for t in so), "%d Sonntage, Season %d" % (len(so), int(wahr.sum())))
breite = {}
for k, t in enumerate(wochen):
    if k < 13:
        continue
    t0 = wochen[k - 13]
    top = liste[monat[(t.year, t.month)]]
    q = [(preis.loc[t].get(i) / preis.loc[t0].get(i)) for i in top if preis.loc[t].get(i) == preis.loc[t].get(i) and preis.loc[t0].get(i) == preis.loc[t0].get(i)]
    if len(q) >= 20:
        breite[t] = float(np.mean([x > bp[t] / bp[t0] for x in q]))
db = max(abs(breite[t] - EK.breite[t]) for t in breite if EK.breite.get(t) == EK.breite.get(t))
pruefe("G1 Breite je Sonntag gleich", db < 1e-12, "groesste Abweichung %.1e" % db)

# ── G2 Bedingungen
cm = sqlite3.connect("file:data/_spot/coinmetrics.db?mode=ro", uri=True)
b = pd.read_sql("SELECT tag, PriceUSD FROM tag WHERE asset='btc' ORDER BY tag", cm, parse_dates=["tag"]).set_index("tag").PriceUSD
cm.close()
# M2 auf einem ZWEITEN Weg: FRED-API mit Schluessel ueber agent.makro_lage.hole_reihe (Verzug 35 T dort hinterlegt) statt fredgraph.csv
# (18.10.: fredgraph antwortete nicht; die Messung o47_f3 nutzt fredgraph - das macht die Probe unabhaengiger)
sys.path.insert(0, os.getcwd())
from dotenv import dotenv_values  # noqa: E402
import agent.makro_lage as ML  # noqa: E402
_r = ML.hole_reihe("M2SL", dotenv_values(".env").get("FRED_API_KEY"), "2014-01-01")
m2 = pd.DataFrame({"ab": _r.index, "m2": _r.values})
m2 = m2.dropna().reset_index(drop=True)
stab = {a: g.set_index("tag").SplyCur for a, g in ST.groupby("asset")}
tg = pd.date_range("2016-10-01", "2019-03-31")


def b3_summe(t):
    return sum(float(s.asof(t - pd.Timedelta(days=1))) if s.index[0] <= t - pd.Timedelta(days=1) else 0.0 for s in stab.values())


B = pd.DataFrame(index=tg)
B["B1"] = [b.asof(t) / b.asof(t - pd.Timedelta(days=91)) - 1 for t in tg]
pos = [int(m2.ab.searchsorted(t, side="right")) - 1 for t in tg]
B["B2"] = [m2.m2[p] / m2.m2[p - 12] - 1 for p in pos]
B["B3"] = [b3_summe(t) / b3_summe(t - pd.Timedelta(days=91)) - 1 for t in tg]
for k in ("B1", "B2", "B3"):
    d = (B[k] - EA[k].reindex(tg)).abs()
    pruefe("G2 %s je Tag gleich (< 1e-9)" % k, float(d.max()) < 1e-9 and int(d.isna().sum()) == 0, "groesste %.1e, fehlend %d" % (float(d.max()), int(d.isna().sum())))

# ── G3 Stufe
br_tag = pd.Series(breite).sort_index()


def stufe(b1, b2, b3, brt, war3):
    m1, m2_, m3 = b1 > 0.20, b2 > 0.05, b3 > 0.10
    if m1 and m2_ and m3:
        return "Ueberhitzung" if brt == brt and brt >= 0.6 else "Season-Klima"
    if war3:
        return "Ende"
    if (not m1) and m2_ and m3:
        return "Vorlauf"
    if m1 and m2_ and not m3:
        return "ungewohnt"
    return "kalt"


roh, letzte = [], None
for t in tg:
    brt = br_tag.asof(t) if br_tag.index[0] <= t else float("nan")
    roh.append(stufe(B.B1[t], B.B2[t], B.B3[t], brt, letzte is not None and (t - letzte).days <= 90))
    if B.B1[t] > 0.20 and B.B2[t] > 0.05 and B.B3[t] > 0.10:
        letzte = t
akt, kand, n, gel = roh[0], roh[0], 0, []
for s in roh:
    kand, n = (kand, n + 1) if s == kand else (s, 1)
    if kand != akt and n >= 7:
        akt = kand
    gel.append(akt)
G = pd.Series(gel, index=tg)
pruefe("G3 geltende Stufe je Tag gleich", bool((G == EA.geltend.reindex(tg)).all()), "%d von %d" % (int((G == EA.geltend.reindex(tg)).sum()), len(tg)))

# ── G4 Urteil
ep, a0, letzt = [], None, None
for t, v in wahr.items():
    if v and a0 is None:
        a0 = t
    if not v and a0 is not None:
        if ep and (a0 - ep[-1][1]).days < 30:
            ep[-1] = (ep[-1][0], t)
        else:
            ep.append((a0, t))
        a0 = None
ep = [(a, e) for a, e in ep if (e - a).days >= 28]
h1 = all(G[(G.index >= a - pd.Timedelta(days=120)) & (G.index <= a + pd.Timedelta(days=30))].isin(["Vorlauf", "Season-Klima"]).any() for a, _e in ep)
R = G[(G.index >= "2018-02-01")]
anteil = float((R == "Season-Klima").mean())
h2 = anteil <= 0.10
print("  Episoden >= 28 T: %s · H1 %s · H2 Season-Klima %.1f %% -> %s" % (" · ".join("%s..%s" % (a.date(), e.date()) for a, e in ep), h1, 100 * anteil, h2))
pruefe("G4 Urteil neu: TRAEGT (H1 und H2)", bool(ep) and h1 and h2)
print("\n%d Pruefungen, %s" % (len(ok), "ALLE BESTANDEN" if all(ok) else "%d FEHLGESCHLAGEN" % ok.count(False)))
