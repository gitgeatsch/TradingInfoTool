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
    python hole_markpreis.py --sperre                                         # andere Instrumente sperren
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


SPERRE_GRENZE = 0.01


def spot_quellen() -> list:
    """Die Spot-Stundenkurse, gegen die gemessen wird: Bestand und Eingestellte."""
    q = [STUNDEN_DB]
    if os.path.exists(EINGESTELLT_DB):
        q.append(EINGESTELLT_DB)
    return q


def sperre(pfad: str) -> int:
    """Sperrt Symbol-Monate, in denen der Markpreis ein ANDERES Instrument ist.

    Gemessen 28.09. abends: unter dem Namen des Vorgaengers laeuft im
    Terminmarkt-Archiv ein anderer Kontrakt weiter, waehrend der Spot schon das
    neue Token ist - A <- EOSUSDT (11-54 %), KAIA <- KLAYUSDT (16-40 %),
    S <- FTMUSDT (25-43 %), RENDER <- RNDRUSDT in der Uebergangszeit (bis 12 %).
    Die Verteilung der Monatsmediane |Markpreis/Spot - 1| hat eine LUECKE: kein
    Monat liegt zwischen 0,53 % und 1,15 %. Darunter liegt der Aufschlag, darueber
    ein anderes Instrument -> Grenze 1 % je Monat (SPERRE_GRENZE).
    Schreibt NUR die Tabelle `_abweichung` in die eigene Markpreis-Datei; ein
    Monat ohne Spot-Vergleich (< 100 gemeinsame Stunden) wird ebenfalls gesperrt -
    ungeprueft ist nicht gueltig."""
    c = lege_an(pfad)                     # derselbe Schutz wie beim Laden
    c.execute("DROP TABLE IF EXISTS _abweichung")
    c.execute("CREATE TABLE _abweichung (symbol TEXT, monat TEXT, stunden INTEGER, "
              "median_abw REAL, gesperrt INTEGER, grund TEXT, PRIMARY KEY (symbol, monat))")
    spots = [sqlite3.connect("file:%s?mode=ro" % q, uri=True) for q in spot_quellen()]
    zeilen = []
    for (sym,) in c.execute("SELECT DISTINCT symbol FROM markpreis").fetchall():
        sp = {}
        for s in spots:
            for st_, cl in s.execute("SELECT stunde, close FROM stundenkurse WHERE symbol=?", (sym,)):
                if cl:
                    sp.setdefault(st_, cl)
        je = {}
        for st_, cl in c.execute("SELECT stunde, close / faktor FROM markpreis WHERE symbol=?", (sym,)):
            je.setdefault(st_[:7], []).append(abs(cl / sp[st_] - 1) if st_ in sp else None)
        for monat, v in je.items():
            w = sorted(x for x in v if x is not None)
            if len(w) < 100:
                zeilen.append((sym, monat, len(w), None, 1, "ohne Spot-Vergleich"))
            else:
                med = w[len(w) // 2]
                zeilen.append((sym, monat, len(w), med, int(med > SPERRE_GRENZE),
                               "anderes Instrument" if med > SPERRE_GRENZE else ""))
    c.executemany("INSERT INTO _abweichung VALUES (?,?,?,?,?,?)", zeilen)
    c.commit()
    g = [z for z in zeilen if z[4]]
    print("SPERRE Grenze %.1f %% je Monat · Symbol-Monate %d · gesperrt %d (anderes Instrument %d, ohne Spot-Vergleich %d)" % (
        100 * SPERRE_GRENZE, len(zeilen), len(g), sum(1 for z in g if z[3] is not None),
        sum(1 for z in g if z[3] is None)))
    je_sym = {}
    for z in g:
        if z[3] is not None:
            je_sym.setdefault(z[0], []).append(z[1])
    for sym, ms in sorted(je_sym.items()):
        print("   %-8s %2d Monate %s bis %s" % (sym, len(ms), min(ms), max(ms)))
    return 0


def kontrolle(pfad: str) -> int:
    """Pruefungen des geladenen Markpreises gegen den Spot (Bestand, stundenkurse).

    ⚠️ 28.09. abends neu gefasst - die erste Fassung verglich das Markpreis-Tief
    mit dem Spot-Tief ALS NIVEAU. Der Markpreis liegt aber um einen kleinen,
    gleichbleibenden Aufschlag neben dem Spot (gemessen rund -0,04 %); bei BTC lag
    das Markpreis-Tief darum in 96,6 % der Stunden UNTER dem Spot-Tief. Gemessen
    war der Aufschlag, nicht der Docht. Zudem waehlte sie DOGE, das gar nicht in
    der Messbasis liegt. Jetzt:

    P1  Abdeckung je Quelle und Ladestatus
    P2  Niveau: Median |Markpreis-Schluss / Spot-Schluss - 1| je Symbol; ⛔ wenn
        nicht mindestens 95 % der Symbole unter 0,2 % liegen
    P2b Zeitlage: die Abweichung ist ohne Versatz kleiner als bei +-1 Stunde;
        ⛔ wenn nicht in mindestens 95 % der Symbole
    P3  Docht JE REIHE - Tief gegen den Schluss der Vorstunde DERSELBEN Reihe
        (der Aufschlag kuerzt sich heraus); ⛔ wenn der Markpreis-Docht nicht im
        Median ueber die Symbole in mehr als der Haelfte der Stunden flacher ist
        und nicht bei den tiefsten 1 % der Spot-Dochte im Mittel flacher
    Symbole: ALLE, die in beiden Dateien liegen (abgeleitet, nicht aufgezaehlt);
    Zeitraum fest 2025-01 bis 2025-06."""
    c = sqlite3.connect("file:%s?mode=ro" % pfad, uri=True)
    s = sqlite3.connect("file:%s?mode=ro" % STUNDEN_DB, uri=True)
    n = c.execute("SELECT COUNT(DISTINCT symbol), COUNT(*) FROM markpreis").fetchone()
    st = dict(c.execute("SELECT status, COUNT(*) FROM _geladen GROUP BY status").fetchall())
    print("P1 Symbole mit Markpreis %d · Stunden %d · Monate %s" % (n[0], n[1], st))
    fak = c.execute("SELECT symbol, faktor FROM markpreis WHERE faktor <> 1 GROUP BY symbol").fetchall()
    print("   Symbole mit Faktor 1000 (Spot-Name ohne 1000): %s" % (", ".join(r[0] for r in fak) or "keine"))
    if not c.execute("SELECT 1 FROM sqlite_master WHERE name='_abweichung'").fetchone():
        print("⛔ Tabelle _abweichung fehlt - erst  python hole_markpreis.py --sperre"); return 1
    gs = c.execute("SELECT COUNT(*), SUM(median_abw IS NOT NULL), COUNT(DISTINCT symbol) "
                   "FROM _abweichung WHERE gesperrt=1").fetchone()
    print("P0  gesperrte Symbol-Monate %d (anderes Instrument %d) in %d Symbolen - "
          "P2 bis P3 laufen auf dem Rest" % (gs[0], gs[1] or 0, gs[2]))
    gesperrt = {(r[0], r[1]) for r in c.execute("SELECT symbol, monat FROM _abweichung WHERE gesperrt=1")}
    von, bis = "2025-01-01", "2025-07-01"
    beide = sorted(set(r[0] for r in c.execute("SELECT DISTINCT symbol FROM markpreis"))
                   & set(r[0] for r in s.execute("SELECT DISTINCT symbol FROM stundenkurse")))
    niveau, lage_ok, flacher, tief_m, tief_s, basis, aus = [], 0, [], [], [], [], []
    for sym in beide:
        mp = c.execute("SELECT stunde, close / faktor, low / faktor FROM markpreis WHERE symbol=? "
                       "AND stunde >= ? AND stunde < ? ORDER BY stunde", (sym, von, bis)).fetchall()
        mp = [r for r in mp if (sym, r[0][:7]) not in gesperrt]
        sp = {r[0]: (r[1], r[2]) for r in s.execute(
            "SELECT stunde, close, low FROM stundenkurse WHERE symbol=? AND stunde >= ? AND stunde < ?",
            (sym, von, bis))}
        k = [r for r in mp if r[0] in sp and sp[r[0]][0]]
        if len(k) < 500:
            continue
        d = sorted(abs(r[1] / sp[r[0]][0] - 1) for r in k)
        niveau.append((d[len(d) // 2], sym))
        basis.append(sorted(r[1] / sp[r[0]][0] - 1 for r in k)[len(k) // 2])
        # P2b: Versatz um eine Stunde in beide Richtungen
        spl = [sp[r[0]][0] for r in k]
        mpl = [r[1] for r in k]
        def med(xs):
            xs = sorted(xs); return xs[len(xs) // 2]
        m0 = med(abs(a / b - 1) for a, b in zip(mpl, spl))
        mv = med(abs(a / b - 1) for a, b in zip(mpl[1:], spl[:-1]))
        mn = med(abs(a / b - 1) for a, b in zip(mpl[:-1], spl[1:]))
        lage_ok += m0 < min(mv, mn)
        # P3: Docht je Reihe gegen den Schluss der Vorstunde derselben Reihe
        dm, ds = [], []
        for (t0, c0, _), (t1, c1, l1) in zip(mp, mp[1:]):
            if t0 in sp and t1 in sp and c0 and sp[t0][0]:
                dm.append(1 - l1 / c0); ds.append(1 - sp[t1][1] / sp[t0][0])
        if len(dm) < 500:
            continue
        flacher.append(sum(a <= b for a, b in zip(dm, ds)) / len(dm))
        q = sorted(ds)[int(0.99 * len(ds))]
        paare = [(a, b) for a, b in zip(dm, ds) if b >= q]
        tief_m.append(sum(a for a, _ in paare) / len(paare)); tief_s.append(sum(b for _, b in paare) / len(paare))
        if tief_m[-1] > tief_s[-1]:
            aus.append(sym)
    z = len(niveau)
    if not z:
        print("⛔ keine gemeinsamen Symbole im Zeitraum"); return 1
    unter = sum(1 for x, _ in niveau if x < 0.002)
    niveau.sort()
    print("   Zeitraum %s bis %s · Symbole in beiden Dateien %d, davon mit >= 500 Stunden %d" % (von, bis, len(beide), z))
    print("P2  Niveau: Median |Markpreis/Spot - 1| unter 0,2 %% in %d von %d (%.1f %%) · Mitte %.4f %% · groesste: %s" % (
        unter, z, 100 * unter / z, 100 * niveau[z // 2][0],
        ", ".join("%s %.3f %%" % (sy, 100 * x) for x, sy in niveau[-3:])))
    print("    Aufschlag Markpreis gegen Spot (Median ueber die Symbole) %+.4f %%" % (100 * sorted(basis)[len(basis) // 2]))
    print("P2b Zeitlage: ohne Versatz naeher als bei +-1 h in %d von %d (%.1f %%)" % (lage_ok, z, 100 * lage_ok / z))
    fl = sorted(flacher)
    print("P3  Docht je Reihe: Markpreis flacher in (Median ueber %d Symbole) %.1f %% der Stunden · "
          "tiefste 1 %%: Markpreis %.3f %% gegen Spot %.3f %% (Mittel) · Markpreis dort tiefer bei: %s" % (
              len(fl), 100 * fl[len(fl) // 2], 100 * sum(tief_m) / len(tief_m), 100 * sum(tief_s) / len(tief_s),
              ", ".join(aus) or "keinem"))
    ok = (unter / z >= 0.95 and lage_ok / z >= 0.95 and fl[len(fl) // 2] > 0.5
          and sum(tief_m) < sum(tief_s))
    print("PRUEFUNG %s (P2 >= 95 %%, P2b >= 95 %%, P3 Median > 50 %% und tiefste 1 %% flacher)" % (
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
    ap.add_argument("--sperre", action="store_true")
    a = ap.parse_args()
    if a.sperre:
        return sperre(a.db)
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
