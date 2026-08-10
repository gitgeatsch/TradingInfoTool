"""Google Gemini API Anbindung (kostenlos, Gemini 2.5 Flash-Lite) - vierte
LLM-Kapazitaetsquelle neben Groq/Cerebras/xAI (2026-07-14, siehe Memory
project_xai_grok_option.md - xAI wurde durch dieses Angebot ersetzt, da
Gemini deutlich mehr kostenlose Kapazitaet bietet: recherchiert ~1.000-1.500
Anfragen/Tag, 250K-1M Tokens/Min, gegenueber Groqs realen ~15-18/Tag und
Cerebras' ~166/Tag - noch NICHT live gegen echte x-ratelimit-Header
verifiziert, siehe Verifikationsskript).

OpenAI-kompatible API wie Groq/Cerebras, identisches `.chat()`-Interface
(api/groq.py::GroqClient, api/cerebras.py::CerebrasClient) - damit kann
agent/krypto/hebel_analyst.py bzw. analyst.py alle drei Clients austauschbar
entgegennehmen, ohne den Provider zu kennen.

WICHTIG (Datenschutz): anders als bei Groq/Cerebras ist bei Gemini die
Nutzung von Prompt/Antwort fuer Google-Produktverbesserung der REGULAERE
Free-Tier-Deal, kein optionales Bonus-Programm zum Abwaehlen (siehe Memory)."""
from __future__ import annotations

import logging
import re
import time

import requests

from api.llm_basis import (Minutenfenster, extrahiere_inhalt, verbrauch_heute,
                           zaehle_aufruf)
from database.api_health import track_api_health

BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
# 2026-07-14 live geprueft: die in der Web-Recherche genannten Modelle
# (gemini-2.5-flash-lite/-flash) sind fuer NEUE Konten nicht mehr verfuegbar
# ("no longer available to new users", echter 404). gemini-3.1-flash-lite ist
# das aktuelle, stabile Flash-Lite-Modell (nicht "-latest"/"-preview", die
# sich unangekuendigt aendern koennen) - per echtem API-Call bestaetigt.
DEFAULT_MODEL = "gemini-3.1-flash-lite"
# Echtes Limit empirisch ermittelt (2026-07-14, Burst-Test): 16 Calls in Folge
# erfolgreich, 17. Call -> echter 429 ("exceeded your current quota"). Gemini
# liefert KEINE x-ratelimit-Header (anders als Groq/Cerebras), daher Burst-
# Test statt Header-Auslesen. ~15/Min bestaetigt sich damit, RATE_LIMIT_PER_
# MINUTE=10 ist ein konservativer Puffer darunter. Echtes Schema-Verhalten
# (4/4 valide Analysen inkl. echtem KAUFEN bei BTC) ebenfalls live gegen
# unser SYSTEM_PROMPT verifiziert - Tages-/Wochenlimit NICHT getestet
# (kostet echtes Kontingent), siehe Memory project_xai_grok_option.md-
# Nachbarschaft fuer den vollen Testkontext.
RATE_LIMIT_PER_MINUTE = 10

logger = logging.getLogger(__name__)

# Wie oft ein 429 wiederholt wird, bevor er durchgereicht wird. Drei Versuche
# decken den beobachteten Fall ab (Server empfiehlt ~40 s) und begrenzen die
# Wartezeit auf gut zwei Minuten je Aufruf - laenger wuerde einen Messlauf
# unkalkulierbar machen, ohne die Ausbeute noch nennenswert zu heben.
_MAX_VERSUCHE_BEI_429 = 3

# Obergrenze fuer eine einzelne Wartezeit. Schlaegt der Server etwas
# Absurdes vor (oder liefert gar nichts), wird nicht minutenlang blockiert.
_MAX_WARTEZEIT_SEKUNDEN = 65.0
_VORGABE_WARTEZEIT_SEKUNDEN = 20.0

# GEMESSEN am 2026-08-09 mit pruefe_gemini_verhalten.py, nicht recherchiert.
# Google nennt die Grenze selbst im Fehlerkoerper:
#
#     quotaId    GenerateRequestsPerDayPerProjectPerModel-FreeTier
#     Grenzwert  500
#
# Drei Eigenschaften dieser Grenze, die wir vorher alle drei falsch hatten:
#
#   PerDay      -> ein Tageslimit. Ein 429 daraus ist NICHT durch Warten zu
#                  heilen; die bisherige dreifache Wiederholung hat je Aufruf
#                  bis zu zwei Minuten verbrannt, um dreimal dasselbe zu hoeren.
#   PerProject  -> haengt am SCHLUESSEL, nicht am Geraet. Desktop-Messlaeufe und
#                  die Produktion am Notebook schoepfen aus demselben Topf. Am
#                  09.08. haben meine Laeufe der Produktion das Budget genommen.
#   PerModel    -> jedes Modell hat einen EIGENEN Topf. `gemini-3.5-flash-lite`
#                  war unberuehrt, waehrend unseres erschoepft war. Der Zaehler
#                  muss deshalb je Modell buchen, nicht je Anbieter.
TAGESBUDGET_JE_MODELL = 500

# Reserve, die der Waechter der Produktion freihaelt. Ein Messlauf soll das
# Budget nicht bis auf den letzten Aufruf leerraeumen - genau das ist am 09.08.
# passiert und hat die Produktion fuer den Rest des Tages stillgelegt.
VORGABE_RESERVE = 0


def _kontingent_tag() -> str:
    """Der Tagesschluessel, nach dem GOOGLE zaehlt - nicht der nach UTC.

    Das Free-Tier-Kontingent setzt zu Mitternacht Pazifik zurueck. Zwischen
    00:00 und ~08:00 UTC steht ein UTC-Tageszaehler auf 0, waehrend Google noch
    den Vortag fuehrt: ein Waechter auf UTC-Basis laesst genau dann durch, wenn
    das Budget in Wahrheit leer ist. Faellt die Zeitzonendatenbank aus (tzdata
    fehlt), wird auf UTC-8 gerechnet - grob, aber naeher dran als UTC."""
    from datetime import datetime, timedelta, timezone
    try:
        from zoneinfo import ZoneInfo
        return datetime.now(ZoneInfo("America/Los_Angeles")).strftime("%Y-%m-%d")
    except Exception:  # noqa: BLE001  - tzdata fehlt o.ae.
        return (datetime.now(timezone.utc) - timedelta(hours=8)).strftime("%Y-%m-%d")


def _quota_verletzungen(response) -> list[dict]:
    """Googles `QuotaFailure`-Details aus dem Fehlerkoerper.

    ICH HATTE BEHAUPTET, der OpenAI-Kompatibilitaets-Endpunkt verschlucke
    diese Angabe. Das war falsch (gemessen 09.08.): er liefert dieselbe
    Struktur, nur als LISTE auf oberster Ebene statt als Objekt. Wir haben den
    Koerper schlicht nie gelesen - `raise_for_status()` und fertig. Zwei Tage
    Spekulation ueber den Mechanismus standen die ganze Zeit in jedem 429."""
    import json
    if response is None:
        return []
    try:
        daten = json.loads(response.text or "")
    except (ValueError, TypeError):
        return []
    if isinstance(daten, list):
        daten = daten[0] if daten and isinstance(daten[0], dict) else {}
    if not isinstance(daten, dict):
        return []
    treffer = []
    for detail in (daten.get("error") or {}).get("details") or []:
        if isinstance(detail, dict) and "QuotaFailure" in str(detail.get("@type", "")):
            treffer.extend(detail.get("violations") or [])
    return [v for v in treffer if isinstance(v, dict)]


def _ist_tageskontingent(response) -> bool:
    """Trennt "heute nichts mehr" von "gerade zu schnell".

    Nur bei `...PerMinute...` hilft Warten. Bei `...PerDay...` ist jede
    Wiederholung verlorene Zeit."""
    return any("PerDay" in str(v.get("quotaId", ""))
               for v in _quota_verletzungen(response))


class TageskontingentErschoepft(requests.HTTPError):
    """Das Tagesbudget dieses MODELLS ist aufgebraucht.

    Eigener Typ, damit ein Aufrufer das von einem Netzwerk- oder Schemafehler
    unterscheiden kann, ohne im Meldungstext zu suchen - ein Messlauf soll
    hier abbrechen statt stundenlang gegen eine geschlossene Tuer zu laufen."""

    # Merkmal fuer `database.api_health.track_api_health` (2026-08-10): ein
    # leeres Tagesbudget darf die Anbieter-Ampel NICHT auf Rot stellen. Als
    # Merkmal statt per Import, weil `api.gemini` bereits `database.api_health`
    # importiert - die Gegenrichtung waere ein Zyklus. Jeder andere Client kann
    # dasselbe Merkmal setzen und wird genauso behandelt.
    ist_kontingent_erschoepft = True

    def __init__(self, nachricht: str, modell: str, response=None):
        super().__init__(nachricht, response=response)
        self.modell = modell


def _wartezeit_aus_antwort(response) -> float:
    """Wie lange der Server selbst zu warten empfiehlt.

    Google liefert die Angabe an zwei Stellen und in zwei Formen: als
    `Retry-After`-Header und im Fehlerkoerper (`"retryDelay": "40s"` bzw.
    im Klartext "Please retry in 40.56s"). Geraten wird hier nichts - fehlt
    beides, gilt eine konservative Vorgabe."""
    kopf = response.headers.get("Retry-After") if response is not None else None
    if kopf:
        try:
            return min(float(kopf), _MAX_WARTEZEIT_SEKUNDEN)
        except (TypeError, ValueError):
            pass
    text = (response.text or "") if response is not None else ""
    for muster in (r'"retryDelay"\s*:\s*"([\d.]+)s"',
                   r"retry in ([\d.]+)\s*s"):
        treffer = re.search(muster, text)
        if treffer:
            try:
                return min(float(treffer.group(1)) + 1.0, _MAX_WARTEZEIT_SEKUNDEN)
            except ValueError:
                pass
    return _VORGABE_WARTEZEIT_SEKUNDEN


# Modelle, deren Tagesbudget in DIESEM Prozess bereits als erschoepft erkannt
# wurde, als {(modell, tag)}. Spart je Folgeaufruf einen HTTP-Aufruf, der
# garantiert scheitert. Prozesslokal und damit bewusst kein Ersatz fuer den
# DB-Zaehler - ein Neustart vergisst das hier, der Zaehler nicht.
_erschoepft: set[tuple[str, str]] = set()


class GeminiClient:
    def __init__(self, api_key: str, session: requests.Session | None = None,
                 tagesbudget: int | None = None, reserve: int | None = None):
        self._api_key = api_key
        self._session = session or requests.Session()
        # TAGESWAECHTER (2026-08-09). Er sitzt HIER und nicht im
        # budget_allocator, obwohl es dort seit dem 14.07. ein
        # `gemini_taegliches_budget` gibt. Grund: dieses greift nur fuer die
        # Produktionspipelines. Jedes Messskript baut sich einen GeminiClient
        # direkt und geht vollstaendig daran vorbei - genau so sind am 09.08.
        # ueber 500 Aufrufe gefallen und haben die Produktion stillgelegt.
        # Im Client kommt kein Aufrufer daran vorbei.
        self._tagesbudget = (TAGESBUDGET_JE_MODELL if tagesbudget is None
                             else tagesbudget)
        self._reserve = VORGABE_RESERVE if reserve is None else reserve
        # Gemeinsame, THREAD-SICHERE Drossel (2026-08-09, api/llm_basis.py).
        # Die vorherige Fassung stand hier viermal identisch in vier Clients
        # und arbeitete ohne Lock - aufgerufen aus bis zu sechs gleichzeitigen
        # Pipeline-Threads war das Limit eine Empfehlung, keine Grenze.
        self._drossel = Minutenfenster(RATE_LIMIT_PER_MINUTE)

    def budget_status(self, model: str = DEFAULT_MODEL) -> dict:
        """Was heute auf DIESEM Modell schon verbraucht ist - ohne Aufruf.

        Fuer eine Vorflugkontrolle: ein Messlauf soll vorher wissen, ob sein
        Bedarf ueberhaupt hineinpasst, statt es nach 200 Aufrufen zu merken."""
        tag = _kontingent_tag()
        verbraucht = verbrauch_heute(f"gemini:{model}", tag)
        nutzbar = max(0, self._tagesbudget - self._reserve)
        return {"modell": model, "tag_pazifik": tag, "verbraucht": verbraucht,
                "budget": self._tagesbudget, "reserve": self._reserve,
                "verfuegbar": max(0, nutzbar - verbraucht),
                "erschoepft": (model, tag) in _erschoepft or verbraucht >= nutzbar}

    def _respect_rate_limit(self) -> None:
        self._drossel.warte_auf_slot()

    @track_api_health("gemini")
    def chat(
        self,
        messages: list[dict],
        model: str = DEFAULT_MODEL,
        temperature: float = 0.3,
        response_format: dict | None = None,
    ) -> str:
        headers = {"Authorization": f"Bearer {self._api_key}"}
        payload = {"model": model, "messages": messages, "temperature": temperature}
        if response_format is not None:
            payload["response_format"] = response_format

        # WIEDERHOLUNG BEI 429 (2026-08-09). Der Nutzer hat den Widerspruch
        # bemerkt: "wenn das Kontingent erschoepft waere duerfte nichts
        # durchgehen - du hast geprueft alles ok und dann wieder Fehler?"
        # Nachgemessen, drei rohe Aufrufe in drei Sekunden: 200, 200, 429.
        # Es ist also KEIN hartes Tageskontingent, sondern (mindestens) ein
        # Burst-Limit - und der Server sagt selbst, wie lange man warten soll.
        #
        # Vorher flog der 429 als HTTPError durch alle Wiederholungsschleifen
        # der Messlaeufe, weil die nur JSONDecodeError/ValueError fangen. Ein
        # einzelner Lauf verlor dadurch 19 Messpunkte, und zwar geballt am
        # Ende - also NICHT zufaellig verteilt, sondern systematisch bei den
        # spaetesten Ankern. Ein stiller Selektionsfehler.
        tag = _kontingent_tag()
        if (model, tag) in _erschoepft:
            raise TageskontingentErschoepft(
                f"Gemini: Tagesbudget von {model} ist am {tag} (Pazifik) "
                f"bereits als erschoepft erkannt - kein weiterer Aufruf.",
                modell=model)
        stand = self.budget_status(model)
        if stand["verfuegbar"] <= 0:
            raise TageskontingentErschoepft(
                f"Gemini: Tagesbudget von {model} ausgeschoepft "
                f"({stand['verbraucht']}/{self._tagesbudget} am {tag}, "
                f"Pazifik, Reserve {self._reserve}) - kein Aufruf gesendet.",
                modell=model)

        letzte = None
        for versuch in range(_MAX_VERSUCHE_BEI_429):
            self._respect_rate_limit()
            # ZWEI Buchungen, absichtlich. "gemini" auf UTC-Tag ist der
            # bestehende Zaehler, den der budget_allocator liest - unveraendert,
            # damit sich dort nichts verschiebt. "gemini:<modell>" auf
            # Pazifik-Tag ist der, der Googles Grenze tatsaechlich abbildet.
            zaehle_aufruf("gemini")
            zaehle_aufruf(f"gemini:{model}", tag)
            response = self._session.post(BASE_URL, json=payload,
                                          headers=headers, timeout=60)
            if response.status_code == 429 and _ist_tageskontingent(response):
                # Warten hilft hier nicht mehr - bis morgen frueh nicht.
                _erschoepft.add((model, tag))
                grenzen = ", ".join(
                    f"{v.get('quotaId')}={v.get('quotaValue')}"
                    for v in _quota_verletzungen(response))
                raise TageskontingentErschoepft(
                    f"Gemini: Tagesbudget von {model} laut Anbieter "
                    f"erschoepft ({grenzen}). Google setzt zu Mitternacht "
                    f"Pazifik zurueck; ein anderes Modell hat ein eigenes "
                    f"Budget.", modell=model, response=response)
            if response.status_code != 429:
                # Fehler ANDERER Art bekommen jetzt Statuscode und Body in die
                # Meldung. Vorher stand dort nur "HTTPError" - und genau daran
                # habe ich am 09.08. zweimal geraten statt gelesen.
                if not response.ok:
                    raise requests.HTTPError(
                        f"Gemini HTTP {response.status_code}: "
                        f"{response.text[:400]}", response=response)
                return extrahiere_inhalt(response.json(), "Gemini")
            letzte = response
            wartezeit = _wartezeit_aus_antwort(response)
            if versuch + 1 >= _MAX_VERSUCHE_BEI_429:
                break
            logger.info("Gemini 429 - warte %.1f s und versuche erneut "
                        "(%d von %d)", wartezeit, versuch + 2,
                        _MAX_VERSUCHE_BEI_429)
            time.sleep(wartezeit)

        raise requests.HTTPError(
            f"Gemini HTTP 429 nach {_MAX_VERSUCHE_BEI_429} Versuchen: "
            f"{(letzte.text if letzte is not None else '')[:400]}",
            response=letzte)
