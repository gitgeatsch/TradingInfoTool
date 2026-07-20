"""Signal-Pipeline fuer Themen-ETFs (2026-07-18, Multi-Asset-Vollstaendigkeitspruefung) -
mirror des Kontrollflusses von agent/rohstoff/pipeline.py::generate_signal() (Gate ->
Regime -> Technik -> Risk-Gate -> Sektor-Rotation -> Facts -> LLM -> Post-Check ->
Signal), siehe agent/themen_etf/analyst.py Modul-Docstring fuer die
Architektur-Begruendung.

Wiederverwendet direkt (kein Duplikat): dieselben Bausteine wie die Rohstoff-Pipeline
(risk_gate.pre_check()/post_check(), compute_current_regime(),
build_technical_snapshot()/summarize_confluence(), Bitpanda-Listing-Check).

WICHTIGER UNTERSCHIED zur Rohstoff-Pipeline: KEIN Futures-Proxy fuer die technische
Historie - anders als die duenn gehandelten WisdomTree-ETCs haben die meisten
UCITS-Themen-ETFs eine echte, direkt handelbare yfinance-.history() (live verifiziert:
VVMX/EXH3/CEBS funktionieren). X136 (Boerse Berlin) und teilweise ISOC liefern
unvollstaendige/veraltete Historie - fuer diese greift schlicht das bestehende
Staleness-Gate (gate_passed=False), KEIN Workaround gebaut (P-10: sauber degradieren
statt eine fragile Ersatzloesung erzwingen)."""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

import numpy as np

import agent.kategorie_thesen as kategorie_thesen
import config
import database.db as db
from agent.krypto.backward_tracking import compute_win_rate_fact
from agent.krypto.llm_provider import llm_model_label
from agent.krypto.makro_analog import get_cached_makro_analog_fact
from agent.krypto.pipeline import MIN_GATE_INDICATORS_AVAILABLE, compute_current_regime
from agent.krypto.risk_gate import post_check, pre_check
from agent.themen_etf.analyst import (
    AnalystResponseInvalid,
    build_facts,
    call_llm_for_signal,
)
from api.yfinance_history import get_full_ohlc_history
from database.models import Signal
from indicators.calculations import build_technical_snapshot, summarize_confluence
from staleness import is_price_stale

logger = logging.getLogger(__name__)

PIPELINE_VERSION = "1"

# Wie bei Aktien/Rohstoffen: Boersenhandelszeiten, kein 24/7-Handel wie Krypto.
_THEMEN_ETF_HISTORY_STALE_THRESHOLD_TAGE = 5

# Breiter Markt-Benchmark fuer die Sektor-Rotations-Berechnung (siehe
# agent/themen_etf/analyst.py Regel 9) - SPY statt eines MSCI-World-Proxys, da SPY
# garantiert liquide/vollstaendige yfinance-Historie hat und als "breiter Markt"-
# Referenz fuer eine relative Staerke-Betrachtung ausreicht. Gespeichert unter einem
# synthetischen Symbol, das mit keinem echten Watchlist-Symbol kollidiert.
_BENCHMARK_TICKER = "SPY"
_BENCHMARK_SYMBOL = "_THEMEN_ETF_BENCHMARK_SPY"

# Trading-Tage-Fenster fuer die relative Staerke (~1 bzw. ~3 Kalendermonate).
_ROTATION_FENSTER_TAGE = {"30d": 21, "90d": 63}


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


def _is_history_stale(last_date: str | None) -> bool:
    if last_date is None:
        return True
    last = datetime.fromisoformat(last_date).date()
    today = datetime.now(timezone.utc).date()
    return (today - last).days > _THEMEN_ETF_HISTORY_STALE_THRESHOLD_TAGE


def _ensure_ohlc_backfilled(conn, asset) -> None:
    last_date = db.get_last_ohlc_date(conn, asset.symbol, "USD")
    if last_date is not None and not _is_history_stale(last_date):
        return
    if not asset.yfinance_symbol:
        logger.warning("Kein yfinance-Symbol fuer %s hinterlegt - keine technische Historie moeglich", asset.symbol)
        return
    ohlc_points = get_full_ohlc_history(asset.yfinance_symbol, asset.symbol, "USD")
    if ohlc_points:
        db.upsert_ohlc_points(conn, ohlc_points)


def _ensure_benchmark_backfilled(conn) -> None:
    last_date = db.get_last_ohlc_date(conn, _BENCHMARK_SYMBOL, "USD")
    if last_date is not None and not _is_history_stale(last_date):
        return
    try:
        ohlc_points = get_full_ohlc_history(_BENCHMARK_TICKER, _BENCHMARK_SYMBOL, "USD")
        if ohlc_points:
            db.upsert_ohlc_points(conn, ohlc_points)
    except Exception as exc:
        logger.info("Benchmark-Historie (%s) fehlgeschlagen: %s", _BENCHMARK_TICKER, exc)


def _load_ohlc(conn, symbol: str):
    ohlc_history = db.get_ohlc_history(conn, symbol, "USD")
    last_date = ohlc_history[-1].date if ohlc_history else None
    dates = np.array([o.date for o in ohlc_history])
    closes = np.array([o.close for o in ohlc_history], dtype=float)
    return dates, closes, ohlc_history, last_date


def _relative_staerke_pct(etf_closes: np.ndarray, benchmark_closes: np.ndarray, fenster_tage: int) -> float | None:
    if len(etf_closes) <= fenster_tage or len(benchmark_closes) <= fenster_tage:
        return None
    etf_perf = (etf_closes[-1] / etf_closes[-1 - fenster_tage] - 1.0) * 100
    benchmark_perf = (benchmark_closes[-1] / benchmark_closes[-1 - fenster_tage] - 1.0) * 100
    return round(etf_perf - benchmark_perf, 2)


def _compute_sektor_rotation(conn, symbol: str, etf_closes: np.ndarray) -> dict | None:
    """Relative Staerke des Themen-ETFs gegenueber SPY ueber 30/90 Handelstage
    (siehe Modul-Docstring). Gibt None zurueck, wenn die Benchmark-Historie fehlt
    oder eine der beiden Reihen zu kurz ist (P-10 - der Fakt wird dann im Prompt
    einfach weggelassen, siehe analyst.py Regel 9)."""
    _, benchmark_closes, _, _ = _load_ohlc(conn, _BENCHMARK_SYMBOL)
    if len(benchmark_closes) == 0:
        return None

    rel_30d = _relative_staerke_pct(etf_closes, benchmark_closes, _ROTATION_FENSTER_TAGE["30d"])
    rel_90d = _relative_staerke_pct(etf_closes, benchmark_closes, _ROTATION_FENSTER_TAGE["90d"])
    if rel_30d is None and rel_90d is None:
        return None

    return {
        "benchmark": "SPY (S&P 500 ETF, Proxy fuer 'breiter Markt')",
        "relative_staerke_30d_pct": rel_30d,
        "relative_staerke_90d_pct": rel_90d,
        "hinweis": (
            "Positiv = Outperformance gegenueber dem breiten Markt (Sektor 'in Rotation'), "
            "negativ = Underperformance. Reines Kurs-Momentum-Indiz, siehe SYSTEM_PROMPT Regel 9."
        ),
    }


def generate_signal(asset, watchlist, conn, llm_client, coingecko_client) -> Signal:
    """Analog zu agent/rohstoff/pipeline.py::generate_signal(). `watchlist` muss die
    VOLLSTAENDIGE Watchlist sein (inkl. BTC) - compute_current_regime() braucht
    zwingend ein BTC-Asset darin. Fuer pre_check()'s RM-2-Allokations-Berechnung wird
    intern auf die Themen-ETF-Teilmenge gefiltert (eigenes Mini-Portfolio-Verhaeltnis,
    analog zur Rohstoff-Pipeline). Die Hedge-Instrumente DBPK/3QSS haben zwar
    ebenfalls assetklasse=='etf', werden hier aber bewusst NICHT mit hineingezaehlt
    (eigene Pipeline, eigene Logik, siehe agent/hedge/) - Aufrufer muss ein Symbol
    ausserhalb von agent.hedge.pipeline.SYMBOL_ZU_HEBEL_FAKTOR uebergeben."""
    from agent.hedge.pipeline import SYMBOL_ZU_HEBEL_FAKTOR as _hedge_symbole

    if asset.assetklasse != "etf" or asset.symbol in _hedge_symbole:
        raise ValueError(
            f"generate_signal() (agent/themen_etf) erwartet ein Themen-ETF (assetklasse=='etf', "
            f"nicht in SYMBOL_ZU_HEBEL_FAKTOR), bekam {asset.symbol!r} (assetklasse={asset.assetklasse!r})"
        )

    themen_etf_watchlist = [
        a for a in watchlist if a.assetklasse == "etf" and a.symbol not in _hedge_symbole
    ]

    _ensure_ohlc_backfilled(conn, asset)
    _ensure_benchmark_backfilled(conn)
    dates, closes, ohlc_history, last_date = _load_ohlc(conn, asset.symbol)
    latest_prices = db.get_latest_prices(conn)
    price_snap = latest_prices.get(asset.symbol)

    if len(closes) == 0:
        signal = _fixed_signal(asset.symbol, "HALTEN", gate_passed=False, gate_reason="keine historischen Daten vorhanden")
        db.insert_signal(conn, signal)
        return signal

    gate_problems = []
    if price_snap is None or is_price_stale(price_snap.fetched_at):
        gate_problems.append("Preis veraltet oder nicht vorhanden")
    elif price_snap.price_usd is None:
        gate_problems.append("USD-Preis nicht verfuegbar (EUR/USD-Kurs fehlte beim letzten Preisabruf)")
    if _is_history_stale(last_date):
        gate_problems.append(f"Historie veraltet (letzter Tag: {last_date})")

    if gate_problems:
        gate_reason = "; ".join(gate_problems)
        signal = _fixed_signal(asset.symbol, "HALTEN", gate_passed=False, gate_reason=gate_reason)
        db.insert_signal(conn, signal)
        return signal

    snapshot = build_technical_snapshot(closes, dates, ohlc_history)

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
    regime_result = compute_current_regime(conn, coingecko_client, watchlist, None, config_dict)

    confluence = summarize_confluence(snapshot, closes[-1])

    try:
        from api.bitpanda import get_listed_non_crypto_assets
        from api.bitpanda import is_listed as bitpanda_is_listed

        bitpanda_assets = get_listed_non_crypto_assets()
        bitpanda_gelistet = bitpanda_is_listed(asset.symbol, bitpanda_assets, name=asset.name)
        # Bitpanda-Gelistet-Override (2026-07-20, siehe database/db.py::
        # asset_bitpanda_override-Tabellendocstring): /v3/assets ist fuer
        # Bitpandas "Bitpanda Stocks"-Fractional-ETF/ETC-Produktlinie keine
        # vollstaendige Quelle - Nutzer bestaetigt per Override manuell, dass
        # ein Symbol trotz negativem Live-Check tatsaechlich handelbar ist.
        if not bitpanda_gelistet and db.get_bitpanda_gelistet_override(conn, asset.symbol):
            bitpanda_gelistet = True
    except Exception as exc:
        bitpanda_gelistet = None
        logger.info("Bitpanda-Listing-Abruf fuer %s fehlgeschlagen: %s", asset.symbol, exc)

    risk_result = pre_check(asset, themen_etf_watchlist, conn, latest_prices, snapshot, regime_result, config_dict, bitpanda_gelistet)

    sektor_rotation = _compute_sektor_rotation(conn, asset.symbol, closes)

    holdings = {h.symbol: h for h in db.get_all_holdings(conn)}
    price_age_minutes = None
    if price_snap is not None:
        fetched = datetime.fromisoformat(price_snap.fetched_at)
        if fetched.tzinfo is None:
            fetched = fetched.replace(tzinfo=timezone.utc)
        price_age_minutes = (datetime.now(timezone.utc) - fetched).total_seconds() / 60

    # Eigener Pool statt des Krypto+Aktien-"spot"-Pools (siehe
    # compute_win_rate_fact()-Docstring) - Themen-ETFs sind qualitativ anders
    # (langsamer, Sektor-Rotation statt Einzeltitel-/Krypto-Momentum).
    _themen_etf_symbole = {a.symbol for a in themen_etf_watchlist}
    historische_erfolgsquote = compute_win_rate_fact(conn, "spot", erlaubte_symbole=_themen_etf_symbole)
    historischer_makro_vergleich = get_cached_makro_analog_fact(conn)
    letztes_signal = db.get_latest_signal(conn, asset.symbol)
    these_abgleich = kategorie_thesen.build_these_abgleich_fact(conn, asset)

    facts = build_facts(
        asset, price_snap, holdings.get(asset.symbol), snapshot, confluence, regime_result,
        risk_result, sektor_rotation, price_age_minutes,
        historische_erfolgsquote=historische_erfolgsquote,
        historischer_makro_vergleich=historischer_makro_vergleich,
        letztes_signal=letztes_signal,
        these_abgleich=these_abgleich,
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
