"""US-Praesidentschaftszyklus + FOMC-Ereigniskalender - Spezifikation Kap. 8/16,
Diskussion "erweiterte Makro-Zyklen-Sicht" 2026-07-08. Bewusst NUR Kontext-
Information (deskriptiv, historische Tendenz), KEINE Handelsentscheidung und KEINE
Handelslogik - siehe agent/regime.py fuer die eigentliche Regime-Bestimmung. Noch
NICHT in Facts/Pipeline verdrahtet, gleiches "Datensicht vor Nutzung"-Muster wie die
uebrigen Makro-Erweiterungen von heute.

Praesidentschaftszyklus: reine Datumsrechnung, KEINE externe Quelle noetig - der
Zyklus ist per US-Verfassung definiert (Wahl immer im November eines durch 4
teilbaren Jahres), nicht gemessen. Die "historische Tendenz" je Zyklusjahr ist ein
seit Jahrzehnten dokumentiertes (aber nicht garantiertes) saisonales Muster fuer
US-Aktien - fuer Krypto erst seit ~2023/24 wirklich relevant geworden, da
Regulierungshaltung inzwischen ein expliziter politischer Unterschied ist, mit noch
wenig eigener historischer Tiefe zum Testen.

FOMC-Termine: statische Liste, oeffentlich von federalreserve.gov/monetarypolicy/
fomccalendars.htm - bewusst KEINE live-API noetig, da Fed-Sitzungstermine Jahre im
Voraus veroeffentlicht werden und sich praktisch nie aendern. Braucht JAEHRLICHE
manuelle Aktualisierung der Liste unten (kein automatischer Prozess)."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

# Quelle: federalreserve.gov/monetarypolicy/fomccalendars.htm, live verifiziert 2026-07-08.
# Naechstes Jahr ergaenzen, sobald die Fed den 2027er-Kalender veroeffentlicht (ueblich
# im Spaetsommer/Herbst des Vorjahres).
FOMC_MEETING_DATES_2026: list[tuple[date, date]] = [
    (date(2026, 1, 27), date(2026, 1, 28)),
    (date(2026, 3, 17), date(2026, 3, 18)),
    (date(2026, 4, 28), date(2026, 4, 29)),
    (date(2026, 6, 16), date(2026, 6, 17)),
    (date(2026, 7, 28), date(2026, 7, 29)),
    (date(2026, 9, 15), date(2026, 9, 16)),
    (date(2026, 10, 27), date(2026, 10, 28)),
    (date(2026, 12, 8), date(2026, 12, 9)),
]

_CYCLE_YEAR_INFO = {
    1: (
        "Jahr 1 (Nachwahljahr)",
        "historisch schwächstes Jahr - neue Regierung setzt oft unpopuläre/nötige "
        "Maßnahmen früh im Zyklus um",
    ),
    2: (
        "Jahr 2 (Midterm-Jahr)",
        "volatil, oft eine Korrektur - ABER der Zeitraum um/nach den Midterms zählt "
        "zu den robustesten saisonalen Mustern überhaupt (politische Unsicherheit "
        "löst sich auf, unabhängig vom Ausgang)",
    ),
    3: (
        "Jahr 3 (Vorwahljahr)",
        "historisch stärkstes Jahr - Regierungen stimulieren tendenziell Richtung "
        "Wiederwahl",
    ),
    4: (
        "Jahr 4 (Wahljahr)",
        "positiv im Schnitt, aber volatiler, Sektor-Rotation je nach erwartetem "
        "Wahlausgang",
    ),
}


@dataclass
class PresidentialCycleContext:
    year_in_cycle: int  # 1-4
    label: str
    historical_bias: str  # deskriptiv, KEINE Prognose-Garantie
    last_election_year: int
    next_election_year: int


def get_presidential_cycle_context(today: date | None = None) -> PresidentialCycleContext:
    today = today or date.today()
    remainder = today.year % 4
    year_in_cycle = 4 if remainder == 0 else remainder
    last_election_year = today.year if remainder == 0 else today.year - remainder
    label, bias = _CYCLE_YEAR_INFO[year_in_cycle]
    return PresidentialCycleContext(
        year_in_cycle=year_in_cycle,
        label=label,
        historical_bias=bias,
        last_election_year=last_election_year,
        next_election_year=last_election_year + 4,
    )


@dataclass
class UpcomingEvent:
    name: str
    date: date
    days_until: int


def get_upcoming_fomc_meetings(today: date | None = None, within_days: int = 30) -> list[UpcomingEvent]:
    """Nur Termine aus `FOMC_MEETING_DATES_2026` - Jahresgrenze beachten, siehe
    Modul-Docstring zur jaehrlichen Aktualisierung."""
    today = today or date.today()
    events = []
    for start, end in FOMC_MEETING_DATES_2026:
        days_until = (start - today).days
        if 0 <= days_until <= within_days:
            events.append(
                UpcomingEvent(
                    name=f"FOMC-Sitzung ({start:%d.%m.}–{end:%d.%m.%Y})",
                    date=start,
                    days_until=days_until,
                )
            )
    return events
