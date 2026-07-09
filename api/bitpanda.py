"""Bitpanda-Handelsbörsen-Abfrage - öffentlicher, kostenloser Preis-Ticker-Endpunkt
(kein Account/Key nötig), genutzt um zu prüfen, ob ein Coin auf der Handelsbörse des
Nutzers überhaupt kaufbar ist. Nutzer-Wunsch (2026-07-09): ein Marktscan-Kaufkandidat
oder sogar ein bestehender Watchlist-Eintrag kann bei CoinGecko/Kraken existieren,
ohne dass er auf der tatsächlichen Handelsbörse des Nutzers gelistet ist - das soll
sichtbar gemacht werden, nicht stillschweigend übergangen werden (P-10).

Live verifiziert 2026-07-09: `GET https://api.bitpanda.com/v1/ticker` liefert ohne
Auth 868 Symbole (Coins, Metalle, Indizes, gehebelte Token), Preise in mehreren
Fiat-Währungen je Symbol - hier wird bewusst NUR die Symbol-Menge genutzt (für Preise
nutzt das Projekt bereits CoinGecko, siehe Kap. 8), es geht ausschließlich um die
Frage "ist der Coin dort überhaupt gelistet"."""
from __future__ import annotations

import requests

BITPANDA_TICKER_URL = "https://api.bitpanda.com/v1/ticker"


def get_listed_symbols(session: requests.Session | None = None) -> set[str]:
    session = session or requests.Session()
    response = session.get(BITPANDA_TICKER_URL, timeout=15)
    response.raise_for_status()
    return set(response.json().keys())
