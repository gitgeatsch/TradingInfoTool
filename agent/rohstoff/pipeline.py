"""Signal-Pipeline fuer Rohstoff-ETCs (2026-07-18, Multi-Asset-Roadmap Phase 2) -
mirror des Kontrollflusses von agent/aktien/pipeline.py::generate_signal() (Gate ->
Regime -> Technik -> Risk-Gate -> Makro-Ueberlagerung+Positionierung -> Facts -> LLM
-> Post-Check -> Signal), siehe agent/rohstoff/analyst.py Modul-Docstring fuer die
Architektur-Begruendung.

Wiederverwendet direkt (kein Duplikat): dieselben Bausteine wie die Aktien-
Pipeline (risk_gate.pre_check()/post_check(), compute_current_regime(),
build_technical_snapshot()/summarize_confluence(), Bitpanda-Listing-Check)."""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone

import numpy as np

import config
import database.db as db
from agent.krypto.backward_tracking import compute_win_rate_fact
from agent.krypto.llm_provider import llm_model_label
from agent.krypto.makro_analog import get_cached_makro_analog_fact
from agent.krypto.pipeline import MIN_GATE_INDICATORS_AVAILABLE, compute_current_regime
from agent.krypto.risk_gate import post_check, pre_check
from agent.rohstoff.analyst import (
    AnalystResponseInvalid,
    build_facts,
    call_llm_for_signal,
)
from api.cftc_cot import get_cot_snapshot
from api.macro import get_fred_latest
from api.yfinance_history import get_full_ohlc_history
from database.models import Signal
from indicators.calculations import build_technical_snapshot, summarize_confluence
from staleness import is_price_stale

logger = logging.getLogger(__name__)

PIPELINE_VERSION = "1"

# Wie bei Aktien: Boersen-/Terminmarkt-Handelszeiten, kein 24/7-Handel wie Krypto.
_ROHSTOFF_HISTORY_STALE_THRESHOLD_TAGE = 5

# ETC-Symbol -> CFTC-COT-Rohstoff-Schluessel (api/cftc_cot.py::COT_MARKET_NAMES).
# Manuell gepflegt statt automatisch abgeleitet (Symbol/Name-Heuristik waere
# fragiler) - bei einem neuen Rohstoff-ETC hier ergaenzen.
SYMBOL_ZU_COT_ROHSTOFF = {
    "OD7N": "silber",
    "OD7H": "gold",
    "OD7C": "kupfer",
    "OD7L": "erdgas",
}

# Live-Fund (2026-07-18, Verifikation dieser Pipeline): yfinance liefert fuer die
# duenn gehandelten WisdomTree-ETC-Boersennotierungen selbst (asset.yfinance_symbol,
# z.B. "OD7H.SG") KEINE .history()-Daten - nur fast_info (aktueller Preis)
# funktioniert, exakt dieselbe Einschraenkung, die 2026-07-09 bereits fuer OD7N/3QSS
# dokumentiert wurde (siehe Memory project_multi_asset_yfinance_symbols.md). Fix:
# technische Analyse (EMA/MACD/RSI/Bollinger/ATR/Fibonacci/S&R) wird stattdessen aus
# dem liquiden, kontinuierlichen Futures-Kontrakt abgeleitet, den das ETC nachbildet -
# 25+ Jahre taegliche Historie live verifiziert (GC=F/SI=F/HG=F/NG=F). Der eigentliche
# EXECUTION-Preis (preis.usd/eur in den Facts, Positionsgroessen-Berechnung) bleibt
# UNVERAENDERT der echte ETC-Kurs aus price_cache (YFinanceClient.fast_info, laeuft
# bereits ueber den bestehenden Preis-Refresh-Job). Kleine Tracking-Differenzen
# (Rollkosten, Waehrungsabsicherung, Emittenten-Marge) zwischen Future und ETC sind
# dadurch moeglich - im Prompt-Disclaimer explizit benannt (siehe build_facts()).
SYMBOL_ZU_FUTURES_TICKER = {
    "OD7N": "SI=F",
    "OD7H": "GC=F",
    "OD7C": "HG=F",
    "OD7L": "NG=F",
}

# FRED-Serien fuer die Makro-Ueberlagerung (siehe agent/rohstoff/analyst.py Regel 9) -
# DTWEXBGS wird bereits fuer den Makro-Analog-Vergleich abgerufen (agent/krypto/
# makro_analog.py), hier separat und live (nicht aus dem Cache), da die Rohstoff-
# Pipeline (wie die Aktien-Pipeline) bislang nur bei manuellem Klick laeuft.
_FRED_SERIES_MAKRO_UEBERLAGERUNG = {
    "realrendite_10j_prozent": "DFII10",
    "dxy_proxy": "DTWEXBGS",
    "industrieproduktion_index": "INDPRO",
}


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


def _is_rohstoff_history_stale(last_date: str | None) -> bool:
    if last_date is None:
        return True
    last = datetime.fromisoformat(last_date).date()
    today = datetime.now(timezone.utc).date()
    return (today - last).days > _ROHSTOFF_HISTORY_STALE_THRESHOLD_TAGE


def _ensure_ohlc_backfilled(conn, asset) -> None:
    """Fetcht die OHLC-Historie ueber den liquiden Futures-Ticker (siehe
    SYMBOL_ZU_FUTURES_TICKER-Docstring), gespeichert unter asset.symbol -
    get_full_ohlc_history()s ticker/symbol-Trennung ist genau dafuer gedacht."""
    last_date = db.get_last_ohlc_date(conn, asset.symbol, "USD")
    if last_date is not None and not _is_rohstoff_history_stale(last_date):
        return
    futures_ticker = SYMBOL_ZU_FUTURES_TICKER.get(asset.symbol)
    if futures_ticker is None:
        logger.warning("Kein Futures-Ticker fuer %s hinterlegt - keine technische Historie moeglich", asset.symbol)
        return
    ohlc_points = get_full_ohlc_history(futures_ticker, asset.symbol, "USD")
    if ohlc_points:
        db.upsert_ohlc_points(conn, ohlc_points)


def _load_ohlc(conn, symbol: str):
    ohlc_history = db.get_ohlc_history(conn, symbol, "USD")
    last_date = ohlc_history[-1].date if ohlc_history else None
    dates = np.array([o.date for o in ohlc_history])
    closes = np.array([o.close for o in ohlc_history], dtype=float)
    return dates, closes, ohlc_history, last_date


def _rescale_ohlc_zum_etc_kurs(closes: np.ndarray, ohlc_history: list, etc_preis_usd: float | None):
    """Die gespeicherte OHLC-Historie stammt vom Futures-Kontrakt (siehe
    SYMBOL_ZU_FUTURES_TICKER-Docstring), nicht vom ETC selbst - Futures- und ETC-
    Kurs liegen auf VOELLIG unterschiedlichen absoluten Preisskalen (z.B. Gold-
    Future ~4000 USD/Unze vs. ein Bruchteils-ETC bei ~18 USD). Ohne Korrektur
    waeren EMA/Bollinger/ATR/Support-Resistance/Fibonacci-Level absolute Preis-
    Level auf der FALSCHEN Skala - eine vom LLM daraus abgeleitete Stop-Loss-Zone
    waere um Groessenordnungen falsch. Fix: die GESAMTE Historie wird mit einem
    EINZIGEN, heute gueltigen Skalierungsfaktor (ETC-Kurs / letzter Futures-Kurs)
    multipliziert, bevor sie in build_technical_snapshot() geht - technische
    MUSTER (Trendrichtung, Support/Resistance-Abstaende in Prozent, Crossover-
    Zeitpunkte) bleiben dabei unveraendert, nur die absolute Preisachse wird auf
    die ETC-Groessenordnung gehoben. RSI ist ohnehin skaleninvariant (Verhaeltnis
    von Gewinn-/Verlust-Mittelwerten), MACD/EMA/Bollinger/ATR sind lineare
    Funktionen des Preises und werden durch eine konstante Multiplikation korrekt
    mitskaliert. Gibt (closes, ohlc_history) UNVERAENDERT zurueck, wenn
    etc_preis_usd fehlt oder die Historie leer ist (P-10 - dann bleibt die
    Skalen-Diskrepanz bestehen, aber der Aufrufer bekommt keinen stillen Fehler)."""
    if etc_preis_usd is None or len(closes) == 0 or closes[-1] <= 0:
        return closes, ohlc_history
    faktor = etc_preis_usd / closes[-1]
    skaliert_closes = closes * faktor
    skaliert_history = [
        type(o)(
            symbol=o.symbol, currency=o.currency, date=o.date,
            open=o.open * faktor, high=o.high * faktor, low=o.low * faktor, close=o.close * faktor,
            volume=o.volume, fetched_at=o.fetched_at,
        )
        for o in ohlc_history
    ]
    return skaliert_closes, skaliert_history


def _fetch_makro_ueberlagerung(fred_api_key: str | None) -> dict | None:
    """P-10: ein fehlgeschlagener Einzel-Call blockiert nicht die anderen - jede
    FRED-Serie wird separat versucht (mirror api/macro.py::get_all_fred_rates()).
    Gibt None zurueck, wenn KEIN FRED_API_KEY gesetzt ist (Fakt fehlt dann
    komplett statt einer leeren/irrefuehrenden Huelle)."""
    if not fred_api_key:
        return None
    werte: dict[str, float | None] = {}
    for feld, series_id in _FRED_SERIES_MAKRO_UEBERLAGERUNG.items():
        try:
            obs = get_fred_latest(series_id, fred_api_key)
            werte[feld] = obs.value
        except Exception as exc:
            logger.info("FRED-Abruf fuer %s (%s) fehlgeschlagen: %s", feld, series_id, exc)
            werte[feld] = None
    werte["hinweis"] = (
        "realrendite_10j_prozent: 10J-TIPS-Realrendite (historisch staerkster Gold-/"
        "Silber-Treiber, negativ korreliert). dxy_proxy: Dollar-Index (inverse "
        "Wirkung auf USD-notierte Rohstoffe). industrieproduktion_index: grober "
        "Industrienachfrage-Proxy, primaer fuer Kupfer relevant."
    )
    return werte


def _fetch_positionierung(symbol: str) -> dict | None:
    """CFTC-COT-Positionierung (Managed Money) - siehe api/cftc_cot.py. Gibt None
    zurueck bei unbekanntem Symbol oder Abruf-Fehlschlag (P-10)."""
    rohstoff = SYMBOL_ZU_COT_ROHSTOFF.get(symbol)
    if rohstoff is None:
        return None
    try:
        snap = get_cot_snapshot(rohstoff)
    except Exception as exc:
        logger.info("CFTC-COT-Abruf fuer %s (%s) fehlgeschlagen: %s", symbol, rohstoff, exc)
        return None
    if snap is None:
        return None
    return {
        "rohstoff": snap.rohstoff,
        "report_datum": snap.report_datum,
        "open_interest": snap.open_interest,
        "managed_money_long": snap.managed_money_long,
        "managed_money_short": snap.managed_money_short,
        "managed_money_netto": snap.managed_money_netto,
        "managed_money_long_anteil_oi_prozent": snap.managed_money_long_anteil_oi_prozent,
        "hinweis": (
            "Managed Money = grosse spekulative Fonds/CTAs laut woechentlichem "
            "CFTC-Report (~3 Tage Verzug bis Veroeffentlichung). Grobes Sentiment-"
            "Indiz, siehe Regel 10 im SYSTEM_PROMPT - kein praezises Timing-Signal."
        ),
    }


def generate_signal(asset, watchlist, conn, llm_client, coingecko_client) -> Signal:
    """Analog zu agent/aktien/pipeline.py::generate_signal(). `watchlist` muss die
    VOLLSTAENDIGE Watchlist sein (inkl. BTC) - compute_current_regime() braucht
    zwingend ein BTC-Asset darin. Fuer pre_check()'s RM-2-Allokations-Berechnung
    wird intern auf die Rohstoff-Teilmenge gefiltert (eigenes Mini-Portfolio-
    Verhaeltnis, analog zur Aktien-Pipeline)."""
    if asset.assetklasse != "rohstoffe":
        raise ValueError(f"generate_signal() (agent/rohstoff) erwartet assetklasse=='rohstoffe', bekam {asset.assetklasse!r}")

    rohstoff_watchlist = [a for a in watchlist if a.assetklasse == "rohstoffe"]

    _ensure_ohlc_backfilled(conn, asset)
    dates, closes, ohlc_history, last_date = _load_ohlc(conn, asset.symbol)
    latest_prices = db.get_latest_prices(conn)
    price_snap = latest_prices.get(asset.symbol)

    if len(closes) == 0:
        signal = _fixed_signal(asset.symbol, "HALTEN", gate_passed=False, gate_reason="keine historischen Daten vorhanden")
        db.insert_signal(conn, signal)
        return signal

    # Gate-Check FUER price_usd VOR der Skalierung (nicht erst danach, siehe unten) -
    # diese ETCs handeln in EUR (Stuttgart/XETRA), price_usd wird erst nachtraeglich
    # aus price_eur * eur_usd_fx_rate abgeleitet (api/yfinance_client.py::_fetch_one())
    # und kann fehlen, wenn beim letzten Preisabruf kein aktueller FX-Kurs vorlag -
    # OHNE price_usd kann _rescale_ohlc_zum_etc_kurs() nicht korrekt skalieren, die
    # gesamte technische Analyse waere sonst still auf der falschen (Futures-)
    # Preisskala (P-10: das darf das Gate nicht durchlassen).
    gate_problems = []
    if price_snap is None or is_price_stale(price_snap.fetched_at):
        gate_problems.append("Preis veraltet oder nicht vorhanden")
    elif price_snap.price_usd is None:
        gate_problems.append("USD-Preis nicht verfuegbar (EUR/USD-Kurs fehlte beim letzten Preisabruf)")
    if _is_rohstoff_history_stale(last_date):
        gate_problems.append(f"Historie veraltet (letzter Tag: {last_date})")

    if gate_problems:
        gate_reason = "; ".join(gate_problems)
        signal = _fixed_signal(asset.symbol, "HALTEN", gate_passed=False, gate_reason=gate_reason)
        db.insert_signal(conn, signal)
        return signal

    # Skalierung Futures-Historie -> ETC-Preisniveau (siehe SYMBOL_ZU_FUTURES_TICKER-
    # Docstring) - MUSS vor build_technical_snapshot() passieren, sonst liegen
    # EMA/Bollinger/ATR/S&R/Fibonacci auf der falschen absoluten Preisskala.
    closes, ohlc_history = _rescale_ohlc_zum_etc_kurs(closes, ohlc_history, price_snap.price_usd)

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
    except Exception as exc:
        bitpanda_gelistet = None
        logger.info("Bitpanda-Listing-Abruf fuer %s fehlgeschlagen: %s", asset.symbol, exc)

    risk_result = pre_check(asset, rohstoff_watchlist, conn, latest_prices, snapshot, regime_result, config_dict, bitpanda_gelistet)

    fred_api_key = os.environ.get("FRED_API_KEY")
    makro_ueberlagerung = _fetch_makro_ueberlagerung(fred_api_key)
    positionierung = _fetch_positionierung(asset.symbol)

    holdings = {h.symbol: h for h in db.get_all_holdings(conn)}
    price_age_minutes = None
    if price_snap is not None:
        fetched = datetime.fromisoformat(price_snap.fetched_at)
        if fetched.tzinfo is None:
            fetched = fetched.replace(tzinfo=timezone.utc)
        price_age_minutes = (datetime.now(timezone.utc) - fetched).total_seconds() / 60

    # Eigener Pool statt des Krypto+Aktien-"spot"-Pools (2026-07-18, Multi-Asset-
    # Vollstaendigkeitspruefung): Rohstoffe bewegen sich strukturell anders
    # (langsamer, andere Zyklen) - eine geliehene fremde Zahl waere irrefuehrend,
    # siehe compute_win_rate_fact()-Docstring.
    _rohstoff_symbole = {a.symbol for a in config.get_watchlist() if a.assetklasse == "rohstoffe"}
    historische_erfolgsquote = compute_win_rate_fact(conn, "spot", erlaubte_symbole=_rohstoff_symbole)
    historischer_makro_vergleich = get_cached_makro_analog_fact(conn)
    letztes_signal = db.get_latest_signal(conn, asset.symbol)

    facts = build_facts(
        asset, price_snap, holdings.get(asset.symbol), snapshot, confluence, regime_result,
        risk_result, makro_ueberlagerung, positionierung, price_age_minutes,
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
