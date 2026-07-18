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
from datetime import datetime, timezone

import yfinance as yf

import database.db as db
from api.kraken_history import OhlcUpdateResult
from api.yfinance_client import run_with_daemon_timeout
from database.api_health import track_api_health
from database.models import OhlcPoint

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


def get_full_ohlc_history(ticker: str, symbol: str, currency: str = "USD") -> list[OhlcPoint]:
    """Echte OHLC-Historie (statt nur Schlusskurs) fuer die Non-Krypto-Agent-Pipeline
    Phase 1 (2026-07-15, agent/aktien/pipeline.py) - liest Open/High/Low/Close/Volume
    aus DERSELBEN `.history()`-Antwort, die _fetch_history() bereits holt (kein
    zusaetzlicher Netzwerk-Call). `price_history_ohlc` ist bereits nach `symbol`
    (nicht `coingecko_id`) geschluesselt - strukturell schon assetklassen-neutral,
    bisher nur von Kraken befuellt. `symbol`/`currency` sind unser internes Symbol
    bzw. die Handelswaehrung (nicht zwingend identisch mit `ticker`, dem
    yfinance-Symbol) - analog zu api/kraken.py's Trennung von Pair-Symbol und
    internem Symbol.

    Wirft bei einem haengenden Aufruf `concurrent.futures.TimeoutError`, sonst die
    zugrundeliegende yfinance-Exception durch (P-10), analog zu get_full_price_history()."""
    return run_with_daemon_timeout(
        lambda: _fetch_ohlc_history(ticker, symbol, currency), _YFINANCE_HISTORY_TIMEOUT_SECONDS
    )


@track_api_health("yfinance")
def _fetch_ohlc_history(ticker: str, symbol: str, currency: str) -> list[OhlcPoint]:
    hist = yf.Ticker(ticker).history(period="max", interval="1d")
    hist = hist[hist["Close"].notna()]
    fetched_at = datetime.now(timezone.utc).isoformat()
    return [
        OhlcPoint(
            symbol=symbol,
            currency=currency,
            date=ts.date().isoformat(),
            open=float(row["Open"]),
            high=float(row["High"]),
            low=float(row["Low"]),
            close=float(row["Close"]),
            volume=float(row["Volume"]),
            fetched_at=fetched_at,
        )
        for ts, row in hist.iterrows()
    ]


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


def backfill_all_aktien_ohlc(conn, watchlist) -> list[OhlcUpdateResult]:
    """Automatischer OHLC-Refresh fuer Einzelaktien (2026-07-16, schliesst eine im
    Asset-Verwaltungs-Audit gefundene Luecke: die Aktien-Pipeline Phase 1
    aktualisierte `price_history_ohlc` bisher NUR bei manuellem Signal-Klick
    (agent/aktien/pipeline.py::_ensure_ohlc_backfilled(), 5-Tage-Staleness-Schwelle) -
    der taegliche Backward-Tracking-Job (06:00) haette ein offenes Aktien-Signal
    sonst zunehmend gegen veraltete Kursdaten geprueft, ohne dass das auffiel.
    Analog zu api/kraken_history.py::backfill_all_ohlc(), aber fuer
    assetklasse=='aktien' via yfinance - IMMER volle Neuabfrage (kein inkrementelles
    `since`, anders als Kraken), da get_full_ohlc_history() ohnehin die komplette
    Historie in einem Call liefert (siehe dortigen Docstring)."""
    results: list[OhlcUpdateResult] = []
    for asset in watchlist:
        if asset.assetklasse != "aktien":
            continue
        try:
            ohlc_points = get_full_ohlc_history(asset.yfinance_symbol, asset.symbol, "USD")
        except Exception as exc:
            results.append(OhlcUpdateResult(asset.symbol, 0, degraded=True, reason=str(exc)))
            continue
        if not ohlc_points:
            results.append(OhlcUpdateResult(asset.symbol, 0, degraded=True, reason="Keine OHLC-Punkte erhalten"))
            continue
        db.upsert_ohlc_points(conn, ohlc_points)
        results.append(OhlcUpdateResult(asset.symbol, len(ohlc_points)))
    return results


@dataclass
class VixReading:
    """CBOE Volatility Index (^VIX) - impliziter Optionsmarkt-Volatilitaets-
    Fruehindikator (2026-07-18). Im Gegensatz zu EquitiesBearMarketReading (reiner
    Kurs-Drawdown, NACHLAUFEND) ist VIX ein VORLAUFENDES Stimmungssignal, kann schon
    ausschlagen, bevor/ohne dass ein echter Drawdown eintritt. Nur der Rohwert, keine
    Label-Einordnung (die haengt von Schwellenwerten ab, siehe agent/krypto/regime.py::
    _vix_label(), analog equities_baermarkt-Split zwischen Rohwert und Schwellenwert-
    Entscheidung)."""
    date: str
    wert: float


def get_vix_reading() -> VixReading:
    """Nutzt denselben Timeout-geschuetzten get_full_price_history() wie
    get_equities_bear_market_status() (P-10: wirft bei Fehlschlag durch, Aufrufer
    degradiert einzeln - siehe agent/krypto/pipeline.py::_fetch_boden_zielzone_context(),
    eigener try/except UNABHAENGIG vom Aktien-Baermarkt-Abruf, damit ein VIX-
    Ausfall nicht auch den Drawdown-Fakt mit reisst und umgekehrt)."""
    history = get_full_price_history("^VIX")
    if not history:
        raise ValueError("Keine VIX-Historie erhalten (^VIX)")
    date, wert = history[-1]
    return VixReading(date=date.date().isoformat(), wert=wert)


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
