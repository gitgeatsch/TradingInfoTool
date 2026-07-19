"""Rekonstruiert echte Bitpanda-Margin-Positions-Lebenszyklen aus der Transaktions-
historie (2026-07-14, Hebel-Phase 3, siehe docs/hebel_positionsformel.md). Portiert
die bereits gegen die komplette echte Transaktionshistorie verifizierte Scratchpad-
Logik (reconstruct_margin_positions.py/detect_liquidations.py) 1:1 in wieder-
verwendbaren, inkrementell-syncfaehigen Code (185 echte Positionen reproduziert,
siehe Regressionstest + docs/hebel_positionsformel.md fuer den 311-vs-185-Fund).

Bitpanda kennzeichnet Liquidationen NICHT separat (identisches Tag wie ein
normaler Close) - `status='wahrscheinlich_liquidiert'` ist ein statistischer
Befund (Gebuehren-Anomalie: tatsaechliche Verkaufsgebuehr weicht > 0,7
Prozentpunkte von der erwarteten 0,3% + 0,18%/Tag-Formel ab), keine von
Bitpanda bestaetigte Tatsache.

Anders als importer/bitpanda_avg_cost.py::compute_avg_buy_prices() (das nur
skalare Werte ueber Sync-Laeufe traegt) gibt es hier kein einfaches Akkumulator-
Objekt als Vorbild - eine offene Margin-Position ist eine mehrstufige Sequenz
(open -> ggf. weitere opens/Nachkaeufe -> close). Die `hebel_positions`-Tabelle
(Zeilen mit status='offen') ist deshalb selbst der Zustandsspeicher zwischen
inkrementellen Syncs, uebergeben als `existing`-Parameter."""
from __future__ import annotations

import logging
import sqlite3
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone

import config as config_module
import database.db as db
from api.bitpanda import BitpandaAsset, BitpandaTransaction, find_listed_asset, get_wallet_transactions, is_listed
from database.models import HebelPosition

logger = logging.getLogger(__name__)

# Bitpanda-Doku-Angabe: 0,3% Verkaufsgebuehr + 0,18%/Tag laufende Kreditgebuehr.
# Eine tatsaechliche Gebuehr, die mehr als diese Marge darueber liegt, deckt sich
# fast exakt mit Bitpandas dokumentierter 1%-Zwangsliquidationsgebuehr (empirisch
# an 4 Faellen bestaetigt, siehe docs/hebel_positionsformel.md).
_ERWARTETE_GEBUEHR_BASIS_PROZENT = 0.3
_ERWARTETE_GEBUEHR_PRO_TAG_PROZENT = 0.18
_LIQUIDATIONS_VERDACHT_SCHWELLE_PROZENTPUNKTE = 0.7


def _unix_to_iso(unix_timestamp: int) -> str:
    return datetime.fromtimestamp(unix_timestamp, tz=timezone.utc).isoformat()


def _iso_to_unix(iso: str) -> int:
    return int(datetime.fromisoformat(iso).timestamp())


@dataclass
class ReconstructionResult:
    offene_positionen: dict[str, HebelPosition] = field(default_factory=dict)
    neu_geschlossene_positionen: list[HebelPosition] = field(default_factory=list)
    # Symbole, die in DIESEM Aufruf mindestens ein margin-Ereignis hatten (fuer
    # sync_hebel_positions(), um nur tatsaechlich veraenderte offene Positionen
    # erneut zu schreiben statt aller unveraendert durchgereichten `existing`-Eintraege).
    aktualisierte_offene_symbole: set[str] = field(default_factory=set)


def reconstruct_margin_positions(
    transactions: list[BitpandaTransaction],
    existing: dict[str, HebelPosition] | None = None,
) -> ReconstructionResult:
    """Reine Funktion, keine DB-/Netzwerk-Zugriffe (wie compute_avg_buy_prices()).

    1. Nur Transaktionen mit einem "margin"-Tag beruecksichtigen.
    2. Nach unix_timestamp gruppieren - mehrere Zeilen mit identischem Zeitstempel
       (Kauf-Leg + Kredit-Leg + Gegenwert-Verkaufs-Leg) bilden EIN Ereignis.
    3. Je Zeitstempel-Gruppe: symbol = cryptocoin_symbol ungleich "EURCV"; kind =
       "close" wenn ein Tag "close" enthaelt, sonst "open" wenn ein Tag "open"
       enthaelt, sonst wird das Ereignis ignoriert.
    4. Chronologisch pro Symbol: "open" akkumuliert buy_value/borrow (setzt auf
       `existing[symbol]` auf, falls dort eine offene Position liegt); "close"
       berechnet Eigenkapital/effektiven Hebel + Gebuehren-Anomalie-Check und
       schliesst die Position ab.
    """
    margin_txs = [t for t in transactions if any("margin" in tag.lower() for tag in t.tags)]

    by_ts: dict[int, list[BitpandaTransaction]] = defaultdict(list)
    for t in margin_txs:
        by_ts[t.unix_timestamp].append(t)

    events_by_symbol: dict[str, list[dict]] = defaultdict(list)
    for ts, group in sorted(by_ts.items()):
        tags_flat = [tg.lower() for t in group for tg in t.tags]
        symbol = next(
            (t.cryptocoin_symbol for t in group if t.cryptocoin_symbol and t.cryptocoin_symbol != "EURCV"),
            None,
        )
        if symbol is None:
            continue
        if any("close" in tg for tg in tags_flat):
            kind = "close"
        elif any("open" in tg for tg in tags_flat):
            kind = "open"
        else:
            continue
        buy_leg = [t for t in group if t.type == "buy" and t.in_or_out == "incoming" and t.cryptocoin_symbol == symbol]
        sell_leg = [t for t in group if t.type == "sell" and t.cryptocoin_symbol == symbol]
        borrow_leg = [t for t in group if any("borrow" in tg.lower() for tg in t.tags)]
        fee_leg = [t for t in group if any("fee" in tg.lower() for tg in t.tags)]
        events_by_symbol[symbol].append(
            {
                "ts": ts,
                "kind": kind,
                "buy_value": sum(t.trade_amount_fiat or 0.0 for t in buy_leg),
                "buy_qty": sum(t.trade_amount_cryptocoin or 0.0 for t in buy_leg),
                "borrow": sum(t.amount_cryptocoin_wallet for t in borrow_leg),
                "fee_crypto": sum(abs(t.amount_cryptocoin_wallet) for t in fee_leg),
                "sell_value": sum(t.trade_amount_fiat or 0.0 for t in sell_leg),
                "sell_price": sell_leg[0].trade_price if sell_leg else None,
            }
        )

    offene: dict[str, HebelPosition] = dict(existing) if existing else {}
    neu_geschlossen: list[HebelPosition] = []
    aktualisierte_symbole: set[str] = set(events_by_symbol.keys())

    for symbol, events in events_by_symbol.items():
        events.sort(key=lambda e: e["ts"])
        state = offene.get(symbol)
        running_value = state.positionswert_eur or 0.0 if state else 0.0
        running_borrow = state.kreditbetrag_eur or 0.0 if state else 0.0
        running_qty = state.positionsmenge or 0.0 if state else 0.0
        opened_at_unix = _iso_to_unix(state.eroeffnet_am) if state else None
        opened_at_iso = state.eroeffnet_am if state else None
        last_ts = state.letzte_transaktion_unix_timestamp if state else None

        for e in events:
            if e["kind"] == "open":
                if opened_at_unix is None:
                    opened_at_unix = e["ts"]
                    opened_at_iso = _unix_to_iso(e["ts"])
                running_value += e["buy_value"]
                running_borrow += e["borrow"]
                running_qty += e["buy_qty"]
                last_ts = e["ts"]
            elif e["kind"] == "close" and opened_at_unix is not None:
                eigenkapital = running_value - running_borrow
                hebel = running_value / eigenkapital if eigenkapital > 0 else None
                haltedauer_tage = (e["ts"] - opened_at_unix) / 86400
                status = "geschlossen"
                if e["sell_price"] and e["sell_value"]:
                    fee_eur = e["fee_crypto"] * e["sell_price"]
                    fee_pct_tatsaechlich = fee_eur / e["sell_value"] * 100
                    erwartet_pct = _ERWARTETE_GEBUEHR_BASIS_PROZENT + _ERWARTETE_GEBUEHR_PRO_TAG_PROZENT * haltedauer_tage
                    if (fee_pct_tatsaechlich - erwartet_pct) > _LIQUIDATIONS_VERDACHT_SCHWELLE_PROZENTPUNKTE:
                        status = "wahrscheinlich_liquidiert"
                neu_geschlossen.append(
                    HebelPosition(
                        symbol=symbol,
                        richtung="LONG",
                        status=status,
                        eroeffnet_am=opened_at_iso,
                        geschlossen_am=_unix_to_iso(e["ts"]),
                        hebel_effektiv=round(hebel, 4) if hebel is not None else None,
                        positionswert_eur=round(running_value, 2),
                        kreditbetrag_eur=round(running_borrow, 2),
                        eigenkapital_eur=round(eigenkapital, 2),
                        positionsmenge=round(running_qty, 8) if running_qty else None,
                        letzte_transaktion_unix_timestamp=e["ts"],
                    )
                )
                offene.pop(symbol, None)
                running_value, running_borrow, running_qty = 0.0, 0.0, 0.0
                opened_at_unix, opened_at_iso, last_ts = None, None, None

        if opened_at_unix is not None and running_value > 0:
            eigenkapital = running_value - running_borrow
            hebel = running_value / eigenkapital if eigenkapital > 0 else None
            offene[symbol] = HebelPosition(
                symbol=symbol,
                richtung="LONG",
                status="offen",
                eroeffnet_am=opened_at_iso,
                hebel_effektiv=round(hebel, 4) if hebel is not None else None,
                positionswert_eur=round(running_value, 2),
                kreditbetrag_eur=round(running_borrow, 2),
                eigenkapital_eur=round(eigenkapital, 2),
                positionsmenge=round(running_qty, 8) if running_qty else None,
                letzte_transaktion_unix_timestamp=last_ts,
            )

    return ReconstructionResult(
        offene_positionen=offene,
        neu_geschlossene_positionen=neu_geschlossen,
        aktualisierte_offene_symbole=aktualisierte_symbole,
    )


@dataclass
class HebelPositionSyncResult:
    positionen_aktualisiert: list[str] = field(default_factory=list)
    neu_geschlossen: int = 0
    total_transactions_fetched: int = 0
    incremental: bool = False


def sync_hebel_positions(conn: sqlite3.Connection, api_key: str) -> HebelPositionSyncResult:
    """1) (neue) Transaktionen laden - Netzwerk zuerst, kein DB-Write vorher
    (Atomaritaetsprinzip wie importer/bitpanda_sync.py/bitpanda_avg_cost.py). 2)
    offene Positionen aus der DB als `existing`-Akkumulator reconstruieren. 3)
    reconstruct_margin_positions() aufrufen. 4) Ergebnisse upserten, Watermark
    fortschreiben."""
    last_synced = db.get_hebel_position_last_synced_unix(conn)
    transactions = get_wallet_transactions(api_key, since_unix=last_synced)

    result = HebelPositionSyncResult(
        total_transactions_fetched=len(transactions),
        incremental=last_synced is not None,
    )

    existing = {p.symbol: p for p in db.get_open_hebel_positions(conn)}
    recon = reconstruct_margin_positions(transactions, existing=existing)

    for pos in recon.neu_geschlossene_positionen:
        db.upsert_hebel_position(conn, pos)
        result.positionen_aktualisiert.append(pos.symbol)
    result.neu_geschlossen = len(recon.neu_geschlossene_positionen)

    for symbol in recon.aktualisierte_offene_symbole:
        pos = recon.offene_positionen.get(symbol)
        if pos is not None:
            db.upsert_hebel_position(conn, pos)
            result.positionen_aktualisiert.append(symbol)

    max_unix = last_synced or 0
    for t in transactions:
        if t.unix_timestamp > max_unix:
            max_unix = t.unix_timestamp
    if transactions or last_synced is None:
        db.set_hebel_position_last_synced_unix(conn, max_unix)

    return result


def auto_add_unknown_hebel_symbols(
    conn: sqlite3.Connection, watchlist: list, listed_assets: list[BitpandaAsset], coingecko_client=None
) -> list[str]:
    """Automatische Watchlist-Ergaenzung fuer Hebel-Symbole ohne Watchlist-
    Eintrag (2026-07-16, Klassifikations-Redesign, Nutzer-Frage "werden neue
    Hebel-Assets bereits automatisch hinzugefuegt?" - Antwort war NEIN: ohne
    Watchlist-Eintrag funktioniert weder das Screening noch die Preis-
    versorgung noch die neue "offene Position hat Prioritaet"-Funktion
    (budget_allocator.py) fuer dieses Symbol, siehe Memory
    project_asset_klassifikation_redesign).

    Default `rolle=taktisch` (die strategische Absicht hinter einer spontan
    eroeffneten Position ist unbekannt, sicherer Default - der Nutzer kann
    das jederzeit manuell auf "core" aendern), `beobachtungsstatus=
    beobachtung`. Bitpanda-Listing wird trotzdem geprueft (P-10, defensiv -
    sollte fuer eine tatsaechlich bei Bitpanda offene Position immer
    zutreffen).

    `coingecko_id`-Aufloesung (2026-07-19, Nutzer-Vorschlag "in dieser
    Schleife sollte das Symbol schon eindeutig sein, sonst gibt's da schon
    Inkonsistenzen"): da das Bitpanda-Listing hier bereits geprueft wird
    (`find_listed_asset()`), steht Bitpandas eigener, kuratierter Name fuer
    dieses Symbol zur Verfuegung - live verifiziert reicht ein Namensabgleich
    gegen `CoinGeckoClient.search_coins()`-Treffer, um die ID in der
    ueberwiegenden Mehrheit der Faelle zuverlaessig OHNE Nutzer-Interaktion
    aufzuloesen (siehe api/coingecko.py::resolve_coingecko_id_by_name()).
    `coingecko_client=None` erhaelt das alte Verhalten (ID bleibt leer, z.B.
    fuer Aufrufer ohne Netzwerkzugriff/Tests) - bei gesetztem Client wird die
    Aufloesung versucht, schlaegt sie fehl (kein/mehrere Namenstreffer -
    echte Inkonsistenz zwischen Bitpanda- und CoinGecko-Katalog), bleibt
    `coingecko_id` weiterhin leer und Spot-Analyse fuer dieses Symbol inaktiv
    bis zur manuellen Ergaenzung (siehe ui/app.py::AssetEditDialog) - Hebel-
    Screening/-Signale funktionieren bereits ohne sie. Gibt die Liste
    tatsaechlich neu hinzugefuegter Symbole zurueck (fuer Logging/
    Benachrichtigung)."""
    watchlist_symbols = {a.symbol for a in watchlist}
    hinzugefuegt: list[str] = []
    for pos in db.get_open_hebel_positions(conn):
        if pos.symbol in watchlist_symbols:
            continue
        bitpanda_asset = find_listed_asset(pos.symbol, listed_assets)
        if bitpanda_asset is None:
            logger.warning(
                "Hebel-Position auf %s ohne Watchlist-Eintrag, aber nicht als bei Bitpanda "
                "gelistet erkannt - kein Auto-Add (unerwartet, da die Position ja existiert)",
                pos.symbol,
            )
            continue

        coingecko_id = None
        if coingecko_client is not None:
            try:
                from api.coingecko import resolve_coingecko_id_by_name

                search_results = coingecko_client.search_coins(pos.symbol)
                coingecko_id = resolve_coingecko_id_by_name(search_results, bitpanda_asset.name)
            except Exception as exc:
                logger.info("CoinGecko-ID-Aufloesung fuer %s fehlgeschlagen (Netzwerkfehler?): %s", pos.symbol, exc)

        try:
            config_module.add_watchlist_entry(
                symbol=pos.symbol, name=pos.symbol, rolle="taktisch", beobachtungsstatus="beobachtung",
                coingecko_id=coingecko_id,
            )
            hinzugefuegt.append(pos.symbol)
            watchlist_symbols.add(pos.symbol)
            if coingecko_id:
                logger.info("coingecko_id fuer %s automatisch aufgeloest: %s", pos.symbol, coingecko_id)
        except config_module.WatchlistWriteError as exc:
            logger.warning("Automatisches Watchlist-Hinzufuegen fuer Hebel-Symbol %s fehlgeschlagen: %s", pos.symbol, exc)
    return hinzugefuegt
