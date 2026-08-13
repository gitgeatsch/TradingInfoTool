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

import re
from dataclasses import dataclass, field
from datetime import datetime

import numpy as np

import database.db as db
from indicators.calculations import TechnicalSnapshot, latest_value

# 2026-07-25, Nutzer-Diskussion (echter INJ-Fund, hebel_risk_gate.py-Pendant) -
# bewusst KEINE Uhrzeit-Schwelle, siehe dortiger Docstring.
DEFAULT_RICHTUNGSWENDE_ATR_SCHWELLE = 0.5

STOP_LOSS_ATR_MULTIPLE = 2.0  # Arbeits-Konvention, nicht spezifikationsseitig vorgegeben
CRV_MINIMUM = 2.0  # Z-2

# Konfidenz-Einstufung (2026-07-19/20, ohne benannte Konstante an dieser UND an
# hebel_risk_gate.py::compute_risikofaktoren_hebel() dupliziert) - hier als
# EINZIGE Quelle der Wahrheit benannt, hebel_risk_gate.py importiert von hier
# (dasselbe Muster wie bereits bei CRV_MINIMUM). Zusaetzlich seit 2026-07-24
# von hebel_risk_gate.py::post_check_hebel() fuer die Kontrathese-Uebersetzung
# wiederverwendet (SCHLIESSEN ab KONFIDENZ_SCHWELLE_HOCH, TEILVERKAUF ab
# KONFIDENZ_SCHWELLE_NIEDRIG) - dieselben, dem Nutzer bereits aus jedem
# Signal-Risikofaktor bekannten Grenzen, keine neu erfundene Zahl.
KONFIDENZ_SCHWELLE_NIEDRIG = 55.0
KONFIDENZ_SCHWELLE_HOCH = 70.0

# Symbole, deren gestakter Anteil NICHT in die Risikoberechnung einfliesst
# (konservativ, Z-1): Un-/Restaking dort bisher nicht instant moeglich.
# Stand 2026-07-11 (Nutzer-Erfahrung): nur ETH betroffen, alle anderen
# bisher gestakten Bitpanda-Assets waren instant handelbar - bei neuen
# gestakten Assets pruefen, ob diese Liste erweitert werden muss.
STAKING_ILLIQUID_SYMBOLS = {"ETH"}

# 2026-07-28 (Punkt 4 der Fakten_Entscheidungsmappe.md-Prioritaetenliste):
# bewusst dupliziert statt von hebel_risk_gate.py importiert - Spot (lang-
# fristige Investitionsthese) und Hebel (kurzfristige Taktik) koennten hier
# inhaltlich auseinanderlaufen (Nutzer-Einschaetzung), z.B. falls Spot
# irgendwann einen Begriff braucht, den Hebel nicht kennt oder umgekehrt.
# Nur fuer den Krypto-Spot-Aufruf gedacht (siehe post_check()-Parameter
# `filter_retail_konsens_top_gruende` unten) - NICHT generisch in post_check()
# fuer alle 4 Spot-family-Pipelines aktiv, weil Aktien/Rohstoffe/Themen-ETF
# das Retail-Konten-Konzept gar nicht kennen (Aktien hat mit
# `short_interest_finra` ein aehnlich klingendes, aber fachlich anderes
# Konzept - institutionelle FINRA-Meldungen, kein Retail-Konsens - der Regex
# wuerde dort zwar vermutlich nicht anschlagen, aber "vermutlich nicht" ist
# keine Basis fuer einen Filter in einer gemeinsam genutzten Funktion).
_RETAIL_KONSENS_TOP_GRUND_MUSTER = re.compile(
    r"(long|short)[- ]?konten|retail[- ]?(konsens|bias|positionierung|trader)|long[- ]?short[- ]?ratio",
    re.IGNORECASE,
)


def filtere_retail_konsens_top_gruende(top_gruende: list) -> list:
    """Entfernt top_gruende-Eintraege, deren Text auf Retail-/Long-Konten-
    Positionierung verweist, komplett - unabhaengig von der angegebenen
    Kategorie. Identische Logik wie hebel_risk_gate.py::
    filtere_retail_konsens_top_gruende() (bewusst dupliziert, siehe Kommentar
    oben), Aufloeser 2026-07-26: Positionierungsdaten sagen etwas ueber
    Squeeze-/Liquidations-Risiko aus, nicht darueber, ob der Kurs steigen
    sollte - ein Kategorie-Fehler in der Begruendung, unabhaengig von Long
    oder Short. Lenient: fehlende Rangplaetze sind unschaedlich (pipeline.py
    liest top_gruende je Rang per .get() mit None-Default)."""
    if not isinstance(top_gruende, list):
        return top_gruende
    return [
        eintrag for eintrag in top_gruende
        if not _RETAIL_KONSENS_TOP_GRUND_MUSTER.search(str((eintrag or {}).get("text") or ""))
    ]


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
    # 2026-08-02 (RM-1d): der Portfoliowert selbst wird in post_check() gebraucht,
    # um den Ziel-Positionszahl-Deckel zu rechnen. Bisher blieb er in pre_check()
    # eingeschlossen und war nicht rekonstruierbar (rm2_allocation_headroom_usd
    # allein reicht nicht, da max_allok_pct dort nicht mit exponiert ist).
    total_value_usd: float | None = None
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
        total_value_usd=total_value_usd,
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
# Gespiegelte CRV-Pflicht (2026-07-27, Nutzer-Wunsch: "verkaufen sprich short
# Richtung muss aus dem Trading ebenfalls eine Zielzone haben welche dann
# umgekehrt funktioniert - also mathematisch deterministisch wie fuer die
# kauf-/long Positionen") - siehe post_check()-Block unten. TAUSCHEN ist
# Krypto-Spot-exklusiv (siehe agent/krypto/gegenpruefung.py), hier trotzdem
# generisch gefuehrt, da die 4 Spot-family-Pipelines dieselbe post_check()
# wiederverwenden. Hedge NICHT betroffen (eigener Deterministik-Deckel, siehe
# agent/hedge/analyst.py Regel 9 - bewusst KEINE CRV-Pflicht).
_SELL_ACTIONS = ("VERKAUFEN", "TAUSCHEN")


@dataclass
class Risikofaktor:
    """2026-07-19 (E-Mail-/App-Neustrukturierung in 3 Abschnitte - Mathematisch
    berechnet / LLM-Bewertung / Konklusion, echter AVAX-Hebel-Fund). Bewusst
    eine eigene, identische Definition statt Import aus hebel_risk_gate.py -
    dieses Modul importiert bereits CRV_MINIMUM VON hebel_risk_gate.py aus der
    Gegenrichtung, ein Rueckimport wuerde einen Zirkelbezug riskieren (siehe
    Modul-Docstring oben: bewusst getrennte Module)."""
    name: str
    bewertung: str  # "positiv" | "neutral" | "negativ"
    begruendung: str
    # 2026-07-30 (Nutzer-Fund: Regime-Konflikt/-Ausrichtung fehlte bislang
    # komplett fuer die Spot-Familie, siehe compute_risikofaktoren()-Nachtrag
    # unten) - identisches Feld wie hebel_risk_gate.py::Risikofaktor.ist_kontext,
    # gleiche Begruendung: in einem anhaltenden Regime praktisch immer
    # vorhanden, daher Kontext-Hinweis statt gezaehlter Bulletpoint.
    ist_kontext: bool = False


def regime_konflikt(regime: str | None, richtung: str | None) -> bool:
    """Asset-neutrales Pendant zu hebel_risk_gate.py::regime_konflikt_hebel() -
    bewusst eigene Kopie statt Import (siehe Risikofaktor-Docstring oben:
    Zirkelbezug-Vermeidung). `richtung` erwartet "LONG"/"SHORT" (siehe
    agent/krypto/gegenpruefung.py::richtung_aus_action() - liefert genau diese
    Werte aus der Spot-family-Action KAUFEN/NACHKAUFEN/VERKAUFEN/TAUSCHEN).
    None (z.B. bei HALTEN oder fehlendem Regime) -> kein Konflikt."""
    if regime is None or richtung is None:
        return False
    return (regime == "baer" and richtung == "LONG") or (regime == "bulle" and richtung == "SHORT")


def _preis_am_datum(iso_zeitpunkt: str, dates, closes) -> float | None:
    """Eigene Kopie von hebel_risk_gate.py::_preis_am_datum() (siehe dortiger
    Docstring) - gleicher Zirkelbezug-Grund wie bei Risikofaktor oben."""
    if dates is None or closes is None or len(dates) == 0:
        return None
    try:
        ziel = datetime.fromisoformat(iso_zeitpunkt[:10]).date()
    except ValueError:
        return None
    ziel_str = ziel.isoformat()
    idx = int(np.searchsorted(dates, ziel_str))
    idx = min(idx, len(dates) - 1)
    if idx > 0:
        try:
            aktuell = abs((datetime.fromisoformat(str(dates[idx])).date() - ziel).days)
            vorherig = abs((datetime.fromisoformat(str(dates[idx - 1])).date() - ziel).days)
            if vorherig < aktuell:
                idx -= 1
        except ValueError:
            pass
    return float(closes[idx])


def richtungswende_risikofaktor(
    richtungswende: dict | None, current_price: float | None, atr_value: float | None,
    dates=None, closes=None, atr_schwelle_relativ: float | None = None,
) -> "Risikofaktor | None":
    """Eigene Kopie von hebel_risk_gate.py::richtungswende_risikofaktor() -
    identische Logik, Spot/Aktien/Rohstoffe/Themen-ETF-Pendant (Aufbau=KAUFEN/
    NACHKAUFEN, Abbau=VERKAUFEN/TAUSCHEN, siehe agent/krypto/
    signal_stabilitaet.py::juengste_richtungswende(), asset-klassen-neutral,
    keine eigene Kopie noetig)."""
    if richtungswende is None or current_price is None or atr_value is None or atr_value <= 0:
        return None
    basis_text = (
        f"Wechselte von {richtungswende['alte_kategorie']} ({richtungswende['alte_aktion']}) zu "
        f"{richtungswende['neue_kategorie']} ({richtungswende['neue_aktion']})"
    )
    alter_preis = _preis_am_datum(richtungswende["alter_zeitpunkt"], dates, closes)
    if alter_preis is None:
        return Risikofaktor(
            "Richtungswende", "neutral",
            f"{basis_text} - Kursbewegung seither nicht ermittelbar (keine Historie für den Zeitpunkt).",
        )
    bewegung_atr = abs(current_price - alter_preis) / atr_value
    schwelle = (
        atr_schwelle_relativ if atr_schwelle_relativ is not None else DEFAULT_RICHTUNGSWENDE_ATR_SCHWELLE
    )
    bestaetigt = bewegung_atr >= schwelle
    if bestaetigt:
        text = f"{basis_text} - bestätigt durch eine Kursbewegung von {bewegung_atr:.1f}× ATR seither."
    else:
        text = (
            f"{basis_text} - Kurs bewegte sich seither nur {bewegung_atr:.1f}× ATR (Schwelle "
            f"{schwelle:.1f}×) - die Wende ist noch nicht durch eine deutliche Kursbewegung bestätigt."
        )
    return Risikofaktor("Richtungswende", "neutral" if bestaetigt else "negativ", text)


def compute_risikofaktoren(
    *, action: str, cash_veto: bool, cash_veto_reason: str | None,
    risk_veto: bool, risk_veto_reason: str | None, confidence_pct: float | None,
    crv: float | None, confluence=None,
    gegenszenario_pct: float | None, gegenszenario_schwelle: float | None,
    crv_knapp_schwelle_relativ: float | None,
    retail_long_bias_extreme: bool | None = None, long_account_pct: float | None = None,
    liquiditaetszonen: dict | None = None,
    signal_stabilitaet: dict | None = None,
    atr_perzentil: float | None = None,
    atr_perzentil_hoch_schwelle: float | None = None,
    richtungswende: dict | None = None,
    current_price: float | None = None,
    atr_value: float | None = None,
    dates=None,
    closes=None,
    richtungswende_atr_schwelle: float | None = None,
    regime: str | None = None,
    regime_persistenz_tage: int | None = None,
) -> list["Risikofaktor"]:
    """Spot/Aktien/Rohstoffe/Themen-ETF-Pendant zu hebel_risk_gate.py::
    compute_risikofaktoren_hebel() - deterministische Zusammenfassung der
    bereits vorhandenen Deckel-/Veto-Checks in eine kompakte positiv/neutral/
    negativ-Liste fuer Abschnitt 3 der neuen E-Mail-/App-Struktur. Bewusst
    NICHT vom LLM generiert. Dafuer cash_veto, das es bei Hebel nicht gibt.

    Nachtrag 2026-07-30 (Regelwerk-Audit LLM-Optimierungen, Punkt B): die
    urspruengliche Docstring-Behauptung "kein eigenes Regime-Konflikt bei
    Spot" war falsch - RM-10/-11 (Hebel-Deckel) sind tatsaechlich
    hebel-spezifisch, aber die reine ANZEIGE eines Regime-Konflikts/einer
    -Ausrichtung (wie bei Hebel, `ist_kontext=True`) fehlte hier schlicht,
    obwohl `regime` fuer alle 4 Spot-family-Pipelines laengst ueber
    `post_check()`s `regime_result`-Parameter vorliegt. `regime`/`richtung`
    (aus `agent/krypto/gegenpruefung.py::richtung_aus_action()`) sind optional
    - ohne sie faellt nur dieser eine Risikofaktor weg (P-10), keine
    BTC-Relativwert-Daempfung wie bei Hebel (asset-uebergreifend nicht
    sinnvoll, betrifft nur Krypto-Alt-Coins gegen BTC).

    `action` erwartet hier bewusst die URSPRUENGLICHE, vom Modell vorgeschlagene
    Aktion (post_check()'s `original_action`, VOR jeder Veto-Ueberschreibung
    auf HALTEN) - nicht die finale, angezeigte Aktion. Grund (2026-07-20,
    Nutzer-Fund am echten KAITO-Fall): bei einem Risiko-Veto (z.B. CRV unter
    Minimum) hatte der Groq-Aufruf zu diesem Zeitpunkt laengst stattgefunden -
    Confluence/Gegenszenario-Wahrscheinlichkeit/Retail-Konsens/Konfidenz lagen
    also bereits vor, wurden aber komplett verworfen und nur der eine
    Veto-Grund gezeigt. Mit der urspruenglichen Aktion als Gate zeigt die
    Liste jetzt das VOLLE Bild der (abgelehnten) Kaufidee, waehrend die
    tatsaechliche Empfehlung (HALTEN) unveraendert bleibt."""
    faktoren: list[Risikofaktor] = []

    if cash_veto:
        faktoren.append(Risikofaktor(
            "Cash-Veto (RM-4)", "negativ",
            cash_veto_reason or "Cash-Reserve-Minimum unterschritten - Kauf blockiert.",
        ))

    if risk_veto:
        faktoren.append(Risikofaktor("Risiko-Veto", "negativ", risk_veto_reason or "Deterministisches Veto ausgelöst."))

    if action not in _BUY_ACTIONS:
        return faktoren

    # Regime-Konflikt/-Ausrichtung (2026-07-30, Nachtrag siehe Docstring oben,
    # Punkt B) - `action` ist an dieser Stelle durch den fruehen Return oben
    # bereits garantiert KAUFEN/NACHKAUFEN, die Richtung also immer "LONG"
    # (kein SHORT-Fall wie bei Hebel, siehe Retail-Konsens-Kommentar unten fuer
    # dieselbe Einschraenkung). Optional (nur wenn `regime` durchgereicht
    # wird) - fehlt es, faellt nur dieser eine Faktor weg.
    if regime is not None:
        persistenz_text = (
            f" Regime seit {regime_persistenz_tage} Tag(en) regelbasiert bestätigt."
            if regime_persistenz_tage is not None and regime_persistenz_tage > 0 else ""
        )
        if regime_konflikt(regime, "LONG"):
            faktoren.append(Risikofaktor(
                "Regime-Konflikt", "negativ",
                f"Kauf-Idee widerspricht dem aktuellen {regime}-Regime.{persistenz_text}",
                ist_kontext=True,
            ))
        else:
            faktoren.append(Risikofaktor(
                "Regime-Ausrichtung", "positiv",
                f"Kauf-Idee folgt dem aktuellen {regime}-Regime, kein Gegen-Trend-Setup.{persistenz_text}",
                ist_kontext=True,
            ))

    if gegenszenario_pct is not None and gegenszenario_schwelle is not None:
        if gegenszenario_pct >= gegenszenario_schwelle:
            faktoren.append(Risikofaktor(
                f"Gegenszenario-Wahrscheinlichkeit {gegenszenario_pct:.0f}%", "negativ",
                f"Modell schätzt die Wahrscheinlichkeit für das Gegenszenario hoch ein "
                f"(>= Schwelle {gegenszenario_schwelle:.0f}%).",
            ))
        else:
            faktoren.append(Risikofaktor(
                f"Gegenszenario-Wahrscheinlichkeit {gegenszenario_pct:.0f}%", "positiv",
                f"Modell schätzt das Gegenszenario als eher unwahrscheinlich ein "
                f"(< Schwelle {gegenszenario_schwelle:.0f}%).",
            ))

    if confluence is not None:
        if confluence.overall_bias == "gemischt":
            faktoren.append(Risikofaktor(
                "Technische Konfluenz", "negativ",
                "Technische Indikatoren widersprechen sich (weder bullish noch bearish dominiert).",
            ))
        else:
            # 2026-07-25, echter KAIA-Fund (hebel_risk_gate.py, hier gespiegelt):
            # eine "eindeutige Tendenz" wurde bisher IMMER als "positiv" gewertet,
            # selbst bearish - dieser Block laeuft nur fuer _BUY_ACTIONS (siehe
            # Zeile oben), die erwartete Tendenz ist hier deshalb immer bullish.
            stuetzt_kauf = confluence.overall_bias == "bullish"
            faktoren.append(Risikofaktor(
                "Technische Konfluenz", "positiv" if stuetzt_kauf else "negativ",
                f"Technische Indikatoren zeigen eine eindeutige Tendenz ({confluence.overall_bias}) - "
                + ("stützt den Kauf." if stuetzt_kauf else "widerspricht dem Kauf."),
            ))

    if crv is not None:
        if crv_knapp_schwelle_relativ is not None and crv < CRV_MINIMUM * (1 + crv_knapp_schwelle_relativ):
            faktoren.append(Risikofaktor(
                f"CRV {crv:.2f}", "negativ",
                f"Chance-Risiko-Verhältnis liegt nur knapp über dem Minimum ({CRV_MINIMUM:.1f}).",
            ))
        elif crv >= CRV_MINIMUM * 1.5:
            faktoren.append(Risikofaktor(
                f"CRV {crv:.2f}", "positiv",
                f"Chance-Risiko-Verhältnis liegt deutlich über dem Minimum ({CRV_MINIMUM:.1f}).",
            ))
        else:
            faktoren.append(Risikofaktor(
                f"CRV {crv:.2f}", "neutral", "Solide über dem Minimum, aber nicht herausragend.",
            ))

    # Retail-Konsens-Risiko (2026-07-19, echter AVAX-Hebel-Fund, Krypto-only -
    # Aktien/Rohstoffe/Themen-ETF liefern keine antizyklisch-Fakten, dann
    # bleiben beide Parameter None und dieser Block wird uebersprungen).
    # 2026-07-25, Fakt-zuerst-Fix aus hebel_risk_gate.py nachgezogen (dort seit
    # 2026-07-22, echter Fund: nicht-extreme Mehrheiten in dieselbe Richtung
    # wurden pauschal als "positiv/antizyklisch" gelabelt, auch wenn die
    # Empfehlung tatsaechlich mit der Mehrheit mitlief). Live per Datenanalyse
    # bestaetigt: von 98 bisherigen "positiv"-Faellen betrafen 79 tatsaechlich
    # eine nicht-extreme long-Mehrheit bei gleichzeitiger Kauf-Empfehlung -
    # haetten "neutral" statt "positiv" sein muessen. "Fakt zuerst": der Text
    # nennt IMMER explizit die Mehrheit, die Bewertung wird ERST DANACH
    # abgeleitet (3 Stufen statt binaerer Ja/Nein-Phrase). `action` ist an
    # dieser Stelle durch den fruehen Return oben immer KAUFEN/NACHKAUFEN -
    # anders als bei Hebel (LONG/SHORT) gibt es bei Spot keine "short-seitige"
    # Gegenrichtung zu pruefen, die Kauf-Empfehlung "folgt der Mehrheit" also
    # genau dann, wenn die Mehrheit selbst long ist.
    if long_account_pct is not None:
        mehrheit_ist_long = long_account_pct > 50.0
        mehrheits_pct = long_account_pct if mehrheit_ist_long else (100.0 - long_account_pct)
        mehrheits_richtung = "long" if mehrheit_ist_long else "short"
        fakt = (
            f"{long_account_pct:.0f}% der Retail-Konten sind long positioniert "
            f"({mehrheits_pct:.0f}% Mehrheit {mehrheits_richtung}) - die Kauf-Empfehlung liegt "
            f"{'in derselben Richtung wie' if mehrheit_ist_long else 'entgegen'} der Mehrheit."
        )
        if mehrheit_ist_long and retail_long_bias_extreme:
            faktoren.append(Risikofaktor(
                "Retail-Konsens-Risiko", "negativ",
                f"{fakt} Extreme Mehrheitspositionierung in dieselbe Richtung - antizyklisch "
                "betrachtet ein Kontraindikator, keine Stütze.",
            ))
        elif mehrheit_ist_long:
            faktoren.append(Risikofaktor(
                "Retail-Konsens-Risiko", "neutral",
                f"{fakt} Nicht extrem genug für einen klaren Kontraindikator, aber auch kein "
                "antizyklischer Pluspunkt.",
            ))
        else:
            faktoren.append(Risikofaktor(
                "Retail-Konsens-Risiko", "positiv",
                f"{fakt} Antizyklisch betrachtet ein unterstützendes Signal.",
            ))

    if confidence_pct is not None:
        if confidence_pct < KONFIDENZ_SCHWELLE_NIEDRIG:
            faktoren.append(Risikofaktor(
                f"Konfidenz {confidence_pct:.0f}%", "negativ", "Niedrige Konfidenz.",
            ))
        elif confidence_pct >= KONFIDENZ_SCHWELLE_HOCH:
            faktoren.append(Risikofaktor(f"Konfidenz {confidence_pct:.0f}%", "positiv", "Hohe Konfidenz."))
        else:
            faktoren.append(Risikofaktor(f"Konfidenz {confidence_pct:.0f}%", "neutral", "Mittlere Konfidenz."))

    # Liquiditaetszonen (Marketmaker-Konzept, Stufe 1, 2026-07-23, Krypto-only
    # - siehe agent/krypto/liquidity_zones.py Modul-Docstring): rein
    # informativ/neutral, KEIN Deckel. Aktien/Rohstoffe/Themen-ETF reichen
    # dieses Feld nie durch (bleibt None), Block wird dort uebersprungen.
    if liquiditaetszonen is not None and liquiditaetszonen.get("in_naehe_ungefegter_zone"):
        seite = liquiditaetszonen.get("seite")
        zone = liquiditaetszonen.get(
            "naechste_buyside_zone" if seite == "buyside" else "naechste_sellside_zone"
        ) or {}
        faktoren.append(Risikofaktor(
            f"Nähe zu Liquiditätszone ({seite})", "neutral",
            f"Kurs liegt {zone.get('abstand_prozent')}% von einer noch nicht gefegten "
            f"{'Buy-Side' if seite == 'buyside' else 'Sell-Side'}-Zone entfernt "
            f"({zone.get('touches')} Beruehrungen, zuletzt {zone.get('letzte_beruehrung_datum')}) - "
            "moegliches Stop-Hunt-Risiko vor der eigentlichen Bewegung, kein Richtungsurteil.",
        ))

    # Signal-Stabilitaet (2026-07-25, echter NEAR/LINK-Fund, Krypto-only wie
    # Liquiditaetszonen - Aktien/Rohstoffe/Themen-ETF reichen dieses Feld nie
    # durch): echter Warncharakter, nicht nur neutral - eine ueber mehrere
    # Zyklen an der Gate-Schwelle oszillierende Konfidenz ist eine
    # tatsaechlich geringere Verlaesslichkeit.
    if signal_stabilitaet is not None:
        faktoren.append(Risikofaktor(
            "Signal-Stabilität", "negativ" if not signal_stabilitaet["stabil"] else "positiv",
            signal_stabilitaet["einordnung"],
        ))

    # Richtungswende (2026-07-25, echter INJ-Fund, Krypto-only wie oben) -
    # eigener Faktor statt Teil von Signal-Stabilitaet, siehe
    # richtungswende_risikofaktor()-Docstring.
    rw_faktor = richtungswende_risikofaktor(
        richtungswende, current_price, atr_value, dates, closes, richtungswende_atr_schwelle,
    )
    if rw_faktor is not None:
        faktoren.append(rw_faktor)

    # Volatilitaets-Perzentil (2026-07-25, Baustein 2, Krypto-only wie
    # Liquiditaetszonen/Signal-Stabilitaet) - reiner Risiko-/Positionsgroessen-
    # Kontext, KEIN Richtungsurteil, deshalb nie "positiv".
    if atr_perzentil is not None:
        ist_hoch = (
            atr_perzentil_hoch_schwelle is not None and atr_perzentil >= atr_perzentil_hoch_schwelle
        )
        faktoren.append(Risikofaktor(
            f"Volatilitäts-Perzentil {atr_perzentil:.0f}", "negativ" if ist_hoch else "neutral",
            (
                f"{atr_perzentil:.0f}. Perzentil - "
                + ("ungewöhnlich hohe" if ist_hoch else "normale bis moderate")
                + " Volatilität für diesen Coin im Vergleich zur eigenen Historie"
                + (" - Positionsgröße/Stop entsprechend konservativer wählen." if ist_hoch else ".")
            ),
        ))

    return faktoren


DEFAULT_FAZIT_KONSISTENZ_SCHWELLE_NIEDRIG = 55.0
DEFAULT_FAZIT_KONSISTENZ_SCHWELLE_HOCH = 65.0


def _fazit_konsistenz_hinweis(
    folgen: str | None, confidence_pct: float | None,
    schwelle_niedrig: float = DEFAULT_FAZIT_KONSISTENZ_SCHWELLE_NIEDRIG,
    schwelle_hoch: float = DEFAULT_FAZIT_KONSISTENZ_SCHWELLE_HOCH,
) -> str | None:
    """Signal-Fazit (2026-07-25, siehe Signal.fazit_folgen-Docstring) - REIN
    DIAGNOSTISCH, aendert NIE `folgen`/`kurzfazit` selbst (siehe Memory
    feedback_llm_synthese_kein_deterministischer_override.md). Vergleicht das
    Fazit AUSSCHLIESSLICH mit der EIGENEN `confidence_pct` desselben Laufs -
    nicht mit einer separat berechneten Risikofaktoren-Anzahl, das waere
    bereits eine zweite, primitivere Bewertung und genau das, was hier
    vermieden werden soll. `mit_vorbehalt` wird NIE geflaggt - das ist
    bereits die explizite Zwischenposition."""
    if folgen is None or confidence_pct is None:
        return None
    if folgen == "ja" and confidence_pct < schwelle_niedrig:
        return "Fazit 'ja' bei vergleichsweise niedriger eigener Konfidenz - ggf. genauer prüfen."
    if folgen == "nein" and confidence_pct > schwelle_hoch:
        return "Fazit 'nein' trotz vergleichsweise hoher eigener Konfidenz - ggf. genauer prüfen."
    return None


def _rm1c_atr_untergrenze(
    sl_abstand_relativ: float | None,
    atr_value: float | None,
    current_price_usd: float | None,
    config: dict,
) -> tuple[bool, str | None]:
    """RM-1c (2026-08-02): volatilitaets-relative Untergrenze fuer den Stop-Abstand.

    Zweite Untergrenze NEBEN RM-1b (fester Prozentsatz) - es vetot, was die
    strengere der beiden reisst. Notwendig, weil eine feste Prozentgrenze
    blind fuer Volatilitaet ist: der ATR der beobachteten Symbole reicht von
    2,2% bis 26,9%, und bei 27% ATR sind die 2,5% aus RM-1b nur 0,09x ATR -
    dort haette das Netz kein Netz.

    Bewusst als gemeinsame Funktion fuer Buy- und Sell-Zweig: RM-1b wurde an
    beiden Stellen kopiert, was zwei Pfade ergibt, die bei einer Aenderung
    auseinanderlaufen koennen. Hier nicht.

    `atr_value` ist ein absoluter Preisabstand, `sl_abstand_relativ` ein
    Anteil - ohne Division durch den Kurs wuerden zwei Einheiten verglichen.

    Einordnung: `STOP_LOSS_ATR_MULTIPLE` (2.0) ist die Rechenkonvention fuer
    die Positionsgroesse in RM-5. RM-1c liegt mit 0,75x bewusst deutlich
    darunter - es ist eine Bodensicherung, keine Sollgroesse.
    """
    faktor = config["risiko"].get("sl_abstand_min_atr_faktor")
    if (
        sl_abstand_relativ is None
        or faktor is None
        or not atr_value
        or not current_price_usd
        or current_price_usd <= 0
    ):
        return False, None
    atr_relativ = atr_value / current_price_usd
    if atr_relativ <= 0 or sl_abstand_relativ >= atr_relativ * faktor:
        return False, None
    return True, (
        f"Stop-Loss-Abstand {sl_abstand_relativ * 100:.2f}% entspricht nur "
        f"{sl_abstand_relativ / atr_relativ:.2f}x ATR (Minimum {faktor}x ATR, RM-1c) - "
        f"bei einer Tagesschwankung von {atr_relativ * 100:.1f}% loest normales "
        f"Kursrauschen den Stop aus, bevor die These sich zeigen kann"
    )


def _rm1_exakt_und_positionszahl(
    basis_max_usd: float,
    sl_abstand_relativ: float | None,
    total_value_usd: float | None,
    config: dict,
) -> tuple[float, list[str]]:
    """Korrigiert die Positionsgroessen-Obergrenze mit dem TATSAECHLICHEN Stop
    (RM-1 exakt) und begrenzt sie zusaetzlich auf `Portfolio / N` (RM-1d).

    Hintergrund RM-1 exakt (2026-08-02): `pre_check()` laeuft VOR dem LLM-Call
    und muss den Stop-Abstand deshalb schaetzen - es nimmt `STOP_LOSS_ATR_
    MULTIPLE` (2,0) x ATR an. Der tatsaechlich vorgeschlagene Stop wurde danach
    nie dagegen geprueft. Messung an 222 Signalen: bei 18,5% liegt er WEITER
    als 2x ATR (Median 2,56x, Extremfall 8,27x). Da
    `max_position = Risikobudget / Stop-Abstand` gilt, ist die freigegebene
    Position dort zu gross und der Verlust uebersteigt das Risikobudget - im
    Median dieser Gruppe um 28%, im Extremfall um 313%. RM-1 ist laut
    Regelwerksmanual "unantastbar"; verletzt wurde sie nicht per Override,
    sondern durch eine Annahme, die niemand gegen das Ergebnis geprueft hat.

    NUR NACH UNTEN korrigierend, bewusst: bei den ueblichen 1,53x ATR waere die
    exakte Rechnung GROESSER als die Schaetzung und wuerde die Positionen um
    rund 30% aufblaehen. Mathematisch waere das RM-1-konform (engerer Stop =
    gleiches Risiko bei mehr Kapital), praktisch riskanter - bei einem Gap ueber
    den Stop hinaus skaliert der Verlust mit der Positionsgroesse, nicht mit dem
    geplanten Stop. RM-1 ist eine Obergrenze, kein Sollwert; sie zu
    unterschreiten ist immer regelkonform.

    Hintergrund RM-1d (Nutzer-Beobachtung 02.08.): dieselbe Formel von der
    anderen Seite - je enger der Stop, desto groesser die Position. Bei 1500 EUR
    Portfolio, 2% Risiko und 3% Stop sind das 1.000 EUR = 67% des Portfolios,
    also faktisch nur EIN Trade gleichzeitig. Der Deckel `Portfolio / N` wirkt
    nur, solange er strenger als RM-1 ist, und verschwindet bei wachsendem
    Portfolio von selbst (Variante C).

    Rueckgabe: (korrigierte Obergrenze, Liste von Erklaertexten fuer `checks`).
    """
    hinweise: list[str] = []
    ergebnis = basis_max_usd

    riskante_prozent = config["risiko"].get("risiko_pro_trade_prozent")
    if sl_abstand_relativ and sl_abstand_relativ > 0 and total_value_usd and riskante_prozent:
        risikobudget = total_value_usd * riskante_prozent / 100
        exakt = risikobudget / sl_abstand_relativ
        if exakt < ergebnis:
            hinweise.append(
                f"RM-1 exakt: Obergrenze {ergebnis:.2f} -> {exakt:.2f} USD "
                f"(tatsaechlicher Stop {sl_abstand_relativ * 100:.2f}% statt "
                f"{STOP_LOSS_ATR_MULTIPLE}x-ATR-Annahme)"
            )
            ergebnis = exakt

    ziel_n = config["risiko"].get("ziel_gleichzeitige_positionen")
    if total_value_usd and ziel_n and ziel_n > 0:
        pro_position = total_value_usd / ziel_n
        if pro_position < ergebnis:
            hinweise.append(
                f"RM-1d: Obergrenze {ergebnis:.2f} -> {pro_position:.2f} USD "
                f"(Kapital soll fuer {ziel_n} gleichzeitige Positionen reichen)"
            )
            ergebnis = pro_position

    return ergebnis, hinweise


def post_check(
    parsed: dict, pre_result: RiskPreCheckResult, regime_result, config: dict, confluence=None,
    retail_long_bias_extreme: bool | None = None, long_account_pct: float | None = None,
    liquiditaetszonen: dict | None = None,
    signal_stabilitaet: dict | None = None,
    atr_perzentil: float | None = None,
    richtungswende: dict | None = None,
    current_price: float | None = None,
    atr_value: float | None = None,
    dates=None,
    closes=None,
    richtungswende_atr_schwelle: float | None = None,
    filter_retail_konsens_top_gruende: bool = False,
    regime_persistenz_tage: int | None = None,
    min_konfidenz_override_prozent: float | None = None,
) -> dict:
    """Nimmt die bereits validierte (siehe agent/analyst.py) Groq-Antwort und erzwingt
    RM-1/-2/-4/-5, Mindest-Konfidenz (R-5.10) und CRV >= 2.0 (Z-2) noch einmal
    deterministisch. Klemmt zusaetzlich eine zu gross vorgeschlagene Positionsgroesse
    auf die RM-1/RM-2-Obergrenze (Korrektur, kein Veto). Gibt die (ggf. korrigierte)
    Antwort + Veto-Metadaten zurueck.

    `filter_retail_konsens_top_gruende` (2026-07-28, Punkt 4 der Fakten_
    Entscheidungsmappe.md-Prioritaetenliste, analog zu hebel_risk_gate.py)
    - Default False mit Absicht: nur agent/krypto/pipeline.py (Krypto-Spot,
    hat als einzige der 4 Spot-family-Pipelines echte Retail-Konten-Daten)
    setzt True. Aktien/Rohstoffe/Themen-ETF rufen post_check() unveraendert
    ohne diesen Parameter auf.

    `confluence` (2026-07-18, Nutzer-Fund am echten CAT-Fall: "Ergebnis ist
    durchgaengig eher schlecht" trotz 80% Konfidenz) optional - ohne sie faellt
    nur der neue Konflikt-Deckel unten weg, der Rest der Funktion bleibt
    unveraendert funktionsfaehig (P-10).

    `regime_persistenz_tage` (2026-07-30, optional wie bei hebel_pipeline.py)
    reichert nur den Regime-Konflikt/-Ausrichtung-Risikofaktor textuell an
    (siehe compute_risikofaktoren()) - `regime` selbst kommt bereits aus dem
    ohnehin vorhandenen `regime_result`-Parameter.

    `min_konfidenz_override_prozent` (2026-07-30, R-5.10-Nachtrag, siehe
    Memory project_llm_optimierung_abdeckung_pruefung + config.yaml::
    regime.min_konfidenz_prozent_krypto_spot_override): ersetzt, wenn
    gesetzt, den aus `config["regime"]["profile"]` gelesenen Schwellenwert
    komplett (nicht additiv) - fuer BEIDE Verwendungen (harter Konfidenz-
    Veto weiter unten UND die Konfidenz-skalierte Positionsgroessen-
    Obergrenze). Default `None` -> unveraendertes Verhalten fuer alle
    Aufrufer, die den Parameter nicht setzen (aktuell nur agent/krypto/
    pipeline.py/Krypto-Spot setzt ihn - Aktien/Rohstoffe/Themen-ETF bleiben
    auf der gemeinsamen `regime.profile`-Schwelle, siehe dortige
    Begruendung: Backtest-Evidenz bisher nur fuer Krypto-Spot ausreichend)."""
    result = dict(parsed)
    if filter_retail_konsens_top_gruende:
        result["top_gruende"] = filtere_retail_konsens_top_gruende(result.get("top_gruende"))
    risk_veto = False
    risk_veto_reason = None
    crv = None

    action = str(result.get("action", "")).upper()
    # Unveraendert festgehalten fuer compute_risikofaktoren() (siehe dort,
    # Nutzer-Fund 2026-07-20: Konklusion zeigte bei einem CRV-Veto nur den
    # Veto-Grund, obwohl der Groq-Aufruf laengst gelaufen war und Confluence/
    # Gegenszenario/Retail-Konsens/Konfidenz bereits vorlagen) - `action`
    # selbst wird unten bei jedem Veto auf "HALTEN" ueberschrieben.
    original_action = action
    # 2026-08-02: wird erst tief im Buy-/Sell-Zweig gesetzt (nur wenn alle sechs
    # Zonenwerte vorliegen), aber weiter unten im Positionsgroessen-Block
    # gelesen - ohne diese Initialisierung waere das bei fehlenden Zonen ein
    # NameError statt einer stillen Nicht-Anwendung.
    sl_abstand_relativ: float | None = None

    if action in _BUY_ACTIONS and not pre_result.kauf_erlaubt:
        risk_veto = True
        risk_veto_reason = pre_result.veto_reason
        action = "HALTEN"

    if action in _BUY_ACTIONS:
        # R-5.10 Mindestkonfidenz. Seit 2026-08-06 wahlweise STETIG statt in
        # vier festen Stufen - siehe regime.py::regime_score() fuer die volle
        # Begruendung, hier nur der Kern:
        #
        # Das diskrete Regime hat sich NIE geaendert (jedes Signal der Historie
        # traegt "baer"), weil es aus einer ODER-Bedingung stammt, in der
        # Fear & Greed allein genuegt. Der halb erholte Zustand - Kurs ueber der
        # EMA50 bei weiter aengstlicher Stimmung - bekam dieselbe harte
        # Schwelle wie ein voll baerischer Markt.
        #
        # Ein diskreter Zustand mit harten Stufen muss entweder traege sein
        # oder flackern; an der Geschwindigkeit zu drehen verschiebt nur, welche
        # der beiden Krankheiten man bekommt. Der stetige Score loest das auf.
        #
        # KALIBRIERT AUF IDENTITAET: der heutige Zustand ergibt 74,7 statt hart
        # 75,0. Da alle Konfidenzwerte des Systems ganzzahlig sind, filtert das
        # EXAKT gleich (nachgerechnet: 594 gegen 594 durchgelassene Signale).
        # Sichtbar wird der Unterschied erst in Lagen, die es heute nicht gibt.
        #
        # Der Override (min_konfidenz_override_prozent) behaelt Vorrang - er ist
        # eine bewusste manuelle Setzung und darf nicht stillschweigend durch
        # einen gerechneten Wert ersetzt werden.
        _stetig_aktiv = bool(config.get("regime", {}).get(
            "stetige_mindestkonfidenz_aktiv", False))
        _stetig_wert = getattr(regime_result, "min_konfidenz_stetig_wert", None)
        min_konfidenz = (
            min_konfidenz_override_prozent
            if min_konfidenz_override_prozent is not None
            else (_stetig_wert if (_stetig_aktiv and _stetig_wert is not None)
                  else config["regime"]["profile"].get(regime_result.regime, {}).get("min_konfidenz_prozent"))
        )
        _quelle = (
            "manueller Override" if min_konfidenz_override_prozent is not None
            else ("stetig aus Regime-Score" if (_stetig_aktiv and _stetig_wert is not None)
                  else f"Stufe '{regime_result.regime}'")
        )
        confidence = result.get("confidence_pct")
        if min_konfidenz is not None and confidence is not None and confidence < min_konfidenz:
            risk_veto = True
            reason = (f"Konfidenz {confidence}% unter Regime-Mindestschwelle "
                      f"{min_konfidenz}% ({_quelle}, R-5.10)")
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
            # RM-1b (2026-08-02): Enge-Stop-Veto VOR dem CRV-Check. Ein extremes
            # CRV entsteht fast immer durch einen zu engen Stop, nicht durch ein
            # ambitioniertes Ziel - liefe der CRV-Check zuerst, waere der Veto-
            # Grund spaeter nicht mehr als Stop-Problem erkennbar. Die Schwelle
            # ist gegen eine mechanische Basislinie aus 10.570 Tagesbalken
            # kalibriert (siehe config.yaml::risiko.sl_abstand_eng_schwelle_
            # relativ); sie wurde hebelfrei simuliert, gilt also unveraendert
            # fuer die Spot-Familie. Betroffenheit hier aktuell praktisch null
            # (Median-Stop 10,6%) - die Regel wirkt als Schutz, nicht als Filter.
            #
            # 2026-08-06 UNABHAENGIG BESTAETIGT: eine survivorship-freie
            # Neumessung an Hebel-Signalen (messe_stop_abstand_baender.py, kein
            # Aufloesungs-Filter, Basislinie je Band, Block-Bootstrap ueber
            # Symbole) findet den Bruch genau hier - unter 2% liegt der
            # Erwartungswert 0,53 R UNTER einem Zufallseinstieg mit demselben
            # Stop und ist das einzige Band, dessen Intervall die Null
            # ausschliesst; das Band 2,5-3% liegt +0,60 R darueber. Die
            # Schwelle 2,5% sitzt damit knapp oberhalb des Bruchs, also
            # richtig. KEINE Aenderung noetig - Verifikation, keine Luecke.
            sl_eng_schwelle = config["risiko"].get("sl_abstand_eng_schwelle_relativ")
            sl_abstand_relativ = abs(entry_mid - stop_von) / entry_mid if entry_mid > 0 else None
            rm1c_verletzt, rm1c_reason = _rm1c_atr_untergrenze(
                sl_abstand_relativ, atr_value, current_price, config
            )
            if (
                sl_abstand_relativ is not None
                and sl_eng_schwelle is not None
                and sl_abstand_relativ < sl_eng_schwelle
            ):
                risk_veto = True
                reason = (
                    f"Stop-Loss-Abstand {sl_abstand_relativ * 100:.2f}% unter Minimum "
                    f"{sl_eng_schwelle * 100:.1f}% (RM-1b, Enge-Stop-Veto): Stop liegt "
                    f"innerhalb der normalen Tagesschwankung und wird mit hoher "
                    f"Wahrscheinlichkeit durch Kursrauschen ausgeloest"
                )
                risk_veto_reason = f"{risk_veto_reason}; {reason}" if risk_veto_reason else reason
                action = "HALTEN"
            elif rm1c_verletzt:
                risk_veto = True
                reason = rm1c_reason
                risk_veto_reason = f"{risk_veto_reason}; {reason}" if risk_veto_reason else reason
                action = "HALTEN"
            elif crv is None or crv < CRV_MINIMUM:
                risk_veto = True
                reason = (
                    f"CRV {crv} unter Minimum {CRV_MINIMUM} (Z-2, konservativ: "
                    f"Entry-Mitte {entry_mid}, ungünstigster Stop {stop_von}, ungünstigstes Ziel {take_von})"
                )
                risk_veto_reason = f"{risk_veto_reason}; {reason}" if risk_veto_reason else reason
                action = "HALTEN"

    # Gespiegelte CRV-Pflicht fuer VERKAUFEN/TAUSCHEN (2026-07-27, siehe
    # _SELL_ACTIONS-Docstring oben) - identische Philosophie wie der _BUY_ACTIONS-
    # Block darueber, nur Zonen-Vorzeichen gedreht: bei einer bearischen These
    # liegt Take-Profit UNTER und Stop-Loss UEBER dem Entry (Regel 3/16 in
    # agent/krypto/analyst.py + 3 weiteren Spot-family-Analysten verlangen das
    # jetzt explizit vom LLM). Konservativ wird hier die JEWEILS NAEHERE Zonen-
    # Grenze (`_bis` statt `_von`) verwendet - der geringste angenommene Gewinn/
    # groesste angenommene Verlust, spiegelbildlich zur `_von`-Wahl bei KAUFEN.
    # `crv is None` (z.B. Zonen falsch orientiert, stop_bis <= entry_mid) faellt
    # automatisch unter denselben Veto-Zweig wie bei KAUFEN - keine eigene
    # Richtungspruefung noetig, die Mathematik erzwingt sie implizit.
    if action in _SELL_ACTIONS:
        entry = result.get("entry") or {}
        stop = result.get("stop_loss") or {}
        take = result.get("take_profit") or {}
        entry_von, entry_bis = entry.get("usd_von"), entry.get("usd_bis")
        stop_bis = stop.get("usd_bis")
        take_bis = take.get("usd_bis")
        if entry_von is not None and entry_bis is not None and stop_bis is not None and take_bis is not None:
            entry_mid = (entry_von + entry_bis) / 2
            crv = (entry_mid - take_bis) / (stop_bis - entry_mid) if stop_bis > entry_mid else None
            # RM-1b gespiegelt: bei bearischer These liegt der Stop UEBER dem
            # Entry, der Abstand berechnet sich entsprechend andersherum. Sonst
            # identisch zum _BUY_ACTIONS-Zweig oben.
            sl_eng_schwelle = config["risiko"].get("sl_abstand_eng_schwelle_relativ")
            sl_abstand_relativ = abs(stop_bis - entry_mid) / entry_mid if entry_mid > 0 else None
            rm1c_verletzt, rm1c_reason = _rm1c_atr_untergrenze(
                sl_abstand_relativ, atr_value, current_price, config
            )
            if (
                sl_abstand_relativ is not None
                and sl_eng_schwelle is not None
                and sl_abstand_relativ < sl_eng_schwelle
            ):
                risk_veto = True
                reason = (
                    f"Stop-Loss-Abstand {sl_abstand_relativ * 100:.2f}% unter Minimum "
                    f"{sl_eng_schwelle * 100:.1f}% (RM-1b, Enge-Stop-Veto, gespiegelt): Stop "
                    f"liegt innerhalb der normalen Tagesschwankung und wird mit hoher "
                    f"Wahrscheinlichkeit durch Kursrauschen ausgeloest"
                )
                risk_veto_reason = f"{risk_veto_reason}; {reason}" if risk_veto_reason else reason
                action = "HALTEN"
            elif rm1c_verletzt:
                risk_veto = True
                reason = rm1c_reason
                risk_veto_reason = f"{risk_veto_reason}; {reason}" if risk_veto_reason else reason
                action = "HALTEN"
            elif crv is None or crv < CRV_MINIMUM:
                risk_veto = True
                reason = (
                    f"CRV {crv} unter Minimum {CRV_MINIMUM} (Z-2, konservativ, gespiegelt: "
                    f"Entry-Mitte {entry_mid}, ungünstigster Stop {stop_bis}, ungünstigstes Ziel {take_bis})"
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
        # RM-1 exakt + RM-1d (2026-08-02): die Basis korrigieren, BEVOR die vier
        # Anteils-Deckel darauf rechnen - sonst wuerden Prozentsaetze auf eine
        # Obergrenze angewendet, die selbst schon falsch ist.
        rm1_korrektur_hinweise: list[str] = []
        if max_usd is not None:
            max_usd, rm1_korrektur_hinweise = _rm1_exakt_und_positionszahl(
                max_usd, sl_abstand_relativ, pre_result.total_value_usd, config
            )
            if max_eur is not None and pre_result.max_position_size_usd:
                # EUR proportional mitziehen, damit beide Waehrungen konsistent
                # bleiben (der FX-Kurs steckt bereits im urspruenglichen Paar).
                max_eur = max_eur * (max_usd / pre_result.max_position_size_usd)
        if max_usd is not None:
            # Vier Deckel-Kandidaten fuer die Positionsgroessen-Obergrenze
            # (Konfidenz-Skalierung, Gegenszenario, technischer Konflikt,
            # CRV-knapp) - bis 2026-07-24 wurden diese multiplikativ verkettet
            # (z.B. 0,5 x 0,5 x 0,6 x 0,6 = 9% der urspruenglichen Obergrenze,
            # wenn alle vier gleichzeitig griffen). Nutzer-Fund (Ueberstrenge-
            # Pruefung nach #333): die vier Faktoren sind inhaltlich NICHT
            # unabhaengig voneinander (gemischte Konfluenz und eine hohe
            # Bear-Wahrscheinlichkeit treten oft gemeinsam auf, da beide
            # Symptome derselben unklaren Marktlage sind) - eine Multiplikation
            # unterstellt aber unabhaengige Beweise und ueberschaetzt dadurch
            # systematisch, wie schlecht das Setup wirklich ist. Ausserdem war
            # die Risikorichtung verkehrt: Hebel (das strukturell risikoreichere
            # Instrument, Liquidationsgefahr) nutzte bereits die mildere
            # min()-ueber-Kandidaten-Logik (siehe hebel_risk_gate.py::
            # _hebel_deckel_kandidaten()), waehrend Spot (kein Hebel-/
            # Liquidationsrisiko) staerker verkettete. Jetzt identisches
            # Prinzip: min() ueber alle AUSGELOESTEN Kandidaten - der staerkste
            # einzelne Grund bindet, ueberlappende Warnsignale addieren sich
            # nicht mehr kuenstlich auf. Eigene Config-Werte bleiben getrennt
            # von Hebels eigenen (nur die Verknuepfungslogik wird angeglichen).
            sockel_anteil = config["risiko"].get("konfidenz_positionsgroesse_sockel_anteil")
            min_konfidenz = (
                min_konfidenz_override_prozent
                if min_konfidenz_override_prozent is not None
                else config["regime"]["profile"].get(regime_result.regime, {}).get("min_konfidenz_prozent")
            )
            confidence = result.get("confidence_pct")
            forecast = result.get("forecast") or {}
            gegenszenario_pct = (forecast.get("bear") or {}).get("probability_pct")
            gegenszenario_schwelle = config["risiko"].get("gegenszenario_wahrscheinlichkeit_schwelle_prozent")
            gegenszenario_deckel_anteil = config["risiko"].get("gegenszenario_positionsgroesse_deckel_anteil")
            konflikt_deckel_anteil = config["risiko"].get("technischer_konflikt_deckel_anteil")
            crv_knapp_schwelle_relativ = config["risiko"].get("crv_knapp_schwelle_relativ")
            crv_knapp_deckel_anteil = config["risiko"].get("crv_knapp_positionsgroesse_deckel_anteil")

            deckel_kandidaten: list[tuple[str, float]] = []

            if (
                sockel_anteil is not None
                and min_konfidenz is not None
                and confidence is not None
                and min_konfidenz < 100
            ):
                spanne = max(0.0, min(1.0, (confidence - min_konfidenz) / (100 - min_konfidenz)))
                scale = sockel_anteil + (1 - sockel_anteil) * spanne
                deckel_kandidaten.append((
                    f"Konfidenz-Skalierung ({confidence}%, Sockel {sockel_anteil * 100:.0f}% "
                    f"bei {min_konfidenz}% Konfidenz)",
                    max_usd * scale,
                ))

            if (
                gegenszenario_pct is not None
                and gegenszenario_schwelle is not None
                and gegenszenario_deckel_anteil is not None
                and gegenszenario_pct >= gegenszenario_schwelle
            ):
                deckel_kandidaten.append((
                    f"hohe Bear-Szenario-Wahrscheinlichkeit ({gegenszenario_pct:.0f}% >= "
                    f"Schwelle {gegenszenario_schwelle:.0f}%)",
                    max_usd * gegenszenario_deckel_anteil,
                ))

            if confluence is not None and confluence.overall_bias == "gemischt" and konflikt_deckel_anteil is not None:
                deckel_kandidaten.append((
                    "widerspruechliche technische Konfluenz (weder bullish noch bearish dominiert)",
                    max_usd * konflikt_deckel_anteil,
                ))

            if (
                crv is not None
                and crv_knapp_schwelle_relativ is not None
                and crv_knapp_deckel_anteil is not None
                and crv < CRV_MINIMUM * (1 + crv_knapp_schwelle_relativ)
            ):
                deckel_kandidaten.append((
                    f"CRV knapp am Minimum ({crv:.2f}, Minimum {CRV_MINIMUM:.1f})",
                    max_usd * crv_knapp_deckel_anteil,
                ))

            # Stufenlose CRV-Abstufung, NUR SPOT (2026-08-04).
            #
            # WOFUER. Bis heute hatte die CRV-Abstufung genau eine Stufe: unter
            # 2,0 Veto, 2,0-2,4 Deckel auf 60 %, ab 2,4 gar nichts mehr. Ein
            # CRV von 2,5 und eines von 6,0 bekamen dieselbe Groesse. Messung
            # vom 03.08. an 298 Spot-Signalen: das Gate entfernt bei Spot nur
            # 12 %, beisst also kaum; die Groesse ist dort der wirksame Hebel.
            # Mit 5-facher Spreizung stieg SQN von +0,63 auf +1,36, die Summe
            # von +9,8 auf +23,1 R, und der Rueckschlag SANK von 36,3 auf
            # 27,1 R - besseres Ergebnis bei kleinerem Risiko.
            #
            # BEIM HEBEL IST DIE ANTWORT GEGENLAEUFIG (Gate behalten, SQN
            # +3,25 gegen +1,25 fuer jede Groessen-Variante). Dieses Modul ist
            # das Spot-Modul; hebel_risk_gate.py hat seine eigene Logik und
            # bleibt bewusst unberuehrt.
            #
            # SICHER DURCH BAUFORM: als weiterer Kandidat im min() kann das
            # eine Position nur verkleinern, nie vergroessern. Eine
            # Ueberexposition ist damit ausgeschlossen, nicht bloss
            # unwahrscheinlich. Abschalten ueber spreizung = 1.0.
            crv_spreizung = config["risiko"].get("crv_positionsgroesse_spreizung")
            crv_voll_ab = config["risiko"].get("crv_positionsgroesse_voll_ab")
            if (
                crv is not None
                and crv_spreizung is not None
                and crv_voll_ab is not None
                and crv_spreizung > 1.0
                and crv_voll_ab > CRV_MINIMUM
            ):
                # Linear von 1/Spreizung bei CRV_MINIMUM auf 1,0 bei voll_ab.
                # Unterhalb des Minimums greift ohnehin das Veto; der clamp
                # dient dem Fall, dass das Veto spaeter einmal entfaellt.
                spanne = (crv - CRV_MINIMUM) / (crv_voll_ab - CRV_MINIMUM)
                spanne = max(0.0, min(1.0, spanne))
                sockel = 1.0 / crv_spreizung
                faktor = sockel + (1.0 - sockel) * spanne
                if faktor < 1.0:
                    deckel_kandidaten.append((
                        f"CRV-Abstufung ({crv:.2f}: {faktor * 100:.0f} % der "
                        f"Obergrenze, volle Groesse ab CRV {crv_voll_ab:.1f})",
                        max_usd * faktor,
                    ))

            # STILLGELEGTE DAEMPFER ZAEHLEN, WIRKEN ABER NICHT (13.08.2026).
            #
            # Nur zwei sind es, und beide beruhen auf einer Groesse, die wir als
            # wertlos GEMESSEN haben: die Konfidenz (r = +0,073, faktisch
            # konstant) und das Regime (ueber 1.022 Faelle konstant "baer"). Ein
            # Daempfer auf einer Konstanten ist ein verkleideter
            # Pauschalabschlag. Alles andere bleibt wirksam - insbesondere die
            # CRV-Abstufung, die an 298 Signalen gemessen wurde und den
            # Rueckschlag SENKT (siehe agent/daempfer.py).
            from agent import daempfer as DA
            _alle_kandidaten = list(deckel_kandidaten)
            deckel_kandidaten, _nur_gezaehlt = DA.teile(deckel_kandidaten)
            if deckel_kandidaten:
                bindender_grund, effective_max_usd = min(deckel_kandidaten, key=lambda paar: paar[1])
                scale_ratio = effective_max_usd / max_usd if max_usd else 1.0
                effective_max_eur = max_eur * scale_ratio if max_eur is not None else None
            else:
                bindender_grund = None
                effective_max_usd = max_usd
                effective_max_eur = max_eur

            if proposed_usd is not None and proposed_usd > effective_max_usd:
                fx = None
                proposed_eur = position_size.get("eur")
                if proposed_eur is not None and proposed_usd:
                    fx = proposed_eur / proposed_usd
                clamp_note = (
                    f"Von {proposed_usd:.2f} USD auf Risiko-Obergrenze {effective_max_usd:.2f} USD "
                    "gekürzt (RM-1/RM-2, deterministisch erzwungen)."
                )
                if bindender_grund:
                    clamp_note = f"{clamp_note} Bindender Grund: {bindender_grund}."
                # WAS STILLGELEGT WURDE, STEHT MIT DA. Ohne diese Zeile waere
                # die Stilllegung genau der unsichtbare Eingriff, gegen den
                # dieses Projekt sonst argumentiert - nur andersherum.
                _v = DA.vermerk(bindender_grund, _alle_kandidaten, _nur_gezaehlt)
                if _v:
                    clamp_note = f"{clamp_note} [{_v}]"
                if rm1_korrektur_hinweise:
                    # RM-1-exakt/RM-1d haben die Basis schon vor den Anteils-Deckeln
                    # gesenkt - ohne diesen Zusatz waere im Signal nicht erkennbar,
                    # warum die Obergrenze niedriger liegt als die RM-1-Rechnung
                    # aus dem Vorab-Check erwarten liesse.
                    clamp_note = f"{clamp_note} " + " ".join(rm1_korrektur_hinweise)
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
    # Selbst-gewaehltes-HALTEN-Flag (2026-07-31, mirror hebel_risk_gate.py::
    # post_check_hebel()-Docstring) - True NUR wenn `original_action` bereits
    # "HALTEN" war UND die finale `action` immer noch "HALTEN" ist UND kein
    # risk_veto gesetzt wurde. Spot hat keine Kontrathese-Uebersetzung wie
    # Hebel, das Prinzip bleibt aber aus Symmetriegruenden identisch.
    result["_ist_reines_llm_halten"] = (
        original_action == "HALTEN" and action == "HALTEN" and not risk_veto
    )
    # Rohe LLM-Aktion VOR jedem Veto (2026-07-31, Nachtrag - Kontrapruefung,
    # nur zur Symmetrie mit HebelSignal.original_action persistiert - Spot hat
    # keinen unbedingten Veto-Zweig, daher kein Diskriminator-Bug hier zu
    # beheben, siehe Signal.original_action-Docstring).
    result["_original_action"] = original_action
    # Cash-Veto (2026-07-18, Detailanalyse) - bewusst IMMER durchgereicht, nicht
    # nur bei einer tatsaechlichen Aktions-Ueberschreibung (siehe cash_veto-
    # Docstring in RiskPreCheckResult): das ist der tatsaechliche RM-4-Zustand
    # dieser Bewertung, unabhaengig davon, ob das Modell selbst schon
    # regelkonform HALTEN gesagt hat.
    result["_cash_veto"] = pre_result.cash_veto
    result["_cash_veto_reason"] = pre_result.cash_veto_reason

    # Risikofaktoren-Liste (2026-07-19, Abschnitt 3 der neuen E-Mail-/App-
    # Struktur) - dieselben Werte wie oben in der Positionsgroessen-Deckelung
    # verwendet, hier bewusst NEU aus `result`/`config` gelesen statt aus den
    # dortigen (tief verschachtelten) Lokalvariablen exportiert - der
    # bestehende, bereits verifizierte Deckel-Code bleibt dadurch unveraendert
    # (kein Regressionsrisiko).
    forecast = result.get("forecast") or {}
    gegenszenario_pct = (forecast.get("bear") or {}).get("probability_pct")
    risikofaktoren = compute_risikofaktoren(
        action=original_action,
        cash_veto=pre_result.cash_veto,
        cash_veto_reason=pre_result.cash_veto_reason,
        risk_veto=risk_veto,
        risk_veto_reason=risk_veto_reason,
        confidence_pct=result.get("confidence_pct"),
        crv=crv,
        confluence=confluence,
        gegenszenario_pct=gegenszenario_pct,
        gegenszenario_schwelle=config["risiko"].get("gegenszenario_wahrscheinlichkeit_schwelle_prozent"),
        crv_knapp_schwelle_relativ=config["risiko"].get("crv_knapp_schwelle_relativ"),
        retail_long_bias_extreme=retail_long_bias_extreme,
        long_account_pct=long_account_pct,
        liquiditaetszonen=liquiditaetszonen,
        signal_stabilitaet=signal_stabilitaet,
        atr_perzentil=atr_perzentil,
        atr_perzentil_hoch_schwelle=config.get("volatilitaets_perzentil", {}).get("hoch_schwelle_perzentil"),
        richtungswende=richtungswende,
        current_price=current_price,
        atr_value=atr_value,
        dates=dates,
        closes=closes,
        richtungswende_atr_schwelle=(
            richtungswende_atr_schwelle
            if richtungswende_atr_schwelle is not None
            else config.get("signal_stabilitaet", {}).get("richtungswende_atr_schwelle_relativ")
        ),
        regime=regime_result.regime if regime_result is not None else None,
        regime_persistenz_tage=regime_persistenz_tage,
    )
    result["_risikofaktoren"] = [
        {"name": f.name, "bewertung": f.bewertung, "begruendung": f.begruendung, "ist_kontext": f.ist_kontext}
        for f in risikofaktoren
    ]

    # Signal-Fazit Konsistenz-Hinweis (2026-07-25) - rein diagnostisch, siehe
    # _fazit_konsistenz_hinweis()-Docstring.
    eigene_einschaetzung = result.get("eigene_einschaetzung") or {}
    fazit_cfg = config.get("signal_fazit", {})
    result["_fazit_konsistenz_hinweis"] = _fazit_konsistenz_hinweis(
        eigene_einschaetzung.get("folgen"),
        result.get("confidence_pct"),
        fazit_cfg.get("konsistenz_schwelle_niedrig", DEFAULT_FAZIT_KONSISTENZ_SCHWELLE_NIEDRIG),
        fazit_cfg.get("konsistenz_schwelle_hoch", DEFAULT_FAZIT_KONSISTENZ_SCHWELLE_HOCH),
    )
    return result
