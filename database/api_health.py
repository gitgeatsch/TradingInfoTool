"""Passives API-Gesundheits-Tracking (2026-07-15) - Nutzer-Wunsch, nach den echten
Vorfaellen (Groq-429-Erschoepfung, Cerebras-Ausfaelle, yfinance-Haenger am Notebook)
jederzeit auf einen Blick zu sehen, welche externe Quelle aktuell funktioniert -
OHNE zusaetzlichen Health-Check-Netzwerk-Traffic (kein zusaetzliches Kontingent-
Risiko bei den LLM-Anbietern). Rein beobachtend: zeichnet nur auf, was ohnehin
schon passiert, veraendert nie Rueckgabewert oder Exception-Typ des Aufrufs.

Liegt bewusst unter database/ statt api/, weil api/*.py bereits heute direkt aus
database/ importiert (z.B. api/yfinance_client.py -> database.models.PriceSnapshot) -
keine neue/unuebliche Abhaengigkeitsrichtung. Kein gemeinsamer Client-Basisklasse
existiert unter den API-Clients, deshalb ein Decorator statt einer Basisklassen-
Aenderung - laesst sich auf jede einzelne Funktion/Methode anwenden, egal ob es
einen internen Funnel gibt oder nicht (siehe Anwendungsstellen in api/*.py)."""
from __future__ import annotations

import functools
from typing import Callable, TypeVar

import database.db as db

F = TypeVar("F", bound=Callable)


def track_api_health(source: str) -> Callable[[F], F]:
    """Dekoriert eine Funktion/Methode, die einen echten Netzwerk-Call macht.
    Oeffnet bei JEDEM Aufruf eine eigene, kurzlebige DB-Connection (kein conn-
    Parameter in den Signaturen der api/*.py-Funktionen vorhanden, und die sollen
    dafuer nicht umgebaut werden) - SQLite-Connection-Overhead ist trivial, die
    Aufruf-Frequenz bleibt durch die echte API-Nutzung natuerlich begrenzt.
    Exceptions werden IMMER weitergereicht (raise) - reine Beobachtung."""

    def decorator(fn: F) -> F:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                result = fn(*args, **kwargs)
            except Exception as exc:
                conn = db.get_connection()
                try:
                    db.record_api_health_error(conn, source, type(exc).__name__, str(exc)[:200])
                finally:
                    conn.close()
                raise
            conn = db.get_connection()
            try:
                db.record_api_health_success(conn, source)
            finally:
                conn.close()
            return result

        return wrapper  # type: ignore[return-value]

    return decorator
