"""R-5.5 Risikopruefung (VETO-Stufe, Spezifikation Kap. 3) + R-5.10 Regime-Profil
anwenden. Zwei Funktionen, bewusst redundant zueinander (Guertel + Hosentraeger):
`pre_check()` laeuft VOR dem Groq-Call und berechnet eine harte Obergrenze, die als
Fakt mitgeschickt wird; `post_check()` laeuft NACH dem Groq-Call und erzwingt
dieselben Regeln nochmal, unabhaengig davon ob Groq sie im Prompt befolgt hat oder
nicht - das Modell wird nie blind vertraut (P-10 auf die LLM-Schicht angewendet).

Abdeckung: RM-1 (Risiko/Trade), RM-2 (max. Allokation/Asset), RM-4 (Cash-Reserve),
RM-5 (Stop-Loss-Pflicht), R-5.10 (Small-Cap-Budget aus dem Regime-Profil). NICHT
abgedeckt (bewusste Luecke, siehe Spezifikation Kap. 16): RM-7/Z-3 Drawdown-
Notbremse (braucht eine Portfolio-Wert-Historie, die noch nicht existiert), RM-8/-9
(voller Risiko-Score), RM-10/-11 (Hebel - S-6 ist ohnehin `aktiv: false`).
"""
from __future__ import annotations

from dataclasses import dataclass, field

import database.db as db
from indicators.calculations import TechnicalSnapshot, latest_value

STOP_LOSS_ATR_MULTIPLE = 2.0  # Arbeits-Konvention, nicht spezifikationsseitig vorgegeben
CRV_MINIMUM = 2.0  # Z-2


@dataclass
class RiskPreCheckResult:
    kauf_erlaubt: bool
    veto_reason: str | None
    max_position_size_usd: float | None
    max_position_size_eur: float | None
    stop_loss_distance_pct: float | None
    cash_reserve_pct_current: float
    allocation_pct_current: float
    small_cap_budget_pct_applicable: float | None
    checks: list[str] = field(default_factory=list)
    drawdown_check_status: str = "nicht implementiert"


def _portfolio_values_usd(watchlist, holdings, latest_prices) -> tuple[float, dict[str, float]]:
    """Gesamtwert + Wert je Symbol in USD, nur fuer Symbole mit bekanntem Preis
    (P-10: fehlender Preis wird NICHT als 0 angenommen und stillschweigend
    ausgelassen - er wird einfach nicht mitgezaehlt, das ist hier akzeptabel, da es
    nur eine Obergrenzen-Berechnung ist, keine Anzeige eines vermeintlich vollstaendigen
    Portfoliowerts)."""
    values: dict[str, float] = {}
    for holding in holdings:
        snap = latest_prices.get(holding.symbol)
        if snap is None or snap.price_usd is None:
            continue
        values[holding.symbol] = holding.quantity * snap.price_usd
    return sum(values.values()), values


def small_cap_budget_headroom(watchlist, holdings, latest_prices, regime_result, config) -> float:
    """Verfuegbares Tier-3-Small-Cap-Budget in Prozentpunkten (Regime-Limit minus
    aktuelle Small-Cap-Allokation), unabhaengig von einem konkreten zu bewertenden
    Asset. Kann negativ sein (Budget bereits ueberschritten). Extrahiert aus
    `pre_check()` fuer Wiederverwendung durch agent/marktscan.py (Stufe D,
    Nutzungs-Diskussion Marktscan 2026-07-09) - reiner Refactor, keine
    Verhaltensaenderung an `pre_check()` selbst (aequivalente Bedingung, siehe dort)."""
    total_value_usd, values_by_symbol = _portfolio_values_usd(watchlist, holdings, latest_prices)
    tier2_threshold = config["marktscan"]["tiers"]["tier2_min_marktkap_usd"]
    profile = config["regime"]["profile"].get(regime_result.regime, {})
    budget_pct = profile.get(
        "small_cap_budget_prozent", config["risiko"]["max_allokation_small_cap_prozent"]
    )
    small_cap_value = sum(
        v
        for sym, v in values_by_symbol.items()
        if (a := next((w for w in watchlist if w.symbol == sym), None))
        and a.typ == "taktisch"
        and (p := latest_prices.get(sym))
        and p.market_cap_usd is not None
        and p.market_cap_usd < tier2_threshold
    )
    current_pct = (small_cap_value / total_value_usd * 100) if total_value_usd > 0 else 0.0
    return budget_pct - current_pct


def pre_check(
    asset,
    watchlist,
    conn,
    latest_prices: dict,
    technical_snapshot: TechnicalSnapshot,
    regime_result,
    config: dict,
) -> RiskPreCheckResult:
    checks: list[str] = []
    veto_reasons: list[str] = []

    holdings = db.get_all_holdings(conn)
    total_value_usd, values_by_symbol = _portfolio_values_usd(watchlist, holdings, latest_prices)
    asset_value_usd = values_by_symbol.get(asset.symbol, 0.0)
    allocation_pct_current = (asset_value_usd / total_value_usd * 100) if total_value_usd > 0 else 0.0

    stablecoin_symbols = {a.symbol for a in watchlist if a.typ == "stablecoin"}
    cash_value_usd = sum(v for sym, v in values_by_symbol.items() if sym in stablecoin_symbols)
    cash_reserve_pct_current = (cash_value_usd / total_value_usd * 100) if total_value_usd > 0 else 0.0

    risiko_cfg = config["risiko"]

    # RM-5: Stop-Loss-Pflicht - ohne ATR keine verlaessliche Stop-Distanz ableitbar.
    stop_loss_distance_pct = None
    current_price = latest_prices.get(asset.symbol)
    current_price_usd = current_price.price_usd if current_price else None
    atr_value = latest_value(technical_snapshot.atr)
    if not technical_snapshot.atr.available or atr_value is None or not current_price_usd:
        veto_reasons.append("kein Stop-Loss ableitbar (Volatilitätsdaten unzureichend, RM-5)")
        checks.append("RM-5: FEHLGESCHLAGEN - ATR/Preis nicht verfügbar")
    else:
        stop_loss_distance_pct = (STOP_LOSS_ATR_MULTIPLE * atr_value) / current_price_usd * 100
        checks.append(f"RM-5: OK - Stop-Loss-Abstand {stop_loss_distance_pct:.2f}% (2x ATR)")

    # RM-1: Risiko pro Trade begrenzt die Positionsgroesse.
    max_position_size_usd = None
    if stop_loss_distance_pct and stop_loss_distance_pct > 0 and total_value_usd > 0:
        risk_budget_usd = total_value_usd * risiko_cfg["risiko_pro_trade_prozent"] / 100
        max_position_size_usd = risk_budget_usd / (stop_loss_distance_pct / 100)
        checks.append(f"RM-1: max. Positionsgröße aus Risiko/Trade = {max_position_size_usd:.2f} USD")
    else:
        checks.append("RM-1: nicht berechenbar (Portfolio-Wert oder Stop-Loss-Abstand unbekannt)")

    # RM-4: Cash-Reserve - bei Unterschreitung wird jeder weitere Kauf blockiert
    # (konservativ: die konkrete Kaufgröße ist an dieser Stelle noch unbekannt).
    if cash_reserve_pct_current <= risiko_cfg["cash_reserve_min_prozent"]:
        veto_reasons.append(
            f"Cash-Reserve {cash_reserve_pct_current:.1f}% <= Minimum "
            f"{risiko_cfg['cash_reserve_min_prozent']}% (RM-4)"
        )
        checks.append("RM-4: FEHLGESCHLAGEN - Cash-Reserve unter Minimum")
    else:
        checks.append(f"RM-4: OK - Cash-Reserve {cash_reserve_pct_current:.1f}%")

    # RM-2: max. Allokation je Einzelwert. Core-Assets (BTC/ETH) haben eine eigene,
    # hoehere Grenze (2026-07-07 eingefuehrt, vorlaeufig - Thema "BTC hat den Lead"
    # noch explizit zu besprechen, siehe Memory project_offene_agent_diskussionspunkte).
    max_allok_pct = (
        risiko_cfg["max_allokation_pro_core_asset_prozent"]
        if asset.typ == "core"
        else risiko_cfg["max_allokation_pro_asset_prozent"]
    )
    if allocation_pct_current >= max_allok_pct:
        veto_reasons.append(
            f"Allokation {allocation_pct_current:.1f}% bereits >= Limit {max_allok_pct}% (RM-2)"
        )
        checks.append("RM-2: FEHLGESCHLAGEN - Asset-Allokation am/über Limit")
    else:
        checks.append(f"RM-2: OK - Allokation {allocation_pct_current:.1f}% von {max_allok_pct}%")
        if max_position_size_usd is not None and total_value_usd > 0:
            remaining_usd = total_value_usd * (max_allok_pct - allocation_pct_current) / 100
            max_position_size_usd = min(max_position_size_usd, remaining_usd)

    # R-5.10: Small-Cap-Budget aus dem aktiven Regime-Profil (nicht dem statischen
    # config-Wert) - das ist der Kern von R-5.10. Headroom-Berechnung ausgelagert
    # (small_cap_budget_headroom() oben), von agent/marktscan.py wiederverwendet.
    small_cap_budget_pct_applicable = None
    tier2_threshold = config["marktscan"]["tiers"]["tier2_min_marktkap_usd"]
    is_small_cap = (
        asset.typ == "taktisch"
        and current_price is not None
        and current_price.market_cap_usd is not None
        and current_price.market_cap_usd < tier2_threshold
    )
    if is_small_cap:
        profile = config["regime"]["profile"].get(regime_result.regime, {})
        small_cap_budget_pct_applicable = profile.get(
            "small_cap_budget_prozent", risiko_cfg["max_allokation_small_cap_prozent"]
        )
        headroom_pct = small_cap_budget_headroom(watchlist, holdings, latest_prices, regime_result, config)
        if headroom_pct <= 0:
            veto_reasons.append(
                f"Small-Cap-Budget bereits ausgeschöpft (Headroom {headroom_pct:.1f} Prozentpunkte, "
                f"Regime-Limit {small_cap_budget_pct_applicable}% - {regime_result.regime}, R-5.10)"
            )
            checks.append("R-5.10: FEHLGESCHLAGEN - Small-Cap-Budget am/über Regime-Limit")
        else:
            checks.append(
                f"R-5.10: OK - Small-Cap-Budget-Headroom {headroom_pct:.1f} Prozentpunkte "
                f"(Regime-Limit {small_cap_budget_pct_applicable}%, {regime_result.regime})"
            )

    max_position_size_eur = None
    if max_position_size_usd is not None and current_price and current_price.price_usd and current_price.price_eur:
        fx = current_price.price_eur / current_price.price_usd
        max_position_size_eur = max_position_size_usd * fx

    return RiskPreCheckResult(
        kauf_erlaubt=len(veto_reasons) == 0,
        veto_reason="; ".join(veto_reasons) if veto_reasons else None,
        max_position_size_usd=max_position_size_usd,
        max_position_size_eur=max_position_size_eur,
        stop_loss_distance_pct=stop_loss_distance_pct,
        cash_reserve_pct_current=cash_reserve_pct_current,
        allocation_pct_current=allocation_pct_current,
        small_cap_budget_pct_applicable=small_cap_budget_pct_applicable,
        checks=checks,
    )


_BUY_ACTIONS = ("KAUFEN", "NACHKAUFEN")


def post_check(parsed: dict, pre_result: RiskPreCheckResult, regime_result, config: dict) -> dict:
    """Nimmt die bereits validierte (siehe agent/analyst.py) Groq-Antwort und erzwingt
    RM-1/-2/-4/-5, Mindest-Konfidenz (R-5.10) und CRV >= 2.0 (Z-2) noch einmal
    deterministisch. Gibt die (ggf. korrigierte) Antwort + Veto-Metadaten zurueck."""
    result = dict(parsed)
    risk_veto = False
    risk_veto_reason = None

    action = str(result.get("action", "")).upper()

    if action in _BUY_ACTIONS and not pre_result.kauf_erlaubt:
        risk_veto = True
        risk_veto_reason = pre_result.veto_reason
        action = "HALTEN"

    if action in _BUY_ACTIONS:
        min_konfidenz = (
            config["regime"]["profile"].get(regime_result.regime, {}).get("min_konfidenz_prozent")
        )
        confidence = result.get("confidence_pct")
        if min_konfidenz is not None and confidence is not None and confidence < min_konfidenz:
            risk_veto = True
            reason = f"Konfidenz {confidence}% unter Regime-Mindestschwelle {min_konfidenz}% (R-5.10)"
            risk_veto_reason = f"{risk_veto_reason}; {reason}" if risk_veto_reason else reason
            action = "HALTEN"

    if action in _BUY_ACTIONS:
        entry = (result.get("entry") or {}).get("usd")
        stop = (result.get("stop_loss") or {}).get("usd")
        take = (result.get("take_profit") or {}).get("usd")
        if entry and stop and take and entry != stop:
            crv = (take - entry) / (entry - stop) if entry > stop else None
            if crv is None or crv < CRV_MINIMUM:
                risk_veto = True
                reason = f"CRV {crv} unter Minimum {CRV_MINIMUM} (Z-2)"
                risk_veto_reason = f"{risk_veto_reason}; {reason}" if risk_veto_reason else reason
                action = "HALTEN"

    # R-5.9: TAUSCHEN statt VERKAUFEN, wenn ein Swap-Ziel genannt wurde (P-6) -
    # mechanisch durchgesetzt statt nur per Prompt erhofft.
    if action == "VERKAUFEN" and result.get("tauschen_target_symbol"):
        action = "TAUSCHEN"

    result["action"] = action
    result["_risk_veto"] = risk_veto
    result["_risk_veto_reason"] = risk_veto_reason
    return result
