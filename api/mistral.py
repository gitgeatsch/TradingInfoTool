"""Mistral AI API Anbindung (kostenlos, "Free Mode"/"Experiment"-Tier) - neue
Fallback-Stufe 2 (2026-07-17, Cerebras-Rueckbau siehe Memory
project_cerebras_free_tier_aenderung_2026-08-17.md): Cerebras beendet seinen
kostenlosen Tier zum 2026-08-17, Mistral ersetzt dessen Rolle - echt im
eigenen Kontingent-Dashboard des Nutzers verifiziert (2.250.000 TPM, 5 RPS
fuer mistral-small-2506 - ca. 20x mehr als Geminis 15 RPM). Ausserdem
vertraglich guenstiger als Gemini: keine EWR/CH/UK-Sonderklausel, keine
explizite Warnung vor vertraulichen/Finanzdaten, Trainings-Nutzung im
Free-Tier abwaehlbar (Gemini: nicht abwaehlbar).

OpenAI-kompatible API wie Groq/Cerebras/Gemini, identisches `.chat()`-
Interface (api/groq.py::GroqClient, api/cerebras.py::CerebrasClient,
api/gemini.py::GeminiClient) - damit kann agent/krypto/hebel_analyst.py bzw.
analyst.py alle vier Clients austauschbar entgegennehmen, ohne den Provider
zu kennen.

DEFAULT_MODEL = "mistral-small-2506" - von den im Nutzer-Dashboard
sichtbaren Modellen mit Abstand die groesszuegigste Kapazitaet
(2.250.000 TPM/5 RPS), Modellqualitaet ist zweitrangig - risk_gate.py::
post_check() validiert jede Empfehlung ohnehin deterministisch nach,
unabhaengig vom LLM-Anbieter (P-7)."""
from __future__ import annotations

import requests

from api.llm_basis import Minutenfenster, extrahiere_inhalt
from database.api_health import track_api_health

BASE_URL = "https://api.mistral.ai/v1/chat/completions"
DEFAULT_MODEL = "mistral-small-2506"
# Einzelfenster-Rate-Limiter (Gemini-Muster) statt Cerebras' Zwei-Fenster-
# Ansatz - der wurde nur wegen Cerebras' echt sehr knapper Limits (4/Min,
# 140/Std.) noetig. Mistrals echt verifizierte Kapazitaet (5 RPS ≈ 300/Min)
# liegt so weit ueber dem, was dieses Projekt als seltene Fallback-Stufe
# jemals braucht, dass ein konservativer Puffer weit darunter reicht - noch
# nicht live per Burst-Test bestaetigt (siehe Verifikationsschritt vor dem
# ersten echten Einsatz).
RATE_LIMIT_PER_MINUTE = 60


class MistralClient:
    def __init__(self, api_key: str, session: requests.Session | None = None):
        self._api_key = api_key
        self._session = session or requests.Session()
        # Gemeinsame, THREAD-SICHERE Drossel (2026-08-09, api/llm_basis.py) -
        # siehe dortigen Docstring, warum das Lock noetig ist.
        self._drossel = Minutenfenster(RATE_LIMIT_PER_MINUTE)

    def _respect_rate_limit(self) -> None:
        self._drossel.warte_auf_slot()

    @track_api_health("mistral")
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
        return extrahiere_inhalt(data, "Mistral")
