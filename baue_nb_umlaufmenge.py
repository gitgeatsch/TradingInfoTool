# -*- coding: utf-8 -*-
"""Die SCHLANKE Mengendatei fuer das Notebook bauen (USB-Uebertragung).

⚠️⚠️⚠️ WARUM SCHLANK (22.09.2026, Umbaukonzept T7). `*.db` steht in
`.gitignore` - ein Pull bringt `data/umlaufmenge_cg.db` NICHT ans
Notebook, und ohne sie faellt `turnover` dort komplett aus, sobald
`umschlag_frei` live geht.

Aber das Notebook braucht nur einen Bruchteil:

    BETRIEB   rechnet Volumen(heute) / Menge(heute) -> es zaehlt der
              JUENGSTE Wert je Symbol, plus die Symbol-zu-CoinGecko-
              Zuordnung, damit der Tagesjob weiss, was er abfragen soll.
    MESSUNG   braucht die volle Historie (137.748 Punkte, 8,3 MB) - und
              die laeuft am DESKTOP.

## ⚠️⚠️ DIE BETRIEBSMARKE IST DER KERN, NICHT DIE GROESSE

Eine Datei mit 14 statt 365 Tagen sieht aus wie die Messbasis und ist es
nicht. Genau dieser Fall hat schon einmal Schaden angerichtet
(`betriebskopie-ist-keine-messbasis`, `messdaten.db` am Notebook). Deshalb
traegt die Kopie eine Markertabelle `_nur_betrieb`, und der MESSleser
(`phase4_c_naeherung_konstante_menge.mengen_heute`) bricht darauf ab -
nicht warnt, bricht ab.

## Die Buendelmarke wird MITKOPIERT, nicht neu ausgestellt

Die Zeilen sind Kopien faktorkorrigierter Zeilen (Befund 2.522, zweifach
belegt). Herkunft und Daten wandern zusammen - das ist etwas anderes, als
einer unmarkierten Datei nachtraeglich eine Marke zu geben.

⚠️ NUR LESEND auf der Quelle.
"""
import datetime as dt
import os
import shutil
import sqlite3
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
os.chdir("D:/CLAUDE_Projects/SoftwareProjekte/TradingInfoTool")

QUELLE = "data/umlaufmenge_cg.db"
TAGE = 14
ZIEL = ("_usb_nach_nb/claudesync/TradingInfoTool/data/umlaufmenge_cg.db")
NB_PFAD = r"C:\CLAUDE_Projects\SoftwareProjekte\TradingInfoTool\data"


def main() -> int:
    if not os.path.exists(QUELLE):
        print("⛔ %s fehlt" % QUELLE)
        return 2
    grenze = (dt.date.today() - dt.timedelta(days=TAGE)).isoformat()
    os.makedirs(os.path.dirname(ZIEL), exist_ok=True)
    if os.path.exists(ZIEL):
        os.remove(ZIEL)

    q = sqlite3.connect("file:%s?mode=ro" % QUELLE, uri=True)
    z = sqlite3.connect(ZIEL)
    z.executescript("""
    CREATE TABLE umlaufmenge (
        symbol TEXT NOT NULL, datum TEXT NOT NULL, wert REAL NOT NULL,
        PRIMARY KEY (symbol, datum));
    CREATE TABLE abruf_symbol (
        symbol TEXT PRIMARY KEY, coingecko_id TEXT, status TEXT,
        punkte INTEGER, verworfen INTEGER, spruenge INTEGER,
        groesster_sprung REAL, urteil TEXT, geholt_am TEXT);
    CREATE TABLE _quelle (
        hinweis TEXT, groesse TEXT, tage INTEGER, gebaut_am TEXT,
        buendelfaktor TEXT);
    CREATE TABLE _nur_betrieb (
        hinweis TEXT, tage INTEGER, gebaut_am TEXT);
    """)

    # ---- die Zuordnung VOLLSTAENDIG - ohne sie findet der Tagesjob nichts
    zeilen = list(q.execute("SELECT * FROM abruf_symbol"))
    z.executemany("INSERT INTO abruf_symbol VALUES (?,?,?,?,?,?,?,?,?)",
                  zeilen)
    # ---- die Mengen nur der letzten Tage
    werte = list(q.execute(
        "SELECT symbol, datum, wert FROM umlaufmenge WHERE datum >= ?",
        (grenze,)))
    z.executemany("INSERT INTO umlaufmenge VALUES (?,?,?)", werte)
    # ---- Herkunft MITKOPIERT
    alt = q.execute("SELECT hinweis, groesse, tage, gebaut_am, "
                    "buendelfaktor FROM _quelle").fetchone()
    z.execute("INSERT INTO _quelle VALUES (?,?,?,?,?)", alt)
    z.execute(
        "INSERT INTO _nur_betrieb VALUES (?,?,?)",
        ("⚠️ BETRIEBSKOPIE, KEINE MESSBASIS. Nur die letzten %d Tage - "
         "genug fuer `turnover_werte` (Volumen heute / Menge heute), NICHT "
         "genug fuer eine Kalibrierung. Die volle Historie liegt am "
         "Desktop. Wer hier misst, misst %d Tage und glaubt, es seien "
         "365." % (TAGE, TAGE), TAGE,
         dt.datetime.now(dt.timezone.utc).isoformat()))
    z.commit()
    n_sym = z.execute("SELECT COUNT(DISTINCT symbol) "
                      "FROM umlaufmenge").fetchone()[0]
    stand = z.execute("SELECT MAX(datum) FROM umlaufmenge").fetchone()[0]
    z.close()
    q.close()

    gross = os.path.getsize(ZIEL) / 1024.0
    print("=" * 78)
    print("SCHLANKE MENGENDATEI FUER DAS NOTEBOOK")
    print("=" * 78)
    print("  Zuordnung   %4d Symbole (vollstaendig)" % len(zeilen))
    print("  Mengen      %4d Symbole · %d Zeilen · ab %s · Stand %s"
          % (n_sym, len(werte), grenze, stand))
    print("  Groesse     %.0f KB  (Quelle: %.1f MB)"
          % (gross, os.path.getsize(QUELLE) / 1e6))
    print("  Marken      _quelle.buendelfaktor mitkopiert · _nur_betrieb "
          "gesetzt")
    print()
    print("  LIEGT HIER:")
    print("    %s" % os.path.abspath(ZIEL))
    print("  AM NOTEBOOK ABLEGEN NACH:")
    print("    %s" % NB_PFAD)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
