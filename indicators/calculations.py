"""Technische Indikatoren (Spezifikation Kap. 7) - reine Berechnung auf numpy-Arrays,
kein I/O.

P-10 (Fail-Loud statt Fail-Silent): jede Funktion prueft die benoetigte Mindest-
Historie ZUERST und gibt bei unzureichenden Daten IndicatorResult(available=False,
reason=...) zurueck - niemals ein verkuerztes/falsches Fenster berechnen.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class IndicatorResult:
    value: Any
    available: bool
    reason: str | None = None


def _log_unavailable(indicator_name: str, reason: str) -> None:
    logger.info("Indikator %s nicht verfügbar: %s", indicator_name, reason)


def ema(closes: np.ndarray, period: int) -> IndicatorResult:
    if len(closes) < period:
        reason = f"benötigt {period} Tage, nur {len(closes)} vorhanden"
        _log_unavailable(f"EMA-{period}", reason)
        return IndicatorResult(None, False, reason)
    alpha = 2 / (period + 1)
    values = np.full(len(closes), np.nan)
    values[period - 1] = closes[:period].mean()
    for i in range(period, len(closes)):
        values[i] = closes[i] * alpha + values[i - 1] * (1 - alpha)
    return IndicatorResult(values, True)


def macd(closes: np.ndarray, fast: int = 12, slow: int = 26, signal: int = 9) -> IndicatorResult:
    min_required = slow + signal
    if len(closes) < min_required:
        reason = f"benötigt {min_required} Tage, nur {len(closes)} vorhanden"
        _log_unavailable("MACD", reason)
        return IndicatorResult(None, False, reason)

    ema_fast = ema(closes, fast).value
    ema_slow = ema(closes, slow).value
    macd_line = ema_fast - ema_slow

    valid_start = slow - 1
    macd_valid = macd_line[valid_start:]
    signal_result = ema(macd_valid, signal)
    if not signal_result.available:
        reason = f"benötigt {min_required} Tage, nur {len(closes)} vorhanden"
        _log_unavailable("MACD", reason)
        return IndicatorResult(None, False, reason)

    signal_line = np.full(len(closes), np.nan)
    signal_line[valid_start:] = signal_result.value
    histogram = macd_line - signal_line
    return IndicatorResult(
        {"macd": macd_line, "signal": signal_line, "histogram": histogram}, True
    )


def _rsi_from_avgs(avg_gain: float, avg_loss: float) -> float:
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100 - 100 / (1 + rs)


def rsi(closes: np.ndarray, period: int = 14) -> IndicatorResult:
    if len(closes) < period + 1:
        reason = f"benötigt {period + 1} Tage, nur {len(closes)} vorhanden"
        _log_unavailable(f"RSI-{period}", reason)
        return IndicatorResult(None, False, reason)

    deltas = np.diff(closes)
    gains = np.where(deltas > 0, deltas, 0.0)
    losses = np.where(deltas < 0, -deltas, 0.0)

    avg_gain = gains[:period].mean()
    avg_loss = losses[:period].mean()

    values = np.full(len(closes), np.nan)
    values[period] = _rsi_from_avgs(avg_gain, avg_loss)
    for i in range(period, len(deltas)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        values[i + 1] = _rsi_from_avgs(avg_gain, avg_loss)
    return IndicatorResult(values, True)


def bollinger_bands(closes: np.ndarray, period: int = 20, num_std: float = 2.0) -> IndicatorResult:
    if len(closes) < period:
        reason = f"benötigt {period} Tage, nur {len(closes)} vorhanden"
        _log_unavailable("Bollinger Bands", reason)
        return IndicatorResult(None, False, reason)

    n = len(closes)
    middle = np.full(n, np.nan)
    upper = np.full(n, np.nan)
    lower = np.full(n, np.nan)
    for i in range(period - 1, n):
        window = closes[i - period + 1 : i + 1]
        sma = window.mean()
        std = window.std(ddof=0)
        middle[i] = sma
        upper[i] = sma + num_std * std
        lower[i] = sma - num_std * std
    return IndicatorResult({"middle": middle, "upper": upper, "lower": lower}, True)


FIBONACCI_RATIOS = [0.0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0]


def fibonacci_levels(swing_high: float, swing_low: float) -> dict[float, float]:
    diff = swing_high - swing_low
    return {ratio: swing_high - diff * ratio for ratio in FIBONACCI_RATIOS}


def atr_close_to_close_proxy(closes: np.ndarray, period: int = 14) -> IndicatorResult:
    """Näherung für Volatilität, NICHT das echte Wilder's ATR (das braucht High/Low,
    welches CoinGecko Free-Tier nicht in Tages-Auflösung liefert, siehe Spezifikation
    Kap. 8). Verwendet die mittlere absolute Tagesveränderung (Close-zu-Close) als
    Volatilitätsmaß. Muss in der UI IMMER als 'Volatilitäts-Näherung (kein ATR)'
    beschriftet werden - niemals kommentarlos als 'ATR' anzeigen (P-2/P-10)."""
    if len(closes) < period + 1:
        reason = f"benötigt {period + 1} Tage, nur {len(closes)} vorhanden"
        _log_unavailable("Volatilitäts-Näherung", reason)
        return IndicatorResult(None, False, reason)

    abs_changes = np.abs(np.diff(closes))
    n = len(abs_changes)
    values = np.full(len(closes), np.nan)
    for i in range(period - 1, n):
        values[i + 1] = abs_changes[i - period + 1 : i + 1].mean()
    return IndicatorResult(values, True)


def swing_highs_lows_close_proxy(
    closes: np.ndarray, dates: np.ndarray, window: int = 5
) -> IndicatorResult:
    """Näherung für Swing-Highs/-Lows über lokale Extrema der Schlusskurse (kein
    echtes Williams-Fraktal, das intrabar High/Low braucht). window = Anzahl Tage
    links/rechts für ein lokales Extremum. In der UI als 'Swing-Punkte (Näherung,
    Schlusskurs-basiert)' kennzeichnen."""
    min_required = window * 2 + 1
    if len(closes) < min_required:
        reason = f"benötigt mind. {min_required} Tage, nur {len(closes)} vorhanden"
        _log_unavailable("Swing-Punkte-Näherung", reason)
        return IndicatorResult(None, False, reason)

    highs, lows = [], []
    for i in range(window, len(closes) - window):
        local = closes[i - window : i + window + 1]
        if closes[i] == local.max():
            highs.append((dates[i], closes[i]))
        elif closes[i] == local.min():
            lows.append((dates[i], closes[i]))
    return IndicatorResult({"highs": highs, "lows": lows}, True)


def support_resistance_levels(
    swing_result: IndicatorResult, tolerance_pct: float = 0.02
) -> IndicatorResult:
    """Clustert die (approximierten) Swing-Punkte zu Support-/Resistance-Zonen.
    Erbt die Näherungs-Einschränkung der zugrundeliegenden Swing-Erkennung."""
    if not swing_result.available:
        return IndicatorResult(None, False, swing_result.reason)

    all_points = [p for _, p in swing_result.value["highs"]] + [
        p for _, p in swing_result.value["lows"]
    ]
    if not all_points:
        return IndicatorResult([], True)

    sorted_points = sorted(all_points)
    clusters: list[list[float]] = []
    for price in sorted_points:
        if clusters and abs(price - clusters[-1][-1]) / clusters[-1][-1] <= tolerance_pct:
            clusters[-1].append(price)
        else:
            clusters.append([price])

    levels = [
        {"price": float(np.mean(cluster)), "touches": len(cluster)} for cluster in clusters
    ]
    return IndicatorResult(levels, True)
