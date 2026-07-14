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
(voller Risiko-Score).

RM-10/-11 (Hebel) sind NICHT hier abgedeckt, aber NICHT mehr wegen `aktiv: false` -
`config.yaml risiko.hebel.erlaubt` ist seit 2026-07-14 `true`. Eigenes Modul
`agent/krypto/hebel_risk_gate.py` (andere Schwellenwerte/Zeitkomponente als Spot,
siehe docs/hebel_positionsformel.md), `CRV_MINIMUM` von dort importiert statt
dupliziert.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import database.db as db
from indicators.calculations import TechnicalSnapshot, latest_value

STOP_LOSS_ATR_MULTIPLE = 2.0  # Arbeits-Konvention, nicht spezifikationsseitig vorgegeben
CRV_MINIMUM = 2.0  # Z-2

# Symbole, deren gestakter Anteil NICHT in die Risikoberechnung einfliesst
# (konservativ, Z-1): Un-/Restaking dort bisher nicht instant moeglich.
# Stand 2026-07-11 (Nutzer-Erfahrung): nur ETH betroffen, alle anderen
# bisher gestakten Bitpanda-Assets waren instant handelbar - bei neuen
# gestakten Assets pruefen, ob diese Liste erweitert werden muss.
STAKING_ILLIQUID_SYMBOLS = {"ETH"}


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
    # Cash-Reserve-Ziel (AZ-4 Baustein 3, 2026-07-12) - exponieren bereits intern
    # berechnete Zwischenwerte zusaetzlich, statt sie erneut zu berechnen (gleiches
    # Prinzip wie BtcLogRegressionRisk.residual_std in Baustein 2). rm1_risk_ceiling_usd
    # ist der Wert VOR dem min() mit RM-2 (siehe max_position_size_usd), rm2_allocation_
    # headroom_usd das verbleibende Allokations-Budget in USD (RM-2), rm4_required_
    # reserve_usd das bereits berechnete RM-4-Minimum (max aus Prozentsatz/Festbetrag).
    rm1_risk_ceiling_usd: float | None = None
    rm2_allocation_headroom_usd: float | None = None
    rm4_required_reserve_usd: float | None = None


def _portfolio_values_usd(watchlist, holdings, latest_prices) -> tuple[float, dict[str, float]]:
    """Gesamtwert + Wert je Symbol in USD, nur fuer Symbole mit bekanntem Preis
    (P-10: fehlender Preis wird NICHT als 0 angenommen und stillschweigend
    ausgelassen - er wird einfach nicht mitgezaehlt, das ist hier akzeptabel, da es
    nur eine Obergrenzen-Berechnung ist, keine Anzeige eines vermeintlich vollstaendigen
    Portfoliowerts). Gestakte Mengen (holding.staked_quantity, additiv zu quantity)
    zaehlen mit, ausser fuer STAKING_ILLIQUID_SYMBOLS (konservativ, Z-1) - dadurch
    zaehlt ein gestakter Stablecoin-Bestand automatisch auch als Cash (siehe
    stablecoin-Filter in pre_check()), ohne eigenen Sonderfall hier."""
    values: dict[str, float] = {}
    for holding in holdings:
        snap = latest_prices.get(holding.symbol)
        if snap is None or snap.price_usd is None:
            continue
        quantity = holding.quantity
        if holding.staked_quantity and holding.symbol not in STAKING_ILLIQUID_SYMBOLS:
            quantity += holding.staked_quantity
        values[holding.symbol] = quantity * snap.price_usd
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
    bitpanda_gelistet: bool | None,
) -> RiskPreCheckResult:
    checks: list[str] = []
    veto_reasons: list[str] = []

    holdings = db.get_all_holdings(conn)
    total_value_usd, values_by_symbol = _portfolio_values_usd(watchlist, holdings, latest_prices)
    asset_value_usd = values_by_symbol.get(asset.symbol, 0.0)

    # Transparenz (Z-4): ausgeschlossene Staking-Mengen sichtbar machen statt
    # sie stillschweigend aus der Risikoberechnung zu lassen.
    for holding in holdings:
        if holding.symbol in STAKING_ILLIQUID_SYMBOLS and holding.staked_quantity:
            checks.append(
                f"Hinweis: {holding.staked_quantity:g} {holding.symbol} gestakt, "
                "nicht in Risikoberechnung einbezogen (Illiquiditäts-Vorsicht)"
            )

    stablecoin_symbols = {a.symbol for a in watchlist if a.typ == "stablecoin"}
    cash_value_usd = sum(v for sym, v in values_by_symbol.items() if sym in stablecoin_symbols)

    # RM-4-Erweiterung (2026-07-10): echtes Fiat-Guthaben (z.B. auf Bitpanda), das die
    # App sonst nirgends kennt - manuell gepflegt (ui/portfolio.py), da kein Boersen-
    # API-Zugriff besteht (P-7). EUR->USD ueber EURCV's eigenes Preis-Snapshot
    # abgeleitet (1 EURCV ~= 1 EUR, siehe A-5) - kein zusaetzlicher Wechselkurs-Call
    # noetig. Fehlt das Snapshot (P-10), wird das Fiat-Guthaben NICHT mitgezaehlt statt
    # falsch geraten (1:1-USD-Annahme waere bei EUR/USD != 1 schlicht falsch).
    eurcv_snap = latest_prices.get("EURCV")
    eur_usd_fx_rate = (
        eurcv_snap.price_usd / eurcv_snap.price_eur
        if eurcv_snap and eurcv_snap.price_usd and eurcv_snap.price_eur
        else None
    )

    fiat_cash_eur = db.get_cash_reserve_fiat_eur(conn)
    fiat_cash_usd = 0.0
    if fiat_cash_eur > 0:
        if eur_usd_fx_rate is not None:
            fiat_cash_usd = fiat_cash_eur * eur_usd_fx_rate
            checks.append(f"RM-4: Fiat-Guthaben {fiat_cash_eur:.2f} EUR = {fiat_cash_usd:.2f} USD beruecksichtigt")
        else:
            checks.append("RM-4: Fiat-Guthaben gesetzt, aber EUR/USD-Kurs (EURCV) nicht verfuegbar - nicht mitgezaehlt")

    cash_value_usd += fiat_cash_usd
    total_value_usd += fiat_cash_usd
    cash_reserve_pct_current = (cash_value_usd / total_value_usd * 100) if total_value_usd > 0 else 0.0
    # RM-2 (allocation_pct_current) bewusst NACH der Fiat-Ergaenzung berechnet, damit
    # RM-1/RM-2/RM-4 durchgaengig dieselbe (fiat-inklusive) Portfolio-Gesamtbasis nutzen.
    allocation_pct_current = (asset_value_usd / total_value_usd * 100) if total_value_usd > 0 else 0.0

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
    rm1_risk_ceiling_usd = None
    if stop_loss_distance_pct and stop_loss_distance_pct > 0 and total_value_usd > 0:
        risk_budget_usd = total_value_usd * risiko_cfg["risiko_pro_trade_prozent"] / 100
        max_position_size_usd = risk_budget_usd / (stop_loss_distance_pct / 100)
        rm1_risk_ceiling_usd = max_position_size_usd  # Cash-Reserve-Ziel (Baustein 3): Wert VOR RM-2-Deckelung
        checks.append(f"RM-1: max. Positionsgröße aus Risiko/Trade = {max_position_size_usd:.2f} USD")
    else:
        checks.append("RM-1: nicht berechenbar (Portfolio-Wert oder Stop-Loss-Abstand unbekannt)")

    # RM-4: Cash-Reserve - bei Unterschreitung wird jeder weitere Kauf blockiert
    # (konservativ: die konkrete Kaufgröße ist an dieser Stelle noch unbekannt).
    # Hybrid-Formel (2026-07-10, Nutzer-Wunsch): erforderliche Reserve ist das GROESSERE
    # aus (a) Prozentsatz vom Portfolio (skaliert mit wachsendem Risiko-Exposure) und
    # (b) einem festen Mindestbetrag in EUR (Vorhersehbarkeit bei kleinen Portfolios) -
    # reiner Prozentsatz allein wuerde bei kleinen Portfolios zu duenne Puffer in
    # absoluten Zahlen erlauben, ein reiner Festbetrag wuerde bei wachsendem Portfolio
    # nicht mitskalieren. Vergleich in USD (nicht Prozent), um einen sauberen Floor
    # zu ermoeglichen, der bei total_value_usd == 0 nicht kollabiert.
    required_reserve_pct_usd = total_value_usd * risiko_cfg["cash_reserve_min_prozent"] / 100
    required_reserve_fixed_usd = (
        risiko_cfg["cash_reserve_min_fixed_eur"] * eur_usd_fx_rate if eur_usd_fx_rate is not None else 0.0
    )
    required_reserve_usd = max(required_reserve_pct_usd, required_reserve_fixed_usd)
    if cash_value_usd < required_reserve_usd:
        veto_reasons.append(
            f"Cash-Reserve {cash_value_usd:.2f} USD ({cash_reserve_pct_current:.1f}%) < "
            f"erforderlichem Minimum {required_reserve_usd:.2f} USD (RM-4: max. von "
            f"{risiko_cfg['cash_reserve_min_prozent']}% oder "
            f"{risiko_cfg['cash_reserve_min_fixed_eur']:.0f} EUR)"
        )
        checks.append("RM-4: FEHLGESCHLAGEN - Cash-Reserve unter Minimum")
    else:
        checks.append(
            f"RM-4: OK - Cash-Reserve {cash_value_usd:.2f} USD ({cash_reserve_pct_current:.1f}%) "
            f">= erforderlichem Minimum {required_reserve_usd:.2f} USD"
        )

    # RM-Bitpanda: nicht auf Bitpanda (der tatsaechlichen Handelsboerse des Nutzers)
    # gelistete Krypto-Assets koennen nicht gekauft werden - Veto analog RM-1/2/4/5.
    # Nur fuer assetklasse=="krypto" relevant (Aktien/ETF/Rohstoffe: kein Vergleich
    # sinnvoll, siehe ui/app.py). bitpanda_gelistet is None (Abruf fehlgeschlagen)
    # -> kein Veto (P-10: unbekannt != Ausschlussgrund).
    if asset.assetklasse == "krypto" and bitpanda_gelistet is False:
        veto_reasons.append(
            f"{asset.symbol} ist nicht bei Bitpanda gelistet - auf der Handelsbörse "
            "des Nutzers aktuell nicht kaufbar"
        )
        checks.append("RM-Bitpanda: FEHLGESCHLAGEN - nicht bei Bitpanda gelistet")
    elif asset.assetklasse == "krypto" and bitpanda_gelistet is True:
        checks.append("RM-Bitpanda: OK - bei Bitpanda gelistet")
    else:
        checks.append("RM-Bitpanda: übersprungen (nicht krypto oder Status unbekannt)")

    # RM-2: max. Allokation je Einzelwert. Core-Assets (BTC/ETH) haben eine eigene,
    # hoehere Grenze (2026-07-07 eingefuehrt, vorlaeufig - Thema "BTC hat den Lead"
    # noch explizit zu besprechen, siehe Memory project_offene_agent_diskussionspunkte).
    max_allok_pct = (
        risiko_cfg["max_allokation_pro_core_asset_prozent"]
        if asset.typ == "core"
        else risiko_cfg["max_allokation_pro_asset_prozent"]
    )
    # Cash-Reserve-Ziel (Baustein 3): Allokations-Headroom in USD immer berechnen
    # (auch im Veto-Fall, dort schlicht <= 0) - unabhaengig davon, ob RM-1 ueberhaupt
    # einen max_position_size_usd liefern konnte.
    rm2_allocation_headroom_usd = (
        total_value_usd * (max_allok_pct - allocation_pct_current) / 100 if total_value_usd > 0 else None
    )
    if allocation_pct_current >= max_allok_pct:
        veto_reasons.append(
            f"Allokation {allocation_pct_current:.1f}% bereits >= Limit {max_allok_pct}% (RM-2)"
        )
        checks.append("RM-2: FEHLGESCHLAGEN - Asset-Allokation am/über Limit")
    else:
        checks.append(f"RM-2: OK - Allokation {allocation_pct_current:.1f}% von {max_allok_pct}%")
        if max_position_size_usd is not None and rm2_allocation_headroom_usd is not None:
            max_position_size_usd = min(max_position_size_usd, rm2_allocation_headroom_usd)

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
        rm1_risk_ceiling_usd=rm1_risk_ceiling_usd,
        rm2_allocation_headroom_usd=rm2_allocation_headroom_usd,
        rm4_required_reserve_usd=required_reserve_usd,
    )


@dataclass
class CashReserveZielResult:
    """AZ-4 Baustein 3 (2026-07-12): Zielgroesse fuer die Cash-Reserve, die eine
    gestaffelte Nachkauf-Kampagne (AZ-4-Tranchen, Baustein 1) ueber BTC UND ETH
    hinweg realistisch abdecken wuerde - REIN INFORMATIV, kein neues Veto. RM-4
    bleibt der bestehende harte Minimum-Floor in risk_gate.py::pre_check()."""
    btc_ziel_usd: float | None
    eth_ziel_usd: float | None
    gesamt_ziel_usd: float | None  # RM-4-Minimum + btc_ziel_usd + eth_ziel_usd
    rm4_minimum_usd: float | None
    begruendung: str


def _cash_reserve_ziel_pro_asset(
    result: RiskPreCheckResult, rundengewichte: tuple[float, float, float], asset_label: str
) -> tuple[float | None, str]:
    """Gibt (ziel_usd, begruendungs_teilsatz) fuer ein einzelnes Asset (BTC/ETH)
    zurueck. Methodik (Nutzer-Diskussion 2026-07-12): 3 Runden, jede unabhaengig so
    bemessen wie ein einzelner Trade heute (RM-1-Risiko-Obergrenze) - naiv summiert
    also 3x diese Zahl. Das wird hart durch die RM-2-Allokations-Obergrenze gedeckelt
    (strukturelles Limit, kann nie ueberschritten werden), erst DANACH werden die
    20/30/50-Gewichte auf die gedeckelte Gesamtsumme verteilt (sonst wuerde sich die
    Gewichtung rechnerisch wegkuerzen - min()-Deckelung zuerst, Gewichtung danach)."""
    if result.rm1_risk_ceiling_usd is None:
        return None, f"{asset_label}: nicht berechenbar (RM-1-Risiko-Obergrenze nicht verfügbar)."

    naive_total = len(rundengewichte) * result.rm1_risk_ceiling_usd
    if result.rm2_allocation_headroom_usd is not None:
        capped_total = max(0.0, min(naive_total, result.rm2_allocation_headroom_usd))
    else:
        capped_total = naive_total

    if capped_total <= 0:
        return 0.0, f"{asset_label}: 0 $ (Allokation bereits am/über RM-2-Limit, kein Spielraum für weitere Nachkäufe)."

    runden_text = ", ".join(
        f"Runde {i + 1} {gewicht:.0f}% = {gewicht / 100 * capped_total:,.0f} $"
        for i, gewicht in enumerate(rundengewichte)
    )
    begruendung = (
        f"{asset_label}: {capped_total:,.0f} $ (3 Runden à heutiger RM-1-Obergrenze "
        f"{result.rm1_risk_ceiling_usd:,.0f} $, gedeckelt durch RM-2-Headroom "
        f"{result.rm2_allocation_headroom_usd:,.0f} $ falls kleiner; verteilt: {runden_text})."
    )
    return capped_total, begruendung


def compute_cash_reserve_ziel(
    btc_result: RiskPreCheckResult,
    eth_result: RiskPreCheckResult,
    rundengewichte: tuple[float, float, float] = (20.0, 30.0, 50.0),
) -> CashReserveZielResult:
    """AZ-4 Baustein 3 - reine Funktion, keine DB-/Netzwerk-Zugriffe. Nimmt die
    bereits fuer BTC und ETH berechneten RiskPreCheckResult-Objekte entgegen (siehe
    agent/krypto/pipeline.py::_compute_cash_reserve_ziel_context()). `rundengewichte`
    sind PROZENTWERTE (muessen auf 100 summieren, z.B. (20, 30, 50) - Nutzer-
    Entscheidung 2026-07-12), gleiche Konvention wie alle anderen Prozent-Werte in
    config.yaml (z.B. risiko_pro_trade_prozent: 2, nicht 0.02). Wird hier NICHT
    validiert (config.yaml-Ladefehler waeren ein Aufrufer-Problem, P-10 gilt fuer
    Datenverfuegbarkeit, nicht fuer Konfigurationsfehler)."""
    btc_ziel_usd, btc_begruendung = _cash_reserve_ziel_pro_asset(btc_result, rundengewichte, "BTC")
    eth_ziel_usd, eth_begruendung = _cash_reserve_ziel_pro_asset(eth_result, rundengewichte, "ETH")

    rm4_minimum_usd = btc_result.rm4_required_reserve_usd or eth_result.rm4_required_reserve_usd
    gesamt_ziel_usd = None
    if rm4_minimum_usd is not None and btc_ziel_usd is not None and eth_ziel_usd is not None:
        gesamt_ziel_usd = rm4_minimum_usd + btc_ziel_usd + eth_ziel_usd

    begruendung = (
        f"RM-4-Minimum {rm4_minimum_usd:,.0f} $ + {btc_begruendung} {eth_begruendung}"
        if rm4_minimum_usd is not None
        else f"{btc_begruendung} {eth_begruendung} (RM-4-Minimum nicht verfügbar)"
    )

    return CashReserveZielResult(
        btc_ziel_usd=btc_ziel_usd,
        eth_ziel_usd=eth_ziel_usd,
        gesamt_ziel_usd=gesamt_ziel_usd,
        rm4_minimum_usd=rm4_minimum_usd,
        begruendung=begruendung,
    )


_BUY_ACTIONS = ("KAUFEN", "NACHKAUFEN")


def post_check(parsed: dict, pre_result: RiskPreCheckResult, regime_result, config: dict) -> dict:
    """Nimmt die bereits validierte (siehe agent/analyst.py) Groq-Antwort und erzwingt
    RM-1/-2/-4/-5, Mindest-Konfidenz (R-5.10) und CRV >= 2.0 (Z-2) noch einmal
    deterministisch. Klemmt zusaetzlich eine zu gross vorgeschlagene Positionsgroesse
    auf die RM-1/RM-2-Obergrenze (Korrektur, kein Veto). Gibt die (ggf. korrigierte)
    Antwort + Veto-Metadaten zurueck."""
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
        entry = result.get("entry") or {}
        stop = result.get("stop_loss") or {}
        take = result.get("take_profit") or {}
        entry_von, entry_bis = entry.get("usd_von"), entry.get("usd_bis")
        stop_von = stop.get("usd_von")
        take_von = take.get("usd_von")
        if entry_von is not None and entry_bis is not None and stop_von is not None and take_von is not None:
            entry_mid = (entry_von + entry_bis) / 2
            crv = (take_von - entry_mid) / (entry_mid - stop_von) if entry_mid > stop_von else None
            if crv is None or crv < CRV_MINIMUM:
                risk_veto = True
                reason = (
                    f"CRV {crv} unter Minimum {CRV_MINIMUM} (Z-2, konservativ: "
                    f"Entry-Mitte {entry_mid}, ungünstigster Stop {stop_von}, ungünstigstes Ziel {take_von})"
                )
                risk_veto_reason = f"{risk_veto_reason}; {reason}" if risk_veto_reason else reason
                action = "HALTEN"

    # RM-1/RM-2: Positionsgroesse deterministisch auf die von pre_check() berechnete
    # Obergrenze klemmen, statt bei Ueberschreitung die ganze Kauf-Idee zu veto'en -
    # eine zu gross vorgeschlagene Positionsgroesse macht die Idee nicht ungueltig,
    # nur die Groesse falsch (anders als CRV/Konfidenz/Bitpanda-Veto oben). Bisher nur
    # als Fakt an Groq gegeben (risiko_check.max_positionsgroesse_*), aber nie
    # nachtraeglich erzwungen - diese Luecke schliesst dieser Block. Transparent im
    # Notizfeld vermerkt, damit der Nutzer sieht, dass korrigiert wurde.
    if action in _BUY_ACTIONS:
        position_size = result.get("position_size") or {}
        proposed_usd = position_size.get("usd")
        max_usd = pre_result.max_position_size_usd
        if proposed_usd is not None and max_usd is not None and proposed_usd > max_usd:
            fx = None
            proposed_eur = position_size.get("eur")
            if proposed_eur is not None and proposed_usd:
                fx = proposed_eur / proposed_usd
            clamp_note = (
                f"Von {proposed_usd:.2f} USD auf Risiko-Obergrenze {max_usd:.2f} USD "
                "gekürzt (RM-1/RM-2, deterministisch erzwungen)."
            )
            position_size["usd"] = max_usd
            position_size["eur"] = max_usd * fx if fx is not None else pre_result.max_position_size_eur
            existing_note = position_size.get("note")
            position_size["note"] = f"{existing_note} {clamp_note}" if existing_note else clamp_note
            result["position_size"] = position_size

    # R-5.9: TAUSCHEN statt VERKAUFEN, wenn ein Swap-Ziel genannt wurde (P-6) -
    # mechanisch durchgesetzt statt nur per Prompt erhofft.
    if action == "VERKAUFEN" and result.get("tauschen_target_symbol"):
        action = "TAUSCHEN"

    result["action"] = action
    result["_risk_veto"] = risk_veto
    result["_risk_veto_reason"] = risk_veto_reason
    return result
