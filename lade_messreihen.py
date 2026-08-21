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
import sqlite3
import sys
import time
from datetime import datetime, timezone

import requests

EXCHANGE_INFO = "https://api.binance.com/api/v3/exchangeInfo"
KLINES = "https://api.binance.com/api/v3/klines"
MAX_KERZEN = 1000
MIN_KERZEN = 400
PRODUKTION = "data/tradinginfotool.db"
KLASSE = "krypto"

SCHEMA = """
CREATE TABLE IF NOT EXISTS price_history_ohlc (
    symbol TEXT NOT NULL, currency TEXT NOT NULL, date TEXT NOT NULL,
    open REAL NOT NULL, high REAL NOT NULL, low REAL NOT NULL,
    close REAL NOT NULL, volume REAL NOT NULL, fetched_at TEXT NOT NULL,
    quelle TEXT NOT NULL DEFAULT 'binance_mess',
    PRIMARY KEY (symbol, currency, date));
CREATE TABLE IF NOT EXISTS messreihen (
    symbol TEXT PRIMARY KEY, assetklasse TEXT NOT NULL);
"""


def _tag(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).date().isoformat()


def paare(s: requests.Session) -> list[str]:
    r = s.get(EXCHANGE_INFO, params={"permissions": "SPOT"}, timeout=30)
    r.raise_for_status()
    return sorted(x["symbol"] for x in r.json()["symbols"]
                  if x["quoteAsset"] == "USDT" and x["status"] == "TRADING")


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


def pruefe(rohe: list[tuple], paar: str) -> tuple[bool, str]:
    """⚠️ Eine Quelle, die sich nicht selbst prueft, verlaesst sich darauf,
    dass eine spaetere Stufe ihren Fehler faengt."""
    if len(rohe) < MIN_KERZEN:
        return False, f"nur {len(rohe)} Kerzen"
    tage = [_tag(int(z[0])) for z in rohe]
    if len(set(tage)) != len(tage):
        return False, "doppelte Daten"
    from datetime import date
    dt = [date.fromisoformat(x) for x in tage]
    ab = sorted((dt[i + 1] - dt[i]).days for i in range(len(dt) - 1))
    if ab[len(ab) // 2] != 1:
        return False, f"Median-Abstand {ab[len(ab) // 2]} Tage"
    for z in rohe:
        o, h, l, c = float(z[1]), float(z[2]), float(z[3]), float(z[4])
        if not (h >= l and min(o, h, l, c) > 0):
            return False, f"unplausible Kerze am {_tag(int(z[0]))}"
    return True, ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="data/messdaten.db")
    ap.add_argument("--schreiben", action="store_true",
                    help="ohne dies wird nur gezaehlt, nichts geschrieben")
    ap.add_argument("--nur", default="", help="Paare, kommagetrennt")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    # ⚠️ HARTE SPERRE. Ein Tippfehler im Pfad wuerde sonst 484 fremde Symbole
    # in die Produktionsdatenbank schreiben.
    if PRODUKTION in a.db.replace("\\", "/"):
        raise SystemExit(f"'{a.db}' ist die Produktionsdatenbank. Diese "
                         f"Messreihen gehoeren in eine eigene Datei.")

    s = requests.Session()
    liste = ([x.strip() for x in a.nur.split(",") if x.strip()] if a.nur
             else paare(s))
    print("=" * 78)
    print(f"BREITE MESSBASIS - {len(liste)} USDT-Spotpaare -> {a.db}")
    print(f"  {'PROBELAUF, es wird nichts geschrieben' if not a.schreiben else 'schreibend'}")
    print("=" * 78)

    conn = None
    if a.schreiben:
        conn = sqlite3.connect(a.db)
        conn.executescript(SCHEMA)

    jetzt = datetime.now(timezone.utc).isoformat()
    ok = zeilen = 0
    abgelehnt: list[tuple[str, str]] = []
    t0 = time.time()
    for i, paar in enumerate(liste):
        sym = paar[:-4]                      # 'BTCUSDT' -> 'BTC'
        try:
            rohe = hole_alles(s, paar)
        except Exception as e:               # noqa: BLE001
            abgelehnt.append((sym, f"{type(e).__name__}"))
            continue
        gut, grund = pruefe(rohe, paar)
        if not gut:
            abgelehnt.append((sym, grund))
            continue
        ok += 1
        zeilen += len(rohe)
        if conn is not None:
            conn.executemany(
                "INSERT OR REPLACE INTO price_history_ohlc "
                "(symbol,currency,date,open,high,low,close,volume,"
                "fetched_at,quelle) VALUES (?,?,?,?,?,?,?,?,?,'binance_mess')",
                [(sym, "USD", _tag(int(z[0])), float(z[1]), float(z[2]),
                  float(z[3]), float(z[4]), float(z[5]), jetzt)
                 for z in rohe])
            conn.execute("INSERT OR REPLACE INTO messreihen VALUES (?,?)",
                         (sym, KLASSE))
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
    if conn is not None:
        conn.close()
        print(f"\n  geschrieben nach {a.db}")
    else:
        print("\n  PROBELAUF - nichts geschrieben. Mit --schreiben wiederholen.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
