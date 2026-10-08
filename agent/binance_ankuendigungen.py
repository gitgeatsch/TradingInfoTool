"""Binance-Ankuendigungen als FAKT in der REGEL0-Signalmail und Vorwaertsprotokoll (O29, E-83/E-84; Voranalyse_Schritt7 Par. 23.22-23.24).

WOZU: Ein angekuendigtes Delisting oder ein Monitoring-Kennzeichen ist das linke Ende der Wette (Gegenbewegung nach Rueckgang): E-1 zeigte
in den unverzerrten Mengen 24 h -1,0 bis -1,5 %, Verlust >= 10 % +7..9 Pp (Par. 23.23) - nach der Vorabregel aber NICHT getragen. Deshalb:
  * in der Mail NUR der Fakt (*"Binance hat am ... angekuendigt ..."*), keine Bewertung, kein Ausloeser, kein Sperren
  * fuer ALLE REGEL0-Signale ein Vorwaertsprotokoll (Tabelle signal_ereignis) - damit wird die Beschreibung an NEUEN Daten pruefbar (E-63)

WIE:
  * Quelle: oeffentliche CMS-Schnittstelle der Binance-Website (ohne Schluessel; Projektregel: nur kostenfreie Quellen), Kataloge 161
    (Delisting) und 49 (News, darin Monitoring). Je Lauf nur die ersten Seiten, Details nur neuer, relevanter Meldungen
  * Arten und Kuerzel nach DENSELBEN Regeln wie die Messung E-1 (Rechenkern_02_10/e1_lade_binance.py, e1_messung.FENSTER) - die
    Gegenprobe e1_betrieb_gegenprobe.py prueft die Gleichheit an allen E-1-Einstiegen
  * Ablage: regel0_signale.db (die REGEL0-Ablage, NICHT die Produktion) - Tabellen ankuendigung, ankuendigung_ereignis,
    ankuendigung_lauf, signal_ereignis
  * SCHALTER: regel0_betrieb.yaml ankuendigung_aktiv (Vorgabe false) - je Lauf gelesen. Aus: kein Abruf, keine Mailzeile
  * scheitert NIE nach aussen: ein Fehler steht in ankuendigung_lauf und im Protokoll; die Mail geht ohne Zeile (P-8)
"""
from __future__ import annotations

import json
import logging
import os
import re
import sqlite3
import time
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)

LISTE = "https://www.binance.com/bapi/composite/v1/public/cms/article/list/query"
DETAIL = "https://www.binance.com/bapi/composite/v1/public/cms/article/detail/query"
LINK = "https://www.binance.com/en/support/announcement/%s"
KOPF = {"User-Agent": "Mozilla/5.0 TradingInfoTool"}
KATALOGE = (161, 49)
QUOTE = {"USDT", "USDC", "BTC", "ETH", "BNB", "FDUSD", "TRY", "EUR", "BUSD", "TUSD", "DAI", "BRL", "JPY", "PLN", "RON", "ARS", "ZAR",
         "UAH", "MXN", "COP", "CZK", "IDRT", "BIDR", "AUD", "GBP", "RUB", "NGN", "USD", "UTC", "USDP", "AEUR", "XUSD", "USD1", "BFUSD"}
# Fenster je Art in Tagen - WIE GEMESSEN (e1_messung.FENSTER); Monitoring endet frueher mit einer 'monitoring_ende'-Meldung
FENSTER = {"token_delist": 30, "futures_delist": 30, "monitoring": 180, "paar_entfernt": 14, "margin": 30}
ARTEN_MAIL = ("token_delist", "futures_delist", "monitoring")   # SCHWER in E-1; Paar entfernt und Margin: kein Effekt, nur Rauschen
SEITEN_JE_LAUF = 2
ZEITGRENZE_S = 90

SCHEMA = """
CREATE TABLE IF NOT EXISTS ankuendigung (code TEXT PRIMARY KEY, katalog INTEGER, titel TEXT, release_ms INTEGER, art TEXT, text TEXT,
                                         geholt TEXT);
CREATE TABLE IF NOT EXISTS ankuendigung_ereignis (code TEXT, art TEXT, symbol TEXT, release_ms INTEGER, PRIMARY KEY (code, symbol));
CREATE TABLE IF NOT EXISTS ankuendigung_lauf (am TEXT PRIMARY KEY, ok INTEGER, neu INTEGER, zuordnungen INTEGER, protokolliert INTEGER,
                                              fehler TEXT, sekunden REAL);
CREATE TABLE IF NOT EXISTS signal_ereignis (symbol TEXT, signalstunde TEXT, arten TEXT, codes TEXT, erfasst_am TEXT,
                                            PRIMARY KEY (symbol, signalstunde));
"""


# ---------------------------------------------------------------------------- Regeln (wie E-1)
def text(body: str) -> str:
    out = []

    def walk(n):
        if isinstance(n, dict):
            if n.get("node") == "text":
                out.append(n.get("text", ""))
            for ch in n.get("child", []) or []:
                walk(ch)
    try:
        walk(json.loads(body))
    except Exception:                                          # noqa: BLE001
        return body or ""
    return " ".join(out).replace("&nbsp;", " ")


def art(titel: str, katalog: int) -> str:
    t = titel.lower()
    if "monitoring tag" in t:
        return "monitoring_ende" if "remove" in t else "monitoring"
    if katalog == 49 or "binance alpha" in t:
        return "sonstiges"
    if "futures" in t and "delist" in t:
        return "futures_delist"
    if "margin" in t:
        return "margin"
    if "removal of spot trading pair" in t:
        return "paar_entfernt"
    if t.startswith("binance will delist"):
        return "token_delist"
    return "sonstiges"


def basis(k: str) -> str:
    m = re.match(r"^(1000000|1000|1M)([A-Z0-9]{2,})$", k)
    return m.group(2) if m else k


def aus_titel(titel: str, muster: str) -> set:
    m = re.search(muster, titel)
    roh = re.split(r",\s*|\s+and\s+|\s*&\s*", m.group(1)) if m else []
    return {x.strip().upper() for x in roh if x.strip()}


def kuerzel(a: str, titel: str, txt: str, welt: set) -> set:
    if a == "token_delist":
        k = aus_titel(titel, r"[Dd]elist (.+?) on \d{4}-\d{2}-\d{2}")
    elif a == "futures_delist":
        k = {basis(x) for x in re.findall(r"\b([A-Z0-9]{2,20})USDT\b", txt)}
    elif a == "paar_entfernt":
        k = set(re.findall(r"\b([A-Z0-9]{2,15})/[A-Z0-9]{2,6}\b", txt))
    elif a == "margin":
        k = aus_titel(titel, r"[Dd]elist (.+?) on \d{4}-\d{2}-\d{2}") | set(re.findall(r"\b([A-Z0-9]{2,15})/[A-Z0-9]{2,6}\b", txt))
    elif a == "monitoring":
        k = aus_titel(titel, r"(?:[Ii]nclude|[Tt]o|[Oo]n) (.+?) on \d{4}-\d{2}-\d{2}") or set(re.findall(r"\b([A-Z0-9]{2,12})\b", titel))
    else:
        k = set()
    return {x for x in k if x in welt and x not in QUOTE}


def welt(ordner: str) -> set:
    s = set()
    for f in ("stundenkurse.db", "stundenkurse_alle.db", "eingestellt_historie.db"):
        p = os.path.join(ordner, f)
        if os.path.exists(p):
            c = sqlite3.connect("file:%s?mode=ro" % p.replace("\\", "/"), uri=True, timeout=30)
            try:
                s |= {r[0] for r in c.execute("SELECT DISTINCT symbol FROM stundenkurse")}
            except sqlite3.Error:
                pass
            finally:
                c.close()
    return s


# ---------------------------------------------------------------------------- Ablage
def oeffne(ordner_ablage: str) -> sqlite3.Connection:
    import agent.regel0_ablage as AB
    c = AB.oeffne(ordner_ablage)
    c.executescript(SCHEMA)
    return c


def aktiv() -> bool:
    try:
        import agent.regel0_groesse as G
        return bool(G.lade().get("ankuendigung_aktiv"))
    except Exception:                                          # noqa: BLE001
        return False                                           # im Zweifel AUS: kein Abruf, keine Zeile


# ---------------------------------------------------------------------------- Abruf
def hole(c: sqlite3.Connection, ordner_daten: str, seiten: int = SEITEN_JE_LAUF, zeitgrenze_s: float = ZEITGRENZE_S, http=None) -> dict:
    """Neue Meldungen der ersten Seiten beider Kataloge holen und zuordnen. Wirft bei Netzfehlern (der Aufrufer protokolliert)."""
    import requests
    http = http or requests
    grenze = time.time() + zeitgrenze_s
    W = welt(ordner_daten)
    neu = zu = 0
    for kat in KATALOGE:
        for seite in range(1, seiten + 1):
            if time.time() > grenze:
                raise TimeoutError("Zeitgrenze %d s" % zeitgrenze_s)
            r = http.get(LISTE, params={"type": 1, "catalogId": kat, "pageNo": seite, "pageSize": 50}, headers=KOPF, timeout=30)
            arts = r.json()["data"]["catalogs"][0]["articles"]
            if not arts:
                break
            bekannt = 0
            for x in arts:
                if c.execute("SELECT 1 FROM ankuendigung WHERE code=?", (x["code"],)).fetchone():
                    bekannt += 1
                    continue
                a = art(x["title"], kat)
                txt = ""
                if a not in ("sonstiges", "monitoring", "monitoring_ende"):
                    d = http.get(DETAIL, params={"articleCode": x["code"]}, headers=KOPF, timeout=30).json()["data"]
                    txt = text(d.get("body") or "")
                c.execute("INSERT OR REPLACE INTO ankuendigung VALUES (?,?,?,?,?,?,?)",
                          (x["code"], kat, x["title"], int(x["releaseDate"]), a, txt, datetime.now(timezone.utc).isoformat()))
                for s in kuerzel(a, x["title"], txt, W):
                    c.execute("INSERT OR IGNORE INTO ankuendigung_ereignis VALUES (?,?,?,?)", (x["code"], a, s, int(x["releaseDate"])))
                    zu += 1
                neu += 1
            c.commit()
            if bekannt == len(arts):
                break                                          # die Seite ist schon ganz bekannt - weiter hinten ist nichts Neues
    return {"neu": neu, "zuordnungen": zu}


# ---------------------------------------------------------------------------- Fenster je Signal (wie e1_messung.flags)
def aktive(c: sqlite3.Connection, symbol: str, ende: datetime) -> list:
    """Ankuendigungen zu `symbol`, die vor `ende` (Schluss der Signalstunde, UTC) erschienen und im Fenster ihrer Art liegen."""
    e_ms = int(ende.replace(tzinfo=timezone.utc).timestamp() * 1000) if ende.tzinfo is None else int(ende.timestamp() * 1000)
    rows = c.execute("SELECT e.art, e.release_ms, e.code, a.titel FROM ankuendigung_ereignis e LEFT JOIN ankuendigung a ON a.code = e.code "
                     "WHERE e.symbol=? AND e.release_ms <= ? ORDER BY e.release_ms", (symbol, e_ms)).fetchall()
    # 'monitoring_ende' (Binance nimmt das Kennzeichen zurueck) hat keine Zuordnung - das Kuerzel steht nur im Titel. ⚠️ In E-1 griff das
    # Ende deshalb NIE (e1_messung sucht es in den Zuordnungen); hier wird es ueber den Titel erkannt, denn die Mail nennt einen FAKT und
    # darf kein zurueckgenommenes Kennzeichen melden. Die Gegenprobe weist die Faelle aus, in denen das von E-1 abweicht.
    ende_m =[ms for (ms, t) in c.execute("SELECT release_ms, titel FROM ankuendigung WHERE art='monitoring_ende' AND release_ms <= ?",
                                          (e_ms,)).fetchall() if re.search(r"(?<![A-Z0-9])%s(?![A-Z0-9])" % re.escape(symbol), t or "")]
    aus = []
    for a, ms, code, titel in rows:
        w = FENSTER.get(a)
        if w is None or ms <= e_ms - w * 86400000:
            continue
        aus.append({"art": a, "release_ms": ms, "code": code, "titel": titel or ""})
    mon = [x for x in aus if x["art"] == "monitoring"]
    if mon:
        letzte = max(x["release_ms"] for x in mon)
        if any(letzte < ms <= e_ms for ms in ende_m):
            aus = [x for x in aus if x["art"] != "monitoring"]
    return aus


def _datum(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).strftime("%d.%m.")


def _wirksam(titel: str) -> str | None:
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", titel or "")
    return "%s.%s." % (m.group(3), m.group(2)) if m else None


def mailteile(c: sqlite3.Connection, r: dict) -> dict | None:
    """{'ein': Satz fuer die Einschaetzung, 'technik': [(Bezeichnung, Text)]} oder None - NUR Fakten, nur die Arten aus ARTEN_MAIL."""
    ende = datetime.strptime(r["signalstunde"], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc) + timedelta(hours=1)
    ev = [x for x in aktive(c, r["symbol"], ende) if x["art"] in ARTEN_MAIL]
    if not ev:
        return None
    saetze, technik = [], []
    for x in sorted(ev, key=lambda y: -y["release_ms"]):
        am, wirk = _datum(x["release_ms"]), _wirksam(x["titel"])
        if x["art"] == "token_delist":
            saetze.append("Binance hat am %s angekuendigt, den Handel%s einzustellen." % (am, (" am %s" % wirk) if wirk else ""))
        elif x["art"] == "futures_delist":
            saetze.append("Binance stellt den Futures-Kontrakt%s ein (angekuendigt am %s)." % ((" am %s" % wirk) if wirk else "", am))
        else:
            saetze.append("Binance fuehrt den Wert seit %s mit Monitoring-Kennzeichen." % am)
        technik.append(("Binance-Meldung", "%s - %s" % (x["titel"][:140], LINK % x["code"])))
    return {"ein": " ".join(dict.fromkeys(saetze)), "technik": technik}


def mailteile_aus_ablage(ordner_ablage: str, r: dict) -> dict | None:
    if not aktiv():
        return None
    c = oeffne(ordner_ablage)
    try:
        return mailteile(c, r)
    finally:
        c.close()


# ---------------------------------------------------------------------------- Vorwaertsprotokoll
def protokolliere(c: sqlite3.Connection) -> int:
    """Jedes REGEL0-Signal ohne Eintrag bekommt einen: welche Arten im Fenster lagen (auch 'keins') - fuer die Pruefung an NEUEN Daten."""
    n = 0
    for sym, st in c.execute("SELECT s.symbol, s.signalstunde FROM signal s LEFT JOIN signal_ereignis e ON e.symbol = s.symbol AND "
                             "e.signalstunde = s.signalstunde WHERE e.symbol IS NULL").fetchall():
        ende = datetime.strptime(st, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc) + timedelta(hours=1)
        ev = aktive(c, sym, ende)
        c.execute("INSERT OR IGNORE INTO signal_ereignis VALUES (?,?,?,?,?)",
                  (sym, st, json.dumps(sorted({x["art"] for x in ev})) if ev else "keins", json.dumps([x["code"] for x in ev]),
                   datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")))
        n += 1
    c.commit()
    return n


# ---------------------------------------------------------------------------- der Job
def lauf(ordner_ablage: str, ordner_daten: str, http=None) -> dict:
    """Abruf + Vorwaertsprotokoll - nur mit Schalter. Scheitert NIE nach aussen; das Ergebnis steht in ankuendigung_lauf."""
    if not aktiv():
        return {"aktiv": False}
    t0 = time.time()
    c = oeffne(ordner_ablage)
    erg = {"aktiv": True, "neu": 0, "zuordnungen": 0, "protokolliert": 0, "fehler": None}
    try:
        try:
            erg.update(hole(c, ordner_daten, http=http))
        except Exception as exc:                               # noqa: BLE001
            erg["fehler"] = "%s: %s" % (type(exc).__name__, str(exc)[:200])
            logger.warning("Binance-Ankuendigungen: Abruf gescheitert - %s", erg["fehler"])
        erg["protokolliert"] = protokolliere(c)
        c.execute("INSERT OR REPLACE INTO ankuendigung_lauf VALUES (?,?,?,?,?,?,?)",
                  (datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"), 0 if erg["fehler"] else 1, erg["neu"], erg["zuordnungen"],
                   erg["protokolliert"], erg["fehler"], round(time.time() - t0, 1)))
        c.commit()
    finally:
        c.close()
    logger.info("Binance-Ankuendigungen: %d neu, %d Zuordnungen, %d Signale protokolliert%s", erg["neu"], erg["zuordnungen"],
                erg["protokolliert"], (" - FEHLER " + erg["fehler"]) if erg["fehler"] else "")
    return erg
