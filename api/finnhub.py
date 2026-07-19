"""Finnhub Free-Tier - 2026-07-19, Datenquellen-Recherche-Nachfolger (siehe
Regelwerksmanual-Nachtrag "zwei neue Datenquellen"). Nur `recommendation-trends`
umgesetzt (Analysten-Konsens-VERLAUF ueber die letzten Monate, ergaenzt den
bereits vorhandenen yfinance-Momentanwert `fundamentaldaten.analysten_konsens`
um eine Richtungskomponente - "wird der Konsens optimistischer oder
pessimistischer?"). Earnings-Kalender BEWUSST NICHT umgesetzt - waere
redundant mit dem bereits vorhandenen `fundamentaldaten.naechstes_earnings_datum`
(aus yfinance), zwei potenziell abweichende Terminquellen im selben Prompt
waeren mehr Verwirrung als Mehrwert (P-10).

Kostenlos, freier API-Key per Registrierung unter https://finnhub.io/register,
Free-Tier laut Dokumentation 60 Requests/Minute.

LIVE VERIFIZIERT (2026-07-19, echter Nutzer-Key): `/stock/recommendation`
liefert fuer VST und PLTR je 4 Monatswerte mit den erwarteten Feldern
(period/strongBuy/buy/hold/sell/strongSell), Konsens plausibel (VST fast
ausschliesslich Buy/Strong-Buy, PLTR gemischter mit Hold-Anteil). Datenform
und Feldnamen bestaetigt korrekt."""
from __future__ import annotations

import logging
from dataclasses import dataclass

import requests

from database.api_health import track_api_health

logger = logging.getLogger(__name__)

FINNHUB_BASE_URL = "https://finnhub.io/api/v1"


@dataclass
class RecommendationTrend:
    period: str  # YYYY-MM-DD, Monatsanfang
    strong_buy: int
    buy: int
    hold: int
    sell: int
    strong_sell: int


@track_api_health("finnhub")
def get_recommendation_trends(
    symbol: str, api_key: str, session: requests.Session | None = None,
) -> list[RecommendationTrend]:
    """Analysten-Empfehlungs-Verteilung der letzten Monate (neuester zuerst laut
    Finnhub-Doku - hier absteigend nach `period` sortiert zurueckgegeben, damit
    der Aufrufer `[0]` als aktuellsten Monat nutzen kann)."""
    session = session or requests.Session()
    response = session.get(
        f"{FINNHUB_BASE_URL}/stock/recommendation",
        params={"symbol": symbol, "token": api_key},
        timeout=15,
    )
    response.raise_for_status()
    data = response.json()
    trends = [
        RecommendationTrend(
            period=row["period"], strong_buy=row["strongBuy"], buy=row["buy"],
            hold=row["hold"], sell=row["sell"], strong_sell=row["strongSell"],
        )
        for row in data
    ]
    return sorted(trends, key=lambda t: t.period, reverse=True)


def summarize_recommendation_trend(trends: list[RecommendationTrend]) -> dict | None:
    """Vergleicht den aktuellsten mit dem zweitaktuellsten Monat, um eine
    Richtungsaussage abzuleiten - reine Lesefunktion, keine Bewertung (das
    bleibt dem LLM ueberlassen). None, wenn keine Daten vorliegen."""
    if not trends:
        return None
    aktuell = trends[0]
    aktuell_dict = {
        "periode": aktuell.period,
        "strong_buy": aktuell.strong_buy,
        "buy": aktuell.buy,
        "hold": aktuell.hold,
        "sell": aktuell.sell,
        "strong_sell": aktuell.strong_sell,
    }
    if len(trends) < 2:
        return {"aktuell": aktuell_dict, "vormonat": None}
    vormonat = trends[1]
    return {
        "aktuell": aktuell_dict,
        "vormonat": {
            "periode": vormonat.period,
            "strong_buy": vormonat.strong_buy,
            "buy": vormonat.buy,
            "hold": vormonat.hold,
            "sell": vormonat.sell,
            "strong_sell": vormonat.strong_sell,
        },
    }
