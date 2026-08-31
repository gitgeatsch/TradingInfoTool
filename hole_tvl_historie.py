# -*- coding: utf-8 -*-
"""Holt die TVL-Historie von DefiLlama in eine EIGENE Messdatei (30.08.2026).

⚠️ SCHREIBT NICHT IN DIE PRODUKTIONS-DB. Ziel ist `data/tvl_historie.db` -
eine neue Datei, analog zu `messdaten.db`. Die Produktion wird nicht beruehrt.

## Warum ueberhaupt

`agent/lebendigkeit.py` ruft `/protocols` ab - eine Momentaufnahme - und baut
daraus Tag fuer Tag eine eigene Reihe (`MINDESTREIHE = {"tvl": 30}`). Deshalb
stand im Projekt "TVL auswertbar ab 18.09.2026". DefiLlama liefert unter
`/protocol/{slug}` aber die KOMPLETTE Historie mit: Uniswap 2.858 Tagespunkte
ueber 7,8 Jahre. Die Wartezeit ist unnoetig.

## Schonender Abruf

Nutzervorgabe: *"nicht zu schnell abfragen"*. Deshalb PAUSE Sekunden zwischen
den Anfragen, ein Wiederholungsversuch bei Fehler, und ein User-Agent, der
sagt, wer fragt. Bei rund 190 Protokollen sind das etwa 5 Minuten.

## Ein Symbol, mehrere Protokolle

Ein Kuerzel kann mehrere Eintraege haben (Aave V2, V3, Lending...). Gesammelt
wird das GROESSTE je Symbol - nicht die Summe, weil die Teilprotokolle
unterschiedlich weit zurueckreichen und eine Summe dann Spruenge bekaeme,
sobald ein Teil beginnt. Das waere derselbe Fehler wie die Token-Umstellungen
in `messdaten.db`.
"""
import datetime as dt
import json
import sqlite3
import sys
import time
import urllib.error
import urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_eigenschaft_beitrag as B

ZIEL = "data/tvl_historie.db"
PAUSE = 1.5          # Sekunden zwischen zwei Anfragen
KOPF = {"User-Agent": "TradingInfoTool/1.0 (Analyse, nicht kommerziell)"}


def hole(url, versuche=3):
    for n in range(versuche):
        try:
            r = urllib.request.Request(url, headers=KOPF)
            with urllib.request.urlopen(r, timeout=60) as a:
                return json.loads(a.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
            if n == versuche - 1:
                raise
            time.sleep(PAUSE * (n + 2))
    return None


def anlegen(conn):
    conn.execute("""CREATE TABLE IF NOT EXISTS tvl_historie (
        symbol TEXT NOT NULL, slug TEXT NOT NULL, datum TEXT NOT NULL,
        tvl_usd REAL NOT NULL, PRIMARY KEY (symbol, datum))""")
    conn.execute("""CREATE TABLE IF NOT EXISTS tvl_quelle (
        symbol TEXT PRIMARY KEY, slug TEXT, name TEXT, kategorie TEXT,
        tvl_jetzt REAL, punkte INTEGER, von TEXT, bis TEXT, geholt_am TEXT)""")
    conn.commit()


def main():
    unsere = set(B.lade().keys())
    print("Unsere Messreihen: %d" % len(unsere))
    prot = hole("https://api.llama.fi/protocols")
    print("DefiLlama-Protokolle: %d" % len(prot))

    # groesstes Protokoll je Symbol
    beste = {}
    for p in prot:
        s = str(p.get("symbol") or "").upper().strip()
        v = p.get("tvl")
        if s not in unsere or not v or not p.get("slug"):
            continue
        if s not in beste or float(v) > beste[s]["tvl"]:
            beste[s] = {"slug": p["slug"], "name": p.get("name"),
                        "kategorie": p.get("category"), "tvl": float(v)}
    print("Davon in unseren Reihen: %d Symbole" % len(beste))
    print("Abruf mit %.1f s Pause -> etwa %.0f Minuten"
          % (PAUSE, len(beste) * (PAUSE + 0.6) / 60))
    print()

    conn = sqlite3.connect(ZIEL)
    anlegen(conn)
    heute = dt.date.today().isoformat()
    ok = leer = fehler = 0
    for i, (sym, e) in enumerate(sorted(beste.items(), key=lambda x: -x[1]["tvl"]), 1):
        try:
            d = hole("https://api.llama.fi/protocol/%s" % e["slug"])
            reihe = d.get("tvl") or []
            punkte = []
            for x in reihe:
                v = x.get("totalLiquidityUSD")
                if v and v > 0:
                    tag = dt.datetime.fromtimestamp(
                        x["date"], dt.timezone.utc).date().isoformat()
                    punkte.append((sym, e["slug"], tag, float(v)))
            if punkte:
                conn.executemany(
                    "INSERT OR REPLACE INTO tvl_historie VALUES (?,?,?,?)", punkte)
                conn.execute(
                    "INSERT OR REPLACE INTO tvl_quelle VALUES (?,?,?,?,?,?,?,?,?)",
                    (sym, e["slug"], e["name"], e["kategorie"], e["tvl"],
                     len(punkte), punkte[0][2], punkte[-1][2], heute))
                conn.commit()
                ok += 1
            else:
                leer += 1
        except Exception as fehl:                      # noqa: BLE001
            fehler += 1
            print("  %-10s FEHLER: %s" % (sym, str(fehl)[:60]))
        if i % 25 == 0:
            print("  %3d von %d  (ok %d, leer %d, Fehler %d)"
                  % (i, len(beste), ok, leer, fehler))
        time.sleep(PAUSE)

    n = conn.execute("SELECT COUNT(*) FROM tvl_historie").fetchone()[0]
    s = conn.execute("SELECT COUNT(DISTINCT symbol) FROM tvl_historie").fetchone()[0]
    a, b = conn.execute("SELECT MIN(datum), MAX(datum) FROM tvl_historie").fetchone()
    print()
    print("FERTIG: %d Symbole, %d Tagespunkte, %s .. %s" % (s, n, a, b))
    print("Datei: %s   (die Produktions-DB wurde NICHT beruehrt)" % ZIEL)
    lang = conn.execute(
        "SELECT COUNT(*) FROM (SELECT symbol FROM tvl_historie "
        "GROUP BY symbol HAVING COUNT(*) >= 400)").fetchone()[0]
    print("Symbole mit mindestens 400 Tagespunkten: %d" % lang)
    conn.close()


if __name__ == "__main__":
    main()
