# -*- coding: utf-8 -*-
"""Zweiter Anlauf: der richtige Community-Endpunkt, und Historie bei Gebuehren."""
import json, sys, time, urllib.request
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
KOPF = {"User-Agent": "TradingInfoTool/1.0 (Analyse, nicht kommerziell)"}
def hole(url, timeout=45):
    r = urllib.request.Request(url, headers=KOPF)
    with urllib.request.urlopen(r, timeout=timeout) as a:
        return json.loads(a.read().decode("utf-8"))

print("### A. Coin Metrics — Community-Endpunkte durchprobieren ###")
kandidaten = [
 ("community-api v4 timeseries",
  "https://community-api.coinmetrics.io/v4/timeseries/asset-metrics"
  "?assets=btc&metrics=AdrActCnt&start_time=2024-01-01&page_size=3"),
 ("api v4 timeseries direkt",
  "https://api.coinmetrics.io/v4/timeseries/asset-metrics"
  "?assets=btc&metrics=AdrActCnt&start_time=2024-01-01&page_size=3"),
 ("catalog (v1-Stil)",
  "https://community-api.coinmetrics.io/v4/catalog/assets?assets=btc"),
]
for name, url in kandidaten:
    try:
        d = hole(url)
        n = len(d.get("data") or [])
        print("  %-28s OK — %d Eintraege" % (name, n))
        if n:
            print("  %-28s Beispiel: %s" % ("", json.dumps(d["data"][0])[:130]))
        break
    except Exception as e:
        print("  %-28s %s" % (name, str(e)[:60]))
    time.sleep(1.5)

print()
print("### B. Wie weit reicht die Historie, und fuer wieviele Assets? ###")
try:
    d = hole("https://community-api.coinmetrics.io/v4/timeseries/asset-metrics"
             "?assets=btc&metrics=AdrActCnt&start_time=2010-01-01&page_size=1")
    print("  BTC aktive Adressen, aeltester Punkt: %s"
          % json.dumps((d.get("data") or [{}])[0])[:110])
except Exception as e:
    print("  %s" % str(e)[:80])
time.sleep(1.5)
try:
    d = hole("https://community-api.coinmetrics.io/v4/catalog/asset-metrics?metrics=AdrActCnt")
    a = (d.get("data") or [{}])[0]
    fr = (a.get("frequencies") or [{}])[0]
    print("  Assets mit dieser Metrik: %d" % len(fr.get("assets") or []))
    print("  Beispiele: %s" % ", ".join((fr.get("assets") or [])[:25]).upper())
except Exception as e:
    print("  Katalog: %s" % str(e)[:80])

print()
print("### C. DefiLlama Gebuehren — gibt es Historie je Protokoll? ###")
time.sleep(1.5)
try:
    d = hole("https://api.llama.fi/summary/fees/uniswap?dataType=dailyFees")
    r = d.get("totalDataChart") or []
    print("  uniswap Gebuehren: %d Tagespunkte" % len(r))
    if r:
        import datetime as dt
        a = dt.datetime.fromtimestamp(r[0][0], dt.timezone.utc).date()
        b = dt.datetime.fromtimestamp(r[-1][0], dt.timezone.utc).date()
        print("  Zeitraum: %s .. %s  (%.1f Jahre)" % (a, b, (b-a).days/365.25))
except Exception as e:
    print("  %s" % str(e)[:80])
