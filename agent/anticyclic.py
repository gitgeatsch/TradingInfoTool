"""R-5.11 Antizyklische Disziplin (Spezifikation Kap. 15) - NUR eine einfache,
explizit als Heuristik gekennzeichnete Naeherung, NICHT die volle AZ-1..AZ-8-
Klassifikation (Flush vs. fundamentaler Zusammenbruch braucht Nachrichten-/
Fundamentaldaten, die dieses System nicht hat). Liefert reinen Kontext an Groq
(agent/analyst.py) - trifft selbst keine Veto-Entscheidung, das bleibt
agent/risk_gate.py vorbehalten.

Schwellenwerte sind bewusste Platzhalter (wie config.yaml an mehreren Stellen
"[OFFEN]"/vorlaeufig kennzeichnet), keine recherchierten Werte."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from api.kraken import KRAKEN_FUTURES_SYMBOL_MAP

FUNDING_RATE_EXTREME_THRESHOLD = 0.0001  # Platzhalter, |mittlerer stdl. rel. Funding-Rate|
DROP_LOOKBACK_DAYS = 3


@dataclass
class AnticyclicContext:
    funding_rate_current: float | None
    funding_rate_extreme: bool
    recent_drop_pct: float | None
    possible_flush: bool
    confirmation_gate_passed: bool | None
    reason: str


def assess(asset, kraken_client, price_history_closes: np.ndarray) -> AnticyclicContext:
    futures_symbol = KRAKEN_FUTURES_SYMBOL_MAP.get(asset.symbol)
    if futures_symbol is None:
        return AnticyclicContext(
            funding_rate_current=None,
            funding_rate_extreme=False,
            recent_drop_pct=None,
            possible_flush=False,
            confirmation_gate_passed=None,
            reason="keine Kraken-Futures-Notierung — Heuristik übersprungen",
        )

    try:
        rates = kraken_client.get_funding_rates(futures_symbol)
    except Exception as exc:
        return AnticyclicContext(
            funding_rate_current=None,
            funding_rate_extreme=False,
            recent_drop_pct=None,
            possible_flush=False,
            confirmation_gate_passed=None,
            reason=f"Funding-Rate-Abruf fehlgeschlagen: {exc}",
        )

    recent = rates[-24:] if len(rates) >= 24 else rates
    funding_rate_current = (
        float(np.mean([r["relative_funding_rate"] for r in recent])) if recent else None
    )
    funding_rate_extreme = (
        funding_rate_current is not None and abs(funding_rate_current) > FUNDING_RATE_EXTREME_THRESHOLD
    )

    recent_drop_pct = None
    if len(price_history_closes) >= DROP_LOOKBACK_DAYS + 1:
        base = price_history_closes[-DROP_LOOKBACK_DAYS - 1]
        recent_drop_pct = float((price_history_closes[-1] - base) / base * 100)

    possible_flush = funding_rate_extreme and recent_drop_pct is not None and recent_drop_pct < -10

    confirmation_gate_passed = None
    if len(price_history_closes) >= DROP_LOOKBACK_DAYS + 1:
        no_new_low = price_history_closes[-1] >= price_history_closes[-DROP_LOOKBACK_DAYS:].min()
        confirmation_gate_passed = bool(no_new_low)

    reason = (
        f"Funding-Rate (Ø letzte {len(recent)}h): {funding_rate_current}, "
        f"{DROP_LOOKBACK_DAYS}-Tage-Kursänderung: {recent_drop_pct}. "
        "Keine unabhängige Nachrichten-/Fundamentalquelle vorhanden — "
        "'moeglicher_flush' ist ein grober Hinweis, keine gesicherte Klassifikation."
    )

    return AnticyclicContext(
        funding_rate_current=funding_rate_current,
        funding_rate_extreme=funding_rate_extreme,
        recent_drop_pct=recent_drop_pct,
        possible_flush=possible_flush,
        confirmation_gate_passed=confirmation_gate_passed,
        reason=reason,
    )
