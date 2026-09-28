# -*- coding: utf-8 -*-
"""Laedt den Binance-MARKPREIS (Terminmarkt, stuendlich) aus dem Archiv - fuer K6/K7.

**28.09.2026.** Voranalyse `Basisinfos/Voranalyse_K6_Hebelstufe_28_09.md`, H9
(Nutzer: *H9 freigegeben*). K7 abgestimmt: *Liquidationskurs = Binance-
Markpreis als Massstab, das Spot-Tief daneben als Vergleich* - das Spot-Tief
zaehlt Dochte (STX -70 % in einer Stunde, 2.667).

WAS   je Symbol und Monat `futures/um/monthly/markPriceKlines/<PAAR>/1h` aus
      data.binance.vision -> Tabelle `markpreis` (open/high/low/close je
      Stunde, stunde = BEGINN der Stunde, UTC - wie stundenkurse)
WER   der Bestand (data/stundenkurse.db) und die Eingestellten samt Vorgeschichte
      (data/eingestellt_historie.db, Tabelle symbole: eingestellt/vorgeschichte)
NAME  ⚠️ manche Spot-Symbole heissen im Terminmarkt anders: PEPE -> 1000PEPEUSDT
      (Kurs x 1000). Versucht wird <SYM>USDT, dann 1000<SYM>USDT; der Faktor
      steht in `faktor` (Kurs im Archiv / Faktor = Kurs je 1 Stueck). Fuer den
      RELATIVEN Rueckgang ist er gleichgueltig, gespeichert wird er trotzdem.

SCHUTZ: schreibt NUR in die eigene Datei (Vorgabe data/markpreis_historie.db),
verweigert tradinginfotool.db und jede bestehende Messbasis. Pause je Datei
0,3 s, bei 418/429 eine Minute (die Abruffunktion aus hole_richtungsdaten).
Wiederaufnahme ueber `_geladen`.

    python hole_markpreis.py --symbole ETH,PEPE --db data/_teile/mp_probe.db   # Probelauf
    python hole_markpreis.py --teil 0/2 --db data/_teile/mp_0.db             # Arbeiter
    python hole_markpreis.py --zusammen data/_teile/mp_*.db
    python hole_markpreis.py --kontrolle                                      # Pruefungen
"""
from __future__ import annotations

import argparse
import glob
import os
import sqlite3
import sys
from datetime import datetime, timezone

from hole_richtungsdaten import BASIS, hole, monate, stunde

HIER = os.path.dirname(os.path.abspath(__file__))
VORGABE_DB = os.path.join(HIER, "data", "markpreis_historie.db")
STUNDEN_DB = os.path.join(HIER, "data", "stundenkurse.db")
EINGESTELLT_DB = os.path.join(HIER, "data", "eingestellt_historie.db")
URL_MP = BASIS + "/futures/um/monthly/markPriceKlines/{p}/1h/{p}-1h-{m}.zip"
FENSTER = ("2021-12", "2026-08")
HERKUNFT = {
    "kennzeichen": "MESSBASIS MARKPREIS - Binance-Terminmarkt markPriceKlines 1h, Bestand und Eingestellte",
    "zweck": "Liquidationskurs fuer K6/K7 (Voranalyse K6, H9); das Spot-Tief bleibt der Vergleich",
    "quelle": "data.binance.vision, futures/um/monthly/markPriceKlines/<PAAR>/1h",
    "zeit": "stunde = BEGINN der Stunde, UTC - wie stundenkurse",
    "faktor": "Kurs im Archiv / faktor = Kurs je Stueck (1000er-Kontrakte, z. B. 1000PEPEUSDT)",
    "lader": "hole_markpreis.py",
}


def lege_an(pfad: str) -> sqlite3.Connection:
    name = os.path.basename(pfad).lower()
    if name == "tradinginfotool.db":
        raise SystemExit("⛔ verweigert: %s ist die Produktionsdatei" % pfad)
    for vorhanden in ("stundenkurse.db", "funding_historie.db", "richtung_historie.db",
                      "terminmarkt_historie.db", "messdaten.db", "eingestellt_historie.db"):
        if name == vorhanden:
            raise SystemExit("⛔ verweigert: %s ist eine bestehende Messbasis (R-R11)" % pfad)
    os.makedirs(os.path.dirname(os.path.abspath(pfad)), exist_ok=True)
    c = sqlite3.connect(pfad)
    c.executescript("""
        CREATE TABLE IF NOT EXISTS markpreis (symbol TEXT NOT NULL, stunde TEXT NOT NULL,
            open REAL, high REAL, low REAL, close REAL, paar TEXT, faktor REAL,
            PRIMARY KEY (symbol, stunde));
        CREATE TABLE IF NOT EXISTS _geladen (symbol TEXT NOT NULL, monat TEXT NOT NULL,
            paar TEXT, status TEXT NOT NULL, anzahl INTEGER, geholt_am TEXT,
            PRIMARY KEY (symbol, monat));
        CREATE TABLE IF NOT EXISTS _herkunft (schluessel TEXT PRIMARY KEY, wert TEXT);
        CREATE TABLE IF NOT EXISTS _nur_messbasis (hinweis TEXT);
    """)
    c.executemany("INSERT OR REPLACE INTO _herkunft VALUES (?,?)", list(HERKUNFT.items()))
    if not c.execute("SELECT COUNT(*) FROM _nur_messbasis").fetchone()[0]:
        c.execute("INSERT INTO _nur_messbasis VALUES ('Messbasis am Desktop, nicht Betrieb')")
    c.commit()
    return c


def kandidaten() -> list:
    """-> [(symbol, [paare])] - Bestand und Eingestellte samt Vorgeschichte."""
    s = sqlite3.connect("file:%s?mode=ro" % STUNDEN_DB, uri=True)
    bestand = sorted(r[0] for r in s.execute("SELECT DISTINCT symbol FROM stundenkurse"))
    s.close()
    aus = {sym: ["%sUSDT" % sym] for sym in bestand}
    if os.path.exists(EINGESTELLT_DB):
        e = sqlite3.connect("file:%s?mode=ro" % EINGESTELLT_DB, uri=True)
        for paar, sym, art in e.execute("SELECT paar, symbol, art FROM symbole "
                                        "WHERE art IN ('eingestellt','vorgeschichte')"):
            aus.setdefault(sym, [])
            if paar not in aus[sym]:
                aus[sym].append(paar)
        e.close()
    return sorted(aus.items())


def lade(c, sym, paare, pause, zaehl):
    erledigt = {r[0] for r in c.execute("SELECT monat FROM _geladen WHERE symbol=?", (sym,))}
    jetzt = datetime.now(timezone.utc).isoformat(timespec="seconds")
    # das zuletzt erfolgreiche Paar zuerst - spart Abrufe (Nutzer: nicht zu schnell)
    folge = [(p, f) for paar in paare for p, f in ((paar, 1.0), ("1000" + paar, 1000.0))]
    for m in monate(*FENSTER):
        if m in erledigt:
            continue
        status, zeilen, benutzt, faktor = "fehlt", None, None, 1.0
        try:
            for p, f in folge:
                zeilen = hole(URL_MP.format(p=p, m=m), pause)
                if zeilen:
                    benutzt, faktor = p, f
                    folge.remove((p, f)); folge.insert(0, (p, f))
                    break
            if zeilen:
                status = "ok"
                c.executemany("INSERT OR IGNORE INTO markpreis VALUES (?,?,?,?,?,?,?,?)",
                              [(sym, stunde(z[0]), float(z[1]), float(z[2]), float(z[3]),
                                float(z[4]), benutzt, faktor) for z in zeilen])
        except Exception as exc:                              # noqa: BLE001
            status = "fehler"
            print("  %s %s: %s" % (sym, m, str(exc)[:80]), flush=True)
        c.execute("INSERT OR REPLACE INTO _geladen VALUES (?,?,?,?,?,?)",
                  (sym, m, benutzt, status, len(zeilen or []), jetzt))
        zaehl[status] += 1
    c.commit()


def kontrolle(pfad: str) -> int:
    """P1 Abdeckung je Quelle · P2 Markpreis gegen Spot-Schluss (Median der
    relativen Abweichung je Symbol) · P3 Tief: Markpreis-Tief ueber dem Spot-Tief
    in den meisten Stunden (Markpreis ist geglaettet) · P4 Luecken."""
    c = sqlite3.connect("file:%s?mode=ro" % pfad, uri=True)
    s = sqlite3.connect("file:%s?mode=ro" % STUNDEN_DB, uri=True)
    n = c.execute("SELECT COUNT(DISTINCT symbol), COUNT(*) FROM markpreis").fetchone()
    st = dict(c.execute("SELECT status, COUNT(*) FROM _geladen GROUP BY status").fetchall())
    print("P1 Symbole mit Markpreis %d · Stunden %d · Monate %s" % (n[0], n[1], st))
    fak = c.execute("SELECT symbol, faktor FROM markpreis WHERE faktor <> 1 GROUP BY symbol").fetchall()
    print("   Symbole mit 1000er-Kontrakt: %s" % (", ".join(r[0] for r in fak) or "keine"))
    abw, tief = [], []
    for sym in ("ETH", "SOL", "LINK", "BNB", "DOGE", "AVAX"):
        mp = {r[0]: (r[1], r[2]) for r in c.execute(
            "SELECT stunde, close / faktor, low / faktor FROM markpreis WHERE symbol=? "
            "AND stunde >= '2024-01-01' AND stunde < '2024-07-01'", (sym,))}
        sp = {r[0]: (r[1], r[2]) for r in s.execute(
            "SELECT stunde, close, low FROM stundenkurse WHERE symbol=? "
            "AND stunde >= '2024-01-01' AND stunde < '2024-07-01'", (sym,))}
        k = sorted(set(mp) & set(sp))
        if not k:
            print("P2 %s: keine gemeinsamen Stunden" % sym); continue
        d = sorted(abs(mp[x][0] / sp[x][0] - 1) for x in k)
        t = sum(1 for x in k if mp[x][1] >= sp[x][1]) / len(k)
        abw.append(d[len(d) // 2]); tief.append(t)
        print("P2/P3 %-5s Stunden %5d · Median |Markpreis/Spot - 1| %.4f %% · Markpreis-Tief >= Spot-Tief in %.1f %%" % (
            sym, len(k), 100 * d[len(d) // 2], 100 * t))
    ok = bool(abw) and max(abw) < 0.002 and min(tief) > 0.5
    print("PRUEFUNG %s (Median-Abweichung unter 0,2 %%, Markpreis-Tief meist ueber dem Spot-Tief)" % (
        "✔ bestanden" if ok else "⛔ NICHT bestanden"))
    return 0 if ok else 1


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:                                         # noqa: BLE001
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=VORGABE_DB)
    ap.add_argument("--symbole")
    ap.add_argument("--teil")
    ap.add_argument("--pause", type=float, default=0.3)
    ap.add_argument("--zusammen", nargs="*")
    ap.add_argument("--kontrolle", action="store_true")
    a = ap.parse_args()
    if a.kontrolle:
        return kontrolle(a.db)
    if a.zusammen is not None:
        c = lege_an(a.db)
        for f in sorted(set(x for g in a.zusammen for x in glob.glob(g))):
            q = sqlite3.connect("file:%s?mode=ro" % f, uri=True)
            c.executemany("INSERT OR IGNORE INTO markpreis VALUES (?,?,?,?,?,?,?,?)",
                          q.execute("SELECT * FROM markpreis"))
            c.executemany("INSERT OR REPLACE INTO _geladen VALUES (?,?,?,?,?,?)",
                          q.execute("SELECT * FROM _geladen"))
            q.close()
            print("  zusammengefuehrt: %s" % f)
        c.commit()
        print("markpreis: %d Stunden, %d Symbole" % c.execute(
            "SELECT COUNT(*), COUNT(DISTINCT symbol) FROM markpreis").fetchone())
        return 0
    ks = kandidaten()
    if a.symbole:
        wahl = {x.strip().upper() for x in a.symbole.split(",")}
        ks = [k for k in ks if k[0].upper() in wahl]
    if a.teil:
        i, t = map(int, a.teil.split("/"))
        ks = [k for j, k in enumerate(ks) if j % t == i]
    c = lege_an(a.db)
    zaehl = {"ok": 0, "fehlt": 0, "fehler": 0}
    for j, (sym, paare) in enumerate(ks, 1):
        lade(c, sym, paare, a.pause, zaehl)
        print("[%3d/%3d] %-10s %s" % (j, len(ks), sym, zaehl), flush=True)
    print("FERTIG %s" % zaehl)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
