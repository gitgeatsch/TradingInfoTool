"""Groq API Anbindung (kostenlos, Llama 3.3 70B) - primaere KI-Analyse-Ebene ab Phase 3.

Siehe Basisinfos/Spezifikation.md Kap. 2 (P-8): lokales Phi-4-mini bleibt Offline-
Fallback, Groq ist die bevorzugte remote-Ebene (kostenlos, kein Widerspruch zu P-8).
OpenAI-kompatible API, kein besonderes SDK noetig.
"""
from __future__ import annotations

import requests

BASE_URL = "https://api.groq.com/openai/v1"
DEFAULT_MODEL = "llama-3.3-70b-versatile"


class GroqClient:
    def __init__(self, api_key: str, session: requests.Session | None = None):
        self._api_key = api_key
        self._session = session or requests.Session()

    def chat(
        self, messages: list[dict], model: str = DEFAULT_MODEL, temperature: float = 0.3
    ) -> str:
        headers = {"Authorization": f"Bearer {self._api_key}"}
        payload = {"model": model, "messages": messages, "temperature": temperature}
        response = self._session.post(
            f"{BASE_URL}/chat/completions", json=payload, headers=headers, timeout=30
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]
