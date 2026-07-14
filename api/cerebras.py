"""Cerebras API Anbindung (kostenlos, gpt-oss-120b) - zweite LLM-Ebene neben Groq,
zunaechst fuer die Hebel-Empfehlungen (agent/krypto/hebel_analyst.py, 2026-07-14).
Bereits gegen das Spot-Signal-Schema live getestet (7/7 valide Antworten, siehe
Memory project_groq_8b_kapazitaet_test), Key in .env als CEREBRAS_API_KEY.

OpenAI-kompatible API wie Groq, identisches `.chat()`-Interface wie
api/groq.py::GroqClient - damit kann agent/krypto/hebel_analyst.py beide Clients
austauschbar entgegennehmen, ohne den Provider zu kennen. Bewusst KEIN interner
Rate-Limiter (anders als GroqClient): kein bestaetigter Cerebras-RPM-Wert bekannt,
echte Drosselung/Tagesbudget gehoert ohnehin in den kuenftigen Budget-Allocator
(docs/budget_queue_design.md), nicht in den reinen HTTP-Client."""
from __future__ import annotations

import requests

BASE_URL = "https://api.cerebras.ai/v1/chat/completions"
DEFAULT_MODEL = "gpt-oss-120b"


class CerebrasClient:
    def __init__(self, api_key: str, session: requests.Session | None = None):
        self._api_key = api_key
        self._session = session or requests.Session()

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
        response = self._session.post(BASE_URL, json=payload, headers=headers, timeout=60)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]
