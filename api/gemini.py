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

from api.llm_basis import Minutenfenster, extrahiere_inhalt, zaehle_aufruf
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


class GeminiClient:
    def __init__(self, api_key: str, session: requests.Session | None = None):
        self._api_key = api_key
        self._session = session or requests.Session()
        # Gemeinsame, THREAD-SICHERE Drossel (2026-08-09, api/llm_basis.py).
        # Die vorherige Fassung stand hier viermal identisch in vier Clients
        # und arbeitete ohne Lock - aufgerufen aus bis zu sechs gleichzeitigen
        # Pipeline-Threads war das Limit eine Empfehlung, keine Grenze.
        self._drossel = Minutenfenster(RATE_LIMIT_PER_MINUTE)

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
        letzte = None
        for versuch in range(_MAX_VERSUCHE_BEI_429):
            self._respect_rate_limit()
            zaehle_aufruf("gemini")
            response = self._session.post(BASE_URL, json=payload,
                                          headers=headers, timeout=60)
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
