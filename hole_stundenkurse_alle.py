# -*- coding: utf-8 -*-
"""Stuendliche Kurse fuer ALLE Krypto-Assets, die Binance fuehrt - die Datenbasis fuer den Betrieb (O11).

Voranalyse: ``Basisinfos/Voranalyse_Datenbasis_alle_Assets_01_10.md`` (Nutzer 01.10.: *wir nehmen alles, was es gibt, vor allem, wenn
es im Bestand ist*; Frage 1 *alles halten statt nach Listen nachladen*; Frage 3 Futures-Kurse gleichwertig; Frage 4 *bewerten, nicht trainieren*).

WAS geladen wird (eine Regel, keine Liste):
    Spot      jedes USDT-Paar im Handel, ohne Stablecoins und Fiat (Liste ``OHNE`` unten)
    Futures   jedes USDT-Perpetual im Handel mit ``underlyingType = COIN``, dessen Basis es NICHT als Spot gibt (auch nicht ohne 1000-Praefix)
    ⭐ je Asset EINE Quelle: der Markt mit der LAENGEREN Historie (ab 2023). Beginnt der Futures-Kurs mehr als 30 Tage vor dem Spot
              (z. B. HYPE: Spot erst ab 24.09.2026, Futures ab 30.05.2025), wird Futures genommen - gleichwertig nach Frage 3. Kein Stueckeln.
              Die Entscheidung haengt nur an den Startdaten und ist damit ueber die Zeit stabil
    ab        2023-01-01 (Trainingsbeginn der REGEL0; fuer die Bewertung reichen 240 h, fuer die Signalbilanz 2024-26)
    ohne      die Symbole der MESSBASIS ``data/stundenkurse.db`` (116) - die liegen dort und bleiben unberuehrt

WOHIN: ``data/stundenkurse_alle.db`` - eine EIGENE Datei. ⚠️⚠️ Nie in ``stundenkurse.db``: ``messe_e2_beitraege.kursreihen`` nimmt dort JEDES
Symbol mit mehr als 2.000 Zeilen in den Bestand auf - jede Messung bekaeme still eine andere Grundgesamtheit (CLAUDE.md: keine Stellschraube).
Tabelle ``stundenkurse`` wie die Messbasis, dazu ``_quelle`` (symbol, markt, paar, geholt_am) und die Marke ``_nur_bewertung``.

Wiederaufnahme wie ``hole_stundenkurse.py``: Start BEI ``MAX(stunde)`` (die letzte Kerze war beim Laden offen), ``INSERT OR REPLACE``.
Beruehrt keine bestehende Datenbank (die Messbasis wird nur lesend nach ihren Symbolen gefragt).

    python hole_stundenkurse_alle.py --pruefen      # nur zaehlen
    python hole_stundenkurse_alle.py --symbole 5    # Probelauf
    python hole_stundenkurse_alle.py                # Erstbefuellung bzw. Nachladen
"""
from __future__ import annotations

import os
import re
import sqlite3
import sys
import time
from datetime import datetime, timezone

import requests

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HIER = os.path.dirname(os.path.abspath(__file__))
ZIEL = os.path.join(HIER, "data", "stundenkurse_alle.db")
MESSBASIS = os.path.join(HIER, "data", "stundenkurse.db")
SPOT = ("https://api.binance.com/api/v3/exchangeInfo", "https://api.binance.com/api/v3/klines")
FUT = ("https://fapi.binance.com/fapi/v1/exchangeInfo", "https://fapi.binance.com/fapi/v1/klines")
AB = "2023-01-01 00:00"
MAX_KERZEN = 1000
PAUSE_S = 0.10
# Stablecoins, Fiat und Edelmetall-Token: kein Kursverlauf im Sinne der REGEL0 (gemessen 01.10. aus der Binance-Liste)
OHNE = {"USDC", "FDUSD", "TUSD", "USDP", "DAI", "EUR", "EURI", "AEUR", "XUSD", "USD1", "BFUSD", "USDE", "RLUSD", "USDS", "PAXG", "XAUT"}


def _ms(stunde):
    return int(datetime.strptime(stunde, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc).timestamp() * 1000)


def _stunde(ms):
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M")


def universum():
    """-> [(symbol, markt, paar)] nach der Regel oben, ohne die Messbasis."""
    sp = requests.get(SPOT[0], timeout=30).json()["symbols"]
    spot = {x["baseAsset"]: x["symbol"] for x in sp if x["quoteAsset"] == "USDT" and x["status"] == "TRADING" and x["baseAsset"] not in OHNE}
    fu = requests.get(FUT[0], timeout=30).json()["symbols"]
    fut = {x["baseAsset"]: x["symbol"] for x in fu if x["quoteAsset"] == "USDT" and x.get("contractType") == "PERPETUAL"
           and x["status"] == "TRADING" and x.get("underlyingType") == "COIN" and x["baseAsset"] not in OHNE}
    onboard = {x["baseAsset"]: x.get("onboardDate") for x in fu if x["baseAsset"] in fut}

    def ohne_praefix(b):
        m = re.match(r"^(1000000|1000|1M)(.+)$", b)
        return m.group(2) if m else b
    c = sqlite3.connect("file:%s?mode=ro" % MESSBASIS.replace("\\", "/"), uri=True)
    mb = {r[0] for r in c.execute("SELECT DISTINCT symbol FROM stundenkurse")}
    c.close()
    aus = []
    for b, p in sorted(spot.items()):
        if b in mb:
            continue
        if b in fut and onboard.get(b):
            r = requests.get(SPOT[1], params={"symbol": p, "interval": "1h", "limit": 1, "startTime": _ms(AB)}, timeout=30).json()
            s0 = r[0][0] if r else None
            f0 = max(int(onboard[b]), _ms(AB))
            time.sleep(PAUSE_S)
            if s0 is not None and f0 < s0 - 30 * 24 * 3_600_000:
                aus.append((b, "futures", fut[b]))
                continue
        aus.append((b, "spot", p))
    for b, p in sorted(fut.items()):
        if b in spot or ohne_praefix(b) in spot or b in mb or ohne_praefix(b) in mb:
            continue
        aus.append((b, "futures", p))
    return aus, len(spot), len(fut), len(mb)


def lege_an(pfad):
    c = sqlite3.connect(pfad)
    c.execute("""CREATE TABLE IF NOT EXISTS stundenkurse (
                   symbol TEXT NOT NULL, stunde TEXT NOT NULL,
                   open REAL, high REAL, low REAL, close REAL, volumen REAL,
                   PRIMARY KEY (symbol, stunde))""")
    c.execute("CREATE TABLE IF NOT EXISTS _quelle (symbol TEXT PRIMARY KEY, markt TEXT, paar TEXT, geholt_am TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS _nur_bewertung (hinweis TEXT)")
    c.execute("DELETE FROM _nur_bewertung")
    c.execute("INSERT INTO _nur_bewertung VALUES (?)", (
        "Datenbasis fuer die BEWERTUNG (O11, 01.10.2026) - NICHT Teil der Messbasis und NICHT im Training der REGEL0 (Frage 4).",))
    c.commit()
    return c


def hole(url, paar, start, ende):
    aus = []
    while start < ende:
        r = requests.get(url, params={"symbol": paar, "interval": "1h", "limit": MAX_KERZEN, "startTime": start}, timeout=30)
        if r.status_code in (418, 429):
            time.sleep(30)
            continue
        r.raise_for_status()
        k = r.json()
        if not k:
            break
        aus.extend(k)
        neu = k[-1][0] + 3_600_000
        if neu <= start:
            break
        start = neu
        time.sleep(PAUSE_S)
    return aus


def main() -> int:
    nur = "--pruefen" in sys.argv
    grenze = int(sys.argv[sys.argv.index("--symbole") + 1]) if "--symbole" in sys.argv else None
    print("=" * 96)
    print("STUENDLICHE KURSE - ALLE KRYPTO-ASSETS BEI BINANCE (O11) -> %s" % os.path.relpath(ZIEL, HIER))
    print("=" * 96)
    u, ns, nf, nm = universum()
    print("  Binance: Spot %d · Futures (COIN) %d · Messbasis %d (bleibt unberuehrt) · NEU zu laden: %d (Spot %d, nur Futures %d)" % (
        ns, nf, nm, len(u), sum(1 for x in u if x[1] == "spot"), sum(1 for x in u if x[1] == "futures")))
    if grenze:
        u = u[:grenze]
        print("  ⚠️ PROBELAUF - nur die ersten %d" % grenze)
    if nur:
        print("  --pruefen: nichts geholt.")
        return 0
    c = lege_an(ZIEL)
    t0, geholt, fehler = time.time(), 0, []
    jetzt = int(time.time() * 1000)
    for i, (sym, markt, paar) in enumerate(u, 1):
        alt = c.execute("SELECT markt FROM _quelle WHERE symbol=?", (sym,)).fetchone()
        if alt and alt[0] != markt:                 # Quelle gewechselt (laengere Historie): die alte Reihe ganz ersetzen, nicht stueckeln
            c.execute("DELETE FROM stundenkurse WHERE symbol=?", (sym,))
            c.commit()
            print("  %-12s Quelle %s -> %s (laengere Historie), Reihe neu" % (sym, alt[0], markt))
        vorh = c.execute("SELECT MAX(stunde) FROM stundenkurse WHERE symbol=?", (sym,)).fetchone()[0]
        start = _ms(vorh) if vorh else _ms(AB)
        try:
            k = hole((SPOT if markt == "spot" else FUT)[1], paar, start, jetzt)
        except Exception as exc:                                     # noqa: BLE001
            fehler.append("%s: %s" % (sym, str(exc)[:60]))
            continue
        if k:
            c.executemany("INSERT OR REPLACE INTO stundenkurse VALUES (?,?,?,?,?,?,?)",
                          [(sym, _stunde(x[0]), float(x[1]), float(x[2]), float(x[3]), float(x[4]), float(x[5])) for x in k])
            c.execute("INSERT OR REPLACE INTO _quelle VALUES (?,?,?,?)", (sym, markt, paar, datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")))
            c.commit()
            geholt += len(k)
        if i % 25 == 0 or i == len(u):
            print("  [%3d/%3d] %-12s %s Kerzen · %.1f Min" % (i, len(u), sym, f"{geholt:,}".replace(",", "."), (time.time() - t0) / 60))
    n = c.execute("SELECT COUNT(*) FROM stundenkurse").fetchone()[0]
    s = c.execute("SELECT COUNT(DISTINCT symbol) FROM stundenkurse").fetchone()[0]
    c.close()
    print("  FERTIG: %s Zeilen · %d Symbole · %.0f MB · %.1f Min" % (f"{n:,}".replace(",", "."), s, os.path.getsize(ZIEL) / 1e6, (time.time() - t0) / 60))
    if fehler:
        print("  ⚠️ %d Symbole mit Fehler: %s" % (len(fehler), "; ".join(fehler[:8])))
    print("SCHLUSS: vollstaendig")
    return 0


if __name__ == "__main__":
    sys.exit(main())
