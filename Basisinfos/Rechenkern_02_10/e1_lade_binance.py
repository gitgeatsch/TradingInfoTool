"""E-1 Schritt 1 (Voranalyse_Schritt7 §23.22/§23.23): Binance-Ankuendigungen (Delisting, Monitoring) laden und je Asset zuordnen.
Oeffentliche Website-Schnittstelle ohne Schluessel, nur lesend; Ablage am DESKTOP data/_e1/binance_ankuendigungen.db (nicht die
Produktion, keine Messbasis). Fortsetzbar: bereits geholte Meldungen werden nicht erneut abgerufen.

    python Basisinfos/Rechenkern_02_10/e1_lade_binance.py

ARTEN (aus dem Titel, vorab festgelegt):
  token_delist    "Binance Will Delist A, B and C on <Datum>"         Kuerzel aus dem TITEL  - der Token verschwindet von Binance Spot
  futures_delist  "Binance Futures Will Delist ..."                    Kuerzel aus dem TEXT (XYZUSDT) - der Hebel faellt weg
  paar_entfernt   "Notice of Removal of Spot Trading Pair(s)"          Kuerzel aus dem TEXT (ABC/QUOTE) - der Token BLEIBT handelbar
  margin          "... Margin ..."                                     Kuerzel aus dem TEXT (ABC/QUOTE)
  monitoring      Titel mit "Monitoring Tag" (BEIDE Kataloge)          Kuerzel aus dem TITEL; "Remove ... Monitoring Tag" = monitoring_ende
  sonstiges       alles andere im Delisting-Katalog                    nicht zugeordnet
Zugeordnet wird NUR ein Kuerzel, das es in unserer Asset-Welt gibt (stundenkurse, stundenkurse_alle, eingestellt_historie); die
Quote-Waehrungen (USDT, USDC, BTC, ETH, BNB, FDUSD, TRY, EUR ...) nie als Basis. 1000er-Kontrakte (1000PEPEUSDT) -> PEPE.
"""
import json
import os
import re
import sqlite3
import sys
import time
from datetime import datetime, timezone

import requests

HIER = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(os.path.dirname(HIER))
D = os.path.join(PROJ, "data")
ABLAGE = os.path.join(D, "_e1", "binance_ankuendigungen.db")
LISTE = "https://www.binance.com/bapi/composite/v1/public/cms/article/list/query"
DETAIL = "https://www.binance.com/bapi/composite/v1/public/cms/article/detail/query"
H = {"User-Agent": "Mozilla/5.0 TradingInfoTool-E1"}
AB_MS = int(datetime(2023, 6, 1, tzinfo=timezone.utc).timestamp() * 1000)   # Messfenster ab 2024 + Vorlauf
QUOTE = {"USDT", "USDC", "BTC", "ETH", "BNB", "FDUSD", "TRY", "EUR", "BUSD", "TUSD", "DAI", "BRL", "JPY", "PLN", "RON", "ARS", "ZAR",
         "UAH", "MXN", "COP", "CZK", "IDRT", "BIDR", "AUD", "GBP", "RUB", "NGN", "USD", "UTC", "USDP", "AEUR", "XUSD", "USD1", "BFUSD"}


def welt() -> set:
    s = set()
    for f in ("stundenkurse.db", "stundenkurse_alle.db", "eingestellt_historie.db"):
        p = os.path.join(D, f)
        if os.path.exists(p):
            c = sqlite3.connect("file:%s?mode=ro" % p.replace("\\", "/"), uri=True)
            s |= {r[0] for r in c.execute("SELECT DISTINCT symbol FROM stundenkurse")}
            c.close()
    return s


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
    if "monitoring tag" in t:                                  # steht in BEIDEN Katalogen (Korrektur nach dem ersten Lauf)
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


def kuerzel(a: str, titel: str, txt: str, W: set) -> set:
    if a == "token_delist":
        k = aus_titel(titel, r"[Dd]elist (.+?) on \d{4}-\d{2}-\d{2}")
    elif a == "futures_delist":
        k = {basis(x) for x in re.findall(r"\b([A-Z0-9]{2,20})USDT\b", txt)}
    elif a == "paar_entfernt":
        k = set(re.findall(r"\b([A-Z0-9]{2,15})/[A-Z0-9]{2,6}\b", txt))
    elif a == "margin":                                       # Titel "... Will Delist A & B on ..." oder Paare im Text
        k = aus_titel(titel, r"[Dd]elist (.+?) on \d{4}-\d{2}-\d{2}") | set(re.findall(r"\b([A-Z0-9]{2,15})/[A-Z0-9]{2,6}\b", txt))
    elif a == "monitoring":                                   # NUR der Titel - der Text nennt auch Werte, deren Kennzeichen endet
        k = aus_titel(titel, r"(?:[Ii]nclude|[Tt]o|[Oo]n) (.+?) on \d{4}-\d{2}-\d{2}") or set(re.findall(r"\b([A-Z0-9]{2,12})\b", titel))
    else:
        k = set()
    return {x for x in k if x in W and x not in QUOTE}


def main():
    os.makedirs(os.path.dirname(ABLAGE), exist_ok=True)
    c = sqlite3.connect(ABLAGE)
    c.executescript("""CREATE TABLE IF NOT EXISTS meldung (code TEXT PRIMARY KEY, katalog INTEGER, titel TEXT, release_ms INTEGER, art TEXT,
                                                           text TEXT, geholt TEXT);
                       CREATE TABLE IF NOT EXISTS ereignis (code TEXT, art TEXT, symbol TEXT, release_ms INTEGER, PRIMARY KEY (code, symbol));""")
    W = welt()
    neu = 0
    for kat in (161, 49):
        for seite in range(1, 80):
            arts = None
            for versuch in range(6):                           # KORREKTUR: eine gescheiterte Abfrage ist KEINE leere Seite
                try:
                    r = requests.get(LISTE, params={"type": 1, "catalogId": kat, "pageNo": seite, "pageSize": 50}, headers=H, timeout=30)
                    arts = r.json()["data"]["catalogs"][0]["articles"]
                    break
                except Exception:                              # noqa: BLE001
                    time.sleep(5 * (versuch + 1))
            if arts is None:
                raise SystemExit("Katalog %d Seite %d nach 6 Versuchen nicht abrufbar - Abbruch (fortsetzbar)" % (kat, seite))
            if not arts:
                break
            for x in arts:
                if x["releaseDate"] < AB_MS:
                    continue
                a = art(x["title"], kat)
                alt = c.execute("SELECT text FROM meldung WHERE code=?", (x["code"],)).fetchone()
                if alt and (alt[0] or a in ("sonstiges", "monitoring", "monitoring_ende")):
                    continue
                txt = ""
                if a not in ("sonstiges", "monitoring", "monitoring_ende"):
                    for versuch in range(3):
                        try:
                            d = requests.get(DETAIL, params={"articleCode": x["code"]}, headers=H, timeout=30).json()["data"]
                            txt = text(d.get("body") or "")
                            break
                        except Exception:                      # noqa: BLE001
                            time.sleep(3)
                    time.sleep(0.25)
                c.execute("INSERT OR REPLACE INTO meldung VALUES (?,?,?,?,?,?,?)", (x["code"], kat, x["title"], x["releaseDate"], a, txt,
                                                                         datetime.now(timezone.utc).isoformat()))
                neu += 1
            c.commit()
            if min(x["releaseDate"] for x in arts) < AB_MS:
                break
            time.sleep(0.3)
    for code, kat, titel in c.execute("SELECT code, katalog, titel FROM meldung").fetchall():   # Art immer nach der aktuellen Regel
        c.execute("UPDATE meldung SET art=? WHERE code=?", (art(titel, kat), code))
    c.execute("DELETE FROM ereignis")
    for code, kat, titel, ms, a, txt in c.execute("SELECT code, katalog, titel, release_ms, art, text FROM meldung").fetchall():
        for s in kuerzel(a, titel, txt or "", W):
            c.execute("INSERT OR IGNORE INTO ereignis VALUES (?,?,?,?)", (code, a, s, ms))
    c.commit()
    print("E-1 Lader · neue Meldungen %d · Ablage %s" % (neu, ABLAGE))
    for a, n, m, s in c.execute("SELECT m.art, COUNT(DISTINCT m.code), COUNT(e.symbol), COUNT(DISTINCT e.symbol) FROM meldung m "
                                "LEFT JOIN ereignis e ON e.code = m.code GROUP BY m.art ORDER BY m.art"):
        print("  %-15s Meldungen %4d · Zuordnungen %4d · Assets %3d" % (a, n, m, s))
    leer = c.execute("SELECT COUNT(*) FROM meldung m WHERE art NOT IN ('sonstiges', 'monitoring_ende') AND NOT EXISTS (SELECT 1 FROM ereignis e WHERE e.code=m.code)").fetchone()[0]
    print("  Meldungen einer bekannten Art OHNE zugeordnetes Asset: %d (Asset nicht in unserer Welt oder Kuerzel nicht gefunden)" % leer)
    for t, a in c.execute("SELECT titel, art FROM meldung m WHERE art NOT IN ('sonstiges', 'monitoring_ende') AND NOT EXISTS (SELECT 1 FROM ereignis e WHERE e.code=m.code) LIMIT 8"):
        print("     ohne: [%s] %s" % (a, t[:110]))
    c.close()


if __name__ == "__main__":
    sys.exit(main())
