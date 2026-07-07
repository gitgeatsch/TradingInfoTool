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
