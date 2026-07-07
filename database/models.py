"""Datenmodelle fuer die SQLite-Tabellen (kein ORM, nur Dataclasses)."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Holding:
    symbol: str
    quantity: float
    updated_at: str
    source: str = "import"


@dataclass
class PriceSnapshot:
    symbol: str
    coingecko_id: str
    price_usd: float | None
    price_eur: float | None
    market_cap_usd: float | None
    volume_24h_usd: float | None
    change_24h_pct: float | None
    fetched_at: str


@dataclass
class PriceHistoryPoint:
    coingecko_id: str
    date: str  # 'YYYY-MM-DD', UTC-Tagesbucket
    price_usd: float | None
    price_eur: float | None
    fetched_at: str


@dataclass
class MacroSnapshot:
    date: str  # 'YYYY-MM-DD', UTC-Tagesbucket
    btc_dominance_pct: float | None
    fear_greed_value: int | None
    fear_greed_label: str | None
    fetched_at: str


@dataclass
class Signal:
    """Ergebnis der Agent-Pipeline (Spezifikation Kap. 5, Ausgabeformat P-5).
    Append-only - jeder Pipeline-Lauf fuegt eine neue Zeile ein (Audit-Trail, Z-4/B-6),
    nie ein Upsert. id=None vor dem Insert."""
    symbol: str
    created_at: str
    action: str  # KAUFEN|VERKAUFEN|TAUSCHEN|HALTEN|NACHKAUFEN
    gate_passed: bool
    gate_reason: str | None
    risk_veto: bool
    facts_json: str
    id: int | None = None
    pipeline_version: str = "1"
    confidence_pct: float | None = None
    short_reasoning: str | None = None
    long_reasoning_technisch: str | None = None
    long_reasoning_fundamental: str | None = None
    long_reasoning_makro: str | None = None
    position_size_usd: float | None = None
    position_size_eur: float | None = None
    position_size_note: str | None = None
    entry_usd: float | None = None
    entry_eur: float | None = None
    stop_loss_usd: float | None = None
    stop_loss_eur: float | None = None
    take_profit_usd: float | None = None
    take_profit_eur: float | None = None
    holding_duration: str | None = None
    holding_duration_reason: str | None = None
    key_risks_text: str | None = None
    regime: str | None = None
    regime_source: str | None = None
    forecast_bull_text: str | None = None
    forecast_bull_prob_pct: float | None = None
    forecast_base_text: str | None = None
    forecast_base_prob_pct: float | None = None
    forecast_bear_text: str | None = None
    forecast_bear_prob_pct: float | None = None
    tauschen_target_symbol: str | None = None
    risk_veto_reason: str | None = None
    groq_raw_response: str | None = None
    groq_model: str | None = None


@dataclass
class OhlcPoint:
    """Echte Tageskerze von Kraken (nicht die CoinGecko-Schlusskurs-Naeherung)."""
    symbol: str
    currency: str  # 'USD' oder 'EUR'
    date: str  # 'YYYY-MM-DD', UTC-Tagesbucket
    open: float
    high: float
    low: float
    close: float
    volume: float
    fetched_at: str
