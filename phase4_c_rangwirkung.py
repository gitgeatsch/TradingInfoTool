# -*- coding: utf-8 -*-
"""AENDERT DIE QUELLE DEN RANG? (20.09.2026)

Die Mengen weichen ab (Median 25 Prozent) - aber in die Bewertung geht
nicht die Menge ein, sondern das FUENFTEL des Umschlags. Die Frage ist
also: wie viele Symbole wechseln das Fuenftel, wenn der Nenner aus
CoinGecko statt aus Coin Metrics kommt?

⚠️ Genau die Frage, die `messe_grundgesamtheit.py` am 20.09. fuer die
Symbolmenge beantwortet hat (18 von 31 -> 0 von 29). Dasselbe Mass,
andere Ursache.

## ⚠️⚠️ Die Zuordnung ist die Gefahr

Ein Symbol ist KEINE eindeutige Kennung - in CoinGeckos Katalog tragen
viele Muenzen dasselbe Kuerzel. Eine falsche Zuordnung wuerde die
Messung still verfaelschen. Deshalb: nur Symbole, die im Katalog GENAU
EINE id haben; der Rest wird ausgewiesen, nicht geraten.

⚠️ Eigener Abruf, nicht ueber `api/coingecko.py`.
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
sys.path.insert(0, "D:/CLAUDE_Projects/SoftwareProjekte/TradingInfoTool")
import agent.marktrang as MR                                 # noqa: E402


def hole(url, versuche=3):
    for i in range(versuche):
        try:
            r = urllib.request.Request(
                url, headers={"User-Agent": "TradingInfoTool-Recherche"})
            with urllib.request.urlopen(r, timeout=40) as a:
                return a.status, json.loads(a.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 429 and i < versuche - 1:
                time.sleep(25 * (i + 1))
                continue
            return e.code, None
        except Exception as exc:                             # noqa: BLE001
            return str(exc)[:60], None
    return "?", None


# ---- 1  Coin-Metrics-Mengen, nur die FRISCHEN --------------------------
import datetime as dt
o = sqlite3.connect("file:data/onchain_historie.db?mode=ro", uri=True)
heute = dt.date.today()
cm = {}
for sym, datum, wert in o.execute(
        "SELECT symbol, datum, wert FROM splycur s WHERE datum = "
        "(SELECT MAX(datum) FROM splycur x WHERE x.symbol = s.symbol)"):
    try:
        alter = (heute - dt.date.fromisoformat(str(datum)[:10])).days
    except Exception:                                        # noqa: BLE001
        continue
    if alter <= MR.SPLYCUR_FRISCHE_TAGE and wert and float(wert) > 0:
        cm[sym.upper()] = float(wert)
print("=" * 100)
print("AENDERT DIE MENGENQUELLE DEN RANG?")
print("=" * 100)
print("  Coin Metrics, frisch (<= %d Tage): %d Symbole"
      % (MR.SPLYCUR_FRISCHE_TAGE, len(cm)))

# ---- 2  Katalog, und nur EINDEUTIGE Kuerzel ---------------------------
status, liste = hole("https://api.coingecko.com/api/v3/coins/list")
if not isinstance(liste, list):
    raise SystemExit("coins/list Status %s" % status)
je_symbol = {}
for e in liste:
    je_symbol.setdefault((e.get("symbol") or "").upper(), []).append(e["id"])
eindeutig = {s: v[0] for s, v in je_symbol.items() if len(v) == 1}
kandidaten = sorted(s for s in cm if s in eindeutig)
mehrdeutig = sorted(s for s in cm if s in je_symbol and len(je_symbol[s]) > 1)
print("  Katalog: %d Eintraege · davon Kuerzel EINDEUTIG: %d"
      % (len(liste), len(eindeutig)))
print("  ⚠️ von unseren %d sind %d eindeutig, %d MEHRDEUTIG (nicht "
      "verwendet): %s"
      % (len(cm), len(kandidaten), len(mehrdeutig),
         ", ".join(mehrdeutig[:18])))

# ---- 3  CoinGecko-Mengen dazu -----------------------------------------
cg = {}
for i in range(0, len(kandidaten), 60):
    teil = kandidaten[i:i + 60]
    st, d = hole("https://api.coingecko.com/api/v3/coins/markets"
                 "?vs_currency=usd&ids=%s&per_page=250&page=1"
                 % ",".join(eindeutig[s] for s in teil))
    if not isinstance(d, list):
        print("  Abruf %d: Status %s" % (i // 60 + 1, st))
        break
    for e in d:
        if e.get("circulating_supply"):
            cg[(e.get("symbol") or "").upper()] = float(e["circulating_supply"])
    time.sleep(4)
gemeinsam = sorted(s for s in kandidaten if s in cg)
print("  mit Menge aus BEIDEN Quellen: %d" % len(gemeinsam))

# ---- 4  Binance-Volumen, dieselbe Quelle wie im Betrieb ---------------
st, b24 = hole(MR.BINANCE_24H)
vol = {}
if isinstance(b24, list):
    for e in b24:
        pa = str(e.get("symbol") or "")
        if pa.endswith("USDT") and e.get("volume"):
            vol[pa[:-4]] = float(e["volume"])
print("  Binance 24h: Status %s, %d USDT-Paare" % (st, len(vol)))

menge_a = {s: cm[s] for s in gemeinsam if s in vol}
menge_b = {s: cg[s] for s in gemeinsam if s in vol}
print("  auswertbar (beide Mengen UND Binance-Volumen): %d" % len(menge_a))
print()


def fuenftel(mengen):
    w = {s: vol[s] / m for s, m in mengen.items() if m > 0}
    rang = sorted(w, key=lambda s: w[s])
    n = len(rang)
    return {s: min(4, i * 5 // n) for i, s in enumerate(rang)}, w


fa, wa = fuenftel(menge_a)
fb, wb = fuenftel(menge_b)
wechsel = [s for s in fa if fa[s] != fb[s]]
zwei = [s for s in fa if abs(fa[s] - fb[s]) >= 2]
rand = [s for s in fa if {fa[s], fb[s]} & {0, 4} and fa[s] != fb[s]]
print("  %-8s %10s %10s %8s %8s" % ("Symbol", "Umschlag CM", "Umschlag CG",
                                    "F. CM", "F. CG"))
for s in sorted(fa, key=lambda x: fa[x]):
    if fa[s] != fb[s]:
        print("  %-8s %10.5f %10.5f %8d %8d  ⚠️"
              % (s, wa[s], wb[s], fa[s], fb[s]))
print()
n = len(fa)
print("  ➤ FUENFTEL GEWECHSELT: %d von %d = %.1f %%"
      % (len(wechsel), n, 100.0 * len(wechsel) / n if n else 0))
print("     davon um ZWEI oder mehr Stufen: %d · mit Randfuenftel "
      "beteiligt: %d" % (len(zwei), len(rand)))
print()
print("  ⚠️ Vergleichsmass: `messe_grundgesamtheit.py` hat am 20.09. fuer "
      "die Symbolmenge")
print("     18 von 31 gemessen (schlecht) und nach dem Fix 0 von 29 (gut). "
      "Der Praezedenzfall")
print("     fuer die Frischegrenze liegt bei 93,5 % Uebereinstimmung, "
      "also 6,5 % Wechsel.")
