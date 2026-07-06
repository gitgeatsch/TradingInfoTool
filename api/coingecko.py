"""CoinGecko API Anbindung (Free Tier, kein API-Key noetig, max. 30 Req/Min)."""
from __future__ import annotations

import time
from collections import deque
from datetime import datetime, timezone

import requests

from database.models import PriceSnapshot

BASE_URL = "https://api.coingecko.com/api/v3"
RATE_LIMIT_PER_MINUTE = 30


class CoinGeckoClient:
    def __init__(self, session: requests.Session | None = None):
        self._session = session or requests.Session()
        self._call_timestamps: deque[float] = deque()

    def _respect_rate_limit(self) -> None:
        now = time.monotonic()
        while self._call_timestamps and now - self._call_timestamps[0] > 60:
            self._call_timestamps.popleft()
        if len(self._call_timestamps) >= RATE_LIMIT_PER_MINUTE:
            sleep_for = 60 - (now - self._call_timestamps[0])
            if sleep_for > 0:
                time.sleep(sleep_for)
        self._call_timestamps.append(time.monotonic())

    def get_simple_prices(
        self, coingecko_ids: list[str], vs_currencies: tuple[str, ...] = ("usd", "eur")
    ) -> dict:
        self._respect_rate_limit()
        params = {
            "ids": ",".join(coingecko_ids),
            "vs_currencies": ",".join(vs_currencies),
            "include_market_cap": "true",
            "include_24hr_vol": "true",
            "include_24hr_change": "true",
        }
        response = self._session.get(f"{BASE_URL}/simple/price", params=params, timeout=15)
        response.raise_for_status()
        return response.json()

    def fetch_price_snapshots(self, assets: list) -> list[PriceSnapshot]:
        coingecko_ids = [asset.coingecko_id for asset in assets]
        raw = self.get_simple_prices(coingecko_ids)
        fetched_at = datetime.now(timezone.utc).isoformat()

        snapshots: list[PriceSnapshot] = []
        for asset in assets:
            data = raw.get(asset.coingecko_id)
            if data is None:
                # coingecko_id unbekannt/ungueltig oder Coin delisted - nicht abstuerzen,
                # nur diesen einen Asset ueberspringen.
                continue
            snapshots.append(
                PriceSnapshot(
                    symbol=asset.symbol,
                    coingecko_id=asset.coingecko_id,
                    price_usd=data.get("usd"),
                    price_eur=data.get("eur"),
                    market_cap_usd=data.get("usd_market_cap"),
                    volume_24h_usd=data.get("usd_24h_vol"),
                    change_24h_pct=data.get("usd_24h_change"),
                    fetched_at=fetched_at,
                )
            )
        return snapshots
