# -*- coding: utf-8 -*-
"""Liefert DefiLlama die TVL-HISTORIE mit - oder nur den Tagesstand?

Das entscheidet, ob TVL erst ab 18.09.2026 messbar ist (so steht es im
Memory) oder SOFORT. Das System sammelt heute taeglich selbst ueber
/protocols - das ist eine Momentaufnahme.
"""
import json, sys, urllib.request
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

def hole(url, timeout=30):
    r = urllib.request.Request(url, headers={"User-Agent": "TradingInfoTool/1.0"})
    with urllib.request.urlopen(r, timeout=timeout) as a:
        return json.loads(a.read().decode("utf-8"))

print("Ein einzelner Testabruf auf die oeffentliche DefiLlama-API (kein Key,")
print("kein Kontingent, keine Daten werden gesendet).")
print()
for name in ("uniswap", "aave"):
    try:
        d = hole("https://api.llama.fi/protocol/%s" % name)
        reihe = d.get("tvl") or []
        print("%-10s Historie: %d Tagespunkte" % (name, len(reihe)))
        if reihe:
            import datetime as dt
            a = dt.datetime.utcfromtimestamp(reihe[0]["date"]).date()
            b = dt.datetime.utcfromtimestamp(reihe[-1]["date"]).date()
            print("%-10s Zeitraum: %s .. %s  (%.1f Jahre)"
                  % ("", a, b, (b - a).days / 365.25))
            print("%-10s Beispiel: %s -> %.0f USD" % ("", a, reihe[0]["totalLiquidityUSD"]))
    except Exception as e:
        print("%-10s FEHLER: %s" % (name, e))
    print()
