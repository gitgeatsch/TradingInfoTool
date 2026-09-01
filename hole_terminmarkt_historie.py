# -*- coding: utf-8 -*-
"""Die Terminmarkt-Historie aus dem Binance-Archiv (01.09.2026).

## Warum es dieses Werkzeug gibt

Am 01.09. galt: *„H-4c (OI als Beitrag) ist vor 2028 nicht belastbar
messbar."* Die Begruendung war richtig gerechnet - unsere EIGENE Sammlung
laeuft seit dem 14.07. und haette bei Horizont H3 rund 600 Kalendertage
gebraucht, um auf 20 Bloecke zu kommen (Methodik 2.95).

⚠️ **Die Begruendung war richtig und die Schlussfolgerung falsch.**
Nutzerhinweis, woertlich: *„ab 2028 ist eher sinnlos, wir bauen jetzt eine
Loesung und nicht in 2 Jahren. Unabhaengig davon muessen wir versuchen eine
Loesung zu finden - kannst du den OI-Beitrag nicht anderweitig beschaffen
bzw. recherchieren, was wir machen koennen."*

Die Antwort stand die ganze Zeit offen zugaenglich: Binance veroeffentlicht
die Terminmarkt-Kennzahlen als oeffentliches Archiv. **Damit ist H-4c
JETZT messbar.**

⚠️ Die Lehre daneben ist die eigentliche: *bevor eine Wartezeit behauptet
wird, ist der Historie-Endpunkt zu suchen* (Methodik 2.90). Dieselbe Regel
hat am 30.08. schon zweimal zugeschlagen - TVL („ab 18.09.") und Funding
(„ab 22.10.") waren beide sofort verfuegbar. **Beim dritten Mal habe ich
sie wieder nicht angewandt.**

## Was das Archiv liefert - an der Quelle geprueft

    Quelle       data.binance.vision/data/futures/um/daily/metrics
    Reichweite   ab 2021 (2020 nicht), taegliche Dateien
    Aufloesung   5 Minuten, 288 Messpunkte je Tag
    Groesse      10,9 KB je Symbol und Tag (Median ueber 32 Symbole)
    Kosten       keine, kein Schluessel, kein Kontingent

    Spalten      create_time · symbol · sum_open_interest
                 sum_open_interest_value
                 count_toptrader_long_short_ratio    <- Positionierung der Grossen
                 sum_toptrader_long_short_ratio
                 count_long_short_ratio              <- der Long-Bias
                 sum_taker_long_short_vol_ratio

⚠️ **Die Long/Short-Verhaeltnisse hatten wir noch nie.** Unser eigenes
`open_interest_snapshot` fuehrt nur `long_account_pct`; die vier
Verhaeltnisse hier trennen Konten von Volumen und Top-Tradern von allen -
genau die Unterscheidung, die die Praxisliteratur beim Short Squeeze macht.

## Die Entscheidungen - und woher sie kommen

**3 JAHRE, 1 STUNDE, EIGENE DATEI** (Nutzerentscheidung 01.09.).

    3 Jahre    36 Bloecke bei H3 - komfortabel ueber der Grenze von 20.
               Ein Jahr gaebe nur 12 und waere untermaechtig.
    1 Stunde   ⚠️ Sie passt zum VERSANDTAKT. Unsere Mails gehen einige Male
               am Tag raus; ein 5-Minuten-Signal ist veraltet, bevor es
               gelesen wird. Und die Praxisquelle des Nutzers nennt fuer
               MACD ausdruecklich den 1-Stunden-Chart.
               Gespeichert werden 0,84 Mio Zeilen statt 10,1 Mio - 77 MB
               statt 920 MB.
    eigene     `data/terminmarkt_historie.db`, wie `funding_historie.db`
    Datei      und `onchain_historie.db`. **Die Produktionsdatenbank wird
               nicht angefasst**, und kein Backup zieht mit.

⚠️ **REVERSIBEL:** Wenn sich zeigt, dass 5 Minuten noetig sind, laedt man
neu. Das Archiv verschwindet nicht - anders als bei einer eigenen Sammlung,
wo jeder nicht gespeicherte Tag dauerhaft fehlt.

## ⚠️ Was NICHT abgedeckt ist

Elf von 43 Watchlist-Werten haben keinen Binance-Perpetual und stehen
deshalb in keinem Archiv:

    AIOZ · ASTER · CANTON · CAT · FLOKI · HYPE · MON · PLUME · SUPRA
    VSN · XNO

Das sind 26 % der Watchlist, darunter gehaltene Positionen. Fuer die
MESSUNG reicht es (32 Symbole je Tag liegen ueber der Querschnittsgrenze
von 15), **aber ein daraus entstehender Beitrag waere fuer diese elf nie
bestimmbar** - sie bekaemen `bewertbar=False`, genau wie heute schon die
Werte ohne Funding. Das ist eine Eigenschaft der Datenlage, kein Fehler,
und sie gehoert bei jeder spaeteren Auswertung dazu.

## Die Verdichtung - und warum LETZTER Wert, nicht Mittel

Open Interest ist ein **Bestand**, keine Stromgroesse: er sagt, wie viele
Kontrakte offen SIND, nicht wie viele gehandelt wurden. Der Wert am
Stundenende ist damit der Zustand zu diesem Zeitpunkt - genau das, was
`positionierung` auch aus den eigenen Schnappschuessen liest.

Ein Mittelwert waere hier die falsche Form (Methodik 2.85: *die FORM der
Groesse vor der Messung klaeren*): er beschriebe einen Zustand, der zu
keinem Zeitpunkt bestand.

⚠️ `punkte` haelt fest, aus wie vielen 5-Minuten-Werten eine Stunde
gebildet wurde. Eine Stunde mit zwei Punkten ist etwas anderes als eine
mit zwoelf, und ohne diese Zahl saehe man den Unterschied nicht.

## Aufwand - gemessen, nicht geschaetzt

    Anfragen   32 Symbole x 1.095 Tage = 35.040
    Durchsatz  6,8 Anfragen/s bei 8 parallel (gemessen)
    Dauer      rund 86 Minuten
    Transfer   373 MB (wird nicht gespeichert, nur gelesen)
    Datenbank  0,84 Mio Zeilen, rund 77 MB

⚠️ **WIEDERAUFNEHMBAR.** Jede (Symbol, Tag)-Kombination wird nach Erfolg in
`abruf_status` vermerkt. Ein Abbruch kostet nichts: der naechste Lauf
ueberspringt, was schon da ist. Bei 86 Minuten Laufzeit ist das keine
Bequemlichkeit, sondern Voraussetzung.

⚠️ **404 IST KEIN FEHLER.** Ein Symbol wurde irgendwann gelistet; davor
gibt es keine Dateien. Diese Tage werden als `fehlt` vermerkt und nicht
erneut versucht - sonst kostete jeder Lauf sie neu.

    python hole_terminmarkt_historie.py                 # 3 Jahre, alle 32
    python hole_terminmarkt_historie.py --jahre 1       # kuerzer
    python hole_terminmarkt_historie.py --symbole BTC,ETH
    python hole_terminmarkt_historie.py --probe         # 2 Symbole, 3 Tage
"""
import argparse
import csv
import io
import sqlite3
import sys
import time
import zipfile
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta

import requests

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASIS = "https://data.binance.vision/data/futures/um/daily/metrics"
DB = "data/terminmarkt_historie.db"
PARALLEL = 8
JAHRE = 3

SCHEMA = """
CREATE TABLE IF NOT EXISTS terminmarkt (
    symbol TEXT NOT NULL,
    stunde TEXT NOT NULL,              -- 'YYYY-MM-DD HH:00'
    oi REAL,                           -- sum_open_interest, LETZTER Wert
    oi_wert REAL,                      -- sum_open_interest_value
    top_konten_verh REAL,              -- count_toptrader_long_short_ratio
    top_summe_verh REAL,               -- sum_toptrader_long_short_ratio
    konten_verh REAL,                  -- count_long_short_ratio
    taker_verh REAL,                   -- sum_taker_long_short_vol_ratio
    punkte INTEGER NOT NULL,           -- wieviele 5-Minuten-Werte
    PRIMARY KEY (symbol, stunde));
CREATE TABLE IF NOT EXISTS abruf_status (
    symbol TEXT NOT NULL, tag TEXT NOT NULL,
    stand TEXT NOT NULL,               -- 'ok' | 'fehlt'
    zeilen INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (symbol, tag));
"""

# ⚠️ Gemessen am 01.09.2026 mit je einer HEAD-Anfrage - nicht geraten.
# Wer die Liste erweitert, prueft ZUERST, ob es das Paar gibt: ein Symbol
# ohne Perpetual erzeugt sonst 1.095 vergebliche Anfragen.
OHNE_PERPETUAL = ("AIOZ", "ASTER", "CANTON", "CAT", "FLOKI", "HYPE", "MON",
                  "PLUME", "SUPRA", "VSN", "XNO")


def watchlist_krypto() -> list[str]:
    """Die Krypto-Werte der Watchlist, ohne die ohne Perpetual."""
    sys.path.insert(0, ".")
    import config as C
    from agent import assetklassen as AK
    alle = AK.gruppiere(C.get_watchlist()).get("krypto", [])
    return [s for s in alle if s.upper() not in OHNE_PERPETUAL]


def verdichte(roh: list) -> dict:
    """5-Minuten-Zeilen zu Stunden - LETZTER Wert je Stunde.

    ⚠️ Open Interest ist ein BESTAND. Der Wert am Stundenende ist der
    Zustand zu diesem Zeitpunkt; ein Mittelwert beschriebe einen Zustand,
    der zu keinem Zeitpunkt bestand (Methodik 2.85, die Form der Groesse).
    """
    je_stunde: dict = defaultdict(list)
    for z in roh:
        t = str(z.get("create_time") or "")
        if len(t) < 13:
            continue
        je_stunde[t[:13] + ":00"].append(z)

    def _f(x):
        try:
            return float(x)
        except (TypeError, ValueError):
            return None

    aus = {}
    for stunde, zeilen in je_stunde.items():
        letzte = sorted(zeilen, key=lambda z: str(z.get("create_time")))[-1]
        aus[stunde] = (
            _f(letzte.get("sum_open_interest")),
            _f(letzte.get("sum_open_interest_value")),
            _f(letzte.get("count_toptrader_long_short_ratio")),
            _f(letzte.get("sum_toptrader_long_short_ratio")),
            _f(letzte.get("count_long_short_ratio")),
            _f(letzte.get("sum_taker_long_short_vol_ratio")),
            len(zeilen))
    return aus


def hole_tag(sitzung, symbol: str, tag: str) -> tuple:
    """(stand, {stunde: werte}) fuer EINEN Symbol-Tag.

    ⚠️ 404 heisst 'fehlt', nicht 'Fehler': vor der Listung eines Paares gibt
    es keine Datei. Ein Netzfehler dagegen heisst 'spaeter nochmal' und wird
    NICHT als `fehlt` vermerkt - sonst waere ein Aussetzer dauerhaft.
    """
    paar = "%sUSDT" % symbol.upper()
    url = "%s/%s/%s-metrics-%s.zip" % (BASIS, paar, paar, tag)
    try:
        r = sitzung.get(url, timeout=30)
    except Exception:
        return "netz", {}
    if r.status_code == 404:
        return "fehlt", {}
    if r.status_code != 200:
        return "netz", {}
    try:
        z = zipfile.ZipFile(io.BytesIO(r.content))
        roh = list(csv.DictReader(
            io.StringIO(z.read(z.namelist()[0]).decode("utf-8", "replace"))))
    except Exception:
        return "netz", {}
    return "ok", verdichte(roh)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--db", default=DB)
    p.add_argument("--jahre", type=float, default=JAHRE)
    p.add_argument("--symbole", default="")
    p.add_argument("--parallel", type=int, default=PARALLEL)
    p.add_argument("--probe", action="store_true",
                   help="2 Symbole, 3 Tage - fuer die Pruefung vor dem Lauf")
    a = p.parse_args()

    symbole = ([s.strip().upper() for s in a.symbole.split(",") if s.strip()]
               or watchlist_krypto())
    heute = date.today()
    tage_n = int(a.jahre * 365)
    if a.probe:
        symbole, tage_n = symbole[:2], 3
    tage = [(heute - timedelta(days=i + 2)).isoformat()
            for i in range(tage_n)]

    conn = sqlite3.connect(a.db)
    conn.executescript(SCHEMA)
    conn.commit()
    fertig = {(r[0], r[1]) for r in conn.execute(
        "SELECT symbol, tag FROM abruf_status")}
    auftrag = [(s, t) for s in symbole for t in tage if (s, t) not in fertig]

    print("=" * 78)
    print("TERMINMARKT-HISTORIE AUS DEM BINANCE-ARCHIV")
    print("=" * 78)
    print("  %d Symbole x %d Tage = %d Kombinationen" %
          (len(symbole), len(tage), len(symbole) * len(tage)))
    print("  davon schon geholt: %d, offen: %d" % (len(fertig), len(auftrag)))
    print("  Ziel: %s  ·  %d parallel" % (a.db, a.parallel))
    if not auftrag:
        print("\n  Nichts zu tun.")
        return 0
    print("  Geschaetzte Dauer: %.0f Minuten" % (len(auftrag) / 6.8 / 60))
    print()

    sitzung = requests.Session()
    t0 = time.time()
    ok = fehlt = netz = zeilen = 0

    def _arbeit(x):
        return x, hole_tag(sitzung, x[0], x[1])

    with ThreadPoolExecutor(max_workers=a.parallel) as ex:
        for i, ((sym, tag), (stand, werte)) in enumerate(
                ex.map(_arbeit, auftrag), 1):
            if stand == "ok":
                conn.executemany(
                    "INSERT OR REPLACE INTO terminmarkt VALUES (?,?,?,?,?,?,?,?,?)",
                    [(sym, st) + w for st, w in sorted(werte.items())])
                conn.execute("INSERT OR REPLACE INTO abruf_status VALUES (?,?,?,?)",
                             (sym, tag, "ok", len(werte)))
                ok += 1
                zeilen += len(werte)
            elif stand == "fehlt":
                conn.execute("INSERT OR REPLACE INTO abruf_status VALUES (?,?,?,?)",
                             (sym, tag, "fehlt", 0))
                fehlt += 1
            else:
                # ⚠️ NICHT VERMERKEN - ein Netzfehler soll beim naechsten
                # Lauf erneut versucht werden.
                netz += 1
            if i % 500 == 0:
                conn.commit()
                v = time.time() - t0
                print("  %6d/%d  ok %5d  fehlt %5d  netz %4d  %6d Stunden  "
                      "%5.1f/s  noch %.0f min"
                      % (i, len(auftrag), ok, fehlt, netz, zeilen, i / v,
                         (len(auftrag) - i) / max(i / v, 0.1) / 60))
    conn.commit()

    print()
    print("=" * 78)
    print("  %d ok · %d ohne Datei (vor der Listung) · %d Netzfehler"
          % (ok, fehlt, netz))
    print("  %d Stundenzeilen geschrieben" % zeilen)
    g = conn.execute("SELECT COUNT(*), COUNT(DISTINCT symbol), "
                     "MIN(stunde), MAX(stunde) FROM terminmarkt").fetchone()
    print("  Bestand: %d Zeilen, %d Symbole, %s .. %s" % g)
    if netz:
        print("  ⚠️ %d Netzfehler wurden NICHT vermerkt - ein erneuter Lauf "
              "holt sie nach." % netz)
    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
