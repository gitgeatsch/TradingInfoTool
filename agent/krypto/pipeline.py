"""R-5.0..R-5.11 Orchestrierung (Spezifikation Kap. 5) - siehe
C:\\Users\\Geatsch\\.claude\\plans\\deep-launching-zebra.md fuer den vollstaendigen
Scope dieser Slice (was drin ist, was bewusst draussen bleibt).

generate_signal() ist rein synchron und UI-frei - Threading fuer den UI-Trigger lebt
ausschliesslich in ui/signals_view.py, nicht hier (leichter isoliert testbar)."""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

import numpy as np

import config
import database.db as db
from agent.krypto.analyst import AnalystResponseInvalid, build_facts, call_groq_for_signal
from agent.krypto.anticyclic import assess as assess_anticyclic
from agent.krypto.regime import determine_regime
from agent.krypto.risk_gate import pre_check, post_check
from database.models import MacroSnapshot, Signal
from indicators.calculations import build_technical_snapshot, summarize_confluence
from staleness import is_history_stale, is_price_stale

logger = logging.getLogger(__name__)

PIPELINE_VERSION = "1"
MIN_GATE_INDICATORS_AVAILABLE = ("rsi", "macd", "bollinger")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _fixed_signal(
    symbol: str, action: str, gate_passed: bool, gate_reason: str | None, facts: dict | None = None
) -> Signal:
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


def _load_closes_and_ohlc(conn, symbol: str, coingecko_id: str):
    history = db.get_price_history(conn, coingecko_id)
    last_date = db.get_last_history_date(conn, coingecko_id)
    dates = np.array([p.date for p in history])
    closes = np.array([p.price_usd for p in history], dtype=float)
    valid = ~np.isnan(closes)
    dates, closes = dates[valid], closes[valid]
    ohlc_history = db.get_ohlc_history(conn, symbol, "USD")
    return dates, closes, ohlc_history, last_date


def _update_macro_snapshot(
    conn, coingecko_client, fred_api_key: str | None, liquidity_context: dict
) -> list[MacroSnapshot]:
    from api.macro import get_all_fred_rates, get_btc_dominance, get_fear_greed_index, get_pboc_lpr

    today = datetime.now(timezone.utc).date().isoformat()
    try:
        dominance = get_btc_dominance(coingecko_client)
    except Exception as exc:
        logger.info("BTC-Dominanz-Abruf fehlgeschlagen: %s", exc)
        dominance = None
    try:
        fgi = get_fear_greed_index()
        fgi_value, fgi_label = fgi.value, fgi.classification
    except Exception as exc:
        logger.info("Fear&Greed-Abruf fehlgeschlagen: %s", exc)
        fgi_value, fgi_label = None, None

    # FRED_API_KEY ist optional (P-8: Kernfunktionen duerfen nicht zwingend von einem
    # KI-/externen Key abhaengen) - ohne Key bleiben alle FRED-Felder None, kein Fehler.
    fred_values: dict[str, float | None] = {}
    if fred_api_key:
        for name, obs in get_all_fred_rates(fred_api_key).items():
            fred_values[name] = obs.value if obs is not None else None

    pboc_lpr_1y = pboc_lpr_5y = None
    try:
        lpr = get_pboc_lpr()
        pboc_lpr_1y, pboc_lpr_5y = lpr.lpr_1y, lpr.lpr_5y
    except Exception as exc:
        logger.info("PBoC-LPR-Abruf fehlgeschlagen (Eastmoney): %s", exc)

    m2_eurozone = liquidity_context.get("m2_eurozone_latest")
    m2_china = liquidity_context.get("m2_china_latest")
    m2_japan = liquidity_context.get("m2_japan_latest")

    any_new_value = any(
        v is not None
        for v in (
            dominance, fgi_value, pboc_lpr_1y, pboc_lpr_5y, m2_eurozone, m2_china, m2_japan,
            *fred_values.values(),
        )
    )
    if any_new_value:
        db.upsert_macro_snapshot(
            conn,
            MacroSnapshot(
                today, dominance, fgi_value, fgi_label, _now(),
                fed_funds_rate=fred_values.get("fed_funds_rate"),
                m2_geldmenge=fred_values.get("m2_geldmenge"),
                cpi_headline=fred_values.get("cpi_headline"),
                cpi_core=fred_values.get("cpi_core"),
                ezb_einlagensatz=fred_values.get("ezb_einlagensatz"),
                ezb_hauptrefinanzierung=fred_values.get("ezb_hauptrefinanzierung"),
                ezb_spitzenrefinanzierung=fred_values.get("ezb_spitzenrefinanzierung"),
                ism_ersatz_philly_fed=fred_values.get("ism_ersatz_philly_fed"),
                boj_tagesgeldsatz=fred_values.get("boj_tagesgeldsatz"),
                bok_diskontsatz=fred_values.get("bok_diskontsatz"),
                pboc_lpr_1y=pboc_lpr_1y,
                pboc_lpr_5y=pboc_lpr_5y,
                m2_eurozone=m2_eurozone,
                m2_china=m2_china,
                m2_japan=m2_japan,
            ),
        )
    return db.get_macro_snapshot_history(conn)


def _fetch_liquidity_context(fred_api_key: str | None) -> dict:
    """Bootstrap-Historie fuers Liquiditaets-Regime (agent/regime.py) - bewusst ein
    frischer Live-Abruf statt aus der macro_snapshot-Akkumulation abgeleitet: die
    Pipeline laeuft nur bei manuellem "Signal berechnen"-Klick (kein taeglicher
    Scheduler), ueber `_dominance_direction()`-Logik haette der Liquiditaets-Trend
    daher realistisch Monate gebraucht, um ueberhaupt einen zweiten Datenpunkt zu
    bekommen. FRED/EZB/Eastmoney liefern die Historie aber bereits fertig - genutzt
    statt darauf zu warten. P-10: jede Quelle einzeln versucht, ein Fehlschlag
    blockiert die anderen nicht. Japan bewusst ohne Trend-Beitrag (keine Historien-
    Quelle vorhanden, siehe api/macro.py::get_japan_m2 - nur der letzte Wert)."""
    from datetime import date, timedelta

    from api.macro import get_china_m2_history, get_ecb_m2_history, get_fred_history, get_japan_m2

    context: dict = {
        "fed_funds_history": [], "m2_us_history": [], "m2_eurozone_history": [], "m2_china_history": [],
        "m2_eurozone_latest": None, "m2_china_latest": None, "m2_japan_latest": None,
    }
    if fred_api_key:
        start = (date.today() - timedelta(days=200)).isoformat()
        try:
            obs = get_fred_history("FEDFUNDS", fred_api_key, start)
            context["fed_funds_history"] = [o.value for o in obs if o.value is not None]
        except Exception as exc:
            logger.info("Fed-Funds-Rate-Historie-Abruf fehlgeschlagen: %s", exc)
        try:
            obs = get_fred_history("M2SL", fred_api_key, start)
            context["m2_us_history"] = [o.value for o in obs if o.value is not None]
        except Exception as exc:
            logger.info("US-M2-Historie-Abruf fehlgeschlagen: %s", exc)
    try:
        ezb = get_ecb_m2_history(6)
        context["m2_eurozone_history"] = [o.value for o in ezb]
        context["m2_eurozone_latest"] = ezb[-1].value if ezb else None
    except Exception as exc:
        logger.info("EZB-M2-Historie-Abruf fehlgeschlagen: %s", exc)
    try:
        cn = get_china_m2_history(6)
        context["m2_china_history"] = [o.value for o in cn]
        context["m2_china_latest"] = cn[-1].value if cn else None
    except Exception as exc:
        logger.info("China-M2-Historie-Abruf fehlgeschlagen: %s", exc)
    try:
        context["m2_japan_latest"] = get_japan_m2().value
    except Exception as exc:
        logger.info("Japan-M2-Abruf fehlgeschlagen: %s", exc)
    return context


def _fetch_cycle_risk_context() -> dict:
    """BTC-Zyklus-Risiko-Kontext fuer agent/regime.py (Nutzungs-Diskussion, Schritt 2,
    2026-07-08): Log-Regression-Risk (indicators/calculations.py) + MVRV/NUPL
    (api/onchain.py) als Cross-Check. P-10: beide Quellen unabhaengig versucht, ein
    Fehlschlag blockiert die andere nicht. Bewusst ein frischer Live-Abruf pro
    Pipeline-Lauf statt Caching - konsistent mit `_fetch_liquidity_context`."""
    from api.onchain import get_btc_full_price_history, get_btc_onchain_snapshot
    from indicators.calculations import compute_btc_log_regression_risk

    context: dict = {"log_regression_risk": None, "onchain_reading": None}
    try:
        history = get_btc_full_price_history()
        context["log_regression_risk"] = compute_btc_log_regression_risk(history)
    except Exception as exc:
        logger.info("BTC-Log-Regression-Risk-Berechnung fehlgeschlagen: %s", exc)
    try:
        context["onchain_reading"] = get_btc_onchain_snapshot()
    except Exception as exc:
        logger.info("MVRV/NUPL-Abruf (CoinMetrics) fehlgeschlagen: %s", exc)
    return context


def fetch_market_context() -> dict:
    """Reiner Groq-Kontext (Nutzungs-Diskussion, letzter Schritt, 2026-07-08) - KEINE
    neue Regime-Logik, nur zusaetzliche Fakten fuers Facts-Objekt (agent/analyst.py::
    build_facts). P-10: Exchange-Flow/Stablecoin-Supply unabhaengig versucht: FOMC-
    Kalender/Praesidentschaftszyklus sind reine Datumsrechnung (agent/cycles.py),
    kein Netzwerk-Call, daher kein try/except noetig."""
    from api.onchain import get_btc_exchange_flows, get_stablecoin_supply
    from agent.cycles import get_presidential_cycle_context, get_upcoming_fomc_meetings

    context: dict = {
        "exchange_flow": None,
        "stablecoin_supply": None,
        "presidential_cycle": get_presidential_cycle_context(),
        "upcoming_fomc": get_upcoming_fomc_meetings(within_days=30),
    }
    try:
        context["exchange_flow"] = get_btc_exchange_flows()
    except Exception as exc:
        logger.info("BTC-Exchange-Flow-Abruf fehlgeschlagen: %s", exc)
    try:
        context["stablecoin_supply"] = get_stablecoin_supply()
    except Exception as exc:
        logger.info("Stablecoin-Supply-Abruf fehlgeschlagen: %s", exc)
    return context


def compute_current_regime(conn, coingecko_client, watchlist, fred_api_key: str | None, config_dict: dict):
    """Buendelt die vollstaendige Regime-Bestimmung (R-5.1 + Liquiditaets-Regime +
    Zyklus-Risiko, siehe agent/regime.py) - von generate_signal() UND
    scheduler/background.py::marktscan_job() genutzt, damit beide denselben
    aktuellen Markt-/Makro-Zustand verwenden statt die Logik zu duplizieren.
    Wirft ValueError, falls kein BTC-Asset in der Watchlist ist (die
    Regime-Bestimmung braucht zwingend BTC-Daten)."""
    btc_asset = next((a for a in watchlist if a.symbol == "BTC"), None)
    if btc_asset is None:
        raise ValueError("Kein BTC-Asset in der Watchlist gefunden - Regime-Bestimmung braucht BTC")

    liquidity_context = _fetch_liquidity_context(fred_api_key)
    cycle_risk_context = _fetch_cycle_risk_context()
    macro_history = _update_macro_snapshot(conn, coingecko_client, fred_api_key, liquidity_context)
    btc_dates, btc_closes, btc_ohlc, _ = _load_closes_and_ohlc(conn, "BTC", btc_asset.coingecko_id)
    btc_snapshot = build_technical_snapshot(btc_closes, btc_dates, btc_ohlc)

    return determine_regime(
        btc_closes, btc_snapshot, macro_history, config_dict["regime"]["manueller_override"],
        fed_funds_history=liquidity_context["fed_funds_history"],
        m2_us_history=liquidity_context["m2_us_history"],
        m2_eurozone_history=liquidity_context["m2_eurozone_history"],
        m2_china_history=liquidity_context["m2_china_history"],
        btc_log_regression_risk=cycle_risk_context["log_regression_risk"],
        btc_onchain_reading=cycle_risk_context["onchain_reading"],
    )


def generate_signal(
    asset, watchlist, conn, groq_client, coingecko_client, kraken_client,
    fred_api_key: str | None = None,
) -> Signal:
    # A-1: Stablecoins haben kein eigenstaendiges Handelssignal.
    if asset.typ == "stablecoin":
        signal = _fixed_signal(
            asset.symbol, "HALTEN", gate_passed=False,
            gate_reason="Stablecoin (A-1): kein eigenständiges Handelssignal",
        )
        db.insert_signal(conn, signal)
        return signal

    dates, closes, ohlc_history, last_date = _load_closes_and_ohlc(conn, asset.symbol, asset.coingecko_id)
    latest_prices = db.get_latest_prices(conn)
    price_snap = latest_prices.get(asset.symbol)

    if len(closes) == 0:
        signal = _fixed_signal(
            asset.symbol, "HALTEN", gate_passed=False, gate_reason="keine historischen Daten vorhanden",
        )
        db.insert_signal(conn, signal)
        return signal

    snapshot = build_technical_snapshot(closes, dates, ohlc_history)

    # R-5.0 Datenqualitaets-Gate (P-10): VOR allem anderen, kein Groq-Call bei
    # unzureichender Datenlage.
    gate_problems = []
    if price_snap is None or is_price_stale(price_snap.fetched_at):
        gate_problems.append("Preis veraltet oder nicht vorhanden")
    if is_history_stale(last_date):
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

    # R-5.1 Marktregime (BTC-Trend + BTC-Dominanz + Fear&Greed + Liquiditaet + Zyklus-Risiko).
    config_dict = config.load_config()
    regime_result = compute_current_regime(conn, coingecko_client, watchlist, fred_api_key, config_dict)
    regime_profile = config_dict["regime"]["profile"].get(regime_result.regime, {})

    # R-5.3 Technische Analyse -> Confluence-Zusammenfassung.
    confluence = summarize_confluence(snapshot, closes[-1])

    # R-5.5 (pre) Risikopruefung.
    risk_result = pre_check(asset, watchlist, conn, latest_prices, snapshot, regime_result, config_dict)

    # R-5.11 Antizyklik-Heuristik.
    anticyclic_context = assess_anticyclic(asset, kraken_client, closes)

    market_context = fetch_market_context()

    holdings = {h.symbol: h for h in db.get_all_holdings(conn)}
    strategien_aktiv = [s["name"] for s in config_dict["strategien"] if s["aktiv"]]
    price_age_minutes = None
    if price_snap is not None:
        fetched = datetime.fromisoformat(price_snap.fetched_at)
        if fetched.tzinfo is None:
            fetched = fetched.replace(tzinfo=timezone.utc)
        price_age_minutes = (datetime.now(timezone.utc) - fetched).total_seconds() / 60

    facts = build_facts(
        asset, price_snap, holdings.get(asset.symbol), snapshot, confluence, regime_result,
        regime_profile, risk_result, anticyclic_context, strategien_aktiv, price_age_minutes,
        market_context,
    )

    # R-5.6 Groq-Synthese.
    try:
        parsed = call_groq_for_signal(groq_client, facts)
    except AnalystResponseInvalid as exc:
        logger.warning("Groq-Antwort fuer %s ungueltig: %s", asset.symbol, exc)
        signal = _fixed_signal(
            asset.symbol, "HALTEN", gate_passed=True,
            gate_reason=f"Agent-Antwort ungültig: {exc}", facts=facts,
        )
        db.insert_signal(conn, signal)
        return signal

    raw_response = parsed.pop("_raw_response", None)

    # R-5.5 (post) / R-5.9 / R-5.10 - deterministische Nachkontrolle, Modell wird nie
    # blind vertraut.
    corrected = post_check(parsed, risk_result, regime_result, config_dict)
    risk_veto = corrected.pop("_risk_veto")
    risk_veto_reason = corrected.pop("_risk_veto_reason")

    long_reasoning = corrected.get("long_reasoning", {})
    position_size = corrected.get("position_size", {})
    entry = corrected.get("entry", {})
    stop_loss = corrected.get("stop_loss", {})
    take_profit = corrected.get("take_profit", {})
    holding_duration = corrected.get("holding_duration", {})
    forecast = corrected.get("forecast", {})

    signal = Signal(
        symbol=asset.symbol,
        created_at=_now(),
        action=corrected["action"],
        gate_passed=True,
        gate_reason=None,
        risk_veto=risk_veto,
        risk_veto_reason=risk_veto_reason,
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
        entry_usd=entry.get("usd"),
        entry_eur=entry.get("eur"),
        stop_loss_usd=stop_loss.get("usd"),
        stop_loss_eur=stop_loss.get("eur"),
        take_profit_usd=take_profit.get("usd"),
        take_profit_eur=take_profit.get("eur"),
        holding_duration=holding_duration.get("bucket"),
        holding_duration_reason=holding_duration.get("reasoning"),
        key_risks_text="\n".join(corrected.get("key_risks", [])),
        regime=regime_result.regime,
        regime_source=regime_result.source,
        forecast_bull_text=forecast.get("bull", {}).get("scenario"),
        forecast_bull_prob_pct=forecast.get("bull", {}).get("probability_pct"),
        forecast_base_text=forecast.get("base", {}).get("scenario"),
        forecast_base_prob_pct=forecast.get("base", {}).get("probability_pct"),
        forecast_bear_text=forecast.get("bear", {}).get("scenario"),
        forecast_bear_prob_pct=forecast.get("bear", {}).get("probability_pct"),
        tauschen_target_symbol=corrected.get("tauschen_target_symbol"),
        groq_raw_response=raw_response,
        groq_model="llama-3.3-70b-versatile",
    )
    db.insert_signal(conn, signal)
    return signal
