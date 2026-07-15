"""Historische Tages-Kurse ueber yfinance - Boden-Zielzone (AZ-4 Baustein 2, 2026-07-12).

Bewusst ein EIGENES Modul statt Erweiterung von api/yfinance_client.py: dessen
`Ticker.fast_info`-Ansatz ist gezielt auf duenn gehandelte Instrumente (WisdomTree-
ETNs etc.) zugeschnitten, bei denen `.history()` nachweislich fehlschlaegt (siehe
dessen Modul-Docstring). Die hier genutzten Ticker (ETH-USD, ^GSPC, ^IXIC) sind
liquide Standard-Instrumente, bei denen `.history()` zuverlaessig funktioniert und
lange Historie liefert - beide Anwendungsfaelle unterscheiden sich genug, um sie
nicht in einer Klasse zu vermischen.

Datenquellen-Hintergrund (live geprueft 2026-07-12): fuer BTC existiert mit
blockchain.com eine kostenlose, unbegrenzte Vollhistorie (api/onchain.py::
get_btc_full_price_history()) - ein Aequivalent dafuer gibt es fuer ETH nicht:
CoinGecko-Free-Tier limitiert `/market_chart` seit 2025 auf 365 Tage (live 401
bekommen), Kraken liefert ueber die OHLC-API nur ein rollierendes ~720-Tage-Fenster
unabhaengig vom `since`-Parameter (live geprueft). yfinance `ETH-USD` liefert
taegliche Kurse seit 2017-11-09 (3168 Punkte, live geprueft) - die beste frei
verfuegbare Quelle, auch wenn kuerzer als BTCs Historie seit 2009."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime

import yfinance as yf

from api.yfinance_client import run_with_daemon_timeout
from database.api_health import track_api_health

logger = logging.getLogger(__name__)

# Gleiches Problem wie in api/yfinance_client.py: yfinance bietet keinen von uns
# kontrollierten Netzwerk-Timeout. .history()-Aufrufe koennen zusaetzlich laenger
# dauern als reine fast_info-Abrufe (mehr Datenvolumen) - Timeout deshalb grosszuegiger.
_YFINANCE_HISTORY_TIMEOUT_SECONDS = 30


def get_full_price_history(ticker: str) -> list[tuple[datetime, float]]:
    """Liefert (Datum, Schlusskurs) fuer die maximal verfuegbare Tages-Historie eines
    yfinance-Tickers (z.B. 'ETH-USD', '^GSPC', '^IXIC'). Zeilen ohne Schlusskurs
    (Feiertage/Datenluecken) werden herausgefiltert.

    Wirft bei einem haengenden Aufruf `concurrent.futures.TimeoutError` nach
    `_YFINANCE_HISTORY_TIMEOUT_SECONDS`, sonst die zugrundeliegende yfinance-Exception
    durch (P-10: kein stiller Fallback auf eine leere/falsche Historie) - Aufrufer
    muss beides behandeln, analog zu YFinanceClient.fetch_price_snapshots().

    Nutzt run_with_daemon_timeout() (api/yfinance_client.py) statt eines eigenen
    ThreadPoolExecutor - 2026-07-15-Bugfix, siehe dortigen Docstring (Notebook blieb
    beim Beenden/Neustarten haengen, da ThreadPoolExecutor-Worker nicht daemonisch
    sind und Pythons globaler atexit-Hook alle jemals erzeugten Executor-Threads
    joint, nicht nur die der aktuellen Instanz)."""
    return run_with_daemon_timeout(lambda: _fetch_history(ticker), _YFINANCE_HISTORY_TIMEOUT_SECONDS)


@track_api_health("yfinance")
def _fetch_history(ticker: str) -> list[tuple[datetime, float]]:
    hist = yf.Ticker(ticker).history(period="max", interval="1d")
    hist = hist[hist["Close"].notna()]
    return [(ts.to_pydatetime(), float(close)) for ts, close in hist["Close"].items()]


@dataclass
class EquitiesBearMarketReading:
    """Rohe Drawdown-Werte, OHNE eine "Baermarkt aktiv"-Entscheidung - die haengt von
    einem Schwellenwert aus config.yaml ab, der sich spaeter aendern kann. Wird
    bewusst am Aufrufort (agent/krypto/pipeline.py) verglichen, nicht hier, damit eine
    spaetere Schwellenwert-Aenderung nicht bereits gespeicherte historische Werte
    umdeutet (siehe database/models.py::MacroSnapshot, keine gespeicherte Bool-Spalte)."""
    date: str
    sp500_price: float
    sp500_ath: float
    sp500_drawdown_pct: float  # negativ = unter Allzeithoch
    nasdaq_price: float
    nasdaq_ath: float
    nasdaq_drawdown_pct: float


def _drawdown_from_ath(history: list[tuple[datetime, float]], lookback_years: float) -> tuple[str, float, float, float]:
    """Gibt (letztes_datum, letzter_preis, ath, drawdown_pct) fuer das auf
    `lookback_years` gekuerzte Fenster der (bereits vollstaendig abgerufenen)
    Historie zurueck."""
    cutoff = history[-1][0].replace(year=history[-1][0].year - int(lookback_years))
    windowed = [(d, p) for d, p in history if d >= cutoff] or history
    last_date, last_price = windowed[-1]
    ath = max(p for _, p in windowed)
    return last_date.date().isoformat(), last_price, ath, (last_price - ath) / ath * 100


def get_equities_bear_market_status(lookback_years: float = 5.0) -> EquitiesBearMarketReading:
    """S&P 500 (^GSPC) + Nasdaq Composite (^IXIC) - Drawdown vom Allzeithoch der
    letzten `lookback_years` Jahre. Boden-Zielzone-Overlay (AZ-4 Baustein 2): ein
    gemeinsamer Liquiditaetsentzug am Aktienmarkt kann BTC/ETH zusaetzlich unter die
    reine Krypto-Zyklus-Zielzone druecken (Nutzer-Punkt, 2026-07-12).

    Nutzt get_full_price_history() (mit Timeout-Schutz) statt eines eigenen
    unprotected yf.Ticker-Aufrufs - dieselbe Netzwerk-Haenger-Absicherung wie fuer
    ETH. Wirft bei einem Fetch-Fehlschlag die zugrundeliegende Exception durch
    (P-10) - Aufrufer (pipeline.py) faengt das ab und degradiert nur diesen einen
    Fakt auf None, statt die gesamte Regime-Berechnung zu blockieren."""
    sp500_history = get_full_price_history("^GSPC")
    nasdaq_history = get_full_price_history("^IXIC")

    date, sp500_price, sp500_ath, sp500_drawdown = _drawdown_from_ath(sp500_history, lookback_years)
    _, nasdaq_price, nasdaq_ath, nasdaq_drawdown = _drawdown_from_ath(nasdaq_history, lookback_years)

    return EquitiesBearMarketReading(
        date=date,
        sp500_price=sp500_price,
        sp500_ath=sp500_ath,
        sp500_drawdown_pct=sp500_drawdown,
        nasdaq_price=nasdaq_price,
        nasdaq_ath=nasdaq_ath,
        nasdaq_drawdown_pct=nasdaq_drawdown,
    )
