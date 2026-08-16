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
    # 2026-07-19 ergaenzt (Release-2-Konzeption Kategorie-Thesen, Luecke aus
    # Basisinfos/Kategorie_Basisinformationen_Release2.md Abschnitt 8) - live
    # gegen die echte CFTC-API geprueft (beide Kontrakte real, 2026-07-14er
    # Bericht, WTI mit ~1,9 Mio. Open Interest der mit Abstand liquideste
    # Oel-Future, "-PHYSICAL"/"LAST DAY" sind die CFTC-eigenen Bezeichnungen
    # fuer die jeweiligen Hauptkontrakte, keine Tippfehler).
    "rohoel_wti": "WTI-PHYSICAL - NEW YORK MERCANTILE EXCHANGE",
    "rohoel_brent": "BRENT LAST DAY - NEW YORK MERCANTILE EXCHANGE",
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


@track_api_health("cftc_cot")
def get_cot_long_anteil_history(rohstoff: str, grenze: int = 400,
                                session: requests.Session | None = None) -> list:
    """Der Long-Anteil des Managed Money am Open Interest als Reihe.

    [(bericht_datum, anteil_prozent), ...], AUFSTEIGEND.

    WOFUER (2026-08-16, Schritt 3). `get_cot_snapshot()` liefert einen Stand.
    "142.318 Kontrakte netto long" traegt fuer ein Sprachmodell nichts - erst
    die Lage in der eigenen Geschichte ist eine Aussage (R-T5). Dafuer die
    Reihe.

    WARUM DER ANTEIL UND NICHT DIE NETTOPOSITION. Gemessen am 16.08. ueber die
    letzten zwei Jahre, Anteil der Wochen mit Extremwert (Perzentil >=90 oder
    <=10) im 156-Wochen-Fenster:

        Long-Anteil am OI     Gold 50 %  Silber 15 %  Kupfer  4 %  Erdgas 35 %
        Netto Managed Money   Gold 63 %  Silber 39 %  Kupfer 41 %  Erdgas 21 %

    Die Nettoposition haengt an der absoluten Marktgroesse und wandert mit
    ihr; der Anteil ist bereits normiert - dieselbe Ueberlegung, aus der
    `positionierung.py` nur OI-AENDERUNGEN vergleicht und keine Niveaus.

    LIVE GEPRUEFT am 16.08.: Gold und Silber tragen 400 Berichte ab 2018-12-18,
    Kupfer und Erdgas 236 ab 2022-02-08 - die Folge der dokumentierten
    CME-Umbenennungen. Fuer ein 156-Wochen-Fenster reicht beides."""
    market_name = COT_MARKET_NAMES.get(rohstoff)
    if market_name is None:
        raise ValueError(f"Unbekannter Rohstoff-Schluessel: {rohstoff!r}")
    session = session or requests.Session()
    response = session.get(
        CFTC_DISAGGREGATED_URL,
        params={
            "$where": f"market_and_exchange_names = '{market_name}'",
            "$select": "report_date_as_yyyy_mm_dd,open_interest_all,"
                       "m_money_positions_long_all",
            # ⚠️ ABSTEIGEND SORTIEREN UND ERST IN PYTHON DREHEN.
            #
            # `ASC` mit `$limit` liefert die AELTESTEN Berichte, nicht die
            # juengsten. Gold und Silber tragen mehr als 400 Zeilen; die erste
            # Fassung dieser Funktion lieferte damit den Stand von 2014 - mit
            # einem einwandfrei aussehenden 46. Perzentil. Kupfer und Erdgas
            # haben nur 236 Berichte und waren deshalb zufaellig richtig, was
            # den Fehler beinahe verdeckt haette.
            #
            # Die Messung, die das Fenster festgelegt hat, benutzte `DESC` -
            # dieselbe Abfrage, andere Daten. "Immer an der Quelle pruefen"
            # gilt auch fuer die eigene Messung von vor zehn Minuten.
            "$order": "report_date_as_yyyy_mm_dd DESC",
            "$limit": int(grenze),
        },
        timeout=30,
    )
    response.raise_for_status()
    raus = []
    for z in (response.json() or []):
        try:
            oi = int(z["open_interest_all"])
            lang = int(z["m_money_positions_long_all"])
        except (KeyError, TypeError, ValueError):
            # KEIN GERATENER WERT (P-10) - eine unvollstaendige Woche faellt
            # aus der Reihe, statt als 0 in das Perzentil einzugehen.
            continue
        if oi > 0:
            raus.append((str(z["report_date_as_yyyy_mm_dd"])[:10],
                         round(100.0 * lang / oi, 2)))
    if not raus:
        logger.warning(
            "CFTC COT: keine Historie fuer Marktname %r (%s) - evtl. umbenannt",
            market_name, rohstoff)
    # Zurueck in die Zeitrichtung, die jeder Aufrufer erwartet.
    return list(reversed(raus))


def get_cot_snapshot(rohstoff: str, session: requests.Session | None = None) -> CotSnapshot | None:
    """`rohstoff`: einer der Schluessel in COT_MARKET_NAMES ("gold"/"silber"/
    "kupfer"/"erdgas"/"rohoel_wti"/"rohoel_brent"). Gibt None zurueck, wenn der Marktname keine Daten mehr
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
