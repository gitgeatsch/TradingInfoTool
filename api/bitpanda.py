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

from collections.abc import Callable
from dataclasses import dataclass

import requests

from database.api_health import track_api_health

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


@track_api_health("bitpanda")
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


# ---------------------------------------------------------------------------
# Authentifizierte Bitpanda-Wallet-Abfrage (2026-07-10, Nutzer besitzt bereits einen
# API-Key mit "Trading, Transaction, Balance"-Scopes). Live gegen die offizielle Doku
# (developers.bitpanda.com) verifiziert: Basis-URL, Header und Antwortschema unten
# entsprechen den dort dokumentierten Beispielen. Recherche diese Session bestaetigt:
# alle drei Scopes sind laut Bitpanda-Doku UND mehreren Drittanbieter-Portfolio-
# Trackern (CoinTracking, Blockpit, Outbank - alle nutzen dasselbe Muster) rein
# LESEND - es gibt ueber die Bitpanda-API grundsaetzlich keine Order-/Auszahlungs-
# faehigkeit, unabhaengig vom gewaehlten Scope. Dieses Modul macht ausschliesslich
# GET-Aufrufe - niemals POST/Order/Auszahlung (P-7: Advisory-only, keine autonome
# Orderausfuehrung).
BITPANDA_API_V1_URL = "https://api.bitpanda.com/v1"


class BitpandaAuthError(Exception):
    """401 von der Bitpanda API - Key ungueltig/abgelaufen/falscher Scope, klar von
    Netzwerkfehlern unterschieden (P-10: sichtbarer, spezifischer Fehler statt
    genereller Exception, die der Aufrufer nicht sinnvoll unterscheiden koennte)."""


@dataclass
class BitpandaFiatWallet:
    symbol: str
    balance: float
    name: str | None = None


@dataclass
class BitpandaCryptoWallet:
    symbol: str
    balance: float
    name: str | None = None


def _auth_headers(api_key: str) -> dict:
    return {"X-Api-Key": api_key}


@track_api_health("bitpanda")
def _authenticated_get(
    path: str, api_key: str, session: requests.Session, params: dict | None = None
) -> dict:
    response = session.get(
        f"{BITPANDA_API_V1_URL}{path}", headers=_auth_headers(api_key), params=params, timeout=15
    )
    if response.status_code == 401:
        raise BitpandaAuthError(
            f"Bitpanda API antwortet mit 401 Unauthorized bei {path} - Key ungueltig, "
            "abgelaufen oder ohne 'Balance'-Scope."
        )
    response.raise_for_status()
    return response.json()


def get_fiat_wallets(api_key: str, session: requests.Session | None = None) -> list[BitpandaFiatWallet]:
    """GET /fiatwallets - Fiat-Guthaben (u.a. EUR) des Nutzers, nur lesend."""
    session = session or requests.Session()
    payload = _authenticated_get("/fiatwallets", api_key, session)
    return [
        BitpandaFiatWallet(
            symbol=entry["attributes"]["fiat_symbol"],
            balance=float(entry["attributes"]["balance"]),
            name=entry["attributes"].get("name"),
        )
        for entry in payload["data"]
    ]


def get_crypto_wallets(api_key: str, session: requests.Session | None = None) -> list[BitpandaCryptoWallet]:
    """GET /wallets - Krypto-Bestaende des Nutzers, nur lesend. Geloeschte Wallets
    (`deleted: true`) werden uebersprungen; mehrere Wallets desselben Symbols (z.B.
    nach einer Wallet-Neuanlage) werden aufsummiert statt nur die erste zu nehmen."""
    session = session or requests.Session()
    payload = _authenticated_get("/wallets", api_key, session)
    balances: dict[str, float] = {}
    names: dict[str, str] = {}
    for entry in payload["data"]:
        attrs = entry["attributes"]
        if attrs.get("deleted"):
            continue
        symbol = attrs["cryptocoin_symbol"]
        balances[symbol] = balances.get(symbol, 0.0) + float(attrs["balance"])
        names.setdefault(symbol, attrs.get("name"))
    return [BitpandaCryptoWallet(symbol=sym, balance=bal, name=names.get(sym)) for sym, bal in balances.items()]


# Nutzer-Korrektur (2026-07-10): Bitpanda fuehrt Aktien/ETF/Rohstoffe im selben
# Account wie Krypto - GET /wallets zeigt nur die Krypto-Gruppe, die anderen
# Assetklassen stecken in GET /asset-wallets unter separaten Gruppen (commodity,
# index, security, equity_security), je mit eigenen Untergruppen (z.B.
# equity_security.equity_stock fuer Aktien, equity_security.equity_etf fuer ETFs).
# Live gegen den echten Account geprueft: alle 13 Non-Krypto-Watchlist-Assets
# gefunden, zwei mit abweichendem Wallet-Symbol (siehe Override-Dict unten).
BITPANDA_NON_CRYPTO_WALLET_SYMBOL_OVERRIDES = {
    "VST-US": "VST",
    "IS0C": "ISOC",  # Ziffer Null statt Buchstabe O im Bitpanda-Wallet-Symbol
}
_NON_CRYPTO_ASSET_WALLET_GROUPS = ("commodity", "index", "security", "equity_security")


def get_non_crypto_wallets(api_key: str, session: requests.Session | None = None) -> list[BitpandaCryptoWallet]:
    """GET /asset-wallets - Aktien-/ETF-/Rohstoff-Bestaende des Nutzers, nur lesend.
    Wallet-Symbole werden ueber BITPANDA_NON_CRYPTO_WALLET_SYMBOL_OVERRIDES auf die
    internen config.yaml-Symbole abgebildet (analog BITPANDA_SYMBOL_OVERRIDES bei
    is_listed()). Geloeschte Wallets uebersprungen, mehrere Wallets desselben
    (abgebildeten) Symbols aufsummiert - identisches Verhalten zu
    get_crypto_wallets()."""
    session = session or requests.Session()
    payload = _authenticated_get("/asset-wallets", api_key, session)
    top_level = payload["data"]["attributes"]
    balances: dict[str, float] = {}
    names: dict[str, str] = {}
    for group_name in _NON_CRYPTO_ASSET_WALLET_GROUPS:
        group = top_level.get(group_name, {})
        for sub in group.values():
            for entry in sub.get("attributes", {}).get("wallets", []):
                attrs = entry["attributes"]
                if attrs.get("deleted"):
                    continue
                raw_symbol = attrs["cryptocoin_symbol"]
                symbol = BITPANDA_NON_CRYPTO_WALLET_SYMBOL_OVERRIDES.get(raw_symbol, raw_symbol)
                balances[symbol] = balances.get(symbol, 0.0) + float(attrs["balance"])
                names.setdefault(symbol, attrs.get("name"))
    return [BitpandaCryptoWallet(symbol=sym, balance=bal, name=names.get(sym)) for sym, bal in balances.items()]


# ---------------------------------------------------------------------------
# Wallet-Transaktionshistorie (2026-07-11, Einstandspreis-Feature) - liefert fuer
# jede buy/sell-Transaktion den ECHTEN Marktpreis zum Zeitpunkt (attributes.trade.
# attributes.price), live gegen den echten Account verifiziert. Live-Test bestaetigt:
# page_number-Paginierung funktioniert identisch zu get_listed_assets() (page_size
# bis mind. 500 akzeptiert, total_count=9534 -> 20 statt ~95 Requests). Ebenfalls
# bestaetigt: die API liefert neueste Transaktion zuerst - ermoeglicht fruehzeitigen
# Pagination-Abbruch bei inkrementellen Folge-Syncs (since_unix-Parameter).
BITPANDA_TRANSACTIONS_PAGE_SIZE = 500


BITPANDA_EUR_FIAT_ID = "1"  # live gegen /fiatwallets verifiziert 2026-07-11


@dataclass
class BitpandaTransaction:
    type: str  # "buy" | "sell" | "transfer" | ...
    in_or_out: str  # "incoming" | "outgoing"
    cryptocoin_symbol: str | None
    amount_cryptocoin_wallet: float
    unix_timestamp: int
    trade_price: float | None  # None wenn kein trade-Unterobjekt (transfer/stake/fee)
    trade_amount_fiat: float | None
    trade_amount_cryptocoin: float | None
    trade_fiat_id: str | None  # "1" = EUR - Aufrufer sollte nicht-EUR-Trades ausschliessen (P-10)
    tags: list[str]  # 2026-07-11, Staking-Sichtbarkeit: short_name je Tag, z.B. "stake"/"unstake"


def get_wallet_transactions(
    api_key: str,
    session: requests.Session | None = None,
    since_unix: int | None = None,
    page_size: int = BITPANDA_TRANSACTIONS_PAGE_SIZE,
    on_page_fetched: Callable[[int, int], None] | None = None,
) -> list[BitpandaTransaction]:
    """GET /wallets/transactions - komplette Transaktionshistorie, nur lesend.
    since_unix (optional) bricht die Paginierung fruehzeitig ab, sobald eine
    Transaktion mit unix_timestamp <= since_unix erscheint - fuer inkrementelle
    Folge-Syncs (siehe importer/bitpanda_avg_cost.py), da neuere Transaktionen
    immer zuerst geliefert werden. on_page_fetched(bisher_geladen, total_count)
    fuer eine Fortschrittsanzeige bei langlaufenden Erstlaeufen."""
    session = session or requests.Session()
    transactions: list[BitpandaTransaction] = []
    page = 1
    while True:
        payload = _authenticated_get(
            "/wallets/transactions",
            api_key,
            session,
            params={"page_size": page_size, "page_number": page},
        )
        meta = payload["meta"]
        total_count = meta["total_count"]
        stop_early = False
        for entry in payload["data"]:
            attrs = entry["attributes"]
            unix_ts = int(attrs["time"]["unix"])
            if since_unix is not None and unix_ts <= since_unix:
                stop_early = True
                break
            trade = attrs.get("trade")
            trade_attrs = trade["attributes"] if trade else None
            transactions.append(
                BitpandaTransaction(
                    type=attrs["type"],
                    in_or_out=attrs["in_or_out"],
                    cryptocoin_symbol=attrs.get("cryptocoin_symbol"),
                    amount_cryptocoin_wallet=float(attrs["amount"]),
                    unix_timestamp=unix_ts,
                    trade_price=float(trade_attrs["price"]) if trade_attrs else None,
                    trade_amount_fiat=float(trade_attrs["amount_fiat"]) if trade_attrs else None,
                    trade_amount_cryptocoin=float(trade_attrs["amount_cryptocoin"]) if trade_attrs else None,
                    trade_fiat_id=trade_attrs.get("fiat_id") if trade_attrs else None,
                    tags=[t["attributes"]["short_name"] for t in attrs.get("tags", [])],
                )
            )
        if on_page_fetched:
            on_page_fetched(len(transactions), total_count)
        if stop_early or page * page_size >= total_count:
            break
        page += 1
    return transactions


def resolve_bitpanda_symbol_to_watchlist(
    bitpanda_symbol: str,
    watchlist: list,
    listed_assets: list[BitpandaAsset],
) -> str | None:
    """Kehrt is_listed()/BITPANDA_SYMBOL_OVERRIDES um: bildet ein von der Wallet-API
    geliefertes Symbol auf das interne config.yaml-Symbol ab. 1) direkter Symbol-
    Treffer, 2) Override-Ruecksuche (z.B. Bitpanda "CC" -> internes "CANTON"),
    3) Namensvergleich ueber listed_assets (wie is_listed(), deckt kuenftige
    unbekannte Symbol-Abweichungen automatisch ab)."""
    for asset in watchlist:
        if asset.symbol == bitpanda_symbol:
            return asset.symbol
    reverse_overrides = {v: k for k, v in BITPANDA_SYMBOL_OVERRIDES.items()}
    if bitpanda_symbol in reverse_overrides:
        internal_symbol = reverse_overrides[bitpanda_symbol]
        if any(a.symbol == internal_symbol for a in watchlist):
            return internal_symbol
    bitpanda_name = next((a.name.strip().lower() for a in listed_assets if a.symbol == bitpanda_symbol), None)
    if bitpanda_name:
        for asset in watchlist:
            if asset.name.strip().lower() == bitpanda_name:
                return asset.symbol
    return None
