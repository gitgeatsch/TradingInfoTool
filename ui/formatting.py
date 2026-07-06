"""Gemeinsame Zahlenformatierung fuer Preis-/Wertanzeigen (nie wissenschaftliche Notation)
sowie Staleness-Erkennung (P-10: veraltete Daten muessen sichtbar markiert werden)."""
from __future__ import annotations

from datetime import datetime, timezone

# P-10 / Spezifikation Kap. 16: Schwellenwerte fuer "veraltet"
PRICE_STALE_THRESHOLD_MINUTES = 10  # 2x 5-Min-Scheduler-Takt
HISTORY_STALE_THRESHOLD_DAYS = 2  # 1 Tag Rueckstand ist normal, 2+ deutet auf Ausfall hin


def format_money(value: float | None) -> str:
    if value is None:
        return "-"
    if abs(value) >= 1:
        return f"{value:,.2f}"
    return f"{value:,.8f}"


def _parse_utc(timestamp: str) -> datetime:
    dt = datetime.fromisoformat(timestamp)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def is_price_stale(fetched_at: str | None) -> bool:
    if fetched_at is None:
        return True
    age_minutes = (datetime.now(timezone.utc) - _parse_utc(fetched_at)).total_seconds() / 60
    return age_minutes > PRICE_STALE_THRESHOLD_MINUTES


def format_price_age(fetched_at: str | None) -> str:
    if fetched_at is None:
        return "nie aktualisiert"
    age_minutes = int((datetime.now(timezone.utc) - _parse_utc(fetched_at)).total_seconds() / 60)
    if age_minutes < 1:
        return "gerade eben"
    if age_minutes < 60:
        return f"vor {age_minutes} Min."
    age_hours = age_minutes // 60
    return f"vor {age_hours} Std."


def is_history_stale(last_date: str | None) -> bool:
    if last_date is None:
        return True
    last = datetime.fromisoformat(last_date).date()
    today = datetime.now(timezone.utc).date()
    return (today - last).days > HISTORY_STALE_THRESHOLD_DAYS
