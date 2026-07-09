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
Frage "ist der Coin dort überhaupt gelistet".

WICHTIGER FUND (2026-07-09, vom Nutzer entdeckt): das interne `symbol`-Feld dieses
Projekts (`config.yaml watchlist:`) entspricht nicht immer dem am Markt tatsächlich
verwendeten Ticker - z.B. "CANTON" hier, aber "CC" bei Bitpanda UND bei praktisch
allen anderen Quellen (CoinGecko, Kraken, Coinbase, Binance, live per Web-Recherche
bestätigt). Ein reiner String-Vergleich haette hier faelschlich "nicht gelistet"
gemeldet, obwohl der Coin sehr wohl gehandelt wird. Analog zum bereits bestehenden
`api/kraken.py::KRAKEN_FUTURES_SYMBOL_MAP` (gleiches Problem, andere Boerse) gibt es
hier eine kleine, EXPLIZIT UNVOLLSTAENDIGE Override-Tabelle fuer bekannte Faelle -
kein Anspruch auf vollstaendige Abdeckung aller 41 Watchlist-Assets, nur die bisher
entdeckten Abweichungen."""
from __future__ import annotations

import requests

BITPANDA_TICKER_URL = "https://api.bitpanda.com/v1/ticker"

# Bekannte Abweichungen zwischen dem internen config.yaml-Symbol und dem am Markt
# tatsächlich verwendeten Ticker (siehe Modul-Docstring) - EXPLIZIT unvollständig,
# bei Bedarf ergänzen, sobald ein weiterer Fall auffällt.
BITPANDA_SYMBOL_OVERRIDES = {
    "CANTON": "CC",  # Canton Network - "CC" ist der Marktstandard-Ticker
}


def get_listed_symbols(session: requests.Session | None = None) -> set[str]:
    session = session or requests.Session()
    response = session.get(BITPANDA_TICKER_URL, timeout=15)
    response.raise_for_status()
    return set(response.json().keys())


def is_listed(symbol: str, listed_symbols: set[str]) -> bool:
    """Prueft ein internes config.yaml-Symbol gegen die Bitpanda-Symbolmenge, unter
    Beruecksichtigung bekannter Ticker-Abweichungen (BITPANDA_SYMBOL_OVERRIDES)."""
    return BITPANDA_SYMBOL_OVERRIDES.get(symbol, symbol) in listed_symbols
