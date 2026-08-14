"""Groq API Anbindung (kostenlos, Llama 3.3 70B) - primaere KI-Analyse-Ebene ab Phase 3.

Siehe Basisinfos/Spezifikation.md Kap. 2 (P-8): lokales Phi-4-mini bleibt Offline-
Fallback, Groq ist die bevorzugte remote-Ebene (kostenlos, kein Widerspruch zu P-8).
OpenAI-kompatible API, kein besonderes SDK noetig.
"""
from __future__ import annotations

import requests

from api.llm_basis import (Minutenfenster, extrahiere_inhalt,
                          zaehle_aufruf, zaehle_token)
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
        # DIE TOKEN AUS DER ANTWORT BUCHEN (O-25, 14.08.2026).
        #
        # Groqs bindende Free-Tier-Grenze sind 100.000 TOKEN je Tag, nicht die
        # 1.000 Anfragen - bei rund 1.200 Token je Aufruf ist der Topf nach 83
        # leer. `scheduler/rollen_job` rechnet das bisher aus einer gemessenen
        # Konstante um; hier steht, was tatsaechlich verbraucht wurde.
        #
        # NACH dem Aufruf, anders als `zaehle_aufruf`: die Zahl steht erst in
        # der Antwort. Ein Fehlschlag verbraucht keine Token, also fehlt dort
        # auch nichts.
        try:
            _u = (data or {}).get("usage") or {}
            zaehle_token("groq", int(_u.get("total_tokens") or 0))
        except Exception:                                    # noqa: BLE001
            pass                                             # P-10
        return extrahiere_inhalt(data, "Groq")
