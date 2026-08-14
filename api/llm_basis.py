"""Gemeinsame Bausteine aller LLM-Clients (2026-08-09, Teil A des
Anbieter-Umbaus).

WARUM DIESES MODUL EXISTIERT. Beim Einbau von OpenRouter in die Signal-Kette
fiel auf, dass dieselben zwei Dinge in fuenf Clients stehen - einmal repariert,
viermal nicht:

  1. `data["choices"][0]["message"]["content"]` ohne Pruefung
  2. `_respect_rate_limit()` als Read-Modify-Write auf einer Deque OHNE Lock

Der Modul-Docstring von `agent/provider_sperre.py` benennt das Prinzip bereits:
*"zwei Kopien wuerden garantiert auseinanderlaufen"*. Genau das war eingetreten
- `api/openrouter.py` hatte am 08.08. beide Korrekturen bekommen, die anderen
vier nicht. Das Vorbild fuer die Aufloesung ist `database/api_health.py`: ein
gemeinsamer Baustein statt einer Basisklasse, weil die Clients keine gemeinsame
Oberklasse haben und auch keine bekommen sollen.
"""
from __future__ import annotations

import logging
import threading
import time
from collections import deque

logger = logging.getLogger(__name__)

# Anbieter liefern Upstream-Fehler teilweise mit HTTP 200 und einem
# `error`-Objekt STATT `choices` aus - `raise_for_status()` sieht davon nichts.
_ERWARTET = "choices"


class LLMAntwortOhneInhalt(RuntimeError):
    """HTTP 200, aber keine verwertbare Antwort.

    EIGENER TYP, KEIN KeyError: der Circuit Breaker
    (`agent/provider_sperre.py::ist_dauerhafter_fehler`) entscheidet anhand des
    FEHLERTEXTES, ob ein zweiter Versuch sinnvoll ist - er sucht "402", "401",
    "403". In einem `KeyError: 'choices'` steht davon nichts, ein
    Berechtigungsfehler wuerde also als voruebergehend eingestuft und dreimal
    wiederholt. Diese Klasse traegt den Original-Fehlertext weiter, damit die
    Einstufung wieder funktioniert.
    """


def extrahiere_inhalt(daten: dict, anbieter: str) -> str:
    """Holt den Antworttext - oder wirft einen Fehler, der den Grund NENNT.

    Vorher endete dieser Pfad in `KeyError: 'choices'`: der wahre Grund
    (gemessen am 08.08.: `{'message': 'Provider timed out after 24566ms',
    'code': 504}`) blieb unsichtbar, und im Log stand ein Feldname statt einer
    Ursache.
    """
    if _ERWARTET not in daten:
        fehler = daten.get("error") or daten
        raise LLMAntwortOhneInhalt(
            f"{anbieter}: HTTP 200 ohne '{_ERWARTET}' - {str(fehler)[:300]}"
        )
    try:
        return daten[_ERWARTET][0]["message"]["content"]
    except (IndexError, KeyError, TypeError) as exc:
        raise LLMAntwortOhneInhalt(
            f"{anbieter}: '{_ERWARTET}' vorhanden, aber unerwartet aufgebaut "
            f"({type(exc).__name__}) - {str(daten)[:300]}"
        ) from exc


def verbrauch_heute(source: str, tag: str | None = None) -> int:
    """Wie viele Aufrufe heute schon auf `source` gebucht sind.

    Gegenstueck zu `zaehle_aufruf()` fuer einen Waechter, der VOR dem Aufruf
    entscheidet. `tag` erlaubt den Tagesschluessel des Anbieters statt UTC
    (Gemini setzt zu Mitternacht Pazifik zurueck).

    Gibt 0 zurueck, wenn die Zaehlung nicht lesbar ist - ein Waechter, der
    wegen eines fehlenden Zaehlers die Produktion anhaelt, waere schlimmer als
    der ungezaehlte Aufruf. Der Aufrufer sieht am Rueckgabewert 0 nicht, ob
    "noch nichts verbraucht" oder "nicht messbar" gilt; deshalb protokolliert
    diese Funktion den Unterschied."""
    import database.db as db          # lokal, s.u.

    try:
        conn = db.get_connection()
        try:
            return db.get_api_call_counter_taeglich(conn, source, tag)
        finally:
            conn.close()
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "Verbrauchszaehler fuer %s nicht lesbar (%s) - der Tageswaechter "
            "arbeitet blind und laesst durch. init_db() legt "
            "api_call_kontingent_taeglich an.", source, exc)
        return 0


def zaehle_aufruf(source: str, tag: str | None = None) -> None:
    """Zaehlt EINEN tatsaechlichen HTTP-Aufruf an einen LLM-Anbieter.

    WARUM DAS NOETIG IST (Teil B des Umbaus, 2026-08-09).
    `db.count_real_llm_calls_today_by_provider()` zaehlt DATENSAETZE - also
    erzeugte Signale. Ein fehlgeschlagener Aufruf erzeugt keine Zeile und ist
    damit unsichtbar. Am 07.08. stand Mistrals Zaehler den ganzen Tag auf 0,
    waehrend jeder einzelne Kandidat dort vergeblich anklopfte und ein
    402 kassierte; `mistral_budget_erschoepft` konnte nie True werden.

    Fuer das QUALITAETS-Tracking ist "Datensaetze" richtig (welcher Anbieter hat
    dieses Signal erzeugt). Als BUDGET-Zaehler ist es falsch. Deshalb zwei
    getrennte Zaehler statt eines umgedeuteten.

    HIER und nicht im `track_api_health`-Decorator, weil OpenRouter innerhalb
    EINES `chat()` durch mehrere Modelle rotiert - jeder dieser Versuche ist
    ein eigener HTTP-Aufruf und zaehlt gegen das Tageslimit des Anbieters.
    Am Decorator haengend wuerde eine Rotation ueber drei Modelle als ein
    einziger Aufruf gezaehlt.

    Zaehlt VOR dem Aufruf, damit ein Fehlschlag mitzaehlt - genau das war der
    Defekt. Fehler beim Zaehlen duerfen den Aufruf nie toeten (P-10).
    """
    import database.db as db          # lokal: api/ soll beim Import nicht auf DB warten

    try:
        conn = db.get_connection()
        try:
            db.increment_api_call_counter(conn, source, tag)
        finally:
            conn.close()
    except Exception as exc:  # noqa: BLE001
        logger.debug("Aufrufzaehler fuer %s nicht geschrieben: %s", source, exc)


# Der Schluessel, unter dem Token statt Aufrufe gebucht werden. Die Einheit
# steckt im Namen, damit niemand die beiden Zahlen versehentlich vergleicht.
TOKEN_SUFFIX = ":token"


def zaehle_token(source: str, anzahl: int, tag: str | None = None) -> None:
    """Bucht `anzahl` Token auf `source` (O-25, 14.08.2026).

    WARUM ES DIESEN ZAEHLER GIBT. Bei Groq ist die bindende Free-Tier-Grenze
    nicht die Anfragenzahl, sondern die TOKEN JE TAG: 1.000 RPD stehen 100.000
    TPD gegenueber, und bei rund 1.200 Token je Aufruf ist der zweite Wert nach
    83 Aufrufen erschoepft - einem Zwoelftel des ersten.

    Bisher gab es dafuer nur eine Umrechnung im Code (`GROQ_AUFRUFE_JE_TAG`).
    Die ist richtig, solange der Prompt so gross ist wie gemessen. Dieser
    Zaehler misst stattdessen, was wirklich verbraucht wurde - auf
    Nutzerwunsch gebaut, damit er da ist, wenn er gebraucht wird.

    NUR ZAEHLEN, NICHT SPERREN. Ein Waechter, der auf dieser Zahl aufsetzt,
    gehoert zum Aufrufer; hier waere er versteckt. Wer sperren will, liest
    `token_heute()` und entscheidet selbst.

    Fehler beim Zaehlen duerfen den Aufruf nie toeten (P-10)."""
    import database.db as db

    if not anzahl or int(anzahl) <= 0:
        return
    try:
        conn = db.get_connection()
        try:
            db.increment_api_call_counter(conn, f"{source}{TOKEN_SUFFIX}", tag,
                                          schritt=int(anzahl))
        finally:
            conn.close()
    except Exception as exc:  # noqa: BLE001
        logger.debug("Tokenzaehler fuer %s nicht geschrieben: %s", source, exc)


def token_heute(source: str, tag: str | None = None) -> int:
    """Wie viele Token heute auf `source` gebucht sind. 0, wenn unlesbar."""
    return verbrauch_heute(f"{source}{TOKEN_SUFFIX}", tag)


class Minutenfenster:
    """Thread-sichere Volumen-Drossel: hoechstens `limit` Aufrufe je 60 s.

    WARUM DAS LOCK NOETIG IST. Die bisherige Fassung stand viermal identisch in
    gemini/groq/mistral/zai und arbeitete OHNE Lock - `while ... popleft()`,
    dann `len()`, dann `sleep`, dann `append` ist ein Read-Modify-Write ueber
    mehrere Schritte. Aufgerufen wird sie aus bis zu sechs gleichzeitig
    laufenden Pipeline-Threads plus den Gegenpruefungs-Threads. Ohne Lock
    koennen zwei Threads dieselbe Luecke sehen und beide durchgehen; das Limit
    ist dann eine Empfehlung, keine Grenze.

    Bewusst blockierend (`time.sleep`): der aufrufende Thread soll warten, nicht
    fehlschlagen - das ist in allen fuenf Clients das bisherige Verhalten und
    wird hier nicht geaendert.
    """

    def __init__(self, limit_pro_minute: int):
        self._limit = limit_pro_minute
        self._zeitpunkte: deque[float] = deque()
        self._lock = threading.Lock()

    def warte_auf_slot(self) -> None:
        with self._lock:
            jetzt = time.monotonic()
            while self._zeitpunkte and jetzt - self._zeitpunkte[0] > 60:
                self._zeitpunkte.popleft()
            if len(self._zeitpunkte) >= self._limit:
                schlafen = 60 - (jetzt - self._zeitpunkte[0])
                if schlafen > 0:
                    time.sleep(schlafen)
                # NACH dem Schlafen erneut aufraeumen - sonst zaehlt der
                # abgelaufene Eintrag weiter mit und das Fenster verschiebt
                # sich dauerhaft. Diesen Schritt hatte die alte Fassung nicht.
                jetzt = time.monotonic()
                while self._zeitpunkte and jetzt - self._zeitpunkte[0] > 60:
                    self._zeitpunkte.popleft()
            self._zeitpunkte.append(time.monotonic())


class Mindestabstand:
    """Thread-sichere Abstands-Drossel: zwischen zwei Aufrufen liegen
    mindestens `sekunden`.

    ANDERE ACHSE als `Minutenfenster` - nicht das Volumen je Minute, sondern
    der Abstand zwischen zwei Aufrufen. OpenRouter nutzt diese Form (20
    Anfragen/Minute laut Doku, also 3 s Abstand); die uebrigen Anbieter nutzen
    das Fenster. Beide hier, damit niemand die falsche kopiert.
    """

    def __init__(self, sekunden: float):
        self._sekunden = sekunden
        self._letzter = 0.0
        self._lock = threading.Lock()

    def warte_auf_slot(self) -> None:
        with self._lock:
            wartezeit = self._sekunden - (time.monotonic() - self._letzter)
            if wartezeit > 0:
                time.sleep(wartezeit)
            self._letzter = time.monotonic()
