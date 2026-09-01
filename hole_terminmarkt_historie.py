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
CREATE TABLE IF NOT EXISTS terminmarkt_tag (
    symbol TEXT NOT NULL,
    tag TEXT NOT NULL,                 -- 'YYYY-MM-DD'
    oi REAL, oi_wert REAL,
    top_konten_verh REAL, top_summe_verh REAL,
    konten_verh REAL, taker_verh REAL,
    punkte INTEGER NOT NULL,
    PRIMARY KEY (symbol, tag));
CREATE TABLE IF NOT EXISTS abruf_status (
    symbol TEXT NOT NULL, tag TEXT NOT NULL,
    stand TEXT NOT NULL,               -- 'ok' | 'fehlt'
    zeilen INTEGER NOT NULL DEFAULT 0,
    aufloesung TEXT NOT NULL DEFAULT 'stunde',
    PRIMARY KEY (symbol, tag, aufloesung));
CREATE TABLE IF NOT EXISTS messbasis (
    symbol TEXT PRIMARY KEY, gezogen_am TEXT NOT NULL, saat INTEGER NOT NULL);
"""

# ⚠️ DIE MESSBASIS IST EINE STICHPROBE MIT FESTER SAAT (01.09.2026).
#
# Der erste Import nahm die 32 WATCHLIST-Werte - und H-4c war damit
# untermaechtig (F-167: zwei von fuenf Negativkontrollen trugen). Die Lehre
# steht seit P6 im Gesamtplan: *„Die Messbasis ist breiter als das
# Portfolio und muss es sein - sonst misst man seine eigene Auswahl."*
#
# ⚠️ WARUM EINE ZUFALLSSTICHPROBE UND NICHT „DIE GROESSTEN 100":
# eine Auswahl nach heutiger Groesse waere Survivorship in Reinform - die
# Werte, die es heute gross gibt, sind die, die ueberlebt haben. Eine
# Stichprobe mit fester Saat ist unverzerrt und wiederholbar; sie wird in
# `messbasis` festgehalten, damit ein spaeterer Lauf dieselbe zieht.
#
# ⚠️ 100 statt 293 ist eine ZEITfrage, keine Messfrage: die Blockzahl haengt
# an den TAGEN (Methodik 2.98), 100 Anker je Tag liegen weit ueber dem
# Mindestquerschnitt von 15. Eine spaetere Erweiterung auf 293 macht die
# Baender enger, nicht die Bloecke mehr.
MESSBASIS_SAAT = 20260901
MESSBASIS_N = 100

# ⚠️ Gemessen am 01.09.2026 mit je einer HEAD-Anfrage - nicht geraten.
# Wer die Liste erweitert, prueft ZUERST, ob es das Paar gibt: ein Symbol
# ohne Perpetual erzeugt sonst 1.095 vergebliche Anfragen.
OHNE_PERPETUAL = ("AIOZ", "ASTER", "CANTON", "CAT", "FLOKI", "HYPE", "MON",
                  "PLUME", "SUPRA", "VSN", "XNO")


def migriere(conn) -> None:
    """⚠️ `CREATE TABLE IF NOT EXISTS` aendert eine BESTEHENDE Tabelle nicht.

    Der erste Lauf legte `abruf_status` mit dem Schluessel (symbol, tag) an.
    Mit zwei Aufloesungen braucht es (symbol, tag, aufloesung) - sonst
    gaelte ein stuendlich geholter Tag als auch taeglich erledigt, und der
    Nachlauf uebersaehe genau die Symbole, fuer die er laeuft.

    ⚠️ SQLite kann keinen Primaerschluessel aendern. Also: neue Tabelle,
    kopieren, umbenennen - in EINER Transaktion, damit ein Abbruch nicht
    auf halbem Weg stehenbleibt. Gefunden VOR dem 8-Stunden-Lauf, nicht
    darin.
    """
    spalten = {r[1] for r in conn.execute("PRAGMA table_info(abruf_status)")}
    if "aufloesung" in spalten:
        return
    conn.executescript("""
        BEGIN;
        CREATE TABLE abruf_status_neu (
            symbol TEXT NOT NULL, tag TEXT NOT NULL,
            stand TEXT NOT NULL, zeilen INTEGER NOT NULL DEFAULT 0,
            aufloesung TEXT NOT NULL DEFAULT 'stunde',
            PRIMARY KEY (symbol, tag, aufloesung));
        INSERT INTO abruf_status_neu (symbol, tag, stand, zeilen, aufloesung)
            SELECT symbol, tag, stand, zeilen, 'stunde' FROM abruf_status;
        DROP TABLE abruf_status;
        ALTER TABLE abruf_status_neu RENAME TO abruf_status;
        COMMIT;""")
    print("  abruf_status migriert: Aufloesung ist jetzt Teil des Schluessels")


def messbasis_symbole(conn, n: int = MESSBASIS_N) -> list[str]:
    """Die Messbasis - Zufallsstichprobe aus den Perpetuals in `messdaten.db`.

    ⚠️ EINMAL GEZOGEN, DANN FESTGEHALTEN. Ein zweiter Lauf mit anderer
    Stichprobe waere eine andere Messung unter demselben Namen.
    """
    import random
    import sqlite3
    da = [r[0] for r in conn.execute("SELECT symbol FROM messbasis ORDER BY symbol")]
    if da:
        return da
    r = requests.get("https://fapi.binance.com/fapi/v1/exchangeInfo", timeout=30)
    perp = {s["symbol"][:-4] for s in r.json().get("symbols", [])
            if s.get("quoteAsset") == "USDT" and s.get("status") == "TRADING"
            and s.get("contractType") == "PERPETUAL"}
    md = sqlite3.connect("file:data/messdaten.db?mode=ro", uri=True)
    mess = {str(x[0]).upper() for x in md.execute(
        "SELECT DISTINCT symbol FROM price_history_ohlc WHERE currency='USD'")}
    md.close()
    kand = sorted(perp & mess)
    rng = random.Random(MESSBASIS_SAAT)
    aus = sorted(rng.sample(kand, min(n, len(kand))))
    import datetime as _d
    conn.executemany("INSERT OR REPLACE INTO messbasis VALUES (?,?,?)",
                     [(s, _d.date.today().isoformat(), MESSBASIS_SAAT)
                      for s in aus])
    conn.commit()
    print("  Messbasis gezogen: %d von %d moeglichen (Saat %d) - festgehalten"
          % (len(aus), len(kand), MESSBASIS_SAAT))
    return aus


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


def verdichte_tag(roh: list) -> tuple | None:
    """Ein ganzer Tag zu EINER Zeile - letzter Wert des Tages.

    ⚠️ Dieselbe Begruendung wie bei der Stunde: Open Interest ist ein
    BESTAND. Der Wert um 23:55 ist der Zustand des Tages.
    """
    if not roh:
        return None
    letzte = sorted(roh, key=lambda z: str(z.get("create_time")))[-1]

    def _f(x):
        try:
            return float(x)
        except (TypeError, ValueError):
            return None

    return (_f(letzte.get("sum_open_interest")),
            _f(letzte.get("sum_open_interest_value")),
            _f(letzte.get("count_toptrader_long_short_ratio")),
            _f(letzte.get("sum_toptrader_long_short_ratio")),
            _f(letzte.get("count_long_short_ratio")),
            _f(letzte.get("sum_taker_long_short_vol_ratio")),
            len(roh))


def hole_tag(sitzung, symbol: str, tag: str, aufloesung: str = "stunde") -> tuple:
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
    if aufloesung == "tag":
        w = verdichte_tag(roh)
        return "ok", ({tag: w} if w else {})
    return "ok", verdichte(roh)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--db", default=DB)
    p.add_argument("--jahre", type=float, default=JAHRE)
    p.add_argument("--symbole", default="")
    p.add_argument("--parallel", type=int, default=PARALLEL)
    p.add_argument("--probe", action="store_true",
                   help="2 Symbole, 3 Tage - fuer die Pruefung vor dem Lauf")
    p.add_argument("--aufloesung", choices=("stunde", "tag"), default="stunde")
    p.add_argument("--messbasis", action="store_true",
                   help="die Zufallsstichprobe statt der Watchlist")
    a = p.parse_args()

    conn0 = sqlite3.connect(a.db)
    conn0.executescript(SCHEMA)
    migriere(conn0)
    conn0.commit()
    symbole = ([s.strip().upper() for s in a.symbole.split(",") if s.strip()]
               or (messbasis_symbole(conn0) if a.messbasis
                   else watchlist_krypto()))
    conn0.close()
    heute = date.today()
    tage_n = int(a.jahre * 365)
    if a.probe:
        symbole, tage_n = symbole[:2], 3
    tage = [(heute - timedelta(days=i + 2)).isoformat()
            for i in range(tage_n)]

    conn = sqlite3.connect(a.db)
    fertig = {(r[0], r[1]) for r in conn.execute(
        "SELECT symbol, tag FROM abruf_status WHERE aufloesung=?",
        (a.aufloesung,))}
    auftrag = [(s, t) for s in symbole for t in tage if (s, t) not in fertig]

    print("=" * 78)
    print("TERMINMARKT-HISTORIE AUS DEM BINANCE-ARCHIV")
    print("=" * 78)
    print("  %d Symbole x %d Tage = %d Kombinationen" %
          (len(symbole), len(tage), len(symbole) * len(tage)))
    print("  davon schon geholt: %d, offen: %d" % (len(fertig), len(auftrag)))
    print("  Ziel: %s  ·  %d parallel  ·  Aufloesung %s"
          % (a.db, a.parallel, a.aufloesung))
    if not auftrag:
        print("\n  Nichts zu tun.")
        return 0
    print("  Geschaetzte Dauer: %.0f Minuten" % (len(auftrag) / 6.8 / 60))
    print()

    sitzung = requests.Session()
    t0 = time.time()
    ok = fehlt = netz = zeilen = 0

    def _arbeit(x):
        return x, hole_tag(sitzung, x[0], x[1], a.aufloesung)

    with ThreadPoolExecutor(max_workers=a.parallel) as ex:
        for i, ((sym, tag), (stand, werte)) in enumerate(
                ex.map(_arbeit, auftrag), 1):
            ziel = "terminmarkt_tag" if a.aufloesung == "tag" else "terminmarkt"
            if stand == "ok":
                conn.executemany(
                    "INSERT OR REPLACE INTO %s VALUES (?,?,?,?,?,?,?,?,?)" % ziel,
                    [(sym, st) + w for st, w in sorted(werte.items())])
                conn.execute("INSERT OR REPLACE INTO abruf_status VALUES (?,?,?,?,?)",
                             (sym, tag, "ok", len(werte), a.aufloesung))
                ok += 1
                zeilen += len(werte)
            elif stand == "fehlt":
                conn.execute("INSERT OR REPLACE INTO abruf_status VALUES (?,?,?,?,?)",
                             (sym, tag, "fehlt", 0, a.aufloesung))
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
    _z = "terminmarkt_tag" if a.aufloesung == "tag" else "terminmarkt"
    _s = "tag" if a.aufloesung == "tag" else "stunde"
    g = conn.execute("SELECT COUNT(*), COUNT(DISTINCT symbol), "
                     "MIN(%s), MAX(%s) FROM %s" % (_s, _s, _z)).fetchone()
    print("  Bestand: %d Zeilen, %d Symbole, %s .. %s" % g)
    if netz:
        print("  ⚠️ %d Netzfehler wurden NICHT vermerkt - ein erneuter Lauf "
              "holt sie nach." % netz)
    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
