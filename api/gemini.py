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

import time
from collections import deque

import requests

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


class GeminiClient:
    def __init__(self, api_key: str, session: requests.Session | None = None):
        self._api_key = api_key
        self._session = session or requests.Session()
        self._call_timestamps_minute: deque[float] = deque()

    def _respect_rate_limit(self) -> None:
        now = time.monotonic()
        while self._call_timestamps_minute and now - self._call_timestamps_minute[0] > 60:
            self._call_timestamps_minute.popleft()
        if len(self._call_timestamps_minute) >= RATE_LIMIT_PER_MINUTE:
            sleep_for = 60 - (now - self._call_timestamps_minute[0])
            if sleep_for > 0:
                time.sleep(sleep_for)
        self._call_timestamps_minute.append(time.monotonic())

    def chat(
        self,
        messages: list[dict],
        model: str = DEFAULT_MODEL,
        temperature: float = 0.3,
        response_format: dict | None = None,
    ) -> str:
        self._respect_rate_limit()
        headers = {"Authorization": f"Bearer {self._api_key}"}
        payload = {"model": model, "messages": messages, "temperature": temperature}
        if response_format is not None:
            payload["response_format"] = response_format
        response = self._session.post(BASE_URL, json=payload, headers=headers, timeout=60)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]
