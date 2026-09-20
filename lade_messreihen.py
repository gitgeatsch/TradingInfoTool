"""Breite Messbasis: alle USDT-Spotpaare in eine EIGENE Datenbank (Umbauplan 107)

WARUM. Die Strukturhypothese aus Kapitel 104/105 scheitert nicht am Verfahren,
sondern an der Breite: der bereinigte Vorsprung liegt bei +7,1 Punkten, die
Zufallsschwelle bei +10,0 - und sie liegt so hoch, weil nur 24 Kursreihen lang
genug fuer zwei Zeitbloecke sind. Gemessen am 20.08.2026 bietet Binance
484 USDT-Spotpaare, davon 265 mit mindestens 750 Handelstagen. Das ist die
elffache Breite.

⚠️ NICHT IN DIE PRODUKTIONSDATENBANK. Neue Symbole dort einzutragen hiesse,
den Live-Betrieb als Nebenwirkung einer Messung zu aendern - die Watchlist
steuert, was das System handelt. Diese Reihen gehoeren in eine getrennte
Datei, und der Pfad wird hier hart geprueft.

⚠️ UND NICHT IN DIE WATCHLIST. Weil `_reihen_roh` die Anlageklasse aus der
Watchlist liest, braeuchte es sonst einen Eintrag je Symbol. Stattdessen
bringt diese Datenbank ihre Zuordnung SELBST mit (Tabelle `messreihen`), und
`simuliere_bremse.klassen_aus_db()` liest sie. Ohne das waeren alle neuen
Reihen STILL uebersprungen worden - die Messung haette normal ausgesehen, nur
mit den alten 24 Reihen.

WAS DIESE DATEN SIND UND WAS NICHT:

    Binance-USDT, nicht Bitpanda-EUR. Fuer den Vergleich H gegen Nicht-H auf
    DENSELBEN Ankern derselben Reihe ist das unkritisch - beide Arme sehen
    dieselben Kurse. Fuer eine Renditeaussage in Euro waere es das nicht.

    ⚠️ UEBERLEBENSVERZERRUNG. Wer heute die handelnden Paare laedt, laedt die,
    die ueberlebt haben; eingestellte Paare fehlen. Auch das trifft beide Arme
    gleich, gehoert aber in jeden Befund, der auf diesen Daten steht.

JEDE REIHE WIRD GEPRUEFT, BEVOR SIE GESCHRIEBEN WIRD:

    Tagesabstand   Median der Luecken genau 1 Tag - sonst sind es keine
                   Tageskerzen (dieselbe Pruefung wie in `boersen_klines`)
    Plausibel      high >= low, alle Preise > 0, keine doppelten Daten
    Laenge         mindestens 400 Kerzen, sonst faellt sie in `_reihen_roh`
                   ohnehin durch

    python lade_messreihen.py --schreiben
"""
from __future__ import annotations

import argparse
import os
import sqlite3
import sys
import time
from datetime import date, datetime, timedelta, timezone

import requests

EXCHANGE_INFO = "https://api.binance.com/api/v3/exchangeInfo"
KLINES = "https://api.binance.com/api/v3/klines"
MAX_KERZEN = 1000
MIN_KERZEN = 400
PRODUKTION = "data/tradinginfotool.db"

# ---------------------------------------------------------------------------
# ⚠️⚠️⚠️ DIE BETRIEBSKOPIE - UND WARUM SIE SICH SELBST KENNZEICHNET
# ---------------------------------------------------------------------------
#
# Nutzerentscheidung 20.09.2026: *"C ist die einzige brauchbare Variante"*
# und *"die Trennung ist erforderlich"*.
#
# Das Notebook braucht `messdaten.db` fuer EINE Sache: `marktrang.schnitte()`
# rechnet daraus den 200-Tage-Schnitt. Dafuer genuegen die letzten Monate -
# gemessen 83.926 Zeilen fuer 220 Tage, rund 3 MB gegen 1,5 GB. Die volle
# Historie dort vorzuhalten waere weder noetig noch uebertragbar.
#
# ⚠️⚠️ ABER EINE GEKUERZTE DATEI SIEHT AUS WIE DIE ECHTE. Ihr fehlt die
# Historie, und ihr fehlen die EINGESTELLTEN Werte - ohne die ist jede
# Messung ueberlebensverzerrt (Kapitel 120.3). Wer darauf misst, bekommt ein
# Ergebnis; ein falsches, und ohne jeden Hinweis.
#
# ➔ DESHALB TRAEGT SIE EINE MARKE, genau wie `_nur_symbolliste` in
#   `baue_messbasis_paket.py`: *"eine verkleinerte Datenbank, die aussieht
#   wie eine echte, ist eine Falle"*. Gelesen wird sie an der Stelle, durch
#   die 32 Messskripte gehen - `backtest_llm1_historisch.lade_reihen_aus_db`
#   bricht dort ab statt still zu rechnen.
BETRIEB_MARKE = """
CREATE TABLE IF NOT EXISTS _nur_betrieb (
    hinweis TEXT NOT NULL, behalte_tage INTEGER NOT NULL,
    mindest_kerzen INTEGER NOT NULL, gebaut_am TEXT NOT NULL,
    herkunft TEXT NOT NULL);
"""
BETRIEB_HINWEIS = (
    "BETRIEBSKOPIE - nur die letzten %d Tage, ohne eingestellte Werte. "
    "NICHT fuer Messungen (Survivorship, fehlende Historie). Volle "
    "Messbasis: python lade_messreihen.py --schreiben")


def ist_betriebskopie(conn) -> bool:
    """Traegt diese Datei die Marke? Eine Stelle, alle fragen hier."""
    return bool(conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' "
        "AND name='_nur_betrieb'").fetchone())


def setze_marke(conn, behalte_tage: int, mindest: int) -> None:
    conn.executescript(BETRIEB_MARKE)
    conn.execute("DELETE FROM _nur_betrieb")
    conn.execute("INSERT INTO _nur_betrieb VALUES (?,?,?,?,?)",
                 (BETRIEB_HINWEIS % behalte_tage, int(behalte_tage),
                  int(mindest),
                  datetime.now(timezone.utc).isoformat(timespec="seconds"),
                  "lade_messreihen.py --betriebskopie"))
    conn.commit()


def letzte_tage(conn, klasse: str) -> dict:
    """Symbol -> juengstes gespeichertes Datum. Grundlage von --seit-letztem."""
    try:
        return {r[0]: r[1] for r in conn.execute(
            "SELECT symbol, MAX(date) FROM price_history_ohlc "
            "WHERE assetklasse=? AND currency='USD' GROUP BY symbol",
            (klasse,))}
    except sqlite3.OperationalError:
        return {}


def kuerze(conn, klasse: str, behalte_tage: int) -> int:
    """Alles aelter als N Tage weg - NUR in der Betriebskopie."""
    grenze = (datetime.now(timezone.utc).date()
              - timedelta(days=int(behalte_tage))).isoformat()
    c = conn.execute("DELETE FROM price_history_ohlc "
                     "WHERE assetklasse=? AND date < ?", (klasse, grenze))
    weg = c.rowcount or 0
    conn.commit()
    # ⚠️ OHNE VACUUM BLEIBEN DIE SEITEN BELEGT. Gemessen am 20.09.:
    # 3.006 Zeilen in einer 2,75-MB-Datei, weil 14.646 geloeschte
    # Seiten stehenblieben. Auf dem Notebook zaehlt jedes MB - und
    # eine Datei, die groesser ist als ihr Inhalt, laedt zu der
    # falschen Annahme ein, sie trage mehr als sie traegt.
    if weg:
        conn.execute("VACUUM")
    return weg
KLASSE = "krypto"          # Vorgabe; --klasse setzt sie um

# ⚠️⚠️ `symbol` ist ueber die vier Klassen hinweg KEINE eindeutige Kennung
# (03.09.2026, N-19). Binance-Kuerzel sind bare Ticker ohne Suffix ('DASH',
# nicht 'DASHUSDT') - und kollidieren mit US-Boersentickern: DASH ist die
# DoorDash-Aktie UND die Kryptowaehrung Dash, STX ist Seagate UND Stacks.
# `assetklasse` gehoert deshalb in den Primary Key von `price_history_ohlc` -
# sonst landen zwei verschiedene reale Instrumente unter demselben Symbol in
# EINER Zeitreihe. Gefunden ueber sieben vermischte Symbole (C, DASH, STX, T,
# BOND, DIA, MDT), nachdem ein Themen-ETF-Lauf stillschweigend Kerzen einer
# frueher als 'rohstoffe'/'krypto' geladenen Reihe ueberschrieben hatte.
SCHEMA = """
CREATE TABLE IF NOT EXISTS price_history_ohlc (
    symbol TEXT NOT NULL, assetklasse TEXT NOT NULL, currency TEXT NOT NULL,
    date TEXT NOT NULL, open REAL NOT NULL, high REAL NOT NULL,
    low REAL NOT NULL, close REAL NOT NULL, volume REAL NOT NULL,
    fetched_at TEXT NOT NULL, quelle TEXT NOT NULL DEFAULT 'binance_mess',
    PRIMARY KEY (symbol, assetklasse, currency, date));
-- ⚠️⚠️ DER SCHLUESSEL TRAEGT DIE KLASSE (Schritt 50 Teil A, 13.09.2026).
--
-- Bis dahin war es `symbol TEXT PRIMARY KEY` - eine Klasse je Symbol.
-- `price_history_ohlc` fuehrt dagegen (symbol, assetklasse, ...) und kann
-- ein Symbol in ZWEI Klassen halten. Sieben Symbole tun das, und es sind
-- keine Datenfehler, sondern TICKER-KOLLISIONEN: DASH ist DoorDash UND
-- die Kryptowaehrung, T ist AT&T UND Threshold, STX Seagate UND Stacks
-- (dazu BOND, C, DIA, MDT).
--
-- ⚠️ FOLGENLOS WAR ES BISHER NUR DURCH EINEN ZWEITEN FIX: `_reihen_roh`
-- ueberspringt seit dem 07.09. den `messreihen`-Filter, sobald die Kerzen
-- ihre Klasse selbst tragen (Befund 2.421). Die falsche Zuordnung stand
-- trotzdem da, und `klassen_aus_db()` gab sie weiter.
--
-- ⚠️ `messreihen_status` GEHOERT DAZU. Es hatte dieselbe Mehrdeutigkeit -
-- EINE Statuszeile fuer ZWEI Reihen. Nur eine der beiden Tabellen zu
-- aendern hiesse, die Mehrdeutigkeit eine Tabelle weiter zu schieben.
CREATE TABLE IF NOT EXISTS messreihen (
    symbol TEXT NOT NULL, assetklasse TEXT NOT NULL,
    PRIMARY KEY (symbol, assetklasse));
CREATE TABLE IF NOT EXISTS messreihen_status (
    symbol TEXT NOT NULL, assetklasse TEXT NOT NULL, status TEXT NOT NULL,
    PRIMARY KEY (symbol, assetklasse));
"""


def migriere_klassenschluessel(conn) -> tuple[int, int]:
    """`CREATE TABLE IF NOT EXISTS` aendert eine BESTEHENDE Tabelle nicht.

    Dieselbe Lage wie bei `hole_terminmarkt_historie.migriere` am 01.09.:
    der Schluessel muss um eine Spalte wachsen, und die Daten sollen
    bleiben.

    ⚠️ WAS SIE TUT: baut beide Tabellen mit dem neuen Schluessel neu,
    uebernimmt jede vorhandene Zeile unveraendert und ERGAENZT die
    fehlende zweite Zeile fuer jedes Symbol, das in
    `price_history_ohlc` in zwei Klassen liegt. Der Status der
    ergaenzten Reihe wird vom Symbol uebernommen - er ist die beste
    verfuegbare Angabe, und eine erfundene waere schlechter.

    ⚠️ SIE IST WIEDERHOLBAR: laeuft sie auf einem bereits migrierten
    Stand, findet sie nichts zu tun und meldet (0, 0).

    Rueckgabe: (ergaenzte messreihen-Zeilen, ergaenzte Statuszeilen).
    """
    def _pk_hat_klasse(tab: str) -> bool:
        return any(r[5] == 2 for r in conn.execute("PRAGMA table_info(%s)" % tab))

    if _pk_hat_klasse("messreihen") and _pk_hat_klasse("messreihen_status"):
        return 0, 0

    doppelt = {r[0]: [x[0] for x in conn.execute(
        "SELECT DISTINCT assetklasse FROM price_history_ohlc WHERE symbol=?",
        (r[0],))] for r in conn.execute(
            "SELECT symbol FROM price_history_ohlc GROUP BY symbol "
            "HAVING COUNT(DISTINCT assetklasse) > 1")}

    alt_r = list(conn.execute("SELECT symbol, assetklasse FROM messreihen"))
    alt_s = list(conn.execute("SELECT symbol, status FROM messreihen_status"))
    klasse_von = dict(alt_r)

    conn.execute("ALTER TABLE messreihen RENAME TO _messreihen_alt")
    conn.execute("ALTER TABLE messreihen_status RENAME TO _messreihen_status_alt")
    conn.executescript(SCHEMA)

    neu_r = list(alt_r)
    for sym, klassen in doppelt.items():
        for k in klassen:
            if (sym, k) not in set(neu_r):
                neu_r.append((sym, k))
    conn.executemany("INSERT OR REPLACE INTO messreihen VALUES (?,?)", neu_r)

    neu_s = []
    for sym, status in alt_s:
        for k in (doppelt.get(sym) or [klasse_von.get(sym)]):
            if k:
                neu_s.append((sym, k, status))
    conn.executemany("INSERT OR REPLACE INTO messreihen_status VALUES (?,?,?)",
                     neu_s)
    conn.execute("DROP TABLE _messreihen_alt")
    conn.execute("DROP TABLE _messreihen_status_alt")
    conn.commit()
    return len(neu_r) - len(alt_r), len(neu_s) - len(alt_s)


def _tag(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).date().isoformat()


def paare(s: requests.Session, status: str = "TRADING") -> list[str]:
    """Alle USDT-Spotpaare mit diesem Status.

    ⚠️ `BREAK` sind die EINGESTELLTEN Paare - und genau sie fehlen jeder
    Messung, die nur die heute handelnden laedt (Ueberlebensverzerrung,
    Kapitel 120.3). Der Kline-Endpunkt liefert fuer sie weiterhin Daten;
    gepruefft am 20.08.2026 an BCCUSDT, EOSUSDT, VENUSDT.

    ⚠️ UND `BREAK` IST NICHT GLEICH GESCHEITERT. Darin stecken auch
    Umbenennungen (BCC -> BCH, VEN -> VET) und Wechsel der Notierungs-
    waehrung. Die Gruppe ist heterogen; das gehoert in jeden Befund, der
    auf ihr steht."""
    r = s.get(EXCHANGE_INFO, params={"permissions": "SPOT"}, timeout=30)
    r.raise_for_status()
    return sorted(x["symbol"] for x in r.json()["symbols"]
                  if x["quoteAsset"] == "USDT" and x["status"] == status)


def hole_alles(s: requests.Session, paar: str) -> list[tuple]:
    """Rueckwaerts blaettern bis zur Listung - 1.000 Kerzen je Seite."""
    aus, start = [], 0
    while True:
        r = s.get(KLINES, params={"symbol": paar, "interval": "1d",
                                  "limit": MAX_KERZEN, "startTime": start},
                  timeout=20)
        r.raise_for_status()
        d = r.json()
        if not isinstance(d, list) or not d:
            break
        aus.extend(d)
        if len(d) < MAX_KERZEN:
            break
        start = int(d[-1][0]) + 86_400_000
    return aus


def hole_ab(s: requests.Session, paar: str, ab_ms: int) -> list[tuple]:
    """Nur die Kerzen ab `ab_ms` - der Nachlauf fuer den taeglichen Job.

    ⚠️ EIN Aufruf mit kleinem `limit` statt drei mit 1.000. Gemessen am
    20.09.: 0,242 s je Paar gegen 0,48 s, und Gewicht 1 statt 5. Fuer 493
    Paare sind das 2 Minuten und rund 493 Gewichtspunkte gegen eine Grenze
    von 2.400 je Minute.
    """
    r = s.get(KLINES, params={"symbol": paar, "interval": "1d",
                              "limit": MAX_KERZEN, "startTime": int(ab_ms)},
              timeout=20)
    r.raise_for_status()
    d = r.json()
    return d if isinstance(d, list) else []


def pruefe(rohe: list[tuple], paar: str,
           mindest: int = MIN_KERZEN) -> tuple[bool, str]:
    """⚠️ Eine Quelle, die sich nicht selbst prueft, verlaesst sich darauf,
    dass eine spaetere Stufe ihren Fehler faengt."""
    # ⚠️ `mindest` ist die MESSGRENZE (400 Kerzen), nicht die
    # Betriebsgrenze. Der Nachlauf holt fuenf Kerzen und muesste daran
    # jedes Mal scheitern - deshalb setzt er sie herunter UND vermerkt das
    # in der Marke `_nur_betrieb`. Eine gesenkte Grenze, die niemand sieht,
    # waere genau die Falle, gegen die die Marke gebaut ist.
    if len(rohe) < mindest:
        return False, f"nur {len(rohe)} Kerzen"
    tage = [_tag(int(z[0])) for z in rohe]
    if len(tage) < 2:
        # ⚠️ Eine einzelne Kerze hat keinen Abstand - die Luecken- und
        # Doppelpruefung unten braucht mindestens zwei. Plausibel muss sie
        # trotzdem sein, deshalb kein frueher Ausstieg.
        return _plausibel(rohe, paar)
    if len(set(tage)) != len(tage):
        return False, "doppelte Daten"
    from datetime import date
    dt = [date.fromisoformat(x) for x in tage]
    ab = sorted((dt[i + 1] - dt[i]).days for i in range(len(dt) - 1))
    if ab[len(ab) // 2] != 1:
        return False, f"Median-Abstand {ab[len(ab) // 2]} Tage"
    return _plausibel(rohe, paar)


def _plausibel(rohe: list[tuple], paar: str) -> tuple[bool, str]:
    """high >= low, alle Preise groesser null.

    ⚠️ EIGENE FUNKTION SEIT 20.09.2026: der taegliche Nachlauf holt
    manchmal eine EINZIGE Kerze. Die Luecken- und Doppelpruefung
    braucht mindestens zwei und wuerde sie abweisen - plausibel muss
    sie aber trotzdem sein. Ohne diese Trennung waere die Wahl
    gewesen: entweder die Einzelkerze verwerfen oder sie ungeprueft
    schreiben.
    """
    for z in rohe:
        o, h, l, c = float(z[1]), float(z[2]), float(z[3]), float(z[4])
        if not (h >= l and min(o, h, l, c) > 0):
            return False, f"unplausible Kerze am {_tag(int(z[0]))}"
    return True, ""


# ---------------------------------------------------------------------------
# ZWEITE QUELLE: yfinance fuer aktien / themen_etf / rohstoffe (31.08.2026)
# ---------------------------------------------------------------------------
#
# Nutzerauftrag 31.08., woertlich: *"Multiassets: aktien, Rohstoffe, ETF sind
# noch offen fuer die Bewertung und muessen sauber nachgezogen werden. Hinweis:
# der aktuelle Bestand ist nicht die relevante Groesse und Massstab! Hole dir
# die Daten, die du brauchst ueber die Schnittstellen."*
#
# ⚠️ WARUM HIER UND NICHT IN EINEM ZWEITEN WERKZEUG. Die Prueflogik
# (`pruefe`) und der Schreibweg sind identisch - nur die Quelle ist eine
# andere. Ein zweites Ladewerkzeug waere eine zweite Landkarte neben einer
# bestehenden (Nutzervorgabe 31.08.: *"nichts neues bauen, was wir schon
# haben"*), und die Prueflogik waere ab Tag eins zweimal da.
#
# ⚠️ DAS PORTFOLIO IST NICHT DIE MESSBASIS. Genau wie bei Krypto (523
# Messreihen gegen 43 Watchlist-Werte): der Querschnittsrang braucht
# mindestens 15 Symbole je Kalendertag. Mit zwei Aktien gibt es keinen
# Querschnitt, egal wie lang ihre Historie ist.
#
# Die Reihen kommen im BINANCE-KLINE-FORMAT zurueck ([ms, o, h, l, c, v]),
# damit `pruefe()` und der Schreibweg unveraendert gelten. Der
# Median-Abstand bleibt bei Boersentagen 1 (vier von fuenf Abstaenden je
# Woche sind ein Tag) - die Pruefung greift also auch hier.

YF_KLASSEN = ("aktien", "themen_etf", "rohstoffe")
YF_MIND_MARKTKAP = 2_000_000_000
# ⚠️ Handverlesen, weil es fuer Rohstoffe kein Screening gibt: das Universum
# IST klein. Das ist ein Befund, keine Nachlaessigkeit - siehe P6c im
# Gesamtplan (dort braucht es die Zeitreihenform statt des Querschnitts).
YF_ROHSTOFFE = (
    "GC=F", "SI=F", "PL=F", "PA=F", "HG=F", "CL=F", "BZ=F", "NG=F",
    "RB=F", "HO=F", "ZC=F", "ZS=F", "ZW=F", "ZL=F", "ZM=F", "KC=F",
    "SB=F", "CC=F", "CT=F", "OJ=F", "LE=F", "HE=F", "ZR=F", "LBS=F",
    "GLD", "SLV", "PPLT", "PALL", "CPER", "USO", "UNG", "DBA",
    "DBC", "GSG", "COMT", "PDBC", "BCI", "FTGC", "CMDY", "GCC")


def yf_universum(klasse: str, wieviele: int) -> list[str]:
    """Das Universum je Klasse - ueber die Schnittstelle, nicht handgepflegt."""
    import yfinance as yf
    if klasse == "rohstoffe":
        return list(YF_ROHSTOFFE)[:wieviele]
    if klasse == "aktien":
        q = yf.EquityQuery("and", [
            yf.EquityQuery("gte", ["intradaymarketcap", YF_MIND_MARKTKAP]),
            yf.EquityQuery("eq", ["region", "us"])])
        sortfeld = "intradaymarketcap"
    else:                                    # themen_etf
        # ⚠️⚠️ ETFQuery, NICHT EquityQuery (03.09.2026, N-19). Der Lauf
        # war deshalb abgestuerzt, nicht wegen der Datenlage: yfinance
        # fuehrt fuer ETFs eine EIGENE Query-Klasse
        # (`yfinance.screener.query.ETFQuery`), auch wenn das Feld
        # `fundnetassets` in beiden Klassen denselben Namen traegt -
        # `EquityQuery` kennt es schlicht nicht ("Invalid field").
        #
        # UND DER SORTFELD-FEHLER STAND DAHINTER, still: waere nur die
        # Query-Klasse getauscht worden, haette `sortField=
        # "intradaymarketcap"` (ein Aktienfeld) den naechsten Aufruf mit
        # HTTP 400 abgebrochen - derselbe Fehlertyp, eine Zeile spaeter.
        # Beide Felder gegen die echte Schnittstelle geprueft, nicht nur
        # gegen die Dokumentation.
        q = yf.ETFQuery("and", [
            yf.ETFQuery("gte", ["fundnetassets", 100_000_000]),
            yf.ETFQuery("eq", ["region", "us"])])
        sortfeld = "fundnetassets"
    holen, aus, versatz = yf.screen, [], 0
    while len(aus) < wieviele:
        try:
            r = holen(q, size=250, offset=versatz,
                      sortField=sortfeld, sortAsc=False)
        except Exception as exc:             # noqa: BLE001
            print("  ⚠️ Screening bei Versatz %d: %s" % (versatz, str(exc)[:90]))
            break
        z = r.get("quotes") or []
        if not z:
            break
        aus.extend(str(x.get("symbol")) for x in z if x.get("symbol"))
        versatz += len(z)
    # Reihenfolge stabil halten, Dubletten raus
    gesehen, sauber = set(), []
    for t in aus:
        if t not in gesehen:
            gesehen.add(t)
            sauber.append(t)
    return sauber[:wieviele]


def yf_hole_alles(ticker: str) -> list[tuple]:
    """Die volle Tageshistorie, im Binance-Kline-Format."""
    import yfinance as yf
    d = yf.Ticker(ticker).history(period="max", interval="1d",
                                  auto_adjust=False, actions=False)
    if d is None or d.empty:
        return []
    aus = []
    for stempel, z in d.iterrows():
        try:
            ms = int(stempel.timestamp() * 1000)
            o, h, l, c = (float(z["Open"]), float(z["High"]),
                          float(z["Low"]), float(z["Close"]))
            v = float(z.get("Volume") or 0.0)
        except Exception:                    # noqa: BLE001
            continue
        # ⚠️ NaN-Zeilen fliegen HIER raus, nicht in `pruefe`. Yahoo liefert
        # bei Handelspausen leere Zeilen; `pruefe` wuerde sie als
        # "unplausible Kerze" melden und die ganze Reihe verwerfen.
        if any(x != x for x in (o, h, l, c)) or min(o, h, l, c) <= 0:
            continue
        aus.append((ms, o, h, l, c, v))
    return aus


def main(argv: list[str] | None = None) -> int:
    """⚠️ `argv` seit 20.09.2026: der Tagesjob am Notebook ruft diese
    Funktion direkt auf, statt den Ablauf nachzubauen. Eine Kopie waere
    die naechste Stelle, die auseinanderlaeuft - und die stehende Vorgabe
    verlangt, dass der Test den ECHTEN Code ruft."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="data/messdaten.db")
    ap.add_argument("--schreiben", action="store_true",
                    help="ohne dies wird nur gezaehlt, nichts geschrieben")
    ap.add_argument("--nur", default="", help="Paare, kommagetrennt")
    ap.add_argument("--klasse", default="krypto",
                    help="krypto (Binance) oder aktien|themen_etf|rohstoffe "
                         "(yfinance). Das Portfolio ist NICHT die Messbasis.")
    ap.add_argument("--wieviele", type=int, default=500,
                    help="Obergrenze je Klasse bei den yfinance-Quellen")
    # ---- ⚠️ DER BETRIEBSMODUS (20.09.2026, Nutzerentscheidung C) -----
    ap.add_argument("--seit-letztem", action="store_true",
                    dest="seit_letztem",
                    help="nur die Kerzen seit dem juengsten gespeicherten "
                         "Datum holen - ein Aufruf je Paar statt drei")
    ap.add_argument("--behalte-tage", type=int, default=0,
                    dest="behalte_tage",
                    help="nach dem Schreiben alles Aeltere loeschen. "
                         "NUR zusammen mit --betriebskopie")
    ap.add_argument("--betriebskopie", action="store_true",
                    help="diese Datei ist eine BETRIEBSKOPIE und wird mit "
                         "`_nur_betrieb` markiert - Messungen brechen "
                         "darauf ab")
    ap.add_argument("--mindest", type=int, default=MIN_KERZEN,
                    help="Mindestkerzen je Reihe (Vorgabe %d, die "
                         "MESSgrenze). Der Betrieb braucht nur den "
                         "200-Tage-Schnitt" % MIN_KERZEN)
    ap.add_argument("--status", default="TRADING",
                    choices=("TRADING", "BREAK"),
                    help="TRADING sind die heute handelnden, BREAK die "
                         "EINGESTELLTEN - ohne sie ist jede Messung "
                         "ueberlebensverzerrt (Kapitel 120.3)")
    a = ap.parse_args(argv)
    # ⚠️⚠️ NICHT JEDES stdout LAESST SICH UMSTELLEN (20.09.2026, von der
    # eigenen Pruefsuite gefangen). Seit der Tagesjob `main()` direkt ruft,
    # laeuft diese Zeile auch dort, wo stdout ersetzt ist - in der Suite ein
    # Mitschnitt-Objekt, am Notebook moeglicherweise die Dienstumleitung.
    # `reconfigure` gibt es dort nicht, und der Job waere mit einem
    # AttributeError gestorben, bevor er eine Kerze geholt hat.
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

    # ⚠️ HARTE SPERRE. Ein Tippfehler im Pfad wuerde sonst 484 fremde Symbole
    # in die Produktionsdatenbank schreiben.
    if PRODUKTION in a.db.replace("\\", "/"):
        raise SystemExit(f"'{a.db}' ist die Produktionsdatenbank. Diese "
                         f"Messreihen gehoeren in eine eigene Datei.")

    # ---- ⚠️⚠️⚠️ NIEMAND KUERZT DIE MESSBASIS AUS VERSEHEN ------------
    #
    # `--behalte-tage 500` auf der vollen `messdaten.db` wuerde 4,3
    # Millionen Zeilen loeschen - unwiederbringlich, und die Befunde, die
    # darauf stehen, waeren nicht mehr reproduzierbar (R-R11). Deshalb
    # zwei Riegel statt eines Hinweises.
    if a.behalte_tage and not a.betriebskopie:
        raise SystemExit(
            "--behalte-tage kuerzt die Datei. Das ist nur fuer die "
            "BETRIEBSKOPIE gedacht - bitte zusammen mit --betriebskopie "
            "aufrufen, dann traegt die Datei auch die Marke.")
    if a.betriebskopie and os.path.exists(a.db):
        _c = sqlite3.connect("file:%s?mode=ro" % a.db, uri=True)
        _schon = ist_betriebskopie(_c)
        try:
            _n = _c.execute("SELECT COUNT(*) FROM "
                            "price_history_ohlc").fetchone()[0]
        except sqlite3.OperationalError:
            _n = 0
        _c.close()
        if not _schon and _n > 0:
            raise SystemExit(
                "'%s' enthaelt %d Zeilen und traegt KEINE Marke - das ist "
                "die volle Messbasis, keine Betriebskopie. Sie zu kuerzen "
                "waere unumkehrbar. Fuer die Betriebskopie einen eigenen "
                "Pfad angeben (--db)." % (a.db, _n))

    _yf = a.klasse in YF_KLASSEN
    s = None if _yf else requests.Session()
    if a.nur:
        liste = [x.strip() for x in a.nur.split(",") if x.strip()]
    elif _yf:
        print("Universum ueber die Schnittstelle holen (%s)..." % a.klasse,
              flush=True)
        liste = yf_universum(a.klasse, a.wieviele)
    else:
        liste = paare(s, a.status)
    print("=" * 78)
    print(f"BREITE MESSBASIS - {len(liste)} Reihen ({a.klasse}) -> {a.db}")
    print(f"  {'PROBELAUF, es wird nichts geschrieben' if not a.schreiben else 'schreibend'}")
    print("=" * 78)

    conn = None
    if a.schreiben:
        conn = sqlite3.connect(a.db)
        conn.executescript(SCHEMA)
        # ⚠️ Die Marke ZUERST - faellt der Lauf danach aus, ist die Datei
        # trotzdem als das gekennzeichnet, was sie ist.
        if a.betriebskopie:
            setze_marke(conn, a.behalte_tage, a.mindest)
            print("  ⚠️ BETRIEBSKOPIE - Marke `_nur_betrieb` gesetzt "
                  "(%d Tage, mindestens %d Kerzen). Messungen brechen auf "
                  "dieser Datei ab." % (a.behalte_tage, a.mindest))

    # ⚠️ Der Nachlauf braucht den Stand je Symbol - EINE Abfrage, nicht
    # eine je Paar.
    stand = letzte_tage(conn, a.klasse) if (conn is not None
                                            and a.seit_letztem) else {}
    if a.seit_letztem:
        print("  Nachlauf: %d Reihen haben schon einen Stand" % len(stand))

    jetzt = datetime.now(timezone.utc).isoformat()
    ok = zeilen = 0
    abgelehnt: list[tuple[str, str]] = []
    kollisionen: list[tuple[str, str, str]] = []
    t0 = time.time()
    for i, paar in enumerate(liste):
        sym = paar if _yf else paar[:-4]     # 'BTCUSDT' -> 'BTC'
        try:
            if a.seit_letztem and not _yf and sym in stand:
                # ⚠️ EINEN TAG ZURUECK: die letzte gespeicherte Kerze kann
                # von einem noch laufenden Tag stammen. Sie wird ohnehin
                # per INSERT OR REPLACE ueberschrieben.
                _ab = ((date.fromisoformat(stand[sym])
                        - timedelta(days=1)).toordinal()
                       - date(1970, 1, 1).toordinal()) * 86_400_000
                rohe = hole_ab(s, paar, _ab)
            elif a.seit_letztem and not _yf:
                # Neu in der Betriebskopie: nur so weit zurueck, wie sie
                # aufbewahrt - nicht die ganze Historie.
                _tage = a.behalte_tage or 500
                _ab = ((date.today() - timedelta(days=_tage)).toordinal()
                       - date(1970, 1, 1).toordinal()) * 86_400_000
                rohe = hole_ab(s, paar, _ab)
            else:
                rohe = yf_hole_alles(paar) if _yf else hole_alles(s, paar)
            # ⚠️⚠️ `pruefe()` GEHOERT IN DENSELBEN VERSUCH (03.09.2026,
            # N-19). Sie stand bisher AUSSERHALB des try/except - und war
            # damit der eigentliche Grund fuer den fruehen Absturz des
            # Aktien-Laufs. `_tag()` ruft `datetime.fromtimestamp()`; ein
            # einzelner kaputter Zeitstempel von yfinance (ein Symbol mit
            # unplausiblen Rohdaten, z.B. aus einer fehlerhaften Kerze vor
            # dem Boersengang) wirft dort unter Windows ein OSError
            # ("Invalid argument") - und das riss bisher den GESAMTEN Lauf
            # ab, statt nur dieses eine Symbol abzulehnen. Bei hunderten
            # Symbolen genuegt EINES mit einer schlechten Kerze.
            # ⚠️⚠️ DIE MINDESTLAENGE GILT DER REIHE, NICHT DEM
            # NACHLAUF (gefunden bei der Wirkungspruefung 20.09.).
            # Die erste Fassung gab `mindest` auch im Nachlauf
            # weiter - der holt zwei Kerzen, und alle sechs
            # Testreihen fielen als ,zu kurz` durch. Die
            # gespeicherte Reihe hat die Grenze beim ERSTEN Laden
            # bestanden; der Nachlauf muss nur plausibel sein.
            _mindest = 1 if (a.seit_letztem and sym in stand) \
                else a.mindest
            gut, grund = pruefe(rohe, paar, mindest=_mindest)
        except Exception as e:               # noqa: BLE001
            abgelehnt.append((sym, f"{type(e).__name__}"))
            continue
        if not gut:
            abgelehnt.append((sym, grund))
            continue
        ok += 1
        zeilen += len(rohe)
        if conn is not None:
            conn.executemany(
                "INSERT OR REPLACE INTO price_history_ohlc "
                "(symbol,assetklasse,currency,date,open,high,low,close,"
                "volume,fetched_at,quelle) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,'binance_mess')",
                [(sym, a.klasse, "USD", _tag(int(z[0])), float(z[1]),
                  float(z[2]), float(z[3]), float(z[4]), float(z[5]), jetzt)
                 for z in rohe])
            # ⚠️⚠️ NIE STILLSCHWEIGEND UMKLASSIFIZIEREN (03.09.2026, N-19).
            # `messreihen` bildet weiterhin symbol -> EINE Klasse ab (das
            # lesen alle Verbraucher ueber `klassen_aus_db()` so). Frueher
            # gewann per INSERT OR REPLACE stumm der LETZTE Lauf; jetzt
            # gewinnt der ERSTE, und eine Kollision wird als Fund
            # gezaehlt statt zu verschwinden.
            # ⚠️⚠️ SEIT DEM 13.09. IST EINE ZWEITE KLASSE KEINE
            # KOLLISION MEHR (Schritt 50 Teil A). Der Schluessel ist
            # (symbol, assetklasse); ein Ticker, den es als Aktie UND als
            # Kryptowaehrung gibt, bekommt ZWEI Zeilen statt einer, die
            # gewinnt. Das ist keine Nachsicht, sondern die Wahrheit:
            # DASH IST DoorDash und die Kryptowaehrung.
            #
            # ⚠️ GEZAEHLT WERDEN SIE WEITER - als DOPPELTICKER, nicht als
            # Fehler. Ein neuer gehoert angesehen, bevor er in eine
            # Messung geraet; nur ist er kein Grund mehr, eine Reihe
            # wegzuwerfen.
            _bisher = [r[0] for r in conn.execute(
                "SELECT assetklasse FROM messreihen WHERE symbol=?",
                (sym,))]
            if a.klasse not in _bisher:
                conn.execute("INSERT INTO messreihen VALUES (?,?)",
                             (sym, a.klasse))
                if _bisher:
                    kollisionen.append((sym, ", ".join(_bisher), a.klasse))
            eigene_klasse = a.klasse
            conn.execute("INSERT OR REPLACE INTO messreihen_status "
                         "VALUES (?,?,?)",
                         (sym, a.klasse, "eingestellt" if a.status == "BREAK"
                          else "handelnd"))
            conn.commit()
        if (i + 1) % 100 == 0:
            print(f"  {i + 1}/{len(liste)} nach {time.time() - t0:.0f} s - "
                  f"{ok} brauchbar, {zeilen} Kerzen", flush=True)

    print(f"\n  {ok} von {len(liste)} Reihen brauchbar, {zeilen} Kerzen, "
          f"{time.time() - t0:.0f} s")
    if abgelehnt:
        print(f"\n  {len(abgelehnt)} abgelehnt - die Gruende, gezaehlt:")
        zaehl: dict = {}
        for _sym, grund in abgelehnt:
            schluessel = ("zu kurz" if "Kerzen" in grund else grund)
            zaehl[schluessel] = zaehl.get(schluessel, 0) + 1
        for grund, n in sorted(zaehl.items(), key=lambda x: -x[1]):
            print(f"    {n:4}  {grund}")
    if kollisionen:
        print(f"\n  ⚠️ {len(kollisionen)} Symbol-Kollisionen - Klasse "
              f"NICHT umgestellt (das Symbol gehoert bereits einer anderen "
              f"Klasse, die Kerzen wurden trotzdem getrennt gespeichert):")
        for sym, alt, neu in kollisionen:
            print(f"    {sym}: bleibt {alt}, wollte {neu}")
    if conn is not None and a.behalte_tage:
        _weg = kuerze(conn, a.klasse, a.behalte_tage)
        print(f"\n  gekuerzt auf {a.behalte_tage} Tage - "
              f"{_weg} alte Zeilen geloescht")
    if conn is not None:
        conn.close()
        print(f"\n  geschrieben nach {a.db}")
    else:
        print("\n  PROBELAUF - nichts geschrieben. Mit --schreiben wiederholen.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
