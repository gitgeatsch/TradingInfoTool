"""Gemeinsame Zahlenformatierung fuer Preis-/Wertanzeigen (nie wissenschaftliche Notation).
Staleness-Erkennung (P-10) lebt in staleness.py (Domaenenlogik, auch vom Agent
gebraucht) - hier nur re-exportiert, damit bestehende Imports unveraendert bleiben."""
from __future__ import annotations

from staleness import format_price_age, is_history_stale, is_price_stale

__all__ = ["format_money", "format_price_age", "is_history_stale", "is_price_stale"]


def format_money(value: float | None) -> str:
    if value is None:
        return "-"
    if abs(value) >= 1:
        return f"{value:,.2f}"
    return f"{value:,.8f}"
