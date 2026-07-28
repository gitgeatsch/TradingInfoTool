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
import threading
from datetime import datetime, timezone

import database.db as db
from agent.krypto.analyst import AnalystResponseInvalid
from agent.krypto.anticyclic import assess as assess_anticyclic
from agent.krypto.backward_tracking import (
    DEFAULT_RICHTUNGSTREFFER_MINDEST_CRV,
    compute_win_rate_fact,
    mindestziel_preis,
    schaetze_mindestziel_zeitraum_tage,
)
from agent.krypto.btc_relativwert import btc_relativwert_fakt
from agent.krypto.gegenpruefung import (
    baue_fakten as baue_zai_fakten,
    baue_objektive_fakten as baue_zai_objektive_fakten,
    fuehre_beide_calls_im_hintergrund,
)
from agent.krypto.hebel_analyst import build_hebel_facts, call_llm_for_hebel_signal
from agent.krypto.hebel_screening import (
    classify_squeeze_divergenz,
    compute_funding_rate_percentile,
    compute_oi_change_pct,
)
from agent.krypto.liquidity_zones import liquiditaetszonen_fakt
from agent.krypto.makro_analog import distill_makro_vergleich_fuer_hebel, get_cached_makro_analog_fact
from agent.krypto.optionsmarkt import fetch_optionsmarkt_fakt
from agent.krypto.signal_stabilitaet import (
    DEFAULT_ANZAHL_ZYKLEN, juengste_richtungswende, signal_stabilitaet_fakt,
)
from agent.krypto.hebel_risk_gate import post_check_hebel, pre_check_hebel
from agent.krypto.llm_provider import llm_model_label
from agent.krypto.pipeline import (
    _load_closes_and_ohlc, compute_current_regime, eur_aus_usd, fetch_market_context,
    jit_refresh_asset_historie, log_eur_abweichungen,
)
from agent.krypto.regime import regime_persistenz_tage
from agent.krypto.risk_gate import STOP_LOSS_ATR_MULTIPLE, _portfolio_values_usd
from database.models import HebelSignal, HebelTrigger
from indicators.calculations import (
    build_technical_snapshot, compute_btc_relativwert, latest_value, summarize_confluence,
)
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
    zai_client=None,
) -> HebelSignal:
    jit_refresh_asset_historie(conn, asset, coingecko_client, kraken_client)
    dates, closes, ohlc_history, last_date = _load_closes_and_ohlc(conn, asset.symbol, asset.coingecko_id)
    latest_prices = db.get_latest_prices(conn)
    price_snap = latest_prices.get(asset.symbol)
    # Nachtrag 2026-07-23 (Nutzer-Fund am Signal-Detail-Panel): gleiche
    # kostenlose EURCV-Ableitung wie risk_gate.py::pre_check() - macht
    # Liquidationspreis/Eigenkapitalbedarf zusaetzlich in EUR berechenbar,
    # ohne einen neuen API-Call.
    eurcv_snap = latest_prices.get("EURCV")
    eur_usd_fx_rate = (
        eurcv_snap.price_usd / eurcv_snap.price_eur
        if eurcv_snap and eurcv_snap.price_usd and eurcv_snap.price_eur else None
    )

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
    # Regime-Persistenz (2026-07-26) - siehe regime.py::regime_persistenz_tage()
    # Docstring. Nur bei regelbasiertem Regime sinnvoll (sonst waere
    # `regime_result.regime` selbst schon ein manueller Wert, siehe dortige
    # Erlaeuterung) - bei aktivem Override bleibt der Wert None (P-8, kein
    # harter Block, hebel_risk_gate.py haengt dann einfach keinen
    # Persistenz-Satz an den Regime-Konflikt/-Ausrichtung-Text an).
    regime_persistenz_tage_wert = (
        regime_persistenz_tage(conn, regime_result.regime)
        if regime_result.source == "regelbasiert" else None
    )

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
    # TEMPORAER (2026-07-25, Diagnose fuer den HYPE-Fund vom selben Tag - siehe
    # project_hebel_kontrathese_uebersetzung.md): zwei nicht reproduzierbare
    # Faelle, in denen die Kontrathese-Uebersetzung trotz offener Position nicht
    # gefeuert hat. Vergleicht diesen Fetch mit dem Log in hebel_risk_gate.py::
    # post_check_hebel() - divergieren beide, ist es ein Durchreiche-Bug,
    # stimmen sie ueberein und die Uebersetzung feuert trotzdem nicht, liegt es
    # an der Bedingung selbst. Nach Reproduktion/Diagnose wieder entfernen.
    if position_aktuell is not None:
        logger.info(
            "Kontrathese-Debug hebel_pipeline %s: angeforderte Trigger-Richtung=%s, "
            "gefundene offene Positionen=%d, position_aktuell.richtung=%s, position_aktuell.status=%s",
            asset.symbol, trigger.richtung, len(open_positions),
            position_aktuell.richtung, position_aktuell.status,
        )

    # Nachtrag 2026-07-17 (echter LINK-Fall, siehe Memory
    # project_hebel_rahmenbedingungen.md): letztes Signal fuer dasselbe
    # Symbol+dieselbe Richtung laden, damit build_hebel_facts() erkennen kann,
    # ob eine vorherige Hebel-Empfehlung offenbar nicht umgesetzt wurde.
    letztes_signal_liste = db.get_hebel_signal_history(conn, asset.symbol, trigger.richtung, limit=1)
    letztes_signal = letztes_signal_liste[0] if letztes_signal_liste else None

    # Kontrathese-Zeitfenster-Bestaetigung (2026-07-24, siehe hebel_risk_gate.py::
    # _kontrathese_bestaetigt_seit_stunden()) - nur relevant, wenn eine offene
    # Position existiert; 30 Eintraege bei 15-Min-Screening-Takt decken ca. 7,5h
    # ab, komfortabel ueber der Standard-Bestaetigungsschwelle (2h).
    kontrathese_verlauf = (
        db.get_hebel_signal_history(conn, asset.symbol, position_aktuell.richtung, limit=30)
        if position_aktuell is not None else []
    )

    price_age_minutes = None
    if price_snap is not None:
        fetched = datetime.fromisoformat(price_snap.fetched_at)
        if fetched.tzinfo is None:
            fetched = fetched.replace(tzinfo=timezone.utc)
        price_age_minutes = (datetime.now(timezone.utc) - fetched).total_seconds() / 60

    now_unix = int(datetime.now(timezone.utc).timestamp())
    historische_erfolgsquote = compute_win_rate_fact(conn, "hebel")
    # 2026-07-28 (Punkt 5 der Fakten_Entscheidungsmappe.md-Prioritaetenliste):
    # verschlankte Fassung statt der vollen Analog-Liste (siehe agent/krypto/
    # pipeline.py fuer die volle Fassung, unveraendert bei Spot) - siehe
    # distill_makro_vergleich_fuer_hebel()-Docstring fuer die Begruendung.
    historischer_makro_vergleich = distill_makro_vergleich_fuer_hebel(get_cached_makro_analog_fact(conn))
    # Liquiditaetszonen (Marketmaker-Konzept, Stufe 1, 2026-07-23) - rein
    # informativ, siehe agent/krypto/liquidity_zones.py Modul-Docstring.
    liquiditaetszonen = liquiditaetszonen_fakt(
        snapshot, current_price_usd, config_dict, dates, closes, eur_usd_fx_rate=eur_usd_fx_rate,
    )
    # Signal-Stabilitaet (2026-07-25, echter NEAR/LINK-Fund) - letzte Bewertungen
    # VOR diesem Lauf fuer dasselbe (Symbol, Richtung), siehe agent/krypto/
    # signal_stabilitaet.py Modul-Docstring. Zyklenzahl konfigurierbar, Default
    # ueber DEFAULT_ANZAHL_ZYKLEN, damit dieselbe Zahl fuer Query-Limit UND
    # Auswertung gilt (kein stiller Mismatch zwischen beiden).
    signal_stabilitaet_verlauf = db.get_hebel_signal_history(
        conn, asset.symbol, trigger.richtung,
        limit=config_dict.get("signal_stabilitaet", {}).get("anzahl_zyklen", DEFAULT_ANZAHL_ZYKLEN),
    )
    signal_stabilitaet = signal_stabilitaet_fakt(signal_stabilitaet_verlauf, config_dict)
    # Richtungswende (2026-07-25, echter INJ-Fund) - eigener Risikofaktor statt
    # Teil der Signal-Stabilitaet, siehe hebel_risk_gate.py::
    # richtungswende_risikofaktor() Docstring. Nutzt denselben Verlauf wie oben.
    richtungswende = juengste_richtungswende(signal_stabilitaet_verlauf)
    # Volatilitaets-Perzentil (2026-07-25, Baustein 2) - snapshot.atr_percentile
    # ist bereits Teil von build_technical_snapshot() (indicators/calculations.py),
    # hier nur der konfigurierbare aktiv-Toggle (kein eigenes Modul noetig).
    atr_perzentil = (
        latest_value(snapshot.atr_percentile)
        if config_dict.get("volatilitaets_perzentil", {}).get("aktiv", True) else None
    )
    # BTC-Relativwert (Baustein 1, 2026-07-25) - Self-Comparison-Guard: BTC
    # braucht keinen Vergleich zu sich selbst. Siehe agent/krypto/pipeline.py
    # (Spot-Pendant) fuer die identische Herleitung.
    btc_relativwert = None
    if asset.symbol != "BTC" and config_dict.get("btc_relativwert", {}).get("aktiv", True):
        btc_asset = next((a for a in watchlist if a.symbol == "BTC"), None)
        if btc_asset is not None:
            btc_dates, btc_closes, _btc_ohlc, _btc_last_date = _load_closes_and_ohlc(
                conn, "BTC", btc_asset.coingecko_id,
            )
            btc_relativwert_ergebnis = compute_btc_relativwert(dates, closes, btc_dates, btc_closes)
            btc_relativwert = btc_relativwert_fakt(btc_relativwert_ergebnis, config_dict)
    # Optionsmarkt (Punkt 2 des Regime-Persistenz-Folge-Vorschlags, 2026-07-26) -
    # immer BTC (marktweiter Barometer), unabhaengig vom Coin dieses Signals,
    # siehe agent/krypto/optionsmarkt.py Modul-Docstring fuer die Live-Fetch-
    # statt-Caching-Begruendung.
    optionsmarkt = fetch_optionsmarkt_fakt(config_dict)
    # OI-Squeeze-Divergenz + Funding-Rate-Perzentil (2026-07-28, Abschnitt 6
    # Fakten-Entscheidungsmappe Punkt 2+3) - siehe agent/krypto/pipeline.py
    # (Spot-Pendant) fuer die volle Begruendung, insbesondere warum ein
    # EIGENES Lookback-Fenster noetig ist statt trigger.oi_change_pct_lookback
    # (4h Trendfolge-Fenster, zeitlich nicht vergleichbar mit dem 3-Tage-
    # Kursfenster dieses neuen Fakts).
    _oi_cfg = config_dict.get("krypto_oi_fakten", {})
    oi_change_pct = compute_oi_change_pct(
        conn, asset.symbol, "binance", _oi_cfg.get("squeeze_oi_lookback_stunden", 72),
    )
    squeeze_divergenz = classify_squeeze_divergenz(
        oi_change_pct, anticyclic_context.recent_drop_pct,
        _oi_cfg.get("squeeze_schwelle_prozent", 1.0),
    )
    funding_rate_perzentil = latest_value(compute_funding_rate_percentile(conn, asset.symbol))
    facts = build_hebel_facts(
        asset, price_snap, snapshot, confluence, regime_result, regime_profile,
        anticyclic_context, market_context, trigger, position_aktuell, pre_result,
        price_age_minutes, now_unix, letztes_signal,
        historische_erfolgsquote=historische_erfolgsquote,
        historischer_makro_vergleich=historischer_makro_vergleich,
        liquiditaetszonen=liquiditaetszonen,
        signal_stabilitaet=signal_stabilitaet,
        btc_relativwert=btc_relativwert,
        optionsmarkt=optionsmarkt,
        squeeze_divergenz=squeeze_divergenz,
        funding_rate_perzentil=funding_rate_perzentil,
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

    # Nur-Long-Deckel (2026-07-28, echter NEAR/TAO-Fund): der Kandidaten-Filter
    # in budget_allocator.py filtert nur nach trigger.richtung VOR dem LLM-Call -
    # das LLM entscheidet `richtung` in seiner Antwort aber komplett frei (siehe
    # hebel_analyst.py-Schema), nichts prüft danach nochmal gegen
    # hebel_richtung_modus. post_check_hebel() bekommt den aktuellen Wert daher
    # hier durchgereicht, siehe dessen Docstring fuer die genaue Veto-Bedingung.
    # Aus config.yaml (nicht mehr data/settings.json, siehe Regelwerksmanual-
    # Nachtrag "Nur-Long-Deckel", Migrations-Zusatz) - config_dict oben bereits
    # geladen (Zeile ~144).
    hebel_richtung_modus = config_dict.get("budget_allocator", {}).get("hebel_richtung_modus", "beide")
    corrected = post_check_hebel(
        parsed, pre_result, regime_result, config_dict, confluence=confluence,
        hebel_richtung_modus=hebel_richtung_modus,
        retail_long_bias_extreme=anticyclic_context.retail_long_bias_extreme,
        long_account_pct=anticyclic_context.long_account_pct,
        historische_erfolgsquote=historische_erfolgsquote,
        funding_rate_stunde=anticyclic_context.funding_rate_current,
        asset_rolle=asset.rolle,
        liquiditaetszonen=liquiditaetszonen,
        signal_stabilitaet=signal_stabilitaet,
        atr_perzentil=atr_perzentil,
        eur_usd_fx_rate=eur_usd_fx_rate,
        position_aktuell=position_aktuell,
        kontrathese_verlauf=kontrathese_verlauf,
        now_unix=now_unix,
        richtungswende=richtungswende,
        regime_persistenz_tage=regime_persistenz_tage_wert,
        btc_relativwert=btc_relativwert,
        current_price=current_price_usd,
        atr_value=atr_value,
        dates=dates,
        closes=closes,
    )
    risk_veto = corrected.pop("_risk_veto")
    risk_veto_reason = corrected.pop("_risk_veto_reason")
    risikofaktoren = corrected.pop("_risikofaktoren", None)
    fazit_konsistenz_hinweis = corrected.pop("_fazit_konsistenz_hinweis", None)
    eigene_einschaetzung = corrected.get("eigene_einschaetzung") or {}

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

    log_eur_abweichungen(asset.symbol, {
        "entry_von": (entry.get("eur_von"), eur_aus_usd(entry.get("usd_von"), eur_usd_fx_rate)),
        "entry_bis": (entry.get("eur_bis"), eur_aus_usd(entry.get("usd_bis"), eur_usd_fx_rate)),
        "stop_loss_von": (stop_loss.get("eur_von"), eur_aus_usd(stop_loss.get("usd_von"), eur_usd_fx_rate)),
        "stop_loss_bis": (stop_loss.get("eur_bis"), eur_aus_usd(stop_loss.get("usd_bis"), eur_usd_fx_rate)),
        "take_profit_von": (take_profit.get("eur_von"), eur_aus_usd(take_profit.get("usd_von"), eur_usd_fx_rate)),
        "take_profit_bis": (take_profit.get("eur_bis"), eur_aus_usd(take_profit.get("usd_bis"), eur_usd_fx_rate)),
        "halte_kriterium_ziel_preis": (
            halte_kriterium.get("ziel_preis_eur"), eur_aus_usd(halte_kriterium.get("ziel_preis_usd"), eur_usd_fx_rate),
        ),
    })

    # Mindestziel-Kurs/Zeitschaetzung (2026-07-27) - siehe pipeline.py fuer die
    # Spot-Variante/Begruendung. Richtungsabhaengig: SHORT spiegelt die Distanz
    # unter den Entry statt darueber.
    _ist_short_neu = corrected["richtung"] == "SHORT"
    _entry_mid_neu = None
    if entry.get("usd_von") is not None and entry.get("usd_bis") is not None:
        _entry_mid_neu = (entry["usd_von"] + entry["usd_bis"]) / 2
    elif entry.get("usd_von") is not None:
        _entry_mid_neu = entry["usd_von"]
    _stop_loss_mid_neu = None
    if stop_loss.get("usd_von") is not None and stop_loss.get("usd_bis") is not None:
        _stop_loss_mid_neu = (stop_loss["usd_von"] + stop_loss["usd_bis"]) / 2
    elif stop_loss.get("usd_von") is not None:
        _stop_loss_mid_neu = stop_loss["usd_von"]
    _risiko_distanz_neu = None
    if _entry_mid_neu is not None and _stop_loss_mid_neu is not None:
        _risiko_distanz_neu = (
            (_stop_loss_mid_neu - _entry_mid_neu) if _ist_short_neu else (_entry_mid_neu - _stop_loss_mid_neu)
        )
    _richtungstreffer_mindest_crv_cfg = config_dict.get("backward_tracking", {}).get(
        "richtungstreffer_mindest_crv", DEFAULT_RICHTUNGSTREFFER_MINDEST_CRV,
    )
    mindestziel_usd_wert = mindestziel_preis(
        _entry_mid_neu, _risiko_distanz_neu, _richtungstreffer_mindest_crv_cfg, _ist_short_neu,
    )
    mindestziel_zeitraum_tage_wert = schaetze_mindestziel_zeitraum_tage(
        mindestziel_usd_wert, _entry_mid_neu, ohlc_history,
    )

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
        entry_eur_von=eur_aus_usd(entry.get("usd_von"), eur_usd_fx_rate),
        entry_eur_bis=eur_aus_usd(entry.get("usd_bis"), eur_usd_fx_rate),
        stop_loss_usd_von=stop_loss.get("usd_von"),
        stop_loss_usd_bis=stop_loss.get("usd_bis"),
        stop_loss_eur_von=eur_aus_usd(stop_loss.get("usd_von"), eur_usd_fx_rate),
        stop_loss_eur_bis=eur_aus_usd(stop_loss.get("usd_bis"), eur_usd_fx_rate),
        take_profit_usd_von=take_profit.get("usd_von"),
        take_profit_usd_bis=take_profit.get("usd_bis"),
        take_profit_eur_von=eur_aus_usd(take_profit.get("usd_von"), eur_usd_fx_rate),
        take_profit_eur_bis=eur_aus_usd(take_profit.get("usd_bis"), eur_usd_fx_rate),
        mindestziel_usd=mindestziel_usd_wert,
        mindestziel_eur=eur_aus_usd(mindestziel_usd_wert, eur_usd_fx_rate),
        mindestziel_zeitraum_tage_geschaetzt=mindestziel_zeitraum_tage_wert,
        halte_kriterium_bucket=halte_kriterium.get("bucket"),
        halte_kriterium_ziel_preis_usd=halte_kriterium.get("ziel_preis_usd"),
        halte_kriterium_ziel_preis_eur=eur_aus_usd(halte_kriterium.get("ziel_preis_usd"), eur_usd_fx_rate),
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
        liquidationspreis_geschaetzt_eur=corrected.get("liquidationspreis_geschätzt_eur"),
        eigenkapitalbedarf_eur=corrected.get("eigenkapitalbedarf_eur"),
        hebel_senkung_eigenkapital_nachschuss_eur=senkung_nachschuss_eur,
        ausfuehrbarkeit_hinweis=corrected.get("ausführbarkeit_hinweis"),
        groq_raw_response=raw_response,
        llm_model=llm_model,
        risikofaktoren_json=json.dumps(risikofaktoren, ensure_ascii=False) if risikofaktoren else None,
        kontrathese_zu_position=corrected.get("kontrathese_zu_position", False),
        kontrathese_llm_richtung=corrected.get("kontrathese_llm_richtung"),
        fazit_folgen=eigene_einschaetzung.get("folgen"),
        fazit_kurzfazit=eigene_einschaetzung.get("kurzfazit"),
        fazit_konsistenz_hinweis=fazit_konsistenz_hinweis,
        **top_grund_fields,
    )
    new_id = db.insert_hebel_signal(conn, signal)
    signal.id = new_id
    db.update_hebel_trigger_status(conn, trigger.id, "llm_generiert")

    # Z.ai-Gegenpruefung (2026-07-26, siehe agent/krypto/gegenpruefung.py) -
    # laeuft in einem eigenen Hintergrund-Thread (siehe
    # gegenpruefung.fuehre_beide_calls_im_hintergrund()-Docstring fuer die
    # Begruendung, warum ein einfacher Aufruf NACH dem Insert - aber noch
    # innerhalb dieser Funktion - die on_signal_ready-E-Mail-Latenz NICHT
    # geloest haette).
    # Rein beobachtend: das zurueckgegebene `signal`-Objekt traegt die neuen
    # Felder bewusst noch nicht (der Thread laeuft ja gerade erst los) - der
    # spaetere DB-Update ist die alleinige Quelle, GUI/Notebook-Export lesen
    # ohnehin aus der DB, nicht aus diesem Rueckgabewert. `signal.id` (oben
    # gesetzt) ermoeglicht genau das: scheduler/background.py::
    # _sende_hebel_email_mit_zai_wartezeit() nutzt es, um vor dem E-Mail-
    # Versand per db.get_hebel_signal_by_id() begrenzt auf dieses Ergebnis
    # zu warten (Nachtrag 2026-07-26, spaeter am Tag - echter Fund: die
    # Notification-E-Mail zeigte nie Z.ai-Zeilen, weil sie sich bisher IMMER
    # auf dieses noch-nicht-angereicherte Rueckgabeobjekt stuetzte).
    if zai_client is not None:
        ema_ordnung_item = next(
            (item for item in confluence.items if item.indicator == "EMA-Ordnung"), None,
        )
        trend_label = ema_ordnung_item.detail if ema_ordnung_item else None
        rsi_wert = latest_value(snapshot.rsi)
        zai_fakten = baue_zai_fakten(
            symbol=asset.symbol,
            richtung=corrected.get("richtung"),
            action=corrected.get("action"),
            confidence_pct=corrected.get("confidence_pct"),
            rsi=rsi_wert,
            trend_label=trend_label,
            regime=regime_result.regime,
            funding_rate_stunde=anticyclic_context.funding_rate_current,
            confluence_bullish=confluence.bullish_count,
            confluence_bearish=confluence.bearish_count,
            confluence_neutral=confluence.neutral_count,
            optionsmarkt_skew=(optionsmarkt or {}).get("skew_prozentpunkte"),
        )
        # Unabhaengiger Richtungs-Abgleich (2026-07-26, gleicher Tag) - siehe
        # agent/krypto/gegenpruefung.py Modul-Docstring Punkt 2: BEWUSST eine
        # eigene, engere Faktenmenge OHNE richtung/action/confidence_pct
        # (Echo-/Anker-Vermeidung), nicht dieselbe `zai_fakten` von oben.
        zai_objektive_fakten = baue_zai_objektive_fakten(
            symbol=asset.symbol,
            rsi=rsi_wert,
            trend_label=trend_label,
            regime=regime_result.regime,
            funding_rate_stunde=anticyclic_context.funding_rate_current,
            confluence_bullish=confluence.bullish_count,
            confluence_bearish=confluence.bearish_count,
            confluence_neutral=confluence.neutral_count,
            optionsmarkt_skew=(optionsmarkt or {}).get("skew_prozentpunkte"),
        )
        threading.Thread(
            target=fuehre_beide_calls_im_hintergrund,
            args=(
                new_id, zai_fakten, corrected.get("short_reasoning"),
                zai_objektive_fakten, corrected.get("richtung"), zai_client,
                db.update_hebel_signal_zai_gegenpruefung,
            ),
            daemon=True,
        ).start()

    return signal
