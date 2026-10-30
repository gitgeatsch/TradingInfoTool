# -*- coding: utf-8 -*-
"""DIE QUELLEN DER SICHTEN S1–S4, S7 — ein Abrufer für Historie UND laufenden Stand (G4, Weg A, Nutzer 29.10.2026).

Nutzer 29.10.: *„ok A wie empfohlen“* — je Quelle EIN Abrufer. Jetzt lädt er am Desktop die Historie ab 2023 (Grundlage für den
Messplan G7); am NB wird DERSELBE Abrufer erst mit dem Bau (G8) eingeschaltet (Regel *Desktop zuerst*, Gesamtplan §6).

    python -X utf8 -m api.sichten_quellen --historie          # ab 2023 laden bzw. fortsetzen (Desktop)
    python -X utf8 -m api.sichten_quellen --laufend           # die letzten 14 Tage (später der Job am NB)
    python -X utf8 -m api.sichten_quellen --stand             # Bestand je Quelle
    ... --quelle yfinance --ablage <pfad>                     # eine Quelle / eine andere Datei (Wegwerf beim Nachweis)

⚠️⚠️ ÜBERGABEREGEL Ü8 — gleiche Form live und im Rückspiel. Deshalb gibt es KEINEN eigenen Historien-Weg: ``--laufend`` ist
dieselbe Funktion mit einem späteren Start. Der Desktop-Nachweis (``Rechenkern_02_10/g4_nachweis_sichtenquellen.py``) vergleicht
beide Wege auf den gemeinsamen Tagen.

⚠️⚠️ KEIN VORGRIFF. Jede Zeile trägt ``bekannt_ab`` (UTC) — den Zeitpunkt, ab dem der Wert öffentlich war:

    yfinance       Tagesschluss der Börse, vorsichtig 22:00 UTC am Beobachtungstag (US-Schluss inkl. Winterzeit)
    FRED/ALFRED    Folgetag 00:00 UTC nach dem Veröffentlichungstag ``realtime_start`` — revidierte Werte bekommen eine EIGENE
                   Zeile (``bis`` = Ende ihrer Gültigkeit), das Rückspiel nimmt den damals bekannten Wert
    Krypto-Tage    Kerzen in UTC: 00:00 UTC des Folgetags
    GDELT-Ton      00:00 UTC des Folgetags

⚠️ Ablage ``data/_sichten/sichten.db`` (nicht versioniert). NIE ``data/tradinginfotool.db``. Jeder Abruf steht in ``lauf`` —
ein Fehlschlag ist nie still (Lehre E-1: eine gescheiterte Abfrage ist keine leere Reihe).
"""
from __future__ import annotations

import html
import os
import re
import sqlite3
import sys
import time
from datetime import date, datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

import requests

PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ABLAGE = os.path.join(PROJ, "data", "_sichten", "sichten.db")
START = "2023-01-01"            # Messfokus ab 2023 (2022 nur Auskunft)
FRED_BEOBACHTUNG_AB = "2018-01-01"   # Einordnung im 5-J-Fenster braucht Vorlauf vor 2023
LAUFEND_TAGE = 14
# GDELT (Nutzer 30.10.: a): zwischen zwei GDELT-Abfragen 10 Minuten; bei einer Sperre EIN zweiter Versuch, dann gilt der Tag als
# Quellausfall und der naechste Lauf setzt fort. Am 29.10. haben 5 Wiederholungen je Fenster die Sperre ueber Stunden verlaengert.
GDELT_ABSTAND_S = 600
H = {"User-Agent": "Mozilla/5.0 TradingInfoTool-Sichten"}

# Sicht -> Kürzel. Börsenkurse ohne Revision, deshalb fürs Rückspiel geeignet (Voranalyse_Luecken A1)
YFINANCE = {"^GSPC": "S3", "^NDX": "S3", "SOXX": "S3", "^VIX": "S3", "^MOVE": "S3",
            "DX-Y.NYB": "S4", "GC=F": "S4", "BZ=F": "S4", "HG=F": "S4"}
# K1–K9 wie agent/makro_lage.REIHEN, dazu HY-Aufschlag und 10J — hier als JAHRGÄNGE (ALFRED) statt mit festem Verzug
FRED = {"M2SL": "S2", "WALCL": "S2", "WTREGEN": "S2", "RRPONTSYD": "S2", "DFII10": "S2", "DGS2": "S2", "DGS10": "S2",
        "T10Y2Y": "S2", "BAA10Y": "S3", "BAMLH0A0HYM2": "S3", "NFCI": "S3", "DTWEXBGS": "S4", "VIXCLS": "S3"}
KRYPTO = ("BTC", "ETH")
GDELT = {"krypto": "(bitcoin OR cryptocurrency) sourcelang:english", "fed": '"federal reserve" sourcelang:english',
         "aktien": '"stock market" sourcelang:english', "konflikt": "(war OR sanctions OR tariffs) sourcelang:english"}
FEEDS = {"cointelegraph": "cointelegraph.com/rss", "coindesk": "coindesk.com/arc/outboundfeeds/rss/", "decrypt": "decrypt.co/feed",
         "cryptoslate": "cryptoslate.com/feed/", "theblock": "www.theblock.co/rss.xml", "bitcoinist": "bitcoinist.com/feed/",
         "coingape": "coingape.com/feed/", "cryptopotato": "cryptopotato.com/feed/", "dailyhodl": "dailyhodl.com/feed/"}   # wie p65


def _jetzt() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _folgetag(d: str) -> str:
    return (date.fromisoformat(d[:10]) + timedelta(days=1)).isoformat() + "T00:00:00+00:00"


def _ms(d: str) -> int:
    return int(datetime.fromisoformat(d[:10]).replace(tzinfo=timezone.utc).timestamp() * 1000)


def _tag(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000, timezone.utc).strftime("%Y-%m-%d")


def verbinde(pfad: str = ABLAGE) -> sqlite3.Connection:
    if os.path.basename(pfad) == "tradinginfotool.db":
        raise SystemExit("sichten_quellen schreibt NIE in die Produktions-DB")
    os.makedirs(os.path.dirname(pfad), exist_ok=True)
    c = sqlite3.connect(pfad)
    c.executescript("""
        CREATE TABLE IF NOT EXISTS reihe (quelle TEXT, symbol TEXT, datum TEXT, wert REAL, bekannt_ab TEXT, bis TEXT, geholt TEXT,
                                          PRIMARY KEY (quelle, symbol, datum, bekannt_ab));
        CREATE TABLE IF NOT EXISTS lauf (quelle TEXT, symbol TEXT, ts TEXT, status TEXT, n INTEGER);
        CREATE TABLE IF NOT EXISTS meldung (feed TEXT, schluessel TEXT, titel TEXT, link TEXT, pub_utc TEXT, beschreibung TEXT,
                                            aufnahme_ts TEXT, PRIMARY KEY (feed, schluessel));""")
    return c


def _hole(url, params=None, versuche=4, pause=10):
    for v in range(versuche):
        try:
            r = requests.get(url, params=params, headers=H, timeout=60)
            if r.status_code == 200:
                return r
        except requests.RequestException:
            pass
        time.sleep(pause * (v + 1))
    return None


def _schreibe(c, quelle, symbol, zeilen, status="ok"):
    """zeilen: (datum, wert, bekannt_ab, bis)."""
    g = _jetzt()
    c.executemany("INSERT OR REPLACE INTO reihe VALUES (?,?,?,?,?,?,?)", [(quelle, symbol, d, w, b, bis, g) for d, w, b, bis in zeilen])
    c.execute("INSERT INTO lauf VALUES (?,?,?,?,?)", (quelle, symbol, g, status, len(zeilen)))
    c.commit()
    return len(zeilen)


def _fehler(c, quelle, symbol, was):
    c.execute("INSERT INTO lauf VALUES (?,?,?,?,?)", (quelle, symbol, _jetzt(), "FEHLER " + str(was)[:200], 0))
    c.commit()
    print("  ✖ %s %s: %s" % (quelle, symbol, str(was)[:160]), flush=True)


# ══ die Abrufer — jeder mit start, sonst nichts ═══════════════════════════════════════════════════════════════════════════
def yfinance_reihe(ticker: str, start: str) -> list:
    import yfinance as yf
    h = yf.Ticker(ticker).history(start=start, interval="1d", auto_adjust=False)
    h = h[h["Close"].notna()]
    heute = datetime.now(timezone.utc).strftime("%Y-%m-%d")   # ⚠️ die Kerze des laufenden Tages ist nicht abgeschlossen
    return [(ts.strftime("%Y-%m-%d"), float(v), ts.strftime("%Y-%m-%d") + "T22:00:00+00:00", None) for ts, v in h["Close"].items()
            if ts.strftime("%Y-%m-%d") < heute]


def fred_jahrgaenge(series_id: str, realtime_start: str, key: str) -> list:
    """Alle Jahrgänge seit ``realtime_start``. Eine Zeile je (Beobachtung, Gültigkeitsbeginn) — die Revision bleibt sichtbar."""
    aus, offset = [], 0
    while True:
        r = _hole("https://api.stlouisfed.org/fred/series/observations",
                  {"series_id": series_id, "api_key": key, "file_type": "json", "observation_start": FRED_BEOBACHTUNG_AB,
                   "realtime_start": realtime_start, "realtime_end": "9999-12-31", "limit": 100000, "offset": offset})
        if r is None:
            raise RuntimeError("FRED %s nicht abrufbar (offset %d)" % (series_id, offset))
        obs = r.json().get("observations", [])
        for o in obs:
            if o["value"] in (".", ""):
                continue
            bis = None if o["realtime_end"] == "9999-12-31" else o["realtime_end"]
            # ⚠️ nie vor dem Ende des Beobachtungstags: ALFRED fuehrt VIXCLS an US-Feiertagen mit einem Gueltigkeitsbeginn VOR dem
            # Tag (29.10.: 26 Zeilen, z. B. 16.01.2023 ab 14.01.) - ohne die Kappung waere das ein Vorgriff (N3)
            aus.append((o["date"], float(o["value"]), _folgetag(max(o["realtime_start"], o["date"])), bis))
        if len(obs) < 100000:
            return aus
        offset += 100000


def _binance_tage(url, params, start):
    aus, ab = {}, _ms(start)
    while True:
        r = _hole(url, dict(params, startTime=ab, limit=1000 if "api/v3" in url else 500))
        if r is None:
            raise RuntimeError("Binance %s nicht abrufbar ab %s" % (params, _tag(ab)))
        k = r.json()
        for x in k:
            aus[_tag(x[0])] = float(x[4])
        if len(k) < (1000 if "api/v3" in url else 500):
            return aus
        ab = k[-1][0] + 86400000


def coinbase_praemie(basis: str, start: str) -> list:
    """Tagesschluss Coinbase {basis}-USD / Binance {basis}USDT − 1 (Nachfrage US gegen Welt)."""
    bn = _binance_tage("https://api.binance.com/api/v3/klines", {"symbol": basis + "USDT", "interval": "1d"}, start)
    cb, ab = {}, date.fromisoformat(start)
    while ab < date.today():
        bis = min(ab + timedelta(days=299), date.today())
        r = _hole("https://api.exchange.coinbase.com/products/%s-USD/candles" % basis,
                  {"granularity": 86400, "start": ab.isoformat() + "T00:00:00Z", "end": bis.isoformat() + "T00:00:00Z"})
        if r is None:
            raise RuntimeError("Coinbase %s nicht abrufbar ab %s" % (basis, ab))
        for x in r.json():
            cb[_tag(x[0] * 1000)] = float(x[4])
        ab = bis + timedelta(days=1)
        time.sleep(0.4)
    heute = date.today().isoformat()
    return [(d, cb[d] / bn[d] - 1, _folgetag(d), None) for d in sorted(cb) if d in bn and d < heute]   # nur abgeschlossene Tage


def basis_quartal(basis: str, start: str) -> list:
    """Schluss des laufenden Quartalskontrakts / Schluss des Perp − 1 (absolut; annualisiert wird in Ebene 1)."""
    q = _binance_tage("https://fapi.binance.com/fapi/v1/continuousKlines",
                      {"pair": basis + "USDT", "contractType": "CURRENT_QUARTER", "interval": "1d"}, start)
    p = _binance_tage("https://fapi.binance.com/fapi/v1/klines", {"symbol": basis + "USDT", "interval": "1d"}, start)
    heute = date.today().isoformat()
    return [(d, q[d] / p[d] - 1, _folgetag(d), None) for d in sorted(q) if d in p and d < heute]


def _gdelt_fenster(abfrage: str, ab: date, bis: date) -> list:
    r = _hole("https://api.gdeltproject.org/api/v2/doc/doc",
              {"query": abfrage, "mode": "timelinetone", "format": "json",
               "startdatetime": ab.strftime("%Y%m%d") + "000000", "enddatetime": bis.strftime("%Y%m%d") + "000000"},
              versuche=2, pause=120)   # 30.10. (Nutzer: a): ein zweiter Versuch, dann Quellausfall - kein Wiederholungsstau
    if r is None or not r.text.startswith("{"):
        raise RuntimeError("GDELT nicht abrufbar ab %s (429 = hoechstens eine Anfrage je 5 s, Sperre haelt laenger an)" % ab)
    tl = r.json().get("timeline") or [{"data": []}]
    return [("%s-%s-%s" % (x["date"][:4], x["date"][4:6], x["date"][6:8]), float(x["value"])) for x in tl[0]["data"]]


class Teilergebnis(RuntimeError):
    """Abbruch mitten in einer Reihe - die schon geholten Zeilen gehen mit, damit der naechste Lauf dort FORTSETZT
    (29.10.: GDELT sperrte nach drei von vier Jahresfenstern, und alles Geholte war verworfen)."""
    def __init__(self, ursache, zeilen):
        super().__init__(str(ursache))
        self.zeilen = zeilen


def gdelt_ton(abfrage: str, start: str) -> list:
    """Tageston aus GDELT DOC. ⚠️ Hoechstens eine Anfrage je 5 s, und nach vielen Anfragen sperrt GDELT LAENGER (29.10.: 429 auch
    nach 20 s und 60 s). Deshalb JAHRESFENSTER (4 Anfragen fuer 2023-26 statt 46). Liefert ein Fenster keine Tagesaufloesung
    (Punkte < 80 % der Tage), wird es monatsweise geholt - nie still eine groebere Reihe."""
    aus, heute = {}, date.today()
    ab = date.fromisoformat(start)
    while ab < heute:
        bis = min(date(ab.year + 1, 1, 1), heute)
        try:
            teil = _gdelt_fenster(abfrage, ab, bis)
            tage = {d for d, _ in teil}
            if len(tage) < 0.8 * (bis - ab).days:             # keine Tagesaufloesung -> monatsweise
                teil, m = [], max(ab.replace(day=1), ab)
                while m < bis:
                    m2 = min((m.replace(day=28) + timedelta(days=4)).replace(day=1), bis)
                    time.sleep(6)
                    teil += _gdelt_fenster(abfrage, m, m2)
                    m = m2
        except RuntimeError as e:
            raise Teilergebnis(e, [(d, w, _folgetag(d), None) for d, w in sorted(aus.items())]) from e
        for d, w in teil:                                     # ⚠️ < bis: der Endtag gehoert zum NAECHSTEN Fenster (Endzeit 00:00)
            if start <= d < min(bis, heute).isoformat():
                aus[d] = w
        ab = bis
        time.sleep(6)
    return [(d, w, _folgetag(d), None) for d, w in sorted(aus.items())]


# ── Nachrichten: dieselbe Zerlegung wie das Archiv (Rechenkern_02_10/p65_lc_archiv_laden.py), damit live = Rückspiel ──
def _text(x):
    x = re.sub(r"<!\[CDATA\[(.*?)\]\]>", r"\1", x or "", flags=re.S)
    return html.unescape(re.sub(r"<[^>]+>", " ", x)).strip()


def _feld(item, tag):
    m = re.search(r"<%s[^>]*>(.*?)</%s>" % (tag, tag), item, re.S)
    return _text(m.group(1)) if m else ""


def zerlege_feed(name: str, xml: str, aufnahme: str) -> list:
    items = re.findall(r"<item[ >].*?</item>", xml, re.S) or re.findall(r"<entry[ >].*?</entry>", xml, re.S)
    rows = []
    for it in items:
        pub = _feld(it, "pubDate") or _feld(it, "published") or _feld(it, "updated")
        try:
            pu = parsedate_to_datetime(pub).astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        except Exception:  # noqa: BLE001
            try:
                pu = datetime.fromisoformat(pub.replace("Z", "+00:00")).astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            except Exception:  # noqa: BLE001
                pu = None
        link = _feld(it, "link") or (re.search(r'<link[^>]*href="([^"]+)"', it) or [None, ""])[1]
        schl = _feld(it, "guid") or _feld(it, "id") or link or _feld(it, "title")
        rows.append((name, schl, _feld(it, "title"), link, pu, _feld(it, "description")[:300], aufnahme))
    return rows


def feeds_laufend(c) -> int:
    """Die 9 Feeds einmal abrufen. Historie gibt es nicht live — sie liegt im Wayback-Archiv ``data/_lc/nachrichten.db``."""
    n = 0
    for name, url in FEEDS.items():
        r = _hole("https://" + url, versuche=2, pause=5)
        if r is None:
            _fehler(c, "feed", name, "nicht abrufbar")
            continue
        rows = zerlege_feed(name, r.text, "LIVE" + _jetzt())
        c.executemany("INSERT OR IGNORE INTO meldung VALUES (?,?,?,?,?,?,?)", rows)
        c.execute("INSERT INTO lauf VALUES (?,?,?,?,?)", ("feed", name, _jetzt(), "ok", len(rows)))
        c.commit()
        n += len(rows)
    return n


# ══ Ablauf ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def auftraege(fred_key: str) -> list:
    """(quelle, symbol, abruf(start)) — EINE Liste für Historie und laufend."""
    a = [("yfinance", t, lambda s, t=t: yfinance_reihe(t, s)) for t in YFINANCE]
    if fred_key:
        a += [("fred", sid, lambda s, sid=sid: fred_jahrgaenge(sid, s, fred_key)) for sid in FRED]
    a += [("coinbase_praemie", b, lambda s, b=b: coinbase_praemie(b, s)) for b in KRYPTO]
    a += [("basis_quartal", b, lambda s, b=b: basis_quartal(b, s)) for b in KRYPTO]
    a += [("gdelt_ton", k, lambda s, q=q: gdelt_ton(q, s)) for k, q in GDELT.items()]
    return a


def lade(start: str, pfad: str = ABLAGE, nur: str | None = None, mit_feeds: bool = False) -> dict:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(PROJ, ".env"))
    key = os.environ.get("FRED_API_KEY") or ""
    c = verbinde(pfad)
    if not key and nur in (None, "fred"):
        _fehler(c, "fred", "*", "kein FRED_API_KEY")
    ergebnis = {}
    letzte_gdelt = None
    for quelle, symbol, abruf in auftraege(key):
        if nur and quelle != nur:
            continue
        try:
            # FRED immer mit allen Jahrgaengen ab START: ALFRED kappt aeltere Gueltigkeitsbeginne auf realtime_start - ein
            # spaeterer Start legte fuer jede alte Beobachtung eine zweite Zeile an. Wenige Abrufe je Reihe, und genau gleich.
            ab = start
            if quelle == "gdelt_ton":
                if letzte_gdelt is not None:
                    time.sleep(max(0.0, GDELT_ABSTAND_S - (time.monotonic() - letzte_gdelt)))
                letzte_gdelt = time.monotonic()
            if quelle == "fred":
                ab = START
            elif quelle == "gdelt_ton":                        # FORTSETZEN: GDELT sperrt lange, Geholtes nicht neu holen
                letzt = c.execute("SELECT MAX(datum) FROM reihe WHERE quelle=? AND symbol=?", (quelle, symbol)).fetchone()[0]
                if letzt and letzt >= start:                   # ab dem LETZTEN Tag: er wird neu geholt (er kann ein Randtag sein)
                    ab = letzt
            n = _schreibe(c, quelle, symbol, abruf(ab))
            ergebnis[(quelle, symbol)] = n
            print("  ✔ %-17s %-13s %6d Zeilen" % (quelle, symbol, n), flush=True)
        except Teilergebnis as e:
            ergebnis[(quelle, symbol)] = None
            _schreibe(c, quelle, symbol, e.zeilen, status="teil")
            _fehler(c, quelle, symbol, "%s (%d Zeilen behalten, naechster Lauf setzt fort)" % (e, len(e.zeilen)))
            print("  ◐ %-17s %-13s %6d Zeilen behalten, Rest gesperrt" % (quelle, symbol, len(e.zeilen)), flush=True)
        except Exception as e:  # noqa: BLE001
            ergebnis[(quelle, symbol)] = None
            _fehler(c, quelle, symbol, e)
    if mit_feeds and nur in (None, "feed"):
        ergebnis[("feed", "*")] = feeds_laufend(c)
        print("  ✔ feeds             9 Quellen     %6d Meldungen" % ergebnis[("feed", "*")], flush=True)
    c.close()
    return ergebnis


def stand(pfad: str = ABLAGE) -> None:
    c = verbinde(pfad)
    print("Bestand %s" % pfad)
    for q, s, n, lo, hi in c.execute("SELECT quelle, symbol, COUNT(*), MIN(datum), MAX(datum) FROM reihe GROUP BY quelle, symbol"):
        print("  %-17s %-13s %7d  %s bis %s" % (q, s, n, lo, hi))
    print("  Meldungen live: %d" % c.execute("SELECT COUNT(*) FROM meldung").fetchone()[0])
    f = c.execute("SELECT quelle, symbol, ts, status FROM lauf WHERE status LIKE 'FEHLER%' ORDER BY ts DESC LIMIT 10").fetchall()
    for x in f:
        print("  ✖ %s" % " · ".join(x))
    c.close()


def main() -> int:
    a = sys.argv
    pfad = a[a.index("--ablage") + 1] if "--ablage" in a else ABLAGE
    nur = a[a.index("--quelle") + 1] if "--quelle" in a else None
    if "--stand" in a:
        stand(pfad)
        return 0
    if "--laufend" in a:
        e = lade((date.today() - timedelta(days=LAUFEND_TAGE)).isoformat(), pfad, nur, mit_feeds=True)
    elif "--historie" in a:
        e = lade(START, pfad, nur)
    else:
        print(__doc__)
        return 1
    stand(pfad)
    return 0 if all(v is not None for v in e.values()) else 2


if __name__ == "__main__":
    sys.exit(main())
