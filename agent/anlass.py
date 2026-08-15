# -*- coding: utf-8 -*-
"""Ist das ueberhaupt eine NEUE Frage? - O-36, Messvariante (15.08.2026).

DER GRUNDANSATZ STAMMT VOM NUTZER:

    "warum eine neue Bewertung und Signal wenn sich nichts geaendert hat ...
     nach einer 1. Bewertung kommt erst eine 2. wenn sich an den Grundlagen
     und Kriterien etwas geaendert hat ... damit nichts blockiert wird, die
     Pruefung nur eine bestimmte Zeit, z.B. 24 Stunden."

WAS DIESES MODUL NICHT BEHAUPTET. Es sagt nichts darueber, ob ein Trade gut
wird. Es sagt nur: dieselbe Frage auf denselben Daten ist keine neue Frage.
Damit ist es KEIN Qualitaetsfilter und braucht keine Prognose - das ist
wichtig, weil dieses Projekt an 8.441 Faellen gemessen hat, dass kein Verfahren
die Basisrate schlaegt. Ein Rang nach erwarteter Guete waere eine Behauptung
gegen den eigenen Grundbefund; "das haben wir schon gefragt" ist keine.

DIE MESSGRUNDLAGE. Ein Modell dreht bei bitgleicher Eingabe in etwa 12 % der
Faelle die Richtung (Formatmessung 09.08.). Dieselbe Frage zweimal erzeugt dort
keine Information, sondern Streuung.

DER FINGERABDRUCK IST DER PROMPT SELBST, nicht eine Schwelle auf dem Kurs.
Das ist der Punkt: eine Schwelle ("hat sich der Kurs um 2 % bewegt") waere eine
gesetzte Zahl, und davon hat dieses Projekt genug. Der Faktentext rundet
ohnehin - "1.093 EUR wert", "-35,7 %" -, also bildet er die Aufloesung ab, die
das Modell wirklich sieht. Ist der Text zeichengleich, ist es woertlich
dieselbe Frage.

ZWEI FINGERABDRUECKE, WEIL DIE RICHTIGE DEFINITION NOCH NICHT FESTSTEHT:

    voll   alles, was das Modell liest - samt Lagebild-Prosa
    asset  nur die Fakten DIESES Assets, ohne das Lagebild

Der Unterschied ist keine Feinheit. Das Lagebild ist Modellprosa und wechselt
alle drei Stunden; naehme man es mit, waere fast jede Frage "neu" und der
Filter wirkungslos. Laesst man es weg, misst man, ob sich am ASSET etwas
geaendert hat. Welche der beiden die richtige ist, soll die Messung sagen und
nicht ich - deshalb werden beide gefuehrt.

ES SPERRT NICHTS. Nutzervorgabe: "erstmal soviele Daten wie moeglich zulassen
und spaeter selektiv einschraenken". Dieses Modul schreibt mit, wie oft es
gegriffen HAETTE. Erst wenn diese Zahl bekannt ist, laesst sich entscheiden -
mit bekannter Wirkung statt geschaetzter.
"""
from __future__ import annotations

import hashlib
import json
import logging
import sqlite3
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)

# Nach dieser Zeit gilt eine Frage wieder als neu, auch bei gleichem Text.
# Nutzervorgabe ("z.B. 24 Stunden"), und ihr Zweck ist ausdruecklich, dass
# NICHTS dauerhaft blockiert: ein Asset, an dem sich wochenlang nichts tut,
# bekommt trotzdem jeden Tag ein Urteil.
HOECHSTALTER_STUNDEN = 24.0

# Das Lagebild steht unter diesem Schluessel im Faktensatz.
_LAGEBILD_SCHLUESSEL = "marktlage_beurteilung"


def _hash(wert) -> str:
    roh = json.dumps(wert, ensure_ascii=False, sort_keys=True,
                     separators=(",", ":"))
    return hashlib.sha256(roh.encode("utf-8")).hexdigest()[:32]


def fingerabdruecke(fakten: dict) -> tuple[str, str]:
    """(voll, asset) - beide aus DEMSELBEN Faktensatz, den das Modell bekommt.

    NICHT AUS DEN ROHDATEN, sondern aus dem fertigen Text. Wer den Kurs
    hashen wuerde, bekaeme bei jedem Tick einen neuen Abdruck; der Text sagt
    "1.093 EUR wert" und aendert sich erst, wenn es der Leser merkt."""
    voll = _hash(fakten or {})
    ohne = {k: v for k, v in (fakten or {}).items()
            if k != _LAGEBILD_SCHLUESSEL}
    return voll, _hash(ohne)


def _tabelle(conn: sqlite3.Connection) -> bool:
    try:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS anlass_beobachtung (
                   id INTEGER PRIMARY KEY,
                   erfasst_am TEXT NOT NULL,
                   symbol TEXT NOT NULL,
                   instrument TEXT NOT NULL,
                   fingerabdruck_voll TEXT NOT NULL,
                   fingerabdruck_asset TEXT NOT NULL,
                   gleich_voll INTEGER NOT NULL,
                   gleich_asset INTEGER NOT NULL,
                   alter_stunden REAL,
                   wuerde_sperren_voll INTEGER NOT NULL,
                   wuerde_sperren_asset INTEGER NOT NULL)""")
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_anlass_paar "
            "ON anlass_beobachtung (symbol, instrument, erfasst_am)")
        return True
    except sqlite3.Error as exc:
        logger.info("Anlass-Tabelle nicht anlegbar: %s", exc)
        return False


def beobachte(conn, *, symbol: str, instrument: str, fakten: dict,
              jetzt: str | None = None,
              hoechstalter_stunden: float = HOECHSTALTER_STUNDEN) -> dict:
    """Schreibt eine Beobachtung und sagt, ob GESPERRT WORDEN WAERE.

    SPERRT SELBST NICHT - der Rueckgabewert ist eine Feststellung, kein Veto.
    Der Aufrufer darf ihn heute nur mitzaehlen.

    Faellt irgendetwas aus, kommt ein leeres Urteil zurueck und der Lauf geht
    weiter: eine Messung, die den Betrieb anhaelt, waere ihren Preis nicht
    wert."""
    voll, asset = fingerabdruecke(fakten)
    aus = {"fingerabdruck_voll": voll, "fingerabdruck_asset": asset,
           "gleich_voll": False, "gleich_asset": False,
           "alter_stunden": None,
           "wuerde_sperren_voll": False, "wuerde_sperren_asset": False}
    if conn is None or not _tabelle(conn):
        return aus
    try:
        nun = (datetime.fromisoformat(jetzt) if jetzt
               else datetime.now(timezone.utc))
        if nun.tzinfo is None:
            nun = nun.replace(tzinfo=timezone.utc)
        grenze = (nun - timedelta(hours=float(hoechstalter_stunden))).isoformat()
        # DIE JUENGSTE BEOBACHTUNG INNERHALB DES FENSTERS. Aelteres zaehlt
        # nicht - genau dafuer gibt es die Decke.
        zeile = conn.execute(
            "SELECT erfasst_am, fingerabdruck_voll, fingerabdruck_asset "
            "FROM anlass_beobachtung WHERE symbol = ? AND instrument = ? "
            "AND erfasst_am >= ? ORDER BY erfasst_am DESC LIMIT 1",
            (str(symbol).upper(), str(instrument), grenze)).fetchone()
        if zeile is not None:
            frueher = (zeile["erfasst_am"] if hasattr(zeile, "keys")
                       else zeile[0])
            v = zeile["fingerabdruck_voll"] if hasattr(zeile, "keys") else zeile[1]
            a = zeile["fingerabdruck_asset"] if hasattr(zeile, "keys") else zeile[2]
            try:
                dann = datetime.fromisoformat(str(frueher))
                if dann.tzinfo is None:
                    dann = dann.replace(tzinfo=timezone.utc)
                aus["alter_stunden"] = round(
                    (nun - dann).total_seconds() / 3600.0, 3)
            except ValueError:
                pass
            aus["gleich_voll"] = (v == voll)
            aus["gleich_asset"] = (a == asset)
            # INNERHALB DES FENSTERS UND GLEICH = waere gesperrt worden.
            aus["wuerde_sperren_voll"] = aus["gleich_voll"]
            aus["wuerde_sperren_asset"] = aus["gleich_asset"]
        conn.execute(
            "INSERT INTO anlass_beobachtung (erfasst_am, symbol, instrument, "
            "fingerabdruck_voll, fingerabdruck_asset, gleich_voll, "
            "gleich_asset, alter_stunden, wuerde_sperren_voll, "
            "wuerde_sperren_asset) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (nun.isoformat(), str(symbol).upper(), str(instrument), voll, asset,
             int(aus["gleich_voll"]), int(aus["gleich_asset"]),
             aus["alter_stunden"], int(aus["wuerde_sperren_voll"]),
             int(aus["wuerde_sperren_asset"])))
        conn.commit()
    except sqlite3.Error as exc:
        logger.info("Anlass-Beobachtung fuer %s nicht geschrieben: %s",
                    symbol, exc)
    return aus
