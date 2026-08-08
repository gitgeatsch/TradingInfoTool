"""Groq API Anbindung (kostenlos, Llama 3.3 70B) - primaere KI-Analyse-Ebene ab Phase 3.

Siehe Basisinfos/Spezifikation.md Kap. 2 (P-8): lokales Phi-4-mini bleibt Offline-
Fallback, Groq ist die bevorzugte remote-Ebene (kostenlos, kein Widerspruch zu P-8).
OpenAI-kompatible API, kein besonderes SDK noetig.
"""
from __future__ import annotations

import requests

from api.llm_basis import Minutenfenster, extrahiere_inhalt, zaehle_aufruf
from database.api_health import track_api_health

BASE_URL = "https://api.groq.com/openai/v1"
DEFAULT_MODEL = "llama-3.3-70b-versatile"
RATE_LIMIT_PER_MINUTE = 28  # Free-Tier-Limit ist 30 RPM, kleiner Puffer


class GroqClient:
    def __init__(self, api_key: str, session: requests.Session | None = None):
        self._api_key = api_key
        self._session = session or requests.Session()
        # Gemeinsame, THREAD-SICHERE Drossel (2026-08-09, api/llm_basis.py) -
        # siehe dortigen Docstring, warum das Lock noetig ist.
        self._drossel = Minutenfenster(RATE_LIMIT_PER_MINUTE)

    def _respect_rate_limit(self) -> None:
        self._drossel.warte_auf_slot()

    @track_api_health("groq")
    def chat(
        self,
        messages: list[dict],
        model: str = DEFAULT_MODEL,
        temperature: float = 0.3,
        response_format: dict | None = None,
    ) -> str:
        self._respect_rate_limit()
        zaehle_aufruf("groq")
        headers = {"Authorization": f"Bearer {self._api_key}"}
        payload = {"model": model, "messages": messages, "temperature": temperature}
        if response_format is not None:
            payload["response_format"] = response_format
        response = self._session.post(
            f"{BASE_URL}/chat/completions", json=payload, headers=headers, timeout=30
        )
        response.raise_for_status()
        data = response.json()
        return extrahiere_inhalt(data, "Groq")
