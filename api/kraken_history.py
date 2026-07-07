"""Backfill und inkrementelles Update der echten Kraken-OHLC-Historie (price_history_ohlc).

Analog zu api/history.py (CoinGecko), aber: Schluessel ist der Ticker-Symbol statt
coingecko_id (Kraken kennt keine CoinGecko-IDs), und nur fuer Assets aus
api.kraken.KRAKEN_PAIR_MAP (35/41, siehe Basisinfos/Spezifikation.md Kap. 8). Assets
ohne Kraken-Listing werden sauber uebersprungen - das ist kein Fehler (P-10 gilt fuer
fehlerhafte/verkuerzte Daten, nicht fuer eine bekannte, dokumentierte Deckungsluecke),
die Naeherung aus indicators/calculations.py bleibt fuer sie die einzige Quelle.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import database.db as db
from api.kraken import KRAKEN_PAIR_MAP
from database.models import OhlcPoint

logger = logging.getLogger(__name__)

DAY_SECONDS = 86400
INCREMENTAL_BUFFER_DAYS = 3


@dataclass
class OhlcUpdateResult:
    symbol: str
    points_upserted: int
    skipped: bool = False  # kein Kraken-Listing fuer dieses Asset
    degraded: bool = False
    reason: str | None = None


def backfill_ohlc(client, conn, asset) -> OhlcUpdateResult:
    pair_map = KRAKEN_PAIR_MAP.get(asset.symbol)
    if pair_map is None:
        return OhlcUpdateResult(asset.symbol, 0, skipped=True, reason="kein Kraken-Listing")

    fetched_at = datetime.now(timezone.utc).isoformat()
    total_points = 0
    errors: list[str] = []

    for currency, pair in pair_map.items():
        last_date = db.get_last_ohlc_date(conn, asset.symbol, currency)
        since = None
        if last_date is not None:
            last = datetime.fromisoformat(last_date).replace(tzinfo=timezone.utc)
            since = int((last - timedelta(days=INCREMENTAL_BUFFER_DAYS)).timestamp())

        try:
            candles = client.get_ohlc(pair, interval=1440, since=since)
        except Exception as exc:
            errors.append(f"{currency}: {exc}")
            logger.info("Kraken-OHLC-Abruf (%s) fuer %s fehlgeschlagen: %s", currency, asset.symbol, exc)
            continue

        points = [
            OhlcPoint(
                symbol=asset.symbol,
                currency=currency,
                date=c["date"],
                open=c["open"],
                high=c["high"],
                low=c["low"],
                close=c["close"],
                volume=c["volume"],
                fetched_at=fetched_at,
            )
            for c in candles
        ]
        db.upsert_ohlc_points(conn, points)
        total_points += len(points)

    if total_points == 0:
        reason = "; ".join(errors) if errors else "Keine Kerzen erhalten"
        return OhlcUpdateResult(asset.symbol, 0, degraded=True, reason=reason)
    if errors:
        return OhlcUpdateResult(asset.symbol, total_points, degraded=True, reason="; ".join(errors))
    return OhlcUpdateResult(asset.symbol, total_points)


def backfill_all_ohlc(client, conn, watchlist) -> list[OhlcUpdateResult]:
    results = []
    for asset in watchlist:
        result = backfill_ohlc(client, conn, asset)
        results.append(result)
        if result.degraded:
            logger.info("Kraken-OHLC fuer %s unvollstaendig: %s", asset.symbol, result.reason)
    return results
