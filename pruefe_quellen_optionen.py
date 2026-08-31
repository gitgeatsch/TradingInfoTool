# -*- coding: utf-8 -*-
"""R-B Schritt 1b: welche weiteren Quellen liefern ASSET-Daten mit Historie?

Getestet wird an der Quelle, nicht aus der Doku. Alle Abrufe sind lesend,
oeffentlich, ohne Schluessel. Rate Limit Coin Metrics: 10 Anfragen / 6 s -
hier sind es drei, mit Pause.
"""
import json, sys, time, urllib.request
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
KOPF = {"User-Agent": "TradingInfoTool/1.0 (Analyse, nicht kommerziell)"}

def hole(url, timeout=45):
    r = urllib.request.Request(url, headers=KOPF)
    with urllib.request.urlopen(r, timeout=timeout) as a:
        return json.loads(a.read().decode("utf-8"))

print("=" * 84)
print("A. COIN METRICS COMMUNITY — welche Metriken, welche Historie?")
print("=" * 84)
try:
    d = hole("https://api.coinmetrics.io/v4/catalog-v2/asset-metrics?assets=btc&pretty=false")
    eintraege = d.get("data") or []
    metriken = []
    for e in eintraege:
        for m in (e.get("metrics") or []):
            f = (m.get("frequencies") or [{}])[0]
            metriken.append((m.get("metric"), f.get("min_time","")[:10], f.get("max_time","")[:10]))
    print("BTC: %d Metriken frei verfuegbar" % len(metriken))
    interessant = [m for m in metriken if any(w in m[0].lower() for w in
                   ("adractcnt", "txcnt", "feetot", "hashrate", "splycur",
                    "adrbal", "txtfrvaladj", "issuance", "nvt"))]
    print()
    print("  %-28s %-12s %s" % ("Metrik", "von", "bis"))
    for m, a, b in sorted(interessant)[:14]:
        print("  %-28s %-12s %s" % (m, a, b))
except Exception as e:
    print("  FEHLER: %s" % str(e)[:120])

time.sleep(2)
print()
print("=" * 84)
print("B. Fuer WELCHE Assets gibt es diese Daten?")
print("=" * 84)
try:
    d = hole("https://api.coinmetrics.io/v4/catalog-v2/asset-metrics?metrics=AdrActCnt&pretty=false")
    assets = sorted({e.get("asset") for e in (d.get("data") or []) if e.get("asset")})
    print("  Aktive Adressen verfuegbar fuer %d Assets" % len(assets))
    print("  Beispiele: %s" % ", ".join(a.upper() for a in assets[:30]))
except Exception as e:
    print("  FEHLER: %s" % str(e)[:120])

time.sleep(2)
print()
print("=" * 84)
print("C. DEFILLAMA — weitere Endpunkte neben TVL?")
print("=" * 84)
for name, url in (("Gebuehren/Umsatz je Protokoll",
                   "https://api.llama.fi/overview/fees?excludeTotalDataChart=true"),
                  ("Stablecoin-Umlauf", "https://stablecoins.llama.fi/stablecoins")):
    try:
        d = hole(url)
        if isinstance(d, dict):
            p = d.get("protocols") or d.get("peggedAssets") or []
            print("  %-32s %d Eintraege" % (name, len(p)))
            if p:
                bsp = p[0]
                print("  %-32s Felder: %s" % ("", ", ".join(list(bsp)[:8])))
    except Exception as e:
        print("  %-32s FEHLER: %s" % (name, str(e)[:60]))
    time.sleep(1.5)
