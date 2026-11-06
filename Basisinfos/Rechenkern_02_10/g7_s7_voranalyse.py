"""G7 S7-ANLAGE — Voranalyse: die Zellen (Asset x Tag), die S7 beurteilen kann, ihre Ballung, Kursabdeckung und die Kursreaktion
seit der Meldung (Voranalyse_G7_S7_Anlage_05_11.md; Nutzer 05.11.: *„S7-Anlage zuerst“*).

KEIN LLM-Urteil wird gelesen (die Ablage data/_g7/gutachten.db bleibt ungeöffnet). Nur lesend: sichten.db (über agent.ereignisse /
agent.zustaende, mode=ro) und die Kurs-Arbeitskopie data/_g7/kurse/ (mode=ro). Kein Netz.

Zelle = (Stichtag T, Asset a), wenn in der S7-Eingabe von T mindestens eine Ereigniszeile a betrifft.
Zielgröße (Entwurf, hier nur Abdeckung): ertrag_s = ln(P[T+1h+72h] / P[T+1h]) / (σ_a · √3), σ_a = Std. der Tageslog-Erträge des
Assets, 60 Tage VOR T. Start T+1 h = Leseverzug wie A1 (das Gutachten entsteht nach 00:00).
Kursreaktion (Fakt, Frage §4): ln(P[T] / P[Stunde, in der die Meldung bekannt wurde]) - und dasselbe gegen BTC.

    python Basisinfos/Rechenkern_02_10/g7_s7_voranalyse.py      -> g7_s7_voranalyse.txt, data/_g7/s7_zellen.csv
"""
import json
import math
import os
import sqlite3
import sys
import time
from collections import Counter

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(os.path.dirname(HIER))
sys.path.insert(0, PROJ)
from agent import sichten_gutachten as G      # noqa: E402

KOPIE = os.path.join(PROJ, "data", "_g7", "kurse")
AUS = os.path.join(PROJ, "data", "_g7", "s7_zellen.csv")
TXT = []


def p(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    TXT.append(s)


def zellen() -> pd.DataFrame:
    q = G.Quelle()
    z = []
    for tag in G.tage():
        _, ev = q.tag(tag)
        x = ev[ev.sicht == "S7"]
        for (typ, a), g in x.groupby(["typ", "assets"], sort=False):
            for sym in json.loads(a):
                z.append(dict(tag=tag, asset=sym, typ=typ, bekannt_ab=g.bekannt_ab.min(), quelle=g.iloc[0].quelle,
                              schwere=g.iloc[0].schwere, n_meld=len(g)))
    Z = pd.DataFrame(z)
    return Z


def kurse(symbole) -> dict:
    dateien = [f for f in ("stundenkurse.db", "stundenkurse_alle.db", "stundenkurse_eingestellt.db")      # G7 P-2: + eingestellte
               if os.path.exists(os.path.join(KOPIE, f))]
    con = {f: sqlite3.connect("file:%s?mode=ro" % os.path.join(KOPIE, f).replace("\\", "/"), uri=True) for f in dateien}
    hat = {f: {r[0] for r in con[f].execute("SELECT DISTINCT symbol FROM stundenkurse")} for f in dateien}
    aus = {}
    for s in symbole:
        f = next((f for f in dateien if s in hat[f]), None)
        if f is None:
            continue
        c = con[f]
        k = pd.Series(dict(c.execute("SELECT stunde, close FROM stundenkurse WHERE symbol=? AND stunde >= '2025-08-01'", (s,)).fetchall()))
        if len(k):
            k.index = pd.to_datetime(k.index)
            aus[s] = k.sort_index().astype(float)
    return aus


def main():
    t0 = time.time()
    p("G7 S7-ANLAGE VORANALYSE · %s · nur lesend, kein LLM-Urteil gelesen" % time.strftime("%Y-%m-%d %H:%M"))
    Z = zellen()
    p("Zellen (Tag x Asset x Ereigniszeile): %d · Tage mit S7-Asset-Ereignis %d von %d · Assets %d · %.0f s" % (
        len(Z), Z.tag.nunique(), len(G.tage()), Z.asset.nunique(), time.time() - t0))
    C = Z.groupby(["tag", "asset"]).agg(typen=("typ", lambda s: ",".join(sorted(set(s)))), n_zeilen=("typ", "size"),
                                         n_meld=("n_meld", "sum"),
                                         erst=("bekannt_ab", "min"), quelle=("quelle", lambda s: ",".join(sorted(set(s))))).reset_index()
    p("Zellen (Tag x Asset): %d · je Tag Median %.0f, P90 %.0f, max %d" % (
        len(C), C.groupby("tag").size().median(), C.groupby("tag").size().quantile(0.9), C.groupby("tag").size().max()))
    # Ballung: dieselbe Zelle am Vortag schon da (das 7-T-Fenster zeigt eine Meldung bis zu 7 Tage)
    s = set(zip(C.tag, C.asset))
    vortag = [((pd.Timestamp(t) - pd.Timedelta(days=1)).strftime("%Y-%m-%d"), a) in s for t, a in zip(C.tag, C.asset)]
    C["vortag"] = vortag
    tz = pd.Timestamp
    C["neu24"] = [(tz(t).tz_localize("UTC") - tz(e)).total_seconds() / 3600 <= 24 for t, e in zip(C.tag, C.erst)]
    p("Ballung: Zelle schon am Vortag da %.1f %% · jüngste Meldung der Zelle < 24 h alt %.1f %% (%d Zellen)" % (
        100 * np.mean(vortag), 100 * C.neu24.mean(), C.neu24.sum()))
    lauf = C.sort_values(["asset", "tag"])
    run = (~lauf.vortag).groupby(lauf.asset).cumsum()
    lae = lauf.groupby([lauf.asset, run]).size()
    p("Läufe je Asset (aufeinanderfolgende Tage): %d · Länge Median %.0f, Mittel %.1f, P90 %.0f" % (
        len(lae), lae.median(), lae.mean(), lae.quantile(0.9)))
    top = C.asset.value_counts()
    p("Zellen je Asset: Top 10 %s · Anteil der Top 5 %.1f %%" % (dict(top.head(10)), 100 * top.head(5).sum() / len(C)))
    p("Typen (Zeilen): %s" % dict(Counter(Z.typ).most_common(14)))
    p("Quellen (Zeilen): %s" % dict(Counter(Z.quelle)))
    # Kurse
    K = kurse(sorted(C.asset.unique()) + ["BTC"])
    btc = K["BTC"]
    zeilen = []
    for r in C.itertuples():
        k = K.get(r.asset)
        T = pd.Timestamp(r.tag)
        d = dict(tag=r.tag, asset=r.asset, kurs=k is not None)
        if k is not None:
            tag_ = k.resample("D").last()
            sig = np.log(tag_).diff().rolling(60).std().shift(1).get(T)
            p0, p3 = k.get(T), k.get(T + pd.Timedelta(hours=72))          # Schluss der Stunde 00:00 = Kurs um T 01:00
            pe = k.get(pd.Timestamp(r.erst).tz_convert(None).floor("h"))
            pT = k.get(T - pd.Timedelta(hours=1))                          # Kurs um T 00:00
            bT, be = btc.get(T - pd.Timedelta(hours=1)), btc.get(pd.Timestamp(r.erst).tz_convert(None).floor("h"))
            er = math.log(p3 / p0) if (p0 and p3) else np.nan
            d.update(sigma=sig, ertrag_s=er / (sig * math.sqrt(3)) if (sig and np.isfinite(er)) else np.nan,
                     reaktion=math.log(pT / pe) if (pT and pe) else np.nan,
                     reaktion_btc=(math.log(pT / pe) - math.log(bT / be)) if (pT and pe and bT and be) else np.nan)
        zeilen.append(d)
    R = pd.DataFrame(zeilen)
    C = C.merge(R, on=["tag", "asset"])
    p("Kursabdeckung: Asset mit Kursreihe %.1f %% · mit Zielgröße ertrag_s(H=3) %.1f %% (%d Zellen) · mit Kursreaktion %.1f %%" % (
        100 * C.kurs.mean(), 100 * C.ertrag_s.notna().mean(), C.ertrag_s.notna().sum(), 100 * C.reaktion.notna().mean()))
    ohne = C[C.ertrag_s.isna()].asset.value_counts()
    p("ohne Zielgröße, häufigste Assets: %s" % dict(ohne.head(10)))
    b = 15                                                              # messnorm._block(3) = max(15, 9)
    blk = ((pd.to_datetime(C[C.ertrag_s.notna()].tag) - pd.Timestamp(G.ZEITRAUM[0])).dt.days // b).nunique()
    p("Blöcke à %d T mit Zielgröße: %d (MIN 20)" % (b, blk))
    m = C[C.ertrag_s.notna()]
    p("ertrag_s (alle Zellen, NUR Verteilung, kein Urteil): Mittel %+.3f, Std %.3f, P5 %+.2f, P95 %+.2f" % (
        m.ertrag_s.mean(), m.ertrag_s.std(), m.ertrag_s.quantile(0.05), m.ertrag_s.quantile(0.95)))
    r_ = C.reaktion_btc.dropna()
    p("Kursreaktion seit Meldung gegen BTC (Fakt): |Median| %.1f %%, P10 %+.1f %%, P90 %+.1f %% · Alter der Meldung Median %.0f h" % (
        100 * r_.abs().median(), 100 * r_.quantile(0.1), 100 * r_.quantile(0.9),
        np.median([(pd.Timestamp(t).tz_localize("UTC") - pd.Timestamp(e)).total_seconds() / 3600 for t, e in zip(C.tag, C.erst)])))
    C.to_csv(AUS, sep=";", index=False)
    p("geschrieben %s · %.0f s" % (AUS, time.time() - t0))
    open(os.path.join(HIER, "g7_s7_voranalyse.txt"), "w", encoding="utf-8").write("\n".join(TXT) + "\n")


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:                                                  # noqa: BLE001
        pass
    main()
