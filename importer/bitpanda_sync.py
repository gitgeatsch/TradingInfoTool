"""Bitpanda-Live-Abgleich der Bestaende (Krypto UND Aktien/ETF/Rohstoffe, siehe
Korrektur unten) + EUR-Fiat-Cash (2026-07-10, Nutzer besitzt bereits einen API-Key).
Bewusst ein DRITTER, unabhaengiger Pfad neben dem bestehenden Excel-Import/-Export
(importer/excel_import.py) - der bleibt vollstaendig als Backup/Fallback erhalten
(Nutzer-Wunsch: Bitpanda hat oefter Ausfaelle).

Korrektur (2026-07-10, vom Nutzer richtiggestellt): urspruenglich als "nur Krypto"
gebaut, da GET /wallets nur die Krypto-Gruppe zeigt - Bitpanda fuehrt aber auch
Aktien/ETF/Rohstoffe im selben Account (GET /asset-wallets, separate Gruppen), live
gegen den echten Account verifiziert (alle 13 Non-Krypto-Watchlist-Assets gefunden).
Beide Wallet-Quellen (api.bitpanda.get_crypto_wallets() + get_non_crypto_wallets())
werden deshalb kombiniert, dieselbe Zuwachs-/Rueckgangs-Logik gilt fuer alle
Assetklassen einheitlich.

Atomaritaet (P-10): ALLE Netzwerk-Aufrufe passieren vor jedem DB-Write. Schlaegt
irgendein Call fehl, propagiert die Exception zum Aufrufer und es wurde noch nichts
in die Datenbank geschrieben - kein Risiko einer teilweisen/inkonsistenten
Aktualisierung."""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field

import config
import database.db as db
from api.bitpanda import (
    BitpandaAsset,
    get_crypto_wallets,
    get_fiat_wallets,
    get_non_crypto_wallets,
    resolve_bitpanda_symbol_to_watchlist,
)

SOURCE_BITPANDA_SYNC = "bitpanda_sync"
FIAT_SYMBOL = "EUR"

# R-5.7/Umsetzungs-Rueckmeldung (ui/signals_view.py::UmsetzungDialog): welche Aktionen
# sich per einfachem Richtungsvergleich (Menge gestiegen/gesunken) einem Bestands-
# wechsel zuordnen lassen. TAUSCHEN bewusst ausgeklammert (beträfe zwei Symbole
# gleichzeitig, fehleranfaelliger) - bleibt weiterhin nur manuell ueber den
# bestehenden UmsetzungDialog bestaetigbar.
_KAUF_AKTIONEN = {"KAUFEN", "NACHKAUFEN"}
_VERKAUF_AKTIONEN = {"VERKAUFEN"}


@dataclass
class PlausibleSignalMatch:
    signal_id: int
    symbol: str
    action: str
    alt_menge: float
    neu_menge: float
    signal_datum: str | None


@dataclass
class DecreaseCandidate:
    """Ein von Bitpanda gemeldeter RUECKGANG (2026-07-10, live entdeckt) - wird NIE
    automatisch geschrieben. Grund: gestakte Bestaende sind ueber diese API nicht
    auslesbar (live gegen 3 Endpunkte geprueft, keiner liefert einen Staking-Wert) -
    ein Rueckgang kann also ein echter Verkauf ODER ein reines API-Sichtfeld-Problem
    (Staking) sein. Nur der Nutzer kann das unterscheiden (ui/app.py::
    BitpandaDecreaseConfirmDialog). Zuwaechse bleiben davon unberuehrt und werden wie
    bisher automatisch geschrieben (dort gibt es kein aequivalentes Blindspot-Risiko)."""

    symbol: str
    alt_menge: float
    neu_menge: float
    matching_signal_id: int | None = None
    matching_signal_action: str | None = None
    matching_signal_datum: str | None = None


@dataclass
class BitpandaSyncResult:
    synced_count: int = 0
    updated_holdings: list[str] = field(default_factory=list)
    cash_reserve_updated: bool = False
    cash_reserve_old_eur: float | None = None
    cash_reserve_new_eur: float | None = None
    unmatched_bitpanda_symbols: list[str] = field(default_factory=list)
    stale_bitpanda_sync_symbols: list[str] = field(default_factory=list)
    plausible_signal_matches: list[PlausibleSignalMatch] = field(default_factory=list)
    decreased_holdings_needs_confirmation: list[DecreaseCandidate] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def sync_from_bitpanda(
    conn: sqlite3.Connection, api_key: str, listed_assets: list[BitpandaAsset]
) -> BitpandaSyncResult:
    watchlist = config.get_watchlist()
    watchlist_symbols = {a.symbol for a in watchlist}

    # Netzwerk-Aufrufe zuerst - noch keine DB-Schreibung (Atomaritaet, siehe Docstring).
    fiat_wallets = get_fiat_wallets(api_key)
    # Krypto- UND Non-Krypto-Wallets kombiniert (2026-07-10, Korrektur: Bitpanda
    # fuehrt Aktien/ETF/Rohstoffe im selben Account) - dieselbe Zuwachs-/Rueckgangs-
    # Logik unten gilt fuer alle Assetklassen einheitlich.
    all_wallets = get_crypto_wallets(api_key) + get_non_crypto_wallets(api_key)

    result = BitpandaSyncResult()
    existing_holdings = {h.symbol: h for h in db.get_all_holdings(conn)}

    # --- EUR-Fiat-Cash ---
    eur_wallet = next((w for w in fiat_wallets if w.symbol == FIAT_SYMBOL), None)
    if eur_wallet is not None:
        old_cash = db.get_cash_reserve_fiat_eur(conn)
        if old_cash != eur_wallet.balance:
            db.set_cash_reserve_fiat_eur(conn, eur_wallet.balance)
            result.cash_reserve_updated = True
            result.cash_reserve_old_eur = old_cash
            result.cash_reserve_new_eur = eur_wallet.balance

    # --- Bestaende (Krypto + Aktien/ETF/Rohstoffe, siehe Modul-Docstring) ---
    matched_symbols: set[str] = set()
    for wallet in all_wallets:
        internal_symbol = resolve_bitpanda_symbol_to_watchlist(wallet.symbol, watchlist, listed_assets)
        if internal_symbol is None:
            if wallet.balance > 0:
                result.unmatched_bitpanda_symbols.append(f"{wallet.symbol} ({wallet.balance:g})")
            continue
        if internal_symbol not in watchlist_symbols:
            # Sollte durch resolve_bitpanda_symbol_to_watchlist() nicht vorkommen
            # (das Symbol kommt ja aus der watchlist selbst), aber defensiv
            # geprueft (P-10).
            continue

        matched_symbols.add(internal_symbol)
        existing = existing_holdings.get(internal_symbol)
        alt_menge = existing.quantity if existing else 0.0
        neu_menge = wallet.balance

        if neu_menge > alt_menge:
            # Zuwachs: automatisch schreiben, kein Blindspot-Risiko (im Gegensatz zu
            # Rueckgaengen kann ein Zuwachs nicht durch fehlende Staking-Sichtbarkeit
            # vorgetaeuscht werden).
            alte_quelle = existing.source if existing else "keiner"
            result.updated_holdings.append(
                f"{internal_symbol}: {alt_menge:g} -> {neu_menge:g} (bisherige Quelle: {alte_quelle})"
            )
            db.upsert_holding(conn, internal_symbol, neu_menge, source=SOURCE_BITPANDA_SYNC)
            result.synced_count += 1

            latest_signal = db.get_latest_signal(conn, internal_symbol)
            if (
                latest_signal is not None
                and latest_signal.umgesetzt is None
                and latest_signal.action in _KAUF_AKTIONEN
            ):
                result.plausible_signal_matches.append(
                    PlausibleSignalMatch(
                        signal_id=latest_signal.id,
                        symbol=internal_symbol,
                        action=latest_signal.action,
                        alt_menge=alt_menge,
                        neu_menge=neu_menge,
                        signal_datum=latest_signal.created_at,
                    )
                )
        elif neu_menge < alt_menge:
            # Rueckgang: NIE automatisch schreiben (siehe DecreaseCandidate-Docstring -
            # live entdeckt, dass gestakte Bestaende hier faelschlich als Rueckgang/0
            # erscheinen). Nur zur Bestaetigung vorgemerkt.
            matching_signal_id = None
            matching_signal_action = None
            matching_signal_datum = None
            latest_signal = db.get_latest_signal(conn, internal_symbol)
            if (
                latest_signal is not None
                and latest_signal.umgesetzt is None
                and latest_signal.action in _VERKAUF_AKTIONEN
            ):
                matching_signal_id = latest_signal.id
                matching_signal_action = latest_signal.action
                matching_signal_datum = latest_signal.created_at
            result.decreased_holdings_needs_confirmation.append(
                DecreaseCandidate(
                    symbol=internal_symbol,
                    alt_menge=alt_menge,
                    neu_menge=neu_menge,
                    matching_signal_id=matching_signal_id,
                    matching_signal_action=matching_signal_action,
                    matching_signal_datum=matching_signal_datum,
                )
            )

    # Symbole, die FRUEHER per Sync gesetzt wurden, aber jetzt fehlen (z.B. Wallet
    # geloescht/API liefert sie nicht mehr) - nur gemeldet, NICHT automatisch auf 0
    # gesetzt (unbekannt != verkauft, P-10).
    for symbol, holding in existing_holdings.items():
        if holding.source == SOURCE_BITPANDA_SYNC and symbol in watchlist_symbols and symbol not in matched_symbols:
            result.stale_bitpanda_sync_symbols.append(symbol)

    return result


def apply_decrease(conn: sqlite3.Connection, candidate: DecreaseCandidate) -> None:
    """Schreibt einen vom Nutzer BESTAETIGTEN Rueckgang (ui/app.py::
    BitpandaDecreaseConfirmDialog) - erst hier, nie automatisch im Sync selbst. Wenn
    der Rueckgang zu einem offenen VERKAUFEN-Signal passt, wird das gleich mit
    bestaetigt (ein Bestaetigungsschritt statt zwei getrennte)."""
    db.upsert_holding(conn, candidate.symbol, candidate.neu_menge, source=SOURCE_BITPANDA_SYNC)
    if candidate.matching_signal_id is not None:
        db.update_signal_umsetzung(
            conn, candidate.matching_signal_id, True, umgesetzt_menge=candidate.neu_menge
        )
