"""P51 VORPRUEFUNG Makro-Umfeld (Spot §51.5, Stufe 1) - nur lesend; Abrufe FRED fredgraph.csv, yfinance, CoinMetrics Community (frei).

    python Basisinfos/Spot_Voranalyse_04_10/p51_vorpruefung.py

Wie im Plan §51.5 (vorab Commit 52bf0e00): neun Kanaele lang/kurz, Drittel im rollierenden 5-J-Fenster, Gesamt lang/kurz; Zielgroessen
T1 BTC 90/180 T, T2 Altkorb/BTC 90 T, M1-M3 Aktien, A1/A2 Gold/DBC. Vorpruefung: Rohabstand je Kanal (guenstiges minus ungunstiges
Drittel) ueber den ganzen Zeitraum und je Epoche, Nullwelt 200 zirkulaere Verschiebungen (Tage, Rand 365 T). Weiter zur Messung, wenn
mindestens ein Kanal oder Gesamt im aeusseren Zehntel der Nullwelt liegt UND in E3 dasselbe Vorzeichen hat.
"""
import io
import os
import sys

import numpy as np
import pandas as pd
import requests

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
os.chdir(os.path.dirname(os.path.dirname(HIER)))
RNG = np.random.default_rng(20261051)
NZ = 200
FENSTER, MINDEST = 1826, 1095
IDX = pd.date_range("2003-01-01", pd.Timestamp.today().normalize(), freq="D")


def fred(s, verzug):
    r = requests.get("https://fred.stlouisfed.org/graph/fredgraph.csv?id=" + s, timeout=120)
    d = pd.read_csv(io.StringIO(r.text))
    d.columns = ["datum", s]
    d["datum"] = pd.to_datetime(d.datum) + pd.Timedelta(days=verzug)
    return pd.to_numeric(d.set_index("datum")[s], errors="coerce").dropna()


def taeglich(r):
    return r.sort_index().reindex(r.index.union(IDX)).ffill().reindex(IDX)


def vor(r, tage):
    return r.shift(tage)                         # IDX ist taeglich ohne Luecke


# ══ Kanaele (Plan §51.5) ═══════════════════════════════════════════════════════════════════════════════════════════════
def kanaele():
    m2 = fred("M2SL", 35)
    m2y = taeglich(m2 / m2.shift(12) - 1)
    w = pd.concat([fred("WALCL", 2), fred("WTREGEN", 2), fred("RRPONTSYD", 1).resample("W-WED").last()], axis=1, sort=True).ffill().dropna()
    netto = taeglich((w["WALCL"] - w["WTREGEN"] - w["RRPONTSYD"] * 1000) / 1e6)
    real, zwei, kurve = taeglich(fred("DFII10", 1)), taeglich(fred("DGS2", 1)), taeglich(fred("T10Y2Y", 1))
    baa, nfci, dollar, vix = taeglich(fred("BAA10Y", 1)), taeglich(fred("NFCI", 5)), taeglich(fred("DTWEXBGS", 1)), taeglich(fred("VIXCLS", 1))
    K = {  # Name: (lang-Groesse, Vorzeichen lang, kurz-Groesse, Vorzeichen kurz)
        "K1 Geldmenge": (m2y, +1, m2y - vor(m2y, 91), +1),
        "K2 Netto-Liquiditaet": (netto / vor(netto, 364) - 1, +1, netto / vor(netto, 91) - 1, +1),
        "K3 Realzins": (real, -1, real - vor(real, 91), -1),
        "K4 Zinspfad 2J": (zwei, -1, zwei - vor(zwei, 91), -1),
        "K5 Kurve": (kurve, +1, None, None),
        "K6 Kredit BAA": (baa, -1, baa - vor(baa, 91), -1),
        "K7 NFCI": (nfci, -1, nfci - vor(nfci, 91), -1),
        "K8 Dollar": (dollar, -1, dollar / vor(dollar, 91) - 1, -1),
        "K9 VIX": (vix, -1, vix - vor(vix, 91), -1),
    }
    dk, d2 = kurve - vor(kurve, 91), zwei - vor(zwei, 91)
    k5_kurz = pd.Series(np.where((dk > 0) & (d2 < 0), 1.0, np.where((dk > 0) & (d2 > 0), -1.0, 0.0)), index=IDX)
    k5_kurz[dk.isna() | d2.isna()] = np.nan
    return K, k5_kurz


def score(x, vz):
    """Drittel im rollierenden 5-J-Fenster: guenstig +1, unguenstig -1, Mitte 0 (Richtung vz)."""
    p = x.rolling(FENSTER, min_periods=MINDEST).rank(pct=True)
    s = pd.Series(np.where(p > 2 / 3, vz, np.where(p < 1 / 3, -vz, 0)).astype(float), index=x.index)
    s[p.isna()] = np.nan
    return s


def scores():
    K, k5k = kanaele()
    S = {}
    for n, (lg, vl, kz, vk) in K.items():
        S[n + " lang"] = score(lg, vl)
        S[n + " kurz"] = k5k if kz is None else score(kz, vk)
    L = pd.concat([S[k] for k in S if k.endswith("lang")], axis=1)
    Kz = pd.concat([S[k] for k in S if k.endswith("kurz")], axis=1)
    for name, M in (("Gesamt lang", L), ("Gesamt kurz", Kz)):
        summe = M.sum(axis=1, min_count=6)
        S[name] = score(summe, +1)
    return S


# ══ Zielgroessen ═════════════════════════════════════════════════════════════════════════════════════════════════════════
def coinmetrics_btc():
    url, par, aus = "https://community-api.coinmetrics.io/v4/timeseries/asset-metrics", {
        "assets": "btc", "metrics": "PriceUSD", "frequency": "1d", "page_size": 10000, "start_time": "2010-07-01"}, {}
    while url:
        j = requests.get(url, params=par, timeout=120).json()
        for x in j.get("data", []):
            aus[pd.Timestamp(x["time"][:10])] = float(x["PriceUSD"])
        url, par = j.get("next_page_url"), None
    return pd.Series(aus).sort_index()


def yf_close(t):
    import yfinance as yf
    h = yf.Ticker(t).history(period="max", interval="1d", auto_adjust=False)
    h.index = pd.to_datetime(h.index.tz_localize(None).date)
    return h["Close"].astype(float)


def vorwaerts(p, h):
    """log-Ertrag ab dem Schluss des Folgetags ueber h Kalendertage (Preise taeglich vorwaerts gefuellt, nur echte Endtage)."""
    p = p.sort_index()
    pd_ = p.reindex(p.index.union(IDX)).ffill().reindex(IDX)
    return np.log(pd_.shift(-(1 + h)) / pd_.shift(-1))


def ziele():
    Z = {}
    btc = coinmetrics_btc()
    Z["T1 BTC 90T"] = (vorwaerts(btc, 90), "2013-01-01")
    Z["T1 BTC 180T"] = (vorwaerts(btc, 180), "2013-01-01")
    import s1_messung as S1
    s1 = S1.baue()
    Z["T2 Altkorb/BTC 90T"] = (vorwaerts(s1["korb"] / s1["Bi"], 90), "2019-01-01")
    ndx, rut, spx = yf_close("^NDX"), yf_close("^RUT"), yf_close("^GSPC")
    Z["M1 Nasdaq/SPX 90T"] = (vorwaerts(ndx / spx.reindex(ndx.index), 90), "2006-01-01")
    Z["M2 Russell/SPX 90T"] = (vorwaerts(rut / spx.reindex(rut.index), 90), "2006-01-01")
    Z["M3 SPX 90T"] = (vorwaerts(spx, 90), "2006-01-01")
    Z["A1 Gold 90T"] = (vorwaerts(yf_close("GC=F"), 90), "2006-01-01")
    Z["A2 DBC 90T"] = (vorwaerts(yf_close("DBC"), 90), "2006-01-01")
    return Z


# ══ Statistik ════════════════════════════════════════════════════════════════════════════════════════════════════════════
def epoche(t):
    return "E1" if t < pd.Timestamp("2021-01-01") else ("E2" if t < pd.Timestamp("2024-01-01") else "E3")


def abstand(s, y):
    plus, minus = y[s == 1], y[s == -1]
    if len(plus) < 5 or len(minus) < 5:
        return np.nan
    return float(plus.mean() - minus.mean())


def main():
    S = scores()
    Z = ziele()
    print("P51 VORPRUEFUNG Makro-Umfeld (§51.5) · Daten bis %s · Nullwelt %d zirkulaere Verschiebungen\n" % (IDX[-1].date(), NZ))
    weiter = []
    for zn, (y, ab) in Z.items():
        print("=" * 150)
        print(zn)
        for sn, s in S.items():
            ok = s.notna() & y.notna() & (IDX >= pd.Timestamp(ab))
            pos = np.where(ok.values)[0]
            if len(pos) < 800:
                continue
            ss, yy = s.values[pos], y.values[pos]
            dts = IDX[pos]
            stich = np.array([d.day == 1 for d in dts])
            a = abstand(pd.Series(ss[stich]), pd.Series(yy[stich]))
            ep = {e: abstand(pd.Series(ss[stich & (np.array([epoche(d) for d in dts]) == e)]), pd.Series(yy[stich & (np.array([epoche(d) for d in dts]) == e)]))
                  for e in ("E1", "E2", "E3")}
            nul = []
            for _ in range(NZ):
                k = int(RNG.integers(365, len(pos) - 365))
                nul.append(abstand(pd.Series(np.roll(ss, k)[stich]), pd.Series(yy[stich])))
            nul = np.array([x for x in nul if x == x])
            rang = float(np.mean(nul < a)) if len(nul) and a == a else np.nan
            aussen = rang == rang and (rang <= 0.10 or rang >= 0.90)
            e3_gleich = ep["E3"] == ep["E3"] and a == a and np.sign(ep["E3"]) == np.sign(a)
            if aussen and e3_gleich and zn.startswith("T"):
                weiter.append((zn, sn, a, rang))
            n_p, n_m = int((ss[stich] == 1).sum()), int((ss[stich] == -1).sum())
            print("  %-28s n+ %3d n- %3d · Abstand %+7.1f %% · E1 %s · E2 %s · E3 %s · Rang %.3f%s" % (
                sn, n_p, n_m, 100 * a if a == a else float("nan"), *["%+6.1f" % (100 * ep[e]) if ep[e] == ep[e] else "   -  " for e in ("E1", "E2", "E3")],
                rang, "  <-- aeusseres Zehntel, E3 gleich" if (aussen and e3_gleich) else (" (aeusseres Zehntel, E3 ANDERS)" if aussen else "")))
    print("\n" + "=" * 150)
    print("ENTSCHEIDUNG nach §51.5 (nur Krypto T1/T2): %s" % ("WEITER zur Messung - %d Faelle: %s" % (len(weiter), "; ".join(
        "%s %s %+.1f %% (Rang %.3f)" % (z, s, 100 * a, r) for z, s, a, r in weiter)) if weiter else "KEIN Kanal erfuellt die Bedingung -> Bericht und Abstimmung"))
    # Stand heute
    print("\nSTAND HEUTE (%s): %s" % (IDX[-1].date(), " · ".join("%s %s" % (k, {1.0: "+", -1.0: "-", 0.0: "0"}.get(v.dropna().iloc[-1], "?") if v.notna().any() else "?")
                                                         for k, v in S.items())))


if __name__ == "__main__":
    main()
