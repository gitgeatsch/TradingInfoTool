"""O47 Fassung 2 (F2-A) - Messung nach Spot §59.7 (vorab 02dae307). A1 Tor 2019-04..2026-06, A2 Holdout 2017-01..2019-03 NUR wenn A1 besteht.

    python Basisinfos/Spot_Voranalyse_04_10/o47_f2a.py

Wahrheit: Wochenkorb wie Schritt 1 (A1: o47_schritt1.csv unveraendert; A2: derselbe Code auf den Aufnahmen 2016-07..2019-07).
Ampel eingefroren (agent.season_ampel): B1/B2 A1 aus am_kalibrierung.csv, A2 CoinMetrics-BTC und FRED M2SL (+35 T); B3 verkettet (Schritt 0,
vor 2021 CoinMetrics); Breite aus dem Wochenkorb (13 Wochen gegen BTC, >= 20 Coins), fortgeschrieben.
Ablage der Tageswerte: data/_spot/o47_f2a_A1.csv, o47_f2a_A2.csv (fuer die Gegenprobe).
"""
import io
import os
import sqlite3
import sys

import numpy as np
import pandas as pd
import requests

WURZEL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, WURZEL)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(WURZEL)
import agent.season_ampel as SA  # noqa: E402
import o47_schritt0 as O0  # noqa: E402
import o47_schritt1 as O1  # noqa: E402
import s1_messung as S1  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass
H = {"User-Agent": "Mozilla/5.0 (TradingInfoTool Forschung)"}


def taeglich(r, idx):
    return r.sort_index().reindex(r.index.union(idx)).ffill().reindex(idx)


def breite_woche(P, btc, tops, wochen):
    """Anteil der Korb-Coins (Liste des Monats) mit 13-Wochen-Rendite ueber BTC, nur Coins mit beiden Kursen, mindestens 20."""
    aus = pd.Series(np.nan, index=wochen)
    pos = {w: k for k, w in enumerate(P.index)}
    for w in wochen:
        k = pos[w]
        if k < 13:
            continue
        w0 = P.index[k - 13]
        top = tops[[m for m in tops if m <= w][-1]]
        a = (P.loc[w, top] / P.loc[w0, top]).dropna()
        if len(a) >= 20:
            aus[w] = float((a > P.loc[w, btc] / P.loc[w0, btc]).mean())
    return aus


def stand(T):
    return (T.B1 > SA.SCHWELLE["B1"]).astype(int) + (T.B2 > SA.SCHWELLE["B2"]).astype(int) + (T.B3 > SA.SCHWELLE["B3"]).astype(int)


def k2(stand_so, wahr):
    g = pd.concat([stand_so.rename("st"), wahr.rename("w")], axis=1).dropna()
    basis = g.w.mean()
    r = g.groupby("st").w.agg(["size", "mean"])
    mono = all(r["mean"].iloc[i] < r["mean"].iloc[i + 1] for i in range(len(r) - 1)) and len(r) == 4
    lift3 = (r["mean"].get(3, np.nan) / basis) if basis else np.nan
    return r, basis, mono, lift3, len(g)


def episoden_lang(wahr):
    return [(a, e) for a, e in S1.episoden(wahr) if (e - a).days >= 28]


def h1h2(G, wahr, ep, ruhe_a, ruhe_e):
    h1 = []
    for a, e in ep:
        w = G[(G.index >= a - pd.Timedelta(days=120)) & (G.index <= a + pd.Timedelta(days=30))]
        vk = w.isin(["Vorlauf", "Season-Klima"])
        h1.append((a, e, bool(vk.any()), int((w == "Vorlauf").sum()), int((w == "Season-Klima").sum()), int((w == "Ueberhitzung").sum()),
                   (vk[vk].index.min() - a).days if vk.any() else None))
    R = G[(G.index >= ruhe_a) & (G.index <= ruhe_e)]
    sk = R == "Season-Klima"
    anteil = float(sk.mean())
    bloecke, fehl = [], []
    blk = (sk != sk.shift()).cumsum()
    for _, x in R[sk].groupby(blk[sk]):
        a, e = x.index[0], x.index[-1]
        if (e - a).days + 1 >= 30:
            season = bool(wahr[(wahr.index >= a) & (wahr.index <= e + pd.Timedelta(days=90))].any())
            bloecke.append((a, e, season))
            if not season:
                fehl.append((a, e))
    return h1, anteil, bloecke, fehl


def zeige_h(h1, anteil, bloecke, fehl):
    for a, e, ok, nv, ns, nu, erst in h1:
        print("   H1 Episode %s..%s (%d T): Vorlauf %d · Season-Klima %d · Ueberhitzung %d Tage im Fenster -> %s%s" % (
            a.date(), e.date(), (e - a).days, nv, ns, nu, "ERFUELLT" if ok else "nicht erfuellt",
            (" (erster Tag %+d T zum Start)" % erst) if erst is not None else ""))
    print("   H2 Season-Klima an %.1f %% der Ruhe-Tage (<= 10 %%) · Bloecke >= 30 T: %s -> ohne Season danach: %s" % (
        100 * anteil, " · ".join("%s..%s%s" % (a.date(), e.date(), "" if s else " OHNE Season") for a, e, s in bloecke) or "keine",
        len(fehl)))


def a1():
    K = pd.read_csv(os.path.join("data", "_spot", "am_kalibrierung.csv"), sep=";", parse_dates=["date"]).set_index("date")
    K = K[(K.index >= "2019-04-01") & K.wahr_bekannt & K[["B1", "B2", "B3"]].notna().all(axis=1)].copy()
    S0 = pd.read_csv(os.path.join("data", "_spot", "o47_schritt0.csv"), sep=";", parse_dates=[0], index_col=0)
    W1 = pd.read_csv(os.path.join("data", "_spot", "o47_schritt1.csv"), sep=";", parse_dates=[0], index_col=0)
    W = O1.lade()
    P, btc, _sym, _st, tops, _r, _f, wochen = O1.korb(W)
    br = breite_woche(P, btc, tops, wochen)
    T = K[["B1", "B2"]].copy()
    T["B3"] = S0.B3_V.reindex(T.index)
    T["Breite"] = taeglich(br.dropna(), T.index)
    G = SA.geltend(SA.stufen(T))
    st = stand(T)
    wahr = (W1.rel13 >= 0.25)[W1.rel13.notna()]
    wahr = wahr[(wahr.index >= "2019-04-01") & (wahr.index <= "2026-06-22")]
    r, basis, mono, lift3, n = k2(st.reindex(wahr.index), wahr)
    print("A1 TOR · 2019-04..2026-06 · %d Sonntage · Wahrheit = Wochenkorb (o47_schritt1.csv), Season-Wochen %.1f %%" % (n, 100 * basis))
    print("   K2: %s" % " · ".join("%d von 3: %d So, Season %.1f %% (Lift %.2f)" % (i, int(x["size"]), 100 * x["mean"], x["mean"] / basis)
                                  for i, x in r.iterrows()))
    besteht = bool(mono and lift3 >= 2)
    print("   Ordnung 0 < 1 < 2 < 3: %s · Lift 3 von 3 = %.2f (>= 2) -> A1 %s" % ("ja" if mono else "NEIN", lift3, "BESTEHT" if besteht else "STOPP"))
    ep = episoden_lang(wahr)
    h1, anteil, bloecke, fehl = h1h2(G, wahr, ep, pd.Timestamp("2021-06-01"), pd.Timestamp("2023-06-30"))
    print("   (Auskunft, dieselben Fragen im Kalibrierungszeitraum; Ruhe = Baerenmarkt 2021-06..2023-06)")
    zeige_h(h1, anteil, bloecke, fehl)
    pd.DataFrame({"B1": T.B1, "B2": T.B2, "B3": T.B3, "Breite": T.Breite, "stand": st, "geltend": G}).to_csv(
        os.path.join("data", "_spot", "o47_f2a_A1.csv"), sep=";")
    return besteht


def holdout_wahrheit(ausfall="minus100"):
    c = sqlite3.connect("file:data/_spot/o47_cm.db?mode=ro", uri=True, timeout=30)
    W = pd.read_sql("SELECT stichtag, id, symbol, preis, cap, umsatz FROM cmc_woche WHERE stichtag>='2016-07-01' AND stichtag<='2019-07-31'", c,
                    parse_dates=["stichtag"])
    c.close()
    alt = O1.KORB_AB
    O1.KORB_AB = pd.Timestamp("2016-08-01")
    try:
        P, btc, sym, stabil, tops, rets, fehlen, wochen = O1.korb(W)
    finally:
        O1.KORB_AB = alt
    ersatz = O1.cm_preis({(s, t) for _i, s, w, w1 in fehlen for t in (w, w1)})
    rel, z, ki = O1.wahrheit(P, btc, tops, wochen, rets, fehlen, ersatz, ausfall)
    n_cw = sum(len(tops[[m for m in tops if m <= w][-1]]) for w in wochen[:-1])
    return dict(P=P, btc=btc, sym=sym, stabil=stabil, tops=tops, wochen=wochen, rel=rel, ki=ki, z=z, fehlen=fehlen, n_cw=n_cw)


def holdout_ampel(br):
    tage = pd.date_range("2016-07-01", "2019-03-31")
    cm = sqlite3.connect("file:data/_spot/coinmetrics.db?mode=ro", uri=True)
    b = pd.read_sql("SELECT tag, PriceUSD FROM tag WHERE asset='btc'", cm, parse_dates=["tag"]).set_index("tag").PriceUSD
    cm.close()
    bi = taeglich(b, tage)
    m2 = pd.read_csv(io.StringIO(requests.get("https://fred.stlouisfed.org/graph/fredgraph.csv?id=M2SL", headers=H, timeout=90).text))
    m2.columns = ["datum", "m2"]
    m2["datum"] = pd.to_datetime(m2.datum) + pd.Timedelta(days=35)
    m2 = pd.to_numeric(m2.set_index("datum").m2, errors="coerce").dropna()
    _cm, _dl, v, _k = O0.reihen()
    sv = taeglich(v, tage)
    T = pd.DataFrame(index=tage)
    T["B1"] = bi / bi.shift(91) - 1
    T["B2"] = taeglich(m2 / m2.shift(12) - 1, tage)
    T["B3"] = sv / sv.shift(91) - 1
    T["Breite"] = taeglich(br.dropna(), tage)
    T = T[T.index >= "2016-10-01"]
    G = SA.geltend(SA.stufen(T))
    return T, G


def a2():
    hw = holdout_wahrheit()
    br = breite_woche(hw["P"], hw["btc"], hw["tops"], hw["wochen"])
    T, G = holdout_ampel(br)
    wahr = (hw["rel"] >= 0.25)[hw["rel"].notna()]
    wahr = wahr[(wahr.index >= "2017-01-01") & (wahr.index <= "2019-03-31")]
    print("\nA2 HOLDOUT · 2017-01-01..2019-03-31 · Wochenkorb %d Sonntage (Season-Wochen %d = %.1f %%) · Ausfaelle %d von %d Coin-Wochen (%.2f %%), "
          "davon mit CoinMetrics-Kurs %d, -100 %% %d" % (len(wahr), int(wahr.sum()), 100 * wahr.mean(), len(hw["fehlen"]), hw["n_cw"],
                                                        100 * len(hw["fehlen"]) / hw["n_cw"], hw["z"]["cm"], hw["z"]["minus100_oder_0"]))
    ep_alle = S1.episoden(wahr)
    ep = [x for x in ep_alle if (x[1] - x[0]).days >= 28]
    print("   Season-Episoden: %s (davon >= 28 T: %d)" % (" · ".join("%s..%s (%d T)" % (a.date(), e.date(), (e - a).days) for a, e in ep_alle) or "keine",
                                                          len(ep)))
    Gh = G[(G.index >= "2017-01-01")]
    wechsel = Gh[Gh != Gh.shift()]
    print("   geltende Stufe (Wechsel): %s" % " · ".join("%s %s" % (t.date(), s) for t, s in wechsel.items()))
    h1, anteil, bloecke, fehl = h1h2(G, wahr, ep, pd.Timestamp("2018-02-01"), pd.Timestamp("2019-03-31"))
    zeige_h(h1, anteil, bloecke, fehl)
    H1 = bool(ep) and all(x[2] for x in h1)
    H2 = anteil <= 0.10 and not fehl
    st = stand(T)
    r, basis, mono, lift3, n = k2(st.reindex(wahr.index), wahr)
    print("   H3 (Auskunft) K2 an %d Sonntagen: %s" % (n, " · ".join("%d von 3: %d So, Season %.1f %%" % (i, int(x["size"]), 100 * x["mean"])
                                                                for i, x in r.iterrows())))
    if not ep:
        urteil = "NUR RUHE GEPRUEFT: H2 %s" % ("erfuellt" if H2 else "NICHT erfuellt")
    else:
        urteil = "TRAEGT" if (H1 and H2) else ("TEILWEISE (H1 %s, H2 %s)" % ("ja" if H1 else "nein", "ja" if H2 else "nein") if (H1 or H2) else "TRAEGT NICHT")
    print("\n   Lage der Bedingungen (Auskunft) 30 T vor und am Start jeder Episode: %s" % " | ".join(
        "%s: B1 %+.0f/%+.0f %% · B2 %+.1f/%+.1f %% · B3 %+.0f/%+.0f %%" % (
            a.date(), 100 * T.B1.asof(a - pd.Timedelta(days=30)), 100 * T.B1.asof(a), 100 * T.B2.asof(a - pd.Timedelta(days=30)), 100 * T.B2.asof(a),
            100 * T.B3.asof(a - pd.Timedelta(days=30)), 100 * T.B3.asof(a)) for a, _e in ep_alle))
    hw0 = holdout_wahrheit("null")
    w0 = (hw0["rel"] >= 0.25)[hw0["rel"].notna()]
    w0 = w0[(w0.index >= "2017-01-01") & (w0.index <= "2019-03-31")]
    e0 = [x for x in S1.episoden(w0) if (x[1] - x[0]).days >= 28]
    h10, a0, _b0, f0 = h1h2(G, w0, e0, pd.Timestamp("2018-02-01"), pd.Timestamp("2019-03-31"))
    print("   Gegenrechnung Ausfall 0 %%: Season-Wochen %d, Episoden >= 28 T %s · H1 %s · H2 %s" % (
        int(w0.sum()), " · ".join("%s..%s" % (a.date(), e.date()) for a, e in e0) or "keine",
        "ja" if (e0 and all(x[2] for x in h10)) else "nein", "ja" if (a0 <= 0.10 and not f0) else "nein"))
    pd.DataFrame({"B1": T.B1, "B2": T.B2, "B3": T.B3, "Breite": T.Breite, "stand": st, "geltend": G}).to_csv(
        os.path.join("data", "_spot", "o47_f2a_A2.csv"), sep=";")
    pd.DataFrame({"korb_index": hw["ki"], "rel13": hw["rel"], "breite": br}).to_csv(os.path.join("data", "_spot", "o47_f2a_A2_korb.csv"), sep=";")
    print("\nURTEIL A2 (vorab §59.7): %s" % urteil)
    return urteil


def main():
    print("O47 FASSUNG 2 (F2-A) · Messplan §59.7 (vorab 02dae307)\n")
    if not a1():
        print("\nURTEIL: A1 STOPP - die eingefrorene Ampel ordnet gegen die Wochenkorb-Wahrheit nicht. Holdout NICHT gerechnet (bleibt ungesehen).")
        return
    a2()


if __name__ == "__main__":
    main()
