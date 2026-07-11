"""Echter Anschaffungspreis (gleitender Durchschnitt) aus Bitpanda-Trade-Daten
(2026-07-11, Nutzer-Wunsch). Bewusst NUR der echte Marktpreis zum Kaufzeitpunkt -
KEINE steuerliche Kostenbasis-Verfolgung ueber Swap-Ketten (Nutzer-Entscheidung:
das bleibt bei Bitpanda selbst, fuer das Tool nicht relevant, siehe
Basisinfos/Regelwerksmanual.md).

Bewusst eine EIGENE Datei, NICHT in importer/bitpanda_sync.py integriert - schuetzt
die dortige, bereits produktiv laufende Bestands-Sync-Atomaritaetslogik vor
Regressionen und macht die deutlich teurere neue Operation (bis zu ~9500
Transaktionen vs. ~60 Wallet-Objekte) zu einem eigenen, unabhaengigen Menuepunkt.

P-10 (kein stiller Falschwert): der gleitende Durchschnitt laesst sich nur aus
bepreisten buy/sell-Trades berechnen. holdings.quantity kann zusaetzliche Einheiten
enthalten, die NIE ueber einen bepreisten Trade liefen (Staking-Gutschriften,
externe Einzahlungen). tracked_quantity haelt fest, auf wie viel sich
avg_buy_price_eur tatsaechlich bezieht - Aufrufer muessen min(holding.quantity,
tracked_quantity) als "bekannte Menge" behandeln, den Rest explizit als "unbekannt"
ausweisen (siehe compute_cost_basis_view())."""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field

import database.db as db
from api.bitpanda import (
    BITPANDA_EUR_FIAT_ID,
    BitpandaAsset,
    BitpandaTransaction,
    get_wallet_transactions,
    resolve_bitpanda_symbol_to_watchlist,
)
from database.models import Holding

_PRICED_TYPES = {"buy", "sell"}


@dataclass
class AvgCostResult:
    symbol: str
    avg_buy_price_eur: float | None
    tracked_quantity: float
    buy_count: int
    sell_count: int


def compute_avg_buy_prices(
    transactions: list[BitpandaTransaction],
    existing: dict[str, AvgCostResult] | None = None,
) -> dict[str, AvgCostResult]:
    """Reine Funktion, keine DB/Netzwerk. Gleitender Durchschnitt ueber alle
    bepreisten buy/sell-Transaktionen (type in {buy, sell}, trade_price vorhanden,
    trade_fiat_id == EUR), chronologisch (unix_timestamp aufsteigend) verarbeitet -
    unabhaengig davon, ob der Trade ein Direktkauf oder die Empfangs-/Verkaufsseite
    eines Swaps war (beide Seiten haben einen echten Marktpreis, siehe Modul-
    Docstring - wir tracken keine Swap-Ketten, jede Transaktion zaehlt fuer sich).
    Alle anderen Typen (transfer/stake/unstake/fee) sowie nicht-EUR-Trades werden
    ignoriert.

    buy blendet in den bestehenden Durchschnitt ein, sell reduziert nur die
    getrackte Menge (der Durchschnitt der verbleibenden Stuecke aendert sich nicht -
    Standard-Verhalten des gleitenden Durchschnitts).

    existing (optional): Ergebnis eines vorherigen Laufs als Startpunkt fuer
    inkrementelle Folge-Syncs (siehe sync_avg_buy_prices) - dieselbe Blend-Formel,
    nur mit dem gespeicherten Wert statt bei 0 zu beginnen."""
    results: dict[str, AvgCostResult] = {}
    if existing:
        for symbol, r in existing.items():
            results[symbol] = AvgCostResult(
                symbol=symbol,
                avg_buy_price_eur=r.avg_buy_price_eur,
                tracked_quantity=r.tracked_quantity,
                buy_count=r.buy_count,
                sell_count=r.sell_count,
            )

    priced = [
        t
        for t in transactions
        if t.type in _PRICED_TYPES
        and t.trade_price is not None
        and t.cryptocoin_symbol
        and t.trade_fiat_id == BITPANDA_EUR_FIAT_ID
    ]
    priced.sort(key=lambda t: t.unix_timestamp)

    for t in priced:
        qty = t.trade_amount_cryptocoin if t.trade_amount_cryptocoin is not None else t.amount_cryptocoin_wallet
        if not qty or qty <= 0:
            continue

        symbol = t.cryptocoin_symbol
        r = results.get(symbol)
        if r is None:
            r = AvgCostResult(symbol=symbol, avg_buy_price_eur=None, tracked_quantity=0.0, buy_count=0, sell_count=0)
            results[symbol] = r

        if t.type == "buy":
            prior_qty = r.tracked_quantity
            prior_price = r.avg_buy_price_eur or 0.0
            new_qty = prior_qty + qty
            r.avg_buy_price_eur = (prior_qty * prior_price + qty * t.trade_price) / new_qty
            r.tracked_quantity = new_qty
            r.buy_count += 1
        else:  # sell
            r.tracked_quantity = max(0.0, r.tracked_quantity - qty)
            r.sell_count += 1

    return results


def compute_staked_quantities(
    transactions: list[BitpandaTransaction],
    existing: dict[str, float] | None = None,
) -> dict[str, float]:
    """2026-07-11, Nutzer-Fund: gestakte Bestaende sind ueber die normalen Wallet-
    Endpunkte strukturell nicht sichtbar (siehe [[project-bitpanda-exchange]]) -
    Bitpanda bucht einen "stake"-Transfer als ABGANG aus der normalen Wallet, ein
    spaeterer "unstake"-Transfer als ZUGANG zurueck. Reine Funktion, keine DB/
    Netzwerk - laeuft chronologisch durch alle "transfer"-Transaktionen mit
    stake/unstake-Tag und fuehrt je Symbol Buch: outgoing+stake erhoeht die
    gestakte Menge, incoming+unstake reduziert sie. Der verbleibende Rest ist die
    AKTUELL (noch nicht zurueckgeholte) gestakte Menge - live gegen den echten
    Account verifiziert (2026-07-11).

    existing (optional): wie compute_avg_buy_prices() - Startpunkt fuer
    inkrementelle Folge-Syncs, da sync_avg_buy_prices() nur neue Transaktionen
    seit dem letzten Lauf nachlaedt, nicht die komplette Historie erneut."""
    staked = dict(existing) if existing else {}
    stake_events = [t for t in transactions if t.type == "transfer" and t.cryptocoin_symbol]
    stake_events.sort(key=lambda t: t.unix_timestamp)

    for t in stake_events:
        symbol = t.cryptocoin_symbol
        if "stake" in t.tags and t.in_or_out == "outgoing":
            staked[symbol] = staked.get(symbol, 0.0) + t.amount_cryptocoin_wallet
        elif "unstake" in t.tags and t.in_or_out == "incoming":
            staked[symbol] = max(0.0, staked.get(symbol, 0.0) - t.amount_cryptocoin_wallet)

    return {sym: qty for sym, qty in staked.items() if qty > 0.0001}


@dataclass
class AvgCostSyncResult:
    updated_symbols: list[str] = field(default_factory=list)
    unmatched_bitpanda_symbols: list[str] = field(default_factory=list)
    total_transactions_fetched: int = 0
    incremental: bool = False
    staked_quantities: dict[str, float] = field(default_factory=dict)


def sync_avg_buy_prices(
    conn: sqlite3.Connection,
    api_key: str,
    watchlist: list,
    listed_assets: list[BitpandaAsset],
    on_progress=None,
) -> AvgCostSyncResult:
    """1) alle (neuen) Transaktionen laden - Netzwerk zuerst, kein DB-Write vorher
    (Atomaritaetsprinzip wie importer/bitpanda_sync.py::sync_from_bitpanda). 2)
    Symbol-Mapping ueber das bestehende resolve_bitpanda_symbol_to_watchlist()
    wiederverwenden. 3) compute_avg_buy_prices(), ggf. inkrementell (siehe
    App-Start-/Trigger-Verhalten im Plan). 4) DB-Writes erst danach."""
    last_synced = db.get_bitpanda_avg_cost_last_synced_unix(conn)
    transactions = get_wallet_transactions(api_key, since_unix=last_synced, on_page_fetched=on_progress)

    result = AvgCostSyncResult(total_transactions_fetched=len(transactions), incremental=last_synced is not None)

    existing_holdings = {h.symbol: h for h in db.get_all_holdings(conn)}
    existing_results: dict[str, AvgCostResult] = {}
    if last_synced is not None:
        for symbol, holding in existing_holdings.items():
            if holding.avg_buy_price_eur is not None or holding.avg_buy_price_tracked_qty:
                existing_results[symbol] = AvgCostResult(
                    symbol=symbol,
                    avg_buy_price_eur=holding.avg_buy_price_eur,
                    tracked_quantity=holding.avg_buy_price_tracked_qty or 0.0,
                    buy_count=0,
                    sell_count=0,
                )

    # Bitpanda-Rohsymbole -> interne Watchlist-Symbole abbilden, bevor gerechnet
    # wird (dieselbe Zuordnung wie beim Bestandsabgleich).
    mapped_transactions: list[BitpandaTransaction] = []
    unmatched: set[str] = set()
    for t in transactions:
        if t.cryptocoin_symbol is None:
            continue
        internal_symbol = resolve_bitpanda_symbol_to_watchlist(t.cryptocoin_symbol, watchlist, listed_assets)
        if internal_symbol is None:
            if t.type in _PRICED_TYPES and t.trade_price is not None:
                unmatched.add(t.cryptocoin_symbol)
            continue
        if internal_symbol != t.cryptocoin_symbol:
            t = BitpandaTransaction(
                type=t.type,
                in_or_out=t.in_or_out,
                cryptocoin_symbol=internal_symbol,
                amount_cryptocoin_wallet=t.amount_cryptocoin_wallet,
                unix_timestamp=t.unix_timestamp,
                trade_price=t.trade_price,
                trade_amount_fiat=t.trade_amount_fiat,
                trade_amount_cryptocoin=t.trade_amount_cryptocoin,
                trade_fiat_id=t.trade_fiat_id,
                tags=t.tags,
            )
        mapped_transactions.append(t)
    result.unmatched_bitpanda_symbols = sorted(unmatched)

    computed = compute_avg_buy_prices(mapped_transactions, existing=existing_results)

    existing_staked = {
        symbol: holding.staked_quantity
        for symbol, holding in existing_holdings.items()
        if holding.staked_quantity
    }
    staked = compute_staked_quantities(mapped_transactions, existing=existing_staked)
    result.staked_quantities = staked
    for symbol, qty in staked.items():
        if symbol in existing_holdings:
            db.update_holding_staked_quantity(conn, symbol, qty)
    # Symbole, die frueher gestakt waren, jetzt aber vollstaendig zurueckgeholt sind
    # (qty auf 0 gefallen, daher von compute_staked_quantities() bereits herausgefiltert) -
    # muessen explizit auf 0 zurueckgesetzt werden, sonst bliebe der alte Wert stehen.
    for symbol in existing_staked:
        if symbol not in staked and symbol in existing_holdings:
            db.update_holding_staked_quantity(conn, symbol, 0.0)

    max_unix = last_synced or 0
    for t in transactions:
        if t.unix_timestamp > max_unix:
            max_unix = t.unix_timestamp

    for symbol, avg_result in computed.items():
        if symbol not in existing_holdings:
            continue  # keine Position (mehr) gehalten - kein Sinn, einen Preis zu speichern
        db.update_holding_avg_buy_price(conn, symbol, avg_result.avg_buy_price_eur, avg_result.tracked_quantity)
        result.updated_symbols.append(symbol)

    if transactions or last_synced is None:
        db.set_bitpanda_avg_cost_last_synced_unix(conn, max_unix)

    return result


@dataclass
class CostBasisView:
    effective_avg_price_eur: float | None
    source: str  # "manuell" | "berechnet" | "unbekannt"
    known_quantity: float
    unknown_quantity: float
    cost_basis_eur: float | None
    current_value_eur: float | None
    pl_pct: float | None


def compute_cost_basis_view(holding: Holding, current_price_eur: float | None) -> CostBasisView:
    """Einziger Berechnungsort fuer bekannte/unbekannte Menge + G/V - von
    ui/portfolio.py UND agent/krypto/analyst.py genutzt, keine doppelte Logik.
    known_quantity = min(holding.quantity, tracked_quantity) - siehe Modul-Docstring
    (P-10: unbepreiste Zugaenge werden nie stillschweigend mitgepreist)."""
    effective_price = holding.effective_avg_buy_price_eur
    if holding.avg_buy_price_manual_eur is not None:
        source = "manuell"
    elif holding.avg_buy_price_eur is not None:
        source = "berechnet"
    else:
        source = "unbekannt"

    if effective_price is None:
        known_quantity = 0.0
        unknown_quantity = holding.quantity
    elif source == "manuell":
        # Ein manueller Override gilt fuer den gesamten Bestand (der Nutzer kennt
        # seinen tatsaechlichen Einstand besser als die automatische Teil-Menge).
        known_quantity = holding.quantity
        unknown_quantity = 0.0
    else:
        tracked = holding.avg_buy_price_tracked_qty or 0.0
        known_quantity = min(holding.quantity, tracked)
        unknown_quantity = max(0.0, holding.quantity - known_quantity)

    cost_basis_eur = known_quantity * effective_price if effective_price is not None and known_quantity > 0 else None
    current_value_eur = holding.quantity * current_price_eur if current_price_eur is not None else None

    pl_pct = None
    if cost_basis_eur and known_quantity > 0 and current_price_eur is not None:
        known_value_eur = known_quantity * current_price_eur
        pl_pct = (known_value_eur - cost_basis_eur) / cost_basis_eur * 100

    return CostBasisView(
        effective_avg_price_eur=effective_price,
        source=source,
        known_quantity=known_quantity,
        unknown_quantity=unknown_quantity,
        cost_basis_eur=cost_basis_eur,
        current_value_eur=current_value_eur,
        pl_pct=pl_pct,
    )
