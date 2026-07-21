"""Orchestrierung: verwandelt einen `HebelTrigger`-Screening-Kandidaten in ein
vollstaendiges `HebelSignal` (2026-07-14, Phase 4, siehe
docs/hebel_positionsformel.md). Mirrort agent/krypto/pipeline.py::
generate_signal() 1:1 im Aufbau, wiederverwendet dessen Bausteine wo die
Bedeutung gleich ist (Regime/Antizyklik/Markt-Kontext/Technische Analyse).

Seit Phase 5 (siehe docs/budget_queue_design.md) wird generate_hebel_signal()
automatisch vom Budget-Allocator (agent/krypto/budget_allocator.py) im
15-Min-Takt aufgerufen - bleibt aber weiterhin eine reine, auch manuell
aufrufbare Funktion ohne eigene Scheduler-/Budget-Logik (die lebt zentral im
Allocator, nicht hier)."""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

import database.db as db
from agent.krypto.analyst import AnalystResponseInvalid
from agent.krypto.anticyclic import assess as assess_anticyclic
from agent.krypto.backward_tracking import compute_win_rate_fact
from agent.krypto.hebel_analyst import build_hebel_facts, call_llm_for_hebel_signal
from agent.krypto.makro_analog import get_cached_makro_analog_fact
from agent.krypto.hebel_risk_gate import post_check_hebel, pre_check_hebel
from agent.krypto.llm_provider import llm_model_label
from agent.krypto.pipeline import _load_closes_and_ohlc, compute_current_regime, fetch_market_context
from agent.krypto.risk_gate import STOP_LOSS_ATR_MULTIPLE, _portfolio_values_usd
from database.models import HebelSignal, HebelTrigger
from indicators.calculations import build_technical_snapshot, latest_value, summarize_confluence
from staleness import is_history_stale, is_price_stale

logger = logging.getLogger(__name__)

PIPELINE_VERSION = "1"
MIN_GATE_INDICATORS_AVAILABLE = ("rsi", "macd", "bollinger")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _fixed_hebel_signal(
    trigger: HebelTrigger, action: str, gate_passed: bool, gate_reason: str | None, facts: dict | None = None
) -> HebelSignal:
    return HebelSignal(
        symbol=trigger.symbol,
        created_at=_now(),
        richtung=trigger.richtung,
        action=action,
        gate_passed=gate_passed,
        gate_reason=gate_reason,
        risk_veto=False,
        facts_json=json.dumps(facts or {}, ensure_ascii=False),
        pipeline_version=PIPELINE_VERSION,
        hebel_trigger_id=trigger.id,
        trigger_zweig=trigger.trigger_zweig,
        trigger_score=trigger.score_gesamt,
    )


def generate_hebel_signal(
    trigger: HebelTrigger,
    asset,
    watchlist,
    conn,
    llm_client,
    coingecko_client,
    kraken_client,
    fred_api_key: str | None = None,
) -> HebelSignal:
    dates, closes, ohlc_history, last_date = _load_closes_and_ohlc(conn, asset.symbol, asset.coingecko_id)
    latest_prices = db.get_latest_prices(conn)
    price_snap = latest_prices.get(asset.symbol)

    if len(closes) == 0:
        signal = _fixed_hebel_signal(
            trigger, "HALTEN", gate_passed=False, gate_reason="keine historischen Daten vorhanden",
        )
        db.insert_hebel_signal(conn, signal)
        return signal

    snapshot = build_technical_snapshot(closes, dates, ohlc_history)

    # Datenqualitaets-Gate (P-10), identisch zu pipeline.py::generate_signal() -
    # VOR jedem LLM-Call, kein Call bei unzureichender Datenlage.
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
        signal = _fixed_hebel_signal(trigger, "HALTEN", gate_passed=False, gate_reason=gate_reason)
        db.insert_hebel_signal(conn, signal)
        return signal

    import config as config_module

    config_dict = config_module.load_config()
    regime_result = compute_current_regime(conn, coingecko_client, watchlist, fred_api_key, config_dict)
    regime_profile = config_dict["regime"]["profile"].get(regime_result.regime, {})

    confluence = summarize_confluence(snapshot, closes[-1])

    # Deterministische Stop-Loss-Distanz (2x ATR) - dieselbe "hauseigene
    # Volatilitaets-Kennzahl" wie bei Spot (risk_gate.py::pre_check()), NICHT
    # vom spaeteren LLM-Zonen-Vorschlag abhaengig (siehe Plan, Design-Punkt 4).
    stop_loss_distance_pct = None
    current_price_usd = price_snap.price_usd if price_snap else None
    atr_value = latest_value(snapshot.atr)
    if snapshot.atr.available and atr_value is not None and current_price_usd:
        stop_loss_distance_pct = (STOP_LOSS_ATR_MULTIPLE * atr_value) / current_price_usd * 100

    holdings = db.get_all_holdings(conn)
    account_equity_usd, _ = _portfolio_values_usd(watchlist, holdings, latest_prices)

    pre_result = pre_check_hebel(
        asset, account_equity_usd, stop_loss_distance_pct, regime_result, config_dict, trigger.trigger_zweig,
    )

    anticyclic_context = assess_anticyclic(asset, kraken_client, closes)
    market_context = fetch_market_context(fred_api_key)

    open_positions = db.get_open_hebel_positions(conn, symbol=asset.symbol)
    position_aktuell = open_positions[0] if open_positions else None

    # Nachtrag 2026-07-17 (echter LINK-Fall, siehe Memory
    # project_hebel_rahmenbedingungen.md): letztes Signal fuer dasselbe
    # Symbol+dieselbe Richtung laden, damit build_hebel_facts() erkennen kann,
    # ob eine vorherige Hebel-Empfehlung offenbar nicht umgesetzt wurde.
    letztes_signal_liste = db.get_hebel_signal_history(conn, asset.symbol, trigger.richtung, limit=1)
    letztes_signal = letztes_signal_liste[0] if letztes_signal_liste else None

    price_age_minutes = None
    if price_snap is not None:
        fetched = datetime.fromisoformat(price_snap.fetched_at)
        if fetched.tzinfo is None:
            fetched = fetched.replace(tzinfo=timezone.utc)
        price_age_minutes = (datetime.now(timezone.utc) - fetched).total_seconds() / 60

    now_unix = int(datetime.now(timezone.utc).timestamp())
    historische_erfolgsquote = compute_win_rate_fact(conn, "hebel")
    historischer_makro_vergleich = get_cached_makro_analog_fact(conn)
    facts = build_hebel_facts(
        asset, price_snap, snapshot, confluence, regime_result, regime_profile,
        anticyclic_context, market_context, trigger, position_aktuell, pre_result,
        price_age_minutes, now_unix, letztes_signal,
        historische_erfolgsquote=historische_erfolgsquote,
        historischer_makro_vergleich=historischer_makro_vergleich,
    )

    try:
        parsed = call_llm_for_hebel_signal(llm_client, facts)
    except AnalystResponseInvalid as exc:
        logger.warning("Hebel-LLM-Antwort fuer %s ungueltig: %s", asset.symbol, exc)
        signal = _fixed_hebel_signal(
            trigger, "HALTEN", gate_passed=True,
            gate_reason=f"Agent-Antwort ungültig: {exc}", facts=facts,
        )
        db.insert_hebel_signal(conn, signal)
        return signal

    raw_response = parsed.pop("_raw_response", None)

    corrected = post_check_hebel(
        parsed, pre_result, regime_result, config_dict, confluence=confluence,
        retail_long_bias_extreme=anticyclic_context.retail_long_bias_extreme,
        long_account_pct=anticyclic_context.long_account_pct,
        historische_erfolgsquote=historische_erfolgsquote,
    )
    risk_veto = corrected.pop("_risk_veto")
    risk_veto_reason = corrected.pop("_risk_veto_reason")
    risikofaktoren = corrected.pop("_risikofaktoren", None)

    # Nachtrag 2026-07-17 (echter LINK-Fall - Punkt 3A+3B der Regelwerk-
    # Ueberarbeitung, siehe Memory project_hebel_rahmenbedingungen.md):
    # HEBEL_SENKEN war bisher nur ein vager Hinweis ohne konkrete Zahl UND
    # ohne klarzustellen, dass das kein Ein-Klick-Vorgang ist. Beides jetzt
    # zusammen geloest - konkreter EUR-Nachschussbetrag deterministisch
    # berechnet (Positionswert bleibt gleich, nur Eigenkapital steigt: neues
    # Eigenkapital = Positionswert / Ziel-Hebel) UND explizit im
    # Ausfuehrbarkeits-Hinweis benannt, damit die Empfehlung nicht als
    # trivial umsetzbar missverstanden wird.
    senkung_nachschuss_eur = None
    if (
        corrected.get("action") == "HEBEL_SENKEN"
        and position_aktuell is not None
        and corrected.get("hebel_final") is not None
        and position_aktuell.positionswert_eur is not None
        and corrected["hebel_final"] > 0
    ):
        ziel_eigenkapital_eur = position_aktuell.positionswert_eur / corrected["hebel_final"]
        senkung_nachschuss_eur = max(0.0, ziel_eigenkapital_eur - (position_aktuell.eigenkapital_eur or 0.0))
        hinweis_senkung = (
            f"Erfordert manuellen Eigenkapital-Nachschuss von ca. {senkung_nachschuss_eur:.2f} EUR "
            "in der Bitpanda-App (kein Ein-Klick-'Hebel senken', der Hebel selbst laesst sich bei "
            "einer offenen Position nicht direkt aendern)."
        )
        bestehender_hinweis = corrected.get("ausführbarkeit_hinweis")
        corrected["ausführbarkeit_hinweis"] = (
            f"{bestehender_hinweis} {hinweis_senkung}" if bestehender_hinweis else hinweis_senkung
        )

    long_reasoning = corrected.get("long_reasoning", {})
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

    llm_model = llm_model_label(llm_client)

    signal = HebelSignal(
        symbol=asset.symbol,
        created_at=_now(),
        richtung=corrected["richtung"],
        action=corrected["action"],
        gate_passed=True,
        gate_reason=None,
        risk_veto=risk_veto,
        risk_veto_reason=risk_veto_reason,
        facts_json=json.dumps(facts, ensure_ascii=False),
        pipeline_version=PIPELINE_VERSION,
        hebel_vorschlag=corrected.get("hebel_vorschlag"),
        hebel_final=corrected.get("hebel_final"),
        hebel_korrektur_hinweis=corrected.get("hebel_korrektur_hinweis"),
        trade_thesis_typ=corrected.get("trade_thesis_typ"),
        hebel_trigger_id=trigger.id,
        trigger_zweig=trigger.trigger_zweig,
        trigger_score=trigger.score_gesamt,
        gegenargument=corrected.get("gegenargument"),
        confidence_pct=corrected.get("confidence_pct"),
        short_reasoning=corrected.get("short_reasoning"),
        long_reasoning_technisch=long_reasoning.get("technisch"),
        long_reasoning_fundamental=long_reasoning.get("fundamental"),
        long_reasoning_makro=long_reasoning.get("makro"),
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
        liquidationspreis_geschaetzt_usd=corrected.get("liquidationspreis_geschätzt"),
        eigenkapitalbedarf_usd=corrected.get("eigenkapitalbedarf"),
        hebel_senkung_eigenkapital_nachschuss_eur=senkung_nachschuss_eur,
        ausfuehrbarkeit_hinweis=corrected.get("ausführbarkeit_hinweis"),
        groq_raw_response=raw_response,
        llm_model=llm_model,
        risikofaktoren_json=json.dumps(risikofaktoren, ensure_ascii=False) if risikofaktoren else None,
        **top_grund_fields,
    )
    db.insert_hebel_signal(conn, signal)
    db.update_hebel_trigger_status(conn, trigger.id, "llm_generiert")
    return signal
