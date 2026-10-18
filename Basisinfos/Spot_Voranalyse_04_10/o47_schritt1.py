"""O47 Schritt 1 (18.10.2026, Spot §59.4, vorab 08f61223): BRUECKE - findet ein Korb aus den CMC-Wochenaufnahmen dieselben Seasons wie S1?

    python Basisinfos/Spot_Voranalyse_04_10/o47_schritt1.py

Nur 2019-04 bis 2026-06 (Kalibrierungszeitraum); der Korb beginnt mit dem Monat 2019-04 (Umsatz aus den Aufnahmen ab 2019-03). Der Holdout
2017/18 wird NICHT beruehrt.
Korb: je Monatserstem (erster Sonntag des Monats) Top 50 nach Umsatz (Mittel der letzten 4 Aufnahmen) unter den Top 200 nach Marktwert,
ohne BTC und Stablecoins (Kuerzelliste und Wochenrendite im Median betragsmaessig < 0,5 %), gefuehrt ueber die CMC-ID, gleich gewichtet,
Wochenrendite Sonntag zu Sonntag. Faellt ein Coin aus den Top 200: Rendite aus CoinMetrics (PriceUSD), wenn vorhanden, sonst -100 % beim
ERSTEN Fehlen, danach 0 bis zum Monatswechsel (Gegenrechnung: 0 % wie S1 'fillna(0)').
Wahrheit: Korb schlaegt BTC in den folgenden 13 Wochen um >= 25 Pp. Vergleich an denselben Sonntagen mit S1 (am_kalibrierung.csv 'season').
Urteil (vorab): ZULAESSIG = gleich an >= 90 % der Sonntage UND beide grossen S1-Episoden (2020-04, 2020-11) mit einer Korb-Episode, Start
+- 28 T UND keine zusaetzliche Korb-Episode >= 28 T ausserhalb +- 30 T der S1-Episoden; sonst UNZULAESSIG.
"""
import os
import sqlite3
import sys
import time

import numpy as np
import pandas as pd
import requests

WURZEL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(WURZEL)
import s1_messung as S1  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass
STAB = {"USDT", "USDC", "TUSD", "PAX", "USDP", "GUSD", "DAI", "BUSD", "HUSD", "USDK", "SAI", "BITUSD", "NUSD", "USDS", "SUSD", "EURS", "USDN",
        "UST", "USTC", "FEI", "FRAX", "LUSD", "USDD", "FDUSD", "PYUSD", "USDE", "USD1", "RLUSD", "TUSDB", "XSGD", "EURC", "EURT", "USDX", "USDJ",
        "GHO", "CRVUSD", "MIM", "ALUSD", "OUSD", "DOLA", "USDB", "USR", "USDY", "BUIDL", "USYC", "SUSDE", "PAXG", "XAUT", "WBTC", "STETH",
        "WSTETH", "WETH", "WBETH", "CBBTC", "BTCB", "RENBTC", "HBTC", "WEETH", "RETH", "CBETH", "METH", "EZETH", "RSETH", "LBTC", "SOLVBTC",
        "BSC-USD", "USDTB", "USDF", "USDG", "USD0", "DEUSD", "AUSD", "USX"}
A, E = "2019-03-01", "2026-10-31"
KORB_AB = pd.Timestamp("2019-04-01")
CM = "https://community-api.coinmetrics.io/v4"


def lade():
    c = sqlite3.connect("file:data/_spot/o47_cm.db?mode=ro", uri=True, timeout=30)
    W = pd.read_sql("SELECT stichtag, id, symbol, preis, cap, umsatz FROM cmc_woche WHERE stichtag>=? AND stichtag<=?", c, params=(A, E),
                    parse_dates=["stichtag"])
    c.close()
    return W


def cm_preis(paare):
    """CoinMetrics PriceUSD fuer (Kuerzel, Tag)-Paare; Kuerzel ohne CoinMetrics-Kurs -> None. Zwischenablage in o47_cm.db 'tag'."""
    kat = requests.get(CM + "/catalog-v2/asset-metrics", params={"metrics": "PriceUSD", "page_size": 10000}, timeout=120).json()["data"]
    hat = {a["asset"] for a in kat}
    c = sqlite3.connect(os.path.join("data", "_spot", "o47_cm.db"), timeout=60)
    aus = {}
    je = {}
    for s, t in paare:
        if s.lower() in hat:
            je.setdefault(s.lower(), set()).add(t)
    for a, ts in je.items():
        ts = sorted(ts)
        da = dict(c.execute("SELECT tag, PriceUSD FROM tag WHERE asset=? AND PriceUSD IS NOT NULL AND tag>=? AND tag<=?",
                            (a, ts[0].strftime("%Y-%m-%d"), ts[-1].strftime("%Y-%m-%d"))).fetchall())
        if not all(t.strftime("%Y-%m-%d") in da for t in ts):
            r = requests.get(CM + "/timeseries/asset-metrics", params={"assets": a, "metrics": "PriceUSD", "frequency": "1d", "page_size": 10000,
                                                                      "start_time": ts[0].strftime("%Y-%m-%d"), "end_time": ts[-1].strftime("%Y-%m-%d")},
                             timeout=120).json().get("data", [])
            rows = [(a, x["time"][:10], float(x["PriceUSD"])) for x in r if x.get("PriceUSD")]
            c.executemany("INSERT INTO tag (asset, tag, PriceUSD) VALUES (?,?,?) ON CONFLICT(asset, tag) DO UPDATE SET PriceUSD=excluded.PriceUSD", rows)
            c.commit()
            da.update({t: p for _a, t, p in rows})
            time.sleep(0.7)
        for t in ts:
            aus[(a, t)] = da.get(t.strftime("%Y-%m-%d"))
    c.close()
    return aus


def korb(W, ausfall="minus100", ranking="umsatz"):
    P = W.pivot_table(index="stichtag", columns="id", values="preis")
    V = W.pivot_table(index="stichtag", columns="id", values="umsatz")
    C = W.pivot_table(index="stichtag", columns="id", values="cap")
    sym = W.groupby("id").symbol.last()
    wr = P / P.shift(1) - 1
    stabil = {i for i in P.columns if str(sym.get(i, "")).upper() in STAB or (wr[i].abs().median() < 0.005 if wr[i].notna().sum() >= 4 else False)}
    btc = int(W[W.symbol == "BTC"].groupby("id").size().idxmax())
    alle = [i for i in P.columns if i != btc and i not in stabil]
    wochen = P.index[P.index >= KORB_AB]
    erster = {}
    for w in wochen:
        erster.setdefault((w.year, w.month), w)
    fehlen = []
    tops, rets = {}, {}
    for k in range(len(wochen) - 1):
        w, w1 = wochen[k], wochen[k + 1]
        m0 = erster[(w.year, w.month)]
        if m0 not in tops:
            i0 = P.index.get_loc(m0)
            da = [i for i in alle if P.loc[m0].get(i) == P.loc[m0].get(i)]
            maß = (V.iloc[max(0, i0 - 3):i0 + 1][da].mean() if ranking == "umsatz" else C.loc[m0, da])
            tops[m0] = list(maß.dropna().sort_values(ascending=False).index[:50])
        top = tops[m0]
        r = []
        for i in top:
            p0, p1 = P.loc[w].get(i), P.loc[w1].get(i)
            if p0 == p0 and p1 == p1:
                r.append(p1 / p0 - 1)
            elif p0 == p0:
                fehlen.append((i, str(sym.get(i, "")), w, w1))
                r.append(np.nan)                                       # wird unten gefuellt
            else:
                r.append(0.0)                                          # nach dem ersten Fehlen: 0 bis zum Monatswechsel
        rets[w1] = r
    return P, btc, sym, stabil, tops, rets, fehlen, wochen


def wahrheit(P, btc, tops, wochen, rets, fehlen, ersatz, ausfall):
    werte = {}
    zaehl = {"cm": 0, "minus100_oder_0": 0}
    for i, s, w, w1 in fehlen:
        e0, e1 = ersatz.get((s.lower(), w)), ersatz.get((s.lower(), w1))
        if e0 and e1:
            werte[(i, w1)] = e1 / e0 - 1
            zaehl["cm"] += 1
        else:
            werte[(i, w1)] = -1.0 if ausfall == "minus100" else 0.0
            zaehl["minus100_oder_0"] += 1
    kr = pd.Series(0.0, index=wochen)
    for k in range(len(wochen) - 1):
        w, w1 = wochen[k], wochen[k + 1]
        top = tops[[m for m in tops if m <= w][-1]]
        r = []
        for i, v in zip(top, rets[w1]):
            r.append(werte.get((i, w1), v) if v != v else v)
        kr[w1] = float(np.mean(r))
    ki = (1 + kr).cumprod()
    b = P[btc].reindex(wochen)
    rel = (ki.shift(-13) / ki) / (b.shift(-13) / b) - 1
    return rel, zaehl, ki


def bewerte(rel, S1t, ep_s1, name):
    gem = pd.concat([rel.rename("k"), S1t.rename("s")], axis=1).dropna()
    gem = gem[(gem.index >= "2019-04-01") & (gem.index <= "2026-06-22")]
    kw, sw = gem.k >= 0.25, gem.s.astype(bool)
    gleich = float((kw == sw).mean())
    ep_k = S1.episoden(kw)
    gross = [x for x in ep_s1 if (x[1] - x[0]).days >= 30][:2]
    treffer = []
    for a, e in gross:
        t = [x for x in ep_k if abs((x[0] - a).days) <= 28]
        treffer.append((a, t[0] if t else None))
    zusatz = [x for x in ep_k if (x[1] - x[0]).days >= 28 and not any(x[0] <= se + pd.Timedelta(days=30) and x[1] >= sa - pd.Timedelta(days=30)
                                                                       for sa, se in ep_s1)]
    ok = gleich >= 0.90 and all(t for _a, t in treffer) and not zusatz
    print("%s: %d Sonntage verglichen · gleich %.1f %% · Season-Wochen Korb %d, S1 %d · beide Season %d, nur Korb %d, nur S1 %d" % (
        name, len(gem), 100 * gleich, int(kw.sum()), int(sw.sum()), int((kw & sw).sum()), int((kw & ~sw).sum()), int((~kw & sw).sum())))
    print("   Korb-Episoden: %s" % (" · ".join("%s..%s (%d T)" % (a.date(), e.date(), (e - a).days) for a, e in ep_k) or "keine"))
    for a, t in treffer:
        print("   S1-Episode %s: %s" % (a.date(), ("getroffen, Korb-Start %s (%+d T)" % (t[0].date(), (t[0] - a).days)) if t else "NICHT getroffen"))
    print("   zusaetzliche Korb-Episoden >= 28 T ausserhalb +-30 T: %s" % (" · ".join("%s..%s" % (a.date(), e.date()) for a, e in zusatz) or "keine"))
    print("   -> %s" % ("ZULAESSIG" if ok else "UNZULAESSIG"))
    return ok, gem


def main():
    W = lade()
    print("O47 SCHRITT 1 · Bruecke Wochenkorb gegen S1 · Aufnahmen %s..%s (%d Sonntage) · Holdout nicht beruehrt\n" % (
        W.stichtag.min().date(), W.stichtag.max().date(), W.stichtag.nunique()))
    P, btc, sym, stabil, tops, rets, fehlen, wochen = korb(W)
    print("BTC-ID %d · als Stablecoin/gebunden ausgeschlossen: %d IDs (u. a. %s)" % (btc, len(stabil), ", ".join(sorted({str(sym[i]) for i in stabil})[:15])))
    ersatz = cm_preis({(s, t) for _i, s, w, w1 in fehlen for t in (w, w1)})
    n_cw = sum(len(tops[[m for m in tops if m <= w][-1]]) for w in wochen[:-1])
    K = pd.read_csv(os.path.join("data", "_spot", "am_kalibrierung.csv"), sep=";", parse_dates=["date"]).set_index("date")
    S1t = K.season.astype(bool)
    ep_s1 = S1.episoden(S1t[(S1t.index >= "2019-04-01") & K.wahr_bekannt])
    print("S1-Episoden (taeglich): %s\n" % " · ".join("%s..%s" % (a.date(), e.date()) for a, e in ep_s1))
    erg = {}
    for ausfall in ("minus100", "null"):
        rel, z, ki = wahrheit(P, btc, tops, wochen, rets, fehlen, ersatz, ausfall)
        if ausfall == "minus100":
            print("AUSFAELLE (Coin binnen einer Woche nicht mehr in den Top 200): %d von %d Coin-Wochen (%.2f %%) · davon mit CoinMetrics-Kurs %d, "
                  "ohne (-100 %%) %d\n" % (len(fehlen), n_cw, 100 * len(fehlen) / n_cw, z["cm"], z["minus100_oder_0"]))
        erg[ausfall] = bewerte(rel, S1t, ep_s1, "Korb nach UMSATZ, Ausfall %s" % ("-100 %" if ausfall == "minus100" else "0 % (Gegenrechnung)"))
        print()
        if ausfall == "minus100":
            pd.DataFrame({"korb_index": ki, "rel13": rel}).to_csv(os.path.join("data", "_spot", "o47_schritt1.csv"), sep=";")
    P2, btc2, sym2, stabil2, tops2, rets2, fehlen2, wochen2 = korb(W, ranking="marktwert")
    ersatz2 = cm_preis({(s, t) for _i, s, w, w1 in fehlen2 for t in (w, w1)})
    rel2, _z, _k = wahrheit(P2, btc2, tops2, wochen2, rets2, fehlen2, ersatz2, "minus100")
    bewerte(rel2, S1t, ep_s1, "Auskunft: Korb nach MARKTWERT, Ausfall -100 %")
    print("\nURTEIL Schritt 1 (vorab, Korb nach Umsatz, Ausfall -100 %%): %s · Gegenrechnung 0 %%: %s" % (
        "ZULAESSIG" if erg["minus100"][0] else "UNZULAESSIG", "zulaessig" if erg["null"][0] else "unzulaessig"))


if __name__ == "__main__":
    main()
