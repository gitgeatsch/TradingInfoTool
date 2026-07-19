"""Signal-Pipeline fuer Einzelaktien (2026-07-15, Non-Krypto-Agent-Pipeline Phase 1) -
mirror des Kontrollflusses von agent/krypto/pipeline.py::generate_signal() (Gate ->
Regime -> Technik -> Risk-Gate -> Fundamentaldaten -> Facts -> LLM -> Post-Check ->
Signal), aber eigenstaendig (siehe agent/aktien/analyst.py Modul-Docstring fuer die
Architektur-Begruendung).

Wiederverwendet direkt (kein Duplikat): `agent.krypto.risk_gate.pre_check()`/
`post_check()` (RM-1/RM-2/RM-4/RM-5-Mathematik ist bereits assetklassen-neutral;
der Bitpanda-Veto war urspruenglich `if asset.assetklasse == "krypto"` bedingt -
2026-07-16 als echte Luecke erkannt und behoben, siehe `bitpanda_gelistet`-Berechnung
unten via `api.bitpanda.get_listed_non_crypto_assets()`),
`agent.krypto.pipeline.compute_current_regime()` (liefert Liquiditaets-Regime +
Aktien-Baermarkt-Overlay als Nebenprodukt der ohnehin noetigen BTC-Regime-Berechnung -
kein zweiter Berechnungsweg noetig), `indicators.calculations.build_technical_snapshot()`/
`summarize_confluence()` (bereits generisch)."""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

import numpy as np

import config
import database.db as db
from agent.aktien.analyst import (
    AnalystResponseInvalid,
    build_facts,
    call_llm_for_signal,
)
from agent.krypto.backward_tracking import compute_win_rate_fact
from agent.krypto.llm_provider import llm_model_label
from agent.krypto.makro_analog import get_cached_makro_analog_fact
from agent.krypto.pipeline import MIN_GATE_INDICATORS_AVAILABLE, compute_current_regime
from agent.krypto.risk_gate import post_check, pre_check
from api.yfinance_client import fetch_fundamentals
from api.yfinance_history import get_full_ohlc_history
from database.models import Signal
from indicators.calculations import build_technical_snapshot, summarize_confluence
from staleness import is_price_stale

logger = logging.getLogger(__name__)

PIPELINE_VERSION = "1"

# Stock-Maerkte schliessen an Wochenenden/Feiertagen (anders als Krypto, 24/7) - der
# crypto-getunte staleness.HISTORY_STALE_THRESHOLD_DAYS (2 Tage) wuerde an jedem
# Montag/Feiertag-Dienstag faelschlich "veraltet" ausloesen (Freitagsschluss ist am
# Sonntag schon 2 Tage alt). Eigener, grosszuegigerer Schwellenwert statt Wiederverwendung.
_AKTIEN_HISTORY_STALE_THRESHOLD_TAGE = 5


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _fixed_signal(symbol: str, action: str, gate_passed: bool, gate_reason: str | None, facts: dict | None = None) -> Signal:
    return Signal(
        symbol=symbol,
        created_at=_now(),
        action=action,
        gate_passed=gate_passed,
        gate_reason=gate_reason,
        risk_veto=False,
        facts_json=json.dumps(facts or {}, ensure_ascii=False),
        pipeline_version=PIPELINE_VERSION,
    )


def _is_aktien_history_stale(last_date: str | None) -> bool:
    if last_date is None:
        return True
    last = datetime.fromisoformat(last_date).date()
    today = datetime.now(timezone.utc).date()
    return (today - last).days > _AKTIEN_HISTORY_STALE_THRESHOLD_TAGE


def _ensure_ohlc_backfilled(conn, asset) -> None:
    """Holt die volle OHLC-Historie NUR, wenn sie fehlt oder veraltet ist (Freshness-
    Check ueber db.get_last_ohlc_date()) - vermeidet einen vollen Re-Download bei jedem
    manuellen Button-Klick (Phase 1 hat noch keinen Scheduler-Automatismus, siehe
    Modul-Docstring)."""
    last_date = db.get_last_ohlc_date(conn, asset.symbol, "USD")
    if last_date is not None and not _is_aktien_history_stale(last_date):
        return
    ohlc_points = get_full_ohlc_history(asset.yfinance_symbol, asset.symbol, "USD")
    if ohlc_points:
        db.upsert_ohlc_points(conn, ohlc_points)


def _load_ohlc(conn, symbol: str):
    ohlc_history = db.get_ohlc_history(conn, symbol, "USD")
    last_date = ohlc_history[-1].date if ohlc_history else None
    dates = np.array([o.date for o in ohlc_history])
    closes = np.array([o.close for o in ohlc_history], dtype=float)
    return dates, closes, ohlc_history, last_date


def generate_signal(asset, watchlist, conn, llm_client, coingecko_client) -> Signal:
    """Analog zu agent/krypto/pipeline.py::generate_signal(), aber fuer Einzelaktien.
    `watchlist` muss die VOLLSTAENDIGE Watchlist sein (inkl. BTC) - compute_current_regime()
    braucht zwingend ein BTC-Asset darin (Regime-Bestimmung ist BTC-verankert, siehe
    agent/krypto/pipeline.py::compute_current_regime()). Fuer pre_check()'s RM-2-
    Allokations-Berechnung wird intern auf die Aktien-Teilmenge gefiltert (analog zur
    Krypto-Pipeline, die dafuer eine krypto-only Watchlist nutzt - eine Aktie soll ihre
    Positionsgroesse relativ zum Aktien-Portfolio sehen, nicht zum gemischten
    Gesamtportfolio). `coingecko_client` wird NUR fuer compute_current_regime()
    durchgereicht, nicht fuer irgendetwas Aktien-Spezifisches."""
    if asset.assetklasse != "aktien":
        raise ValueError(f"generate_signal() (agent/aktien) erwartet assetklasse=='aktien', bekam {asset.assetklasse!r}")

    aktien_watchlist = [a for a in watchlist if a.assetklasse == "aktien"]

    _ensure_ohlc_backfilled(conn, asset)
    dates, closes, ohlc_history, last_date = _load_ohlc(conn, asset.symbol)
    latest_prices = db.get_latest_prices(conn)
    price_snap = latest_prices.get(asset.symbol)

    if len(closes) == 0:
        signal = _fixed_signal(asset.symbol, "HALTEN", gate_passed=False, gate_reason="keine historischen Daten vorhanden")
        db.insert_signal(conn, signal)
        return signal

    snapshot = build_technical_snapshot(closes, dates, ohlc_history)

    # Datenqualitaets-Gate (P-10), mirror agent/krypto/pipeline.py - VOR jedem LLM-Call.
    gate_problems = []
    if price_snap is None or is_price_stale(price_snap.fetched_at):
        gate_problems.append("Preis veraltet oder nicht vorhanden")
    if _is_aktien_history_stale(last_date):
        gate_problems.append(f"Historie veraltet (letzter Tag: {last_date})")
    for name in MIN_GATE_INDICATORS_AVAILABLE:
        result = getattr(snapshot, name)
        if not result.available:
            gate_problems.append(f"{name.upper()}: {result.reason}")

    if gate_problems:
        gate_reason = "; ".join(gate_problems)
        signal = _fixed_signal(asset.symbol, "HALTEN", gate_passed=False, gate_reason=gate_reason)
        db.insert_signal(conn, signal)
        return signal

    config_dict = config.load_config()
    # Liefert als Nebenprodukt der BTC-Regime-Berechnung liquiditaets_regime +
    # equities_baermarkt_aktiv - siehe Modul-Docstring, kein zweiter Berechnungsweg.
    regime_result = compute_current_regime(conn, coingecko_client, watchlist, None, config_dict)

    confluence = summarize_confluence(snapshot, closes[-1])

    # Bitpanda-Listing-Check (2026-07-16, Audit-Fund: bisher hartkodiert None -
    # risk_gate.py::pre_check() konnte den Bitpanda-Veto fuer Aktien nie auslösen,
    # obwohl Bitpanda auch Aktien/ETFs fuehrt). Gleiches Muster wie
    # agent/krypto/pipeline.py::generate_signal() - eigener try/except, ein
    # Fehlschlag degradiert nur auf "unbekannt" (P-10), blockiert nicht die Analyse.
    try:
        from api.bitpanda import get_listed_non_crypto_assets
        from api.bitpanda import is_listed as bitpanda_is_listed

        bitpanda_assets = get_listed_non_crypto_assets()
        bitpanda_gelistet = bitpanda_is_listed(asset.symbol, bitpanda_assets, name=asset.name)
    except Exception as exc:
        bitpanda_gelistet = None
        logger.info("Bitpanda-Listing-Abruf fuer %s fehlgeschlagen: %s", asset.symbol, exc)

    risk_result = pre_check(asset, aktien_watchlist, conn, latest_prices, snapshot, regime_result, config_dict, bitpanda_gelistet)

    fundamentals = None
    try:
        fundamentals = fetch_fundamentals(asset.symbol, asset.yfinance_symbol)
    except Exception as exc:
        logger.warning("Fundamentaldaten-Abruf fuer %s fehlgeschlagen (degradiert auf None): %s", asset.symbol, exc)

    holdings = {h.symbol: h for h in db.get_all_holdings(conn)}
    price_age_minutes = None
    if price_snap is not None:
        fetched = datetime.fromisoformat(price_snap.fetched_at)
        if fetched.tzinfo is None:
            fetched = fetched.replace(tzinfo=timezone.utc)
        price_age_minutes = (datetime.now(timezone.utc) - fetched).total_seconds() / 60

    # Krypto+Aktien bleiben bewusst gepoolt, siehe agent/krypto/pipeline.py fuer
    # dieselbe Begruendung + compute_win_rate_fact()-Docstring.
    _spot_pool_symbole = {a.symbol for a in config.get_watchlist() if a.assetklasse in ("krypto", "aktien")}
    historische_erfolgsquote = compute_win_rate_fact(conn, "spot", erlaubte_symbole=_spot_pool_symbole)
    historischer_makro_vergleich = get_cached_makro_analog_fact(conn)
    # Wiederholungs-Erkennung (2026-07-18, Multi-Asset-Vollstaendigkeitspruefung,
    # siehe agent/krypto/wiederholungs_erkennung.py) - bisher nur Krypto hatte das.
    letztes_signal = db.get_latest_signal(conn, asset.symbol)

    facts = build_facts(
        asset, price_snap, holdings.get(asset.symbol), snapshot, confluence, regime_result,
        risk_result, fundamentals, price_age_minutes,
        historische_erfolgsquote=historische_erfolgsquote,
        historischer_makro_vergleich=historischer_makro_vergleich,
        letztes_signal=letztes_signal,
    )

    try:
        parsed = call_llm_for_signal(llm_client, facts)
    except AnalystResponseInvalid as exc:
        logger.warning("LLM-Antwort fuer %s ungueltig: %s", asset.symbol, exc)
        signal = _fixed_signal(asset.symbol, "HALTEN", gate_passed=True, gate_reason=f"Agent-Antwort ungültig: {exc}", facts=facts)
        db.insert_signal(conn, signal)
        return signal

    raw_response = parsed.pop("_raw_response", None)

    corrected = post_check(parsed, risk_result, regime_result, config_dict, confluence=confluence)
    risk_veto = corrected.pop("_risk_veto")
    risk_veto_reason = corrected.pop("_risk_veto_reason")
    cash_veto = corrected.pop("_cash_veto")
    cash_veto_reason = corrected.pop("_cash_veto_reason")
    risikofaktoren = corrected.pop("_risikofaktoren", None)

    long_reasoning = corrected.get("long_reasoning", {})
    position_size = corrected.get("position_size", {})
    entry = corrected.get("entry", {})
    stop_loss = corrected.get("stop_loss", {})
    take_profit = corrected.get("take_profit", {})
    halte_kriterium = corrected.get("halte_kriterium", {})
    top_gruende_by_rang = {g.get("rang"): g for g in corrected.get("top_gruende", [])}
    forecast = corrected.get("forecast", {})

    top_grund_fields = {}
    for rang in range(1, 6):
        eintrag = top_gruende_by_rang.get(rang, {})
        top_grund_fields[f"top_grund_{rang}_kategorie"] = eintrag.get("kategorie")
        top_grund_fields[f"top_grund_{rang}_text"] = eintrag.get("text")

    signal = Signal(
        symbol=asset.symbol,
        created_at=_now(),
        action=corrected["action"],
        gate_passed=True,
        gate_reason=None,
        risk_veto=risk_veto,
        risk_veto_reason=risk_veto_reason,
        cash_veto=cash_veto,
        cash_veto_reason=cash_veto_reason,
        risikofaktoren_json=json.dumps(risikofaktoren, ensure_ascii=False) if risikofaktoren else None,
        facts_json=json.dumps(facts, ensure_ascii=False),
        pipeline_version=PIPELINE_VERSION,
        confidence_pct=corrected.get("confidence_pct"),
        short_reasoning=corrected.get("short_reasoning"),
        long_reasoning_technisch=long_reasoning.get("technisch"),
        long_reasoning_fundamental=long_reasoning.get("fundamental"),
        long_reasoning_makro=long_reasoning.get("makro"),
        position_size_usd=position_size.get("usd"),
        position_size_eur=position_size.get("eur"),
        position_size_note=position_size.get("note"),
        entry_usd_von=entry.get("usd_von"),
        entry_usd_bis=entry.get("usd_bis"),
        entry_eur_von=entry.get("eur_von"),
        entry_eur_bis=entry.get("eur_bis"),
        stop_loss_usd_von=stop_loss.get("usd_von"),
        stop_loss_usd_bis=stop_loss.get("usd_bis"),
        stop_loss_eur_von=stop_loss.get("eur_von"),
        stop_loss_eur_bis=stop_loss.get("eur_bis"),
        take_profit_usd_von=take_profit.get("usd_von"),
        take_profit_usd_bis=take_profit.get("usd_bis"),
        take_profit_eur_von=take_profit.get("eur_von"),
        take_profit_eur_bis=take_profit.get("eur_bis"),
        halte_kriterium_bucket=halte_kriterium.get("bucket"),
        halte_kriterium_ziel_preis_usd=halte_kriterium.get("ziel_preis_usd"),
        halte_kriterium_ziel_preis_eur=halte_kriterium.get("ziel_preis_eur"),
        halte_kriterium_ziel_datum=halte_kriterium.get("ziel_datum"),
        halte_kriterium_bedingung_text=halte_kriterium.get("bedingung_text"),
        halte_kriterium_reasoning=halte_kriterium.get("reasoning"),
        key_risks_text="\n".join(corrected.get("key_risks", [])),
        regime=regime_result.regime,
        regime_source=regime_result.source,
        forecast_bull_text=forecast.get("bull", {}).get("scenario"),
        forecast_bull_prob_pct=forecast.get("bull", {}).get("probability_pct"),
        forecast_base_text=forecast.get("base", {}).get("scenario"),
        forecast_base_prob_pct=forecast.get("base", {}).get("probability_pct"),
        forecast_bear_text=forecast.get("bear", {}).get("scenario"),
        forecast_bear_prob_pct=forecast.get("bear", {}).get("probability_pct"),
        gegenargument=corrected.get("gegenargument"),
        groq_raw_response=raw_response,
        groq_model=llm_model_label(llm_client),
        **top_grund_fields,
    )
    db.insert_signal(conn, signal)
    return signal
