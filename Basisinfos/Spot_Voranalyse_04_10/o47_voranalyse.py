"""O47 VORANALYSE (18.10.2026, Spot §59) - Season-Ampel Fassung 2: echter Holdout auf 2017/18. NUR Datenlage, KEINE Ampel, KEINE Wahrheit.

    python Basisinfos/Spot_Voranalyse_04_10/o47_voranalyse.py

⚠️ Der Holdout bleibt UNGESEHEN: dieses Skript rechnet auf 2017/18 weder die Ampel (B1-B3, Stufe) noch die Wahrheit (Korb gegen BTC),
nur Abdeckung und Brueckentauglichkeit der Daten. Sonst waere der Messplan nicht mehr vorab.

Abrufe (frei, ohne Schluessel): CoinMetrics Community v4 (Katalog, PriceUSD/CapMrktCurUSD/SplyCur), CoinMarketCap historische
Momentaufnahmen (oeffentliche Seite, eingebettete Rangliste), DefiLlama stablecoincharts/all, FRED fredgraph.csv M2SL. Zwischenablage in
data/_spot/o47_cm.db (Forschungsdaten, nie Produktion). Nur lesend gegen alles andere.

V1 Katalog: wie viele Assets haben ab wann einen Tageskurs (vor 2017-01, 2017-10, 2019-01)
V2 Grundgesamtheit: CMC-Top-50 (ohne BTC/Stablecoins) an fuenf Stichtagen 2017-2019 - wie viele davon hat CoinMetrics (Zahl, Marktwert)?
V3 Stablecoins: Summe SplyCur CoinMetrics gegen DefiLlama peggedUSD auf 2019-04..2026 - Hoehe, und B3 (91 T > 10 %) an wie vielen Tagen gleich
V4 Korb-Tauglichkeit: Zahl der CoinMetrics-Alts mit Kurs und Marktwert je Monat 2016-10..2019-03 (reicht es fuer Top 50?)
V5 B1 / B2: BTC-Kurs und M2SL lueckenlos ueber den Holdout-Zeitraum
"""
import io
import json
import os
import re
import sqlite3
import sys
import time

import pandas as pd
import requests

os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass
CM = "https://community-api.coinmetrics.io/v4"
ABL = os.path.join("data", "_spot", "o47_cm.db")
STABLE_CM = ("usdt", "usdc", "pax", "tusd", "gusd", "busd", "dai", "husd", "usdk", "sai")   # 'usdt' ist die Summe ueber die Ketten
STAPEL = ("2017-01-01", "2017-10-01", "2018-01-07", "2018-06-03", "2019-01-06")
HOLD_A, HOLD_E = "2016-10-01", "2019-03-31"      # Vorlauf (91 T + M2-Verzug) bis vor die Kalibrierung (ab 2019-04)
H = {"User-Agent": "Mozilla/5.0 (TradingInfoTool Forschung)"}


def ablage():
    c = sqlite3.connect(ABL)
    c.execute("CREATE TABLE IF NOT EXISTS tag (asset TEXT, tag TEXT, PriceUSD REAL, CapMrktCurUSD REAL, SplyCur REAL, PRIMARY KEY (asset, tag))")
    c.execute("CREATE TABLE IF NOT EXISTS cmc (stichtag TEXT, rang INTEGER, symbol TEXT, name TEXT, slug TEXT, cap REAL, PRIMARY KEY (stichtag, rang))")
    c.execute("CREATE TABLE IF NOT EXISTS _herkunft (schluessel TEXT PRIMARY KEY, wert TEXT)")
    return c


def katalog():
    j = requests.get(CM + "/catalog-v2/asset-metrics", params={"metrics": "PriceUSD,CapMrktCurUSD,SplyCur", "page_size": 10000}, timeout=120).json()
    aus = {}
    for a in j["data"]:
        for m in a["metrics"]:
            for f in m["frequencies"]:
                if f["frequency"] == "1d" and f.get("community"):
                    aus.setdefault(a["asset"], {})[m["metric"]] = f["min_time"][:10]
    return aus


def hole(c, assets, metrics, start, ende):
    """CoinMetrics Tageswerte in die Ablage (seitenweise, je 20 Assets)."""
    for i in range(0, len(assets), 20):
        teil = assets[i:i + 20]
        url, p = CM + "/timeseries/asset-metrics", {"assets": ",".join(teil), "metrics": metrics, "frequency": "1d",
                                                   "start_time": start, "end_time": ende, "page_size": 10000}
        while url:
            for v in range(4):
                try:
                    r = requests.get(url, params=p, timeout=120)
                    if r.status_code == 429:
                        time.sleep(10 * (v + 1)); continue
                    r.raise_for_status()
                    break
                except requests.RequestException:
                    if v == 3:
                        raise
                    time.sleep(5)
            j = r.json()
            rows = [(x["asset"], x["time"][:10], float(x["PriceUSD"]) if x.get("PriceUSD") else None,
                     float(x["CapMrktCurUSD"]) if x.get("CapMrktCurUSD") else None, float(x["SplyCur"]) if x.get("SplyCur") else None)
                    for x in j.get("data", [])]
            c.executemany("INSERT INTO tag VALUES (?,?,?,?,?) ON CONFLICT(asset, tag) DO UPDATE SET PriceUSD=COALESCE(excluded.PriceUSD, PriceUSD), "
                          "CapMrktCurUSD=COALESCE(excluded.CapMrktCurUSD, CapMrktCurUSD), SplyCur=COALESCE(excluded.SplyCur, SplyCur)", rows)
            c.commit()
            url, p = j.get("next_page_url"), None
            time.sleep(0.7)


def cmc(c, stichtag):
    if c.execute("SELECT COUNT(*) FROM cmc WHERE stichtag=?", (stichtag,)).fetchone()[0]:
        return
    t = requests.get("https://coinmarketcap.com/historical/%s/" % stichtag.replace("-", ""), headers=H, timeout=90).text
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', t, re.S)
    ini = json.loads(json.loads(m.group(1))["props"]["initialState"]) if "initialState" in json.loads(m.group(1))["props"] else None
    if ini is None:
        ini = json.loads(json.loads(m.group(1))["props"]["pageProps"]["initialState"])
    liste = ini["cryptocurrency"]["listingHistorical"]["data"]
    rows = []
    for x in liste:
        q = x.get("quote", {}).get("USD", {}) or (x.get("quotes") or [{}])[0]
        rows.append((stichtag, int(x["cmcRank"]), x["symbol"], x["name"], x["slug"], float(q.get("marketCap") or q.get("market_cap") or 0)))
    c.executemany("INSERT OR REPLACE INTO cmc VALUES (?,?,?,?,?,?)", rows)
    c.commit()
    time.sleep(2)


def main():
    c = ablage()
    print("O47 VORANALYSE Season-Ampel Holdout 2017/18 · nur Datenlage (Ampel und Wahrheit auf dem Holdout NICHT gerechnet)\n")
    kat = katalog()
    preis = {a: v["PriceUSD"] for a, v in kat.items() if "PriceUSD" in v}
    print("V1 KATALOG CoinMetrics Community (1d): %d Assets mit PriceUSD · vor 2017-01: %d · vor 2017-10: %d · vor 2019-01: %d" % (
        len(preis), sum(t < "2017-01-01" for t in preis.values()), sum(t < "2017-10-01" for t in preis.values()), sum(t < "2019-01-01" for t in preis.values())))
    mit_cap = {a for a, v in kat.items() if "CapMrktCurUSD" in v and v["CapMrktCurUSD"] < "2017-10-01"}
    print("   davon mit Marktwert (CapMrktCurUSD) vor 2017-10: %d\n" % len(mit_cap))

    print("V2 GRUNDGESAMTHEIT: CMC-Top-50 ohne BTC und Stablecoins - wie viel davon hat CoinMetrics (Kurs bis zum Stichtag)?")
    stabil_sym = {"USDT", "USDC", "TUSD", "PAX", "GUSD", "DAI", "BUSD", "HUSD", "USDK", "SAI", "BITUSD", "NUSD"}
    v2 = {}
    for st in STAPEL:
        cmc(c, st)
        L = pd.read_sql("SELECT * FROM cmc WHERE stichtag=? ORDER BY rang", c, params=(st,))
        L = L[(L.symbol != "BTC") & (~L.symbol.isin(stabil_sym))].head(50)
        da = L.symbol.str.lower().map(lambda s: s in preis and preis[s] <= st) | L.slug.map(lambda s: False)
        # Kuerzel mit Ketten-Endung (eos_eth, qtum_eth ...) zaehlen, wenn das blanke fehlt
        da = da | L.symbol.str.lower().map(lambda s: any(k.startswith(s + "_") and preis[k] <= st for k in preis))
        fehlt = L[~da]
        v2[st] = (int(da.sum()), float(L.cap[da].sum() / L.cap.sum()) if L.cap.sum() else float("nan"), list(fehlt.symbol)[:25])
        print("   %s: %2d von 50 · Marktwert-Anteil %.0f %% · fehlen u. a.: %s" % (st, v2[st][0], 100 * v2[st][1], ", ".join(v2[st][2])))
    c.execute("INSERT OR REPLACE INTO _herkunft VALUES ('cmc', 'coinmarketcap.com/historical/<JJJJMMTT>/ eingebettete Rangliste, geladen %s')"
              % time.strftime("%Y-%m-%d %H:%M"))

    print("\nV3 STABLECOINS: CoinMetrics SplyCur (Summe %s) gegen DefiLlama peggedUSD" % "/".join(STABLE_CM))
    st_assets = [a for a in STABLE_CM if a in kat and "SplyCur" in kat[a]]
    hole(c, st_assets, "SplyCur", "2014-10-01", "2026-10-17")
    S = pd.read_sql("SELECT asset, tag, SplyCur FROM tag WHERE asset IN (%s)" % ",".join("?" * len(st_assets)), c, params=st_assets, parse_dates=["tag"])
    cm_sum = S.pivot(index="tag", columns="asset", values="SplyCur").sort_index().asfreq("D").ffill().fillna(0).sum(axis=1)
    j = requests.get("https://stablecoins.llama.fi/stablecoincharts/all", timeout=120).json()
    dl = pd.Series({pd.Timestamp(int(x["date"]), unit="s").normalize() + pd.Timedelta(days=1): x["totalCirculatingUSD"].get("peggedUSD", 0) for x in j}).sort_index()
    gem = pd.concat([cm_sum.rename("cm"), dl.rename("dl")], axis=1).dropna()
    gem = gem[(gem.index >= "2019-04-01")]
    b3c, b3d = gem.cm / gem.cm.shift(91) - 1, gem.dl / gem.dl.shift(91) - 1
    ok = b3c.notna() & b3d.notna()
    gleich = ((b3c[ok] > 0.10) == (b3d[ok] > 0.10))
    print("   Erster Wert CoinMetrics-Summe: %s (%.0f Mio USD) · im Holdout-Beginn 2016-10: %.0f Mio · 2017-12: %.0f Mio · 2018-12: %.0f Mio" % (
        cm_sum[cm_sum > 0].index[0].date(), cm_sum[cm_sum > 0].iloc[0] / 1e6, cm_sum.get(pd.Timestamp("2016-10-01"), 0) / 1e6,
        cm_sum.get(pd.Timestamp("2017-12-01"), 0) / 1e6, cm_sum.get(pd.Timestamp("2018-12-01"), 0) / 1e6))
    print("   2019-04..heute: Verhaeltnis CM/DL Median %.3f (5 %%: %.3f, 95 %%: %.3f) · B3 (91 T > 10 %%) gleich an %d von %d Tagen (%.1f %%) · "
          "91-T-Rate Abweichung Median %.2f Pp, 95 %% %.2f Pp" % (
              (gem.cm / gem.dl).median(), (gem.cm / gem.dl).quantile(0.05), (gem.cm / gem.dl).quantile(0.95), int(gleich.sum()), int(ok.sum()),
              100 * gleich.mean(), 100 * (b3c[ok] - b3d[ok]).abs().median(), 100 * (b3c[ok] - b3d[ok]).abs().quantile(0.95)))
    print("   Anteil USDT an der CM-Summe: 2017-12 %.0f %% · 2018-12 %.0f %%" % (
        100 * S[(S.asset == "usdt") & (S.tag == "2017-12-01")].SplyCur.sum() / max(cm_sum.get(pd.Timestamp("2017-12-01"), 1), 1),
        100 * S[(S.asset == "usdt") & (S.tag == "2018-12-01")].SplyCur.sum() / max(cm_sum.get(pd.Timestamp("2018-12-01"), 1), 1)))

    print("\nV4 KORB-TAUGLICHKEIT 2016-10..2019-03 (CoinMetrics-Alts ohne BTC und Stablecoins, mit Kurs UND Marktwert am Monatsersten)")
    alts = sorted(a for a, t in preis.items() if t < "2019-04-01" and a != "btc" and a not in STABLE_CM and not a.startswith("usdt")
                  and "CapMrktCurUSD" in kat.get(a, {}))
    hole(c, alts + ["btc"], "PriceUSD,CapMrktCurUSD", HOLD_A, "2019-07-01")
    P = pd.read_sql("SELECT asset, tag, PriceUSD, CapMrktCurUSD FROM tag WHERE tag>=? AND tag<=? AND asset NOT IN (%s)" % ",".join("?" * len(STABLE_CM)),
                    c, params=(HOLD_A, "2019-07-01") + STABLE_CM, parse_dates=["tag"])
    P = P[(P.asset != "btc") & P.PriceUSD.notna() & P.CapMrktCurUSD.notna()]
    z = P[P.tag.dt.day == 1].groupby("tag").asset.nunique()
    print("   " + " · ".join("%s %d" % (t.strftime("%Y-%m"), n) for t, n in z.items() if t.month in (1, 4, 7, 10)))
    print("   Monate mit < 50 Alts: %d von %d (erster Monat mit >= 50: %s)" % (int((z < 50).sum()), len(z), z[z >= 50].index.min().strftime("%Y-%m") if (z >= 50).any() else "keiner"))
    print("   ⚠️ Kein Boersenumsatz in der Community-Schnittstelle -> Korb nach MARKTWERT (Bruecke V-B noetig, s. Messplan)")

    print("\nV5 B1 / B2 ueber den Holdout")
    b = pd.read_sql("SELECT tag, PriceUSD FROM tag WHERE asset='btc' AND tag>=? AND tag<=?", c, params=(HOLD_A, HOLD_E), parse_dates=["tag"]).set_index("tag").PriceUSD
    print("   BTC PriceUSD: %d Tage, Luecken %d" % (len(b), int(pd.date_range(HOLD_A, HOLD_E).difference(b.index).size)))
    m2 = pd.read_csv(io.StringIO(requests.get("https://fred.stlouisfed.org/graph/fredgraph.csv?id=M2SL", headers=H, timeout=90).text))
    m2.columns = ["datum", "m2"]
    m2 = m2[(m2.datum >= "2015-06-01") & (m2.datum <= HOLD_E)]
    print("   M2SL (FRED, monatlich): %d Monate %s..%s, fehlend %d" % (len(m2), m2.datum.min(), m2.datum.max(), int(pd.to_numeric(m2.m2, errors="coerce").isna().sum())))
    c.execute("INSERT OR REPLACE INTO _herkunft VALUES ('coinmetrics', 'CoinMetrics Community API v4 (CC BY-NC 4.0), geladen %s')" % time.strftime("%Y-%m-%d %H:%M"))
    c.commit()
    c.close()


if __name__ == "__main__":
    main()
