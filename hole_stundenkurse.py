# -*- coding: utf-8 -*-
"""Stuendliche Kerzen von Binance - die fehlende Haelfte des Datenschatzes.

Vorabfestlegung: `Basisinfos/Vorabfestlegung_Geometrie_Hebel_24_09.md`
Befunde 2.580, 2.581, 2.582.

═══════════════════════════════════════════════════════════════════════
 WARUM - und warum es keine Verbesserung ist, sondern Voraussetzung
═══════════════════════════════════════════════════════════════════════

Gemessen am 24.09. (2.582), ueber sechs Horizonte:

    H2   29,5 % Stop   61,3 % OFFEN   bedingte Quote 23,7 %
    H20  63,3 % Stop    4,8 % offen   bedingte Quote 33,5 %

Bei kurzen Haltedauern bleibt die MEHRHEIT der Trades offen - sie enden
weder im Ziel noch im Stop, sondern durch Entscheidung. Ihr Ergebnis ist
der Zwischenstand beim Ausstieg.

⚠️⚠️ AUF TAGESDATEN KENNEN WIR DIESEN KURS NICHT. Damit ist der kurze
Horizont - der, auf dem der Hebel stattfindet - gar nicht bewertbar. Die
Zielgroesse `barriere` wirft die offenen Faelle heute weg und misst
dadurch ein Drittel der Wirklichkeit, und zwar das unguenstigste.

➤ Die stuendlichen TERMINMARKT-Daten liegen laengst vor: 3.355.712 Zeilen,
122 Symbole, sieben Groessen, seit 2021-12. Es fehlen die KURSE in
derselben Aufloesung. Diese Datei holt sie.

═══════════════════════════════════════════════════════════════════════
 MACHBARKEIT - vor dem Bau gemessen, nicht geschaetzt
═══════════════════════════════════════════════════════════════════════

    Abdeckung     117 von 122 Symbolen bei Binance handelbar
                  (es fehlen XMR, KAS, BRETT, AKT, GRIFFAIN)
    Abrufe        3.295 a 1000 Stundenkerzen
    Gewicht       2 je Abruf - GEMESSEN am Antwortkopf x-mbx-used-weight
                  (Limit 1200/Minute, also 600 Abrufe/Min moeglich)
    Laufzeit      rund 33 Minuten sequenziell, konservativ
    Datenmenge    rund 195 MB
    Zugang        kostenlos, ohne Schluessel - DIESELBE API, die fuer
                  Funding und Open Interest ohnehin laeuft

═══════════════════════════════════════════════════════════════════════
 ⚠️⚠️ MESSBASIS, NICHT BETRIEB - die Trennung gilt unveraendert
═══════════════════════════════════════════════════════════════════════

Die Datei gehoert zur selben Klasse wie `messdaten.db` (1,5 GB), die am
Notebook MIT ABSICHT fehlt. Der Betrieb rechnet mit Tageskursen und
braucht sie nicht.

    Desktop    ✔ hierher
    Notebook   ⛔ kommt nicht hin - kein Speicher, keine Last, kein Netz

⚠️ Sie wird deshalb als eigene Datei gefuehrt (`data/stundenkurse.db`) und
NICHT in `messdaten.db` gelegt: eine Messbasis, die versehentlich
mitwandert, ist genau der Fall, den die Geraetetrennung verhindern soll.

⚠️⚠️ UND SIE RUEHRT KEINE BESTEHENDE DATENBANK AN. `data/tradinginfotool.db`
ist am Notebook die PRODUKTION; dieses Werkzeug oeffnet sie nicht einmal
lesend.

    python hole_stundenkurse.py --pruefen      # nur rechnen, nichts holen
    python hole_stundenkurse.py                # der Abruf
    python hole_stundenkurse.py --symbole 5    # kleiner Probelauf
"""
from __future__ import annotations

import os
import sqlite3
import sys
import time
from datetime import datetime, timezone

import requests

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

URL = "https://api.binance.com/api/v3/klines"
INFO = "https://api.binance.com/api/v3/exchangeInfo"
ZIEL = os.path.join("data", "stundenkurse.db")
QUELLE = os.path.join("data", "terminmarkt_historie.db")
MAX_KERZEN = 1000
# ⚠️ Konservativ: das Limit erlaubt 600 Abrufe/Minute, wir nehmen ein
# Zehntel davon. Ein Abruf, der wegen Ueberlast scheitert, kostet mehr
# Zeit als die Pause.
PAUSE_S = 0.10


def _ms(stunde: str) -> int:
    return int(datetime.strptime(stunde, "%Y-%m-%d %H:%M")
               .replace(tzinfo=timezone.utc).timestamp() * 1000)


def _stunde(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).strftime(
        "%Y-%m-%d %H:%M")


def symbole_und_spanne() -> list:
    """Welche Symbole, und ab wann? - aus dem TERMINMARKT abgeleitet.

    ⚠️ Nicht aufgezaehlt: gebraucht werden genau die Symbole, fuer die es
    stuendliche MERKMALE gibt. Ein Kurs ohne Merkmal traegt keinen Beitrag.
    """
    c = sqlite3.connect("file:%s?mode=ro" % QUELLE, uri=True)
    rows = c.execute(
        "SELECT symbol, MIN(stunde), MAX(stunde), COUNT(*) "
        "FROM terminmarkt GROUP BY symbol ORDER BY COUNT(*) DESC").fetchall()
    c.close()
    return rows


def handelbar() -> set:
    r = requests.get(INFO, timeout=30)
    r.raise_for_status()
    return {s["symbol"] for s in r.json()["symbols"] if s["status"] == "TRADING"}


def lege_an(pfad: str) -> sqlite3.Connection:
    neu = not os.path.exists(pfad)
    c = sqlite3.connect(pfad)
    c.execute("""CREATE TABLE IF NOT EXISTS stundenkurse (
                   symbol TEXT NOT NULL, stunde TEXT NOT NULL,
                   open REAL, high REAL, low REAL, close REAL, volumen REAL,
                   PRIMARY KEY (symbol, stunde))""")
    # ⚠️ DIE MARKE, analog `_nur_symbolliste` und `_nur_betrieb`: diese
    # Datei ist eine MESSBASIS und gehoert nicht aufs Notebook.
    c.execute("CREATE TABLE IF NOT EXISTS _nur_messbasis "
              "(hinweis TEXT)")
    c.execute("DELETE FROM _nur_messbasis")
    c.execute("INSERT INTO _nur_messbasis VALUES (?)",
              ("Messbasis - gehoert NICHT aufs Notebook (wie messdaten.db). "
               "Angelegt 2026-09-24, Befund 2.582.",))
    c.commit()
    if neu:
        print("  angelegt: %s" % pfad)
    return c


def hole(symbol: str, von_ms: int, bis_ms: int) -> list:
    """Alle Stundenkerzen im Fenster - in Bloecken zu 1000."""
    aus, start = [], von_ms
    while start < bis_ms:
        r = requests.get(URL, params={"symbol": "%sUSDT" % symbol,
                                      "interval": "1h", "limit": MAX_KERZEN,
                                      "startTime": start}, timeout=30)
        if r.status_code == 429:                    # Rate limit
            time.sleep(30)
            continue
        r.raise_for_status()
        k = r.json()
        if not k:
            break
        aus.extend(k)
        neu_start = k[-1][0] + 3_600_000
        if neu_start <= start:                      # kein Fortschritt
            break
        start = neu_start
        time.sleep(PAUSE_S)
    return aus


def main() -> int:
    nur_rechnen = "--pruefen" in sys.argv
    grenze = None
    if "--symbole" in sys.argv:
        grenze = int(sys.argv[sys.argv.index("--symbole") + 1])

    print("=" * 84)
    print("STUENDLICHE KURSE VON BINANCE - die fehlende Haelfte")
    print("=" * 84)
    rows = symbole_und_spanne()
    print("  Terminmarkt: %d Symbole mit stuendlichen Merkmalen" % len(rows))
    paare = handelbar()
    da = [r for r in rows if "%sUSDT" % r[0] in paare]
    fehlt = [r[0] for r in rows if "%sUSDT" % r[0] not in paare]
    print("  Bei Binance handelbar: %d   ohne Paar: %s"
          % (len(da), ", ".join(fehlt) or "-"))
    if grenze:
        da = da[:grenze]
        print("  ⚠️ PROBELAUF - nur die ersten %d" % grenze)
    abrufe = sum((r[3] + MAX_KERZEN - 1) // MAX_KERZEN for r in da)
    print("  Erwartete Abrufe: %d · Stunden: %s"
          % (abrufe, f"{sum(r[3] for r in da):,}".replace(",", ".")))
    print("  Geschaetzte Dauer: %.0f Minuten" % (abrufe * 0.6 / 60))
    if nur_rechnen:
        print("\n  --pruefen: nichts geholt.")
        return 0

    c = lege_an(ZIEL)
    t0, geholt, fehler = time.time(), 0, []
    for i, (sym, von, bis, n) in enumerate(da, 1):
        # ⚠️ WIEDERAUFNAHME: was schon dasteht, wird nicht neu geholt -
        # MIT EINER AUSNAHME, und die ist der Grund fuer diese Zeilen.
        #
        # ⛔⛔ BEFUND 25.09.2026: die JEWEILS LETZTE Kerze war beim Laden
        # noch OFFEN und blieb es fuer immer. Gemessen ueber 116 Symbole:
        # Median-Volumenquote der letzten Kerze 0,720 (bei vollstaendiger
        # Kerze 1,0), 43 von 116 unter 60 %. Am Einzelfall BTC, Stunde
        # 2026-09-24 15:00, gegen eine frisch geholte Reihe:
        #     hier:    high 84100,01  close 84080,01  vol  481,36
        #     Binance: high 84468,01  close 84418,00  vol 1011,04
        # `open` und `low` stimmen exakt - dieselbe Kerze, zu
        # verschiedenen Zeitpunkten gelesen.
        #
        # ⚠️ Es war KEIN selbstheilendes Problem: der Start lag bei
        # `MAX(stunde) + 1 Stunde`, die offene Kerze wurde also nie wieder
        # abgerufen - und `INSERT OR IGNORE` haette sie ohnehin nicht
        # ueberschrieben. 43 Symbole trugen eine unvollstaendige Kerze vom
        # 24.09., und kein Lauf haette sie je korrigiert.
        #
        # ➤ Jetzt setzt der Start BEI `MAX(stunde)` an, und das Einfuegen
        # ueberschreibt (siehe `INSERT OR REPLACE` unten). Kostet einen
        # Abruf mehr je Symbol und macht die letzte Kerze richtig.
        vorh = c.execute("SELECT MAX(stunde) FROM stundenkurse WHERE symbol=?",
                         (sym,)).fetchone()[0]
        start = _ms(vorh) if vorh else _ms(von)
        ende = _ms(bis) + 3_600_000
        if start >= ende:
            continue
        try:
            k = hole(sym, start, ende)
        except Exception as exc:                             # noqa: BLE001
            fehler.append("%s: %s" % (sym, str(exc)[:60]))
            continue
        if k:
            c.executemany(
                # ⚠️ REPLACE statt IGNORE - sonst bliebe die zuvor
                # offene Kerze stehen, obwohl sie gerade neu geholt wurde.
                "INSERT OR REPLACE INTO stundenkurse VALUES (?,?,?,?,?,?,?)",
                [(sym, _stunde(x[0]), float(x[1]), float(x[2]), float(x[3]),
                  float(x[4]), float(x[5])) for x in k])
            c.commit()
            geholt += len(k)
        if i % 10 == 0 or i == len(da):
            print("  [%3d/%3d] %-10s  %s Kerzen  %.1f Min"
                  % (i, len(da), sym, f"{geholt:,}".replace(",", "."),
                     (time.time() - t0) / 60))
    print()
    n = c.execute("SELECT COUNT(*) FROM stundenkurse").fetchone()[0]
    s = c.execute("SELECT COUNT(DISTINCT symbol) FROM stundenkurse").fetchone()[0]
    lo, hi = c.execute("SELECT MIN(stunde), MAX(stunde) FROM stundenkurse").fetchone()
    c.close()
    print("  FERTIG: %s Zeilen · %d Symbole · %s bis %s · %.0f MB"
          % (f"{n:,}".replace(",", "."), s, lo, hi,
             os.path.getsize(ZIEL) / 1e6))
    if fehler:
        print("  ⚠️ %d Symbole mit Fehler: %s" % (len(fehler), "; ".join(fehler[:5])))
    print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60))
    print()
    print("  ⚠️ MESSBASIS - gehoert NICHT aufs Notebook (Marke `_nur_messbasis`).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
