"""Bitpanda-Handelsbörsen-Abfrage - öffentlicher, kostenloser Endpunkt (kein Account/
Key nötig), genutzt um zu prüfen, ob ein Coin auf der Handelsbörse des Nutzers
überhaupt kaufbar ist. Nutzer-Wunsch (2026-07-09): ein Marktscan-Kaufkandidat oder
sogar ein bestehender Watchlist-Eintrag kann bei CoinGecko/Kraken existieren, ohne
dass er auf der tatsächlichen Handelsbörse des Nutzers gelistet ist - das soll
sichtbar gemacht werden, nicht stillschweigend übergangen werden (P-10).

WICHTIGER FUND (2026-07-09, vom Nutzer entdeckt): das interne `symbol`-Feld dieses
Projekts (`config.yaml watchlist:`) entspricht nicht immer dem am Markt tatsächlich
verwendeten Ticker - z.B. "CANTON" hier, aber "CC" bei Bitpanda UND bei praktisch
allen anderen Quellen (CoinGecko, Kraken, Coinbase, Binance, live per Web-Recherche
bestätigt). Ein reiner String-Vergleich hätte hier fälschlich "nicht gelistet"
gemeldet, obwohl der Coin sehr wohl gehandelt wird - analog zum bereits bestehenden
`api/kraken.py::KRAKEN_FUTURES_SYMBOL_MAP` (gleiches Problem, andere Börse).

Live verifiziert 2026-07-09: `GET https://api.bitpanda.com/v3/assets` liefert ohne
Auth Symbol UND Name (paginiert, `page_size`/`page_number`, insgesamt 3233 Einträge
über alle Anlageklassen, davon 857 in den Krypto-relevanten Gruppen coin/token/
leveraged_token/index). Ersetzt den ursprünglich genutzten `/v1/ticker`-Endpunkt
(nur Symbole, keine Namen) - der Namensvergleich erlaubt `is_listed()` einen
AUTOMATISCHEN Fallback bei einem Symbol-Mismatch, statt jeden künftigen CANTON-
ähnlichen Fall manuell in `BITPANDA_SYMBOL_OVERRIDES` nachtragen zu müssen. Voller
Namensabgleich aller 41 Watchlist-Assets (2026-07-09) bestätigte: CANTON war der
einzige Fall, "CC" heißt bei Bitpanda selbst offiziell "Canton" (exakte
Namensübereinstimmung, kein Ticker-Zufallstreffer)."""
from __future__ import annotations

from dataclasses import dataclass

import requests

BITPANDA_ASSETS_URL = "https://api.bitpanda.com/v3/assets"
BITPANDA_ASSETS_PAGE_SIZE = 500
# Gruppen, die tatsaechlich Kryptowaehrungen sind (schliesst stock/etf/etc/metal aus,
# siehe Modul-Docstring - live per Gruppen-Auszaehlung ermittelt 2026-07-09).
CRYPTO_ASSET_GROUPS = {"coin", "token", "leveraged_token", "index"}

# Bekannte Abweichungen zwischen dem internen config.yaml-Symbol und dem am Markt
# tatsächlich verwendeten Ticker (siehe Modul-Docstring) - dient nur noch als
# schneller Vorab-Check, der Namensvergleich in is_listed() faengt neue Faelle
# ohnehin automatisch ab.
BITPANDA_SYMBOL_OVERRIDES = {
    "CANTON": "CC",  # Canton Network - "CC" ist der Marktstandard-Ticker
}


@dataclass
class BitpandaAsset:
    symbol: str
    name: str
    group: str


def get_listed_assets(session: requests.Session | None = None) -> list[BitpandaAsset]:
    """Alle Krypto-relevanten Bitpanda-Assets (Symbol + Name), paginiert abgerufen."""
    session = session or requests.Session()
    assets: list[BitpandaAsset] = []
    page = 1
    while True:
        response = session.get(
            BITPANDA_ASSETS_URL,
            params={"page_size": BITPANDA_ASSETS_PAGE_SIZE, "page_number": page},
            timeout=15,
        )
        response.raise_for_status()
        payload = response.json()
        for entry in payload["data"]:
            attrs = entry["attributes"]
            if attrs["group"] in CRYPTO_ASSET_GROUPS:
                assets.append(BitpandaAsset(symbol=attrs["symbol"], name=attrs["name"], group=attrs["group"]))
        meta = payload["meta"]
        if meta["page_number"] * BITPANDA_ASSETS_PAGE_SIZE >= meta["total_count"]:
            break
        page += 1
    return assets


def is_listed(symbol: str, listed_assets: list[BitpandaAsset], name: str | None = None) -> bool:
    """Prüft primär per Symbol (unter Berücksichtigung bekannter Ticker-Abweichungen,
    `BITPANDA_SYMBOL_OVERRIDES`). Fällt bei Fehlschlag automatisch auf einen
    Namensvergleich zurück, falls `name` mitgegeben wird - deckt damit auch bisher
    UNBEKANNTE Symbol-Abweichungen ab (wie ursprünglich bei CANTON/CC entdeckt),
    ohne dass jeder Einzelfall manuell nachgetragen werden muss."""
    target_symbol = BITPANDA_SYMBOL_OVERRIDES.get(symbol, symbol)
    if any(a.symbol == target_symbol for a in listed_assets):
        return True
    if name:
        name_normalized = name.strip().lower()
        return any(a.name.strip().lower() == name_normalized for a in listed_assets)
    return False
