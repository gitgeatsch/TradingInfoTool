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
    # Cash-Veto als eigenes, robustes Feld (2026-07-18, Nutzer-Detailanalyse
    # "wann informiert das System ueber einen Cash-Block") - bewusst UNABHAENGIG
    # davon, ob `veto_reasons` (und damit `kauf_erlaubt`) am Ende ueberhaupt
    # etwas enthaelt: das Modell ist per Prompt-Regel angewiesen, bei
    # `risiko_check.kauf_erlaubt == false` von sich aus schon HALTEN zu sagen -
    # der bisherige `risk_veto`-Flag in post_check() feuert aber NUR, wenn das
    # Modell diese Regel MISSACHTET und trotzdem KAUFEN/NACHKAUFEN vorschlaegt.
    # Im (haeufigeren) Normalfall eines regelkonformen Modells blieb der
    # Cash-Block damit bisher komplett unsichtbar. cash_veto/cash_veto_reason
    # spiegeln den tatsaechlichen RM-4-Zustand, unabhaengig vom Modellverhalten.
    cash_veto: bool = False
    cash_veto_reason: str | None = None


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
        and a.rolle == "taktisch" and not a.ist_cash_aequivalent
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

    stablecoin_symbols = {a.symbol for a in watchlist if a.ist_cash_aequivalent}
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
    # Grund fuer den Ausschluss des Fiat-Guthabens (2026-07-18, Detailanalyse
    # Punkt 3) - bisher landete das nur in `checks` (verworfen, siehe unten),
    # jetzt zusaetzlich festgehalten, um es bei einem tatsaechlichen RM-4-Veto
    # als Ursache anzuhaengen, statt den Nutzer raten zu lassen.
    fiat_cash_excluded_note = None
    if fiat_cash_eur > 0:
        if eur_usd_fx_rate is not None:
            fiat_cash_usd = fiat_cash_eur * eur_usd_fx_rate
            checks.append(f"RM-4: Fiat-Guthaben {fiat_cash_eur:.2f} EUR = {fiat_cash_usd:.2f} USD beruecksichtigt")
        else:
            fiat_cash_excluded_note = (
                f"Hinweis: {fiat_cash_eur:.2f} EUR Fiat-Guthaben vorhanden, aber EUR/USD-Kurs "
                "(EURCV) nicht verfuegbar - NICHT in der Cash-Reserve mitgezaehlt."
            )
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
    cash_veto = False
    cash_veto_reason = None
    if cash_value_usd < required_reserve_usd:
        cash_veto = True
        cash_veto_reason = (
            f"Cash-Reserve {cash_value_usd:.2f} USD ({cash_reserve_pct_current:.1f}%) < "
            f"erforderlichem Minimum {required_reserve_usd:.2f} USD (RM-4: max. von "
            f"{risiko_cfg['cash_reserve_min_prozent']}% oder "
            f"{risiko_cfg['cash_reserve_min_fixed_eur']:.0f} EUR)"
        )
        if fiat_cash_excluded_note:
            cash_veto_reason = f"{cash_veto_reason} {fiat_cash_excluded_note}"
        veto_reasons.append(cash_veto_reason)
        checks.append("RM-4: FEHLGESCHLAGEN - Cash-Reserve unter Minimum")
    else:
        checks.append(
            f"RM-4: OK - Cash-Reserve {cash_value_usd:.2f} USD ({cash_reserve_pct_current:.1f}%) "
            f">= erforderlichem Minimum {required_reserve_usd:.2f} USD"
        )
        # NEU (2026-07-17, Spot-Regelwerk-Konsistenzpruefung): RM-4 war bisher rein
        # rueckwaertsgerichtet - prueft nur, ob die Reserve JETZT SCHON unter dem
        # Minimum liegt, nie ob der vorgeschlagene Kauf SELBST die Reserve erst
        # darunter druecken wuerde (anders als RM-1/RM-2, die beide vorwaerts-
        # gerichtet eine Obergrenze berechnen). Cash-Reserve-Headroom analog zu
        # RM-2s Allokations-Headroom (siehe unten) direkt in die Positionsgroessen-
        # Obergrenze einrechnen, bevor ueberhaupt ein Vorschlag entsteht - ein
        # einzelner Kauf kann die Reserve dadurch nicht mehr unter das Minimum
        # druecken, unabhaengig davon, was der Rest des Portfolios vorschlaegt.
        cash_reserve_headroom_usd = cash_value_usd - required_reserve_usd
        if max_position_size_usd is not None:
            max_position_size_usd = min(max_position_size_usd, max(0.0, cash_reserve_headroom_usd))
            checks.append(
                f"RM-4: Positionsgrößen-Obergrenze zusätzlich auf Cash-Reserve-Headroom "
                f"{cash_reserve_headroom_usd:.2f} USD begrenzt (verhindert, dass der Kauf selbst "
                "die Reserve unter das Minimum drückt)."
            )

    # RM-Bitpanda: nicht auf Bitpanda (der tatsaechlichen Handelsboerse des Nutzers)
    # gelistete Assets koennen nicht gekauft werden - Veto analog RM-1/2/4/5. Bis
    # 2026-07-16 nur fuer assetklasse=="krypto" geprueft (Audit-Fund: Aktien-Pipeline
    # reicht bitpanda_gelistet=None durch, kein Vergleich fand je statt) - jetzt
    # assetklassen-neutral, der Aufrufer liefert den Wert (agent/krypto/pipeline.py
    # ueber get_listed_assets(), agent/aktien/pipeline.py ueber die neue
    # get_listed_non_crypto_assets(), beide api/bitpanda.py). bitpanda_gelistet is
    # None (Abruf fehlgeschlagen ODER Aufrufer verzichtet bewusst) -> kein Veto
    # (P-10: unbekannt != Ausschlussgrund).
    if bitpanda_gelistet is False:
        veto_reasons.append(
            f"{asset.symbol} ist nicht bei Bitpanda gelistet - auf der Handelsbörse "
            "des Nutzers aktuell nicht kaufbar"
        )
        checks.append("RM-Bitpanda: FEHLGESCHLAGEN - nicht bei Bitpanda gelistet")
    elif bitpanda_gelistet is True:
        checks.append("RM-Bitpanda: OK - bei Bitpanda gelistet")
    else:
        checks.append("RM-Bitpanda: übersprungen (Status unbekannt)")

    # RM-2: max. Allokation je Einzelwert. Core-Assets (BTC/ETH) haben eine eigene,
    # hoehere Grenze (2026-07-07 eingefuehrt, vorlaeufig - Thema "BTC hat den Lead"
    # noch explizit zu besprechen, siehe Memory project_offene_agent_diskussionspunkte).
    max_allok_pct = (
        risiko_cfg["max_allokation_pro_core_asset_prozent"]
        if asset.rolle == "core"
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
        asset.rolle == "taktisch" and not asset.ist_cash_aequivalent
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
        cash_veto=cash_veto,
        cash_veto_reason=cash_veto_reason,
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


def post_check(
    parsed: dict, pre_result: RiskPreCheckResult, regime_result, config: dict, confluence=None,
) -> dict:
    """Nimmt die bereits validierte (siehe agent/analyst.py) Groq-Antwort und erzwingt
    RM-1/-2/-4/-5, Mindest-Konfidenz (R-5.10) und CRV >= 2.0 (Z-2) noch einmal
    deterministisch. Klemmt zusaetzlich eine zu gross vorgeschlagene Positionsgroesse
    auf die RM-1/RM-2-Obergrenze (Korrektur, kein Veto). Gibt die (ggf. korrigierte)
    Antwort + Veto-Metadaten zurueck.

    `confluence` (2026-07-18, Nutzer-Fund am echten CAT-Fall: "Ergebnis ist
    durchgaengig eher schlecht" trotz 80% Konfidenz) optional - ohne sie faellt
    nur der neue Konflikt-Deckel unten weg, der Rest der Funktion bleibt
    unveraendert funktionsfaehig (P-10)."""
    result = dict(parsed)
    risk_veto = False
    risk_veto_reason = None
    crv = None

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
    #
    # 2026-07-16 ergaenzt: die Obergrenze selbst ist jetzt Konfidenz-skaliert statt
    # flach - gaengige Trading-Praxis (konviktionsgewichtete Positionsgroesse). Eine
    # Empfehlung genau an der Regime-Mindestschwelle (R-5.10, min_konfidenz_prozent)
    # ist der am wenigsten ueberzeugende noch durchgelassene Fall und bekommt nur den
    # Sockel-Anteil (config risiko.konfidenz_positionsgroesse_sockel_anteil, Default
    # 50%) der Obergrenze; bei 100% Konfidenz die volle Obergrenze, linear dazwischen.
    # Vorher clusterten reale Positionsgroessen empirisch nahe 100% der Obergrenze
    # unabhaengig von der tatsaechlichen Konfidenz (Nutzer-Beobachtung 2026-07-16).
    if action in _BUY_ACTIONS:
        position_size = result.get("position_size") or {}
        proposed_usd = position_size.get("usd")
        max_usd = pre_result.max_position_size_usd
        max_eur = pre_result.max_position_size_eur
        if max_usd is not None:
            effective_max_usd = max_usd
            effective_max_eur = max_eur
            konfidenz_scale_note = None
            sockel_anteil = config["risiko"].get("konfidenz_positionsgroesse_sockel_anteil")
            min_konfidenz = (
                config["regime"]["profile"].get(regime_result.regime, {}).get("min_konfidenz_prozent")
            )
            confidence = result.get("confidence_pct")
            if (
                sockel_anteil is not None
                and min_konfidenz is not None
                and confidence is not None
                and min_konfidenz < 100
            ):
                spanne = max(0.0, min(1.0, (confidence - min_konfidenz) / (100 - min_konfidenz)))
                scale = sockel_anteil + (1 - sockel_anteil) * spanne
                effective_max_usd = max_usd * scale
                effective_max_eur = max_eur * scale if max_eur is not None else None
                konfidenz_scale_note = (
                    f"Obergrenze bei Konfidenz {confidence}% auf {scale * 100:.0f}% skaliert "
                    f"(Sockel {sockel_anteil * 100:.0f}% bei {min_konfidenz}% Konfidenz, "
                    "100% bei 100% Konfidenz)."
                )

            # Gegenszenario-Wahrscheinlichkeit (2026-07-17, Regelwerk-Konsistenzpruefung
            # nach dem Hebel-Fix, analog hebel_risk_gate.py::post_check_hebel()): das
            # Modell liefert bereits forecast.bear.probability_pct, wurde bisher aber nie
            # ausgewertet - derselbe blinde Fleck wie beim urspruenglichen Hebel-Fund.
            # Anders als bei Hebel gibt es hier kein Liquidationsrisiko, daher bewusst
            # KEIN hartes Veto, sondern eine zusaetzliche multiplikative Deckelung der
            # ohnehin schon konfidenz-skalierten Obergrenze - konsistent mit der
            # bestehenden RM-1/RM-2-Korrektur-statt-Veto-Philosophie dieser Funktion.
            gegenszenario_note = None
            forecast = result.get("forecast") or {}
            gegenszenario_pct = (forecast.get("bear") or {}).get("probability_pct")
            gegenszenario_schwelle = config["risiko"].get("gegenszenario_wahrscheinlichkeit_schwelle_prozent")
            gegenszenario_deckel_anteil = config["risiko"].get("gegenszenario_positionsgroesse_deckel_anteil")
            if (
                gegenszenario_pct is not None
                and gegenszenario_schwelle is not None
                and gegenszenario_deckel_anteil is not None
                and gegenszenario_pct >= gegenszenario_schwelle
            ):
                effective_max_usd = effective_max_usd * gegenszenario_deckel_anteil
                effective_max_eur = (
                    effective_max_eur * gegenszenario_deckel_anteil if effective_max_eur is not None else None
                )
                gegenszenario_note = (
                    f"Obergrenze wegen hoher Bear-Szenario-Wahrscheinlichkeit "
                    f"({gegenszenario_pct:.0f}% >= Schwelle {gegenszenario_schwelle:.0f}%) zusaetzlich auf "
                    f"{gegenszenario_deckel_anteil * 100:.0f}% reduziert (Gegenszenario-Deckel)."
                )

            # Technischer Konflikt (2026-07-18, Nutzer-Fund am echten CAT-Fall,
            # "Ergebnis durchgaengig eher schlecht" trotz 80% Konfidenz):
            # summarize_confluence() klassifiziert bereits deterministisch
            # "gemischt" (weder bullish noch bearish dominiert), das wurde bisher
            # nirgends im Risiko-Gate ausgewertet - genau der Fall, der beim
            # CAT-Signal vorlag ("EMA-Ordnung ist bearish, aber MACD/RSI bieten
            # Gegenargumente"). Deterministisch, haengt NICHT davon ab, ob das
            # Modell den Widerspruch selbst benennt.
            konflikt_note = None
            if confluence is not None and confluence.overall_bias == "gemischt":
                konflikt_deckel_anteil = config["risiko"].get("technischer_konflikt_deckel_anteil")
                if konflikt_deckel_anteil is not None:
                    effective_max_usd = effective_max_usd * konflikt_deckel_anteil
                    effective_max_eur = (
                        effective_max_eur * konflikt_deckel_anteil if effective_max_eur is not None else None
                    )
                    konflikt_note = (
                        f"Obergrenze wegen widerspruechlicher technischer Konfluenz (weder bullish "
                        f"noch bearish dominiert) zusaetzlich auf {konflikt_deckel_anteil * 100:.0f}% "
                        "reduziert (Konflikt-Deckel)."
                    )

            # CRV knapp am Minimum (2026-07-18, gleicher Fund): CRV_MINIMUM ist
            # bisher ein binaeres Gate - 2,01 und 4,0 werden identisch behandelt,
            # obwohl ein CRV knapp ueber der Grenze ein deutlich schwaecheres
            # Setup ist (beim CAT-Fall lag das CRV bei ca. 2,08). Analog zur
            # Konfidenz-Skalierung: je naeher am Minimum, desto kleiner die
            # zulaessige Position.
            crv_knapp_note = None
            crv_knapp_schwelle_relativ = config["risiko"].get("crv_knapp_schwelle_relativ")
            crv_knapp_deckel_anteil = config["risiko"].get("crv_knapp_positionsgroesse_deckel_anteil")
            if (
                crv is not None
                and crv_knapp_schwelle_relativ is not None
                and crv_knapp_deckel_anteil is not None
                and crv < CRV_MINIMUM * (1 + crv_knapp_schwelle_relativ)
            ):
                effective_max_usd = effective_max_usd * crv_knapp_deckel_anteil
                effective_max_eur = (
                    effective_max_eur * crv_knapp_deckel_anteil if effective_max_eur is not None else None
                )
                crv_knapp_note = (
                    f"Obergrenze wegen CRV knapp am Minimum ({crv:.2f}, Minimum {CRV_MINIMUM:.1f}) "
                    f"zusaetzlich auf {crv_knapp_deckel_anteil * 100:.0f}% reduziert (CRV-Knapp-Deckel)."
                )

            if proposed_usd is not None and proposed_usd > effective_max_usd:
                fx = None
                proposed_eur = position_size.get("eur")
                if proposed_eur is not None and proposed_usd:
                    fx = proposed_eur / proposed_usd
                clamp_note = (
                    f"Von {proposed_usd:.2f} USD auf Risiko-Obergrenze {effective_max_usd:.2f} USD "
                    "gekürzt (RM-1/RM-2, deterministisch erzwungen)."
                )
                if konfidenz_scale_note:
                    clamp_note = f"{clamp_note} {konfidenz_scale_note}"
                if gegenszenario_note:
                    clamp_note = f"{clamp_note} {gegenszenario_note}"
                if konflikt_note:
                    clamp_note = f"{clamp_note} {konflikt_note}"
                if crv_knapp_note:
                    clamp_note = f"{clamp_note} {crv_knapp_note}"
                position_size["usd"] = effective_max_usd
                position_size["eur"] = effective_max_usd * fx if fx is not None else effective_max_eur
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
    # Cash-Veto (2026-07-18, Detailanalyse) - bewusst IMMER durchgereicht, nicht
    # nur bei einer tatsaechlichen Aktions-Ueberschreibung (siehe cash_veto-
    # Docstring in RiskPreCheckResult): das ist der tatsaechliche RM-4-Zustand
    # dieser Bewertung, unabhaengig davon, ob das Modell selbst schon
    # regelkonform HALTEN gesagt hat.
    result["_cash_veto"] = pre_result.cash_veto
    result["_cash_veto_reason"] = pre_result.cash_veto_reason
    return result
