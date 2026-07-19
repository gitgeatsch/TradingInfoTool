"""EIA Open Data API (U.S. Energy Information Administration) - 2026-07-19,
Datenquellen-Recherche-Nachfolger (siehe Regelwerksmanual-Nachtrag "zwei neue
Datenquellen"). Schliesst die im Rohstoff-Pipeline-Disclaimer bereits als Luecke
dokumentierte Erdgas-Lagerbestandsdaten (siehe agent/rohstoff/analyst.py
build_facts() Disclaimer-Text: "EIA-Erdgas-Speicher sind NOCH NICHT einbezogen").

Kostenlos, freier API-Key per E-Mail-Registrierung unter
https://www.eia.gov/opendata/register.php - KEINE erkennbaren restriktiven
Rate-Limits fuer unseren Nutzungsumfang (eine Handvoll Abfragen pro Aktien-/
Rohstoff-Signal-Lauf).

LIVE VERIFIZIERT (2026-07-19, echter Nutzer-Key): `WEEKLY_STORAGE_SERIES_ID`
liefert echte, plausible Wochenwerte (Lower-48-Bestand steigt saisonal
richtig von 2.483 auf 3.024 Bcf ueber den 8-Wochen-Testzeitraum Ende
Mai/Anfang Juli 2026, Build in jeder Woche - konsistent mit dem
US-Sommer-Fuellsaison-Muster). Datenform und Feldnamen bestaetigt korrekt."""
from __future__ import annotations

import logging
from dataclasses import dataclass

import requests

from database.api_health import track_api_health

logger = logging.getLogger(__name__)

EIA_BASE_URL = "https://api.eia.gov/v2/natural-gas/stor/wkly/data/"

# EIA-Namenskonvention: N=Natural gas, W2=Weekly/underground storage,
# EPG0=Total natural gas, SWO=Working gas in underground storage,
# R48=Lower 48 States, BCF=Billion cubic feet. Siehe Vorbehalt im Modul-Docstring.
WEEKLY_STORAGE_SERIES_ID = "NW2_EPG0_SWO_R48_BCF"


@dataclass
class NatGasStorageReading:
    date: str
    value_bcf: float
    net_change_bcf: float | None  # Woche-zu-Woche-Aenderung, None beim aeltesten Punkt


@track_api_health("eia")
def get_natural_gas_storage_history(
    api_key: str, n_weeks: int = 8, session: requests.Session | None = None,
) -> list[NatGasStorageReading]:
    """Letzte `n_weeks` Wochenwerte des Lower-48-Erdgas-Lagerbestands, aufsteigend
    sortiert, inkl. berechneter Woche-zu-Woche-Aenderung (Build = Zunahme,
    Draw = Abnahme). Live verifiziert (2026-07-19, siehe Modul-Docstring)."""
    session = session or requests.Session()
    response = session.get(
        EIA_BASE_URL,
        params={
            "api_key": api_key,
            "frequency": "weekly",
            "data[0]": "value",
            "facets[series][]": WEEKLY_STORAGE_SERIES_ID,
            "sort[0][column]": "period",
            "sort[0][direction]": "desc",
            "length": n_weeks,
        },
        timeout=15,
    )
    response.raise_for_status()
    rows = response.json()["response"]["data"]
    rows_asc = list(reversed(rows))  # EIA liefert absteigend -> fuer die Delta-Berechnung umdrehen

    readings: list[NatGasStorageReading] = []
    previous_value: float | None = None
    for row in rows_asc:
        value = float(row["value"])
        net_change = None if previous_value is None else round(value - previous_value, 1)
        readings.append(NatGasStorageReading(date=row["period"], value_bcf=value, net_change_bcf=net_change))
        previous_value = value
    return readings
