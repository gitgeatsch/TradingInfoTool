"""Pruefung der UNGEMESSENEN Indikatoren (Spot §45, 11.10.2026) - Quellenprobe: frei? Historie? Abdeckung unseres Universums? Nur lesende
oeffentliche Abrufe ohne Schluessel, gespeichert wird NICHTS ausser dieser Ausgabe.

    python Basisinfos/Spot_Voranalyse_04_10/kp_quellenprobe.py

Universum = Watchlist-Universum am letzten Stichtag der Messung (data/_spot/b4_vormessung.csv), CoinGecko-ID aus strukturprofil.db.
  Q1 Wikipedia-Seitenaufrufe (Wikimedia REST, frei ab 07/2015): Artikel ueber den CoinGecko-Namen auffindbar? Stichprobe 60
  Q2 Stablecoin-Bestand JE KETTE (DefiLlama stablecoins, frei): Ketten mit gecko_id im Universum, Historie
  Q3 DEX-Umsatz je Kette / Protokoll (DefiLlama overview/dexs, frei): Zuordnung ueber gecko_id, Historie
  Q4 CoinMetrics Community je Asset: welche Altcoins haben AdrActCnt / TxCnt / FeeTotNtv / CapMVRVCur frei
  Q5 GitHub-Aktivitaet: CoinGecko /coins/{id} -> repos_url, Stichprobe 12; GitHub-API ohne Schluessel (60/h) erreichbar?
  Q6 Free Crypto News (K5 aus P2, nie gepruefte Datenprobe): erreichbar? Archiv?
  Q7 Binance-Archiv futures/um metrics (Top-Trader Long/Short, Taker-Verhaeltnis, OI taeglich): Datei fuer einen Altcoin 2023 vorhanden?
"""
import os
import random
import sqlite3
import time

import pandas as pd
import requests

os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
UA = {"User-Agent": "TradingInfoTool-Forschung/1.0 (privat; gernot)"}
random.seed(45)


def hole(url, **kw):
    try:
        r = requests.get(url, headers=UA, timeout=40, **kw)
        return r.status_code, (r.json() if "json" in r.headers.get("content-type", "") else r.text)
    except Exception as e:  # noqa: BLE001
        return None, str(e)[:120]


B = pd.read_csv("data/_spot/b4_vormessung.csv", sep=";", parse_dates=["t"])
uni = sorted(B[B.t == B.t.max()].sym.unique())
pr = pd.read_sql("SELECT symbol, cg_id FROM profil", sqlite3.connect("file:data/_spot/strukturprofil.db?mode=ro", uri=True)).set_index("symbol").cg_id
ids = {s: pr.get(s) for s in uni if isinstance(pr.get(s), str)}
print("QUELLENPROBE ungemessene Indikatoren · Universum %d Coins (Stichtag %s), mit CoinGecko-ID %d\n" % (len(uni), B.t.max().date(), len(ids)))

# Q1
st, cgl = hole("https://api.coingecko.com/api/v3/coins/list")
namen = {x["id"]: x["name"] for x in cgl} if st == 200 else {}
probe = random.sample(sorted(ids), 60)
treffer, alt = 0, []
for s in probe:
    n = namen.get(ids[s])
    if not n:
        continue
    for titel in (n, n + " (cryptocurrency)", n + " (blockchain)"):
        st, j = hole("https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/user/%s/monthly/2023010100/2023013100"
                     % requests.utils.quote(titel.replace(" ", "_"), safe=""))
        if st == 200:
            treffer += 1
            alt.append(s)
            break
    time.sleep(0.2)
print("Q1 Wikipedia: CoinGecko-Namensliste %s · Artikel mit Aufrufen 01/2023 fuer %d von 60 (%.0f %%) · z. B. %s" % (
    "ok" if namen else "NICHT erreichbar (%s)" % st, treffer, 100 * treffer / 60, ", ".join(alt[:12])))
print("   ⚠️ Treffer ueber den Namen koennen falsch sein (Begriff statt Coin) - Zuordnung waere von Hand zu pruefen\n")

# Q2
st, ch = hole("https://stablecoins.llama.fi/stablecoinchains")
if st == 200:
    # KORREKTUR nach dem ersten Lauf: stablecoinchains traegt KEINE gecko_id - die Zuordnung Kette -> Token steht in /v2/chains
    _, v2 = hole("https://api.llama.fi/v2/chains")
    stc = {c["name"] for c in ch}
    gid = {c.get("gecko_id"): c["name"] for c in (v2 or []) if c.get("gecko_id") and c["name"] in stc}
    im = {s: gid[i] for s, i in ids.items() if i in gid}
    print("Q2 Stablecoins je Kette: %d Ketten mit gecko_id · davon im Universum %d: %s" % (len(gid), len(im), ", ".join(sorted(im)[:40])))
    if im:
        s0 = sorted(im)[0]
        st2, h = hole("https://stablecoins.llama.fi/stablecoincharts/%s" % requests.utils.quote(im[s0]))
        if st2 == 200 and h:
            print("   Historie Beispiel %s (%s): %d Tage ab %s" % (s0, im[s0], len(h), pd.to_datetime(int(h[0]["date"]), unit="s").date()))
else:
    print("Q2 Stablecoins je Kette: NICHT erreichbar (%s)" % st)
print()

# Q3
st, dx = hole("https://api.llama.fi/overview/dexs?excludeTotalDataChart=true&excludeTotalDataChartBreakdown=true")
if st == 200:
    prot = dx.get("protocols", [])
    # KORREKTUR nach dem ersten Lauf: overview/dexs traegt KEINE gecko_id - Zuordnung Protokoll -> Token ueber /protocols (gecko_id, slug)
    _, pl = hole("https://api.llama.fi/protocols")
    mit_dex = {p.get("slug") for p in prot} | {p.get("name") for p in prot}
    gp = {q.get("gecko_id"): q.get("slug") for q in (pl or []) if q.get("gecko_id") and (q.get("slug") in mit_dex or q.get("name") in mit_dex)}
    imp = sorted(s for s, i in ids.items() if i in gp)
    print("Q3 DEX-Umsatz: %d Protokolle mit gecko_id · Token im Universum %d: %s" % (len(gp), len(imp), ", ".join(imp[:30])))
    if imp:
        st2, h = hole("https://api.llama.fi/summary/dexs/%s?dataType=dailyVolume" % gp[ids[imp[0]]])
        if st2 == 200 and isinstance(h, dict) and h.get("totalDataChart"):
            print("   Historie Beispiel %s: %d Tage ab %s" % (imp[0], len(h["totalDataChart"]), pd.to_datetime(h["totalDataChart"][0][0], unit="s").date()))
else:
    print("Q3 DEX-Umsatz: NICHT erreichbar (%s)" % st)
print()

# Q4
st, cat = hole("https://community-api.coinmetrics.io/v4/catalog-v2/asset-metrics?pretty=false&page_size=10000")
if st == 200:
    zeilen = cat.get("data", [])
    hat = {}
    for z in zeilen:
        a = z.get("asset", "").upper()
        mets = {m["metric"] for m in z.get("metrics", [])}
        hat[a] = mets
    for m in ("AdrActCnt", "TxCnt", "FeeTotNtv", "CapMVRVCur", "NVTAdj"):
        s_ = sorted(s for s in uni if m in hat.get(s, set()))
        print("Q4 CoinMetrics %-10s frei fuer %3d Universum-Coins: %s" % (m, len(s_), ", ".join(s_[:25])))
else:
    print("Q4 CoinMetrics-Katalog: NICHT erreichbar (%s %s)" % (st, str(cat)[:100]))
print()

# Q5
gh_ok = 0
for s in random.sample(sorted(ids), 12):
    st, j = hole("https://api.coingecko.com/api/v3/coins/%s?localization=false&tickers=false&market_data=false&community_data=false&developer_data=true" % ids[s])
    if st == 200:
        rep = (j.get("links", {}).get("repos_url", {}) or {}).get("github", [])
        gh_ok += bool(rep)
    time.sleep(2.5)
st, j = hole("https://api.github.com/rate_limit")
print("Q5 GitHub: Repo-Verweis bei CoinGecko fuer %d von 12 · GitHub-API ohne Schluessel %s (Grenze %s/h)\n" % (
    gh_ok, "erreichbar" if st == 200 else "NICHT erreichbar (%s)" % st, j.get("rate", {}).get("limit") if isinstance(j, dict) else "?"))

# Q6
for u in ("https://cryptocurrency.cv/api/news?limit=1", "https://cryptocurrency.cv/"):
    st, j = hole(u)
    print("Q6 Free Crypto News %s -> %s %s" % (u, st, str(j)[:120].replace("\n", " ")))
print()

# Q7
for sym in ("LINKUSDT", "INJUSDT"):
    st, _ = hole("https://data.binance.vision/data/futures/um/daily/metrics/%s/%s-metrics-2023-06-01.zip" % (sym, sym))
    print("Q7 Binance-Archiv metrics %s 2023-06-01 -> %s" % (sym, st))
