# -*- coding: utf-8 -*-
"""Korrigiert NUR die letzte, offen gespeicherte Stundenkerze je Symbol

**25.09.2026**, Nutzervorgabe: *"sowohl der Betrieb und in den Messdaten
korrigiert"* · Befund `Basisinfos/Befund_Offene_Stundenkerze_25_09.md`

═══════════════════════════════════════════════════════════════════════
 ⚠️⚠️ WARUM NICHT EINFACH `hole_stundenkurse.py`?
═══════════════════════════════════════════════════════════════════════

Der Lader ist korrigiert (Start bei `MAX(stunde)`, `INSERT OR REPLACE`) und
wuerde die offenen Kerzen mit abschliessen. **Aber er holt ab `MAX(stunde)`
BIS ZUM ENDE der Terminmarkt-Spanne** - also moeglicherweise tausende neue
Kerzen je Symbol.

➤ Das waere eine ganz andere Aenderung: die ANKERMENGE der Befunde 2.597 und
2.598 wuerde sich massiv verschieben, und R-R11 (Reproduktion vor Widerruf)
liesse sich nicht mehr fuehren. Man koennte nicht unterscheiden, ob ein
abweichendes Ergebnis von der Kerzenkorrektur oder von den neuen Daten kommt.

⭐ **Deshalb dieses Werkzeug: es aendert GENAU die letzte Kerze je Symbol und
sonst nichts.** Eine Zeile pro Symbol, 116 insgesamt. Die Aenderung ist damit
klein genug, dass ihre Wirkung VORAB ausrechenbar ist - und genau das prueft
`pruefe_rr11_stundenkerze.py` nach.

⚠️ Das Nachladen neuer Kurse ist eine EIGENE Entscheidung und gehoert nicht
in dieselbe Aenderung.

═══════════════════════════════════════════════════════════════════════
 SICHERUNG
═══════════════════════════════════════════════════════════════════════

Die alten 116 Zeilen werden vor dem Ueberschreiben in eine kleine eigene
Datei geschrieben (`data/kerzen_vor_korrektur_<datum>.db`, wenige KB). Eine
Vollsicherung der 346 MB waere unnoetig - geaendert werden 116 Zeilen, und
nur die muessen rekonstruierbar sein.

═══════════════════════════════════════════════════════════════════════
 DER RIEGEL
═══════════════════════════════════════════════════════════════════════

⚠️⚠️ Am Notebook liegen verkuerzte Fassungen der Messbasen
(`_nur_symbolliste`, 12-16 KB) und Betriebskopien (`_nur_betrieb`). Dieses
Werkzeug BRICHT AB, wenn es eine davon vor sich hat - auf einer Symbolliste
gaebe es keine Kerzen zu korrigieren, und ein Schreibzugriff waere dort ein
Seiteneffekt, den eine Korrektur nicht haben darf.

    python korrigiere_letzte_kerze.py [--pruefen] [--datei <pfad>]
"""
from __future__ import annotations

import os
import shutil
import sqlite3
import sys
import time
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hole_stundenkurse import hole, _ms, _stunde                # noqa: E402

ZIEL = os.path.join("data", "stundenkurse.db")
#: Marken, bei denen abgebrochen wird - eine verkuerzte Datei ist keine
#: Messbasis (registrierte Regel).
VERBOTEN = ("_nur_symbolliste", "_nur_betrieb")


def _riegel(c: sqlite3.Connection, pfad: str) -> None:
    tabs = {r[0] for r in c.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")}
    for marke in VERBOTEN:
        if marke in tabs:
            raise SystemExit(
                "⛔ ABBRUCH: %s tragt die Marke `%s` - das ist eine "
                "verkuerzte Fassung, keine Messbasis. Eine Korrektur darf "
                "dort keinen Seiteneffekt haben." % (pfad, marke))
    if "stundenkurse" not in tabs:
        raise SystemExit("⛔ ABBRUCH: %s hat keine Tabelle `stundenkurse`"
                         % pfad)
    n = c.execute("SELECT COUNT(*) FROM stundenkurse").fetchone()[0]
    if n < 100_000:
        raise SystemExit(
            "⛔ ABBRUCH: nur %d Zeilen in %s - zu wenig fuer die volle "
            "Messbasis. Verkuerzte Datei?" % (n, pfad))


def main() -> int:
    nur_rechnen = "--pruefen" in sys.argv
    pfad = ZIEL
    if "--datei" in sys.argv:
        pfad = sys.argv[sys.argv.index("--datei") + 1]

    print("=" * 92)
    print("KORREKTUR: die letzte, offen gespeicherte Stundenkerze je Symbol")
    print("=" * 92)
    print("  Datei: %s" % pfad)

    c = sqlite3.connect("file:%s?mode=ro" % pfad, uri=True)
    _riegel(c, pfad)
    letzte = c.execute(
        "SELECT symbol, MAX(stunde) FROM stundenkurse GROUP BY symbol"
    ).fetchall()
    alt = {}
    for sym, st in letzte:
        alt[(sym, st)] = c.execute(
            "SELECT open, high, low, close, volumen FROM stundenkurse "
            "WHERE symbol=? AND stunde=?", (sym, st)).fetchone()
    c.close()
    print("  %d Symbole, %d letzte Kerzen zu pruefen" % (len(letzte),
                                                         len(alt)))

    # ⚠️ Nur Kerzen, deren Stunde ABGESCHLOSSEN ist - eine Stunde, die
    # gerade laeuft, waere nach dem Holen wieder offen. Das waere kein
    # Fortschritt, sondern dasselbe Problem mit neuem Datum.
    jetzt_ms = int(time.time() * 1000)
    faellig = [(sym, st) for sym, st in letzte
               if _ms(st) + 3_600_000 <= jetzt_ms]
    laufend = len(letzte) - len(faellig)
    print("  davon abgeschlossen: %d · noch laufend (uebersprungen): %d"
          % (len(faellig), laufend))
    if nur_rechnen:
        print("\n  --pruefen: nichts geaendert.")
        return 0

    # ── Sicherung der 116 alten Zeilen ────────────────────────────────
    tag = datetime.now(timezone.utc).strftime("%Y_%m_%d")
    sich = os.path.join("data", "kerzen_vor_korrektur_%s.db" % tag)
    sc = sqlite3.connect(sich)
    sc.execute("""CREATE TABLE IF NOT EXISTS vorher (
                    symbol TEXT, stunde TEXT, open REAL, high REAL,
                    low REAL, close REAL, volumen REAL,
                    PRIMARY KEY (symbol, stunde))""")
    sc.executemany("INSERT OR REPLACE INTO vorher VALUES (?,?,?,?,?,?,?)",
                   [(s, t) + tuple(v) for (s, t), v in alt.items() if v])
    sc.commit(); sc.close()
    print("  ⭐ Sicherung: %s (%.0f KB, %d Zeilen)"
          % (sich, os.path.getsize(sich) / 1e3, len(alt)))

    # ── korrigieren ───────────────────────────────────────────────────
    w = sqlite3.connect(pfad)
    geaendert, gleich, fehler = 0, 0, []
    t0 = time.time()
    for i, (sym, st) in enumerate(faellig, 1):
        try:
            k = hole(sym, _ms(st), _ms(st) + 3_600_000)
        except Exception as exc:                            # noqa: BLE001
            fehler.append("%s: %s" % (sym, str(exc)[:50]))
            continue
        k = [x for x in k if _stunde(x[0]) == st]
        if not k:
            continue
        neu = (float(k[0][1]), float(k[0][2]), float(k[0][3]),
               float(k[0][4]), float(k[0][5]))
        if alt.get((sym, st)) == neu:
            gleich += 1
            continue
        w.execute("INSERT OR REPLACE INTO stundenkurse VALUES (?,?,?,?,?,?,?)",
                  (sym, st) + neu)
        geaendert += 1
        if i % 25 == 0:
            w.commit()
            print("  [%3d/%3d] %d geaendert, %d schon richtig, %.1f Min"
                  % (i, len(faellig), geaendert, gleich,
                     (time.time() - t0) / 60))
    w.commit()

    # ── Abnahmeprobe: ist die Volumenquote jetzt bei 1? ───────────────
    import numpy as np
    quoten = []
    for sym, st in faellig:
        r = w.execute("SELECT volumen FROM stundenkurse WHERE symbol=? "
                      "ORDER BY stunde DESC LIMIT 101", (sym,)).fetchall()
        if len(r) < 50:
            continue
        rest = [x[0] for x in r[1:] if x[0]]
        if rest and r[0][0]:
            quoten.append(r[0][0] / float(np.median(rest)))
    w.close()
    print()
    print("  FERTIG: %d geaendert · %d waren schon richtig · %d Fehler"
          % (geaendert, gleich, len(fehler)))
    if quoten:
        q = np.array(quoten)
        print("  ⭐ Abnahmeprobe: Median-Volumenquote der letzten Kerze "
              "jetzt %.3f (vorher 0,736) · unter 60 %%: %d von %d"
              % (float(np.median(q)), int((q < 0.6).sum()), len(q)))
        print("     ⚠️ Der Median wird NICHT genau 1,0 - eine einzelne "
              "Stunde streut")
        print("        naturgemaess um das Mittel der 100 davor. "
              "Entscheidend ist,")
        print("        dass die systematische Untererfassung verschwindet.")
    if fehler:
        print("  ⚠️ %d Fehler: %s" % (len(fehler), "; ".join(fehler[:3])))
    print()
    print("  ➤ JETZT R-R11: `python pruefe_rr11_stundenkerze.py "
          "<vorher.txt> <nachher.txt>`")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
