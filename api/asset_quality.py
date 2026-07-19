"""Asset-Qualitaets-/Kompositionsdaten (2026-07-19, Nutzer-Wunsch: "wie setzt
sich zusammen" + "bessere Produkte filtern, damit die Investition besser
funktioniert und wir nicht wieder Produkte im Portfolio haben welche gleich
wieder delisted werden oder sind").

WICHTIGE EINSCHRAENKUNG (P-10, ehrlich statt vorgetaeuscht): diese Daten sind
NUR fuer Assets mit einem ECHTEN yfinance-Ticker verfuegbar (reale Boersen-
ETFs/Aktien, z.B. die bereits gehaltenen VVMX.DE/EXH3.DE/CEBS.DE/ISOC.DE oder
neue Aktien-Kandidaten aus dem Screener). Bitpandas EIGENE synthetische ETF/
ETC-Themenkoerbe (`agent/aktien/screener.py::scan_etf_candidates()`, Symbole
wie "COPPERMINE"/"GOLDMINE") sind KEINE echten boersengehandelten Fonds mit
oeffentlicher Zusammensetzung/AUM/Kostenquote - fuer diese Kandidaten bleibt
`get_asset_quality()` strukturell `None` (kein Fehler, aber auch kein
"besseres Produkt"-Vergleich moeglich). Die urspruengliche Nutzer-Sorge
("Produkte, die delisted werden") laesst sich fuer ECHTE Fonds ueber AUM
(kleine Fonds werden haeufiger geschlossen) als groben Proxy adressieren -
fuer Bitpandas eigene Produkte gibt es dafuer keine oeffentliche Datenquelle,
das bleibt ein bewusst offener, dokumentierter Rest (siehe Regelwerksmanual-
Nachtrag)."""
from __future__ import annotations

import logging
from dataclasses import dataclass

import yfinance as yf

from database.api_health import track_api_health

logger = logging.getLogger(__name__)


@dataclass
class AssetQualitySnapshot:
    symbol: str
    quote_type: str | None  # "ETF" | "EQUITY" | ...
    fund_family: str | None
    aum_usd: float | None  # None fuer Einzelaktien (kein Fonds)
    expense_ratio_pct: float | None  # None fuer Einzelaktien
    top_holdings: list[tuple[str, float]]  # [(Name, Anteil_pct), ...], leer bei Einzelaktien
    sektor_gewichtung: dict[str, float]  # nur Sektoren mit Anteil > 0, leer bei Einzelaktien


@track_api_health("yfinance")
def get_asset_quality(yfinance_symbol: str) -> AssetQualitySnapshot | None:
    """Liefert Fonds-Zusammensetzung (Top-10-Holdings, Sektor-Gewichtung) +
    Groessen-/Kosten-Kennzahlen (AUM, Kostenquote) ueber `yfinance`s
    `Ticker.info`/`Ticker.funds_data` - live verifiziert (2026-07-19) fuer
    VVMX.DE/EXH3.DE/SPY. Bei Einzelaktien (quoteType == "EQUITY") bleiben
    Fonds-spezifische Felder leer/None (kein Fehler, strukturell nicht
    vorhanden). `None` bei Netzwerkfehler oder unbekanntem Ticker (P-10)."""
    try:
        ticker = yf.Ticker(yfinance_symbol)
        info = ticker.info
        quote_type = info.get("quoteType")
        if quote_type is None:
            # yfinance wirft bei einem unbekannten Ticker KEINE Exception,
            # sondern liefert ein (fast) leeres info-Dict (live bestaetigt,
            # 2026-07-19) - ohne diesen Check waere ein Tippfehler im
            # yfinance_symbol als "echtes Asset ohne Fonds-Daten" statt als
            # "Ticker nicht gefunden" fehlinterpretiert worden.
            return None
        aum_usd = info.get("totalAssets")
        expense_ratio_pct = info.get("netExpenseRatio")
        fund_family = info.get("fundFamily")

        top_holdings: list[tuple[str, float]] = []
        sektor_gewichtung: dict[str, float] = {}
        if quote_type == "ETF":
            funds_data = ticker.funds_data
            if funds_data is not None:
                holdings_df = funds_data.top_holdings
                if holdings_df is not None and not holdings_df.empty:
                    top_holdings = [
                        (row["Name"], round(row["Holding Percent"] * 100, 2))
                        for _, row in holdings_df.iterrows()
                    ]
                weightings = funds_data.sector_weightings or {}
                sektor_gewichtung = {k: round(v * 100, 2) for k, v in weightings.items() if v > 0}

        return AssetQualitySnapshot(
            symbol=yfinance_symbol,
            quote_type=quote_type,
            fund_family=fund_family,
            aum_usd=aum_usd,
            expense_ratio_pct=expense_ratio_pct,
            top_holdings=top_holdings,
            sektor_gewichtung=sektor_gewichtung,
        )
    except Exception as exc:
        logger.info("Asset-Qualitaetsdaten-Abruf fuer %s fehlgeschlagen (degradiert auf None): %s", yfinance_symbol, exc)
        return None
