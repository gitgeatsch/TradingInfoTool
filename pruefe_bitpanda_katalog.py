"""Bitpanda-Katalog gegen Binance (O11, Voranalyse_Datenbasis_alle_Assets_01_10.md Abschnitt 10) - nur lesen, ausser mit --eintragen.

Fuer jedes Krypto-Asset des oeffentlichen Bitpanda-Tickers (ohne Edelmetalle und Stablecoins) wird der passende Binance-Kurs gesucht:

    gleich           dasselbe Kuerzel (Spot, sonst Futures), Abweichung <= 5 %          -> keine Zeile noetig
    Faktor-Ausnahme  erst mit Praefix 1000 / 1000000 / 1M, Abweichung <= 2 %            -> Zeile (mit --eintragen automatisch)
    Kollision        dasselbe Kuerzel bei Binance, Kurs > 5 % daneben, kein Praefix passt -> Zeile mit Markt 'gesperrt'
    ohne Binance     kein Kuerzel passt; genau EIN Binance-Coin mit Kurs +-1 % -> Kandidat (nur gemeldet, nie eingetragen)

Gegenprobe (muss bestehen): CAT -> 1000CAT als Faktor-Ausnahme, CC als 'gleich' ueber Futures.

    python pruefe_bitpanda_katalog.py              # nur pruefen
    python pruefe_bitpanda_katalog.py --eintragen  # Faktor-Ausnahmen und Kollisionen in Basisinfos/symbol_zuordnung.csv
"""
from __future__ import annotations

import csv
import os
import sqlite3
import sys

import requests

HIER = os.path.dirname(os.path.abspath(__file__))
ZUORDNUNG = os.path.join(HIER, "Basisinfos", "symbol_zuordnung.csv")
OHNE = {"XAU", "XAG", "XPT", "XPD", "USDC", "USDT", "EURCV", "EURC", "DAI", "TUSD", "USDP", "PYUSD", "FDUSD", "USDE", "USDS", "EURI", "AEUR",
        "BUSD", "USD1", "RLUSD", "PAXG", "XAUT"}
PRAEFIX = (("1000", 1000.0), ("1000000", 1e6), ("1M", 1e6))


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:                                         # noqa: BLE001
        pass
    bp = requests.get("https://api.bitpanda.com/v1/ticker", timeout=30).json()
    bpu = {s: float(v["USD"]) for s, v in bp.items() if s not in OHNE and v.get("USD") and float(v["USD"]) > 0}
    # ⚠️ nur Paare IM HANDEL: der Ticker liefert auch eingestellte Paare mit altem Kurs (gefunden 01.10.: MKR +2,6 Mio %, FTM, EOS, OCEAN)
    ih_s = {x["symbol"] for x in requests.get("https://api.binance.com/api/v3/exchangeInfo", timeout=30).json()["symbols"]
            if x["status"] == "TRADING" and x["quoteAsset"] == "USDT"}
    ih_f = {x["symbol"] for x in requests.get("https://fapi.binance.com/fapi/v1/exchangeInfo", timeout=30).json()["symbols"]
            if x["status"] == "TRADING" and x["quoteAsset"] == "USDT" and x.get("contractType") == "PERPETUAL"}
    sp = {x["symbol"][:-4]: float(x["price"]) for x in requests.get("https://api.binance.com/api/v3/ticker/price", timeout=30).json()
          if x["symbol"] in ih_s}
    fu = {x["symbol"][:-4]: float(x["price"]) for x in requests.get("https://fapi.binance.com/fapi/v1/ticker/price", timeout=30).json()
          if x["symbol"] in ih_f}
    da = set()
    for d in ("stundenkurse.db", "stundenkurse_alle.db"):
        p = os.path.join(HIER, "data", d)
        if os.path.exists(p):
            da |= {r[0] for r in sqlite3.connect("file:%s?mode=ro" % p.replace("\\", "/"), uri=True).execute("SELECT DISTINCT symbol FROM stundenkurse")}
    erg = {"gleich": [], "Faktor-Ausnahme": [], "Kollision": [], "ohne Binance": []}
    kand = []
    for s, p in sorted(bpu.items()):
        treffer = None
        for markt, tab in (("spot", sp), ("futures", fu)):
            if s in tab and abs(tab[s] / p - 1) <= 0.05:
                treffer = ("gleich", s, markt, 1.0, tab[s] / p - 1)
                break
        if treffer is None:
            for pre, f in PRAEFIX:
                for markt, tab in (("spot", sp), ("futures", fu)):
                    k = pre + s
                    if k in tab and abs(tab[k] / f / p - 1) <= 0.02:
                        treffer = ("Faktor-Ausnahme", k, markt, f, tab[k] / f / p - 1)
                        break
                if treffer:
                    break
        if treffer is None and (s in sp or s in fu):
            tab = sp if s in sp else fu
            treffer = ("Kollision", s, "gesperrt", 1.0, tab[s] / p - 1)
        if treffer is None:
            nah = [(b, m) for m, tab in (("spot", sp), ("futures", fu)) for b, x in tab.items() if abs(x / p - 1) <= 0.01]
            nah = sorted(set(b for b, _m in nah))
            if len(nah) == 1:
                kand.append((s, nah[0], p))
            erg["ohne Binance"].append((s, None, None, None, None))
            continue
        erg[treffer[0]].append((s,) + treffer[1:])
    print("=" * 110)
    print("BITPANDA-KATALOG GEGEN BINANCE · Bitpanda-Ticker %d (ohne Edelmetalle/Stablecoins %d) · Binance Spot %d, Futures %d" % (
        len(bp), len(bpu), len(sp), len(fu)))
    print("=" * 110)
    for k in ("gleich", "Faktor-Ausnahme", "Kollision", "ohne Binance"):
        v = erg[k]
        mit = sum(1 for x in v if x[1] in da)
        print("  %-16s %4d%s" % (k, len(v), ("   davon mit Stundenkursen bei uns %d%s" % (mit, (": " + ", ".join(x[0] for x in v if x[1] in da)) if k == "Kollision" else "")) if k != "ohne Binance" else ""))
    for k in ("Faktor-Ausnahme", "Kollision"):
        print("  %s:" % k.upper())
        for s, b, m, f, a in erg[k]:
            print("      %-10s -> %-12s %-8s Faktor %-7g Abweichung %+.2f %%" % (s, b, m, f, 100 * a))
    print("  KANDIDATEN fuer umbenannte Kuerzel (genau ein Binance-Coin mit Kurs +-1 %%): %d - ⚠️ UNBRAUCHBAR: Kursgleichheit allein paart fremde Coins (01.10.), nur Auskunft" % len(kand))
    for s, b, p in kand[:10]:
        print("      %-10s ?-> %-12s (Bitpanda %.6g USD)" % (s, b, p))
    g1 = any(x[0] == "CAT" and x[1] == "1000CAT" for x in erg["Faktor-Ausnahme"])
    g2 = any(x[0] == "CC" and x[2] == "futures" for x in erg["gleich"])
    print("  GEGENPROBE: CAT -> 1000CAT als Faktor-Ausnahme %s · CC gleich ueber Futures %s" % ("✔" if g1 else "⛔", "✔" if g2 else "⛔"))
    if "--eintragen" in sys.argv:
        with open(ZUORDNUNG, encoding="utf-8") as f_:
            alt = {r["bitpanda"]: r for r in csv.DictReader(f_, delimiter=";")}
        neu = 0
        for k in ("Faktor-Ausnahme", "Kollision"):
            for s, b, m, f, a in erg[k]:
                if s not in alt:
                    alt[s] = {"bitpanda": s, "binance": b, "markt": m, "faktor": "%g" % f,
                              "vermerk": "%s laut pruefe_bitpanda_katalog.py (Abweichung %+.2f %%) - 01.10.2026" % (k, 100 * a)}
                    neu += 1
        with open(ZUORDNUNG, "w", encoding="utf-8", newline="") as f_:
            w = csv.DictWriter(f_, fieldnames=["bitpanda", "binance", "markt", "faktor", "vermerk"], delimiter=";", lineterminator="\n")
            w.writeheader()
            for r in alt.values():
                w.writerow(r)
        print("  EINGETRAGEN: %d neue Zeilen in %s" % (neu, os.path.relpath(ZUORDNUNG, HIER)))
    print("SCHLUSS: vollstaendig")
    return 0 if (g1 and g2) else 1


if __name__ == "__main__":
    raise SystemExit(main())
