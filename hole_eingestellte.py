# -*- coding: utf-8 -*-
"""Laedt die EINGESTELLTEN Binance-Paare und BTC ab 2021-12 aus dem Archiv - gegen die Ueberlebensverzerrung.

**27.09.2026.** Befund 2.668: `stundenkurse.db` enthaelt nur heute gehandelte
Paare. Stehende Regel (CLAUDE.md, Kap. 120.3): *"Eingestellte Werte gehoeren
dazu. Ohne sie ist jede Messung ueberlebensverzerrt, und der Boden der
Verteilung fehlt."* Voranalyse: `Basisinfos/Voranalyse_Nachladen_Eingestellte_27_09.md`
(N1-N5 abgestimmt: alle laden, Teil A zuerst, Anker bis zum echten Ende,
Vorgeschichte bei Umbenennungen, Spot vor Terminmarkt).

WAS (Teil A), je Symbol und Monat aus data.binance.vision:
    stundenkurse  Stundenkerze - Spot, ohne Spot-Paar die Terminmarkt-Kerze
                  (Spalte quelle); dieselbe Form wie data/stundenkurse.db
    fluss         Kaeuferanteil aus DERSELBEN Kerze (Spalte 9) - kein Zusatzabruf
    premium       Premium-Index-Kerze
    funding       Tagessumme der Abrechnungen je UTC-Tag - wie hole_fremdreihen.py
    btcdom        nur mit --btc: BTCDOMUSDT 2021-12 bis 2022-12

WER (Tabelle `symbole`, aus data/_recherche_eingestellt.json - recherche_eingestellte_perps.py):
    eingestellt     heute nicht gehandelt, Krypto -> geladen
    vorgeschichte   Umbenennung, Nachfolger ist in unserer Menge -> unter dem
                    NACHFOLGER-Namen geladen (EOS->A, FTM->S, MATIC->POL,
                    RNDR->RENDER, KLAY->KAIA)
    umbenennung     Nachfolger nicht in unserer Menge -> nicht geladen (er hatte
                    seine Chance in der Zufallsziehung)
    kein_krypto     Aktie, Rohstoff, Index - amtlich aus fapi underlyingType,
                    fuer nicht mehr gelistete von Hand (BLUEBIRD, FOOTBALL) -> nicht geladen
    ⚠️ LUNA ist KEINE Umbenennung (LUNA2 ist eine neue Kette, das alte LUNA ist
    im Mai 2022 zusammengebrochen - genau der Boden) - eingestellt.
    ⚠️ NEIROETH ist ein anderer Token als NEIRO - eingestellt.

ZOMBIE-MONATE (Voranalyse 2): das Archiv schreibt nach der Einstellung weiter -
konstanter Kurs, Volumen 0 (FTMUSDT 2026-08). `--abschliessen` schneidet am
Reihenende jeden Lauf von >= 72 Stunden mit Volumen 0 UND unveraendertem Kurs
ab und vermerkt das echte Ende in `symbole`.

SCHUTZ: schreibt NUR in die eigene Datei (Vorgabe data/eingestellt_historie.db),
verweigert tradinginfotool.db (Produktion). Die bestehenden Messbasen bleiben
unveraendert (R-R11: jeder Befund bleibt bitgleich reproduzierbar).
Pause je Datei 0,3 s, bei 418/429 eine Minute (Nutzer: *nicht zu schnell*).

    python hole_eingestellte.py --symbole WAVES,FTT --db <Pfad>          # Probelauf
    python hole_eingestellte.py --teil 0/4 --db data/_teile/eing_0.db     # Arbeiter
    python hole_eingestellte.py --btc --db data/_teile/eing_btc.db
    python hole_eingestellte.py --zusammen data/_teile/eing_*.db
    python hole_eingestellte.py --abschliessen
    python hole_eingestellte.py --kontrolle ETH,SOL,DOGE --von 2024-01 --bis 2024-03 --db <Pfad>
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import time
from datetime import datetime, timezone

from hole_richtungsdaten import BASIS, URL, hole, monate, stunde

HIER = os.path.dirname(os.path.abspath(__file__))
VORGABE_DB = os.path.join(HIER, "data", "eingestellt_historie.db")
RECHERCHE = os.path.join(HIER, "data", "_recherche_eingestellt.json")
UNDERLYING = os.path.join(HIER, "data", "_recherche_underlying.json")
STUNDEN_DB = os.path.join(HIER, "data", "stundenkurse.db")
URL_FUNDING = BASIS + "/futures/um/monthly/fundingRate/{p}/{p}-fundingRate-{m}.zip"
FENSTER = ("2021-12", "2026-08")
ZOMBIE_H = 72

# Umbenennungen - am Archiv belegt (altes Ende / neuer Anfang, Recherche 27.09.)
UMBENENNUNG = {"EOS": "A", "FTM": "S", "MATIC": "POL", "RNDR": "RENDER",
               "KLAY": "KAIA", "AGIX": "FET", "OCEAN": "FET", "MKR": "SKY",
               "GAL": "G", "TOMO": "VIC", "DAR": "D", "STPT": "STP"}
# nicht mehr gelistet, daher ohne amtliche Angabe - Grund je Eintrag
KEIN_KRYPTO_HAND = {"BLUEBIRD": "Index (Binance Bluebird-Index)",
                    "FOOTBALL": "Index (Binance Football-Index)"}

HERKUNFT = {
    "kennzeichen": "MESSBASIS EINGESTELLTE - Binance-Paare, die heute nicht mehr gehandelt werden, plus BTC ab 2021-12",
    "zweck": "gegen die Ueberlebensverzerrung (Befund 2.668); nur MIT data/stundenkurse.db zusammen lesen",
    "quelle": "data.binance.vision (Monatsdateien), Symbolliste aus recherche_eingestellte_perps.py",
    "tabellen": "stundenkurse (+quelle), fluss, premium, funding, btcdom, symbole, _geladen, _herkunft",
    "zeit": "stunde = BEGINN der Stunde, UTC - wie stundenkurse; funding datum = UTC-Tag der Abrechnung",
    "funding": "Tagessumme der Einzelsaetze je UTC-Tag - dieselbe Verdichtung wie hole_fremdreihen.py",
    "zombie": "Reihenende nach --abschliessen = letzte Stunde vor einem Lauf >= 72 h mit Volumen 0 und konstantem Kurs",
    "lader": "hole_eingestellte.py",
}


def lege_an(pfad: str) -> sqlite3.Connection:
    if os.path.basename(pfad).lower() == "tradinginfotool.db":
        raise SystemExit("⛔ verweigert: %s ist die Produktionsdatei" % pfad)
    for vorhanden in ("stundenkurse.db", "funding_historie.db", "richtung_historie.db",
                      "terminmarkt_historie.db", "messdaten.db"):
        if os.path.basename(pfad).lower() == vorhanden:
            raise SystemExit("⛔ verweigert: %s ist eine bestehende Messbasis - "
                             "sie bleibt unveraendert (R-R11)" % pfad)
    os.makedirs(os.path.dirname(os.path.abspath(pfad)), exist_ok=True)
    c = sqlite3.connect(pfad)
    c.executescript("""
        CREATE TABLE IF NOT EXISTS stundenkurse (symbol TEXT NOT NULL, stunde TEXT NOT NULL,
            open REAL, high REAL, low REAL, close REAL, volumen REAL, quelle TEXT,
            PRIMARY KEY (symbol, stunde));
        CREATE TABLE IF NOT EXISTS fluss (symbol TEXT NOT NULL, stunde TEXT NOT NULL,
            quelle TEXT NOT NULL, volumen REAL, kauf_volumen REAL, quote_volumen REAL,
            kauf_quote REAL, trades INTEGER, PRIMARY KEY (symbol, stunde));
        CREATE TABLE IF NOT EXISTS premium (symbol TEXT NOT NULL, stunde TEXT NOT NULL,
            open REAL, high REAL, low REAL, close REAL, PRIMARY KEY (symbol, stunde));
        CREATE TABLE IF NOT EXISTS funding (symbol TEXT NOT NULL, datum TEXT NOT NULL,
            wert REAL NOT NULL, PRIMARY KEY (symbol, datum));
        CREATE TABLE IF NOT EXISTS btcdom (stunde TEXT PRIMARY KEY, open REAL, high REAL,
            low REAL, close REAL, volumen REAL);
        CREATE TABLE IF NOT EXISTS symbole (paar TEXT PRIMARY KEY, symbol TEXT, art TEXT,
            nachfolger TEXT, grund TEXT, erster_monat TEXT, letzter_monat TEXT,
            echtes_ende TEXT, zombie_stunden INTEGER);
        CREATE TABLE IF NOT EXISTS _geladen (symbol TEXT NOT NULL, reihe TEXT NOT NULL,
            monat TEXT NOT NULL, status TEXT NOT NULL, anzahl INTEGER, geholt_am TEXT,
            PRIMARY KEY (symbol, reihe, monat));
        CREATE TABLE IF NOT EXISTS _herkunft (schluessel TEXT PRIMARY KEY, wert TEXT);
        CREATE TABLE IF NOT EXISTS _nur_messbasis (hinweis TEXT);
    """)
    c.executemany("INSERT OR REPLACE INTO _herkunft VALUES (?,?)", list(HERKUNFT.items()))
    if not c.execute("SELECT COUNT(*) FROM _nur_messbasis").fetchone()[0]:
        c.execute("INSERT INTO _nur_messbasis VALUES ('Messbasis am Desktop, nicht Betrieb')")
    c.commit()
    return c


def einordnung() -> list:
    """-> [(paar, symbol, art, nachfolger, grund, monate)] fuer alle Kandidaten."""
    rec = json.load(open(RECHERCHE, encoding="utf-8"))
    und = json.load(open(UNDERLYING, encoding="utf-8")) if os.path.exists(UNDERLYING) else {}
    s = sqlite3.connect("file:%s?mode=ro" % STUNDEN_DB, uri=True)
    menge = {r[0] for r in s.execute("SELECT DISTINCT symbol FROM stundenkurse")}
    s.close()
    aus = []
    for paar, ms in sorted(rec["kandidaten"].items()):
        basis = paar[:-4]
        typ = (und.get(paar) or [None])[0]
        if typ and typ != "COIN":
            aus.append((paar, basis, "kein_krypto", "", "amtlich: %s" % typ, ms))
        elif basis in KEIN_KRYPTO_HAND:
            aus.append((paar, basis, "kein_krypto", "", KEIN_KRYPTO_HAND[basis], ms))
        elif basis in UMBENENNUNG:
            neu = UMBENENNUNG[basis]
            if neu in menge:
                aus.append((paar, neu, "vorgeschichte", neu,
                            "Umbenennung, Nachfolger in der Menge", ms))
            else:
                aus.append((paar, basis, "umbenennung", neu,
                            "Nachfolger nicht in der Menge", ms))
        else:
            aus.append((paar, basis, "eingestellt", "", "heute nicht gehandelt", ms))
    return aus


def lade_monat(c, sym, paar, m, erledigt, pause, zaehl, nur=("kurs", "premium", "funding")):
    jetzt = datetime.now(timezone.utc).isoformat(timespec="seconds")
    if "kurs" in nur and (sym, "kurs", m) not in erledigt:
        quelle, zeilen = "spot", None
        try:
            zeilen = hole(URL["spot"].format(p=paar, m=m), pause)
            if zeilen is None:
                quelle = "um"
                zeilen = hole(URL["um"].format(p=paar, m=m), pause)
            status = "ok" if zeilen else "fehlt"
            if zeilen:
                c.executemany("INSERT OR REPLACE INTO stundenkurse VALUES (?,?,?,?,?,?,?,?)",
                              [(sym, stunde(z[0]), float(z[1]), float(z[2]), float(z[3]),
                                float(z[4]), float(z[5]), quelle) for z in zeilen])
                c.executemany("INSERT OR REPLACE INTO fluss VALUES (?,?,?,?,?,?,?,?)",
                              [(sym, stunde(z[0]), quelle, float(z[5]), float(z[9]),
                                float(z[7]), float(z[10]), int(float(z[8]))) for z in zeilen])
        except Exception as exc:                              # noqa: BLE001
            status = "fehler"
            print("  %s kurs %s: %s" % (sym, m, str(exc)[:80]), flush=True)
        c.execute("INSERT OR REPLACE INTO _geladen VALUES (?,?,?,?,?,?)",
                  (sym, "kurs", m, status, len(zeilen or []), jetzt))
        zaehl[status] += 1
    if "premium" in nur and (sym, "premium", m) not in erledigt:
        zeilen = None
        try:
            zeilen = hole(URL["premium"].format(p=paar, m=m), pause)
            status = "ok" if zeilen else "fehlt"
            if zeilen:
                c.executemany("INSERT OR REPLACE INTO premium VALUES (?,?,?,?,?,?)",
                              [(sym, stunde(z[0]), float(z[1]), float(z[2]), float(z[3]),
                                float(z[4])) for z in zeilen])
        except Exception as exc:                              # noqa: BLE001
            status = "fehler"
            print("  %s premium %s: %s" % (sym, m, str(exc)[:80]), flush=True)
        c.execute("INSERT OR REPLACE INTO _geladen VALUES (?,?,?,?,?,?)",
                  (sym, "premium", m, status, len(zeilen or []), jetzt))
        zaehl[status] += 1
    if "funding" in nur and (sym, "funding", m) not in erledigt:
        zeilen = None
        try:
            zeilen = hole(URL_FUNDING.format(p=paar, m=m), pause)
            status = "ok" if zeilen else "fehlt"
            if zeilen:
                je_tag = {}
                for z in zeilen:
                    tag = stunde(z[0])[:10]
                    je_tag[tag] = je_tag.get(tag, 0.0) + float(z[-1])
                # jede Monatsdatei traegt nur die Abrechnungen IHRES Monats
                # (auch die um 00:00 am Ersten) - jeder UTC-Tag liegt also
                # vollstaendig in genau einer Datei; ersetzen ist richtig.
                # P1 prueft das gegen funding_historie.db.
                c.executemany("INSERT OR REPLACE INTO funding VALUES (?,?,?)",
                              [(sym, t, v) for t, v in je_tag.items()])
        except Exception as exc:                              # noqa: BLE001
            status = "fehler"
            print("  %s funding %s: %s" % (sym, m, str(exc)[:80]), flush=True)
        c.execute("INSERT OR REPLACE INTO _geladen VALUES (?,?,?,?,?,?)",
                  (sym, "funding", m, status, len(zeilen or []), jetzt))
        zaehl[status] += 1
    c.commit()


def abschliessen(c) -> None:
    """Zombie-Monate am Reihenende abschneiden, echtes Ende vermerken.

    Dazu die VORGESCHICHTE dort abschneiden, wo der Bestand des Nachfolgers
    beginnt - sonst traegt dieselbe Stunde zwei Kurse, sobald beide Dateien
    zusammen gelesen werden (P4 prueft die Ueberlappung).
    """
    s = sqlite3.connect("file:%s?mode=ro" % STUNDEN_DB, uri=True)
    for sym, in c.execute("SELECT DISTINCT symbol FROM symbole WHERE art='vorgeschichte'").fetchall():
        beginn = s.execute("SELECT MIN(stunde) FROM stundenkurse WHERE symbol=?", (sym,)).fetchone()[0]
        if not beginn:
            continue
        n = c.execute("SELECT COUNT(*) FROM stundenkurse WHERE symbol=? AND stunde>=?",
                      (sym, beginn)).fetchone()[0]
        for t in ("stundenkurse", "fluss", "premium"):
            c.execute("DELETE FROM %s WHERE symbol=? AND stunde>=?" % t, (sym, beginn))
        c.execute("DELETE FROM funding WHERE symbol=? AND datum>=?", (sym, beginn[:10]))
        if n:
            print("  %-10s Vorgeschichte ab %s abgeschnitten (%d Stunden, Bestand beginnt)" % (sym, beginn, n))
    s.close()
    # ⚠️ ZOMBIE AUCH MITTEN IN DER REIHE (28.09., gefunden im Vergleich): nach
    # dem Ende des Spot-Handels liefert die Terminmarkt-Kerze oft schon einen
    # eingefrorenen Kurs mit Volumen 0 (A2Z, AERGO ...). Jeder Lauf >= 72 h mit
    # Volumen 0 UND unveraendertem Kurs wird entfernt - er wuerde sonst
    # scheinbare Ruhe messen. Die entstehende Luecke schliesst die Messung aus.
    for (sym,) in c.execute("SELECT DISTINCT symbol FROM stundenkurse").fetchall():
        rows = c.execute("SELECT stunde, close, volumen FROM stundenkurse WHERE symbol=? "
                         "ORDER BY stunde", (sym,)).fetchall()
        weg, i = [], 1
        while i < len(rows):
            if (rows[i][2] or 0) == 0 and rows[i][1] == rows[i - 1][1]:
                j = i
                while j < len(rows) and (rows[j][2] or 0) == 0 and rows[j][1] == rows[i - 1][1]:
                    j += 1
                if j - i >= ZOMBIE_H and j < len(rows):
                    weg.append((rows[i][0], rows[j - 1][0], j - i))
                i = j
            else:
                i += 1
        for von, bis, k in weg:
            for t in ("stundenkurse", "fluss", "premium"):
                c.execute("DELETE FROM %s WHERE symbol=? AND stunde BETWEEN ? AND ?" % t,
                          (sym, von, bis))
            print("  %-10s Zombie INNEN entfernt: %5d Stunden %s bis %s" % (sym, k, von, bis))
    c.commit()
    # und jedes durch Luecken abgetrennte STUECK ganz ohne Volumen (die erste
    # eingefrorene Stunde nach dem Ende des Spot-Handels, A2Z/IDEX/SXP ...)
    import numpy as _np
    for (sym,) in c.execute("SELECT DISTINCT symbol FROM stundenkurse").fetchall():
        rows = c.execute("SELECT stunde, volumen FROM stundenkurse WHERE symbol=? ORDER BY stunde",
                         (sym,)).fetchall()
        if not rows:
            continue
        h = _np.array([r[0].replace(" ", "T") for r in rows], "datetime64[h]")
        v = _np.array([r[1] or 0 for r in rows], float)
        grenzen = [0] + list(_np.flatnonzero(_np.diff(h).astype(int) > 1) + 1) + [len(rows)]
        for a0, b0 in zip(grenzen[:-1], grenzen[1:]):
            if v[a0:b0].sum() == 0:
                for t in ("stundenkurse", "fluss", "premium"):
                    c.execute("DELETE FROM %s WHERE symbol=? AND stunde BETWEEN ? AND ?" % t,
                              (sym, rows[a0][0], rows[b0 - 1][0]))
                print("  %-10s Stueck ohne Volumen entfernt: %d Stunden ab %s" % (sym, b0 - a0, rows[a0][0]))
    c.commit()
    for (sym,) in c.execute("SELECT DISTINCT symbol FROM stundenkurse").fetchall():
        rows = c.execute("SELECT stunde, close, volumen FROM stundenkurse WHERE symbol=? "
                         "ORDER BY stunde", (sym,)).fetchall()
        k = len(rows)
        while k > 1 and (rows[k - 1][2] or 0) == 0 and rows[k - 1][1] == rows[k - 2][1]:
            k -= 1
        lauf = len(rows) - k
        if lauf >= ZOMBIE_H:
            grenze = rows[k][0]
            for t in ("stundenkurse", "fluss"):
                c.execute("DELETE FROM %s WHERE symbol=? AND stunde>=?" % t, (sym, grenze))
            c.execute("DELETE FROM premium WHERE symbol=? AND stunde>=?", (sym, grenze))
            c.execute("DELETE FROM funding WHERE symbol=? AND datum>?", (sym, grenze[:10]))
        ende = rows[k - 1][0] if rows else None
        c.execute("UPDATE symbole SET echtes_ende=?, zombie_stunden=? WHERE symbol=? "
                  "AND art IN ('eingestellt','vorgeschichte')",
                  (ende, lauf if lauf >= ZOMBIE_H else 0, sym))
        if lauf >= ZOMBIE_H:
            print("  %-10s Zombie abgeschnitten: %5d Stunden ab %s" % (sym, lauf, rows[k][0]))
    c.commit()


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:                                         # noqa: BLE001
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=VORGABE_DB)
    ap.add_argument("--symbole", default="", help="Basisnamen, z. B. WAVES,FTT (Probelauf)")
    ap.add_argument("--teil", default="", help="i/N fuer parallele Arbeiter, je eigene --db")
    ap.add_argument("--pause", type=float, default=0.3)
    ap.add_argument("--btc", action="store_true", help="BTC 2021-12 bis 2023-08 und BTCDOM 2021-12 bis 2022-12")
    ap.add_argument("--zusammen", nargs="*", default=None)
    ap.add_argument("--abschliessen", action="store_true")
    ap.add_argument("--kontrolle", default="",
                    help="heute gehandelte Symbole in eine EIGENE --db laden (Pruefung P1)")
    ap.add_argument("--von", default=FENSTER[0])
    ap.add_argument("--bis", default=FENSTER[1])
    a = ap.parse_args()

    if a.zusammen is not None:
        c = lege_an(a.db)
        for teil in a.zusammen:
            c.execute("ATTACH DATABASE ? AS t", (os.path.abspath(teil),))
            for tab in ("stundenkurse", "fluss", "premium", "funding", "btcdom", "symbole"):
                if c.execute("SELECT COUNT(*) FROM t.sqlite_master WHERE name=?", (tab,)).fetchone()[0]:
                    c.execute("INSERT OR IGNORE INTO %s SELECT * FROM t.%s" % (tab, tab))
            c.execute("INSERT OR REPLACE INTO _geladen SELECT * FROM t._geladen")
            c.commit()
            c.execute("DETACH DATABASE t")
            print("  zusammengefuehrt: %s" % teil)
        c.close()
        return 0
    if a.abschliessen:
        c = lege_an(a.db)
        abschliessen(c)
        c.close()
        return 0

    c = lege_an(a.db)
    erledigt = {(r[0], r[1], r[2]) for r in c.execute(
        "SELECT symbol, reihe, monat FROM _geladen WHERE status IN ('ok','fehlt')")}
    zaehl = {"ok": 0, "fehlt": 0, "fehler": 0}
    t0 = time.time()

    if a.kontrolle:
        for sym in [x.strip().upper() for x in a.kontrolle.split(",") if x.strip()]:
            for m in monate(a.von, a.bis):
                lade_monat(c, sym, sym + "USDT", m, erledigt, a.pause, zaehl)
            print("  Kontrolle %s fertig" % sym, flush=True)
        c.close()
        return 0

    if a.btc:
        for m in monate("2021-12", "2023-08"):
            lade_monat(c, "BTC", "BTCUSDT", m, erledigt, a.pause, zaehl)
        for m in monate("2021-12", "2022-12"):
            if ("BTCDOMUSDT", "btcdom", m) in erledigt:
                continue
            zeilen = hole(URL["um"].format(p="BTCDOMUSDT", m=m), a.pause)
            if zeilen:
                c.executemany("INSERT OR REPLACE INTO btcdom VALUES (?,?,?,?,?,?)",
                              [(stunde(z[0]), float(z[1]), float(z[2]), float(z[3]),
                                float(z[4]), float(z[5])) for z in zeilen])
            c.execute("INSERT OR REPLACE INTO _geladen VALUES (?,?,?,?,?,?)",
                      ("BTCDOMUSDT", "btcdom", m, "ok" if zeilen else "fehlt",
                       len(zeilen or []), datetime.now(timezone.utc).isoformat(timespec="seconds")))
            c.commit()
        c.execute("INSERT OR REPLACE INTO symbole VALUES (?,?,?,?,?,?,?,?,?)",
                  ("BTCUSDT", "BTC", "ergaenzung", "", "BTC-Stundenkurse fehlen vor 2023-09",
                   "2021-12", "2023-08", None, 0))
        c.commit()
        print("  BTC fertig · ok %d · fehlt %d · Fehler %d" % (zaehl["ok"], zaehl["fehlt"], zaehl["fehler"]))
        c.close()
        return 0

    liste = einordnung()
    c.executemany("INSERT OR REPLACE INTO symbole VALUES (?,?,?,?,?,?,?,?,?)",
                  [(p, s, art, n, g, ms[0], ms[-1], None, None) for p, s, art, n, g, ms in liste])
    c.commit()
    laden = [x for x in liste if x[2] in ("eingestellt", "vorgeschichte")]
    if a.symbole:
        wahl = {x.strip().upper() for x in a.symbole.split(",") if x.strip()}
        laden = [x for x in laden if x[0][:-4] in wahl]
    if a.teil:
        i_, n_ = map(int, a.teil.split("/"))
        laden = laden[i_::n_]
    print("Eingestellte: %d Paare -> %s (Pause %.1f s) · Einordnung: %s" % (
        len(laden), a.db, a.pause,
        {k: sum(x[2] == k for x in liste) for k in ("eingestellt", "vorgeschichte",
                                                  "umbenennung", "kein_krypto")}), flush=True)
    for i, (paar, sym, art, _n, _g, ms) in enumerate(laden, 1):
        for m in ms:
            lade_monat(c, sym, paar, m, erledigt, a.pause, zaehl)
        print("  [%3d/%3d] %-12s -> %-8s %-13s %2d Monate · ok %d · fehlt %d · Fehler %d · %.1f Min"
              % (i, len(laden), paar, sym, art, len(ms), zaehl["ok"], zaehl["fehlt"],
                 zaehl["fehler"], (time.time() - t0) / 60), flush=True)
    c.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
