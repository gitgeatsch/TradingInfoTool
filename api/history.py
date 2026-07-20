"""Backfill und inkrementelles Update der historischen Kursdaten (price_history, Kap. 8/11).

Nutzt /coins/{id}/market_chart (CoinGecko Free Tier: echte Tagesdaten fuer >90 Tage,
bis zu 365 Tage). Erstlauf: voller Jahres-Call je Waehrung. Danach nur die Luecke seit
dem letzten gespeicherten Tag nachladen (+ Puffer fuer UTC-Bucket-Verschiebungen).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone

import database.db as db
from database.models import PriceHistoryPoint

logger = logging.getLogger(__name__)

FULL_BACKFILL_DAYS = 365
INCREMENTAL_BUFFER_DAYS = 3


@dataclass
class HistoryUpdateResult:
    coingecko_id: str
    points_upserted: int
    degraded: bool = False
    reason: str | None = None


def _bucket_prices_by_date(raw_prices: list) -> dict[str, float]:
    """raw_prices: [[timestamp_ms, price], ...] -> {date: price} (letzter Punkt je Tag)."""
    buckets: dict[str, float] = {}
    for timestamp_ms, price in raw_prices:
        date = datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc).date().isoformat()
        buckets[date] = price
    return buckets


def backfill_history(client, conn, asset, days: int = FULL_BACKFILL_DAYS) -> HistoryUpdateResult:
    # 2026-07-20, echter Notebook-Fund (API-Health-Log: ".../coins/None/market_chart"
    # 404) - ein Krypto-Asset ohne aufgeloeste coingecko_id (z.B. frisch per Auto-Add
    # angelegt, Aufloesung noch ausstehend/fehlgeschlagen) loeste hier taeglich zwei
    # sinnlose CoinGecko-Calls aus, die ohnehin nur per try/except abgefangen wurden.
    # Klarer Skip statt stillem Fehlschlag (P-10).
    if not asset.coingecko_id:
        return HistoryUpdateResult(
            coingecko_id=asset.coingecko_id, points_upserted=0, degraded=True,
            reason="Keine coingecko_id vorhanden - Historie-Abruf übersprungen.",
        )
    last_date = db.get_last_history_date(conn, asset.coingecko_id)
    if last_date is None:
        fetch_days = days
    else:
        last = datetime.fromisoformat(last_date).date()
        today = datetime.now(timezone.utc).date()
        gap_days = (today - last).days
        fetch_days = max(gap_days + INCREMENTAL_BUFFER_DAYS, 1)

    # USD und EUR unabhaengig voneinander versuchen: schlaegt eine Waehrung fehl, soll die
    # andere (falls erfolgreich) trotzdem gespeichert werden, statt beides zu verwerfen (P-10 -
    # transparent degradiert statt komplett leer bei einem Teilausfall).
    usd_by_date: dict[str, float] = {}
    eur_by_date: dict[str, float] = {}
    errors: list[str] = []

    try:
        usd_data = client.get_market_chart(asset.coingecko_id, "usd", fetch_days)
        usd_by_date = _bucket_prices_by_date(usd_data.get("prices", []))
    except Exception as exc:
        errors.append(f"USD: {exc}")
        logger.info("Historie-Abruf (USD) für %s fehlgeschlagen: %s", asset.symbol, exc)

    try:
        eur_data = client.get_market_chart(asset.coingecko_id, "eur", fetch_days)
        eur_by_date = _bucket_prices_by_date(eur_data.get("prices", []))
    except Exception as exc:
        errors.append(f"EUR: {exc}")
        logger.info("Historie-Abruf (EUR) für %s fehlgeschlagen: %s", asset.symbol, exc)

    all_dates = sorted(set(usd_by_date) | set(eur_by_date))

    if not all_dates:
        reason = "; ".join(errors) if errors else "Keine Datenpunkte erhalten"
        return HistoryUpdateResult(asset.coingecko_id, 0, degraded=True, reason=reason)

    fetched_at = datetime.now(timezone.utc).isoformat()
    points = [
        PriceHistoryPoint(
            coingecko_id=asset.coingecko_id,
            date=date,
            price_usd=usd_by_date.get(date),
            price_eur=eur_by_date.get(date),
            fetched_at=fetched_at,
        )
        for date in all_dates
    ]

    db.upsert_price_history_points(conn, points)

    if errors:
        return HistoryUpdateResult(
            asset.coingecko_id, len(points), degraded=True, reason="; ".join(errors)
        )
    return HistoryUpdateResult(asset.coingecko_id, len(points))


def backfill_all(client, conn, watchlist) -> list[HistoryUpdateResult]:
    results = []
    for asset in watchlist:
        result = backfill_history(client, conn, asset)
        results.append(result)
        if result.degraded:
            logger.info(
                "Historie für %s (%s) unvollständig: %s",
                asset.symbol,
                asset.coingecko_id,
                result.reason,
            )
    return results
