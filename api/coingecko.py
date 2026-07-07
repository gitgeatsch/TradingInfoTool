"""CoinGecko API Anbindung. Free Tier ohne Key: 30 Req/Min (anonym, in der Praxis
unzuverlaessig - siehe Spezifikation Kap. 8/16, laengere Sperren bei intensivem Testen
moeglich). Mit kostenlosem Demo-API-Key (COINGECKO_API_KEY in .env): 100 Req/Min,
stabiler. Key ist optional - App funktioniert auch ohne (konservativeres Limit)."""
from __future__ import annotations

import time
from collections import deque
from datetime import datetime, timezone

import requests

from database.models import PriceSnapshot

BASE_URL = "https://api.coingecko.com/api/v3"
RATE_LIMIT_ANONYMOUS_PER_MINUTE = 30
RATE_LIMIT_WITH_KEY_PER_MINUTE = 100
DEFAULT_COOLDOWN_SECONDS = 60  # Backoff nach 429, falls kein Retry-After-Header vorhanden
MAX_COOLDOWN_SECONDS = 300  # Deckel fuer den exponentiellen Backoff (5 Min)


class CoinGeckoClient:
    def __init__(self, session: requests.Session | None = None, api_key: str | None = None):
        self._session = session or requests.Session()
        self._call_timestamps: deque[float] = deque()
        self._cooldown_until: float = 0.0
        self._consecutive_429s: int = 0
        self._rate_limit_per_minute = (
            RATE_LIMIT_WITH_KEY_PER_MINUTE if api_key else RATE_LIMIT_ANONYMOUS_PER_MINUTE
        )
        if api_key:
            self._session.headers.update({"x-cg-demo-api-key": api_key})

    def _respect_rate_limit(self) -> None:
        now = time.monotonic()
        if now < self._cooldown_until:
            time.sleep(self._cooldown_until - now)
            now = time.monotonic()
        while self._call_timestamps and now - self._call_timestamps[0] > 60:
            self._call_timestamps.popleft()
        if len(self._call_timestamps) >= self._rate_limit_per_minute:
            sleep_for = 60 - (now - self._call_timestamps[0])
            if sleep_for > 0:
                time.sleep(sleep_for)
        self._call_timestamps.append(time.monotonic())

    def _get(self, url: str, params: dict) -> dict:
        self._respect_rate_limit()
        response = self._session.get(url, params=params, timeout=15)
        if response.status_code == 429:
            # Server sagt "zu viele Anfragen" trotz unseres eigenen Limiters (z.B. IP-weites
            # Limit, nicht nur pro Client) - exponentiell laengere Abkuehlpause erzwingen,
            # bevor der NAECHSTE Call (auch fuer ein anderes Asset) versucht wird. Verhindert
            # eine Kaskade sofortiger Folgefehler UND reagiert auf laenger anhaltende Sperren
            # (z.B. nach intensivem Testen), bei denen eine fixe Pause nicht reicht.
            self._consecutive_429s += 1
            retry_after = response.headers.get("Retry-After")
            if retry_after:
                cooldown_seconds = float(retry_after)
            else:
                cooldown_seconds = min(
                    DEFAULT_COOLDOWN_SECONDS * (2 ** (self._consecutive_429s - 1)),
                    MAX_COOLDOWN_SECONDS,
                )
            self._cooldown_until = time.monotonic() + cooldown_seconds
        else:
            self._consecutive_429s = 0
        response.raise_for_status()
        return response.json()

    def get_simple_prices(
        self, coingecko_ids: list[str], vs_currencies: tuple[str, ...] = ("usd", "eur")
    ) -> dict:
        params = {
            "ids": ",".join(coingecko_ids),
            "vs_currencies": ",".join(vs_currencies),
            "include_market_cap": "true",
            "include_24hr_vol": "true",
            "include_24hr_change": "true",
        }
        return self._get(f"{BASE_URL}/simple/price", params)

    def get_market_chart(self, coingecko_id: str, vs_currency: str, days: int) -> dict:
        params = {"vs_currency": vs_currency, "days": days}
        return self._get(f"{BASE_URL}/coins/{coingecko_id}/market_chart", params)

    def get_global_data(self) -> dict:
        """Liefert u.a. data.market_cap_percentage.btc (BTC-Dominanz, Kap. 8 R-5.1)."""
        return self._get(f"{BASE_URL}/global", params={})

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
