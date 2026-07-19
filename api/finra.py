"""FINRA Consolidated Short Interest - 2026-07-19, letzter der vier vom Nutzer
gewaehlten Datenquellen-Kandidaten (siehe Regelwerksmanual-Nachtrag "zwei neue
Datenquellen" + "EIA-Erdgas-Lagerbestand + Finnhub-Analysten-Trend").

LIVE VERIFIZIERT (2026-07-19): der Endpunkt `api.finra.org/data/group/otcMarket/
name/ConsolidatedShortInterest` ist OEFFENTLICH ohne API-Key nutzbar (dieselbe
Backend-API, die finra.org's eigene Daten-Browse-Oberflaeche verwendet) - anders
als EIA/Finnhub war hier kein Nutzer-Key-Setup noetig. Fuer VST/PLTR (beide
NYSE) echte Historie zurueckbekommen (VST: 205 Datenpunkte 2017-2026, PLTR: 138
Datenpunkte). Bei unbekanntem Symbol liefert die API HTTP 204 (leerer Body,
KEIN valides JSON) statt einer leeren Liste - `response.json()` wuerde dabei
crashen, deshalb expliziter 204-Check unten.

FINRA-Mitgliedsfirmen melden Short-Positionen laut Rule 4560 zweimal im Monat
(Settlement zum 15. und zum letzten Handelstag), veroeffentlicht am 7.
Geschaeftstag danach - die Daten sind also strukturell IMMER 1-3 Wochen alt,
kein Echtzeit-Signal. `daysToCoverQuantity` (aktuelle Short-Position / mittleres
Tagesvolumen) ist die gaengige "wie viele Handelstage braucht es, die Shorts
einzudecken"-Kennzahl."""
from __future__ import annotations

import logging
from dataclasses import dataclass

import requests

from database.api_health import track_api_health

logger = logging.getLogger(__name__)

FINRA_SHORT_INTEREST_URL = "https://api.finra.org/data/group/otcMarket/name/ConsolidatedShortInterest"

# FINRA liefert die volle History unsortiert und ohne Sortier-Unterstuetzung ueber
# den Partition-Key settlementDate hinweg (siehe Modul-Docstring) - ein grosszuegiger
# Limit-Wert holt die komplette ~5-Jahres-Historie in einem Aufruf, Sortierung/
# Zuschneiden auf n_periods passiert clientseitig.
_FETCH_LIMIT = 500


@dataclass
class ShortInterestReading:
    settlement_date: str
    short_position_qty: int
    days_to_cover: float | None
    change_percent: float | None  # Aenderung ggue. der VORHERIGEN Meldung


@track_api_health("finra")
def get_short_interest_history(
    symbol: str, n_periods: int = 6, session: requests.Session | None = None,
) -> list[ShortInterestReading]:
    """Letzte `n_periods` Meldeperioden (aufsteigend sortiert) fuer ein
    NYSE/Nasdaq-Symbol. Leere Liste, wenn FINRA das Symbol nicht fuehrt (z.B.
    OTC-only oder unbekannt) - kein Fehler (P-8)."""
    session = session or requests.Session()
    response = session.post(
        FINRA_SHORT_INTEREST_URL,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        json={
            "limit": _FETCH_LIMIT,
            "compareFilters": [{"compareType": "equal", "fieldName": "symbolCode", "fieldValue": symbol}],
        },
        timeout=15,
    )
    response.raise_for_status()
    if response.status_code == 204 or not response.text.strip():
        return []
    rows = response.json()
    rows_sorted = sorted(rows, key=lambda r: r["settlementDate"])
    recent = rows_sorted[-n_periods:]
    return [
        ShortInterestReading(
            settlement_date=row["settlementDate"],
            short_position_qty=int(row["currentShortPositionQuantity"]),
            days_to_cover=row.get("daysToCoverQuantity"),
            change_percent=row.get("changePercent"),
        )
        for row in recent
    ]


def summarize_short_interest(readings: list[ShortInterestReading]) -> dict | None:
    """Vergleicht die letzte mit der vorletzten Meldeperiode, um eine
    Richtungsaussage abzuleiten - reine Lesefunktion, keine Bewertung (bleibt
    dem LLM ueberlassen, siehe neue Regel 24 in agent/aktien/analyst.py). None,
    wenn keine Daten vorliegen."""
    if not readings:
        return None
    aktuell = readings[-1]
    aktuell_dict = {
        "settlement_date": aktuell.settlement_date,
        "short_position_qty": aktuell.short_position_qty,
        "days_to_cover": aktuell.days_to_cover,
        "change_percent_ggue_vorperiode": aktuell.change_percent,
    }
    if len(readings) < 2:
        return {"aktuell": aktuell_dict, "vorperiode": None}
    vorperiode = readings[-2]
    return {
        "aktuell": aktuell_dict,
        "vorperiode": {
            "settlement_date": vorperiode.settlement_date,
            "short_position_qty": vorperiode.short_position_qty,
            "days_to_cover": vorperiode.days_to_cover,
        },
    }
