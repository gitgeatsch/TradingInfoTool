"""OpenRouter-Client, ausschliesslich fuer die Gegenpruefung (2026-08-07).

WARUM DIESER ANBIETER UEBERHAUPT. Mistral hat am 07.08. alle Modelle
kostenpflichtig gestellt (Free-Plan: 10 $ Monatsbudget, kontoweit ueber Studio/
Vibe Code/API geteilt, Reset in 24 Tagen). Danach trug **Gemini allein** alle
142 Signale des Tages - ein Ein-Anbieter-Risiko. Die Suche nach einem zweiten
freien Anbieter (Runde 5, siehe Regelwerk-Entscheidungslog) ergab: der
Ausschlussgrund ist unser EIGENER System-Prompt mit ~9.100 Token, nicht das
Tagesvolumen. Cerebras und Z.ai haetten je 1 Mio. Token/Tag, scheitern aber an
8K Kontext. Groq hat 100K Token/TAG - acht Analysen.

WARUM NUR FUER DIE GEGENPRUEFUNG. Die meisten freien Endpunkte auf OpenRouter
verlangen, dass Logging/Training aktiviert ist - Prompts werden Trainings- bzw.
Evaluierungsmaterial. Unser SYSTEM_PROMPT ist mit ~9.100 Token das inhaltliche
Herzstueck des Projekts (Regelwerk, Bewertungslogik, Risikokriterien); den
dorthin zu schicken hiesse, genau diese Arbeit wegzugeben.

Die Gegenpruefung (`agent/krypto/gegenpruefung.py`) benutzt dagegen einen
bewusst schlanken Faktensatz von rund zehn Feldern und bekommt den
SYSTEM_PROMPT **nie** zu sehen. Der Nutzer hat die Trainings-Freigabe genau
dafuer - und nur dafuer - ausdruecklich erteilt (07.08.).

**Wer diesen Client in die Haupt-Signalkette haengt, macht diese Entscheidung
rueckgaengig, ohne sie zu treffen.** Deshalb steht das hier und nicht nur im
Entscheidungslog.

WIE KEINE KOSTEN ENTSTEHEN. Zwei Regeln, beide hier im Code durchgesetzt statt
auf Disziplin gebaut:

  1. **Nur `:free`-Modell-IDs.** Auf OpenRouter existieren Modelle doppelt -
     einmal bezahlt, einmal mit `:free`-Suffix zum Nullpreis. `chat()` weist
     jede ID ohne dieses Suffix ab.
  2. **Kein Auto-Router, kein Modell-Fallback.** OpenRouters `models`-Feld und
     die Auto-Routing-Endpunkte koennen eine Anfrage auf einer bezahlten
     Variante landen lassen. Wir senden immer genau EIN explizites Modell.

Damit zehrt die Nutzung das Guthaben nicht auf. Das ist wichtig, weil der
Tagesboden fuer freie Modelle an "Credits purchased (all time)" haengt: ab
10 $ Lebenszeit-Kauf dauerhaft 1.000 statt 50 Anfragen/Tag, **unabhaengig vom
aktuellen Kontostand**. Eine Ueberschreitung liefert 429, keine stille
Abbuchung.
"""
from __future__ import annotations

import logging
import threading
import time

import requests

from database.api_health import track_api_health

logger = logging.getLogger(__name__)

BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

# Nur Modelle mit diesem Suffix kosten nichts. Siehe Modul-Docstring, Regel 1.
FREE_SUFFIX = ":free"

# Vorgabemodell fuer die Gegenpruefung. Bewusst ein grosses, offen gewichtetes
# Modell: der Gegenpruefungs-Faktensatz ist zwar schlank, aber die Frage
# ("stuetzt die Begruendung die Richtung?") verlangt echtes Schlussfolgern -
# an genau dieser Anforderung ist Groqs 8B strukturell gescheitert.
#
# ACHTUNG, WARTUNGSPUNKT: die Free-Liste auf OpenRouter rotiert ohne
# Vorwarnung. Faellt dieses Modell weg, liefert die API einen Fehler - der
# Circuit Breaker (agent/provider_sperre.py) faengt das ab, aber der Eintrag
# hier muss dann nachgezogen werden. Aktuelle Liste: openrouter.ai/models,
# Preisfilter 0.
DEFAULT_MODEL = "deepseek/deepseek-r1:free"

# Free-Tier: 20 Anfragen/Minute (OpenRouter-Doku, Stand 07.08.2026). Ein
# eigener Drosselwert statt blindem Feuern - dieselbe Bauart wie bei Z.ai.
MIN_ABSTAND_SEKUNDEN = 3.0


class OpenRouterModelNichtFrei(ValueError):
    """Eine Modell-ID ohne `:free`-Suffix wuerde echtes Guthaben kosten."""


class OpenRouterClient:
    """Gleiches `.chat()`-Interface wie die uebrigen Clients (Duck-Typing) -
    `gegenpruefung.py` ruft ausschliesslich `.chat()` auf und muss deshalb
    nicht wissen, welcher Anbieter dahintersteht."""

    def __init__(self, api_key: str, session: requests.Session | None = None):
        self._api_key = api_key
        self._session = session or requests.Session()
        self._lock = threading.Lock()
        self._letzter_call = 0.0

    def _respect_rate_limit(self) -> None:
        with self._lock:
            wartezeit = MIN_ABSTAND_SEKUNDEN - (time.monotonic() - self._letzter_call)
            if wartezeit > 0:
                time.sleep(wartezeit)
            self._letzter_call = time.monotonic()

    @track_api_health("openrouter")
    def chat(
        self,
        messages: list[dict],
        model: str = DEFAULT_MODEL,
        temperature: float = 0.3,
        response_format: dict | None = None,
    ) -> str:
        # REGEL 1 aus dem Modul-Docstring, hier durchgesetzt statt vorausgesetzt.
        # Ein Tippfehler in einer Modell-ID waere sonst eine stille Abbuchung.
        if not model.endswith(FREE_SUFFIX):
            raise OpenRouterModelNichtFrei(
                f"Modell '{model}' hat kein '{FREE_SUFFIX}'-Suffix und wuerde echtes "
                f"Guthaben kosten. Dieser Client ist ausschliesslich fuer die "
                f"kostenlosen Varianten gedacht (siehe Modul-Docstring)."
            )
        self._respect_rate_limit()
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            # OpenRouter bittet um diese beiden Felder zur Zuordnung; sie sind
            # optional, aber ohne sie landen Anfragen in einem anonymen Topf.
            "HTTP-Referer": "https://github.com/gitgeatsch/TradingInfoTool",
            "X-Title": "TradingInfoTool",
        }
        # REGEL 2: genau EIN Modell, kein `models`-Array, kein `route`-Feld -
        # beides koennte auf einer bezahlten Variante landen.
        payload = {"model": model, "messages": messages, "temperature": temperature}
        if response_format is not None:
            payload["response_format"] = response_format
        response = self._session.post(BASE_URL, json=payload, headers=headers, timeout=90)
        response.raise_for_status()
        daten = response.json()
        return daten["choices"][0]["message"]["content"]
