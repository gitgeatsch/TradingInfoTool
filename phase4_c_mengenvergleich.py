# -*- coding: utf-8 -*-
"""MISST COINGECKO DASSELBE WIE COIN METRICS? (20.09.2026)

⚠️⚠️ DIE ENTSCHEIDENDE FRAGE VOR JEDER ERGAENZUNG. `turnover` ist
`Binance-Stueckvolumen / Umlaufmenge`. Kaeme die Menge fuer einen Teil
der Symbole von Coin Metrics und fuer den anderen von CoinGecko, stuenden
ZWEI QUELLEN IM SELBEN NENNER - genau der Fehler, den Schritt 49 (2.410)
gerade behoben hat.

Pruefbar ist das direkt: fuer die Symbole MIT `splycur`-Reihe beide
Mengen nebeneinander stellen.

⚠️ Eigener schlanker Abruf, NICHT ueber `api/coingecko.py` (das bucht
ueber `api_health` in die Produktionsdatenbank).
"""
import json
import os
import sqlite3
import sys
import time
import urllib.error
import urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
os.chdir("D:/CLAUDE_Projects/SoftwareProjekte/TradingInfoTool")
HIER = os.path.dirname(os.path.abspath(__file__))
SICHERUNG = os.path.join(HIER, "prod_1432.db")


def hole(url: str, versuche: int = 3):
    for i in range(versuche):
        try:
            r = urllib.request.Request(
                url, headers={"User-Agent": "TradingInfoTool-Recherche"})
            with urllib.request.urlopen(r, timeout=25) as a:
                return a.status, json.loads(a.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 429 and i < versuche - 1:
                time.sleep(20 * (i + 1))
                continue
            return e.code, None
        except Exception as exc:                             # noqa: BLE001
            return str(exc)[:50], None
    return "?", None


o = sqlite3.connect("file:data/onchain_historie.db?mode=ro", uri=True)
# juengster Punkt je Symbol
cm = {}
for sym, datum, wert in o.execute(
        "SELECT symbol, datum, wert FROM splycur s WHERE datum = "
        "(SELECT MAX(datum) FROM splycur x WHERE x.symbol = s.symbol)"):
    if wert and float(wert) > 0:
        cm[sym.upper()] = (float(wert), str(datum)[:10])

p = sqlite3.connect("file:%s?mode=ro" % SICHERUNG.replace("\\", "/"), uri=True)
ids = {}
for sym, cg in p.execute(
        "SELECT DISTINCT symbol, coingecko_id FROM price_cache "
        " WHERE coingecko_id IS NOT NULL AND coingecko_id != ''"):
    ids.setdefault(sym.upper(), cg)

gemeinsam = sorted(s for s in cm if s in ids)
print("=" * 100)
print("VERGLEICH DER UMLAUFMENGEN - COIN METRICS gegen COINGECKO")
print("=" * 100)
print("  Symbole mit `splycur`-Reihe UND bekannter coingecko_id: %d"
      % len(gemeinsam))
print()

cg_werte = {}
for i in range(0, len(gemeinsam), 60):
    teil = gemeinsam[i:i + 60]
    url = ("https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd"
           "&ids=%s&per_page=250&page=1"
           % ",".join(ids[s] for s in teil))
    status, daten = hole(url)
    if not isinstance(daten, list):
        print("  Abruf %d: Status %s - abgebrochen" % (i // 60 + 1, status))
        break
    for e in daten:
        s = (e.get("symbol") or "").upper()
        if e.get("circulating_supply"):
            cg_werte[s] = float(e["circulating_supply"])
    time.sleep(3)

print("  %-8s %18s %12s %18s %10s" % ("Symbol", "Coin Metrics", "Stand",
                                      "CoinGecko", "Abweichung"))
gross = klein = 0
abw = []
for s in gemeinsam:
    if s not in cg_werte:
        continue
    a, tag = cm[s]
    b = cg_werte[s]
    d = 100.0 * (b - a) / a if a else float("nan")
    abw.append(abs(d))
    if abs(d) > 5.0:
        gross += 1
    else:
        klein += 1
    print("  %-8s %18.0f %12s %18.0f %+9.1f %%%s"
          % (s, a, tag, b, d, "  ⚠️" if abs(d) > 5 else ""))
print()
if abw:
    abw.sort()
    print("  ➤ %d Symbole verglichen · Abweichung Median %.1f %% · "
          "90. Perzentil %.1f %%"
          % (len(abw), abw[len(abw) // 2], abw[int(0.9 * len(abw))]))
    print("     unter 5 %%: %d · ueber 5 %%: %d" % (klein, gross))
    print()
    print("  ⚠️ Eine ABWEICHUNG IM NENNER geht 1:1 in `turnover` ein: 10 %% "
          "mehr Menge heisst")
    print("     10 %% weniger Umschlag - und der Rang verschiebt sich "
          "entsprechend.")
