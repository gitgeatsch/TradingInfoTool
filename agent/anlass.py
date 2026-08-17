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


def bloeckeabdruecke(bloecke: dict | None) -> dict:
    """Ein Abdruck JE BLOCK - damit die Messung sagt, WELCHER es war.

    NUTZERFRAGE, die das ausgeloest hat (15.08.2026): *"warum brauchen wir
    einen LLM-Aufruf, der Hash kann ja deterministisch gebildet werden?"* Er
    hat recht - und die Anschlussfrage ist die interessantere: wenn eine Frage
    als "neu" gilt, WORAN lag es?

    DER VERDACHT, DEN DAS PRUEFEN SOLL. Der Finanzierungsblock aendert sich bei
    Krypto alle acht Stunden von selbst - eine neue Funding-Periode verschiebt
    die Perzentile, ohne dass am Chart etwas geschehen ist. Er koennte den
    Filter also ausgerechnet dort stumpf machen, wo er am meisten braechte. Und
    es ist derselbe Block, der laut O-34 in 63 % der SPOT-Urteile zitiert wird,
    obwohl er dort gar nicht anfaellt.

    Ohne diese Aufschluesselung waere die Messung eine Zahl ohne Ursache."""
    return {str(k): _hash(v) for k, v in (bloecke or {}).items()}


# ---------------------------------------------------------------------------
# DIE SPERRE (16.08.2026) - aus der Messung, nicht aus einer Schaetzung.
#
# DER WEG HIERHER, weil er die Vorgaben erklaert. Diese Stufe hat vom 15. bis
# zum 16.08. NUR gemessen. Die Messung ergab:
#
#     74 % Wiederholungen bei intakter Datenlage (83 % mit stehenden Kursen)
#     82 von 121 Einstiegen auf einem Faktensatz, den es schon gab
#     11 von 26 Wiederholungen kippten die AKTION - bei bitgleicher Eingabe
#
# ICH HABE DARAUS ZUERST DEN FALSCHEN SCHLUSS GEZOGEN: der Filter "kostet" 82
# Einstiege, also lohne er nicht. Der Nutzer hat den Fehlschluss benannt -
# "Schaden" setzt voraus, dass diese Einstiege einen Wert haben, und im selben
# Absatz stand, dass sie keinen haben.
#
# DAS TRAGENDE ARGUMENT IST EIN KORREKTHEITSARGUMENT, kein Renditeargument:
#
#     Eine Empfehlung, die auf identischen Daten beruht wie eine vorherige
#     NICHT-Empfehlung, ist keine Empfehlung - sie ist die Streuung des
#     Modells.
#
# Es haengt nicht davon ab, ob das System je Geld verdient.
#
# VOR DEM MODELLAUFRUF, nicht danach. Wer die Antwort erst holt und dann
# wegwirft, hat das Kontingent schon ausgegeben und das Rauschen bereits
# erzeugt - er versteckt es nur.

# Vorgabe: AUS. Ein Modul, das beim blossen Einspielen die Produktion
# umstellt, nimmt dem Nutzer die Entscheidung ab - dieselbe Regel wie bei
# `rollen_kette.aktiv_fuer`. Eingeschaltet wird in `config.yaml`.
SPERRE_VORGABE = {
    "aktiv": False,
    # Welcher Abdruck entscheidet. "asset" laesst das Lagebild weg - es ist
    # Modellprosa und wechselt alle drei Stunden. GEMESSEN macht es nur zwei
    # Prozentpunkte aus (79 % gegen 81 %), aber die zwei Punkte waeren
    # ausschliesslich Prosa.
    "abdruck": "asset",
    "hoechstalter_stunden": HOECHSTALTER_STUNDEN,
    # --- FEINJUSTIERUNG, ohne Codeaenderung ---------------------------------
    #
    # Beide Regler greifen NUR, wenn der Abdruck sich unterscheidet - sie
    # koennen also nur MEHR sperren, nie weniger. Ein identischer Abdruck ist
    # immer eine Wiederholung.
    #
    # `ignoriere_bloecke`  Bloecke, deren Aenderung NICHT als neue Frage zaehlt.
    #                      Der Kandidat ist `marken`. ⚠️ NACHGEMESSEN AM
    #                      17.08. an 7.308 Beobachtungen: sie tragen
    #                      59,3 % aller Blockaenderungen (1.579 von 2.663) -
    #                      hier stand bis dahin 15 %, und das war eine
    #                      Schaetzung, keine Messung. Sie sind kursnah und
    #                      springen, sobald ein Tick ueber eine
    #                      Clustergrenze laeuft; mit `mindest_bloecke: 1`
    #                      reicht dieser eine Block. Er ist damit der
    #                      groesste einzelne Grund, warum die Bremse
    #                      durchlaesst. Ob das eine neue Lage ist oder
    #                      Rauschen, ist offen - deshalb ein Regler und
    #                      keine Setzung.
    # `mindest_bloecke`    wie viele Bloecke sich bewegt haben muessen. 1 ist
    #                      die heutige Bedeutung von "geaendert".
    "ignoriere_bloecke": [],
    "mindest_bloecke": 1,
}


def sperre_konfig(config: dict | None = None) -> dict:
    """Die Sperreinstellungen - Vorgabe, ueberschrieben aus `config.yaml`.

    LIEST NICHT SELBST. Die Kette reicht ihre `config` durch; ein Modul, das
    sich seine Konfiguration selbst holt, laesst sich in keiner Simulation
    umlenken - und genau das brauchen `simuliere_kette.py` und die
    Paketpruefungen."""
    aus = dict(SPERRE_VORGABE)
    roh = ((config or {}).get("anlass") or {}) if isinstance(config, dict) else {}
    for k in aus:
        if k in roh:
            aus[k] = roh[k]
    return aus


def sperrt(beobachtung: dict, config: dict | None = None) -> tuple[bool, str]:
    """Ist das eine Wiederholung? (ja/nein, Begruendung fuer das Protokoll)

    NIMMT DIE BEOBACHTUNG ENTGEGEN, statt selbst zu rechnen - `beobachte()`
    hat den Abdruck und die geaenderten Bloecke bereits ermittelt, und zwar
    aus DEMSELBEN Faktensatz, der ans Modell geht. Eine zweite Rechnung waere
    die naechste Stelle zum Auseinanderlaufen.

    GIBT IMMER `False` ZURUECK, WENN ETWAS FEHLT. Eine Sperre, die bei einer
    Luecke zuschlaegt, entfernt Signale aus einem Grund, den niemand sieht -
    fail-soft heisst hier ausdruecklich: im Zweifel durchlassen."""
    cfg = sperre_konfig(config)
    if not cfg.get("aktiv"):
        return False, ""
    if not isinstance(beobachtung, dict):
        return False, ""
    # Ohne Vorgaengerfrage im Fenster gibt es nichts zu wiederholen.
    if beobachtung.get("alter_stunden") is None:
        return False, ""

    schluessel = ("gleich_voll" if str(cfg.get("abdruck")) == "voll"
                  else "gleich_asset")
    alter = beobachtung.get("alter_stunden")
    if beobachtung.get(schluessel):
        return True, (f"Faktensatz unveraendert seit {alter:.1f} h "
                      f"({cfg.get('abdruck')})")

    # --- Feinjustierung: was zaehlt als Aenderung? --------------------------
    geaendert = [b for b in (beobachtung.get("geaenderte_bloecke") or [])
                 if b not in set(cfg.get("ignoriere_bloecke") or ())]
    if len(geaendert) < int(cfg.get("mindest_bloecke", 1)):
        gesehen = ", ".join(beobachtung.get("geaenderte_bloecke") or []) or "keine"
        return True, (f"nur {len(geaendert)} zaehlende Blockaenderung(en) seit "
                      f"{alter:.1f} h (bewegt: {gesehen})")
    return False, ""


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
                   wuerde_sperren_asset INTEGER NOT NULL,
                   bloecke_json TEXT,
                   geaenderte_bloecke TEXT)""")
        # NACHTRAEGLICH FUER BESTEHENDE TABELLEN. `CREATE TABLE IF NOT EXISTS`
        # aendert eine vorhandene nicht - wer schon Beobachtungen hat, bekaeme
        # sonst still keine Blockspalten.
        vorhanden = {r[1] for r in conn.execute(
            "PRAGMA table_info(anlass_beobachtung)")}
        for spalte in ("bloecke_json", "geaenderte_bloecke"):
            if spalte not in vorhanden:
                conn.execute("ALTER TABLE anlass_beobachtung "
                             f"ADD COLUMN {spalte} TEXT")
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_anlass_paar "
            "ON anlass_beobachtung (symbol, instrument, erfasst_am)")
        return True
    except sqlite3.Error as exc:
        logger.info("Anlass-Tabelle nicht anlegbar: %s", exc)
        return False


def beobachte(conn, *, symbol: str, instrument: str, fakten: dict,
              bloecke: dict | None = None, jetzt: str | None = None,
              hoechstalter_stunden: float = HOECHSTALTER_STUNDEN,
              schreiben: bool = True) -> dict:
    """Schreibt eine Beobachtung und sagt, ob GESPERRT WORDEN WAERE.

    `schreiben=False` FUER DEN TROCKENLAUF (O-38, 16.08.2026). Bis heute
    uebersprang der Trockenlauf diese Stufe ganz - weil sie schreibt. Damit
    kannte er die Sperre nicht und meldete einen Durchsatz, den der scharfe
    Betrieb nie erreicht. Das Urteil braucht den Schreibvorgang aber nicht:
    der Fingerabdruck wird gerechnet, der Vergleich gelesen, nur die neue
    Zeile entfaellt.

    SPERRT SELBST NICHT - der Rueckgabewert ist eine Feststellung, kein Veto.
    Der Aufrufer darf ihn heute nur mitzaehlen.

    Faellt irgendetwas aus, kommt ein leeres Urteil zurueck und der Lauf geht
    weiter: eine Messung, die den Betrieb anhaelt, waere ihren Preis nicht
    wert."""
    voll, asset = fingerabdruecke(fakten)
    je_block = bloeckeabdruecke(bloecke)
    aus = {"fingerabdruck_voll": voll, "fingerabdruck_asset": asset,
           "gleich_voll": False, "gleich_asset": False,
           "alter_stunden": None, "bloecke": je_block,
           "geaenderte_bloecke": [],
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
            "SELECT erfasst_am, fingerabdruck_voll, fingerabdruck_asset, "
            "bloecke_json FROM anlass_beobachtung WHERE symbol = ? "
            "AND instrument = ? AND erfasst_am >= ? "
            "ORDER BY erfasst_am DESC LIMIT 1",
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
            # WELCHER BLOCK HAT SICH GEAENDERT? Das ist die Antwort auf
            # "warum galt das als neue Frage" - ohne sie waere die
            # Messung eine Zahl ohne Ursache. Ein Block, der neu
            # DAZUKOMMT oder WEGFAELLT, zaehlt ebenfalls als Aenderung.
            try:
                frueher_bloecke = json.loads(
                    (zeile["bloecke_json"] if hasattr(zeile, "keys")
                     else zeile[3]) or "{}")
            except (TypeError, ValueError):
                frueher_bloecke = {}
            aus["geaenderte_bloecke"] = sorted(
                k for k in set(frueher_bloecke) | set(je_block)
                if frueher_bloecke.get(k) != je_block.get(k))
            # INNERHALB DES FENSTERS UND GLEICH = waere gesperrt worden.
            aus["wuerde_sperren_voll"] = aus["gleich_voll"]
            aus["wuerde_sperren_asset"] = aus["gleich_asset"]
        if not schreiben:
            # KEINE ZEILE, ABER DAS VOLLE URTEIL. Ein Trockenlauf, der
            # schreibt, veraendert die Grundlage des naechsten scharfen
            # Laufs - genau der Fehler, den `probe` vermeiden soll.
            return aus
        conn.execute(
            "INSERT INTO anlass_beobachtung (erfasst_am, symbol, instrument, "
            "fingerabdruck_voll, fingerabdruck_asset, gleich_voll, "
            "gleich_asset, alter_stunden, wuerde_sperren_voll, "
            "wuerde_sperren_asset, bloecke_json, geaenderte_bloecke) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (nun.isoformat(), str(symbol).upper(), str(instrument), voll, asset,
             int(aus["gleich_voll"]), int(aus["gleich_asset"]),
             aus["alter_stunden"], int(aus["wuerde_sperren_voll"]),
             int(aus["wuerde_sperren_asset"]),
             json.dumps(je_block, ensure_ascii=False, sort_keys=True),
             ",".join(aus["geaenderte_bloecke"]) or None))
        conn.commit()
    except sqlite3.Error as exc:
        logger.info("Anlass-Beobachtung fuer %s nicht geschrieben: %s",
                    symbol, exc)
    return aus
