"""Nachlader der REGEL0-Datenbasis im Betrieb (Schritt 7, S7-1; Voranalyse_Schritt7_Betrieb_02_10.md, E-42).

Haelt die vier Dateien stuendlich aktuell, die per USB ans Notebook kamen:

    stundenkurse.db         Messbasis 116 (Spot)           -> api/v3/klines            Symbole aus der Datei selbst
    stundenkurse_alle.db    alle uebrigen (Spot/Futures)   -> klines je _quelle.markt  Markt und Paar aus _quelle
    markpreis_historie.db   Markpreis der Messbasis        -> fapi/v1/markPriceKlines  Paar und Faktor aus der letzten Zeile
    markpreis_alle.db       Markpreis der uebrigen         -> fapi/v1/markPriceKlines

Je Symbol wird AB DER LETZTEN GESPEICHERTEN STUNDE nachgeladen (die wird neu geholt und ueberschrieben - Lehre 25.09.: die letzte
Kerze war beim Laden offen). Gespeichert werden NUR ABGESCHLOSSENE Stunden. Paare, die nicht mehr gehandelt werden, werden uebersprungen
und gezaehlt (die Historie bleibt). Ein Lauf, der abbricht, ist beim naechsten Lauf ohne Luecke fortgesetzt.

⚠️ Warum ein eigener Lader und nicht hole_stundenkurse.py: der leitet Symbole und Spannen aus terminmarkt_historie.db ab, und die liegt
am Notebook nur als Symbolliste (Sollzustand) - er waere dort nicht lauffaehig.

SCHUTZ: schreibt nur in die vier genannten Dateien im angegebenen Ordner; verweigert jede andere Datei (auch tradinginfotool.db).
Tests laufen gegen Wegwerfkopien (``--ordner``), nie gegen die Vorgabe.

    python -m agent.regel0_nachlader --ordner data                     # ein Lauf (im Betrieb stuendlich)
    python -m agent.regel0_nachlader --ordner <kopie> --symbole BTC,HYPE  # Probe auf einer Kopie
"""
from __future__ import annotations

import os
import sqlite3
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

import requests

SPOT = ("https://api.binance.com/api/v3/exchangeInfo", "https://api.binance.com/api/v3/klines")
FUT = ("https://fapi.binance.com/fapi/v1/exchangeInfo", "https://fapi.binance.com/fapi/v1/klines")
MARK = "https://fapi.binance.com/fapi/v1/markPriceKlines"
DATEIEN = ("stundenkurse.db", "stundenkurse_alle.db", "markpreis_historie.db", "markpreis_alle.db")
H_MS = 3_600_000
DATEN_VORGABE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
PAUSE_S = 0.05
# Abfragen PARALLEL (gemessen 02.10.: nacheinander dauerte ein normaler Stundenlauf ueber 10 min - die Wartezeit je Abfrage, nicht die Last).
# Geschrieben wird weiter nacheinander im Hauptfaden. Das Binance-Gewicht wird an den Antwortkoepfen ueberwacht.
ARBEITER = 8
GRENZE_GEWICHT = {"api.binance.com": 6000, "fapi.binance.com": 2400}     # je Minute
_lokal = threading.local()


def _sitzung():
    if not hasattr(_lokal, "s"):
        _lokal.s = requests.Session()
    return _lokal.s


def _bremse(url, antwort):
    """Ab 70 % des Minutengewichts kurz warten - schuetzt vor 429/418 (Sperre der IP)."""
    host = url.split("/")[2]
    try:
        benutzt = int(antwort.headers.get("x-mbx-used-weight-1m") or 0)
    except ValueError:
        return
    if benutzt > 0.7 * GRENZE_GEWICHT.get(host, 1200):
        time.sleep(5)


def _ms(stunde: str) -> int:
    return int(datetime.strptime(stunde, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc).timestamp() * 1000)


def _stunde(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M")


def _im_handel():
    sp = {x["symbol"] for x in requests.get(SPOT[0], timeout=30).json()["symbols"] if x["status"] == "TRADING"}
    fu = {x["symbol"] for x in requests.get(FUT[0], timeout=30).json()["symbols"] if x["status"] == "TRADING"}
    return sp, fu


def _hole(url: str, paar: str, start_ms: int, jetzt_ms: int) -> list:
    """Alle ABGESCHLOSSENEN Stundenkerzen ab start_ms. Kleine Abfragen kleines limit (Gewicht), Wartezeit bei 418/429."""
    aus = []
    while start_ms + H_MS <= jetzt_ms:
        noetig = (jetzt_ms - start_ms) // H_MS + 1
        lim = int(min(max(noetig, 2), 1000))
        r = _sitzung().get(url, params={"symbol": paar, "interval": "1h", "startTime": start_ms, "limit": lim}, timeout=30)
        _bremse(url, r)
        if r.status_code in (418, 429):
            time.sleep(60)
            continue
        r.raise_for_status()
        k = r.json()
        if not k:
            break
        aus.extend(x for x in k if int(x[0]) + H_MS <= jetzt_ms)       # nur abgeschlossene Stunden
        neu = int(k[-1][0]) + H_MS
        if neu <= start_ms:
            break
        start_ms = neu
        time.sleep(PAUSE_S)
    return aus


def _pruefe_ziel(ordner: str, name: str) -> str:
    if name not in DATEIEN:
        raise SystemExit("⛔ verweigert: %s gehoert nicht zur REGEL0-Datenbasis" % name)
    p = os.path.join(ordner, name)
    if os.path.basename(p).lower() == "tradinginfotool.db":
        raise SystemExit("⛔ verweigert: Produktionsdatei")
    if not os.path.exists(p):
        raise SystemExit("⛔ %s fehlt (erst die Historie uebertragen, pruefe_uebertragung.py)" % p)
    return p


def lauf(ordner: str, symbole: set | None = None, ausgabe=print) -> dict:
    jetzt = int(time.time() * 1000)
    sp, fu = _im_handel()
    bericht = {}
    for name in DATEIEN:
        p = _pruefe_ziel(ordner, name)
        c = sqlite3.connect(p)
        ist_mark = name.startswith("markpreis")
        tab = "markpreis" if ist_mark else "stundenkurse"
        stand = {s: m for s, m in c.execute("SELECT symbol, MAX(stunde) FROM %s GROUP BY symbol" % tab)}
        if ist_mark:
            ziel = {s: c.execute("SELECT paar, faktor FROM markpreis WHERE symbol=? AND stunde=?", (s, m)).fetchone() for s, m in stand.items()}
        elif name == "stundenkurse_alle.db":
            ziel = {s: (p_, mk) for s, mk, p_ in c.execute("SELECT symbol, markt, paar FROM _quelle")}
        else:
            ziel = {s: (s + "USDT", "spot") for s in stand}
        neu = ersetzt = ausser = fehler = 0
        auftraege = []
        for s in sorted(stand):
            if symbole and s not in symbole:
                continue
            if ist_mark:
                paar, faktor = ziel[s]
                url, handel = MARK, paar in fu
            else:
                paar, markt = ziel.get(s, (s + "USDT", "spot"))
                faktor = None
                url, handel = (SPOT[1], paar in sp) if markt == "spot" else (FUT[1], paar in fu)
            if not handel:
                ausser += 1
                continue
            auftraege.append((s, url, paar, faktor))

        def _einer(a_):
            try:
                return a_, _hole(a_[1], a_[2], _ms(stand[a_[0]]), jetzt), None
            except Exception as ex:                                     # noqa: BLE001
                return a_, None, ex
        with ThreadPoolExecutor(max_workers=ARBEITER) as pool:
            ergebnisse = list(pool.map(_einer, auftraege))
        for (s, url, paar, faktor), k, ex in ergebnisse:
            if ex is not None:
                fehler += 1
                ausgabe("  ⚠️ %s %s: %s" % (name, s, str(ex)[:80]))
                continue
            if not k:
                continue
            if ist_mark:
                zeilen = [(s, _stunde(int(x[0])), float(x[1]), float(x[2]), float(x[3]), float(x[4]), paar, faktor) for x in k]
                c.executemany("INSERT OR REPLACE INTO markpreis VALUES (?,?,?,?,?,?,?,?)", zeilen)
            else:
                zeilen = [(s, _stunde(int(x[0])), float(x[1]), float(x[2]), float(x[3]), float(x[4]), float(x[5])) for x in k]
                c.executemany("INSERT OR REPLACE INTO stundenkurse VALUES (?,?,?,?,?,?,?)", zeilen)
            ersetzt += sum(1 for z in zeilen if z[1] <= stand[s])
            neu += sum(1 for z in zeilen if z[1] > stand[s])
            c.commit()
        c.execute("CREATE TABLE IF NOT EXISTS _nachlader (lauf_am TEXT, neue_stunden INTEGER, ersetzt INTEGER, "
                  "nicht_im_handel INTEGER, fehler INTEGER)")
        c.execute("INSERT INTO _nachlader VALUES (?,?,?,?,?)", (datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"), neu, ersetzt, ausser, fehler))
        c.commit()
        hoch = c.execute("SELECT MAX(stunde) FROM %s" % tab).fetchone()[0]
        c.close()
        bericht[name] = dict(neue_stunden=neu, ersetzt=ersetzt, nicht_im_handel=ausser, fehler=fehler, bis=hoch)
        ausgabe("  %-24s neue Stunden %7d · ersetzt %5d · nicht im Handel %3d · Fehler %d · bis %s" % (name, neu, ersetzt, ausser, fehler, hoch))
    return bericht


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:                                         # noqa: BLE001
        pass
    a = sys.argv
    ordner = a[a.index("--ordner") + 1] if "--ordner" in a else DATEN_VORGABE
    sym = set(a[a.index("--symbole") + 1].split(",")) if "--symbole" in a else None
    t0 = time.time()
    print("REGEL0-NACHLADER · Ordner %s%s" % (os.path.abspath(ordner), (" · nur %s" % ",".join(sorted(sym))) if sym else ""))
    b = lauf(ordner, sym)
    print("FERTIG in %.0f s · Fehler gesamt %d" % (time.time() - t0, sum(x["fehler"] for x in b.values())))
    return 0 if not sum(x["fehler"] for x in b.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
