"""Z.ai (Zhipu AI) API Anbindung - vierter, testweise VOR Mistral eingehaengter
Kandidat (2026-07-20, siehe Memory reference_llm_provider_recherche_uebersicht.md
und project_groq_alternative_recherche_2026-07-20.md). Anders als bei Mistral/
Gemini/Groq ist die reale Kapazitaet NICHT ueber ein Nutzer-Dashboard verifiziert
- Z.ai veroeffentlicht fuer die kostenlosen Modelle nur ein "Concurrency limit"
(GLM-4.5-Flash=2, GLM-4.7-Flash=1), keine RPM/TPM/RPD-Zahl. Nutzer-Entscheidung:
bewusst KEINE konservative Drosselung im Client (anders als Mistral/Gemini) -
"kein Grund nicht auf ein bestimmtes hoeheres Limit zu gehen, wenn diese Quelle
blockiert wird passiert auch nichts fuer diese eine Nacht". Reale Kapazitaet
zeigt sich ueber echte 429-Fehler in api_health (gleiches Prinzip wie Groq).

Vertragsbedingungen laut offizieller Datenschutzerklaerung
(docs.z.ai/legal-agreement/privacy-policy) fuer API-Kunden gut: keine
Speicherung der Anfrage-/Antwortinhalte (nur Echtzeit-Verarbeitung), keine
Trainings-Nutzung. Verarbeitung laut Policy in Singapur.

DEFAULT_MODEL = "glm-4.5-flash" - eines der beiden dauerhaft kostenlosen
Modelle (GLM-4.5-Flash/GLM-4.7-Flash, laut offizieller Pricing-Seite als
"Free" statt nur "Limited-time Free" gelistet), Concurrency-Limit 2 (etwas
hoeher als GLM-4.7-Flashs 1) - Modellqualitaet ist ohnehin zweitrangig,
risk_gate.py::post_check() validiert jede Empfehlung unabhaengig vom
LLM-Anbieter deterministisch nach (P-7).

OpenAI-kompatible API wie Groq/Mistral/Gemini, identisches `.chat()`-
Interface."""
from __future__ import annotations

import time
from collections import deque

import requests

from database.api_health import track_api_health

BASE_URL = "https://api.z.ai/api/paas/v4/chat/completions"
DEFAULT_MODEL = "glm-4.5-flash"
# Bewusst KEINE konservative Drosselung (Nutzer-Vorgabe 2026-07-20, siehe
# Modul-Docstring) - nur ein grosszuegiger Sicherheitsnetz-Wert gegen einen
# etwaigen Endlosschleifen-Bug, keine Kapazitaetsschaetzung. Die reale
# Obergrenze ist unbekannt und soll sich im echten Betrieb zeigen.
RATE_LIMIT_PER_MINUTE = 120


class ZaiClient:
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

    @track_api_health("zai")
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
