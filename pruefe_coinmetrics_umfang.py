# -*- coding: utf-8 -*-
"""Welche Coin-Metrics-Metriken sind frei, fuer wieviele UNSERER Symbole?"""
import json, sys, time, urllib.request
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import messe_eigenschaft_beitrag as B
KOPF = {"User-Agent": "TradingInfoTool/1.0 (Analyse, nicht kommerziell)"}
def hole(url, timeout=60):
    r = urllib.request.Request(url, headers=KOPF)
    with urllib.request.urlopen(r, timeout=timeout) as a:
        return json.loads(a.read().decode("utf-8"))

unsere = {s.upper() for s in B.lade().keys()}
print("### Freie Metriken bei Coin Metrics Community (Auswahl) ###")
d = hole("https://community-api.coinmetrics.io/v4/catalog/asset-metrics")
alle = d.get("data") or []
print("  insgesamt %d Metriken" % len(alle))
print()
WICHTIG = ("AdrActCnt", "TxCnt", "TxTfrValAdjUSD", "FeeTotUSD", "HashRate",
           "SplyCur", "AdrBalCnt", "IssTotUSD", "NVTAdj", "CapMrktCurUSD",
           "AdrBalUSD10Cnt", "BlkCnt", "VtyDayRet30d")
print("  %-18s %6s   %-12s %s" % ("Metrik", "Assets", "ab", "unsere davon"))
for m in alle:
    name = m.get("metric")
    if name not in WICHTIG:
        continue
    fr = (m.get("frequencies") or [{}])
    tag = next((f for f in fr if f.get("frequency") == "1d"), fr[0])
    assets = [a.upper() for a in (tag.get("assets") or [])]
    treffer = len(set(assets) & unsere)
    print("  %-18s %6d   %-12s %d" % (name, len(assets),
          str(tag.get("min_time", ""))[:10], treffer))
time.sleep(1)
print()
print("### Wie weit reicht eine Reihe wirklich? (ETH, aktive Adressen) ###")
d = hole("https://community-api.coinmetrics.io/v4/timeseries/asset-metrics"
         "?assets=eth&metrics=AdrActCnt&frequency=1d&start_time=2015-01-01"
         "&page_size=10000")
r = d.get("data") or []
print("  ETH: %d Tagespunkte, %s .. %s"
      % (len(r), r[0]["time"][:10] if r else "-", r[-1]["time"][:10] if r else "-"))
