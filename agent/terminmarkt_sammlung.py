# -*- coding: utf-8 -*-
"""Die Terminmarkt-Daten sammeln und ihre Frische ueberwachen (Schritt 54, 14.09.2026).

WARUM ES DIESES MODUL GIBT - Befund 2.452. Bis zum 12.09. schrieb das alte
Hebel-Screening `open_interest_snapshot` als NEBENPRODUKT. Mit
`hebel_screening.aktiv: false` (Schritt 40) schrieb sie niemand mehr, und
`positionierung` las ohne Altersgrenze weiter: Rolle BC und Rolle G bekamen
eingefrorene Saetze wie ,in den letzten 8 Stunden praktisch unveraendert' -
bei 13 Werten sogar aus dem Juli (2.452-alt), weil das Screening nur Werte mit
erlaubter Hebelpruefung abfragte.

NUTZERENTSCHEIDUNGEN 14.09.2026:

    ein EIGENER Job        nicht im Job der Rollen-Kette - dauert dort ein
                           Umlauf laenger als 15 Minuten, fiele das Sammeln aus
    ALLE Kryptowerte       die die Kette beurteilt, nicht nur die mit erlaubter
                           Hebelpruefung
    Meldegrenze 6 h        eine Mail je Ausfall, gezaehlt ab dem App-Start
    Einzelwert 24 h        ein Wert hatte Daten und liefert nicht mehr, waehrend
                           die anderen frisch sind - genau der Juli-Fall
    keine Entwarnung       jede weitere Mail stumpft ab
    alte Warnung ersetzt   die Mail ,8 Fehlschlaege in Folge' kam fuer Werte,
                           die keine Boerse fuehrt, jeden Tag neu

Die LESEgrenze (2 h) steht nicht hier, sondern beim Leser `positionierung` -
dort, wo entschieden wird, ob ein Satz entsteht.

⚠️ DER WAECHTER LAEUFT NICHT IN DIESEM JOB. `frische()` wird vom Job der
Rollen-Kette aufgerufen: ein Waechter im selben Job schwiege genau dann, wenn
der Job ausfaellt. Die Rollen-Kette ist ohnehin der Verbraucher der Daten.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Ab wie vielen Stunden ohne jede neue Zeile eine Mail kommt. Gemessen an der
# Produktionssicherung (01.08.-12.09.): jobweite Luecken ueber 2 h 15-mal, ueber
# 4 h 10-mal, ueber 6 h 5-mal - alles echte Ausfaelle (Notebook aus, 97 h am
# 10.08.). Kurze Luecken (Neustart nach dem Pull) liegen fast alle unter 90 min.
MELDEGRENZE_STUNDEN = 6.0

# Ab wann EIN Wert als ausgefallen gilt, waehrend die anderen frisch sind.
# Ein einzelner Abruf scheitert oefter (528 Luecken ueber 1 h bei Binance in
# sechs Wochen) - ein ganzer Tag ohne Zeile ist kein Aussetzer mehr.
EINZELWERT_GRENZE_STUNDEN = 24.0


def werte_der_kette(watchlist) -> list:
    """Die Assets, die die Rollen-Kette als Krypto beurteilt.

    DIESELBE ABGRENZUNG WIE `assetklassen.gruppiere`: Gruppe `krypto`, ohne
    Cash-Aequivalente. KEIN Filter auf `hebel_pruefung_erlaubt` - genau der
    liess 13 Werte seit Juli ohne Daten (2.452-alt)."""
    from agent import assetklassen as AK

    return [a for a in (watchlist or [])
            if not getattr(a, "ist_cash_aequivalent", False)
            and AK.gruppe(a) == "krypto"]


def sammle(conn, assets, kraken_client, abruf=None) -> dict:
    """Einen Durchlauf abfragen und schreiben.

    DIE ABRUFFUNKTION BLEIBT DIE BEWAEHRTE (`hebel_screening.
    fetch_and_store_oi_snapshot`): dieselben Zeilen, dieselben Boersen-
    Etiketten, derselbe gemeinsame `fetched_at` JE ASSET (nicht je
    Durchlauf - Korrektur aus dem Review 14.09.) - `positionierung.
    _divergenz` paart die Boersen eines Assets genau darauf.

    JEDER WERT EINZELN GEFANGEN. Ein Fehler bei einem Wert darf die anderen
    nicht mitnehmen.

    Der Abdeckungszaehler (`oi_abdeckung_status`) wird weiter gefuehrt - die
    Watchlist-Ansicht zeigt ihn an. Gemailt wird daraus nicht mehr."""
    import database.db as db

    if abruf is None:
        from agent.krypto.hebel_screening import fetch_and_store_oi_snapshot as abruf

    mit_daten, ohne, fehler = [], [], []
    for asset in assets:
        sym = asset.symbol
        try:
            erfolg = bool(abruf(conn, asset, kraken_client))
        except Exception as exc:                             # noqa: BLE001
            logger.info("Terminmarkt-Sammlung %s fehlgeschlagen: %s", sym, exc)
            fehler.append(sym)
            erfolg = False
        (mit_daten if erfolg else ohne).append(sym)
        try:
            db.record_oi_abdeckung_ergebnis(conn, sym, erfolg)
        except Exception as exc:                             # noqa: BLE001
            logger.info("OI-Abdeckung %s nicht vermerkt: %s", sym, exc)
    return {"werte": len(assets), "mit_daten": mit_daten, "ohne": ohne,
            "fehler": fehler}


def _zeit(text) -> datetime | None:
    try:
        t = datetime.fromisoformat(str(text))
    except (TypeError, ValueError):
        return None
    return t if t.tzinfo else t.replace(tzinfo=timezone.utc)


def _stunden(von: datetime, bis: datetime) -> float:
    return (bis - von).total_seconds() / 3600.0


def frische(conn, symbole, jetzt: datetime | None = None,
            app_start: datetime | None = None) -> dict:
    """Wie frisch sind die Terminmarkt-Daten - insgesamt und je Wert?

    GEZAEHLT AB DEM APP-START. Sonst meldet ein Neustart nach einer
    Notebook-Pause sofort ,seit 97 Stunden' - obwohl die Sammlung nie laufen
    konnte. Eine App, die aus war, ist kein Datenausfall.

    DREI ARTEN WERTE, und nur zwei davon sind ein Befund:
        gesamt    keine neue Zeile fuer IRGENDEINEN Wert seit >= 6 h
        einzeln   ein Wert HATTE Daten und liefert seit >= 24 h nichts
        nie       keine Boerse fuehrt den Wert (CANTON, SUPRA, VSN, XNO am
                  14.09.) - das ist ein Zustand, kein Ausfall
    """
    jetzt = jetzt or datetime.now(timezone.utc)
    symbole = sorted({str(s).upper() for s in (symbole or [])})
    stand: dict[str, datetime] = {}
    if symbole:
        platz = ",".join("?" * len(symbole))
        for sym, t in conn.execute(
                "SELECT symbol, MAX(fetched_at) FROM open_interest_snapshot "
                f"WHERE symbol IN ({platz}) GROUP BY symbol", symbole):
            z = _zeit(t)
            if z is not None:
                stand[str(sym).upper()] = z

    def _bezug(t: datetime | None) -> datetime | None:
        kandidaten = [x for x in (t, app_start) if x is not None]
        return max(kandidaten) if kandidaten else None

    neueste = max(stand.values()) if stand else None
    b = _bezug(neueste)
    gesamt_stunden = _stunden(b, jetzt) if b is not None else None
    gesamt = gesamt_stunden is not None and gesamt_stunden >= MELDEGRENZE_STUNDEN

    einzeln = []
    if not gesamt:
        for sym, t in sorted(stand.items()):
            h = _stunden(_bezug(t), jetzt)
            if h >= EINZELWERT_GRENZE_STUNDEN:
                einzeln.append({"symbol": sym, "stand": t,
                                "stunden": _stunden(t, jetzt)})
    return {"gesamt": gesamt, "neueste": neueste,
            "gesamt_stunden": None if neueste is None else _stunden(neueste, jetzt),
            "einzeln": einzeln,
            "nie": [s for s in symbole if s not in stand]}


class Meldezustand:
    """Was in DIESEM Prozess schon gemeldet ist - eine Mail je Ausfall.

    IM SPEICHER, NICHT IN DER DATENBANK, und das ist Absicht: nach einem
    Neustart zaehlt der Ausfall ohnehin neu ab dem App-Start."""

    def __init__(self):
        self.gesamt = False
        self.einzeln: set[str] = set()


def _stand_text(t: datetime | None) -> str:
    if t is None:
        return "noch nie"
    return t.astimezone().strftime("%d.%m. %H:%M")


def meldung(befund: dict, zustand: Meldezustand):
    """(betreff, text, vormerken) oder None - hoechstens EINE Mail je Aufruf.

    `vormerken` traegt der Aufrufer erst nach erfolgreichem Versand ein
    (dasselbe Muster wie die frueher dort stehende, am 14.09. ersetzte
    OI-Abdeckungswarnung): scheitert der
    Versand, soll der naechste Lauf es wieder versuchen.

    ⚠️ ERHOLT SICH DER BESTAND, WIRD DER ZUSTAND SOFORT ZURUECKGESETZT - auch
    ohne Mail. Sonst wuerde der naechste Ausfall verschwiegen."""
    if not befund.get("gesamt"):
        zustand.gesamt = False
    aktuell = {e["symbol"] for e in befund.get("einzeln") or []}
    zustand.einzeln &= aktuell

    if befund.get("gesamt"):
        if zustand.gesamt:
            return None
        h = befund.get("gesamt_stunden")
        seit = ("seit %d Stunden" % int(h)) if h is not None else "seit dem App-Start"
        betreff = f"TradingInfoTool: Terminmarkt-Daten {seit} nicht aktualisiert"
        text = (
            f"Seit {_stand_text(befund.get('neueste'))} ist fuer KEINEN "
            "Kryptowert eine neue Terminmarkt-Zeile gekommen (Open Interest, "
            "Finanzierungsrate, Anteil der Long-Konten).\n\n"
            "WAS DAS BEDEUTET: Die Urteile laufen weiter, aber ohne Terminmarkt. "
            "Rolle BC und Rolle G bekommen statt der Zahlen den Satz, dass keine "
            "aktuelle Angabe vorliegt (ab 2 Stunden Alter).\n\n"
            "WAS ZU TUN IST: Im Log nach ,Terminmarkt-Sammlung' suchen - laeuft "
            "der Job ueberhaupt, und sind Binance, Bybit, OKX und Kraken "
            "erreichbar?\n\n"
            "Zu diesem Ausfall kommt keine weitere Mail. Sobald wieder Daten "
            "fliessen, gilt er als beendet.")
        return betreff, text, ("gesamt", None)

    neu = aktuell - zustand.einzeln
    if not neu:
        return None
    zeilen = []
    for e in befund["einzeln"]:
        marke = "NEU  " if e["symbol"] in neu else "     "
        zeilen.append("  %s%-8s letzter Stand %s (vor %d Stunden)" % (
            marke, e["symbol"], _stand_text(e["stand"]), int(e["stunden"])))
    n = len(befund["einzeln"])
    betreff = (f"TradingInfoTool: Terminmarkt-Daten fuer {n} "
               f"Wert{'e' if n != 1 else ''} seit ueber 24 Stunden veraltet")
    text = (
        "Die Terminmarkt-Sammlung laeuft, aber fuer diese Werte kommt seit "
        "mindestens 24 Stunden keine neue Zeile:\n\n" + "\n".join(zeilen) + "\n\n"
        "WAS DAS BEDEUTET: Fuer diese Werte bekommen Rolle BC und Rolle G "
        "keinen Terminmarkt-Satz, sondern den Hinweis, dass keine aktuelle "
        "Angabe vorliegt.\n\n"
        "WAS ZU TUN IST: Pruefen, ob der Wert an Binance, Bybit oder OKX noch "
        "gehandelt wird (Umbenennung, Delisting) - das Log nennt je Wert, "
        "welche Boerse scheitert.\n\n"
        "Zu diesen Werten kommt keine weitere Mail, solange sie ausfallen.")
    return betreff, text, ("einzeln", aktuell)


def vormerken(zustand: Meldezustand, marke) -> None:
    art, werte = marke
    if art == "gesamt":
        zustand.gesamt = True
    else:
        zustand.einzeln = set(werte or ())
