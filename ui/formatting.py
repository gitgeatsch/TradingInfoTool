"""Gemeinsame Zahlenformatierung fuer Preis-/Wertanzeigen (nie wissenschaftliche Notation)."""
from __future__ import annotations


def format_money(value: float | None) -> str:
    if value is None:
        return "-"
    if abs(value) >= 1:
        return f"{value:,.2f}"
    return f"{value:,.8f}"
