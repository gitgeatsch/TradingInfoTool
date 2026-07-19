"""Hebel-Backward-Tracking (2026-07-15) - mirror von agent/krypto/backward_tracking.py
(Selbstverifikations-Vision Schritt 2), aber fuer hebel_signals statt signals. Prueft
vergangene ERÖFFNEN/NACHKAUFEN-Hebel-Empfehlungen gegen die seit ihrer Erstellung
tatsaechlich eingetretene Kurshistorie - richtungsabhaengig (LONG/SHORT), da bei SHORT
Take-Profit unterhalb und Stop-Loss oberhalb des Einstiegs liegt (umgekehrt zu LONG/Spot).

Zusaetzlich zu take_profit_erreicht/stop_loss_erreicht gibt es hier
OUTCOME_LIQUIDATION: der Liquidationspreis liegt naeher am Kurs als der Stop-Loss
(Sicherheitsmarge 15-20%, siehe Regelwerksmanual) - wird deshalb VOR dem Stop-Loss
geprueft (konservativste Annahme zuerst, gleiches Prinzip wie "trifft ein Tag beide
Zonen, gewinnt Stop-Loss" in backward_tracking.py). Rein beobachtend (P-7 Advisory-only)."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

import database.db as db
from agent.krypto.backward_tracking import (
    DEFAULT_ABGELAUFEN_TAGE_BUCKET,
    DEFAULT_ABGELAUFEN_TAGE_FALLBACK,
    OUTCOME_ABGELAUFEN,
    OUTCOME_LIQUIDATION,
    OUTCOME_NICHT_ANWENDBAR,
    OUTCOME_OFFEN,
    OUTCOME_STOP_LOSS,
    OUTCOME_TAKE_PROFIT,
    OUTCOME_UEBERHOLT,
)

# ERÖFFNEN/NACHKAUFEN sind die einzigen Aktionen mit Entry/Stop-Pflicht + CRV>=2.0-
# Vorgabe (siehe hebel_analyst.py:25-28,67) - HEBEL_ERHÖHEN/HEBEL_SENKEN/TEILVERKAUF/
# SCHLIESSEN/HALTEN haben keine trackbare Entry-vs-Kurs-Semantik.
_TRACKABLE_HEBEL_ACTIONS = {"ERÖFFNEN", "NACHKAUFEN"}


@dataclass
class HebelBackwardTrackingResult:
    geprueft_count: int = 0
    resolved_take_profit: int = 0
    resolved_stop_loss: int = 0
    resolved_liquidation: int = 0
    expired: int = 0
    superseded: int = 0
    still_open: int = 0
    warnings: list[str] = field(default_factory=list)


def _entry_mid(signal) -> float | None:
    von = signal.entry_usd_von
    bis = signal.entry_usd_bis
    if von is not None and bis is not None:
        return (von + bis) / 2
    return von


def check_hebel_signal_outcome(conn, signal, watchlist) -> tuple[str, dict]:
    """Prueft EIN Hebel-Signal gegen die seit signal.created_at vorliegende
    Kurshistorie - mirror check_signal_outcome() (backward_tracking.py:57-118),
    richtungsabhaengig. Gibt (neuer_status, extra_felder) zurueck, schreibt selbst
    nichts (Testbarkeit ohne DB-Mocking der Schreibpfade)."""
    if signal.action not in _TRACKABLE_HEBEL_ACTIONS:
        return OUTCOME_NICHT_ANWENDBAR, {}

    take_profit_threshold = signal.take_profit_usd_von
    stop_loss_threshold = signal.stop_loss_usd_von
    if take_profit_threshold is None or stop_loss_threshold is None:
        return OUTCOME_NICHT_ANWENDBAR, {}

    liquidation_threshold = signal.liquidationspreis_geschaetzt_usd
    ist_short = signal.richtung == "SHORT"

    asset = next((a for a in watchlist if a.symbol == signal.symbol), None)
    if asset is None:
        return OUTCOME_OFFEN, {}

    min_date = signal.created_at[:10]
    entry_mid = _entry_mid(signal)

    def resolve(exit_price: float, status: str) -> tuple[str, dict]:
        realized_crv = None
        if entry_mid is not None:
            if ist_short:
                risiko_distanz = stop_loss_threshold - entry_mid
                if risiko_distanz != 0:
                    realized_crv = (entry_mid - exit_price) / risiko_distanz
            else:
                risiko_distanz = entry_mid - stop_loss_threshold
                if risiko_distanz != 0:
                    realized_crv = (exit_price - entry_mid) / risiko_distanz
        return status, {
            "entschieden_am": day,
            "realisiertes_crv": realized_crv,
            "datenquelle": datenquelle,
        }

    def _check_day(high: float, low: float, day_value: str) -> tuple[str, dict] | None:
        nonlocal day
        day = day_value
        if ist_short:
            hit_liquidation = liquidation_threshold is not None and high >= liquidation_threshold
            hit_stop = high >= stop_loss_threshold
            hit_take = low <= take_profit_threshold
            exit_hoch, exit_tief = high, low
        else:
            hit_liquidation = liquidation_threshold is not None and low <= liquidation_threshold
            hit_stop = low <= stop_loss_threshold
            hit_take = high >= take_profit_threshold
            exit_hoch, exit_tief = high, low

        # Konservativste Annahme zuerst: Liquidation vor Stop-Loss vor Take-Profit.
        if hit_liquidation:
            return resolve(liquidation_threshold, OUTCOME_LIQUIDATION)
        if hit_stop:
            return resolve(stop_loss_threshold, OUTCOME_STOP_LOSS)
        if hit_take:
            return resolve(take_profit_threshold, OUTCOME_TAKE_PROFIT)
        return None

    day = None
    ohlc_rows = db.get_ohlc_history(conn, signal.symbol, "USD", min_date=min_date)
    if len(ohlc_rows) >= 1:
        datenquelle = "real"
        for row in ohlc_rows:
            result = _check_day(row.high, row.low, row.date)
            if result is not None:
                return result
    else:
        datenquelle = "proxy"
        price_rows = db.get_price_history(conn, asset.coingecko_id, min_date=min_date) if asset.coingecko_id else []
        for row in price_rows:
            if row.price_usd is None:
                continue
            result = _check_day(row.price_usd, row.price_usd, row.date)
            if result is not None:
                return result

    return OUTCOME_OFFEN, {}


def _is_superseded(signal, latest_real: dict) -> bool:
    """Mirror backward_tracking.py::_is_superseded(), aber nach (symbol,
    richtung) geschluesselt - ein LONG- und ein SHORT-Signal fuer denselben
    Coin sind unabhaengige Thesen, eines ueberholt das andere nicht.

    NACHTRAG (2026-07-19, Backtracking-Aussagekraft-Audit, siehe dortiger
    Docstring): eine reine HALTEN-Bestaetigung ueberholt die offene
    ERÖFFNEN-These nicht mehr - live geprueft, dass 60% der offenen Hebel-
    Signale unter der alten Regel nach durchschnittlich 11,7 Std. ueberholt
    wurden (hebel_position_cooldown_stunden=3), bevor der Kurs ueberhaupt
    eine faire Chance hatte, Take-Profit/Stop-Loss zu erreichen.

    Rein deterministischer Datums-/ID-/Aktions-Vergleich, KEIN LLM-Call."""
    latest = latest_real.get((signal.symbol, signal.richtung))
    return (
        latest is not None
        and latest.id != signal.id
        and latest.created_at > signal.created_at
        and latest.action != "HALTEN"
    )


def _is_expired(signal, bucket_tage: dict[str, int], fallback_tage: int) -> bool:
    """Mirror backward_tracking.py::_is_expired() - inhaltsbasierte Ablaufzeit
    aus halte_kriterium statt einer fixen Frist fuer alle Hebel-Signale."""
    created = datetime.fromisoformat(signal.created_at)
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)

    ziel_datum = getattr(signal, "halte_kriterium_ziel_datum", None)
    if ziel_datum:
        try:
            deadline = datetime.fromisoformat(ziel_datum)
            if deadline.tzinfo is None:
                deadline = deadline.replace(tzinfo=timezone.utc)
            return now > deadline
        except ValueError:
            pass

    bucket = getattr(signal, "halte_kriterium_bucket", None)
    tage = bucket_tage.get(bucket, fallback_tage) if bucket else fallback_tage
    age_days = (now - created).days
    return age_days >= tage


def run_hebel_backward_tracking(conn, watchlist, config: dict) -> HebelBackwardTrackingResult:
    """Mirror run_backward_tracking() (backward_tracking.py:131-178) - holt alle
    hebel_signals mit outcome_status IN (NULL, 'offen'), prueft jedes, schreibt nur
    bei tatsaechlicher Statusaenderung. Nutzt dieselbe abgelaufen_nach_tagen-
    Konfiguration wie Spot (config['backward_tracking']) - kein separater Wert noetig,
    gleiche Ablauf-Logik."""
    result = HebelBackwardTrackingResult()
    bt_cfg = config.get("backward_tracking", {})
    bucket_tage = bt_cfg.get("abgelaufen_nach_tagen_bucket", DEFAULT_ABGELAUFEN_TAGE_BUCKET)
    fallback_tage = bt_cfg.get("abgelaufen_nach_tagen_fallback", DEFAULT_ABGELAUFEN_TAGE_FALLBACK)
    latest_real = db.get_latest_hebel_signal_per_symbol_and_richtung(conn)

    rows = conn.execute(
        "SELECT id FROM hebel_signals WHERE outcome_status IS NULL OR outcome_status = ?",
        (OUTCOME_OFFEN,),
    ).fetchall()

    for row in rows:
        signal = db.get_hebel_signal_by_id(conn, row["id"])
        if signal is None:
            continue
        result.geprueft_count += 1

        status, extra = check_hebel_signal_outcome(conn, signal, watchlist)

        if status == OUTCOME_NICHT_ANWENDBAR:
            db.update_hebel_signal_outcome(conn, signal.id, status)
            continue

        if status in (OUTCOME_TAKE_PROFIT, OUTCOME_STOP_LOSS, OUTCOME_LIQUIDATION):
            db.update_hebel_signal_outcome(
                conn, signal.id, status,
                entschieden_am=extra.get("entschieden_am"),
                realisiertes_crv=extra.get("realisiertes_crv"),
                datenquelle=extra.get("datenquelle"),
            )
            if status == OUTCOME_TAKE_PROFIT:
                result.resolved_take_profit += 1
            elif status == OUTCOME_STOP_LOSS:
                result.resolved_stop_loss += 1
            else:
                result.resolved_liquidation += 1
            continue

        # status == OUTCOME_OFFEN: erst Ueberholt-Check, dann Ablauf-Check.
        if _is_superseded(signal, latest_real):
            db.update_hebel_signal_outcome(conn, signal.id, OUTCOME_UEBERHOLT)
            result.superseded += 1
        elif _is_expired(signal, bucket_tage, fallback_tage):
            db.update_hebel_signal_outcome(conn, signal.id, OUTCOME_ABGELAUFEN)
            result.expired += 1
        else:
            result.still_open += 1

    return result
