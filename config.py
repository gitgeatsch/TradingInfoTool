"""Laedt Basisinfos/config.yaml (Watchlist etc.) sowie optional .env fuer den Rest der App.

.env-Loading ist bewusst minimal (nur COINGECKO_API_KEY, siehe P-9/P-10-Kontext) - kein
ANTHROPIC_API_KEY/GITHUB_TOKEN-Gebrauch hier, das bleibt Phase 3 vorbehalten (P-8:
lokale Autonomie, Claude nur optional)."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml
from dotenv import load_dotenv

CONFIG_PATH = Path(__file__).resolve().parent / "Basisinfos" / "config.yaml"
ENV_PATH = Path(__file__).resolve().parent / ".env"

_config_cache: dict | None = None


def load_env() -> None:
    """Laedt .env falls vorhanden (kein Fehler falls die Datei fehlt - Key ist optional)."""
    load_dotenv(ENV_PATH)


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
