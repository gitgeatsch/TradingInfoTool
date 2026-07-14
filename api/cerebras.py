"""Cerebras API Anbindung (kostenlos, gpt-oss-120b) - zweite LLM-Ebene neben Groq,
zunaechst fuer die Hebel-Empfehlungen (agent/krypto/hebel_analyst.py, 2026-07-14).
Bereits gegen das Spot-Signal-Schema live getestet (7/7 valide Antworten, siehe
Memory project_groq_8b_kapazitaet_test), Key in .env als CEREBRAS_API_KEY.

OpenAI-kompatible API wie Groq, identisches `.chat()`-Interface wie
api/groq.py::GroqClient - damit kann agent/krypto/hebel_analyst.py beide Clients
austauschbar entgegennehmen, ohne den Provider zu kennen.

Echte Limits (2026-07-14 per Response-Headern `x-ratelimit-*` bestaetigt,
nicht nur dokumentiert): 5 Requests/Min, 150/Std., 2.400/Tag, 30.000
Tokens/Min, 1.000.000 Tokens/Tag. Bei ~6.000 Tokens/Call (gemessene
Payload-Groesse, siehe signal_batch.py-Docstring) ist der Tages-Token-Wert
mit ~166 Calls/Tag die bindende Grenze - deutlich mehr als Groqs reale
~15-18/Tag, aber eben nicht unbegrenzt. Rate-Limiter unten schuetzt vor dem
Minuten-Limit (das echte 429 in Phase 4 ausgeloest hat); das Tages-/
Stunden-Budget selbst verwaltet der Budget-Allocator (agent/krypto/
budget_allocator.py), nicht dieser reine HTTP-Client."""
from __future__ import annotations

import time
from collections import deque

import requests

BASE_URL = "https://api.cerebras.ai/v1/chat/completions"
DEFAULT_MODEL = "gpt-oss-120b"
RATE_LIMIT_PER_MINUTE = 4  # echtes Limit ist 5/Min, kleiner Puffer (siehe Docstring)


class CerebrasClient:
    def __init__(self, api_key: str, session: requests.Session | None = None):
        self._api_key = api_key
        self._session = session or requests.Session()
        self._call_timestamps: deque[float] = deque()

    def _respect_rate_limit(self) -> None:
        now = time.monotonic()
        while self._call_timestamps and now - self._call_timestamps[0] > 60:
            self._call_timestamps.popleft()
        if len(self._call_timestamps) >= RATE_LIMIT_PER_MINUTE:
            sleep_for = 60 - (now - self._call_timestamps[0])
            if sleep_for > 0:
                time.sleep(sleep_for)
        self._call_timestamps.append(time.monotonic())

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
