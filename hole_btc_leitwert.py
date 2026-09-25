# -*- coding: utf-8 -*-
"""BTC als LEITWERT - die Marktreihe, die der Messbasis fehlt

**Nutzerhinweis 25.09.2026, woertlich:**

    *"BTC kann nicht der Zufall sein sondern die Ursache - der komplette
    Kryptomarkt haengt vom steigen oder fallen von btc ab. Viele Werte
    laufen mit btc mit oder reagieren."*

═══════════════════════════════════════════════════════════════════════
 WARUM DIESE DATEI UEBERHAUPT GEBRAUCHT WIRD
═══════════════════════════════════════════════════════════════════════

Gemessen am 25.09.2026 in `data/stundenkurse.db`:

    BTC                       26.872 Stunden, ab 2023-09-01
    ETH, ADA, 1INCH, ALGO ..  42.000 Stunden, ab 2021-12-01
    52 von 116 Symbolen       beginnen vor 2023-09

⚠️⚠️⚠️ **Der Leitwert des Marktes hat die kuerzeste relevante Reihe** - 21
Monate weniger als die Werte, die er laut Nutzerhinweis treibt. Folge: der
`btc_trend`-Test in Schritt 3 lief auf 62 % der Zeit, und die fehlenden
38 % enthalten das Jahr 2022 mit `E[R]` = -0,0430, das schlechteste im
Fenster. Der Test war zu schwach, nicht das Merkmal.

**Die Ursache liegt eine Ebene tiefer:** auch im Terminmarkt beginnt BTC
erst 2023-09-01 (26.270 gegen 41.678 Stunden bei ADA/ETH), und
`hole_stundenkurse.symbole_und_spanne()` leitet die Spanne je Symbol
DARAUS ab - mit der Begruendung *"Ein Kurs ohne Merkmal traegt keinen
Beitrag."*

⭐ **Und genau diese Begruendung greift hier nicht.** Sie ist richtig fuer
ASSET-Beitraege: ein Altcoin ohne Terminmarkt-Merkmale ist wertlos. Fuer
BTC als MARKTINDIKATOR gilt sie nicht - dafuer braucht es nur den
KURSVERLAUF, keine Terminmarkt-Merkmale.

⚠️⚠️ **Und ein zweiter Mangel, der dabei auffiel:** die Wiederaufnahme in
`hole_stundenkurse.py` setzt bei `MAX(stunde)` an, also am ENDE. Ein
Symbol, dessen Quellspanne sich nach HINTEN erweitert, wird nie
nachgeholt - die Luecke davor bleibt dauerhaft und still. Dieses Werkzeug
ergaenzt deshalb in BEIDE Richtungen.

═══════════════════════════════════════════════════════════════════════
 ⚠️ WARUM EINE EIGENE DATEI UND NICHT `stundenkurse.db`
═══════════════════════════════════════════════════════════════════════

**Nutzerentscheidung 25.09.2026.** BTC ist in `stundenkurse.db` ein
HANDELBARES SYMBOL. Wuerde man es dort um 21 Monate verlaengern, aenderten
sich die Ankermengen der Befunde 2.597 und 2.598 - und beide waeren nicht
mehr reproduzierbar (R-R11 verlangt Reproduktion vor Widerruf).

➤ Der Leitwert ist eine ANDERE Groesse als das handelbare Symbol, auch
wenn es dieselben Kerzen sind. Er bekommt deshalb eine eigene Datei, und
die Messbasis bleibt unberuehrt.

⚠️ NUR DIESE DATEI WIRD GESCHRIEBEN. `stundenkurse.db`,
`terminmarkt_historie.db` und `tradinginfotool.db` werden nicht angefasst.

    python hole_btc_leitwert.py [--pruefen] [--ab 2021-01-01]
"""
from __future__ import annotations

import os
import sqlite3
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hole_stundenkurse import hole, _ms, _stunde        # noqa: E402

ZIEL = os.path.join("data", "btc_leitwert.db")
#: Vorlauf vor dem Beginn der Messbasis (2021-12-01), damit die
#: 30-Tage-Mittel dort schon belegt sind - sonst beginnt `btc_trend` erst
#: 30 Tage spaeter als die Anker.
AB_VORGABE = "2021-09-01 00:00"
SYMBOL = "BTC"


def lege_an(pfad: str) -> sqlite3.Connection:
    neu = not os.path.exists(pfad)
    verzeichnis = os.path.dirname(pfad)
    if verzeichnis and not os.path.isdir(verzeichnis):
        os.makedirs(verzeichnis)
    c = sqlite3.connect(pfad)
    c.execute("""CREATE TABLE IF NOT EXISTS leitwert (
                   symbol TEXT NOT NULL, stunde TEXT NOT NULL,
                   open REAL, high REAL, low REAL, close REAL, volumen REAL,
                   PRIMARY KEY (symbol, stunde))""")
    # ⚠️ ZWEI Marken. Die erste wie bei den anderen Messbasen, die zweite
    # ist neu und wichtig: diese Reihe ist KEIN handelbares Symbol. Wer
    # sie als Asset in eine Beitragsmessung nimmt, misst BTC zweimal.
    c.execute("CREATE TABLE IF NOT EXISTS _nur_messbasis (hinweis TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS _nur_leitwert (hinweis TEXT)")
    for tab, text in (
            ("_nur_messbasis",
             "Messbasis - gehoert NICHT aufs Notebook (wie messdaten.db)."),
            ("_nur_leitwert",
             "MARKTINDIKATOR, KEIN handelbares Symbol. Angelegt 2026-09-25 "
             "auf Nutzerentscheidung, weil BTC in stundenkurse.db erst ab "
             "2023-09 vorliegt. NICHT als Asset in eine Beitragsmessung "
             "geben - sonst wird BTC zweimal gezaehlt.")):
        c.execute("DELETE FROM %s" % tab)
        c.execute("INSERT INTO %s VALUES (?)" % tab, (text,))
    c.commit()
    if neu:
        print("  angelegt: %s" % pfad)
    return c


def main() -> int:
    nur_rechnen = "--pruefen" in sys.argv
    ab = AB_VORGABE
    if "--ab" in sys.argv:
        ab = sys.argv[sys.argv.index("--ab") + 1]
        if len(ab) == 10:
            ab += " 00:00"

    print("=" * 84)
    print("BTC ALS LEITWERT - die Marktreihe, die der Messbasis fehlt")
    print("=" * 84)
    print("  Ziel: %s (eigene Datei - die Messbasis bleibt unberuehrt)" % ZIEL)
    print("  Ab:   %s" % ab)
    print("  ⚠️ Nutzerhinweis: BTC ist nicht der Zufall, sondern die URSACHE")
    print("     - der Kryptomarkt haengt am Steigen und Fallen von BTC.")

    # ── was fehlt? In BEIDE Richtungen, nicht nur vorwaerts ───────────
    vorhanden = (0, None, None)
    if os.path.exists(ZIEL):
        c = sqlite3.connect("file:%s?mode=ro" % ZIEL, uri=True)
        try:
            vorhanden = c.execute(
                "SELECT COUNT(*), MIN(stunde), MAX(stunde) FROM leitwert "
                "WHERE symbol=?", (SYMBOL,)).fetchone()
        except sqlite3.OperationalError:
            pass
        c.close()
    n0, lo, hi = vorhanden
    print("  Vorhanden: %s Stunden%s"
          % (f"{n0:,}".replace(",", "."),
             " (%s bis %s)" % (lo, hi) if lo else ""))

    jetzt_ms = int(time.time() * 1000)
    luecken = []
    if not n0:
        luecken.append((_ms(ab), jetzt_ms, "alles"))
    else:
        # ⭐ RUECKWAERTS - genau das, was `hole_stundenkurse.py` nie tut
        if _ms(ab) < _ms(lo):
            luecken.append((_ms(ab), _ms(lo), "rueckwaerts"))
        # ⚠️ AB `hi` selbst, nicht ab hi+1: die letzte vorhandene Kerze
        # war beim Laden moeglicherweise noch OFFEN. Gemessen an der
        # eigenen Datei: Volumenquote der letzten Stunde 0,086 - sie war
        # beim Holen wenige Minuten alt. Derselbe Fehler, den dieses
        # Werkzeug in `hole_stundenkurse.py` aufgedeckt hat, war hier
        # nachgebaut.
        if _ms(hi) < jetzt_ms:
            luecken.append((_ms(hi), jetzt_ms, "vorwaerts"))
    if not luecken:
        print("  ✔ nichts zu holen - die Reihe ist vollstaendig.")
        return 0
    for von, bis, art in luecken:
        print("    %-12s %d Stunden zu holen"
              % (art, (bis - von) // 3_600_000))
    if nur_rechnen:
        print("\n  --pruefen: nichts geholt.")
        return 0

    c = lege_an(ZIEL)
    t0, geholt = time.time(), 0
    for von, bis, art in luecken:
        try:
            k = hole(SYMBOL, von, bis)
        except Exception as exc:                            # noqa: BLE001
            print("  ⚠️ %s fehlgeschlagen: %s" % (art, str(exc)[:80]))
            continue
        if k:
            c.executemany(
                # ⚠️ REPLACE, damit eine zuvor offene Kerze ueberschrieben wird.
                "INSERT OR REPLACE INTO leitwert VALUES (?,?,?,?,?,?,?)",
                [(SYMBOL, _stunde(x[0]), float(x[1]), float(x[2]),
                  float(x[3]), float(x[4]), float(x[5])) for x in k])
            c.commit()
            geholt += len(k)
            print("    %-12s %s Kerzen" % (art,
                                           f"{len(k):,}".replace(",", ".")))

    n, lo, hi = c.execute(
        "SELECT COUNT(*), MIN(stunde), MAX(stunde) FROM leitwert "
        "WHERE symbol=?", (SYMBOL,)).fetchone()
    # ── Abnahmeprobe: sind es LUECKENLOSE Stunden? ────────────────────
    monate = c.execute("SELECT COUNT(DISTINCT substr(stunde,1,7)) "
                       "FROM leitwert WHERE symbol=?", (SYMBOL,)).fetchone()[0]
    c.close()
    soll = (_ms(hi) - _ms(lo)) // 3_600_000 + 1 if lo else 0
    print()
    print("  FERTIG: %s Stunden · %s bis %s · %d Monate · %.1f MB"
          % (f"{n:,}".replace(",", "."), lo, hi, monate,
             os.path.getsize(ZIEL) / 1e6))
    print("  ⭐ Abnahmeprobe: %s von %s Stunden der Spanne belegt (%.2f %%) %s"
          % (f"{n:,}".replace(",", "."), f"{soll:,}".replace(",", "."),
             100.0 * n / max(1, soll),
             "✔ lueckenlos" if n >= 0.999 * soll
             else "⚠️ LUECKEN - vor der Messung klaeren"))
    print("  Dauer %.1f Minuten · %s Kerzen geholt"
          % ((time.time() - t0) / 60, f"{geholt:,}".replace(",", ".")))
    print()
    print("  ⚠️ MARKTINDIKATOR, KEIN handelbares Symbol (Marke")
    print("     `_nur_leitwert`). Nicht als Asset in eine Beitragsmessung")
    print("     geben - sonst wird BTC zweimal gezaehlt.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
