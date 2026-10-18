"""Gegenprobe O47 Schritt 1 (18.10.2026) - ZWEITER Weg fuer den Wochenkorb, ohne den Code von o47_schritt1.

    python Basisinfos/Spot_Voranalyse_04_10/o47_schritt1_gegenprobe.py

Langformat: je Woche die Aufnahme t mit t+1 ueber die CMC-ID zusammengefuehrt (merge), Monatsliste per groupby, Ausfaelle wie im Plan
(CoinMetrics-Kurs aus der Zwischenablage, sonst -100 % beim ersten Fehlen, danach 0). Vergleich je Sonntag mit data/_spot/o47_schritt1.csv:
G1 Korbindex gleich (relativ < 1e-9) · G2 Wahrheit (rel13 >= 25 Pp) an jedem Sonntag gleich · G3 Zahl der Season-Wochen gleich
G4 Stichprobe: fuer drei Monate die Top-50-Liste von Hand aus den Rohzeilen (Umsatz-Mittel der letzten 4 Aufnahmen) nachgezaehlt
"""
import os
import sqlite3
import sys

import numpy as np
import pandas as pd

WURZEL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(WURZEL)
from o47_schritt1 import STAB, KORB_AB  # noqa: E402  (nur die vorab festgelegten Listen, nicht die Rechnung)

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass
ok = []


def pruefe(name, bed, info=""):
    ok.append(bool(bed))
    print("  %s  %s%s" % ("OK  " if bed else "FEHL", name, ("  (%s)" % info) if info else ""))


c = sqlite3.connect("file:data/_spot/o47_cm.db?mode=ro", uri=True, timeout=30)
W = pd.read_sql("SELECT stichtag, id, symbol, preis, umsatz FROM cmc_woche WHERE stichtag>='2019-03-01'", c, parse_dates=["stichtag"])
CMP = pd.read_sql("SELECT asset, tag, PriceUSD FROM tag WHERE PriceUSD IS NOT NULL AND tag>='2019-03-01'", c, parse_dates=["tag"])
c.close()
cmp_ = {(a, t): p for a, t, p in CMP.itertuples(index=False)}
E = pd.read_csv("data/_spot/o47_schritt1.csv", sep=";", parse_dates=[0], index_col=0)
tage = sorted(W.stichtag.unique())
sym = W.sort_values("stichtag").groupby("id").symbol.last()
W = W.sort_values(["id", "stichtag"])
W["wr"] = W.groupby("id").preis.pct_change(fill_method=None)
W.loc[W.groupby("id").stichtag.diff() != pd.Timedelta(days=7), "wr"] = np.nan        # nur echte Folgewochen
med = W.groupby("id").wr.apply(lambda x: x.abs().median() if x.notna().sum() >= 4 else np.nan)
stabil = {i for i in sym.index if str(sym[i]).upper() in STAB or (med.get(i) == med.get(i) and med.get(i) < 0.005)}
btc = int(W[W.symbol == "BTC"].groupby("id").size().idxmax())
wochen = [t for t in tage if t >= KORB_AB]
monat = {}
for t in wochen:
    monat.setdefault((t.year, t.month), t)
liste = {}
for (y, m), t0 in monat.items():
    i0 = tage.index(t0)
    fenster = tage[max(0, i0 - 3):i0 + 1]
    jetzt = W[(W.stichtag == t0) & ~W.id.isin(stabil) & (W.id != btc)].id
    u = W[W.stichtag.isin(fenster) & W.id.isin(jetzt)].groupby("id").umsatz.mean().dropna()
    liste[t0] = list(u.sort_values(ascending=False).index[:50])
idx = [1.0]
tot = set()
for k in range(len(wochen) - 1):
    t, t1 = wochen[k], wochen[k + 1]
    t0 = monat[(t.year, t.month)]
    if t == t0:
        tot = set()
    top = liste[t0]
    a = W[(W.stichtag == t) & W.id.isin(top)][["id", "preis"]]
    b = W[(W.stichtag == t1) & W.id.isin(top)][["id", "preis"]]
    m = pd.DataFrame({"id": top}).merge(a, on="id", how="left").merge(b, on="id", how="left", suffixes=("_0", "_1"))
    r = []
    for i, p0, p1 in m.itertuples(index=False):
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
bp = W[W.id == btc].set_index("stichtag").preis.reindex(wochen)
rel = (ki.shift(-13) / ki) / (bp.shift(-13) / bp) - 1
print("O47 SCHRITT 1 GEGENPROBE (zweiter Weg) · %d Wochen\n" % len(wochen))
dk = (ki / E.korb_index.reindex(ki.index) - 1).abs()
pruefe("G1 Korbindex je Woche gleich (relativ < 1e-9)", float(dk.max()) < 1e-9, "groesste %.2e" % float(dk.max()))
g = pd.concat([rel.rename("a"), E.rel13.rename("b")], axis=1).dropna()
pruefe("G2 Wahrheit je Sonntag gleich", bool(((g.a >= 0.25) == (g.b >= 0.25)).all()), "%d Sonntage" % len(g))
pruefe("G3 Season-Wochen gleich gezaehlt", int((g.a >= 0.25).sum()) == int((g.b >= 0.25).sum()), "%d" % int((g.a >= 0.25).sum()))
for t0 in [list(monat.values())[i] for i in (0, len(monat) // 2, len(monat) - 2)]:
    i0 = tage.index(t0)
    roh = W[W.stichtag.isin(tage[max(0, i0 - 3):i0 + 1])]
    da = set(W[W.stichtag == t0].id) - stabil - {btc}
    summe = {}
    for i, u in roh[["id", "umsatz"]].itertuples(index=False):
        if i in da and u == u:
            summe.setdefault(i, []).append(u)
    hand = [i for i, _v in sorted(((i, sum(v) / len(v)) for i, v in summe.items()), key=lambda x: -x[1])[:50]]
    pruefe("G4 Top 50 %s von Hand nachgezaehlt" % t0.date(), hand == liste[t0], "Schnitt %d" % len(set(hand) & set(liste[t0])))
print("\n%d Pruefungen, %s" % (len(ok), "ALLE BESTANDEN" if all(ok) else "%d FEHLGESCHLAGEN" % ok.count(False)))
