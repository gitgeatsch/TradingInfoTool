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
Aktualisierung. Ausnahme, bewusst dokumentiert (siehe Staking-Verifikation unten):
der optionale Transaktions-Abruf fuer die Staking-Erkennung darf fuer sich allein
fehlschlagen, OHNE den gesamten Sync abzubrechen - er degradiert dann nur auf die
alte, konservative Rueckgangs-Bestaetigung. Kein DB-Write geschieht, bevor ALLE
(auch dieser optionale) Netzwerk-Aufrufe abgeschlossen sind.

Staking-Verifikation (2026-07-16, Nutzer-Frage "kauf/verkauf erfolgt nur durch
den Nutzer selbst - wo ist das Risiko?"): das eigentliche Risiko war nie, WER die
Aenderung ausloest (das ist immer der Nutzer, per Trade oder Limit-Order), sondern
dass Bitpandas Live-Bestands-API einen echten Verkauf nicht von einem Staking-
Transfer unterscheiden kann (beide erscheinen identisch als Rueckgang im
sichtbaren Wallet-Guthaben, siehe DecreaseCandidate-Docstring). Diese Ambiguitaet
ist aber bereits an anderer Stelle geloest: `importer/bitpanda_avg_cost.py::
compute_staked_quantities()` rekonstruiert aus der Transaktionshistorie (stake/
unstake-Tags), wie viel aktuell gestakt ist - bisher nur beim manuellen
"Einstandspreise berechnen"-Button genutzt. Wird dieselbe Berechnung inkrementell
(EIGENER Cursor, siehe db.py::get/set_bitpanda_holdings_last_synced_unix() -
bewusst NICHT derselbe Schluessel wie bitpanda_avg_cost_last_synced_unix, sonst
wuerden sich beide Features gegenseitig Transaktionen "wegkonsumieren") auch hier
aufgerufen, lassen sich BEIDE Richtungen sicher automatisch schreiben: `quantity`
kommt direkt vom Live-Wallet-Saldo, `staked_quantity` direkt aus der
Transaktionshistorie - beide unabhaengig korrekt, keine Interpretation "war das
ein Verkauf?" mehr noetig. Nur wenn der Transaktions-Abruf selbst fehlschlaegt
(z.B. Netzwerkfehler), bleibt der alte, konservative Bestaetigungs-Weg als
Fallback erhalten."""
from __future__ import annotations

import logging
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone

import config
import database.db as db
from api.bitpanda import (
    BitpandaAsset,
    BitpandaTransaction,
    get_crypto_wallets,
    get_fiat_wallets,
    get_non_crypto_wallets,
    get_wallet_transactions,
    resolve_bitpanda_symbol_to_watchlist,
)
from importer.bitpanda_avg_cost import compute_staked_quantities

logger = logging.getLogger(__name__)

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
    """Ein von Bitpanda gemeldeter RUECKGANG (2026-07-10, live entdeckt).

    Seit 2026-07-16 nur noch der FALLBACK-Pfad: wenn die Staking-Verifikation
    (siehe Modul-Docstring) erfolgreich war, wird ein Rueckgang direkt per
    apply_decrease() automatisch geschrieben (quantity + staked_quantity beide
    unabhaengig korrekt) - `DecreaseCandidate` wird dann gar nicht erst erzeugt.
    Nur wenn der Transaktions-Abruf selbst fehlschlaegt (z.B. Netzwerkfehler),
    bleibt diese Klasse und der Bestaetigungs-Dialog (ui/app.py::
    BitpandaDecreaseConfirmDialog) als konservativer Rueckfallweg bestehen -
    ohne Transaktionshistorie kann ein echter Verkauf nicht sicher von einem
    Staking-Transfer unterschieden werden (beide erscheinen identisch als
    Rueckgang im sichtbaren Wallet-Guthaben). Zuwaechse bleiben davon unberuehrt
    und werden weiterhin immer automatisch geschrieben."""

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
    # 2026-07-16 (Staking-Verifikation, siehe Modul-Docstring): True, wenn der
    # inkrementelle Transaktions-Abruf fuer die Staking-Erkennung erfolgreich
    # war - dann wurden Rueckgaenge in DIESEM Lauf automatisch uebernommen
    # (siehe auto_confirmed_decreases), NICHT zur Bestaetigung vorgemerkt.
    staking_verified: bool = False
    auto_confirmed_decreases: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class BitpandaCashSyncResult:
    updated: bool = False
    old_eur: float | None = None
    new_eur: float | None = None


def sync_fiat_cash_from_bitpanda(conn: sqlite3.Connection, api_key: str) -> BitpandaCashSyncResult:
    """Nur der EUR-Fiat-Cash-Anteil von sync_from_bitpanda() - extrahiert
    (2026-07-11), urspruenglich damit ein automatischer Scheduler-Job diesen
    Teil regelmaessig nachziehen konnte, OHNE die volle Bestaende-Sync-Logik
    (inkl. interaktivem Rueckgangs-Bestaetigungsdialog) aus einem Hintergrund-
    Thread aufzurufen. Seit 2026-07-16 (Staking-Verifikation, siehe
    sync_from_bitpanda()-Modul-Docstring) ruft `scheduler/background.py::
    refresh_bitpanda_holdings_job()` direkt die volle sync_from_bitpanda() auf
    (kein separater Cash-only-Job mehr noetig, da der interaktive Dialog jetzt
    nur noch ein seltener Fallback ist) - diese Funktion bleibt als isolierter
    Cash-Baustein bestehen, sync_from_bitpanda() ruft sie weiterhin intern auf,
    keine Logik-Duplikation."""
    result = BitpandaCashSyncResult()
    fiat_wallets = get_fiat_wallets(api_key)
    eur_wallet = next((w for w in fiat_wallets if w.symbol == FIAT_SYMBOL), None)
    if eur_wallet is not None:
        old_cash = db.get_cash_reserve_fiat_eur(conn)
        if old_cash != eur_wallet.balance:
            db.set_cash_reserve_fiat_eur(conn, eur_wallet.balance)
            result.updated = True
            result.old_eur = old_cash
            result.new_eur = eur_wallet.balance
        # Zeitstempel IMMER setzen, auch wenn sich der Wert nicht geaendert hat -
        # das beantwortet "wann haben wir zuletzt tatsaechlich nachgefragt", nicht
        # nur "wann hat sich etwas geaendert" (2026-07-11, Nutzer-Fund: Bitpanda
        # sperrt fuer offene Fusion-Limit-Orders reservierte Betraege sofort aus
        # dem Wallet-Guthaben, ohne dass die App das mitbekommt - siehe
        # db.get_cash_reserve_synced_at()-Docstring).
        db.set_cash_reserve_synced_at(conn, datetime.now(timezone.utc).isoformat())
    return result


def _map_transactions_to_internal_symbols(
    transactions: list[BitpandaTransaction], watchlist: list, listed_assets: list[BitpandaAsset],
) -> list[BitpandaTransaction]:
    """Bildet Bitpanda-Rohsymbole auf interne Watchlist-Symbole ab - dieselbe
    Zuordnung wie beim Bestandsabgleich (resolve_bitpanda_symbol_to_watchlist()).
    Bewusst eine LOKALE Kopie der Mapping-Logik aus bitpanda_avg_cost.py::
    sync_avg_buy_prices() (statt geteilt) - vermeidet jedes Risiko einer
    Regression in der dortigen, bereits produktiv laufenden Einstandspreis-
    Berechnung, siehe Modul-Docstring dort ("schuetzt vor Regressionen").
    Transaktionen ohne cryptocoin_symbol oder ohne Watchlist-Zuordnung werden
    verworfen (P-10: eine unbekannte Zuordnung darf nicht geraten werden)."""
    mapped: list[BitpandaTransaction] = []
    for t in transactions:
        if t.cryptocoin_symbol is None:
            continue
        internal_symbol = resolve_bitpanda_symbol_to_watchlist(t.cryptocoin_symbol, watchlist, listed_assets)
        if internal_symbol is None:
            continue
        if internal_symbol != t.cryptocoin_symbol:
            t = BitpandaTransaction(
                type=t.type, in_or_out=t.in_or_out, cryptocoin_symbol=internal_symbol,
                amount_cryptocoin_wallet=t.amount_cryptocoin_wallet, unix_timestamp=t.unix_timestamp,
                trade_price=t.trade_price, trade_amount_fiat=t.trade_amount_fiat,
                trade_amount_cryptocoin=t.trade_amount_cryptocoin, trade_fiat_id=t.trade_fiat_id, tags=t.tags,
            )
        mapped.append(t)
    return mapped


def sync_from_bitpanda(
    conn: sqlite3.Connection, api_key: str, listed_assets: list[BitpandaAsset]
) -> BitpandaSyncResult:
    watchlist = config.get_watchlist()
    watchlist_symbols = {a.symbol for a in watchlist}

    # Netzwerk-Aufrufe zuerst - noch keine DB-Schreibung (Atomaritaet, siehe Docstring).
    # Fiat-Cash separat via sync_fiat_cash_from_bitpanda() (macht dort selbst den
    # get_fiat_wallets()-Call und die DB-Schreibung - kein Bruch der Atomaritaets-
    # Garantie hier, da dieser Teil ohnehin unabhaengig von den Bestaenden ist).
    # Krypto- UND Non-Krypto-Wallets kombiniert (2026-07-10, Korrektur: Bitpanda
    # fuehrt Aktien/ETF/Rohstoffe im selben Account) - dieselbe Zuwachs-/Rueckgangs-
    # Logik unten gilt fuer alle Assetklassen einheitlich.
    all_wallets = get_crypto_wallets(api_key) + get_non_crypto_wallets(api_key)

    result = BitpandaSyncResult()
    existing_holdings = {h.symbol: h for h in db.get_all_holdings(conn)}

    # --- Staking-Verifikation (2026-07-16, siehe Modul-Docstring) ---
    # EIGENER, unabhaengiger Netzwerk-Aufruf - schlaegt er fehl, degradiert NUR
    # dieser Teil (Rueckgaenge bleiben dann bestaetigungspflichtig, siehe unten),
    # der Rest des Syncs (Zuwaechse, Cash) laeuft unveraendert weiter.
    staking_verified = False
    new_staked: dict[str, float] = {}
    existing_staked = {
        symbol: h.staked_quantity for symbol, h in existing_holdings.items() if h.staked_quantity
    }
    last_holdings_synced = db.get_bitpanda_holdings_last_synced_unix(conn)
    raw_transactions: list[BitpandaTransaction] = []
    try:
        raw_transactions = get_wallet_transactions(api_key, since_unix=last_holdings_synced)
        mapped_transactions = _map_transactions_to_internal_symbols(raw_transactions, watchlist, listed_assets)
        new_staked = compute_staked_quantities(mapped_transactions, existing=existing_staked)
        staking_verified = True
    except Exception as exc:
        logger.info(
            "Staking-Verifikation (Transaktions-Abruf) fehlgeschlagen - Rückgänge "
            "bleiben in diesem Lauf bestätigungspflichtig: %s", exc,
        )

    # --- EUR-Fiat-Cash ---
    cash_result = sync_fiat_cash_from_bitpanda(conn, api_key)
    result.cash_reserve_updated = cash_result.updated
    result.cash_reserve_old_eur = cash_result.old_eur
    result.cash_reserve_new_eur = cash_result.new_eur

    # --- Bestaende (Krypto + Aktien/ETF/Rohstoffe, siehe Modul-Docstring) ---
    matched_symbols: set[str] = set()
    # Symbole, fuer die in DIESEM Lauf tatsaechlich eine holdings-Zeile geschrieben
    # wurde (Bugfix: NICHT dasselbe wie matched_symbols - ein Symbol mit
    # alt_menge == neu_menge == 0 landet zwar in matched_symbols, bekommt aber
    # KEINEN db.upsert_holding()-Aufruf, siehe staked_quantity-Persistenz unten).
    rows_written: set[str] = set()
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
            rows_written.add(internal_symbol)
            result.synced_count += 1

            # Klassifikations-Redesign (2026-07-16): keine Status-Auto-
            # Hochstufung mehr hier - "gehalten" wird jetzt ueberall live aus
            # den echten Bestaenden abgeleitet (siehe config.py::
            # WatchlistAsset-Docstring), es gibt also nichts mehr, das beim
            # Kauf synchronisiert werden muesste.

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
            # Rueckgang: Ambiguitaet ("echter Verkauf ODER Staking-Transfer?") ist
            # geloest, WENN die Staking-Verifikation oben erfolgreich war - dann
            # kommt quantity direkt vom Live-Wallet-Saldo UND staked_quantity
            # unabhaengig aus der Transaktionshistorie, beide fuer sich korrekt
            # (siehe Modul-Docstring). Nur wenn der Transaktions-Abruf selbst
            # fehlschlug, bleibt der alte, konservative Bestaetigungs-Weg.
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
            candidate = DecreaseCandidate(
                symbol=internal_symbol,
                alt_menge=alt_menge,
                neu_menge=neu_menge,
                matching_signal_id=matching_signal_id,
                matching_signal_action=matching_signal_action,
                matching_signal_datum=matching_signal_datum,
            )
            if staking_verified:
                apply_decrease(conn, candidate)
                rows_written.add(internal_symbol)
                result.synced_count += 1
                hinweis = " (VERKAUFEN-Signal automatisch bestätigt)" if matching_signal_id else ""
                result.auto_confirmed_decreases.append(
                    f"{internal_symbol}: {alt_menge:g} -> {neu_menge:g}{hinweis}"
                )
            else:
                result.decreased_holdings_needs_confirmation.append(candidate)

    # Symbole, die FRUEHER per Sync gesetzt wurden, aber jetzt fehlen (z.B. Wallet
    # geloescht/API liefert sie nicht mehr) - nur gemeldet, NICHT automatisch auf 0
    # gesetzt (unbekannt != verkauft, P-10).
    for symbol, holding in existing_holdings.items():
        if holding.source == SOURCE_BITPANDA_SYNC and symbol in watchlist_symbols and symbol not in matched_symbols:
            result.stale_bitpanda_sync_symbols.append(symbol)

    result.staking_verified = staking_verified
    if staking_verified:
        # staked_quantity fuer jedes betroffene Symbol persistieren (identisches
        # Muster wie bitpanda_avg_cost.py::sync_avg_buy_prices()) - nur fuer
        # Symbole mit einer bestehenden ODER in diesem Lauf neu angelegten
        # holdings-Zeile (ein Symbol ohne jede Position braucht keinen
        # staked_quantity-Eintrag).
        bekannte_symbole = set(existing_holdings) | rows_written
        for symbol, qty in new_staked.items():
            if symbol not in bekannte_symbole:
                # Randfall (Bugfix): ein Symbol, das schon VOR dieser App
                # komplett gestakt war (Live-Wallet-Saldo also immer 0, nie
                # ein Zuwachs/Rueckgang ausgeloest, daher nie eine holdings-
                # Zeile angelegt) - ohne diese Basis-Zeile wuerde die folgende
                # UPDATE-Anweisung ins Leere laufen (0 betroffene Zeilen,
                # staked_quantity ginge stillschweigend verloren).
                db.upsert_holding(conn, symbol, 0.0, source=SOURCE_BITPANDA_SYNC)
                bekannte_symbole.add(symbol)
            db.update_holding_staked_quantity(conn, symbol, qty)
        # Symbole, die FRUEHER gestakt waren, jetzt aber vollstaendig zurueckgeholt
        # sind (compute_staked_quantities() filtert 0-Werte bereits heraus) -
        # muessen explizit auf 0 zurueckgesetzt werden, sonst bliebe der alte
        # Wert stehen.
        for symbol in existing_staked:
            if symbol not in new_staked and symbol in bekannte_symbole:
                db.update_holding_staked_quantity(conn, symbol, 0.0)

        max_unix_holdings = last_holdings_synced or 0
        for t in raw_transactions:
            if t.unix_timestamp > max_unix_holdings:
                max_unix_holdings = t.unix_timestamp
        if raw_transactions or last_holdings_synced is None:
            db.set_bitpanda_holdings_last_synced_unix(conn, max_unix_holdings)

    return result


def apply_decrease(conn: sqlite3.Connection, candidate: DecreaseCandidate) -> None:
    """Schreibt einen Rueckgang. Zwei Aufrufer seit 2026-07-16: (1) ui/app.py::
    BitpandaDecreaseConfirmDialog nach einer vom NUTZER bestaetigten Auswahl
    (Fallback-Pfad, Staking-Verifikation fehlgeschlagen), (2) sync_from_bitpanda()
    selbst, AUTOMATISCH, wenn die Staking-Verifikation erfolgreich war (siehe
    dortigen Modul-Docstring - dann ist die Unterscheidung "echter Verkauf vs.
    Staking-Transfer" bereits sicher aufgeloest, keine Nutzer-Bestaetigung mehr
    noetig). Wenn der Rueckgang zu einem offenen VERKAUFEN-Signal passt, wird das gleich mit
    bestaetigt (ein Bestaetigungsschritt statt zwei getrennte)."""
    db.upsert_holding(conn, candidate.symbol, candidate.neu_menge, source=SOURCE_BITPANDA_SYNC)
    if candidate.matching_signal_id is not None:
        db.update_signal_umsetzung(
            conn, candidate.matching_signal_id, True, umgesetzt_menge=candidate.neu_menge
        )
