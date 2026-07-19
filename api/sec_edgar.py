"""SEC EDGAR Insider-Trading (Form 4) - 2026-07-19, Datenquellen-Recherche-Nachfolger
(siehe Regelwerksmanual-Nachtrag "Backtracking-Aussagekraft-Audit" / Memory
project_selbstverifikation_ki_trimmen.md). Komplett kostenlos, offiziell, kein
API-Key noetig - nur ein aussagekraeftiger User-Agent-Header ist Pflicht (SEC-
Vorgabe, siehe https://www.sec.gov/os/accessing-edgar-data). Rate-Limit laut SEC:
10 Requests/Sekunde/IP - bei unserem Nutzungsmuster (wenige Aktien, Cooldown
24-72h) nie annaehernd erreicht, daher kein eigener Rate-Limiter noetig.

Live verifiziert (2026-07-19) fuer VST (CIK 1692819) und PLTR (CIK 1321655):
- `company_tickers.json` liefert Ticker->CIK.
- `submissions/CIK##########.json` liefert die Filing-Liste inkl. Form-Typ +
  `primaryDocument` (Pfad wie "xslF345X06/wk-form4_XXXX.xml" - das ist die
  XSLT-GERENDERTE HTML-Ansicht, NICHT die Rohdaten). Die eigentliche Roh-XML mit
  den strukturierten Transaktionsdaten liegt im selben Verzeichnis OHNE den
  "xslF345X06/"-Praefix (bestaetigt fuer beide Testfaelle) - reiner
  String-Präfix-Strip, kein zusaetzlicher Index-Abruf noetig.

Nur Transaktionscode P (offener Markt-Kauf) und S (offener Markt-Verkauf) gelten
als echtes Insider-Conviction-Signal - A (Zuteilung/Grant), M (Optionsausuebung),
F (Steuerabzug), G (Schenkung) etc. sind administrativ/verguetungsbedingt und
sagen nichts ueber die Markteinschaetzung des Insiders aus (P-10: keine
Fehlinterpretation als Kauf-/Verkaufssignal)."""
from __future__ import annotations

import logging
from dataclasses import dataclass

import requests

from database.api_health import track_api_health

logger = logging.getLogger(__name__)

USER_AGENT = "TradingInfoTool gernotspiessmaier@gmail.com"
TICKER_CIK_URL = "https://www.sec.gov/files/company_tickers.json"
SUBMISSIONS_URL_TEMPLATE = "https://data.sec.gov/submissions/CIK{cik:010d}.json"
ARCHIVES_BASE_URL = "https://www.sec.gov/Archives/edgar/data"

# Nur diese beiden Codes sind ein echtes Kauf-/Verkaufssignal, siehe Modul-Docstring.
_CONVICTION_CODES = {"P": "kauf", "S": "verkauf"}

_cik_cache: dict[str, int] = {}


@dataclass
class InsiderTransaction:
    owner_name: str
    is_officer: bool
    is_director: bool
    is_ten_percent_owner: bool
    transaction_code: str
    transaction_date: str
    shares: float
    price_per_share: float | None
    acquired_disposed: str  # "A" (Acquired) oder "D" (Disposed)
    filing_date: str


def _headers() -> dict[str, str]:
    return {"User-Agent": USER_AGENT}


@track_api_health("sec_edgar")
def get_cik_for_ticker(ticker: str, session: requests.Session | None = None) -> int | None:
    """Ticker->CIK-Aufloesung ueber SECs offizielle Gesamtliste. In-Memory
    gecacht (Modul-Konstante) - die Zuordnung aendert sich praktisch nie
    innerhalb eines App-Laufs, ein wiederholter ~800KB-Abruf pro Signal waere
    reine Verschwendung."""
    ticker_upper = ticker.upper()
    if ticker_upper in _cik_cache:
        return _cik_cache[ticker_upper]

    session = session or requests.Session()
    response = session.get(TICKER_CIK_URL, headers=_headers(), timeout=15)
    response.raise_for_status()
    data = response.json()
    for entry in data.values():
        _cik_cache[entry["ticker"].upper()] = entry["cik_str"]
    return _cik_cache.get(ticker_upper)


@track_api_health("sec_edgar")
def _fetch_recent_form4_filings(cik: int, session: requests.Session, max_filings: int, lookback_tage: int) -> list[dict]:
    from datetime import date, timedelta

    response = session.get(SUBMISSIONS_URL_TEMPLATE.format(cik=cik), headers=_headers(), timeout=15)
    response.raise_for_status()
    recent = response.json()["filings"]["recent"]
    cutoff = (date.today() - timedelta(days=lookback_tage)).isoformat()

    filings = []
    for i, form in enumerate(recent["form"]):
        if form != "4":
            continue
        filing_date = recent["filingDate"][i]
        if filing_date < cutoff:
            continue
        filings.append({
            "accessionNumber": recent["accessionNumber"][i],
            "filingDate": filing_date,
            "primaryDocument": recent["primaryDocument"][i],
        })
        if len(filings) >= max_filings:
            break
    return filings


def _parse_form4_xml(xml_text: str, filing_date: str) -> list[InsiderTransaction]:
    import xml.etree.ElementTree as ET

    root = ET.fromstring(xml_text)
    owner_el = root.find("reportingOwner")
    if owner_el is None:
        return []
    owner_name = (owner_el.findtext("reportingOwnerId/rptOwnerName") or "").strip()
    relationship = owner_el.find("reportingOwnerRelationship")
    is_officer = (relationship.findtext("isOfficer") if relationship is not None else "0") == "1"
    is_director = (relationship.findtext("isDirector") if relationship is not None else "0") == "1"
    is_ten_pct = (relationship.findtext("isTenPercentOwner") if relationship is not None else "0") == "1"

    transactions = []
    for tx in root.findall("nonDerivativeTable/nonDerivativeTransaction"):
        code = tx.findtext("transactionCoding/transactionCode")
        if code not in _CONVICTION_CODES:
            continue
        shares_text = tx.findtext("transactionAmounts/transactionShares/value")
        price_text = tx.findtext("transactionAmounts/transactionPricePerShare/value")
        acquired_disposed = tx.findtext("transactionAmounts/transactionAcquiredDisposedCode/value") or ""
        tx_date = tx.findtext("transactionDate/value") or filing_date
        if shares_text is None:
            continue
        transactions.append(InsiderTransaction(
            owner_name=owner_name,
            is_officer=is_officer,
            is_director=is_director,
            is_ten_percent_owner=is_ten_pct,
            transaction_code=code,
            transaction_date=tx_date,
            shares=float(shares_text),
            price_per_share=float(price_text) if price_text else None,
            acquired_disposed=acquired_disposed,
            filing_date=filing_date,
        ))
    return transactions


def get_recent_insider_transactions(
    ticker: str, session: requests.Session | None = None,
    max_filings: int = 5, lookback_tage: int = 90,
) -> list[InsiderTransaction]:
    """Holt die letzten `max_filings` Form-4-Filings (max. `lookback_tage` alt)
    fuer `ticker` und extrahiert daraus NUR echte Kauf-/Verkaufstransaktionen
    (Code P/S, siehe Modul-Docstring). P-10: liefert eine leere Liste statt
    zu raten, wenn CIK nicht gefunden wird oder keine Form-4-Filings im
    Zeitfenster liegen - kein Fehler, einfach keine Daten."""
    session = session or requests.Session()
    cik = get_cik_for_ticker(ticker, session)
    if cik is None:
        logger.info("SEC EDGAR: keine CIK fuer Ticker %s gefunden", ticker)
        return []

    filings = _fetch_recent_form4_filings(cik, session, max_filings, lookback_tage)
    transactions: list[InsiderTransaction] = []
    for filing in filings:
        accession_nodash = filing["accessionNumber"].replace("-", "")
        raw_filename = filing["primaryDocument"].split("/")[-1]
        url = f"{ARCHIVES_BASE_URL}/{cik}/{accession_nodash}/{raw_filename}"
        try:
            response = session.get(url, headers=_headers(), timeout=15)
            response.raise_for_status()
            transactions.extend(_parse_form4_xml(response.text, filing["filingDate"]))
        except Exception as exc:  # noqa: BLE001 - ein fehlerhaftes Einzel-Filing darf die anderen nicht blockieren
            logger.info("SEC EDGAR: Form-4-Filing %s fuer %s konnte nicht geparst werden: %s", filing["accessionNumber"], ticker, exc)
    return transactions


def summarize_insider_activity(transactions: list[InsiderTransaction]) -> dict | None:
    """Aggregiert die rohen Transaktionen zu einer knappen Zusammenfassung fuers
    Facts-Objekt - reine Lesefunktion, keine Bewertung/Meinung (das bleibt dem
    LLM ueberlassen). None, wenn keine Transaktionen vorliegen (Prompt sollte
    den Fakt dann einfach weglassen, P-10)."""
    if not transactions:
        return None
    kaeufe = [t for t in transactions if t.transaction_code == "P"]
    verkaeufe = [t for t in transactions if t.transaction_code == "S"]
    return {
        "anzahl_kaeufe": len(kaeufe),
        "anzahl_verkaeufe": len(verkaeufe),
        "kauf_volumen_usd": sum(t.shares * t.price_per_share for t in kaeufe if t.price_per_share) or None,
        "verkauf_volumen_usd": sum(t.shares * t.price_per_share for t in verkaeufe if t.price_per_share) or None,
        "letzte_transaktion_datum": max(t.transaction_date for t in transactions),
        "beteiligte_insider": sorted({t.owner_name for t in transactions}),
    }
