"""Spot B3 - Upbit-Listing eines gehaltenen Coins als VERKAUFSANLASS (P16, 12.10.2026; Voranalyse_Spot_Neubau_04_10.md §38, §39.7,
§42.2, §47).

Nutzer 12.10.: *"Ja"* zum Bau des Buendels P15 + P16.

DIE REGEL (wie gemessen, nichts neu gewaehlt - ``c2_messung.ereignisse`` Art "C2-b Upbit-Listing"; Teil 0 prueft die Gleichheit am Archiv):

    Ereignis   Upbit-Meldung Kategorie 'trade', Titel mit '신규 거래지원' UND 'KRW'; Kuerzel = Klammern VOR dem Stichwort
    Kreis      L-Bestaende (``spot_mitnahme.kreis``: Krypto der Watchlist ohne Kern/Stablecoins, frei + gestakt > 0)
    Handlung   die GANZE Position verkaufen - in den naechsten Stunden. Gemessen ist Halten gegen Nicht-Halten der ganzen Position:
               7 T -10 Pp gegen BTC (schadet), in Dollar -8,5 %, faellt in 25 von 32 (§38.4, §42.2)
    Frist      Mail nur, wenn die Meldung hoechstens MAIL_HOECHSTENS_H alt ist (gemessen +4 h, Abrufraster 1 h, Puffer); aelter -> 'verpasst'
    erster Lauf  setzt eine Startmarke: alte Meldungen werden nur abgelegt, nie gemailt

Zuordnung Upbit-Kuerzel <-> Bitpanda-Symbol: gleich, ausser ``Basisinfos/symbol_zuordnung.csv`` mit Faktor 1 (CANTON -> CC).
ABLAGE: ``data/spot_betrieb.db`` (wie B1, nicht die Produktion). Liest die Produktion nur. Scheitert nie nach aussen (P-8).
NICHT in B3: Futures-Start (Binance-Katalog 48) - nach §39.7 keine eigene Mail, kommt mit B4 (P18) in die Abbau-Zeile.
"""
from __future__ import annotations

import csv
import json
import os
import re
import sqlite3
import time
from datetime import datetime, timedelta, timezone

import agent.spot_mitnahme as _SM

ANKUENDIGUNGEN = "https://api-manager.upbit.com/api/v1/announcements"
MAERKTE = "https://api.upbit.com/v1/market/all"
MELDUNG_LINK = "https://upbit.com/service_center/notice?id=%s"
KOPF = {"User-Agent": "Mozilla/5.0 TradingInfoTool"}
STICHWORT = "신규 거래지원"
MAIL_HOECHSTENS_H = 6
SEITEN_JE_LAUF = 2
JE_SEITE = 20
ABLAGE = _SM.ABLAGE
ZUORDNUNG = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Basisinfos", "symbol_zuordnung.csv")
BELEG = ("Gemessen ab 2024 an 32 Upbit-Listings von Coins, die schon handelten: Halten lag nach 7 Tagen 10 Prozentpunkte unter BTC "
         "(schadet, Rang 0,00 gegen Zufall der Klasse); in Dollar fiel der Coin in 25 von 32 Fällen, im Mittel −8,5 % (Spot §38.4, §42.2)")


# ══ die Regel - EINE Funktion, dieselbe wie in der Messung (Teil 0) ════════════════════════════════════════════════════════
def listing(titel: str) -> list:
    """Kuerzel eines KRW-Listings aus dem Upbit-Titel - genau ``c2_messung.ereignisse`` (C2-b). Kein Listing -> []."""
    if STICHWORT in titel and "KRW" in titel:
        return re.findall(r"\(([A-Z0-9]{2,15})\)", titel.split(STICHWORT)[0])
    return []


def zuordnung() -> dict:
    """{Bitpanda-Symbol: Upbit-Kuerzel} fuer die abweichenden Namen (symbol_zuordnung.csv, nur Faktor 1)."""
    out = {}
    try:
        with open(ZUORDNUNG, encoding="utf-8") as f:
            for r in csv.DictReader(f, delimiter=";"):
                if str(r.get("faktor", "")).strip() == "1" and r.get("bitpanda") and r.get("binance"):
                    out[r["bitpanda"].strip()] = r["binance"].strip()
    except OSError:
        pass
    return out


# ══ Ablage ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def oeffne(ordner: str) -> sqlite3.Connection:
    c = _SM.oeffne(ordner)                 # legt die gemeinsame Datei und die Tabelle protokoll an
    c.execute("CREATE TABLE IF NOT EXISTS upbit_meldung (id INTEGER, kuerzel TEXT, titel TEXT, utc TEXT, geholt TEXT, PRIMARY KEY (id, kuerzel))")
    c.execute("CREATE TABLE IF NOT EXISTS upbit_fall (id INTEGER, symbol TEXT, kuerzel TEXT, utc TEXT, status TEXT, menge REAL, mail_am TEXT, "
              "PRIMARY KEY (id, symbol))")
    c.execute("CREATE TABLE IF NOT EXISTS upbit_lauf (am TEXT PRIMARY KEY, ok INTEGER, neu INTEGER, faelle INTEGER, kreis INTEGER, "
              "ohne_krw TEXT, fehler TEXT, sekunden REAL)")
    c.commit()
    return c


# ══ Abruf (frei, ohne Schluessel) ═══════════════════════════════════════════════════════════════════════════════════════════
def _get(http, url, params=None):
    if http is not None:
        return http(url, params)
    import requests
    r = requests.get(url, params=params, headers=KOPF, timeout=30)
    r.raise_for_status()
    return r.json()


def hole_meldungen(http=None, seiten: int = SEITEN_JE_LAUF) -> list:
    """[(id, titel, utc)] der neuesten Handelsmeldungen. utc = first_listed_at (wie die Messung), sonst listed_at."""
    out = []
    for seite in range(1, seiten + 1):
        j = _get(http, ANKUENDIGUNGEN, {"os": "web", "page": seite, "per_page": JE_SEITE, "category": "trade"})
        no = (j.get("data") or {}).get("notices") or []
        for x in no:
            t = datetime.fromisoformat(x.get("first_listed_at") or x["listed_at"]).astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            out.append((int(x["id"]), x["title"], t))
        if not no:
            break
    return out


def krw_maerkte(http=None) -> set:
    return {x["market"].split("-", 1)[1] for x in _get(http, MAERKTE) if str(x.get("market", "")).startswith("KRW-")}


# ══ ein Lauf ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def lauf(conn_prod, ordner: str, watchlist: list, jetzt: datetime | None = None, http=None) -> dict:
    """Meldungen holen und ablegen, neue Listings den L-Bestaenden zuordnen. Schreibt nur in die Ablage; scheitert nie nach aussen.
    -> {'ok', 'kreis', 'ohne_krw', 'neu', 'faelle': [...], 'faellig': [Mailfaelle], 'startmarke', 'fehler'}"""
    jetzt = jetzt or datetime.now(timezone.utc)
    jt = jetzt.strftime("%Y-%m-%d %H:%M:%S")
    t0 = time.monotonic()
    erg = {"ok": False, "kreis": 0, "ohne_krw": [], "neu": 0, "faelle": [], "faellig": [], "startmarke": False, "fehler": None}
    c = oeffne(ordner)
    try:
        try:
            bestand = _SM.kreis(conn_prod, watchlist)
            zu = zuordnung()
            name = {s: zu.get(s, s) for s in bestand}
            krw = krw_maerkte(http)
            erg["kreis"] = len(bestand)
            erg["ohne_krw"] = sorted(s for s in bestand if name[s] not in krw)
            meldungen = hole_meldungen(http)
            erster = c.execute("SELECT COUNT(*) FROM upbit_lauf WHERE ok=1").fetchone()[0] == 0
            erg["startmarke"] = erster
            gesehen = {(i, k) for i, k in c.execute("SELECT id, kuerzel FROM upbit_meldung")}
            je_kuerzel = {}
            for s, k in name.items():
                je_kuerzel.setdefault(k, []).append(s)
            for i, titel, utc in meldungen:
                for k in listing(titel):
                    if (i, k) in gesehen:
                        continue
                    c.execute("INSERT OR IGNORE INTO upbit_meldung VALUES (?,?,?,?,?)", (i, k, titel, utc, jt))
                    erg["neu"] += 1
                    if erster:
                        continue
                    for s in je_kuerzel.get(k, []):
                        alter_h = (jetzt - datetime.strptime(utc, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)).total_seconds() / 3600
                        status = "faellig" if alter_h <= MAIL_HOECHSTENS_H else "verpasst"
                        c.execute("INSERT OR IGNORE INTO upbit_fall VALUES (?,?,?,?,?,?,?)", (i, s, k, utc, status, bestand[s], None))
                        c.execute("INSERT INTO protokoll VALUES (?,?,?,?)", (jt[:16], s, "upbit " + status,
                                  "Upbit-Listing %s (KRW) %s UTC, %.1f h alt: %s" % (k, utc[:16], alter_h, titel[:120])))
                        erg["faelle"].append({"id": i, "symbol": s, "status": status})
            if erster:
                c.execute("INSERT INTO protokoll VALUES (?,?,?,?)", (jt[:16], "-", "upbit startmarke",
                          "erster Lauf: %d Meldungen abgelegt, nichts gemailt" % len(meldungen)))
            for i, s, k, utc, menge in c.execute("SELECT id, symbol, kuerzel, utc, menge FROM upbit_fall WHERE status='faellig' AND mail_am IS NULL"):
                alter_h = (jetzt - datetime.strptime(utc, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)).total_seconds() / 3600
                if alter_h <= MAIL_HOECHSTENS_H and s in bestand:
                    titel = c.execute("SELECT titel FROM upbit_meldung WHERE id=? AND kuerzel=?", (i, k)).fetchone()
                    erg["faellig"].append({"id": i, "symbol": s, "kuerzel": k, "utc": utc, "menge": bestand[s], "alter_h": alter_h,
                                           "titel": titel[0] if titel else ""})
            erg["ok"] = True
        except Exception as e:                                       # noqa: BLE001
            erg["fehler"] = "%s: %s" % (type(e).__name__, str(e)[:200])
        c.execute("INSERT OR REPLACE INTO upbit_lauf VALUES (?,?,?,?,?,?,?,?)", (jt, int(erg["ok"]), erg["neu"], len(erg["faelle"]), erg["kreis"],
                  json.dumps(erg["ohne_krw"]), erg["fehler"], round(time.monotonic() - t0, 2)))
        c.commit()
    finally:
        c.close()
    return erg


def vermerke_mail(ordner: str, meldung_id: int, symbol: str) -> None:
    c = oeffne(ordner)
    try:
        jt = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
        c.execute("UPDATE upbit_fall SET mail_am=?, status='gemailt' WHERE id=? AND symbol=?", (jt, meldung_id, symbol))
        c.execute("INSERT INTO protokoll VALUES (?,?,?,?)", (jt, symbol, "upbit gemailt", "Verkaufsmail Upbit-Listing"))
        c.commit()
    finally:
        c.close()


# ══ die Mail (E-91: Coin · was tun · bis wann · warum) ══════════════════════════════════════════════════════════════════════
def mail(fall: dict, ausserhalb_binance: bool = False, gestakt: float | None = None, kurs_jetzt_usd: float | None = None,
         kurs_vorher_usd: float | None = None) -> tuple:
    s = fall["symbol"]
    b = "Spot: %s verkaufen (Upbit-Listing)" % s
    z = ["1  WAS ZU TUN IST",
         "  %s: die GANZE Position verkaufen – in den nächsten Stunden (%s Stück)." % (s, _SM._menge(fall["menge"]))]
    if gestakt:
        z.append("  Davon gestakt: %s Stück – bei Bitpanda wie Spot verkaufbar." % _SM._menge(gestakt))
    z += ["", "2  WARUM",
          "  Upbit hat %s für den Handel in Won (KRW) angekündigt: %s UTC, vor %s Stunden." % (
              fall["kuerzel"] if fall["kuerzel"] == s else "%s (%s)" % (s, fall["kuerzel"]), fall["utc"][:16], ("%.1f" % fall["alter_h"]).replace(".", ",")),
          "  " + BELEG + ".",
          "  In den ersten Stunden nach der Meldung stieg der Kurs im Median um 12 % – danach wurde der Anstieg abgegeben."]
    if ausserhalb_binance:
        z.append("  Hinweis: Gemessen ist auf Coins mit Binance-Spot; %s liegt außerhalb – angewandt, nicht auf ihm gemessen." % s)
    z += ["", "3  KONTEXT (keine Handlung)"]
    if kurs_jetzt_usd and kurs_vorher_usd:
        z.append("  Kurs gegen den letzten Tagesschluss vor der Meldung: %s %%." % ("%+.1f" % (100 * (kurs_jetzt_usd / kurs_vorher_usd - 1))).replace(".", ","))
    z.append("  Kosten bei Bitpanda je Seite nach Klasse: H %s %% · M %s %% · S %s %% (nur Information)." % tuple(
        ("%.2f" % _SM.KOSTEN_JE_SEITE[k]).replace(".", ",") for k in ("H", "M", "S")))
    z.append("  Wiedereinstieg und Erlös: nicht gemessen.")
    z.append("  Meldung: %s" % (MELDUNG_LINK % fall["id"]))
    z.append("  Titel: %s" % fall.get("titel", ""))
    z += ["", "4  TECHNIK", "  Spot B3 Upbit-Verkaufsanlass · Regel wie die Messung C2-b · Mail nur bis %d h nach der Meldung." % MAIL_HOECHSTENS_H]
    return b, "\n".join(z)


# ══ Lesen fuer Statusseite, Teilexport und GUI ══════════════════════════════════════════════════════════════════════════════
def stand(ordner: str) -> dict:
    p = os.path.join(ordner, ABLAGE)
    if not os.path.exists(p):
        return {"ablage": False}
    c = _SM._ro(p)
    try:
        if not c.execute("SELECT name FROM sqlite_master WHERE name='upbit_lauf'").fetchone():
            return {"ablage": True, "laeufe": 0}
        n, n_ok = c.execute("SELECT COUNT(*), SUM(ok) FROM upbit_lauf").fetchone()
        letzter = c.execute("SELECT am, ok, neu, faelle, kreis, ohne_krw, fehler, sekunden FROM upbit_lauf ORDER BY am DESC LIMIT 1").fetchone()
        letzter_fehler = c.execute("SELECT am, fehler FROM upbit_lauf WHERE ok=0 ORDER BY am DESC LIMIT 1").fetchone()
        je = [tuple(r) for r in c.execute("SELECT status, COUNT(*) FROM upbit_fall GROUP BY status ORDER BY 2 DESC")]
        meldungen = c.execute("SELECT COUNT(*), MAX(utc) FROM upbit_meldung").fetchone()
        letzte = [tuple(r) for r in c.execute("SELECT am, symbol, art, text FROM protokoll WHERE art LIKE 'upbit%' ORDER BY rowid DESC LIMIT 5")]
        return {"ablage": True, "laeufe": n or 0, "ok": n_ok or 0, "letzter": letzter, "letzter_fehler": letzter_fehler, "je_status": je,
                "meldungen": meldungen[0] or 0, "juengste_meldung": meldungen[1], "ohne_krw": json.loads(letzter[5]) if letzter and letzter[5] else [],
                "letzte": letzte}
    finally:
        c.close()
