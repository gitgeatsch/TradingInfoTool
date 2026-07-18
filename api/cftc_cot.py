"""CFTC Commitments-of-Traders-Report (2026-07-18, Rohstoff-Pipeline) - kostenlose,
oeffentliche Socrata-API der US-Aufsichtsbehoerde (`publicreporting.cftc.gov`), kein
API-Key noetig. Liefert die woechentliche "Disaggregated Futures Only"-Tabelle
(Dataset `72hh-3qpy`), die Positionen nach Haendlerkategorie aufschluesselt -
`m_money_positions_long_all`/`m_money_positions_short_all` ("Managed Money", grosse
spekulative Fonds) ist der in diesem Projekt genutzte Positionierungs-Proxy (naeher
an "Sentiment grosser Spekulanten" als die Legacy-Kategorie "Non-Commercial").

Marktnamen live verifiziert (2026-07-18, siehe Basisinfos/Regelwerksmanual.md
Nachtrag) - CFTC benennt Kontrakte gelegentlich um (z.B. Erdgas hiess frueher
"NATURAL GAS - NEW YORK MERCANTILE EXCHANGE", seit einer nicht dokumentierten
CME-Umbenennung heisst der liquide Hauptkontrakt "NAT GAS NYME - ..." - die alte
Bezeichnung existiert zwar noch als Marktname in der Tabelle, hat aber seit 2024
keine neuen Daten mehr). Kupfer hat ebenfalls eine Falle: "COPPER-GRADE #1 - ..."
sieht wie der Hauptkontrakt aus, ist aber ein separater, kaum gehandelter Eintrag -
der echte Hauptkontrakt heisst "COPPER- #1 - ...". Bei einer erneuten CME-
Umbenennung liefert get_cot_snapshot() schlicht None (kein stiller Fallback auf
einen falschen/veralteten Wert, siehe dortigen Docstring) - COT_MARKET_NAMES
muesste dann manuell aktualisiert werden, analog zu den FRED-Series-IDs in
api/macro.py."""
from __future__ import annotations

import logging
from dataclasses import dataclass

import requests

from database.api_health import track_api_health

logger = logging.getLogger(__name__)

CFTC_DISAGGREGATED_URL = "https://publicreporting.cftc.gov/resource/72hh-3qpy.json"

# Live verifiziert 2026-07-18 (siehe Modul-Docstring) - falls sich ein Marktname
# erneut aendert, greift automatisch die Fallback-Suche in get_cot_snapshot().
COT_MARKET_NAMES = {
    "gold": "GOLD - COMMODITY EXCHANGE INC.",
    "silber": "SILVER - COMMODITY EXCHANGE INC.",
    "kupfer": "COPPER- #1 - COMMODITY EXCHANGE INC.",
    "erdgas": "NAT GAS NYME - NEW YORK MERCANTILE EXCHANGE",
}


@dataclass
class CotSnapshot:
    rohstoff: str
    marktname: str
    report_datum: str
    open_interest: int
    managed_money_long: int
    managed_money_short: int
    managed_money_netto: int
    # Anteil Managed-Money-Long an OI, grobe Positionierungs-Intensitaet -
    # deterministisch vorberechnet, damit das LLM nicht selbst dividieren muss
    # (P-10-Analogie zu anderen vorberechneten Prozentwerten im Projekt).
    managed_money_long_anteil_oi_prozent: float


@track_api_health("cftc_cot")
def _fetch_latest_report(market_name: str, session: requests.Session | None = None) -> dict | None:
    session = session or requests.Session()
    params = {
        "$where": f"market_and_exchange_names = '{market_name}'",
        "$order": "report_date_as_yyyy_mm_dd DESC",
        "$limit": 1,
    }
    response = session.get(CFTC_DISAGGREGATED_URL, params=params, timeout=20)
    response.raise_for_status()
    rows = response.json()
    return rows[0] if rows else None


def get_cot_snapshot(rohstoff: str, session: requests.Session | None = None) -> CotSnapshot | None:
    """`rohstoff`: einer der Schluessel in COT_MARKET_NAMES ("gold"/"silber"/
    "kupfer"/"erdgas"). Gibt None zurueck, wenn der Marktname keine Daten mehr
    liefert (z.B. nach einer erneuten CME-Umbenennung) - P-10: Aufrufer muss mit
    fehlender Positionierung umgehen koennen, kein stiller Fallback auf einen
    veralteten/falschen Wert."""
    market_name = COT_MARKET_NAMES.get(rohstoff)
    if market_name is None:
        raise ValueError(f"Unbekannter Rohstoff-Schluessel: {rohstoff!r}")

    row = _fetch_latest_report(market_name, session)
    if row is None:
        logger.warning(
            "CFTC COT: kein Report fuer Marktname %r (%s) gefunden - evtl. erneut umbenannt",
            market_name, rohstoff,
        )
        return None

    open_interest = int(row["open_interest_all"])
    mm_long = int(row["m_money_positions_long_all"])
    mm_short = int(row["m_money_positions_short_all"])
    return CotSnapshot(
        rohstoff=rohstoff,
        marktname=market_name,
        report_datum=row["report_date_as_yyyy_mm_dd"][:10],
        open_interest=open_interest,
        managed_money_long=mm_long,
        managed_money_short=mm_short,
        managed_money_netto=mm_long - mm_short,
        managed_money_long_anteil_oi_prozent=(
            round(mm_long / open_interest * 100, 1) if open_interest > 0 else 0.0
        ),
    )
