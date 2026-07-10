"""Lokale KI-Ebene (P-8, Basisinfos/Spezifikation.md Kap. 2) - Architektur-Seam
vorbereitet (2026-07-10), tatsaechliche Modell-Integration bewusst noch NICHT
umgesetzt (siehe Begruendung unten).

Kontext: der Nutzer betreibt die App perspektivisch 24/7 auf einem Notebook mit
aktuell 8 GB RAM. P-8 verlangt, dass Kernfunktionen nie zwingend von einem
externen KI-Key abhaengen - Groq (agent/krypto/analyst.py, api/groq.py) ist
bereits vollstaendig OPTIONAL (ohne Key bleibt der Signale-Tab nutzbar, nur die
Berechnung deaktiviert). Diese Datei bereitet den naechsten Schritt vor: ein
lokales Modell als echte Offline-Alternative, sobald die Hardware dafuer
aufgeruestet ist.

Entscheidung (2026-07-10, Recherche diese Session): sobald umgesetzt, soll
**llama.cpp (via llama-cpp-python) + ein Phi-4-mini-GGUF-Modell + GBNF-Grammar-
Constraint** genutzt werden - NICHT ONNX Runtime GenAI (Microsofts eigener Pfad,
urspruenglich in P-8 genannt). Grund: unser SYSTEM_PROMPT-Schema
(agent/krypto/analyst.py) ist sehr streng (genau 5 top_gruende-Eintraege,
Enum-Validierung, von<=bis-Zonen, bedingte Pflichtfelder in halte_kriterium) -
selbst Groq (Llama 3.3 70B) braucht dafuer gelegentlich einen Retry
(max_retries=2). Ein kleineres lokales Modell (3-4B Parameter) waere ohne
harte Struktur-Erzwingung vermutlich noch unzuverlaessiger. GBNF-Grammar-
Constraint (llama.cpp) erzwingt gueltiges JSON bereits auf Token-Ebene beim
Sampling - eine strukturelle Garantie, die Phi-4-minis natives Tool-Calling
(ONNX Runtime GenAI) nicht bietet (das ist trainiertes Verhalten, keine
Erzwingung). Die GBNF-Grammatik muesste aus dem bestehenden JSON-Schema in
analyst.py generiert werden (noch nicht gebaut).

Bewusst NICHT jetzt umgesetzt (Stufe 2, nach Hardware-Upgrade): ein
int4-quantisiertes ~3-4B-Modell braucht schaetzungsweise 2,5-3,5 GB RAM allein
fuer die Gewichte - auf der aktuellen 8-GB-Notebook-Hardware wuerde das den
bisher komfortablen Speicherpuffer spuerbar einengen. Ausserdem waere ein
JSON-Schema-Zuverlaessigkeitstest auf der Ziel-Hardware noetig, bevor man sich
darauf verlassen kann - das jetzt auf beengter Hardware zu pruefen, ergaebe ein
zu pessimistisches Bild."""
from __future__ import annotations


class LocalModelClient:
    """Platzhalter mit demselben Interface wie api.groq.GroqClient (chat()-Methode,
    identische Signatur) - agent/krypto/analyst.py::call_groq_for_signal() ruft
    bereits ausschliesslich .chat(messages, model, temperature, response_format)
    auf und ist damit schon provider-agnostisch, ohne Aenderung noetig. Sobald
    Stufe 2 umgesetzt wird, ersetzt eine echte Implementierung hier nur diese
    Klasse - der Rest der Pipeline aendert sich nicht."""

    def __init__(self, model_path: str | None = None, grammar_path: str | None = None):
        self._model_path = model_path
        self._grammar_path = grammar_path

    def chat(
        self,
        messages: list[dict],
        model: str = "phi-4-mini",
        temperature: float = 0.3,
        response_format: dict | None = None,
    ) -> str:
        raise NotImplementedError(
            "Lokale KI-Ebene ist als Architektur-Seam vorbereitet, aber noch nicht "
            "implementiert (siehe Modul-Docstring) - geplant: llama-cpp-python + "
            "Phi-4-mini-GGUF + GBNF-Grammar, nach Hardware-Upgrade. Bis dahin "
            "config.yaml agent.ai_provider auf 'groq' belassen."
        )
