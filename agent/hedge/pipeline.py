"""Signal-Pipeline fuer Portfolio-Hedge-Instrumente (2026-07-18) - siehe
agent/hedge/analyst.py Modul-Docstring fuer die Architektur-Begruendung
(portfolio-exposure-basiert statt einzeltitel-technisch).

Live-Fund waehrend der Rohstoff-Pipeline-Verifikation (siehe agent/rohstoff/
pipeline.py): 3QSS (WisdomTree Nasdaq-100 3x Short, IE00BLRPRJ20.SG) hat wie die
Rohstoff-ETCs KEINE yfinance-.history()-Daten - nur fast_info (aktueller Preis)
funktioniert. DBPK (Xtrackers S&P 500 2x Inverse) hat dagegen funktionierende
Kurshistorie. Statt fuer 3QSS wieder eine Futures-Ersatz-Loesung zu bauen (die
fuer ein GEHEBELTES/INVERSES Produkt zusaetzlich eine korrekte taegliche
Rebalancing-Simulation braeuchte, um nicht selbst wieder falsche technische
Level zu erzeugen), wurde bewusst entschieden, GAR KEINE Einzeltitel-Technik-
analyse fuer Hedge-Instrumente zu betreiben (siehe analyst.py) - konsistent
fuer beide Instrumente, und inhaltlich ohnehin die richtige Bewertungsbasis
fuer ein Absicherungs-Overlay (siehe dortigen Docstring)."""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

import agent.kategorie_thesen as kategorie_thesen
import config
import database.db as db
from agent.hedge.analyst import AnalystResponseInvalid, build_facts, call_llm_for_signal
from agent.krypto.backward_tracking import compute_win_rate_fact
from agent.krypto.llm_provider import llm_model_label
from agent.krypto.makro_analog import get_cached_makro_analog_fact
from agent.krypto.pipeline import compute_current_regime
from agent.krypto.risk_gate import _portfolio_values_usd
from database.models import Signal
from staleness import is_price_stale

logger = logging.getLogger(__name__)

PIPELINE_VERSION = "1"

# Manuell gepflegt (analog SYMBOL_ZU_FUTURES_TICKER in agent/rohstoff/pipeline.py) -
# bei einem neuen Hedge-Instrument hier ergaenzen. hebel_faktor bestimmt, wie viel
# USD "effektive Abdeckung" 1 USD Positionswert liefert (2x/3x taeglich gehebelt).
SYMBOL_ZU_HEBEL_FAKTOR = {
    "DBPK": 2.0,
    "3QSS": 3.0,
}
SYMBOL_ZU_REFERENZ_INDEX = {
    "DBPK": "S&P 500",
    "3QSS": "Nasdaq-100",
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


def _compute_portfolio_exposure(asset, watchlist, conn, latest_prices, config_dict) -> dict:
    """Long-Exposure = Portfolio-Wert OHNE die Hedge-Instrumente selbst und OHNE
    Cash-Aequivalente (Stablecoins) - das ist das Risiko, das potenziell
    abgesichert werden muss. Hedge-Abdeckung = Summe ueber ALLE aktuell
    gehaltenen Hedge-Instrumente, je mit ihrem hebel_faktor multipliziert (1 USD
    in einem 3x-Short-ETF deckt effektiv 3 USD Long-Exposure ab). Das
    verbleibende Budget wird bereits durch DIESES Instruments hebel_faktor
    geteilt - der LLM-Vorschlag (`position_size.usd`) ist der NOTIONAL-Wert
    dieses Instruments, nicht die effektive Abdeckung."""
    holdings = db.get_all_holdings(conn)
    holdings_by_symbol = {h.symbol: h for h in holdings}
    total_value_usd, values_by_symbol = _portfolio_values_usd(watchlist, holdings, latest_prices)

    hedge_symbole = set(SYMBOL_ZU_HEBEL_FAKTOR.keys())
    stablecoin_symbole = {a.symbol for a in watchlist if a.ist_cash_aequivalent}
    long_exposure_usd = sum(
        v for sym, v in values_by_symbol.items()
        if sym not in hedge_symbole and sym not in stablecoin_symbole
    )
    aktuelle_hedge_abdeckung_usd = sum(
        values_by_symbol.get(sym, 0.0) * hebel for sym, hebel in SYMBOL_ZU_HEBEL_FAKTOR.items()
    )

    # Live-Fund (2026-07-18, Verifikation gegen echtes Portfolio): _portfolio_values_usd()
    # laesst ein Symbol OHNE bekannten Preis (P-10) einfach aus values_by_symbol weg -
    # ein anderes, tatsaechlich gehaltenes Hedge-Instrument mit fehlendem price_usd
    # (z.B. wegen einer fehlgeschlagenen EUR/USD-Umrechnung, siehe generate_signal()s
    # eigenem price_usd-Gate) wuerde sonst STILLSCHWEIGEND als "0 USD Abdeckung"
    # gezaehlt - aktuelle_hedge_abdeckung_usd waere dann UNTERSCHAETZT, und ein darauf
    # basierender KAUFEN/NACHKAUFEN-Vorschlag koennte das Portfolio unbemerkt
    # ueberhedgen. Fix: erkennen + explizit warnen, UND das verbleibende Budget auf 0
    # deckeln (VERKAUFEN/HALTEN bleiben davon unberuehrt, nur ein Hedge-AUFBAU wird
    # blockiert, solange die Abdeckungs-Rechnung unsicher ist).
    fehlende_preise = [
        sym for sym in hedge_symbole
        if (holdings_by_symbol.get(sym) and (holdings_by_symbol[sym].quantity or 0.0) > 0.0)
        and sym not in values_by_symbol
    ]

    hedge_cfg = config_dict.get("hedge", {})
    max_abdeckung_anteil = hedge_cfg.get("max_abdeckung_anteil", 1.0)
    max_hedge_abdeckung_usd = long_exposure_usd * max_abdeckung_anteil
    verbleibendes_budget_usd = max(0.0, max_hedge_abdeckung_usd - aktuelle_hedge_abdeckung_usd)

    hebel_faktor = SYMBOL_ZU_HEBEL_FAKTOR[asset.symbol]
    verbleibendes_budget_fuer_instrument_usd = verbleibendes_budget_usd / hebel_faktor
    if fehlende_preise:
        verbleibendes_budget_fuer_instrument_usd = 0.0

    hinweis = (
        "aktuelle_hedge_abdeckung_* summiert ALLE aktuell gehaltenen Hedge-"
        "Instrumente zusammen (leverage-adjustiert), nicht nur dieses eine. "
        "verbleibendes_hedge_budget_usd ist bereits durch den hebel_faktor "
        "DIESES Instruments geteilt - das ist der maximale Notional-Wert, den "
        "eine KAUFEN/NACHKAUFEN-Empfehlung fuer DIESES Instrument haben darf, "
        "ohne ziel_hedge_abdeckung_max_prozent zu ueberschreiten."
    )
    if fehlende_preise:
        hinweis += (
            f" WARNUNG: fuer {', '.join(fehlende_preise)} (ebenfalls gehalten) fehlt "
            "aktuell ein Preis - aktuelle_hedge_abdeckung_usd ist dadurch "
            "UNTERSCHAETZT. verbleibendes_hedge_budget_usd wurde deshalb "
            "vorsorglich auf 0 gesetzt (empfiehl KEIN KAUFEN/NACHKAUFEN, bis die "
            "Abdeckung wieder vollstaendig berechenbar ist - VERKAUFEN/HALTEN "
            "bleiben moeglich)."
        )

    return {
        "ungesichertes_long_exposure_usd": round(long_exposure_usd, 2),
        "aktuelle_hedge_abdeckung_usd": round(aktuelle_hedge_abdeckung_usd, 2),
        "aktuelle_hedge_abdeckung_prozent": (
            round(aktuelle_hedge_abdeckung_usd / long_exposure_usd * 100, 1) if long_exposure_usd > 0 else 0.0
        ),
        "ziel_hedge_abdeckung_max_prozent": max_abdeckung_anteil * 100,
        "verbleibendes_hedge_budget_usd": round(verbleibendes_budget_fuer_instrument_usd, 2),
        "berechnung_unsicher_fehlende_preise": fehlende_preise or None,
        "hinweis": hinweis,
    }, verbleibendes_budget_fuer_instrument_usd


def _post_check_hedge(
    parsed: dict, verbleibendes_budget_usd: float, eur_usd_fx_rate: float | None, config_dict: dict,
) -> dict:
    """Deterministischer Deckel (P-10, mirror risk_gate.py::post_check()s RM-1/2-
    Klemm-Logik, aber eigenstaendig - siehe analyst.py Modul-Docstring, warum
    risk_gate.post_check() hier NICHT wiederverwendet wird): kuerzt eine zu
    grosse KAUFEN/NACHKAUFEN-Positionsgroesse auf das verbleibende Hedge-Budget,
    statt die Empfehlung selbst zu verwerfen.

    PLUS Bull-Wahrscheinlichkeits-Deckel (2026-07-18, Multi-Asset-Vollstaendig-
    keitspruefung): das Hedge-Pendant zum Gegenszenario-Deckel aus
    risk_gate.py::post_check(), aber bewusst NICHT 1:1 uebernommen, sondern
    SPIEGELVERKEHRT. Bei einer normalen Directional-Long-Position (Spot/Aktien/
    Rohstoffe) ist eine hohe forecast.bear.probability_pct das Risiko-Szenario
    ("die Position koennte gegen mich laufen") - der bestehende Deckel kappt
    dort folgerichtig die Positionsgroesse. Fuer ein inverses Hedge-Instrument
    (DBPK/3QSS) ist das Verhaeltnis GENAU UMGEKEHRT: die Position GEWINNT bei
    fallenden Kursen, ihr Risiko-Szenario ist eine hohe forecast.bull.
    probability_pct - dann decayt eine grosse, taeglich neu gehebelte Position
    ohne Absicherungsnutzen zu liefern (Volatility-Decay, siehe SYSTEM_PROMPT
    Regel 4). Ein naiv wiederverwendeter Bear-Deckel waere hier funktional
    falschherum gewesen (haette die Positionsgroesse ausgerechnet dann NICHT
    gekappt, wenn der Decay-Effekt am staerksten drueckt)."""
    result = dict(parsed)
    action = result.get("action")
    if action in ("KAUFEN", "NACHKAUFEN"):
        position_size = result.get("position_size") or {}
        proposed_usd = position_size.get("usd")
        if proposed_usd is not None and proposed_usd > verbleibendes_budget_usd:
            proposed_eur = position_size.get("eur")
            fx = (proposed_usd / proposed_eur) if proposed_eur else eur_usd_fx_rate
            note = (
                f"Von {proposed_usd:.2f} USD auf verbleibendes Hedge-Budget "
                f"{verbleibendes_budget_usd:.2f} USD gekuerzt (deterministisch erzwungen, "
                "Gesamt-Hedge-Abdeckung darf das konfigurierte Maximum nicht ueberschreiten)."
            )
            position_size["usd"] = verbleibendes_budget_usd
            position_size["eur"] = verbleibendes_budget_usd / fx if fx else None
            existing_note = position_size.get("note")
            position_size["note"] = f"{existing_note} {note}" if existing_note else note
            result["position_size"] = position_size

        hedge_cfg = config_dict.get("hedge", {})
        bull_pct = ((result.get("forecast") or {}).get("bull") or {}).get("probability_pct")
        schwelle = hedge_cfg.get("bull_wahrscheinlichkeit_schwelle_prozent")
        deckel_anteil = hedge_cfg.get("bull_wahrscheinlichkeit_deckel_anteil")
        if (
            bull_pct is not None and schwelle is not None and deckel_anteil is not None
            and bull_pct >= schwelle
        ):
            position_size = result.get("position_size") or {}
            proposed_usd = position_size.get("usd")
            if proposed_usd is not None:
                gedeckelt_usd = proposed_usd * deckel_anteil
                if gedeckelt_usd < proposed_usd:
                    proposed_eur = position_size.get("eur")
                    fx = (proposed_usd / proposed_eur) if proposed_eur else eur_usd_fx_rate
                    note = (
                        f"Zusaetzlich auf {deckel_anteil * 100:.0f}% reduziert (Bull-Wahrscheinlichkeit "
                        f"{bull_pct:.0f}% >= Schwelle {schwelle:.0f}% - Decay-Risiko bei anhaltendem "
                        "Aufwaertstrend, Bull-Wahrscheinlichkeits-Deckel)."
                    )
                    position_size["usd"] = gedeckelt_usd
                    position_size["eur"] = gedeckelt_usd / fx if fx else None
                    existing_note = position_size.get("note")
                    position_size["note"] = f"{existing_note} {note}" if existing_note else note
                    result["position_size"] = position_size
    return result


def generate_signal(asset, watchlist, conn, llm_client, coingecko_client) -> Signal:
    """`asset.symbol` muss in SYMBOL_ZU_HEBEL_FAKTOR stehen. `watchlist` muss die
    VOLLSTAENDIGE Watchlist sein (fuer compute_current_regime() UND fuer die
    Portfolio-Exposure-Berechnung ueber alle Assetklassen hinweg - anders als
    bei Aktien/Rohstoff wird hier bewusst NICHT auf eine Assetklassen-Teilmenge
    gefiltert, das Hedge-Instrument sichert das GESAMTE Portfolio ab)."""
    if asset.symbol not in SYMBOL_ZU_HEBEL_FAKTOR:
        raise ValueError(f"generate_signal() (agent/hedge) erwartet ein bekanntes Hedge-Symbol, bekam {asset.symbol!r}")

    latest_prices = db.get_latest_prices(conn)
    price_snap = latest_prices.get(asset.symbol)

    if price_snap is None or is_price_stale(price_snap.fetched_at):
        signal = _fixed_signal(asset.symbol, "HALTEN", gate_passed=False, gate_reason="Preis veraltet oder nicht vorhanden")
        db.insert_signal(conn, signal)
        return signal
    if price_snap.price_usd is None:
        signal = _fixed_signal(
            asset.symbol, "HALTEN", gate_passed=False,
            gate_reason="USD-Preis nicht verfuegbar (EUR/USD-Kurs fehlte beim letzten Preisabruf)",
        )
        db.insert_signal(conn, signal)
        return signal

    config_dict = config.load_config()
    regime_result = compute_current_regime(conn, coingecko_client, watchlist, None, config_dict)

    portfolio_exposure, verbleibendes_budget_usd = _compute_portfolio_exposure(
        asset, watchlist, conn, latest_prices, config_dict
    )

    eurcv_snap = latest_prices.get("EURCV")
    eur_usd_fx_rate = (
        eurcv_snap.price_usd / eurcv_snap.price_eur
        if eurcv_snap and eurcv_snap.price_usd and eurcv_snap.price_eur
        else None
    )

    holdings = {h.symbol: h for h in db.get_all_holdings(conn)}
    price_age_minutes = None
    fetched = datetime.fromisoformat(price_snap.fetched_at)
    if fetched.tzinfo is None:
        fetched = fetched.replace(tzinfo=timezone.utc)
    price_age_minutes = (datetime.now(timezone.utc) - fetched).total_seconds() / 60

    historischer_makro_vergleich = get_cached_makro_analog_fact(conn)
    letztes_signal = db.get_latest_signal(conn, asset.symbol)
    # Eigener Pool (2026-07-18, Multi-Asset-Vollstaendigkeitspruefung): Hedge-
    # Signale sind qualitativ anders (Absicherung statt Gewinnerwartung) als
    # Krypto/Aktien - eine geliehene fremde Trefferquote waere irrefuehrend.
    _hedge_symbole = set(SYMBOL_ZU_HEBEL_FAKTOR.keys())
    historische_erfolgsquote = compute_win_rate_fact(conn, "spot", erlaubte_symbole=_hedge_symbole)
    these_abgleich = kategorie_thesen.build_these_abgleich_fact(conn, asset)

    facts = build_facts(
        asset, price_snap, holdings.get(asset.symbol), SYMBOL_ZU_HEBEL_FAKTOR[asset.symbol],
        SYMBOL_ZU_REFERENZ_INDEX[asset.symbol], portfolio_exposure, regime_result, price_age_minutes,
        historischer_makro_vergleich=historischer_makro_vergleich,
        historische_erfolgsquote=historische_erfolgsquote,
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
    corrected = _post_check_hedge(parsed, verbleibendes_budget_usd, eur_usd_fx_rate, config_dict)

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
        risk_veto=False,
        risk_veto_reason=None,
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
