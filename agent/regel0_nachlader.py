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


def betrieb_erlaubt(ordner: str) -> tuple[bool, str]:
    """Darf der STUNDENJOB in diesem Ordner schreiben? (S7-1b, 02.10.)

    Nur am BETRIEBSGERAET. Erkannt an einem Zustand, den es nur dort gibt (CLAUDE.md, *12 KB sind der SOLLZUSTAND*):
    ``terminmarkt_historie.db`` traegt die Marke ``_nur_symbolliste``. Am Desktop ist sie voll - dort liegen unter denselben
    Namen die MESSBASEN, und die aendern sich nur von Hand (``hole_*.py``), sonst ist keine Messung reproduzierbar (R-R11).
    Kein Geraetename, keine Aufzaehlung. Gelesen nur mit ``mode=ro``. Im Zweifel NEIN.
    Der Aufruf von Hand (``--ordner <kopie>``) ist davon nicht betroffen."""
    p = os.path.join(ordner, "terminmarkt_historie.db")
    if not os.path.exists(p):
        return False, "terminmarkt_historie.db fehlt - Geraet nicht erkannt"
    try:
        c = sqlite3.connect("file:%s?mode=ro" % p.replace("\\", "/"), uri=True, timeout=5)
        try:
            marke = c.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='_nur_symbolliste'").fetchone()
        finally:
            c.close()
    except sqlite3.Error as ex:
        return False, "terminmarkt_historie.db nicht lesbar (%s)" % ex
    if not marke:
        return False, "volle Messbasis (Desktop) - dort schreiben nur die hole_*.py von Hand"
    fehlt = [d for d in DATEIEN if not os.path.exists(os.path.join(ordner, d))]
    if fehlt:
        return False, "REGEL0-Datenbasis unvollstaendig, es fehlt: %s" % ", ".join(fehlt)
    return True, "Betriebsgeraet (terminmarkt_historie.db nur Symbolliste), vier Dateien vorhanden"


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


# ══ S7-5a: NEUAUFNAHME neu gelisteter Assets (E-40 *alles, was Binance fuehrt*; Voranalyse_Schritt7 Par. 16, F-1/F-4) ══════════
NEU_AB = "2023-01-01 00:00"          # wie die Erstbefuellung (hole_stundenkurse_alle.AB)
NEU_VERSUCHE = 3                     # gemessen 03.10.: 2 von 3 Laeufen von universum() liefen am Desktop in Zeitgrenzen


def _universum_mit_wiederholung(ausgabe=print):
    """Die Auswahlregel der Erstbefuellung (``hole_stundenkurse_alle.universum``) - EINE Regel, keine Liste - mit Wiederholung."""
    import hole_stundenkurse_alle as H
    letzter = None
    for v in range(NEU_VERSUCHE):
        try:
            return H.universum()
        except requests.RequestException as ex:
            letzter = ex
            ausgabe("  Neuaufnahme: Binance nicht erreichbar (Versuch %d/%d: %s)" % (v + 1, NEU_VERSUCHE, type(ex).__name__))
            time.sleep(20)
    raise letzter


def neuaufnahme(ordner: str, ausgabe=print, universum=None) -> dict:
    """Neu gelistete Binance-Assets in ``stundenkurse_alle.db`` (und ihren Markpreis in ``markpreis_alle.db``) aufnehmen.

    Neu ist, was die Regel heute ergibt und in der Datei noch fehlt. Je Asset wird die GANZE Historie ab dem Listing (fruehestens
    2023) geholt, nur abgeschlossene Stunden, und erst DANACH eingetragen (Kerzen und ``_quelle`` in einer Transaktion) - ein
    Aussetzer hinterlaesst nichts Halbes, das Asset wird beim naechsten Lauf wieder versucht. Nie in die Messbasis
    (``universum`` nimmt die Messbasis aus; Grundgesamtheit). Bewertet, nicht trainiert. ``universum`` nur fuer die Probe."""
    jetzt = int(time.time() * 1000)
    aus, _ns, _nf, _nm = (universum or (lambda: _universum_mit_wiederholung(ausgabe)))()
    pa = _pruefe_ziel(ordner, "stundenkurse_alle.db")
    pm = _pruefe_ziel(ordner, "markpreis_alle.db")
    ca = sqlite3.connect(pa, timeout=30)
    da = {r[0] for r in ca.execute("SELECT symbol FROM _quelle")}
    neu = [(b, m_, p_) for b, m_, p_ in aus if b not in da]
    bericht = dict(regel=len(aus), datei=len(da), neu=[], fehler=[], markpreis=[])
    if not neu:
        ca.execute("CREATE TABLE IF NOT EXISTS _neuaufnahme (lauf_am TEXT, regel INTEGER, datei INTEGER, neu TEXT, fehler TEXT)")
        ca.execute("INSERT INTO _neuaufnahme VALUES (?,?,?,?,?)", (_stunde(jetzt), len(aus), len(da), "", ""))
        ca.commit(); ca.close()
        ausgabe("  Neuaufnahme: Regel %d Assets, Datei %d - nichts Neues" % (len(aus), len(da)))
        return bericht
    _sp, fu = _im_handel()
    cm = sqlite3.connect(pm, timeout=30)
    try:
        for b, markt, paar in neu:
            url = SPOT[1] if markt == "spot" else FUT[1]
            try:
                k = _hole(url, paar, _ms(NEU_AB), jetzt)
                if not k:
                    raise ValueError("keine Kerzen")
                # Markpreis: das eigene Paar (Faktor 1), sonst das 1000er (Faktor 1000) - wie hole_markpreis.lade
                mp, mpaar, mfak = [], None, None
                for p_, f_ in ((paar, 1.0), ("1000" + paar, 1000.0)):
                    if p_ in fu:
                        mp = _hole(MARK, p_, _ms(NEU_AB), jetzt)
                        if mp:
                            mpaar, mfak = p_, f_
                            break
            except Exception as ex:                                     # noqa: BLE001
                bericht["fehler"].append("%s: %s" % (b, str(ex)[:60]))
                ausgabe("  ⚠️ Neuaufnahme %s: %s - naechster Lauf versucht es wieder" % (b, str(ex)[:80]))
                continue
            with ca:                                                    # EINE Transaktion: alles oder nichts
                ca.executemany("INSERT OR REPLACE INTO stundenkurse VALUES (?,?,?,?,?,?,?)",
                               [(b, _stunde(int(x[0])), float(x[1]), float(x[2]), float(x[3]), float(x[4]), float(x[5])) for x in k])
                ca.execute("INSERT OR REPLACE INTO _quelle VALUES (?,?,?,?)", (b, markt, paar, _stunde(jetzt)))
            if mp:
                with cm:
                    cm.executemany("INSERT OR REPLACE INTO markpreis VALUES (?,?,?,?,?,?,?,?)",
                                   [(b, _stunde(int(x[0])), float(x[1]), float(x[2]), float(x[3]), float(x[4]), mpaar, mfak) for x in mp])
                bericht["markpreis"].append(b)
            bericht["neu"].append("%s(%s, %d h ab %s)" % (b, markt, len(k), _stunde(int(k[0][0]))))
            ausgabe("  Neuaufnahme: %s %s %s - %d Stunden ab %s%s" % (b, markt, paar, len(k), _stunde(int(k[0][0])),
                                                                    ", Markpreis %s" % mpaar if mp else ", ohne Markpreis"))
    finally:
        cm.close()
    ca.execute("CREATE TABLE IF NOT EXISTS _neuaufnahme (lauf_am TEXT, regel INTEGER, datei INTEGER, neu TEXT, fehler TEXT)")
    ca.execute("INSERT INTO _neuaufnahme VALUES (?,?,?,?,?)", (_stunde(jetzt), len(aus), len(da), ", ".join(bericht["neu"]), " | ".join(bericht["fehler"])))
    ca.commit(); ca.close()
    return bericht


def neuaufnahme_faellig(ordner: str, jetzt_utc: datetime | None = None, stunde: int = 2) -> bool:
    """Taeglich ab ``stunde`` UTC (F-4), einmal je Tag - auch nachgeholt, wenn die App zur Stunde nicht lief."""
    jetzt_utc = jetzt_utc or datetime.now(timezone.utc)
    if jetzt_utc.hour < stunde:
        return False
    try:
        c = sqlite3.connect("file:%s?mode=ro" % os.path.join(ordner, "stundenkurse_alle.db").replace("\\", "/"), uri=True)
        try:
            r = c.execute("SELECT MAX(lauf_am) FROM _neuaufnahme").fetchone()
        finally:
            c.close()
    except sqlite3.Error:
        return True                       # Tabelle gibt es noch nicht - also nie gelaufen
    return not (r and r[0] and r[0][:10] == jetzt_utc.strftime("%Y-%m-%d"))


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
