"""R-5.1 Marktregime-Bestimmung (Spezifikation Kap. 5/14) - NUR die regelbasierte
Basis (RG-1a). KI-Override (RG-1b) ist bewusst nicht Teil dieser Slice. Manueller
Override (RG-8) wird respektiert (RG-9: Vorrang vor der regelbasierten Basis), harte
Limits (RG-6, Stop-Loss/Risiko-pro-Trade/Drawdown-Notbremse) sind davon unberuehrt -
die werden ausschliesslich in agent/risk_gate.py durchgesetzt, nie hier.

Bewusst einfache Heuristik (dokumentiert, nicht die volle RG-1..RG-11-Feinheit):
EMA-Ordnung fuer den BTC-Trend, BTC-Dominanz-Trend aus macro_snapshot-Historie,
Fear&Greed-Einstufung direkt von alternative.me uebernommen (keine eigene
Schwellenwert-Erfindung)."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from database.models import MacroSnapshot
from indicators.calculations import TechnicalSnapshot, latest_value

REGIME_STATES = ("krise_extrem", "baer", "seitwaerts", "bulle", "euphorie_extrem")


@dataclass
class RegimeResult:
    regime: str
    source: str  # "regelbasiert" | "manuell"
    reason: str
    btc_trend_label: str
    dominance_trend_label: str
    fear_greed_value: int | None
    fear_greed_label: str | None


def _btc_change_pct(btc_closes: np.ndarray, days: int = 30) -> float | None:
    if len(btc_closes) < days + 1:
        return None
    return float((btc_closes[-1] - btc_closes[-days - 1]) / btc_closes[-days - 1] * 100)


def _dominance_trend(macro_history: list[MacroSnapshot]) -> str:
    with_dominance = [m for m in macro_history if m.btc_dominance_pct is not None]
    if len(with_dominance) < 2:
        return "nicht verfügbar (nur 1 Messpunkt)"
    delta = with_dominance[-1].btc_dominance_pct - with_dominance[0].btc_dominance_pct
    if delta > 0.5:
        return f"steigend ({delta:+.2f} Prozentpunkte seit {with_dominance[0].date})"
    if delta < -0.5:
        return f"fallend ({delta:+.2f} Prozentpunkte seit {with_dominance[0].date})"
    return f"gleichbleibend ({delta:+.2f} Prozentpunkte seit {with_dominance[0].date})"


def determine_regime(
    btc_closes: np.ndarray,
    btc_snapshot: TechnicalSnapshot,
    macro_history: list[MacroSnapshot],
    manual_override: str,
) -> RegimeResult:
    ema20 = latest_value(btc_snapshot.ema[20])
    ema50 = latest_value(btc_snapshot.ema[50])
    ema200 = latest_value(btc_snapshot.ema[200])
    change_30d = _btc_change_pct(btc_closes)

    if ema20 is not None and ema50 is not None and ema200 is not None:
        if ema20 > ema50 > ema200:
            btc_trend_label = "aufwärts (EMA20 > EMA50 > EMA200)"
        elif ema20 < ema50 < ema200:
            btc_trend_label = "abwärts (EMA20 < EMA50 < EMA200)"
        else:
            btc_trend_label = "gemischt"
    else:
        btc_trend_label = "nicht verfügbar (zu wenig Historie)"

    dominance_trend_label = _dominance_trend(macro_history)

    latest_macro = macro_history[-1] if macro_history else None
    fgi_value = latest_macro.fear_greed_value if latest_macro else None
    fgi_label = latest_macro.fear_greed_label if latest_macro else None

    below_ema200 = bool(len(btc_closes)) and ema200 is not None and btc_closes[-1] < ema200
    above_all = ema20 is not None and ema50 is not None and ema200 is not None and ema20 > ema50 > ema200

    if fgi_label == "Extreme Fear" and below_ema200 and change_30d is not None and change_30d < -20:
        regime = "krise_extrem"
        reason = "Extreme Fear + BTC unter EMA200 + 30-Tage-Rückgang > 20%"
    elif fgi_label == "Extreme Greed" and above_all and change_30d is not None and change_30d > 20:
        regime = "euphorie_extrem"
        reason = "Extreme Greed + BTC über EMA20>EMA50>EMA200 + 30-Tage-Anstieg > 20%"
    elif (ema50 is not None and ema200 is not None and btc_closes[-1] < ema50) or fgi_label in (
        "Fear", "Extreme Fear",
    ):
        regime = "baer"
        reason = "BTC unter EMA50 und/oder Fear&Greed im Angst-Bereich"
    elif (
        ema50 is not None and ema200 is not None and btc_closes[-1] > ema50 > ema200
    ) and fgi_label in ("Greed", "Extreme Greed"):
        regime = "bulle"
        reason = "BTC über EMA50>EMA200 und Fear&Greed im Gier-Bereich"
    else:
        regime = "seitwaerts"
        reason = "keine der Bär-/Bulle-/Extrem-Bedingungen eindeutig erfüllt (Fallback)"

    if manual_override and manual_override != "none":
        return RegimeResult(
            regime=manual_override,
            source="manuell",
            reason=f"Manueller Override ({manual_override}) - regelbasiert wäre '{regime}' gewesen: {reason}",
            btc_trend_label=btc_trend_label,
            dominance_trend_label=dominance_trend_label,
            fear_greed_value=fgi_value,
            fear_greed_label=fgi_label,
        )

    return RegimeResult(
        regime=regime,
        source="regelbasiert",
        reason=reason,
        btc_trend_label=btc_trend_label,
        dominance_trend_label=dominance_trend_label,
        fear_greed_value=fgi_value,
        fear_greed_label=fgi_label,
    )
