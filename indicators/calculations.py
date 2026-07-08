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


def atr_wilder(
    highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int = 14
) -> IndicatorResult:
    """Echtes Wilder's ATR auf Basis von Kraken-OHLC-Daten (High/Low verfuegbar,
    siehe Basisinfos/Spezifikation.md Kap. 8). Nur fuer die 35/41 Assets nutzbar, die
    ein Kraken-Spot-Paar haben - fuer den Rest bleibt atr_close_to_close_proxy die
    einzige Quelle. True Range = max(H-L, |H-Cprev|, |L-Cprev|); erster ATR-Wert =
    einfacher Mittelwert der ersten `period` True Ranges, danach Wilder-Glaettung
    (wie bei RSI: (vorheriger*(period-1) + aktueller) / period)."""
    if len(closes) < period + 1:
        reason = f"benötigt {period + 1} Tage, nur {len(closes)} vorhanden"
        _log_unavailable("ATR", reason)
        return IndicatorResult(None, False, reason)

    prev_closes = closes[:-1]
    true_ranges = np.maximum(
        highs[1:] - lows[1:],
        np.maximum(np.abs(highs[1:] - prev_closes), np.abs(lows[1:] - prev_closes)),
    )

    n = len(closes)
    values = np.full(n, np.nan)
    values[period] = true_ranges[:period].mean()
    for i in range(period, len(true_ranges)):
        values[i + 1] = (values[i] * (period - 1) + true_ranges[i]) / period
    return IndicatorResult(values, True)


def swing_highs_lows_fractal(
    highs: np.ndarray, lows: np.ndarray, dates: np.ndarray, window: int = 2
) -> IndicatorResult:
    """Echtes Williams-Fraktal auf Basis von Kraken-OHLC-Daten (High/Low verfuegbar).
    Standard-Fenster window=2 (5-Kerzen-Muster). Swing-High: high[i] ist das Maximum
    unter den `window` Kerzen davor UND danach. Swing-Low analog fuer Minimum. Gleiche
    Rueckgabeform wie swing_highs_lows_close_proxy ({"highs": [...], "lows": [...]}),
    damit UI-Code beide Quellen gleich weiterverarbeiten kann."""
    min_required = window * 2 + 1
    if len(highs) < min_required:
        reason = f"benötigt mind. {min_required} Tage, nur {len(highs)} vorhanden"
        _log_unavailable("Swing-Punkte (Williams-Fraktal)", reason)
        return IndicatorResult(None, False, reason)

    swing_highs, swing_lows = [], []
    for i in range(window, len(highs) - window):
        high_window = highs[i - window : i + window + 1]
        low_window = lows[i - window : i + window + 1]
        if highs[i] == high_window.max():
            swing_highs.append((dates[i], highs[i]))
        if lows[i] == low_window.min():
            swing_lows.append((dates[i], lows[i]))
    return IndicatorResult({"highs": swing_highs, "lows": swing_lows}, True)


def _last_valid(arr: np.ndarray) -> float | None:
    valid = arr[~np.isnan(arr)]
    if len(valid) == 0:
        return None
    return float(valid[-1])


def latest_value(result: IndicatorResult) -> float | int | None:
    """Letzter nicht-NaN-Wert eines IndicatorResult, als natives float/int (kein
    numpy-Skalar) - gebraucht ueberall dort, wo ein einzelner aktueller Wert statt der
    ganzen Zeitreihe noetig ist (Chart-Label, Agent-Facts-Objekt)."""
    if not result.available or result.value is None:
        return None
    return _last_valid(np.asarray(result.value, dtype=float))


@dataclass
class TechnicalSnapshot:
    """Buendelt alle Chart-/Agent-Indikatoren fuer eine Preisreihe, inkl. der
    "echte Kraken-OHLC-Daten bevorzugen, sonst Naeherung"-Weiche (siehe
    atr_wilder/atr_close_to_close_proxy, swing_highs_lows_fractal/_close_proxy).
    Geteilte Quelle fuer ui/charts.py UND agent/pipeline.py - vermeidet Drift zwischen
    Chart-Anzeige und Agent-Fakten."""
    has_real_ohlc: bool
    ema: dict[int, IndicatorResult]
    macd: IndicatorResult
    rsi: IndicatorResult
    bollinger: IndicatorResult
    swing: IndicatorResult
    swing_label: str
    swing_source: str  # "real" | "proxy"
    support_resistance: IndicatorResult
    fibonacci: dict[float, float] | None
    atr: IndicatorResult
    atr_label: str
    atr_source: str  # "real" | "proxy"


def build_technical_snapshot(
    closes: np.ndarray,
    dates: np.ndarray,
    ohlc_history: list,
    ema_periods: tuple[int, ...] = (20, 50, 200),
) -> TechnicalSnapshot:
    has_real_ohlc = len(ohlc_history) >= 3

    if has_real_ohlc:
        ohlc_dates = np.array([p.date for p in ohlc_history])
        ohlc_highs = np.array([p.high for p in ohlc_history], dtype=float)
        ohlc_lows = np.array([p.low for p in ohlc_history], dtype=float)
        ohlc_closes = np.array([p.close for p in ohlc_history], dtype=float)

        swing = swing_highs_lows_fractal(ohlc_highs, ohlc_lows, ohlc_dates)
        swing_label = "Swing-Punkte (echt, Williams-Fraktal/Kraken)"
        swing_source = "real"

        atr_result = atr_wilder(ohlc_highs, ohlc_lows, ohlc_closes)
        atr_label = "ATR-14 (echt, Kraken)"
        atr_source = "real"
    else:
        swing = swing_highs_lows_close_proxy(closes, dates)
        swing_label = "Swing-Punkte (Näherung, Schlusskurs-basiert)"
        swing_source = "proxy"

        atr_result = atr_close_to_close_proxy(closes)
        atr_label = "Volatilitäts-Näherung (kein ATR)"
        atr_source = "proxy"

    ema_results = {period: ema(closes, period) for period in ema_periods}

    fibonacci = None
    if swing.available:
        all_highs = [p for _, p in swing.value["highs"]]
        all_lows = [p for _, p in swing.value["lows"]]
        if all_highs and all_lows:
            fibonacci = fibonacci_levels(max(all_highs), min(all_lows))

    return TechnicalSnapshot(
        has_real_ohlc=has_real_ohlc,
        ema=ema_results,
        macd=macd(closes),
        rsi=rsi(closes),
        bollinger=bollinger_bands(closes),
        swing=swing,
        swing_label=swing_label,
        swing_source=swing_source,
        support_resistance=support_resistance_levels(swing),
        fibonacci=fibonacci,
        atr=atr_result,
        atr_label=atr_label,
        atr_source=atr_source,
    )


@dataclass
class ConfluenceItem:
    indicator: str
    available: bool
    bias: str | None = None  # "bullish" | "bearish" | "neutral"
    detail: str | None = None


@dataclass
class ConfluenceSummary:
    """Einfache, bewusst als Heuristik gekennzeichnete Zusammenfassung, WELCHE
    Indikatoren bullish/bearish/neutral stehen (Kap. 7: confluence_pflicht - kein
    Signal aus einem einzelnen Indikator). Entscheidet NICHTS selbst - liefert nur
    deskriptive Fakten, die Signal-Synthese (KAUFEN/VERKAUFEN/HALTEN) passiert in
    agent/analyst.py durch Groq, nicht hier."""
    items: list[ConfluenceItem]
    bullish_count: int
    bearish_count: int
    neutral_count: int
    unavailable_count: int
    overall_bias: str  # "bullish" | "bearish" | "neutral" | "gemischt"


def summarize_confluence(snapshot: TechnicalSnapshot, latest_close: float) -> ConfluenceSummary:
    items: list[ConfluenceItem] = []

    ema20, ema50, ema200 = (latest_value(snapshot.ema[p]) for p in (20, 50, 200))
    if ema20 is not None and ema50 is not None and ema200 is not None:
        if latest_close > ema20 > ema50 > ema200:
            items.append(ConfluenceItem("EMA-Ordnung", True, "bullish", "Preis > EMA20 > EMA50 > EMA200"))
        elif latest_close < ema20 < ema50 < ema200:
            items.append(ConfluenceItem("EMA-Ordnung", True, "bearish", "Preis < EMA20 < EMA50 < EMA200"))
        else:
            items.append(ConfluenceItem("EMA-Ordnung", True, "neutral", "gemischte EMA-Reihenfolge"))
    else:
        missing = [p for p in (20, 50, 200) if not snapshot.ema[p].available]
        detail = "; ".join(f"EMA-{p}: {snapshot.ema[p].reason}" for p in missing)
        items.append(ConfluenceItem("EMA-Ordnung", False, detail=detail))

    if snapshot.macd.available:
        macd_val = _last_valid(snapshot.macd.value["macd"])
        signal_val = _last_valid(snapshot.macd.value["signal"])
        hist_val = _last_valid(snapshot.macd.value["histogram"])
        if macd_val is not None and signal_val is not None and hist_val is not None:
            if macd_val > signal_val and hist_val > 0:
                items.append(ConfluenceItem("MACD", True, "bullish", f"MACD {macd_val:.4g} > Signal {signal_val:.4g}"))
            elif macd_val < signal_val and hist_val < 0:
                items.append(ConfluenceItem("MACD", True, "bearish", f"MACD {macd_val:.4g} < Signal {signal_val:.4g}"))
            else:
                items.append(ConfluenceItem("MACD", True, "neutral"))
        else:
            items.append(ConfluenceItem("MACD", False))
    else:
        items.append(ConfluenceItem("MACD", False, detail=snapshot.macd.reason))

    if snapshot.rsi.available:
        rsi_val = latest_value(snapshot.rsi)
        if rsi_val is not None:
            if rsi_val > 70:
                items.append(ConfluenceItem("RSI-14", True, "neutral", f"{rsi_val:.1f} überkauft"))
            elif rsi_val > 60:
                items.append(ConfluenceItem("RSI-14", True, "bullish", f"{rsi_val:.1f}"))
            elif rsi_val < 30:
                items.append(ConfluenceItem("RSI-14", True, "neutral", f"{rsi_val:.1f} überverkauft"))
            elif rsi_val < 40:
                items.append(ConfluenceItem("RSI-14", True, "bearish", f"{rsi_val:.1f}"))
            else:
                items.append(ConfluenceItem("RSI-14", True, "neutral", f"{rsi_val:.1f}"))
        else:
            items.append(ConfluenceItem("RSI-14", False))
    else:
        items.append(ConfluenceItem("RSI-14", False, detail=snapshot.rsi.reason))

    if snapshot.bollinger.available:
        upper = _last_valid(snapshot.bollinger.value["upper"])
        lower = _last_valid(snapshot.bollinger.value["lower"])
        if upper is not None and lower is not None:
            if latest_close >= upper:
                items.append(ConfluenceItem("Bollinger", True, "bullish", "am/über oberem Band (überdehnt)"))
            elif latest_close <= lower:
                items.append(ConfluenceItem("Bollinger", True, "bearish", "am/unter unterem Band (überdehnt)"))
            else:
                items.append(ConfluenceItem("Bollinger", True, "neutral"))
        else:
            items.append(ConfluenceItem("Bollinger", False))
    else:
        items.append(ConfluenceItem("Bollinger", False, detail=snapshot.bollinger.reason))

    bullish = sum(1 for i in items if i.bias == "bullish")
    bearish = sum(1 for i in items if i.bias == "bearish")
    neutral = sum(1 for i in items if i.available and i.bias == "neutral")
    unavailable = sum(1 for i in items if not i.available)

    if bullish > bearish and bullish > neutral:
        overall = "bullish"
    elif bearish > bullish and bearish > neutral:
        overall = "bearish"
    elif bullish == 0 and bearish == 0:
        overall = "neutral"
    else:
        overall = "gemischt"

    return ConfluenceSummary(items, bullish, bearish, neutral, unavailable, overall)


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


BTC_GENESIS_DATE = np.datetime64("2009-01-03")


@dataclass
class BtcLogRegressionRisk:
    """Bewusst EIGENES, einfaches Modell - KEINE Nachbildung der proprietaeren
    "Bitcoin Risk"-Formel von Into The Cryptoverse (Benjamin Cowen) oder aehnlicher
    kommerzieller Anbieter, deren exakte Methodik nicht oeffentlich ist. Einfache,
    transparente Log-Log-lineare Regression ueber die gesamte verfuegbare Historie
    plus Residuen-Streuung als Band - an vier bekannten historischen Zyklus-Extremen
    (2017/2018/2021/2022) live gegengeprueft, zeigt die richtige Richtung, aber ist
    keine praezise Nachbildung etablierter kommerzieller Modelle."""
    date: str
    current_price: float
    predicted_price: float  # Wert der Regressionslinie zum aktuellen Datum
    deviation_std: float  # Abweichung des aktuellen Preises von der Linie, in Std.
    risk: float  # 0-1, siehe deviation_std_range Parameter fuer die Skalierung


def compute_btc_log_regression_risk(
    history: list[tuple[Any, float]], deviation_std_range: float = 3.0
) -> BtcLogRegressionRisk:
    """`history`: Liste von (Datum, Preis) ueber moeglichst die gesamte BTC-Historie
    (siehe api/onchain.py::get_btc_full_price_history()). Preise <= 0 (2009,
    kein etablierter Markt) werden herausgefiltert, log(0) ist undefiniert.

    Modell: lineare Regression von log10(Preis) auf log10(Tage seit Genesis-Block)
    ueber die GESAMTE Historie. `risk` bildet die aktuelle Abweichung von dieser
    Linie (in Streuungs-Einheiten der historischen Residuen) linear auf [0, 1] ab,
    wobei +-`deviation_std_range` Standardabweichungen auf die vollen Baender
    (0 bzw. 1) gemappt werden - Werte ausserhalb werden auf 0/1 begrenzt (clamped).

    Wirft ValueError bei zu wenig verwertbaren Datenpunkten statt einen unsicheren
    Wert zurueckzugeben (P-10)."""
    # np.datetime64 kennt keine Zeitzonen - tzinfo vorher entfernen (Daten sind ohnehin
    # UTC, siehe api/onchain.py::get_btc_full_price_history()), sonst UserWarning.
    dates = np.array([np.datetime64(d.replace(tzinfo=None)) for d, _ in history])
    prices = np.array([p for _, p in history], dtype=float)
    valid = prices > 0
    dates, prices = dates[valid], prices[valid]

    if len(prices) < 30:
        raise ValueError(f"Zu wenige verwertbare BTC-Historiendaten fuer eine Regression: {len(prices)}")

    days_since_genesis = (dates - BTC_GENESIS_DATE).astype("timedelta64[D]").astype(float)
    x = np.log10(days_since_genesis)
    y = np.log10(prices)
    slope, intercept = np.polyfit(x, y, 1)
    residuals = y - (slope * x + intercept)
    std = residuals.std()

    current_price = float(prices[-1])
    deviation = float(residuals[-1] / std) if std > 0 else 0.0
    predicted_price = float(10 ** (slope * x[-1] + intercept))
    risk = float(np.clip((deviation + deviation_std_range) / (2 * deviation_std_range), 0.0, 1.0))

    return BtcLogRegressionRisk(
        date=str(dates[-1]),
        current_price=current_price,
        predicted_price=predicted_price,
        deviation_std=deviation,
        risk=risk,
    )
