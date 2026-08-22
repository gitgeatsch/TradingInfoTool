# -*- coding: utf-8 -*-
"""H als SCHATTEN - markieren, nicht sperren (22.08.2026, V1).

⚠️ DIESES MODUL SPERRT NICHTS. Es rechnet ein Merkmal aus, schreibt es weg
und stellt zwei Zeilen fuer die Mail bereit. Kein Signal wird verhindert,
keine Reihenfolge geaendert, kein Budget umgelenkt.

DER GRUND FUER DIESE BAUFORM. H ist auf 523 Binance-USDT-Reihen gemessen
(Kapitel 108-122): +4,5 Punkte Trefferquote gegen eine Zufallsschwelle von
+2,6, bestaetigt in Large (+5,9) und Small (+7,9). Auf der echten Watchlist
stimmt der Punktschaetzer (+4,8) - aber 27 Reihen tragen die noetige Schwelle
(+9,2) NICHT. Der Befund steht also auf fremden Reihen, nicht auf unseren.

    Und die Zahl, um die es geht: H trifft auf 3,3 % der Ankertage zu.
    Ueber 29 Symbole ist das rund EIN Symboltag pro Tag - aus 24
    Eroeffnungen wuerde ungefaehr eine.

Ein Schnitt dieser Groesse wird nicht auf einen Befund von fremden Reihen
gebaut. Deshalb erst der Schatten: vier Wochen mitschreiben, dann pruefen, ob
die von H aussortierten Signale WIRKLICH die schlechteren waren - auf unseren
eigenen. Erst danach die Entscheidung, ob H sperrt, die Reihenfolge bestimmt
oder die Positionsgroesse.

⚠️ NUR LONG. Kapitel 110 hat die gespiegelte Bedingung H' gemessen: sie
spiegelt NICHT. Sie hilft im Bullenmarkt und schadet im Baermarkt, genau wie
H - die Richtung dreht nicht mit. Fuer SHORT ist H damit unbelegt, und
unbelegt heisst hier: `h = None`, nicht `h = False`. Ein Merkmal, das man
nicht kennt, darf nie aussehen wie eines, das man geprueft hat.

DIE DEFINITION IST WOERTLICH DIE DER MESSUNG (`messe_marken.laufe`):

    A  frei      keine Marke ueber dem Kurs mit >= 2 Beruehrungen
                 unterhalb des ZIELS
    B  gedeckt   eine Marke unter dem Kurs mit >= 2 Beruehrungen
                 oberhalb des STOPS
    H  = A und B

⚠️ EIN UNTERSCHIED ZUR MESSUNG BLEIBT, UND ER IST BEABSICHTIGT. Dort standen
Stop und Ziel auf fester Geometrie (k * ATR, CRV 2,0); hier stehen die
ECHTEN Werte des Signals. Das ist die Groesse, die uns interessiert - ob H
auf dem hilft, was wir tatsaechlich handeln. Kapitel 117/118 stuetzen das:
H braucht keine eigene Geometrie, sein Optimum liegt in derselben Ecke wie
das der Basis.

⚠️ DESHALB WERDEN DIE ZUTATEN MITGESCHRIEBEN, nicht nur das Urteil. Preis
und Beruehrungszahl beider Marken stehen in der Zeile; wer H spaeter anders
schneiden will (drei Beruehrungen, ein anderer Abstand), rechnet es aus den
Rohdaten nach, ohne vier Wochen zu verlieren.
"""
from __future__ import annotations

import json
import logging
import sqlite3

logger = logging.getLogger(__name__)

# Dieselbe Zahl wie `messe_marken.MIN_BERUEHRUNGEN` - ein einzelner
# Wendepunkt ist keine Marke.
MIN_BERUEHRUNGEN = 2

# Was auf 523 Reihen gemessen wurde, in Punkten Trefferquote. Steht hier,
# damit die Mail den Befund nennen kann, auf den sie sich beruft.
GEMESSEN = {"vorsprung_punkte": 4.5, "schwelle_punkte": 2.6,
            "reihen": 523, "anteil_traeger": 0.033,
            "kapitel": "108-122"}

_TABELLE = "vorfilter_schatten"


def _tabelle(conn) -> bool:
    try:
        conn.execute(
            f"""CREATE TABLE IF NOT EXISTS {_TABELLE} (
                    id INTEGER PRIMARY KEY,
                    erfasst_am TEXT NOT NULL,
                    signal_id INTEGER,
                    symbol TEXT NOT NULL,
                    assetklasse TEXT,
                    instrument TEXT,
                    ist_short INTEGER,
                    h INTEGER,
                    frei INTEGER,
                    gedeckt INTEGER,
                    grund TEXT,
                    zutaten_json TEXT)""")
        conn.execute(
            f"CREATE INDEX IF NOT EXISTS idx_{_TABELLE}_signal "
            f"ON {_TABELLE}(signal_id)")
        conn.commit()
        return True
    except sqlite3.Error as exc:
        logger.info("Vorfilter-Tabelle nicht anlegbar: %s", exc)
        return False


# ⚠️ AUF WELCHER ANLAGEKLASSE IST H UEBERHAUPT GEMESSEN? Auf genau einer.
# Die 523 Reihen sind Binance-USDT - also Krypto. Fuer Aktien, Rohstoffe,
# Themen-ETF und Hedge ist H nicht etwa unbestaetigt, sondern NIE GEPRUEFT;
# Kapitel 106 hat gezeigt, dass 2 Aktien- und 4 ETF-Reihen dafuer nicht
# reichen. Der Schatten laeuft trotzdem ueber alle Klassen - sonst haben wir
# in vier Wochen wieder nur Krypto-Daten und stehen an derselben Stelle.
# Aber die Mail sagt es dazu.
GEMESSEN_AUF = "krypto"


def bewerte(marken_werte: dict | None, stop_eur, ziel_eur,
            ist_short: bool = False, assetklasse: str = "") -> dict:
    """A, B, H - und die Zutaten. Urteilt ueber das Signal NICHT.

    Gibt `h=None` zurueck, wenn die Frage hier nicht beantwortbar ist:
    bei SHORT (unbelegt, siehe Modulkopf) und wenn Marken, Stop oder Ziel
    fehlen. `None` ist nicht `False` - das eine heisst "wissen wir nicht",
    das andere "geprueft und nein"."""
    aus = {"h": None, "frei": None, "gedeckt": None, "grund": "",
           "widerstand_eur": None, "widerstand_beruehrungen": None,
           "traeger_eur": None, "traeger_beruehrungen": None,
           "stop_eur": stop_eur, "ziel_eur": ziel_eur,
           "assetklasse": str(assetklasse or "").lower(),
           "in_gemessener_klasse":
               str(assetklasse or "").lower() == GEMESSEN_AUF}
    if ist_short:
        aus["grund"] = ("SHORT - die gespiegelte Bedingung wurde gemessen "
                        "und traegt nicht (Kapitel 110)")
        return aus
    if not marken_werte:
        aus["grund"] = "keine Marken ermittelt"
        return aus
    try:
        stop = float(stop_eur)
        ziel = float(ziel_eur)
    except (TypeError, ValueError):
        aus["grund"] = "Stop oder Ziel fehlt"
        return aus
    if not (stop > 0 and ziel > 0):
        aus["grund"] = "Stop oder Ziel nicht positiv"
        return aus

    def traegt(m) -> bool:
        return int((m or {}).get("beruehrungen") or 0) >= MIN_BERUEHRUNGEN

    # A - FREIER WEG: keine mehrfach beruehrte Marke unter dem Ziel.
    oben = [m for m in (marken_werte.get("oben") or [])
            if traegt(m) and m.get("preis_eur") is not None
            and float(m["preis_eur"]) < ziel]
    aus["frei"] = not oben
    if oben:
        # Die NAECHSTE am Kurs ist die, auf die er zuerst trifft - dieselbe
        # Wahl wie in der Messung (Kapitel 112), nicht "die staerkste".
        w = min(oben, key=lambda m: float(m["preis_eur"]))
        aus["widerstand_eur"] = float(w["preis_eur"])
        aus["widerstand_beruehrungen"] = int(w.get("beruehrungen") or 0)

    # B - STOP GEDECKT: eine mehrfach beruehrte Marke ueber dem Stop.
    unten = [m for m in (marken_werte.get("unten") or [])
             if traegt(m) and m.get("preis_eur") is not None
             and float(m["preis_eur"]) > stop]
    aus["gedeckt"] = bool(unten)
    if unten:
        t = max(unten, key=lambda m: float(m["preis_eur"]))
        aus["traeger_eur"] = float(t["preis_eur"])
        aus["traeger_beruehrungen"] = int(t.get("beruehrungen") or 0)

    aus["h"] = bool(aus["frei"] and aus["gedeckt"])
    return aus


def saetze(b: dict | None) -> list[str]:
    """Die Zeilen fuer die Mail. SPERREN NICHTS - das steht auch da."""
    if not b:
        return []
    from agent.schreibweise import de

    kopf = "Vorfilter H (Schattenmessung, sperrt nichts):"
    if b.get("h") is None:
        return [kopf, f"   Hier nicht bestimmbar: {b.get('grund') or '?'}"]

    # ⚠️ DIE BEIDEN TEILE EINZELN NENNEN, nicht nur das Ergebnis. Faellt H
    # aus, will man wissen WORAN - sonst ist die Zeile eine Note ohne
    # Begruendung, und niemand kann ihr widersprechen.
    if b["frei"]:
        a_zeile = "   A Weg zum Ziel frei: ja - keine mehrfach beruehrte Marke darunter"
    else:
        a_zeile = (f"   A Weg zum Ziel frei: NEIN - Marke bei "
                   f"{de(b['widerstand_eur'], 4)} EUR "
                   f"({b['widerstand_beruehrungen']}-mal beruehrt) liegt "
                   f"vor dem Ziel")
    if b["gedeckt"]:
        b_zeile = (f"   B Stop gedeckt: ja - Marke bei "
                   f"{de(b['traeger_eur'], 4)} EUR "
                   f"({b['traeger_beruehrungen']}-mal beruehrt) liegt "
                   f"ueber dem Stop")
    else:
        b_zeile = "   B Stop gedeckt: NEIN - keine mehrfach beruehrte Marke ueber dem Stop"

    if b["h"]:
        urteil = ("   TRIFFT ZU (A und B) - auf 523 fremden Reihen hatten "
                  "solche Einstiege 4,5 Punkte mehr Treffer.")
    else:
        urteil = ("   trifft NICHT zu - auf 523 fremden Reihen waren solche "
                  "Einstiege die schlechtere Haelfte.")
    # ⚠️ AUSSERHALB VON KRYPTO IST DAS KEINE SCHWAECHERE AUSSAGE, SONDERN
    # GAR KEINE. Die 523 Reihen sind Binance-USDT; fuer Aktien, Rohstoffe,
    # ETF und Hedge wurde H nie gemessen. Wer die Zeile dort liest wie bei
    # Krypto, uebertraegt einen Befund auf eine Grundgesamtheit, die ihn nie
    # gesehen hat - derselbe Fehler wie in Kapitel 109.
    if b.get("in_gemessener_klasse"):
        schluss = ("⚠️ NUR MITGESCHRIEBEN, NICHT ANGEWENDET - der Befund "
                   "steht auf fremden Reihen und ist auf unseren 29 "
                   "Symbolen noch nicht bestaetigt. Diese Zeilen sperren "
                   "nichts.")
    else:
        schluss = (f"⚠️ AUF {(b.get('assetklasse') or '?').upper()} NIE "
                   f"GEMESSEN - die 523 Reihen sind Krypto. Hier wird das "
                   f"Merkmal nur MITGESCHRIEBEN, damit es spaeter ueberhaupt "
                   f"pruefbar wird. Es sagt fuer diese Klasse bisher nichts.")
    return [kopf, a_zeile, b_zeile, urteil, schluss]


def schreibe(conn, *, symbol: str, bewertung: dict,
             signal_id: int | None = None, assetklasse: str = "",
             instrument: str = "", jetzt: str | None = None) -> bool:
    """Eine Schattenzeile. Faellt sie aus, fehlt ein Messpunkt - nie ein
    Signal; deshalb faengt sie breit ab und meldet nur."""
    from datetime import datetime, timezone

    if conn is None or not bewertung or not _tabelle(conn):
        return False
    zutaten = {k: bewertung.get(k) for k in
               ("widerstand_eur", "widerstand_beruehrungen", "traeger_eur",
                "traeger_beruehrungen", "stop_eur", "ziel_eur")}
    try:
        conn.execute(
            f"INSERT INTO {_TABELLE} (erfasst_am, signal_id, symbol, "
            f"assetklasse, instrument, ist_short, h, frei, gedeckt, grund, "
            f"zutaten_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (jetzt or datetime.now(timezone.utc).isoformat(),
             int(signal_id) if signal_id else None, str(symbol).upper(),
             str(assetklasse or ""), str(instrument or ""),
             1 if bewertung.get("stop_eur") is not None
             and "SHORT" in (bewertung.get("grund") or "") else 0,
             None if bewertung.get("h") is None else int(bewertung["h"]),
             None if bewertung.get("frei") is None
             else int(bewertung["frei"]),
             None if bewertung.get("gedeckt") is None
             else int(bewertung["gedeckt"]),
             str(bewertung.get("grund") or ""),
             json.dumps(zutaten, ensure_ascii=False, default=float)))
        conn.commit()
        return True
    except sqlite3.Error as exc:
        logger.info("Vorfilter %s nicht schreibbar: %s", symbol, exc)
        return False


def stand(conn) -> dict:
    """Wie weit ist die Schattenmessung? Fuer den NB-Export.

    ⚠️ MELDET GESUNDHEIT, NICHT NUR WACHSTUM (Methodik 2.57). Deshalb der
    letzte Lauf einzeln und die Zahl der nicht bestimmbaren Faelle - eine
    reine Gesamtzahl waere gewachsen, auch wenn `h` seit Tagen nur noch
    `NULL` ist."""
    try:
        n = conn.execute(f"SELECT COUNT(*) FROM {_TABELLE}").fetchone()[0]
        je = {("h" if r[0] == 1 else "nicht_h" if r[0] == 0
               else "nicht_bestimmbar"): r[1] for r in conn.execute(
            f"SELECT h, COUNT(*) FROM {_TABELLE} GROUP BY 1")}
        spanne = conn.execute(
            f"SELECT MIN(erfasst_am), MAX(erfasst_am), "
            f"COUNT(DISTINCT substr(erfasst_am, 1, 10)) "
            f"FROM {_TABELLE}").fetchone()
        aus = {"zeilen": n, "je_urteil": je,
               "erste": spanne[0], "letzte": spanne[1], "tage": spanne[2],
               "je_tag": {r[0]: r[1] for r in conn.execute(
                   f"SELECT substr(erfasst_am,1,10), COUNT(*) FROM {_TABELLE}"
                   f" GROUP BY 1 ORDER BY 1 DESC LIMIT 14")},
               "ohne_signal_id": conn.execute(
                   f"SELECT COUNT(*) FROM {_TABELLE} "
                   f"WHERE signal_id IS NULL").fetchone()[0],
               "hinweis": ("V1 schreibt nur mit. Die Auswertung braucht "
                           "aufgeloeste Signale - ohne signal_id ist eine "
                           "Zeile fuer den Vergleich verloren.")}
        if not n:
            aus["WARNUNG"] = (
                "KEINE Zeile. Der Vorfilter-Schatten schreibt nicht - jeder "
                "Tag ohne Zeile verschiebt die Entscheidung um einen Tag.")
        return aus
    except sqlite3.Error as exc:
        return {"nicht_verfuegbar": str(exc),
                "WARNUNG": "Tabelle fehlt - der Schatten hat nie geschrieben."}
