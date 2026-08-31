# -*- coding: utf-8 -*-
"""Liefert Binance die FUNDING-Historie rueckwirkend?

Im Memory steht: Positionierung (Funding, OI) "Wirkung erst ab 22.10.2026
messbar", weil das System seit 14.07. selbst sammelt (227 Zeilen). Bei TVL
war genau diese Annahme falsch - die Quelle liefert die Vergangenheit mit.
"""
import json, sys, time, urllib.request, datetime as dt
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
KOPF = {"User-Agent": "TradingInfoTool/1.0 (Analyse, nicht kommerziell)"}
def hole(url, timeout=45):
    r = urllib.request.Request(url, headers=KOPF)
    with urllib.request.urlopen(r, timeout=timeout) as a:
        return json.loads(a.read().decode("utf-8"))

print("### A. Funding-Rate-Historie (Binance Futures, oeffentlich) ###")
try:
    d = hole("https://fapi.binance.com/fapi/v1/fundingRate?symbol=BTCUSDT&limit=1000")
    print("  BTCUSDT: %d Eintraege in EINEM Abruf (max 1000)" % len(d))
    if d:
        a = dt.datetime.fromtimestamp(d[0]["fundingTime"]/1000, dt.timezone.utc)
        b = dt.datetime.fromtimestamp(d[-1]["fundingTime"]/1000, dt.timezone.utc)
        print("  Zeitraum dieses Abrufs: %s .. %s" % (a.date(), b.date()))
        print("  Beispiel: %s -> %s" % (a.date(), d[0]["fundingRate"]))
except Exception as e:
    print("  FEHLER: %s" % str(e)[:100])
time.sleep(1.5)
print()
print("  Wie weit zurueck? Abruf ab 2019-09-01:")
try:
    ab = int(dt.datetime(2019, 9, 1, tzinfo=dt.timezone.utc).timestamp()*1000)
    d = hole("https://fapi.binance.com/fapi/v1/fundingRate?symbol=BTCUSDT"
             "&startTime=%d&limit=1000" % ab)
    if d:
        a = dt.datetime.fromtimestamp(d[0]["fundingTime"]/1000, dt.timezone.utc)
        print("  aeltester Punkt: %s  -> %.1f Jahre Historie verfuegbar"
              % (a.date(), (dt.datetime.now(dt.timezone.utc)-a).days/365.25))
        print("  (8-Stunden-Takt -> rund 1.095 Punkte je Jahr je Symbol)")
except Exception as e:
    print("  FEHLER: %s" % str(e)[:100])
time.sleep(1.5)
print()
print("### B. Open Interest — auch rueckwirkend? ###")
try:
    d = hole("https://fapi.binance.com/futures/data/openInterestHist"
             "?symbol=BTCUSDT&period=1d&limit=500")
    print("  BTCUSDT: %d Tagespunkte" % len(d))
    if d:
        a = dt.datetime.fromtimestamp(d[0]["timestamp"]/1000, dt.timezone.utc)
        b = dt.datetime.fromtimestamp(d[-1]["timestamp"]/1000, dt.timezone.utc)
        print("  Zeitraum: %s .. %s  (%d Tage)" % (a.date(), b.date(), (b-a).days))
        print("  ⚠️ Binance begrenzt Open Interest auf die letzten 30 Tage.")
except Exception as e:
    print("  FEHLER: %s" % str(e)[:100])
