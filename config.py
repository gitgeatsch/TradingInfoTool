"""Laedt Basisinfos/config.yaml (Watchlist etc.) fuer den Rest der App."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

CONFIG_PATH = Path(__file__).resolve().parent / "Basisinfos" / "config.yaml"

_config_cache: dict | None = None


@dataclass
class WatchlistAsset:
    symbol: str
    name: str
    typ: str        # core | taktisch | stablecoin
    status: str     # aktiv | watchlist
    coingecko_id: str


def load_config() -> dict:
    global _config_cache
    if _config_cache is None:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            _config_cache = yaml.safe_load(f)
    return _config_cache


def get_watchlist() -> list[WatchlistAsset]:
    config = load_config()
    return [
        WatchlistAsset(
            symbol=entry["symbol"],
            name=entry["name"],
            typ=entry["typ"],
            status=entry["status"],
            coingecko_id=entry["coingecko_id"],
        )
        for entry in config["watchlist"]
    ]
