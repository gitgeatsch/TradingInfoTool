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

import threading
import time
from collections import deque

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
