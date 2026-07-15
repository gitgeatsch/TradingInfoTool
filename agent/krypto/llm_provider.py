"""Providerkennzeichnung fuer austauschbare LLM-Clients (2026-07-14, Budget-
Allocator-Phase). Groq und Cerebras haben identisches `.chat()`-Interface
(siehe api/groq.py::GroqClient/api/cerebras.py::CerebrasClient), daher
erkennen call_groq_for_signal()/call_llm_for_hebel_signal() den Provider
bewusst nicht selbst (duck-typing). Diese Funktion wird NUR fuers Speichern
gebraucht (welcher Anbieter/Modell hat dieses Signal tatsaechlich erzeugt) -
seit der Budget-Allocator Groq UND Cerebras fuer dieselbe Pipeline-Funktion
einsetzen kann, ist die vorherige Praxis (Modellname hart im Code hinterlegt)
nicht mehr korrekt. Ermoeglicht das in docs/budget_queue_design.md geforderte
Qualitaets-Tracking (Cerebras-Ergebnisse ueber echte Produktionsdaten
beobachtbar machen, statt nur einmalig zu testen)."""
from __future__ import annotations


def llm_model_label(llm_client) -> str:
    module = type(llm_client).__module__
    if module.endswith("cerebras"):
        from api.cerebras import DEFAULT_MODEL

        return f"cerebras:{DEFAULT_MODEL}"
    if module.endswith("groq"):
        from api.groq import DEFAULT_MODEL

        return f"groq:{DEFAULT_MODEL}"
    if module.endswith("gemini"):
        from api.gemini import DEFAULT_MODEL

        return f"gemini:{DEFAULT_MODEL}"
    return type(llm_client).__name__
