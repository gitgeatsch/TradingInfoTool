"""§33 - Ereignisanalyse Ebene 2 mit Markt- und Makro-Einordnung, Seasons 2019-2026 (Ebene 1), Kosten-Nutzen der Season-Option (Plan vorab 5e31c51).

    python Basisinfos/Spot_Voranalyse_04_10/e33_analyse.py

Nur lesend; Abrufe nach aussen: FRED (WALCL, WTREGEN, RRPONTSYD, M2SL, DFF, DTWEXBGS, SP500, DGS10) und DefiLlama Stablecoins - alle frei.
Zeitpunkttreue: jeder Makrowert gilt erst ab dem Tag, an dem er bekannt war (woechentlich +2 T, M2 monatlich +35 T, taeglich +1 T).
"""
import io
import itertools
import os
import sqlite3
import sys

import numpy as np
import pandas as pd
import requests

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
os.chdir(os.path.dirname(os.path.dirname(HIER)))
import as_messung as M      # noqa: E402
import mk_messung as MK     # noqa: E402
import v32_vorpruefung as V  # noqa: E402
import wl_messung as W      # noqa: E402

K, IDX, POS, BTCV = M.K, M.IDX, M.POS, M.BTCV
RNG = np.random.default_rng(20261033)
KERN = ("BTC", "ETH", "SOL")


def ro(p):
    return sqlite3.connect("file:%s?mode=ro" % p, uri=True)


# ---------------------------------------------------------------- Reihen
def fred(s, verzug):
    r = requests.get("https://fred.stlouisfed.org/graph/fredgraph.csv?id=" + s, timeout=90)
    d = pd.read_csv(io.StringIO(r.text))
    d.columns = ["datum", s]
    d["datum"] = pd.to_datetime(d.datum) + pd.Timedelta(days=verzug)
    return pd.to_numeric(d.set_index("datum")[s], errors="coerce").dropna()


def reihen():
    R = {}
    w = pd.concat([fred("WALCL", 2), fred("WTREGEN", 2), fred("RRPONTSYD", 1).resample("W-WED").last().shift(0)], axis=1).ffill().dropna()
    R["netto"] = (w["WALCL"] - w["WTREGEN"] - w["RRPONTSYD"] * 1000) / 1e6
    R["m2"] = fred("M2SL", 35)
    R["zins"] = fred("DFF", 1)
    R["dollar"] = fred("DTWEXBGS", 1)
    R["spx"] = fred("SP500", 1)
    R["us10"] = fred("DGS10", 1)
    j = requests.get("https://stablecoins.llama.fi/stablecoincharts/all", timeout=90).json()
    R["stable"] = pd.Series({pd.Timestamp(int(x["date"]), unit="s").normalize() + pd.Timedelta(days=1): x["totalCirculatingUSD"].get("peggedUSD", 0) for x in j}).sort_index()
    fg = pd.read_sql("select date, fear_greed_value from macro_snapshot where fear_greed_value is not null", ro("data/tradinginfotool.db"), parse_dates=["date"])
    R["fg"] = fg.groupby("date").fear_greed_value.mean().sort_index()
    dom = pd.read_sql("select stunde, close from btcdom", ro("data/richtung_historie.db"))
    dom["tag"] = pd.to_datetime(dom.stunde.str[:10])
    R["dom"] = dom.groupby("tag").close.last()
    f = pd.read_sql("select symbol, datum, wert from funding", ro("data/funding_historie.db"), parse_dates=["datum"])
    f = f[~f.symbol.isin(KERN)]
    R["funding"] = f.groupby("datum").wert.median().rolling(7, min_periods=4).mean()
    oi = pd.read_sql("select symbol, tag, oi_wert from terminmarkt_tag", ro("data/terminmarkt_historie.db"), parse_dates=["tag"])
    oi = oi[~oi.symbol.isin(KERN)].pivot_table(index="tag", columns="symbol", values="oi_wert")
    R["oi30"] = (oi / oi.shift(30) - 1).median(axis=1)
    return R


def asof(r, d):
    x = r[:d]
    return x.iloc[-1] if len(x) else np.nan


def aend(r, d, tage):
    a, b = asof(r, d), asof(r, d - pd.Timedelta(days=tage))
    return a / b - 1 if (a == a and b == b and b) else np.nan


def breite_tag(d):
    t = d.to_period("M").to_timestamp()
    if t not in POS:
        return np.nan
    _, rg = MK.rang_mw(t)
    top = [s for s in rg.sort_values().index[:51] if s != "BTC"][:50]
    i = int(np.searchsorted(IDX, d, side="right")) - 1
    b90 = BTCV[i] / BTCV[i - 90]
    x = [K[s].values[i] / K[s].values[i - 90] > b90 for s in top if K[s].values[i - 90] > 0 and K[s].values[i] == K[s].values[i]]
    return np.mean(x) if x else np.nan


def lage(d, R):
    i = int(np.searchsorted(IDX, d, side="right")) - 1
    eth = K["ETH"].values
    return {"BTC 90T": BTCV[i] / BTCV[i - 90] - 1, "BTC unter Hoch": 1 - BTCV[i] / np.nanmax(BTCV[:i + 1]),
            "ETH/BTC 30T": (eth[i] / eth[i - 30]) / (BTCV[i] / BTCV[i - 30]) - 1, "Breite": breite_tag(d),
            "Funding Alts": asof(R["funding"], d), "OI Alts 30T": asof(R["oi30"], d), "Fear&Greed": asof(R["fg"], d),
            "Netto-Liq 13W": aend(R["netto"], d, 91), "Stablecoins 30T": aend(R["stable"], d, 30), "Zins 90T": asof(R["zins"], d) - asof(R["zins"], d - pd.Timedelta(days=90)),
            "Dollar 30T": aend(R["dollar"], d, 30), "S&P 30T": aend(R["spx"], d, 30), "US10J 30T": asof(R["us10"], d) - asof(R["us10"], d - pd.Timedelta(days=30))}


CHRONIK = [("2023-03-10", "US-Bankenkrise (SVB)"), ("2024-01-10", "BTC-Spot-ETF zugelassen"), ("2024-04-20", "BTC-Halving"),
           ("2024-07-23", "ETH-Spot-ETF Handelsstart"), ("2024-08-05", "Carry-Trade-Ausverkauf (Yen)"), ("2024-09-18", "erste Fed-Senkung"),
           ("2024-11-05", "US-Wahl"), ("2025-04-02", "US-Zollpaket"), ("2025-10-10", "Liquidationswelle 10./11.10. (Nutzer: Manipulation)")]


# ---------------------------------------------------------------- Teil 1
def signale(dom, schwelle, luecke=14):
    ch = dom / dom.shift(30) - 1
    an = ch[ch >= schwelle].index
    out = []
    for d in an:
        if not out or (d - out[-1][1]).days >= luecke:
            out.append([d, d])
        else:
            out[-1][1] = d
    return [a for a, _ in out]


def paar_suche(X, y):
    """Median-Teilung je Merkmal; je Paar 4 Felder; Youden = Anteil Treffer im Feld - Anteil Fehlalarme im Feld; bestes je Paar."""
    nT, nF = y.sum(), (~y).sum()
    B = (X >= X.median()).astype(int).where(X.notna())
    erg = []
    for a, b in itertools.combinations(X.columns, 2):
        for va, vb in itertools.product((0, 1), (0, 1)):
            m = (B[a] == va) & (B[b] == vb)
            tp, fa = int((m & y).sum()), int((m & ~y).sum())
            erg.append((tp / nT - fa / nF, a, "hoch" if va else "tief", b, "hoch" if vb else "tief", tp, fa))
    erg.sort(reverse=True)
    return erg


def teil1(R):
    I = pd.read_csv(os.path.join("data", "_spot", "v32_altindex_mw.csv"), sep=";", index_col=0, parse_dates=True).iloc[:, 0]
    E = V.episoden(I)
    tiefs = list(E.tief)
    dom = R["dom"]
    print("TEIL 1 - EBENE 2: Dominanz-Spitze (BTCDOM 30 T) gegen die %d Rally-Tiefs %s\n" % (len(tiefs), ", ".join(str(t.date()) for t in tiefs)))
    print("  Dosis (Signale = erste Tage, Luecke 14 T; Treffer = Rally-Tief 10 T vor bis 45 T nach dem Signal):")
    for s in (0.05, 0.087, 0.12, 0.15):
        sg = signale(dom, s)
        tr = [any(-10 <= (t - d).days <= 45 for t in tiefs) for d in sg]
        erfasst = sum(any(-10 <= (t - d).days <= 45 for d in sg) for t in tiefs)
        print("    Schwelle %4.1f %%: Signale %2d · Treffer %2d · Fehlalarm %2d (%.0f %%) · Rallyes erfasst %d von %d" % (
            100 * s, len(sg), sum(tr), len(sg) - sum(tr), 100 * (1 - np.mean(tr)) if sg else 0, erfasst, len(tiefs)))
    sg = signale(dom, 0.087)
    # KORREKTUR vor der Bewertung: Basisrate - wie oft liegt ein BELIEBIGER Tag 10 T vor bis 45 T nach einem Rally-Tief?
    tage = dom.index[(dom.index >= dom.index[30]) & (dom.index <= dom.index[-1] - pd.Timedelta(days=45))]
    basis = np.mean([any(-10 <= (t - d).days <= 45 for t in tiefs) for d in tage])
    quote = np.mean([any(-10 <= (t - d).days <= 45 for t in tiefs) for d in sg])
    zq = []
    for _ in range(2000):
        z, letzt = [], None
        for d in sorted(RNG.choice(tage, size=len(sg) * 3, replace=False)):
            d = pd.Timestamp(d)
            if letzt is None or (d - letzt).days >= 14:
                z.append(d); letzt = d
            if len(z) == len(sg):
                break
        zq.append(np.mean([any(-10 <= (t - d).days <= 45 for t in tiefs) for d in z]))
    print("\n  BASISRATE: ein beliebiger Tag liegt in %.0f %% der Faelle 10 T vor bis 45 T nach einem Rally-Tief · Dominanz-Spitze %.0f %% (Lift %.2f) · "
          "Zufalls-Signale (%d Tage, 14 T Abstand, 2.000 Welten) erreichen %.0f %% oder mehr in %.0f %% der Welten" % (
              100 * basis, 100 * quote, quote / basis, len(sg), 100 * quote, 100 * np.mean(np.array(zq) >= quote - 1e-12)))
    zeilen = []
    for d in sg:
        z = lage(d, R)
        z["Signal"] = d
        z["Treffer"] = any(-10 <= (t - d).days <= 45 for t in tiefs)
        z["Index 60T danach"] = I[d:d + pd.Timedelta(days=60)].max() / I[:d].iloc[-1] - 1 if len(I[:d]) else np.nan
        z["Chronik"] = "; ".join(n for c, n in CHRONIK if -30 <= (pd.Timestamp(c) - d).days <= 45)
        zeilen.append(z)
    S = pd.DataFrame(zeilen).set_index("Signal")
    print("\n  JEDES SIGNAL (Schwelle 8,7 %%), Lage am Signaltag:")
    sp = ["BTC 90T", "BTC unter Hoch", "ETH/BTC 30T", "Breite", "Funding Alts", "OI Alts 30T", "Fear&Greed", "Netto-Liq 13W", "Stablecoins 30T", "Zins 90T", "Dollar 30T", "S&P 30T", "US10J 30T"]
    fmt = {"Funding Alts": "{:+.5f}", "Fear&Greed": "{:.0f}", "Zins 90T": "{:+.2f}", "US10J 30T": "{:+.2f}", "Breite": "{:.2f}"}
    print("    %-10s %-7s %s | Index 60T | Chronik" % ("Signal", "", " ".join("%-12s" % c[:12] for c in sp)))
    for d, r in S.iterrows():
        werte = []
        for c in sp:
            v = r[c]
            werte.append("%-12s" % ("-" if v != v else (fmt.get(c, "{:+.0%}").format(v))))
        print("    %s %-7s %s | %+5.0f %% | %s" % (d.date(), "TREFFER" if r.Treffer else "fehl", " ".join(werte), 100 * r["Index 60T danach"], r.Chronik))
    y = S.Treffer.values.astype(bool)
    X = S[sp].astype(float)
    print("\n  MITTEL Treffer gegen Fehlalarm: %s" % " · ".join("%s %s/%s" % (c, (fmt.get(c, "{:+.0%}")).format(X[c][y].mean()), (fmt.get(c, "{:+.0%}")).format(X[c][~y].mean())) for c in sp))
    if y.sum() >= 2 and (~y).sum() >= 2:
        erg = paar_suche(X, pd.Series(y, index=X.index))
        best = erg[0][0]
        zuf = []
        for _ in range(1000):
            yp = pd.Series(RNG.permutation(y), index=X.index)
            zuf.append(paar_suche(X, yp)[0][0])
        p = float(np.mean(np.array(zuf) >= best - 1e-12))
        print("\n  PAAR-SUCHE (%d Merkmale, %d Paare x 4 Felder): bestes Youden %.2f · der ZUFALL erreicht das in %.0f %% der 1.000 Vertauschungen -> %s" % (
            len(sp), len(list(itertools.combinations(sp, 2))), best, 100 * p, "ANSATZ" if p < 0.05 else "KEIN Ansatz (vom Zufall nicht zu unterscheiden)"))
        for e in erg[:6]:
            print("    Youden %.2f · %s %s UND %s %s · Treffer %d von %d · Fehlalarm %d von %d" % (e[0], e[1], e[2], e[3], e[4], e[5], y.sum(), e[6], (~y).sum()))
    S.to_csv(os.path.join("data", "_spot", "e33_signale.csv"), sep=";")
    return S


# ---------------------------------------------------------------- Teil 2
def altindex_lang(start="2019-01-01", gewicht="mw"):
    r_tag = K.pct_change(fill_method=None)
    b_tag = pd.Series(BTCV, index=IDX).pct_change()
    werte = []
    for t in pd.date_range(start, M.ENDE, freq="MS"):
        if t not in POS:
            continue
        _, rg = MK.rang_mw(t)
        top = [s for s in rg.sort_values().index if s not in KERN][:100]
        i = POS[t]
        w = pd.Series({s: MK.umlauf(s, t) * K[s].values[i] for s in top}).dropna()
        w = w[w > 0]
        if gewicht == "gleich":
            w = w * 0 + 1
        mt = IDX[(IDX > t) & (IDX <= t + pd.DateOffset(months=1))]
        rr = r_tag.loc[mt, w.index]
        tr = rr.mul(w, axis=1).sum(axis=1) / rr.notna().mul(w, axis=1).sum(axis=1)
        werte.append((1 + tr) / (1 + b_tag.loc[mt]) - 1)
    rel = pd.concat(werte)
    return (1 + rel[~rel.index.duplicated()].fillna(0)).cumprod()


PHASEN = [("2020-04-10", "2020-06-17"), ("2020-11-12", "2021-03-23"), ("2022-05-11", "2022-06-15"), ("2023-10-16", "2023-10-25")]


def teil2(R):
    print("\n\nTEIL 2 - EBENE 1: Seasons 2019-2026 je Quartal (Beschreibung; Umlauf vor 21.09.2025 von heute = Vorgriff -> marktwertgewichtet vor 2025 VERZERRT, gleichgewichtet daneben)")
    print("  'Season' = Quartal ueberschneidet [Phasenbeginn, Phasenende + 90 T] (die S1-Phasen sind EINSTIEGSzeitraeume, der Gewinn faellt in den 90 T danach an)")
    I = altindex_lang()
    IG = altindex_lang(gewicht="gleich")
    print("  Quartal  Season  Alt/BTC MW  gleich   BTC     ETH/BTC  Netto-Liq  M2 J/J   Leitzins  Stablecoins  S&P")
    zeilen = []
    for q in pd.period_range("2019Q2", pd.Timestamp(M.ENDE).to_period("Q"), freq="Q"):
        a, e = q.start_time, min(q.end_time.normalize(), M.ENDE)
        if a not in POS and len(IDX[IDX >= a]) == 0:
            continue
        ia, ie = int(np.searchsorted(IDX, a)), int(np.searchsorted(IDX, e, side="right")) - 1
        season = any(pd.Timestamp(x) <= e and pd.Timestamp(y) + pd.Timedelta(days=90) >= a for x, y in PHASEN)
        alt = I[:e].iloc[-1] / I[:a].iloc[-1] - 1 if len(I[:a]) else np.nan
        altg = IG[:e].iloc[-1] / IG[:a].iloc[-1] - 1 if len(IG[:a]) else np.nan
        z = dict(q=str(q), season=season, alt=alt, altg=altg, btc=BTCV[ie] / BTCV[ia] - 1,
                 eth=(K["ETH"].values[ie] / K["ETH"].values[ia]) / (BTCV[ie] / BTCV[ia]) - 1,
                 netto=aend(R["netto"], e, 91), m2=aend(R["m2"], e, 365), zins=asof(R["zins"], e) - asof(R["zins"], a),
                 stable=aend(R["stable"], e, 91), spx=aend(R["spx"], e, 91))
        zeilen.append(z)
        print("  %s  %-6s  %+6.0f %%   %+6.0f %%  %+5.0f %%  %+5.0f %%   %+5.1f %%    %+5.1f %%  %+5.2f     %+6.0f %%      %+4.0f %%" % (
            z["q"], "SEASON" if season else "", 100 * alt, 100 * altg, 100 * z["btc"], 100 * z["eth"], 100 * z["netto"], 100 * z["m2"], z["zins"], 100 * z["stable"], 100 * z["spx"]))
    Q = pd.DataFrame(zeilen)
    s = Q[Q.season]
    print("\n  In den Season-Quartalen (%d) gegen die uebrigen (%d), Mittel:" % (len(s), len(Q) - len(s)))
    for c, n in (("altg", "Alt/BTC gleich"), ("btc", "BTC"), ("netto", "Netto-Liq"), ("m2", "M2 J/J"), ("zins", "Leitzins-Aend."), ("stable", "Stablecoins"), ("eth", "ETH/BTC")):
        print("    %-15s Season %+7.2f · uebrige %+7.2f" % (n, s[c].mean(), Q[~Q.season][c].mean()))
    kombi = (Q.btc > 0.2) & (Q.m2 > 0.05) & (Q.stable > 0.1)
    print("  Kombination 'BTC > +20 %% im Quartal UND M2 > +5 %% J/J UND Stablecoins > +10 %% im Quartal' (aus der Erzaehlung 2020/21, nicht gefittet): an in %d Quartalen, davon Season %d: %s" % (
        int(kombi.sum()), int((kombi & Q.season).sum()), ", ".join(Q[kombi].q)))
    Q.to_csv(os.path.join("data", "_spot", "e33_quartale.csv"), sep=";", index=False)
    return I


# ---------------------------------------------------------------- Teil 3
def teil3(I):
    print("\n\nTEIL 3 - F1: Kosten-Nutzen der Season-Option (Rolle L)")
    L = pd.read_csv(os.path.join("data", "_spot", "fb_messung_l.csv"), sep=";", parse_dates=["t"])
    c_halten = -L.groupby("t").halten_btc.mean().mean()
    c_regel = -L.groupby("t").gg_btc.mean().mean()
    print("  Kosten je Jahr ab 2024 (L-Korb gegen BTC, Mittel der Starttag-Koerbe): halten %.0f %% · mit Mitnahme x3 %.0f %% · (je Position Median: halten %.0f %%)" % (
        100 * c_halten, 100 * c_regel, -100 * L.halten_btc.median()))
    D = MK.paare_mw(365).reset_index(drop=True)
    Z = M.Zellen(D)
    D["fuenftel"] = M.pct_in_zelle(Z, W.wert(Z, M.merkmale(D))) > 0.8
    for a, e in PHASEN[:2]:
        t = pd.Timestamp(a).to_period("M").to_timestamp()
        g = D[(D.t == t)]
        ia, ie = int(np.searchsorted(IDX, pd.Timestamp(a))), int(np.searchsorted(IDX, pd.Timestamp(e), side="right")) - 1
        def korb(sy, zeige=False):
            x = {s: (K[s].values[ie] / K[s].values[ia]) / (BTCV[ie] / BTCV[ia]) - 1 for s in sy if K[s].values[ia] == K[s].values[ia] and K[s].values[ie] == K[s].values[ie]}
            v = np.array(list(x.values()))
            if zeige and len(v):
                top = sorted(x.items(), key=lambda kv: -kv[1])[:5]
                print("      groesste Beitraege: %s · Mittel %+.0f %% · Median %+.0f %% · gestutzt (ohne obere/untere 10 %%) %+.0f %%" % (
                    " ".join("%s %+.0f %%" % (s, 100 * w) for s, w in top), 100 * v.mean(), 100 * np.median(v),
                    100 * np.mean(np.sort(v)[int(len(v) * 0.1):max(int(len(v) * 0.9), int(len(v) * 0.1) + 1)])))
            # KORREKTUR vor der Bewertung: der MEDIAN ist der Season-Vorsprung (ein Mittel wird von Einzelwerten/Datenfehlern getragen)
            return (np.median(v) if len(v) else np.nan), len(v)
        print("    L-Korb:")
        gf, nf = korb(g[g.fuenftel].sym, zeige=True)
        print("    alle der Klassen:")
        ga, na = korb(g.sym, zeige=True)
        gi = I[:pd.Timestamp(e)].iloc[-1] / I[:pd.Timestamp(a)].iloc[-1] - 1
        print("  Season %s bis %s (Einstiegszeitraum; Ergebnis bis Phasenende): L-Korb Median (Fuenftel am %s, n %d) gegen BTC %+.0f %% · alle der Klassen Median (n %d) %+.0f %% · Altindex MW %+.0f %%" % (a, e, t.date(), nf, 100 * gf, na, 100 * ga, 100 * gi))
        for G, nm in ((gf, "L-Korb"), (gi, "Altindex")):
            if G == G:
                for c, cn in ((c_halten, "halten"), (c_regel, "Mitnahme")):
                    for k, kn in ((0.0072, "H"), (0.0176, "M"), (0.064, "S")):
                        if c > 0:
                            T = np.log((1 + G) * (1 - k)) / -np.log(1 - c)
                            if kn == "M":
                                print("    Break-even %-8s %-9s Kosten Hin+Rueck %s: Season darf hoechstens %.1f Jahre auf sich warten lassen" % (nm, cn, kn, T))
    print("  (Break-even: (1 + G) x (1 - k) x (1 - c)^T = 1; G Season-Vorsprung, c Kosten je Jahr, k Handelskosten Hin+Rueck je Klasse aus §32.1 D)")


def main():
    print("§33 · Kurse bis %s\n" % M.ENDE.date())
    R = reihen()
    teil1(R)
    I = teil2(R)
    teil3(I)


if __name__ == "__main__":
    main()
