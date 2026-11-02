"""AUSZUG Stundenkurse vom NOTEBOOK über den Austauschordner (G7 Stufe 0e, Voranalyse_G7_Messplan_02_11.md §6.3, Nutzer 02.11.:
*„bei 6.3 warum per USB können wir das nicht über den Austauschordner Google drive erledigen?“* — ja, und kleiner als per USB).

Liest am NB NUR LESEND (``mode=ro``) die zwei REGEL0-Kursdateien, die dort der Job ``regel0_nachlader`` stündlich fortschreibt, und
schreibt die Zeilen AB ``AB`` in EINE neue Datei NEBEN dieses Skript (im Austauschordner). Am Desktop fehlen die Wochen ab Mitte
September (G7-1): ohne sie hat das Rückspiel Dez. 2025 – Okt. 2026 schon bei H = 1 nur 19 Blöcke.

⚠️ Berührt NICHTS im Projekt: keine Produktions-DB (``tradinginfotool.db`` wird verweigert), kein Netz, kein Schreiben in ``data/``.
⚠️ Wartet, bis die Minute zwischen 20 und 50 liegt — der Nachlader schreibt ab Minute 5 jeder Stunde.

Am NB, im PROJEKTORDNER (dort, wo ``data\\stundenkurse.db`` liegt):

    python "<Laufwerk>:\\My Drive\\Claude_Austauschordner\\G7_Kurse\\nb_auszug_kurse.py"

Ergebnis: ``kurse_auszug_<JJJJ-MM-TT>.db`` im selben Ordner (≈ 50–100 MB). Danach am Desktop: ``g7_kurse_einlesen.py``.
"""
import os
import socket
import sqlite3
import sys
import time
from datetime import datetime, timezone

AB = "2026-08-01"                                  # sechs Wochen Überlappung mit dem Desktop (Gegenprobe), dann das Neue
DATEIEN = ("stundenkurse.db", "stundenkurse_alle.db")


def main():
    daten = os.path.join(sys.argv[1] if len(sys.argv) > 1 else os.getcwd(), "data")
    for f in DATEIEN:
        if not os.path.exists(os.path.join(daten, f)):
            sys.exit("nicht gefunden: %s - bitte im Projektordner starten (oder den Projektordner als Argument angeben)" % os.path.join(daten, f))
    ziel_ordner = os.path.dirname(os.path.abspath(__file__))
    if os.path.abspath(ziel_ordner).lower().startswith(os.path.abspath(daten).lower()):
        sys.exit("das Skript muss im Austauschordner liegen, nicht im Projekt")
    while not 20 <= datetime.now().minute <= 50:
        print("warte auf Minute 20-50 (der Nachlader schreibt ab Minute 5) ...", flush=True)
        time.sleep(60)
    ziel = os.path.join(ziel_ordner, "kurse_auszug_%s.db" % datetime.now().strftime("%Y-%m-%d"))
    if os.path.basename(ziel) == "tradinginfotool.db":
        sys.exit("verweigert")
    if os.path.exists(ziel):
        os.remove(ziel)                                # nur die eigene Auszugsdatei von heute
    z = sqlite3.connect(ziel)
    z.execute("CREATE TABLE _meta (schluessel TEXT, wert TEXT)")
    for f in DATEIEN:
        t0 = time.time()
        q = sqlite3.connect("file:%s?mode=ro" % os.path.join(daten, f).replace("\\", "/"), uri=True, timeout=60)
        spalten = [r[1] for r in q.execute("PRAGMA table_info(stundenkurse)")]
        marken = [r[0] for r in q.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '\\_%' ESCAPE '\\'")]
        zeilen = q.execute("SELECT %s FROM stundenkurse WHERE stunde >= ?" % ",".join(spalten), (AB,)).fetchall()
        quelle = q.execute("SELECT * FROM _quelle").fetchall() if "_quelle" in marken else []
        q.close()
        tab = "kurse_" + f.replace(".db", "")
        z.execute("CREATE TABLE %s (%s)" % (tab, ",".join(spalten)))
        z.executemany("INSERT INTO %s VALUES (%s)" % (tab, ",".join("?" * len(spalten))), zeilen)
        if quelle:
            z.execute("CREATE TABLE quelle_%s (symbol, markt, paar, geholt_am)" % f.replace(".db", ""))
            z.executemany("INSERT INTO quelle_%s VALUES (?,?,?,?)" % f.replace(".db", ""), quelle)
        mx = max((r[1] for r in zeilen), default="")
        z.executemany("INSERT INTO _meta VALUES (?,?)", [("%s.zeilen" % f, str(len(zeilen))), ("%s.bis" % f, mx),
                                                        ("%s.marken" % f, ",".join(marken)),
                                                        ("%s.symbole" % f, str(len({r[0] for r in zeilen})))])
        print("%-22s %8d Zeilen ab %s, bis %s, %d Symbole, Marken %s (%.0f s)" % (
            f, len(zeilen), AB, mx, len({r[0] for r in zeilen}), ",".join(marken) or "-", time.time() - t0), flush=True)
    z.executemany("INSERT INTO _meta VALUES (?,?)", [("rechner", socket.gethostname()), ("ab", AB),
                                                    ("geholt_utc", datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00"))])
    z.commit()
    z.close()
    print("fertig: %s (%.0f MB) - Google Drive synchronisiert ihn zum Desktop" % (ziel, os.path.getsize(ziel) / 1e6))


if __name__ == "__main__":
    main()
