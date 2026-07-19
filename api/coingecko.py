"""CoinGecko API Anbindung. Free Tier ohne Key: 30 Req/Min (anonym, in der Praxis
unzuverlaessig - siehe Spezifikation Kap. 8/16, laengere Sperren bei intensivem Testen
moeglich). Mit kostenlosem Demo-API-Key (COINGECKO_API_KEY in .env): 100 Req/Min,
stabiler. Key ist optional - App funktioniert auch ohne (konservativeres Limit)."""
from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone

import requests

from database.api_health import track_api_health
from database.models import PriceSnapshot

BASE_URL = "https://api.coingecko.com/api/v3"
RATE_LIMIT_ANONYMOUS_PER_MINUTE = 30
RATE_LIMIT_WITH_KEY_PER_MINUTE = 100
DEFAULT_COOLDOWN_SECONDS = 60  # Backoff nach 429, falls kein Retry-After-Header vorhanden
MAX_COOLDOWN_SECONDS = 300  # Deckel fuer den exponentiellen Backoff (5 Min)


@dataclass
class CoinSearchResult:
    coingecko_id: str
    symbol: str
    name: str
    market_cap_rank: int | None


@dataclass
class TrendingCoin:
    coingecko_id: str
    symbol: str
    name: str
    market_cap_rank: int | None
    trending_rank: int  # Position in der Trending-Liste (1-basiert)


@dataclass
class MarketCoin:
    coingecko_id: str
    symbol: str
    name: str
    price_usd: float | None
    market_cap_usd: float | None
    volume_24h_usd: float | None
    change_24h_pct: float | None
    atl_date: str | None  # Alters-Proxy, siehe agent/krypto/marktscan.py - CoinGecko liefert
    # kein echtes Listing-Datum, live geprueft 2026-07-09
    # Mehrtages-Kontext (2026-07-16, Marktscan-Momentum-Nachbesserung, siehe
    # agent/krypto/marktscan.py::score_momentum()) - GRATIS im selben
    # /coins/markets-Call miterfasst (live per WebFetch verifiziert:
    # price_change_percentage=24h,7d,30d liefert alle drei Felder ohne
    # Zusatzkosten). None fuer Kandidaten aus dem Trending-Ergaenzungs-Call
    # (get_simple_prices() liefert kein 7d/30d, P-10: fehlend statt geraten).
    change_7d_pct: float | None = None
    change_30d_pct: float | None = None


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

    @track_api_health("coingecko")
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

    def search_coins(self, query: str) -> list[CoinSearchResult]:
        """CoinGecko `/search` - fuer die manuelle Symbol->coingecko_id-Aufloesung
        im "Asset hinzufuegen/bearbeiten"-Dialog (2026-07-19, echter Fund: Symbol
        allein ist bei CoinGecko NICHT eindeutig - z.B. teilen sich 12
        verschiedene IDs den Ticker "SOL" (echtes Solana + 11 gebrueckte/
        gewrappte Varianten), 2.116 von 13.704 Symbolen insgesamt sind
        mehrdeutig, live per WebFetch/Skript verifiziert). Deshalb bewusst KEINE
        automatische Zuordnung (z.B. "erstes Ergebnis nehmen") - das koennte
        still die falsche Coin-Historie laden. Stattdessen zeigt der Dialog dem
        Nutzer eine sortierte Auswahl, er bestaetigt selbst.

        Ergebnis sortiert: exakte Symbol-Treffer zuerst (Marktkap.-Rang
        aufsteigend, kein Rang zuletzt), danach die uebrigen (Name-)Treffer in
        der von CoinGecko gelieferten Relevanz-Reihenfolge - der `/search`-
        Endpunkt liefert `market_cap_rank` bereits mit, ein zusaetzlicher
        `/coins/markets`-Call zur Disambiguierung ist nicht noetig."""
        data = self._get(f"{BASE_URL}/search", {"query": query})
        results = [
            CoinSearchResult(
                coingecko_id=c["id"], symbol=c["symbol"].upper(), name=c["name"],
                market_cap_rank=c.get("market_cap_rank"),
            )
            for c in data.get("coins", [])
        ]
        query_upper = query.strip().upper()
        exakt = sorted(
            (r for r in results if r.symbol == query_upper),
            key=lambda r: (r.market_cap_rank is None, r.market_cap_rank or 0),
        )
        rest = [r for r in results if r.symbol != query_upper]
        return exakt + rest

    def get_global_data(self) -> dict:
        """Liefert u.a. data.market_cap_percentage.btc (BTC-Dominanz, Kap. 8 R-5.1)."""
        return self._get(f"{BASE_URL}/global", params={})

    def get_trending(self) -> list[TrendingCoin]:
        """CoinGecko `/search/trending` - taeglich neu berechnete Trending-Coins
        (suchanfragen-basiert, nicht Kursperformance). MS-2. Live verifiziert
        2026-07-09."""
        data = self._get(f"{BASE_URL}/search/trending", params={})
        result = []
        for rank, entry in enumerate(data.get("coins", []), start=1):
            item = entry["item"]
            result.append(
                TrendingCoin(
                    coingecko_id=item["id"], symbol=item["symbol"].upper(), name=item["name"],
                    market_cap_rank=item.get("market_cap_rank"), trending_rank=rank,
                )
            )
        return result

    def get_markets_page(self, page: int, per_page: int = 250, vs_currency: str = "usd") -> list[MarketCoin]:
        """Eine Seite von `/coins/markets`, sortiert nach Marktkapitalisierung
        (absteigend). WICHTIG: der `order=price_change_percentage_24h_desc`-Parameter
        ist auf der Free-Tier praktisch wirkungslos (live verifiziert 2026-07-09 -
        lieferte weiterhin nach Marktkap. sortierte Ergebnisse, keine echten
        Top-Gewinner) - deshalb IMMER `market_cap_desc` abrufen und bei Bedarf
        client-seitig sortieren, siehe `fetch_top_gainers()`."""
        params = {
            "vs_currency": vs_currency, "order": "market_cap_desc", "per_page": per_page,
            "page": page, "sparkline": "false",
            # 24h,7d,30d in EINEM Call (2026-07-16 erweitert, live per WebFetch
            # verifiziert - keine Zusatzkosten) - Grundlage fuer den
            # Mehrtages-Kontext in marktscan.py::score_momentum().
            "price_change_percentage": "24h,7d,30d",
        }
        data = self._get(f"{BASE_URL}/coins/markets", params)
        return [
            MarketCoin(
                coingecko_id=c["id"], symbol=c["symbol"].upper(), name=c["name"],
                price_usd=c.get("current_price"), market_cap_usd=c.get("market_cap"),
                volume_24h_usd=c.get("total_volume"),
                change_24h_pct=c.get("price_change_percentage_24h"), atl_date=c.get("atl_date"),
                change_7d_pct=c.get("price_change_percentage_7d_in_currency"),
                change_30d_pct=c.get("price_change_percentage_30d_in_currency"),
            )
            for c in data
        ]

    def fetch_top_gainers(self, pages: int = 5, top_n: int = 30) -> list[MarketCoin]:
        """Top-Gewinner nach 24h-Aenderung ueber die obersten `pages` Marktkap.-Seiten
        (client-seitiger Workaround, siehe `get_markets_page()`-Docstring). MS-2.
        `pages=5` deckt die Top ~1250 nach Marktkap. ab - reicht i.d.R. bis in den
        Tier-3-Bereich (>= 20 Mio. $, siehe config.yaml marktscan.tiers), Quota-Kosten
        ~5 Calls/Scan-Lauf."""
        all_coins: list[MarketCoin] = []
        for page in range(1, pages + 1):
            all_coins.extend(self.get_markets_page(page))
        sortable = [c for c in all_coins if c.change_24h_pct is not None]
        sortable.sort(key=lambda c: c.change_24h_pct, reverse=True)
        return sortable[:top_n]

    def fetch_price_snapshots(self, assets: list) -> list[PriceSnapshot]:
        coingecko_ids = [asset.coingecko_id for asset in assets if asset.coingecko_id is not None]
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


def resolve_coingecko_id_by_name(results: list[CoinSearchResult], expected_name: str) -> str | None:
    """Loest eine `coingecko_id` automatisch auf, wenn GENAU EIN `search_coins()`-
    Treffer namentlich mit dem von Bitpanda gelisteten Namen uebereinstimmt
    (2026-07-19, Nutzer-Vorschlag: Bitpandas eigener, kuratierter Katalog
    listet nie zwei verschiedene Coins unter demselben Ticker - live
    verifiziert, z.B. Bitpanda-Name "Solana" fuer Symbol SOL matcht exakt
    genau EINEN von 25 CoinGecko-Suchtreffern. Der Namensabgleich disambiguiert
    dadurch zuverlaessig in der ueberwiegenden Mehrheit der Faelle, ohne dass
    der Nutzer manuell auswaehlen muss). Gibt bewusst None zurueck, wenn KEIN
    oder MEHR ALS EIN Treffer passt - das ist dann eine echte Inkonsistenz
    (Bitpanda-Name ohne eindeutiges CoinGecko-Pendant), kein Fall fuer
    automatisches Raten (siehe CoinSearchDialog-Docstring in ui/app.py fuer
    den manuellen Rueckfall in genau diesem Fall)."""
    expected_normalized = expected_name.strip().lower()
    matches = [r for r in results if r.name.strip().lower() == expected_normalized]
    if len(matches) == 1:
        return matches[0].coingecko_id
    return None
