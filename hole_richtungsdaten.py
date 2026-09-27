# -*- coding: utf-8 -*-
"""Laedt die RICHTUNGSDATEN aus dem Binance-Archiv: Kaeuferanteil und Premium-Index, stuendlich.

**27.09.2026.** Nutzerauftrag: *"Loader bauen, Probelauf, dann Vollladung
starten ... Wenn wir die Daten haben, die wir benoetigen, diese kennzeichnen,
damit wir diese wiederverwenden koennen."* Und: *"Vorsicht bei API-Aufrufen,
nicht zu schnell, um nicht gesperrt zu werden."*

WARUM (2.660): Die Richtung ist mit Kurs, Funding, Open Interest und
Long/Short-Verhaeltnis ausgereizt. Zwei Reihen liegen naeher an der Richtung
und sind kostenfrei mit Historie vorhanden (Recherche 27.09.):
    fluss     KAEUFERANTEIL: Taker-Kaufvolumen je Stunde (wer aggressiv kauft).
              Steht in jeder Binance-Kerze (Spalte 9) - `hole_stundenkurse.py`
              speichert nur Spalte 0 bis 5 und hat ihn bisher VERWORFEN.
              Quelle Spot; gibt es kein Spot-Paar, die Terminmarkt-Kerze
              (Spalte `quelle` sagt, welche).
    premium   AUFSCHLAG Terminmarkt gegen Spot (Premium-Index-Kerze, o/h/l/c).
              Feiner und schneller als das taegliche Funding.

QUELLE: data.binance.vision - ein statischer Dateiserver (Monatsdateien),
keine API mit Gewichtslimit. Trotzdem EINE Datei nach der anderen mit Pause
(Vorgabe 0,5 s), bei 429/418 eine Minute warten.

ZEIT: `stunde` = BEGINN der Stunde in UTC als 'YYYY-MM-DD HH:MM' - dieselbe
Konvention wie `stundenkurse` (Kerze nach Oeffnungszeit). ⚠️ Die Spot-Archive
fuehren ab 2025 MIKROsekunden statt Millisekunden - wird erkannt.

KENNZEICHNUNG FUER DIE WIEDERVERWENDUNG
    _herkunft  was in der Datei steht: Quelle, Spalten, Einheiten, Zeit, Zweck
    _geladen   je Symbol, Reihe und Monat: ok / fehlt / fehler - fortsetzbar

SCHUTZ: schreibt NUR in die eigene Datei (Vorgabe data/richtung_historie.db);
verweigert jede Datei namens tradinginfotool.db (Produktion).

    python hole_richtungsdaten.py --symbole BTC,ETH,1000CAT --von 2024-12 --bis 2025-02 --db <Pfad>
    python hole_richtungsdaten.py --von 2023-01 --bis 2026-08
"""
from __future__ import annotations

import argparse
import csv
import io
import os
import sqlite3
import sys
import time
import zipfile
from datetime import datetime, timezone

import requests

HIER = os.path.dirname(os.path.abspath(__file__))
VORGABE_DB = os.path.join(HIER, "data", "richtung_historie.db")
STUNDEN_DB = os.path.join(HIER, "data", "stundenkurse.db")
BASIS = "https://data.binance.vision/data"
URL = {"spot": BASIS + "/spot/monthly/klines/{p}/1h/{p}-1h-{m}.zip",
       "um": BASIS + "/futures/um/monthly/klines/{p}/1h/{p}-1h-{m}.zip",
       "premium": BASIS + "/futures/um/monthly/premiumIndexKlines/{p}/1h/{p}-1h-{m}.zip"}
# ⭐ BTC-DOMINANZ (Nutzerwunsch 27.09.): Binance-Terminmarkt-Index BTCDOMUSDT.
# Offiziell und im Archiv ab 2021-06, stuendlich. ⚠️ KEIN Prozentanteil,
# sondern ein Index ueber gewichtete Top-Coins, der sich wie die Dominanz
# bewegt - brauchbar fuer VERAENDERUNG und Richtung, nicht als Niveau.
# Die echte Dominanz in Prozent gibt es kostenfrei nur ueber einen
# undokumentierten CoinMarketCap-Endpunkt gegen deren Nutzungsbedingungen -
# bewusst NICHT verwendet (Nutzerentscheidung 27.09.).
BTCDOM_PAAR = "BTCDOMUSDT"

HERKUNFT = {
    "kennzeichen": "MESSBASIS RICHTUNGSDATEN - Kaeuferanteil und Premium-Index, stuendlich",
    "quelle": "data.binance.vision (Binance-Archiv, Monatsdateien, kostenfrei, ohne Schluessel)",
    "zweck": "Richtungs-Beitraege fuer den Hebel-Neubau (Befund 2.660: Richtung mit den alten Merkmalen ausgereizt)",
    "tabelle fluss": "symbol, stunde, quelle (spot | um), volumen, kauf_volumen, quote_volumen, kauf_quote, trades",
    "einheit fluss": "volumen/kauf_volumen in Stueck des Basiswerts, quote_* in USDT; Kaeuferanteil = kauf_volumen / volumen",
    "tabelle premium": "symbol, stunde, open, high, low, close des Premium-Index (Terminmarkt USDT-M gegen Index)",
    "einheit premium": "dimensionslos, Anteil (0,001 = 0,1 Prozent Aufschlag)",
    "zeit": "stunde = BEGINN der Stunde, UTC, 'YYYY-MM-DD HH:MM' - wie stundenkurse; der Wert ist mit dem Schlusskurs der Stunde bekannt",
    "zuordnung": "Symbol + USDT; fluss aus Spot, ohne Spot-Paar aus der Terminmarkt-Kerze (Spalte quelle)",
    "lader": "hole_richtungsdaten.py",
    "tabelle btcdom": "stunde, open, high, low, close, volumen - Binance-Terminmarkt BTCDOMUSDT (1h-Kerze)",
    "einheit btcdom": "Indexpunkte, KEIN Prozentanteil - nur Veraenderung und Richtung sind deutbar",
}


def monate(von: str, bis: str) -> list:
    j, m = map(int, von.split("-"))
    j2, m2 = map(int, bis.split("-"))
    aus = []
    while (j, m) <= (j2, m2):
        aus.append("%04d-%02d" % (j, m))
        m += 1
        if m > 12:
            j, m = j + 1, 1
    return aus


def stunde(ts) -> str:
    t = int(float(ts))
    if t > 10 ** 14:              # Mikrosekunden (Spot-Archiv ab 2025)
        t //= 1000
    return datetime.fromtimestamp(t / 1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M")


def lege_an(pfad: str) -> sqlite3.Connection:
    if os.path.basename(pfad).lower() == "tradinginfotool.db":
        raise SystemExit("⛔ verweigert: %s ist die Produktionsdatei" % pfad)
    c = sqlite3.connect(pfad)
    c.execute("""CREATE TABLE IF NOT EXISTS fluss (
                   symbol TEXT NOT NULL, stunde TEXT NOT NULL, quelle TEXT NOT NULL,
                   volumen REAL, kauf_volumen REAL, quote_volumen REAL,
                   kauf_quote REAL, trades INTEGER, PRIMARY KEY (symbol, stunde))""")
    c.execute("""CREATE TABLE IF NOT EXISTS premium (
                   symbol TEXT NOT NULL, stunde TEXT NOT NULL,
                   open REAL, high REAL, low REAL, close REAL,
                   PRIMARY KEY (symbol, stunde))""")
    c.execute("""CREATE TABLE IF NOT EXISTS _geladen (
                   symbol TEXT NOT NULL, reihe TEXT NOT NULL, monat TEXT NOT NULL,
                   status TEXT NOT NULL, anzahl INTEGER, geholt_am TEXT,
                   PRIMARY KEY (symbol, reihe, monat))""")
    c.execute("""CREATE TABLE IF NOT EXISTS btcdom (
                   stunde TEXT PRIMARY KEY, open REAL, high REAL, low REAL,
                   close REAL, volumen REAL)""")
    c.execute("CREATE TABLE IF NOT EXISTS _herkunft (schluessel TEXT PRIMARY KEY, wert TEXT)")
    c.executemany("INSERT OR REPLACE INTO _herkunft VALUES (?,?)", list(HERKUNFT.items()))
    c.commit()
    return c


def hole(url: str, pause: float):
    """-> Zeilen der CSV oder None (404). Wiederholt bei Stoerung."""
    for versuch in range(4):
        try:
            r = requests.get(url, timeout=60)
        except requests.RequestException:
            time.sleep(10 * (versuch + 1))
            continue
        time.sleep(pause)
        if r.status_code == 404:
            return None
        if r.status_code in (418, 429):
            time.sleep(60)
            continue
        if r.status_code != 200:
            time.sleep(10 * (versuch + 1))
            continue
        z = zipfile.ZipFile(io.BytesIO(r.content))
        text = z.read(z.namelist()[0]).decode("utf-8")
        zeilen = [x for x in csv.reader(io.StringIO(text)) if x]
        if zeilen and not zeilen[0][0].strip().isdigit():     # Kopfzeile
            zeilen = zeilen[1:]
        return zeilen
    raise RuntimeError("keine Antwort nach 4 Versuchen: %s" % url)


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:                                         # noqa: BLE001
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=VORGABE_DB)
    ap.add_argument("--symbole", default="")
    ap.add_argument("--von", default="2023-01")
    ap.add_argument("--bis", default="2026-08")
    ap.add_argument("--pause", type=float, default=0.5)
    ap.add_argument("--nur-btcdom", action="store_true",
                    help="nur die Reihe BTCDOMUSDT laden (Tabelle btcdom)")
    ap.add_argument("--teil", default="",
                    help="i/N: nur jedes N-te Symbol ab i (0-basiert) - fuer parallele "
                         "Arbeiter, JEDER in eine EIGENE --db (keine Schreibkonflikte)")
    ap.add_argument("--zusammen", nargs="*", default=None,
                    help="Teildateien in --db zusammenfuehren (danach pruefe_richtungsdaten.py)")
    ap.add_argument("--premium-tag", default="",
                    help="YYYY-MM-DD: einen Tag Premium-Index aus den TAGESdateien nachladen - "
                         "die Monatsdatei 2026-06 fehlt am 29.06. bei ALLEN Symbolen (Archivluecke)")
    a = ap.parse_args()
    if a.premium_tag:
        c = lege_an(a.db)
        s = sqlite3.connect("file:%s?mode=ro" % STUNDEN_DB, uri=True)
        syms = sorted(r[0] for r in s.execute("SELECT DISTINCT symbol FROM stundenkurse"))
        s.close()
        url = BASIS + "/futures/um/daily/premiumIndexKlines/{p}/1h/{p}-1h-{m}.zip"
        neu = 0
        for sym in syms:
            zeilen = hole(url.format(p="%sUSDT" % sym, m=a.premium_tag), a.pause)
            if zeilen:
                vorher = c.total_changes
                c.executemany("INSERT OR IGNORE INTO premium VALUES (?,?,?,?,?,?)",
                              [(sym, stunde(z[0]), float(z[1]), float(z[2]), float(z[3]),
                                float(z[4])) for z in zeilen])
                neu += c.total_changes - vorher
            c.commit()
        print("  premium %s: %d Stunden nachgeladen" % (a.premium_tag, neu))
        c.close()
        return 0
    if a.zusammen is not None:
        c = lege_an(a.db)
        for teil in a.zusammen:
            # ⚠️ Pfad, nicht URI: die Verbindung ist keine URI-Verbindung. Aus
            # der Teildatei wird nur gelesen (SELECT).
            c.execute("ATTACH DATABASE ? AS t", (os.path.abspath(teil),))
            for tab in ("fluss", "premium", "btcdom"):
                if c.execute("SELECT COUNT(*) FROM t.sqlite_master WHERE name=?",
                             (tab,)).fetchone()[0]:
                    c.execute("INSERT OR IGNORE INTO %s SELECT * FROM t.%s" % (tab, tab))
            c.execute("INSERT OR REPLACE INTO _geladen SELECT * FROM t._geladen")
            c.commit()
            c.execute("DETACH DATABASE t")
            print("  zusammengefuehrt: %s" % teil)
        c.close()
        return 0
    if a.nur_btcdom:
        c = lege_an(a.db)
        erledigt = {r[0] for r in c.execute("SELECT monat FROM _geladen WHERE "
                                            "symbol=? AND reihe='btcdom' AND status IN ('ok','fehlt')",
                                            (BTCDOM_PAAR,))}
        ms = monate(a.von, a.bis)
        print("BTCDOM: %d Monate -> %s (Pause %.1f s)" % (len(ms), a.db, a.pause), flush=True)
        for m in ms:
            if m in erledigt:
                continue
            zeilen = None
            try:
                zeilen = hole(URL["um"].format(p=BTCDOM_PAAR, m=m), a.pause)
                status = "ok" if zeilen else "fehlt"
                if zeilen:
                    c.executemany("INSERT OR REPLACE INTO btcdom VALUES (?,?,?,?,?,?)",
                                  [(stunde(z[0]), float(z[1]), float(z[2]), float(z[3]),
                                    float(z[4]), float(z[5])) for z in zeilen])
            except Exception as exc:                          # noqa: BLE001
                status = "fehler"
                print("  btcdom %s: %s" % (m, str(exc)[:80]), flush=True)
            c.execute("INSERT OR REPLACE INTO _geladen VALUES (?,?,?,?,?,?)",
                      (BTCDOM_PAAR, "btcdom", m, status, len(zeilen or []),
                       datetime.now(timezone.utc).isoformat(timespec="seconds")))
            c.commit()
        n, v, b = c.execute("SELECT COUNT(*), MIN(stunde), MAX(stunde) FROM btcdom").fetchone()
        print("  btcdom %d Stunden · %s bis %s" % (n, v, b))
        c.close()
        return 0
    # ⭐ START JE SYMBOL: erst ab dem Monat, den auch stundenkurse hat - vor der
    # Listung gibt es nichts, und jede Anfrage dorthin ist ein Leerlauf (bei
    # 1000CAT waren es 42 von 88).
    s = sqlite3.connect("file:%s?mode=ro" % STUNDEN_DB, uri=True)
    erster = {r[0]: r[1][:7] for r in s.execute(
        "SELECT symbol, MIN(stunde) FROM stundenkurse GROUP BY symbol")}
    s.close()
    if a.symbole:
        syms = [x.strip().upper() for x in a.symbole.split(",") if x.strip()]
    else:
        syms = sorted(erster)
    if a.teil:
        i_, n_ = map(int, a.teil.split("/"))
        syms = syms[i_::n_]
    ms = monate(a.von, a.bis)
    c = lege_an(a.db)
    erledigt = {(r[0], r[1], r[2]) for r in c.execute(
        "SELECT symbol, reihe, monat FROM _geladen WHERE status IN ('ok','fehlt')")}
    print("Richtungsdaten: %d Symbole x %d Monate -> %s (Pause %.1f s)"
          % (len(syms), len(ms), a.db, a.pause), flush=True)
    t0, dateien, zaehl = time.time(), 0, {"ok": 0, "fehlt": 0, "fehler": 0}
    for i, sym in enumerate(syms, 1):
        paar = "%sUSDT" % sym
        for m in ms:
            if sym in erster and m < erster[sym]:
                continue
            # Kaeuferanteil: Spot, sonst Terminmarkt
            if (sym, "fluss", m) not in erledigt:
                quelle, zeilen = "spot", None
                try:
                    zeilen = hole(URL["spot"].format(p=paar, m=m), a.pause)
                    if zeilen is None:
                        quelle = "um"
                        zeilen = hole(URL["um"].format(p=paar, m=m), a.pause)
                    status = "ok" if zeilen else "fehlt"
                    if zeilen:
                        c.executemany(
                            "INSERT OR REPLACE INTO fluss VALUES (?,?,?,?,?,?,?,?)",
                            [(sym, stunde(z[0]), quelle, float(z[5]), float(z[9]),
                              float(z[7]), float(z[10]), int(float(z[8]))) for z in zeilen])
                except Exception as exc:                      # noqa: BLE001
                    status = "fehler"
                    print("  %s fluss %s: %s" % (sym, m, str(exc)[:80]), flush=True)
                c.execute("INSERT OR REPLACE INTO _geladen VALUES (?,?,?,?,?,?)",
                          (sym, "fluss", m, status, len(zeilen or []),
                           datetime.now(timezone.utc).isoformat(timespec="seconds")))
                zaehl[status] += 1
                dateien += 1
            if (sym, "premium", m) not in erledigt:
                zeilen = None
                try:
                    zeilen = hole(URL["premium"].format(p=paar, m=m), a.pause)
                    status = "ok" if zeilen else "fehlt"
                    if zeilen:
                        c.executemany(
                            "INSERT OR REPLACE INTO premium VALUES (?,?,?,?,?,?)",
                            [(sym, stunde(z[0]), float(z[1]), float(z[2]), float(z[3]),
                              float(z[4])) for z in zeilen])
                except Exception as exc:                      # noqa: BLE001
                    status = "fehler"
                    print("  %s premium %s: %s" % (sym, m, str(exc)[:80]), flush=True)
                c.execute("INSERT OR REPLACE INTO _geladen VALUES (?,?,?,?,?,?)",
                          (sym, "premium", m, status, len(zeilen or []),
                           datetime.now(timezone.utc).isoformat(timespec="seconds")))
                zaehl[status] += 1
                dateien += 1
            c.commit()
        print("  [%3d/%3d] %-10s  %d Dateien · ok %d · fehlt %d · Fehler %d · %.1f Min"
              % (i, len(syms), sym, dateien, zaehl["ok"], zaehl["fehlt"],
                 zaehl["fehler"], (time.time() - t0) / 60), flush=True)
    for t in ("fluss", "premium"):
        n, s_, v, b = c.execute("SELECT COUNT(*), COUNT(DISTINCT symbol), MIN(stunde), "
                                "MAX(stunde) FROM %s" % t).fetchone()
        print("  %-8s %9d Zeilen · %3d Symbole · %s bis %s" % (t, n, s_, v, b))
    c.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
