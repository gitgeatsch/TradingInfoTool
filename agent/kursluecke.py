# -*- coding: utf-8 -*-
"""SCHLUSSKURS-RUECKFALL, WENN YAHOOS TAGESHISTORIE HINKT (15.09.2026)

⚠️⚠️ ANLASS - Befund 2.455-kapitalkurse. Fuer vier Xetra-Titel (CEBS.DE,
VVMX.DE, DBPK.DE, EXH3.DE) enthielt Yahoos TAGESHISTORIE den Montag am
Dienstag um 05:45 UTC noch nicht - und das unstabil: 2 von rund 15 Abfragen
lieferten ihn, die uebrigen nicht, auch mit gleichen Parametern. Die
Kursangabe desselben Titels kannte ihn richtig: CEBS letzter Handel Montag
15:35 UTC zu 9,745, Vortagesschluss 10,14. Der Portfoliowert rechnete deshalb
jeden Werktag mit dem Kurs des Vortags, und Rolle A sah morgens den Vorvortag.

DIE REGEL. Fehlt einer Reihe nach dem normalen Laden der letzte abgeschlossene
Handelstag, fragt der Ladeweg den LETZTEN HANDEL des Titels ab (Zeitpunkt in
der Zeitzone des Handelsplatzes, Kurs, Tageshoch und -tief). Eine Kerze wird
geschrieben, wenn

    1  der Handelstag NACH der letzten Kerze der Reihe liegt
    2  die Sitzung dieses Tages BEENDET ist - der Platz ist beim Abruf schon in
       der naechsten Handelsperiode oder deren Ende ist vorbei
    3  der Kurs positiv ist und die Waehrung der Reihe entspricht

Sie traegt `quelle='schnappschuss'`. Liefert Yahoo die echte Tageskerze
spaeter, ueberschreibt der normale Ladeweg sie (`upsert_ohlc_points` schreibt
die Quelle mit), und die Abweichung steht im Log - der Rueckfall prueft sich so
selbst gegen den offiziellen Kurs.

⚠️ HANDELSPLATZGENAU, OHNE FEIERTAGSKALENDER. Die Angabe sagt, wann DIESER
Platz zuletzt gehandelt hat. Hatte er am Bezugstag keinen Handel - Feiertag,
oder bei einem duennen Platz schlicht kein Umsatz -, entsteht keine Kerze, und
die Eingabepruefung des Portfoliowerts nennt das als Grund statt einer WARNING.

NICHT FUER: Krypto (eigener Job, handelt taeglich) und die rekonstruierten
Reihen (OD7C/H/L/N, 3QSS) - sie haengen an ihrer Referenz. (Bis 15.09.2026
stand hier ,deren Kursangabe ist bei Yahoo veraltet (OD7C.SG: letzter Handel
2022)' - und wurde als Eigenschaft der Instrumente gelesen statt als Fehler
des Kuerzels. Der Preis war der ANKER der Rekonstruktion; siehe unten.)

⚠️⚠️ DIE KURSANGABE SELBST (15.09.2026, Befund 2.455-kurs-od7-eingefroren).
OD7H.SG und OD7C.SG meldeten zwei Jahre lang den Preis vom 02.09.2022
(18,215 / 30,098 EUR statt 36,50 / 47,43). `price_cache.fetched_at` war jede
Viertelstunde frisch, die rekonstruierte Reihe bewegte sich mit ihrer
Referenz - nur ihr NIVEAU lag bei der Haelfte. Keine Pruefung sah das, weil
alle das Abrufalter pruefen, keine das Alter des Handels an der Quelle.
`kursangaben` fragt deshalb einmal taeglich je Nicht-Krypto-Wert den letzten
Handel ab (auch fuer ,nur fast_info'-Ticker), `tote_kursangaben` nennt jeden,
dessen letzter Handel laenger als `KURSANGABE_GRENZE_HANDELSTAGE` zurueckliegt
- die Datenfrische meldet sie unter ,Kursreihen'.
"""
from __future__ import annotations

from datetime import datetime, timezone

QUELLE_SCHNAPPSCHUSS = "schnappschuss"
# Ab welcher Abweichung zur spaeter gelieferten echten Kerze der Ersatz im Log
# eine WARNING ist statt einer INFO. Ein Schlusskurs ist ein Schlusskurs - mehr
# als ein halbes Prozent heisst, dass die Kursangabe nicht der Tagesschluss war.
ABWEICHUNG_WARNUNG_PROZENT = 0.5
# Ab wann eine Kursangabe als TOT gilt: eine volle Handelswoche ohne Handel an
# der Quelle. Bewusst weiter als die Reihengrenze der Datenfrische (3) - ein
# duenner Platz wie X136.MU handelt nicht jeden Tag, und gesucht wird ein
# eingefrorenes Kuerzel (Befund: zwei JAHRE), kein ruhiger Tag.
KURSANGABE_GRENZE_HANDELSTAGE = 5
# Meta-Schluessel, unter dem der 05:30-Job das Ergebnis ablegt.
META_KURSANGABEN = "kursangaben_json"


def sitzung_beendet(handel: dict, jetzt: datetime | None = None) -> bool:
    """Ist die Sitzung des letzten Handelstags vorbei?

    `handel["datum"]` ist der Tag des letzten Handels in der Zeitzone des
    Platzes; `periode_start_datum`/`periode_ende_utc` beschreiben die AKTUELLE
    Handelsperiode laut Yahoo. Liegt deren Beginn an einem spaeteren Tag, ist
    der Handelstag abgeschlossen; ist es noch derselbe Tag, erst nach ihrem
    Ende."""
    jetzt = jetzt or datetime.now(timezone.utc)
    tag, beginn, ende = (handel.get("datum"), handel.get("periode_start_datum"),
                         handel.get("periode_ende_utc"))
    if not tag:
        return False
    if beginn and tag < beginn:
        return True
    return bool(ende and beginn == tag and jetzt >= ende)


def kerze(symbol: str, waehrung: str, handel: dict, letzte_kerze: str | None,
          jetzt: datetime | None = None):
    """Die Ersatzkerze als `OhlcPoint` - oder None, wenn eine Bedingung fehlt."""
    from database.models import OhlcPoint

    jetzt = jetzt or datetime.now(timezone.utc)
    if not handel or not handel.get("datum"):
        return None
    if letzte_kerze and handel["datum"] <= str(letzte_kerze)[:10]:
        return None
    if not sitzung_beendet(handel, jetzt):
        return None
    kurs = handel.get("kurs")
    if not kurs or kurs <= 0:
        return None
    if str(handel.get("waehrung") or "").upper() != str(waehrung or "").upper():
        return None
    hoch = handel.get("hoch") if (handel.get("hoch") or 0) > 0 else kurs
    tief = handel.get("tief") if (handel.get("tief") or 0) > 0 else kurs
    return OhlcPoint(symbol=symbol, currency=waehrung, date=handel["datum"],
                     open=handel.get("eroeffnung") or kurs,
                     high=max(hoch, kurs), low=min(tief, kurs), close=kurs,
                     volume=float(handel.get("umsatz") or 0.0),
                     fetched_at=jetzt.isoformat())


def ersetzte(vorher: list, conn) -> list[dict]:
    """Welche Ersatzkerzen hat der Ladeweg durch eine ECHTE ersetzt - und mit
    welcher Abweichung? `vorher`: Zeilen (symbol, currency, date, close) mit
    quelle='schnappschuss' VOR dem Laden."""
    aus = []
    for symbol, waehrung, datum, alt in vorher:
        z = conn.execute(
            "SELECT close, quelle FROM price_history_ohlc WHERE symbol=? AND currency=? "
            "AND date=?", (symbol, waehrung, datum)).fetchone()
        if not z or z[1] == QUELLE_SCHNAPPSCHUSS or not alt:
            continue
        aus.append({"symbol": symbol, "datum": datum, "ersatz": alt, "echt": z[0],
                    "abweichung_prozent": 100.0 * (z[0] - alt) / alt})
    return aus


def _wertpapier_ticker(watchlist) -> dict[str, str]:
    """symbol -> yfinance-Ticker fuer jeden Nicht-Krypto-Wert mit Ticker
    (ohne Cash-Aequivalente)."""
    aus = {}
    for a in watchlist or []:
        klasse = str(getattr(a, "assetklasse", "") or "krypto").lower()
        ticker = getattr(a, "yfinance_symbol", None)
        if klasse == "krypto" or not ticker or getattr(a, "ist_cash_aequivalent", False):
            continue
        aus[str(a.symbol).upper()] = str(ticker)
    return aus


def kursangaben(watchlist, abfrage, jetzt: datetime | None = None) -> dict:
    """{symbol: {ticker, letzter_handel, geprueft_am}} - `letzter_handel` ist
    der Tag des letzten Handels am Platz oder None (keine Angabe). Fail-soft
    je Titel: ein Fehler ergibt None, nicht den Abbruch."""
    jetzt = jetzt or datetime.now(timezone.utc)
    aus = {}
    for symbol, ticker in sorted(_wertpapier_ticker(watchlist).items()):
        try:
            handel = abfrage(ticker) or {}
        except Exception:                                    # noqa: BLE001
            handel = {}
        aus[symbol] = {"ticker": ticker, "letzter_handel": handel.get("datum"),
                       "geprueft_am": jetzt.isoformat()}
    return aus


def tote_kursangaben(stand: dict, watchlist, heute=None) -> list[dict]:
    """Die Kursangaben, deren letzter Handel zu lange zurueckliegt - im Format
    der Datenfrische (`veraltete_werte`), damit Mail und Export sie ohne eigenen
    Zweig anzeigen.

    ⚠️ NUR, WENN DER TICKER NOCH DER DER WATCHLIST IST. Nach einer Umstellung
    (OD7H.SG -> GB00B15KXX56.SG) steht bis zum naechsten 05:30-Lauf der alte
    Eintrag - er waere ein Fehlalarm fuer ein Kuerzel, das niemand mehr fragt.
    ⚠️ KEINE ANGABE IST KEIN BEFUND: ein Netzfehler um 05:30 soll keine Mail
    ausloesen; einen toten Abruf findet die Datenfrische ueber den Job."""
    from staleness import handelstage_alter

    ticker = _wertpapier_ticker(watchlist)
    aus = []
    for symbol, e in sorted((stand or {}).items()):
        if ticker.get(symbol) != e.get("ticker") or not e.get("letzter_handel"):
            continue
        alter = handelstage_alter(e["letzter_handel"], heute)
        if alter is not None and alter > KURSANGABE_GRENZE_HANDELSTAGE:
            aus.append({"symbol": "%s (Kursangabe %s)" % (symbol, e["ticker"]),
                        "stand": str(e["letzter_handel"])[:10], "alter": alter,
                        "einheit": "Handelstage", "grenze": KURSANGABE_GRENZE_HANDELSTAGE,
                        "job": "refresh_aktien_ohlc", "art": "kursangabe"})
    return aus
