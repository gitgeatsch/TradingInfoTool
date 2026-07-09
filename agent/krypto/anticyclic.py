"""R-5.11 Antizyklische Disziplin (Spezifikation Kap. 15) - NUR eine einfache,
explizit als Heuristik gekennzeichnete Naeherung, NICHT die volle AZ-1..AZ-8-
Klassifikation (Flush vs. fundamentaler Zusammenbruch braucht Nachrichten-/
Fundamentaldaten, die dieses System nicht hat). Liefert reinen Kontext an Groq
(agent/analyst.py) - trifft selbst keine Veto-Entscheidung, das bleibt
agent/risk_gate.py vorbehalten.

Schwellenwerte sind bewusste Platzhalter (wie config.yaml an mehreren Stellen
"[OFFEN]"/vorlaeufig kennzeichnet), keine recherchierten Werte."""
from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np

from api.derivatives import get_binance_long_short_ratio, get_binance_open_interest, get_bybit_open_interest, get_okx_open_interest
from api.kraken import KRAKEN_FUTURES_SYMBOL_MAP

logger = logging.getLogger(__name__)

FUNDING_RATE_EXTREME_THRESHOLD = 0.0001  # Platzhalter, |mittlerer stdl. rel. Funding-Rate|
DROP_LOOKBACK_DAYS = 3
# Platzhalter (wie FUNDING_RATE_EXTREME_THRESHOLD), keine recherchierte Schwelle:
# > 65% Long-Konten gilt hier als "ueberwiegend long positioniert" - bei einem
# gleichzeitigen Kursrueckgang sind das potenziell die Positionen, die als naechstes
# liquidiert/geschlossen werden (siehe Nutzungs-Diskussion Schritt 3, 2026-07-08).
LONG_BIAS_EXTREME_THRESHOLD_PCT = 65.0


@dataclass
class AnticyclicContext:
    funding_rate_current: float | None
    funding_rate_extreme: bool
    recent_drop_pct: float | None
    possible_flush: bool
    confirmation_gate_passed: bool | None
    open_interest_binance: float | None
    open_interest_bybit: float | None
    open_interest_okx_usd: float | None
    long_short_ratio: float | None
    long_account_pct: float | None
    retail_long_bias_extreme: bool
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
            open_interest_binance=None,
            open_interest_bybit=None,
            open_interest_okx_usd=None,
            long_short_ratio=None,
            long_account_pct=None,
            retail_long_bias_extreme=False,
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
            open_interest_binance=None,
            open_interest_bybit=None,
            open_interest_okx_usd=None,
            long_short_ratio=None,
            long_account_pct=None,
            retail_long_bias_extreme=False,
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

    # OI/Long-Short-Ratio (api/derivatives.py, Nutzungs-Diskussion Schritt 3,
    # 2026-07-08): unabhaengig von Kraken, eigene Boersen-Symbole (SYMBOL+USDT bzw.
    # SYMBOL-USDT-SWAP) - fuer kleinere Watchlist-Assets ohne Binance/Bybit/OKX-
    # Perpetual schlaegt das einfach fehl (P-10, kein Symbol-Mapping gepflegt, anders
    # als bei Kraken, da die grosse Mehrheit der drei Boersen der einfachen
    # SYMBOL+USDT-Konvention folgt). Jede Boerse einzeln versucht, ein Fehlschlag
    # blockiert die anderen nicht. OI-Werte bewusst NICHT summiert (unterschiedliche
    # Einheiten je Boerse - Kontrakte vs. Coin vs. USD, siehe api/derivatives.py).
    binance_symbol = f"{asset.symbol}USDT"
    open_interest_binance = open_interest_bybit = open_interest_okx_usd = None
    long_short_ratio = long_account_pct = None
    try:
        open_interest_binance = get_binance_open_interest(binance_symbol).open_interest
    except Exception as exc:
        logger.info("Binance-Open-Interest-Abruf fuer %s fehlgeschlagen: %s", binance_symbol, exc)
    try:
        open_interest_bybit = get_bybit_open_interest(binance_symbol).open_interest
    except Exception as exc:
        logger.info("Bybit-Open-Interest-Abruf fuer %s fehlgeschlagen: %s", binance_symbol, exc)
    try:
        open_interest_okx_usd = get_okx_open_interest(f"{asset.symbol}-USDT-SWAP").open_interest_usd
    except Exception as exc:
        logger.info("OKX-Open-Interest-Abruf fuer %s fehlgeschlagen: %s", asset.symbol, exc)
    try:
        lsr = get_binance_long_short_ratio(binance_symbol)
        long_short_ratio, long_account_pct = lsr.long_short_ratio, lsr.long_account_pct
    except Exception as exc:
        logger.info("Binance-Long-Short-Ratio-Abruf fuer %s fehlgeschlagen: %s", binance_symbol, exc)

    retail_long_bias_extreme = (
        long_account_pct is not None and long_account_pct > LONG_BIAS_EXTREME_THRESHOLD_PCT
    )

    reason = (
        f"Funding-Rate (Ø letzte {len(recent)}h): {funding_rate_current}, "
        f"{DROP_LOOKBACK_DAYS}-Tage-Kursänderung: {recent_drop_pct}. "
        "Keine unabhängige Nachrichten-/Fundamentalquelle vorhanden — "
        "'moeglicher_flush' ist ein grober Hinweis, keine gesicherte Klassifikation."
    )
    if long_account_pct is not None:
        reason += (
            f" Long-Konten-Anteil (Binance): {long_account_pct:.1f}%, "
            f"Long-Short-Ratio: {long_short_ratio:.2f}."
        )
        if possible_flush and retail_long_bias_extreme:
            reason += " Überwiegend Long-positioniert bei möglichem Flush — Signal zusätzlich bestätigt."
        elif possible_flush and long_account_pct < 50:
            reason += " Mehrheit bereits short positioniert trotz möglichem Flush — uneindeutig."

    return AnticyclicContext(
        funding_rate_current=funding_rate_current,
        funding_rate_extreme=funding_rate_extreme,
        recent_drop_pct=recent_drop_pct,
        possible_flush=possible_flush,
        confirmation_gate_passed=confirmation_gate_passed,
        open_interest_binance=open_interest_binance,
        open_interest_bybit=open_interest_bybit,
        open_interest_okx_usd=open_interest_okx_usd,
        long_short_ratio=long_short_ratio,
        long_account_pct=long_account_pct,
        retail_long_bias_extreme=retail_long_bias_extreme,
        reason=reason,
    )
