# -*- coding: utf-8 -*-
"""RECHERCHE: gibt es die AKTUELLE Umlaufmenge frei? (20.09.2026)

⚠️ Andere Frage als am 13.09. Damals gesucht: mehrjaehrige HISTORIE
(2.417, neun Anbieter, gescheitert). Der BETRIEB braucht aber nur den
letzten Punkt je Symbol - `marktrang.umlaufmengen()` nimmt ausdruecklich
*„nur den letzten Punkt je Symbol, und nur wenn er frisch genug ist"*.

⚠️⚠️ NICHT ueber `api/coingecko.py` - jeder Abruf dort bucht ueber
`api_health` in die Produktionsdatenbank. Hier ein eigener, schlanker
Abruf ohne Projektmodul.

⚠️ 401 gegen 429 trennen (Verbot gegen Drosselung), wie 2.417 es
verlangt - sonst sieht eine Drosselung wie eine Sperre aus.
"""
import io
import json
import os
import sqlite3
import sys
import time
import urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
os.chdir("D:/CLAUDE_Projects/SoftwareProjekte/TradingInfoTool")
HIER = os.path.dirname(os.path.abspath(__file__))
SICHERUNG = os.path.join(HIER, "prod_1432.db")


def hole(url: str, versuche: int = 3):
    """-> (status, json|None). 401/403 = Verbot, 429 = Drosselung."""
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


# ---- Welche Symbole fehlen, und welche coingecko_id haben sie? -------
o = sqlite3.connect("file:data/onchain_historie.db?mode=ro", uri=True)
turn = {r[0].upper() for r in o.execute("SELECT DISTINCT symbol FROM splycur")}
p = sqlite3.connect("file:%s?mode=ro" % SICHERUNG.replace("\\", "/"), uri=True)
ids = {}
for sym, cg in p.execute(
        "SELECT DISTINCT symbol, coingecko_id FROM price_cache "
        " WHERE coingecko_id IS NOT NULL AND coingecko_id != ''"):
    ids.setdefault(sym.upper(), cg)
bestand = []
for sym, q, s in p.execute(
        "SELECT symbol, COALESCE(quantity,0), COALESCE(staked_quantity,0) "
        "  FROM holdings"):
    S = sym.upper()
    if (q or 0) + (s or 0) > 0 and S in ids:
        bestand.append(S)
fehlend = sorted(set(bestand) - turn)
print("=" * 96)
print("RECHERCHE: AKTUELLE UMLAUFMENGE FUER DIE FEHLENDEN WERTE")
print("=" * 96)
print("  Im Bestand ohne `splycur`-Reihe: %d  %s"
      % (len(fehlend), ", ".join(fehlend)))
print()

# ---- CoinGecko /coins/markets: liefert `circulating_supply` ----------
gefragt = [ids[s] for s in fehlend if ids.get(s)]
url = ("https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd"
       "&ids=%s&per_page=250&page=1" % ",".join(gefragt))
print("  CoinGecko /coins/markets (frei, ohne Schluessel) fuer %d ids ..."
      % len(gefragt))
status, daten = hole(url)
print("  Status: %s" % status)
if isinstance(daten, list):
    print()
    print("  %-10s %-22s %18s %18s"
          % ("Symbol", "coingecko_id", "circulating_supply", "total_supply"))
    treffer = 0
    for e in daten:
        cs = e.get("circulating_supply")
        if cs:
            treffer += 1
        print("  %-10s %-22s %18s %18s"
              % ((e.get("symbol") or "").upper(), e.get("id"),
                 ("%.0f" % cs) if cs else "-",
                 ("%.0f" % e["total_supply"]) if e.get("total_supply")
                 else "-"))
    print()
    print("  ➤ %d von %d angefragten ids liefern eine Umlaufmenge."
          % (treffer, len(gefragt)))
else:
    print("  -> keine Liste zurueck")
