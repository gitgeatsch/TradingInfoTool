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
from agent.krypto.backward_tracking import compute_win_rate_fact
from agent.krypto.makro_analog import get_cached_makro_analog_fact
from agent.krypto.llm_provider import llm_model_label
from agent.krypto.regime import determine_regime
from agent.krypto.risk_gate import CashReserveZielResult, compute_cash_reserve_ziel, pre_check, post_check
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


def _fetch_boden_zielzone_context(conn, config_dict: dict) -> dict:
    """Boden-Zielzone (AZ-4 Baustein 2, 2026-07-12): ETH-Log-Regression + Aktien-
    Baermarkt-Status (S&P 500/Nasdaq) fuer agent/regime.py::_boden_zielzone().
    BTC selbst braucht hier nichts (nutzt das ohnehin schon frische
    btc_log_regression_risk aus _fetch_cycle_risk_context() weiter, bewusst IMMER
    frisch wie zyklus_risiko).

    ETH + Aktien-Indizes sind dagegen ECHTE NEUE yfinance-Netzwerk-Calls -
    Tages-Cache ueber macro_snapshot (existiert fuer heute schon eine Zeile mit
    gefuelltem eth_regression_predicted_price, werden die gespeicherten Werte
    wiederverwendet statt neu abgerufen). Das verhindert, dass jeder manuelle
    "Signal berechnen"-Klick UND jeder der 2 taeglichen Marktscan-Laeufe zusaetzliche
    yfinance-Calls ausloest - compute_current_regime() laeuft sonst komplett
    ungedrosselt. _boden_zielzone() selbst wird trotzdem bei JEDEM Aufruf frisch
    gerechnet (billige Arithmetik, kein Netzwerk) - auch bei einem Cache-Treffer,
    damit eine zwischenzeitliche config.yaml-Aenderung sofort greift."""
    from api.yfinance_history import get_equities_bear_market_status, get_full_price_history, get_vix_reading
    from indicators.calculations import BtcLogRegressionRisk, compute_eth_log_regression_risk

    cfg = config_dict.get("boden_zielzone", {})
    context: dict = {
        "eth_log_regression_risk": None,
        "daempfer_staerke": cfg.get("reifegrad_daempfer_staerke", 0.0),
        "overlay_shift_std": cfg.get("equities_overlay_shift_std", 0.0),
        "equities_baermarkt_aktiv": None,
        "equities_baermarkt_begruendung": "Aktien-Bärenmarkt-Status nicht verfügbar.",
        # VIX-Fruehindikator (2026-07-18) - siehe get_vix_reading() Docstring
        # fuer die Abgrenzung zum nachlaufenden Drawdown-Status oben.
        "vix_wert": None,
    }
    if not cfg.get("aktiv", True):
        context["equities_baermarkt_begruendung"] = "Boden-Zielzone deaktiviert (config.yaml boden_zielzone.aktiv=false)."
        return context

    today = datetime.now(timezone.utc).date().isoformat()
    cached = db.get_latest_macro_snapshot(conn)
    cache_hit = (
        cached is not None and cached.date == today
        and cached.eth_regression_predicted_price is not None
    )
    sp500_drawdown_pct = nasdaq_drawdown_pct = None
    if cache_hit:
        context["eth_log_regression_risk"] = BtcLogRegressionRisk(
            date=today, current_price=0.0, predicted_price=cached.eth_regression_predicted_price,
            deviation_std=0.0, risk=0.0, residual_std=cached.eth_regression_residual_std,
        )
        sp500_drawdown_pct = cached.equities_sp500_drawdown_pct
        nasdaq_drawdown_pct = cached.equities_nasdaq_drawdown_pct
        context["vix_wert"] = cached.vix_wert
    else:
        try:
            eth_history = get_full_price_history("ETH-USD")
            context["eth_log_regression_risk"] = compute_eth_log_regression_risk(eth_history)
        except Exception as exc:
            logger.info("ETH-Log-Regression-Risk-Berechnung fehlgeschlagen: %s", exc)
        try:
            equities = get_equities_bear_market_status(
                lookback_years=cfg.get("equities_baermarkt_lookback_jahre", 5)
            )
            sp500_drawdown_pct = equities.sp500_drawdown_pct
            nasdaq_drawdown_pct = equities.nasdaq_drawdown_pct
        except Exception as exc:
            logger.info("Aktien-Bärenmarkt-Status-Abruf fehlgeschlagen: %s", exc)
        try:
            # Eigener try/except, UNABHAENGIG vom Aktien-Baermarkt-Abruf oben (P-10) -
            # ein VIX-Ausfall soll die Drawdown-Fakten nicht mit reissen und umgekehrt,
            # es sind zwei separate yfinance-Ticker-Abrufe (^VIX vs. ^GSPC/^IXIC).
            context["vix_wert"] = get_vix_reading().wert
        except Exception as exc:
            logger.info("VIX-Abruf fehlgeschlagen: %s", exc)

        elr = context["eth_log_regression_risk"]
        db.upsert_macro_snapshot(conn, MacroSnapshot(
            date=today, btc_dominance_pct=None, fear_greed_value=None, fear_greed_label=None,
            fetched_at=_now(),
            eth_regression_predicted_price=elr.predicted_price if elr else None,
            eth_regression_residual_std=elr.residual_std if elr else None,
            equities_sp500_drawdown_pct=sp500_drawdown_pct,
            equities_nasdaq_drawdown_pct=nasdaq_drawdown_pct,
            vix_wert=context["vix_wert"],
        ))

    # "aktiv"-Entscheidung: config-abhaengiger Schwellenwert-Vergleich, bewusst HIER
    # (nicht in regime.py, das komplett config-frei bleibt) - bei jedem Aufruf neu,
    # egal ob die Drawdown-Werte aus dem Cache oder frisch kommen (siehe Docstring).
    schwelle = cfg.get("equities_baermarkt_schwelle_prozent", 20)
    lookback = cfg.get("equities_baermarkt_lookback_jahre", 5)
    verknuepfung = cfg.get("equities_baermarkt_verknuepfung", "entweder")
    if sp500_drawdown_pct is None and nasdaq_drawdown_pct is None:
        context["equities_baermarkt_begruendung"] = "Aktien-Bärenmarkt-Status nicht verfügbar (Datenabruf fehlgeschlagen)."
    else:
        sp500_aktiv = sp500_drawdown_pct is not None and sp500_drawdown_pct <= -schwelle
        nasdaq_aktiv = nasdaq_drawdown_pct is not None and nasdaq_drawdown_pct <= -schwelle
        context["equities_baermarkt_aktiv"] = (
            (sp500_aktiv and nasdaq_aktiv) if verknuepfung == "beide" else (sp500_aktiv or nasdaq_aktiv)
        )
        sp500_text = f"{sp500_drawdown_pct:+.1f}%" if sp500_drawdown_pct is not None else "n/v"
        nasdaq_text = f"{nasdaq_drawdown_pct:+.1f}%" if nasdaq_drawdown_pct is not None else "n/v"
        context["equities_baermarkt_begruendung"] = (
            f"S&P 500: {sp500_text}, Nasdaq: {nasdaq_text} vom {lookback}-Jahres-Hoch "
            f"(Schwelle: -{schwelle}%, Verknüpfung: {verknuepfung}) - "
            f"{'aktiv' if context['equities_baermarkt_aktiv'] else 'nicht aktiv'}."
        )
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
    boden_zielzone_context = _fetch_boden_zielzone_context(conn, config_dict)
    btc_dates, btc_closes, btc_ohlc, _ = _load_closes_and_ohlc(conn, "BTC", btc_asset.coingecko_id)
    btc_snapshot = build_technical_snapshot(btc_closes, btc_dates, btc_ohlc)

    regime_result = determine_regime(
        btc_closes, btc_snapshot, macro_history, config_dict["regime"]["manueller_override"],
        fed_funds_history=liquidity_context["fed_funds_history"],
        m2_us_history=liquidity_context["m2_us_history"],
        m2_eurozone_history=liquidity_context["m2_eurozone_history"],
        m2_china_history=liquidity_context["m2_china_history"],
        btc_log_regression_risk=cycle_risk_context["log_regression_risk"],
        btc_onchain_reading=cycle_risk_context["onchain_reading"],
        eth_log_regression_risk=boden_zielzone_context["eth_log_regression_risk"],
        boden_zielzone_daempfer_staerke=boden_zielzone_context["daempfer_staerke"],
        equities_baermarkt_aktiv=boden_zielzone_context["equities_baermarkt_aktiv"],
        equities_baermarkt_begruendung=boden_zielzone_context["equities_baermarkt_begruendung"],
        boden_zielzone_overlay_shift_std=boden_zielzone_context["overlay_shift_std"],
        vix_wert=boden_zielzone_context["vix_wert"],
    )

    # Fertige Zone zusaetzlich zu den Cache-Rohwerten persistieren (siehe
    # _fetch_boden_zielzone_context()) - erst hier bekannt, da _boden_zielzone() erst
    # innerhalb von determine_regime() laeuft. Reiner Verlaufszweck (Nutzer-Wunsch
    # 2026-07-12: Verschiebung der Zone ueber Zeit nachvollziehbar machen), beeinflusst
    # keine Entscheidung - ein Fehlschlag hier darf die Regime-Berechnung nicht kippen.
    # 2026-07-17 (Regime-Status-Anzeige): zusaetzlich zyklus_risiko/liquiditaets_regime/
    # btc_trend_label/regime_reason persistiert - bisher nirgends gespeichert, obwohl
    # hier bereits fertig berechnet. Reine Persistierungs-Erweiterung, kein neuer
    # Netzwerk-Call - macht die Werte fuer eine passive "letzter bekannter Stand"-Anzeige
    # verfuegbar (agent/krypto/regime.py::get_last_known_regime_status()).
    try:
        today = datetime.now(timezone.utc).date().isoformat()
        db.upsert_macro_snapshot(conn, MacroSnapshot(
            date=today, btc_dominance_pct=None, fear_greed_value=None, fear_greed_label=None,
            fetched_at=_now(),
            btc_boden_zielzone_von=regime_result.btc_boden_zielzone_von,
            btc_boden_zielzone_bis=regime_result.btc_boden_zielzone_bis,
            eth_boden_zielzone_von=regime_result.eth_boden_zielzone_von,
            eth_boden_zielzone_bis=regime_result.eth_boden_zielzone_bis,
            zyklus_risiko=regime_result.zyklus_risiko,
            zyklus_risiko_begruendung=regime_result.zyklus_risiko_begruendung,
            liquiditaets_regime=regime_result.liquiditaets_regime,
            liquiditaets_regime_begruendung=regime_result.liquiditaets_regime_begruendung,
            btc_trend_label=regime_result.btc_trend_label,
            regime_reason=regime_result.reason,
        ))
    except Exception:
        logger.exception("Boden-Zielzone-Verlaufs-Persistierung fehlgeschlagen (unkritisch)")

    return regime_result


def _compute_cash_reserve_ziel_context(
    conn, watchlist, regime_result, config_dict: dict, latest_prices: dict
) -> CashReserveZielResult | None:
    """AZ-4 Baustein 3 (2026-07-12): siehe agent/krypto/risk_gate.py::
    compute_cash_reserve_ziel() fuer die Methodik. Bewusst OHNE den per-Asset-DCA-
    Toggle (anders als tranchen_erlaubt unten) - Cash-Reserve-Ziel ist ein
    portfolioweiter Informationswert, keine Tranchen-Vorschlag-Einstellung. Reine
    DB-Reads (keine Netzwerk-Calls), daher kein Cache noetig - wird nur aufgerufen,
    wenn das aktuell zu bewertende Asset selbst BTC oder ETH ist (siehe
    generate_signal()), nicht bei jedem Alt-Coin-Signal."""
    if regime_result.regime not in ("baer", "krise_extrem", "seitwaerts"):
        return None

    btc_asset = next((a for a in watchlist if a.symbol == "BTC"), None)
    eth_asset = next((a for a in watchlist if a.symbol == "ETH"), None)
    if btc_asset is None or eth_asset is None:
        return None

    btc_dates, btc_closes, btc_ohlc, _ = _load_closes_and_ohlc(conn, "BTC", btc_asset.coingecko_id)
    btc_snapshot = build_technical_snapshot(btc_closes, btc_dates, btc_ohlc)
    btc_risk_result = pre_check(
        btc_asset, watchlist, conn, latest_prices, btc_snapshot, regime_result, config_dict,
        bitpanda_gelistet=None,
    )

    eth_dates, eth_closes, eth_ohlc, _ = _load_closes_and_ohlc(conn, "ETH", eth_asset.coingecko_id)
    eth_snapshot = build_technical_snapshot(eth_closes, eth_dates, eth_ohlc)
    eth_risk_result = pre_check(
        eth_asset, watchlist, conn, latest_prices, eth_snapshot, regime_result, config_dict,
        bitpanda_gelistet=None,
    )

    cfg = config_dict.get("cash_reserve_ziel", {})
    rundengewichte = tuple(cfg.get("rundengewichte", (20.0, 30.0, 50.0)))
    return compute_cash_reserve_ziel(btc_risk_result, eth_risk_result, rundengewichte)


def generate_signal(
    asset, watchlist, conn, groq_client, coingecko_client, kraken_client,
    fred_api_key: str | None = None,
) -> Signal:
    # A-1: Stablecoins/Cash-Aequivalente haben kein eigenstaendiges Handelssignal.
    if asset.ist_cash_aequivalent:
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

    # RM-Bitpanda: Handelsboersen-Check (analog marktscan.py) - einmal pro Signal-Lauf,
    # kein Cache noetig (oeffentlicher, unauthentifizierter Endpunkt, ein Lauf dauert
    # ohnehin schon mehrere Sekunden wegen Groq/Regime/Makro).
    try:
        from api.bitpanda import get_listed_assets
        from api.bitpanda import is_listed as bitpanda_is_listed

        bitpanda_assets = get_listed_assets()
        bitpanda_gelistet = bitpanda_is_listed(asset.symbol, bitpanda_assets, name=asset.name)
    except Exception as exc:
        bitpanda_gelistet = None
        logger.info("Bitpanda-Listing-Abruf fehlgeschlagen: %s", exc)

    # R-5.5 (pre) Risikopruefung.
    risk_result = pre_check(
        asset, watchlist, conn, latest_prices, snapshot, regime_result, config_dict, bitpanda_gelistet,
    )

    # R-5.11 Antizyklik-Heuristik.
    anticyclic_context = assess_anticyclic(asset, kraken_client, closes)

    market_context = fetch_market_context()

    holdings = {h.symbol: h for h in db.get_all_holdings(conn)}
    # Wiederholungs-Erkennung (2026-07-17, siehe analyst.py::build_facts()
    # Konstanten-Docstring) - letztes Signal fuer dieses Symbol VOR dem
    # Schreiben des neuen, damit build_facts() die vorherige Empfehlung mit
    # dem aktuellen Haltebestand vergleichen kann.
    letztes_signal = db.get_latest_signal(conn, asset.symbol)
    strategien_aktiv = [s["name"] for s in config_dict["strategien"] if s["aktiv"]]
    price_age_minutes = None
    if price_snap is not None:
        fetched = datetime.fromisoformat(price_snap.fetched_at)
        if fetched.tzinfo is None:
            fetched = fetched.replace(tzinfo=timezone.utc)
        price_age_minutes = (datetime.now(timezone.utc) - fetched).total_seconds() / 60

    # AZ-4-Tranchen (2026-07-12, 2026-07-18 um SOL erweitert): nur Regime
    # baer/krise_extrem/seitwaerts + BTC/ETH/SOL + per-Asset-Toggle
    # (ui/app.py Watchlist-Tab, Default an fuer BTC/ETH/SOL) - siehe
    # Regelwerksmanual Kap. 4. Bewusst weiterhin eine feste Liste statt
    # "alle core-Assets" - Tranchen sind fuer die groessten, liquidesten
    # Positionen gedacht, keine pauschale Ausweitung auf jedes core-Asset.
    tranchen_erlaubt = (
        regime_result.regime in ("baer", "krise_extrem", "seitwaerts")
        and asset.symbol in ("BTC", "ETH", "SOL")
        and db.get_dca_erlaubt(conn, asset.symbol)
    )

    # Cash-Reserve-Ziel (AZ-4 Baustein 3, 2026-07-12): nur berechnen, wenn das
    # aktuelle Asset selbst BTC/ETH ist - kein unnoetiger Mehraufwand fuer
    # Alt-Coin-Signale, die das Ergebnis ohnehin nicht anzeigen (siehe
    # ui/signals_view.py). Regime-Bedingung wird innerhalb der Funktion geprueft.
    cash_reserve_ziel = (
        _compute_cash_reserve_ziel_context(conn, watchlist, regime_result, config_dict, latest_prices)
        if asset.symbol in ("BTC", "ETH") else None
    )

    # Krypto+Aktien bleiben bewusst als "spot"-Pool zusammen (aehnliches
    # Momentum-/CRV-Profil, fruehere dokumentierte Entscheidung) - Rohstoffe/
    # Hedge/Themen-ETF NICHT mehr stillschweigend mit hineingezogen (2026-07-18,
    # siehe compute_win_rate_fact()-Docstring). `config.get_watchlist()` statt
    # dem lokalen (Krypto-gefilterten) `watchlist`-Parameter, da hier auch die
    # Aktien-Symbole gebraucht werden.
    _spot_pool_symbole = {a.symbol for a in config.get_watchlist() if a.assetklasse in ("krypto", "aktien")}
    historische_erfolgsquote = compute_win_rate_fact(conn, "spot", erlaubte_symbole=_spot_pool_symbole)
    historischer_makro_vergleich = get_cached_makro_analog_fact(conn)

    facts = build_facts(
        asset, price_snap, holdings.get(asset.symbol), snapshot, confluence, regime_result,
        regime_profile, risk_result, anticyclic_context, strategien_aktiv, price_age_minutes,
        market_context, bitpanda_gelistet, tranchen_erlaubt, cash_reserve_ziel,
        letztes_signal=letztes_signal,
        historische_erfolgsquote=historische_erfolgsquote,
        historischer_makro_vergleich=historischer_makro_vergleich,
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
    corrected = post_check(
        parsed, risk_result, regime_result, config_dict, confluence=confluence,
        retail_long_bias_extreme=anticyclic_context.retail_long_bias_extreme,
        long_account_pct=anticyclic_context.long_account_pct,
    )
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
        tauschen_target_symbol=corrected.get("tauschen_target_symbol"),
        tranchen_json=(
            json.dumps(corrected["tranchen"], ensure_ascii=False)
            if corrected.get("tranchen") else None
        ),
        cash_reserve_ziel_btc_usd=cash_reserve_ziel.btc_ziel_usd if cash_reserve_ziel else None,
        cash_reserve_ziel_eth_usd=cash_reserve_ziel.eth_ziel_usd if cash_reserve_ziel else None,
        cash_reserve_ziel_gesamt_usd=cash_reserve_ziel.gesamt_ziel_usd if cash_reserve_ziel else None,
        cash_reserve_ziel_begruendung=cash_reserve_ziel.begruendung if cash_reserve_ziel else None,
        gegenargument=corrected.get("gegenargument"),
        groq_raw_response=raw_response,
        groq_model=llm_model_label(groq_client),
        **top_grund_fields,
    )
    db.insert_signal(conn, signal)
    return signal
