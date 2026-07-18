"""R-5.1 Marktregime-Bestimmung (Spezifikation Kap. 5/14) - NUR die regelbasierte
Basis (RG-1a). KI-Override (RG-1b) ist bewusst nicht Teil dieser Slice. Manueller
Override (RG-8) wird respektiert (RG-9: Vorrang vor der regelbasierten Basis), harte
Limits (RG-6, Stop-Loss/Risiko-pro-Trade/Drawdown-Notbremse) sind davon unberuehrt -
die werden ausschliesslich in agent/risk_gate.py durchgesetzt, nie hier.

Bewusst einfache Heuristik (dokumentiert, nicht die volle RG-1..RG-11-Feinheit):
EMA-Ordnung fuer den BTC-Trend, BTC-Dominanz-Trend aus macro_snapshot-Historie,
Fear&Greed-Einstufung direkt von alternative.me uebernommen (keine eigene
Schwellenwert-Erfindung)."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from api.onchain import OnChainReading
from database.models import MacroSnapshot
from indicators.calculations import (
    BTC_CYCLE_BOTTOM_DEVIATIONS_STD,
    ETH_CYCLE_BOTTOM_DEVIATIONS_STD,
    BtcLogRegressionRisk,
    TechnicalSnapshot,
    latest_value,
)

REGIME_STATES = ("krise_extrem", "baer", "seitwaerts", "bulle", "euphorie_extrem")

# RG-2 BTC-Matrix (Spezifikation Kap. 14): ordnet zusammen mit dem BTC-Trend die
# BTC-Dominanz-Richtung ein, um Alt-Signale (nicht Core-Assets) im richtigen Kontext
# zu lesen - z.B. ist ein bullischer Alt-Ausbruch in "btc_season" meist eine Falle.
BTC_MATRIX = {
    ("aufwaerts", "steigend"): (
        "btc_season",
        "BTC steigt, Dominanz steigt (BTC-Season): Kapital rotiert eher in BTC als in "
        "Alts - Alt-Ausbrueche mit Skepsis behandeln, viele erweisen sich als Fallen.",
    ),
    ("aufwaerts", "fallend"): (
        "altseason",
        "BTC steigt, Dominanz faellt (Altseason-Tendenz): Kapital rotiert von BTC in "
        "Alts - Alt-Ausbrueche sind eher vertrauenswuerdig.",
    ),
    ("abwaerts", "steigend"): (
        "baer_flucht",
        "BTC faellt, Dominanz steigt (klassischer Baer/Flucht in BTC): Alt-Ausbrueche "
        "meist Fallen - erhoehte Vorsicht bei Alt-Kaufsignalen.",
    ),
    ("abwaerts", "fallend"): (
        "unklar_defensiv",
        "BTC faellt, Dominanz faellt gleichzeitig (unueblich, ggf. breiter Risk-Off "
        "inkl. BTC-Abfluss): uneindeutige Lage, tendenziell defensiv einordnen.",
    ),
}


# Liquiditaets-Regime (Nutzungs-Diskussion 2026-07-08, siehe
# project-offene-agent-diskussionspunkte Abschnitt 6): kombiniert den Trend der
# globalen M2-Geldmenge mit der Fed-Funds-Rate-Richtung. Bewusst als EIGENE
# Dimension neben `regime` (nicht eingemischt) - beantwortet eine andere Frage
# ("wird die Liquiditaet groesser oder kleiner") als das bestehende Bär/Bulle-Regime
# ("wie verhaelt sich der Markt gerade"). Schwellenwerte sind eine bewusste,
# dokumentierte Modellierungsentscheidung, keine Standardwerte aus der Literatur.
LIQUIDITY_M2_TREND_THRESHOLD_PCT = 1.0  # Veraenderung ueber ~6 Monate, siehe agent/pipeline.py::_fetch_liquidity_context
LIQUIDITY_FED_FUNDS_THRESHOLD_PP = 0.1  # Prozentpunkte

# Zyklus-Risiko (Nutzungs-Diskussion, Schritt 2, 2026-07-08): BTC-Log-Regression-Risk
# (indicators/calculations.py) als primaeres, quantifiziertes Regime-Feld; MVRV/NUPL
# (api/onchain.py) bewusst NICHT als eigenes Regime-Feld, sondern nur als Cross-Check-
# Text daneben - beide Modelle beantworten dieselbe Frage ("wie weit ist BTC von einem
# Bewertungsextrem entfernt"), ein zweites Regime-Feld wuerde dasselbe Signal doppelt
# gewichten (Fear&Greed zaehlt es implizit schon mit).
#
# MVRV-Baender: eigene, dokumentierte Einteilung (keine Nachbildung einer
# kommerziellen Formel) - grobe Orientierung an haeufig zitierten historischen
# MVRV-Zonen (< 1 = Kapitulation, > 3.5 = fruehere Zyklus-Top-Naehe), NICHT
# wissenschaftlich hergeleitet oder statistisch optimiert.
MVRV_BANDS = (
    (1.0, "unterbewertet (historisch: Kapitulationszone)"),
    (2.0, "neutral/moderat"),
    (3.5, "erhöht"),
    (float("inf"), "historisch extrem (Nähe an früheren Zyklus-Toppen)"),
)

# VIX-Baender (2026-07-18): branchenuebliche CBOE-Praktiker-Konvention (nicht
# projekteigen erfunden wie z.B. die MVRV-Baender oben) - <20 gilt gemeinhin als
# ruhige Marktphase, 20-30 als erhoehte Unsicherheit, 30-40 als deutlicher Stress,
# >40 als Krisen-/Panik-Niveau (historisch nur in echten Crash-Phasen erreicht,
# z.B. Finanzkrise 2008, Covid-Crash 2020).
VIX_BANDS = (
    (20.0, "ruhig"),
    (30.0, "erhöht"),
    (40.0, "gestresst"),
    (float("inf"), "krise"),
)


@dataclass
class RegimeResult:
    regime: str
    source: str  # "regelbasiert" | "manuell"
    reason: str
    btc_trend_label: str
    dominance_trend_label: str
    fear_greed_value: int | None
    fear_greed_label: str | None
    btc_matrix_state: str
    btc_matrix_beschreibung: str
    liquiditaets_regime: str
    liquiditaets_regime_begruendung: str
    zyklus_risiko: float | None  # 0-1, siehe BtcLogRegressionRisk.risk
    zyklus_risiko_begruendung: str
    # Boden-Zielzone (AZ-4 Baustein 2, 2026-07-12) - siehe _boden_zielzone() unten.
    # In USD, None wenn die zugrundeliegende Regression nicht berechnet werden konnte
    # (P-10, kein Fallback-Wert).
    btc_boden_zielzone_von: float | None
    btc_boden_zielzone_bis: float | None
    btc_boden_zielzone_begruendung: str
    eth_boden_zielzone_von: float | None
    eth_boden_zielzone_bis: float | None
    eth_boden_zielzone_begruendung: str
    # Aktien-Baermarkt-Overlay: None = Datenlage unbekannt (Abruf fehlgeschlagen),
    # sonst bool ob mindestens einer der beiden Indizes ueber der config.yaml-
    # Schwelle liegt (Verknuepfung "entweder", Nutzer-Entscheidung 2026-07-12).
    equities_baermarkt_aktiv: bool | None
    equities_baermarkt_begruendung: str
    # VIX-Fruehindikator (2026-07-18): im Gegensatz zu equities_baermarkt_aktiv
    # (nachlaufender Drawdown-Schwellenwert) ein VORLAUFENDES Optionsmarkt-
    # Stimmungssignal - kann schon ausschlagen, bevor/ohne dass ein echter
    # Drawdown eintritt. Rein beschreibender Fakt (kein deterministischer
    # Deckel, Nutzer-Entscheidung 2026-07-18), siehe _vix_label() unten.
    vix_wert: float | None
    vix_label: str


def _btc_change_pct(btc_closes: np.ndarray, days: int = 30) -> float | None:
    if len(btc_closes) < days + 1:
        return None
    return float((btc_closes[-1] - btc_closes[-days - 1]) / btc_closes[-days - 1] * 100)


def _dominance_direction(macro_history: list[MacroSnapshot]) -> tuple[str, float | None, str | None]:
    """Gibt (richtung, delta, seit_datum) zurueck - richtung in
    {"steigend","fallend","gleichbleibend","unbekannt"}. Einzige Quelle fuer den
    Schwellenwert (0.5 Prozentpunkte), sowohl fuer das Anzeige-Label als auch fuer
    die BTC-Matrix genutzt."""
    with_dominance = [m for m in macro_history if m.btc_dominance_pct is not None]
    if len(with_dominance) < 2:
        return "unbekannt", None, None
    delta = with_dominance[-1].btc_dominance_pct - with_dominance[0].btc_dominance_pct
    since = with_dominance[0].date
    if delta > 0.5:
        return "steigend", delta, since
    if delta < -0.5:
        return "fallend", delta, since
    return "gleichbleibend", delta, since


def _dominance_trend_label(macro_history: list[MacroSnapshot]) -> str:
    richtung, delta, since = _dominance_direction(macro_history)
    if richtung == "unbekannt":
        return "nicht verfügbar (nur 1 Messpunkt)"
    return f"{richtung} ({delta:+.2f} Prozentpunkte seit {since})"


def _pct_trend(values: list[float], threshold_pct: float = LIQUIDITY_M2_TREND_THRESHOLD_PCT) -> str:
    if len(values) < 2 or values[0] == 0:
        return "unbekannt"
    change_pct = (values[-1] - values[0]) / values[0] * 100
    if change_pct > threshold_pct:
        return "steigend"
    if change_pct < -threshold_pct:
        return "fallend"
    return "gleichbleibend"


def _fed_funds_direction(values: list[float], threshold_pp: float = LIQUIDITY_FED_FUNDS_THRESHOLD_PP) -> str:
    if len(values) < 2:
        return "unbekannt"
    delta = values[-1] - values[0]
    if delta > threshold_pp:
        return "straffung"
    if delta < -threshold_pp:
        return "lockerung"
    return "halten"


def _m2_global_trend(
    m2_us_history: list[float], m2_eurozone_history: list[float], m2_china_history: list[float]
) -> tuple[str, str]:
    """Mehrheitsentscheid ueber die verfuegbaren Regionen (Japan bewusst aussen vor -
    keine Historien-Quelle, siehe api/macro.py::get_japan_m2). Prozent-Veraenderung
    statt absoluter Summen: die drei Serien liegen in unterschiedlichen Waehrungen/
    Einheiten vor (USD Mrd. / EUR Mio. / CNY hundert Mio.) - eine Wachstumsrate ist
    waehrungsneutral vergleichbar, eine direkte Summe waere es nicht."""
    trends = {
        "USA": _pct_trend(m2_us_history),
        "Eurozone": _pct_trend(m2_eurozone_history),
        "China": _pct_trend(m2_china_history),
    }
    known = {region: t for region, t in trends.items() if t != "unbekannt"}
    if not known:
        return "unbekannt", "keine ausreichende M2-Historie fuer USA/Eurozone/China verfuegbar"
    detail = ", ".join(f"{region}: {t}" for region, t in known.items())
    steigend = sum(1 for t in known.values() if t == "steigend")
    fallend = sum(1 for t in known.values() if t == "fallend")
    if steigend > fallend:
        return "steigend", detail
    if fallend > steigend:
        return "fallend", detail
    return "gemischt", detail


def _liquidity_regime(m2_trend: str, fed_direction: str, m2_detail: str) -> tuple[str, str]:
    if m2_trend == "unbekannt" or fed_direction == "unbekannt":
        return "unbekannt", f"zu wenig Historie ({m2_detail}; Fed-Funds-Richtung: {fed_direction})"
    if m2_trend == "gemischt":
        return "gemischt", f"regionale M2-Trends uneinheitlich, keine Mehrheit ({m2_detail})"
    if m2_trend == "steigend" and fed_direction in ("lockerung", "halten"):
        return (
            "expansiv",
            f"globales M2 {m2_trend} ({m2_detail}), Fed {fed_direction} - Liquidität fließt tendenziell eher in "
            "Risiko-Assets.",
        )
    if m2_trend == "fallend" and fed_direction in ("straffung", "halten"):
        return (
            "restriktiv",
            f"globales M2 {m2_trend} ({m2_detail}), Fed {fed_direction} - Liquidität wird tendenziell eher knapper.",
        )
    return (
        "widerspruechlich",
        f"globales M2 {m2_trend} ({m2_detail}), aber Fed {fed_direction} - gegenläufige Signale, keine klare "
        "Einordnung möglich.",
    )


def _vix_label(vix_wert: float | None) -> str:
    if vix_wert is None:
        return "nicht verfügbar"
    for threshold, label in VIX_BANDS:
        if vix_wert < threshold:
            return label
    return VIX_BANDS[-1][1]


def _mvrv_band(mvrv: float) -> str:
    for threshold, label in MVRV_BANDS:
        if mvrv < threshold:
            return label
    return MVRV_BANDS[-1][1]


def _zyklus_risiko(
    log_regression_risk: BtcLogRegressionRisk | None, onchain: OnChainReading | None
) -> tuple[float | None, str]:
    if log_regression_risk is None:
        return None, "BTC-Log-Regression-Risk nicht verfügbar (Historien-Abruf fehlgeschlagen)."

    parts = [
        f"BTC-Log-Regression-Risk: {log_regression_risk.risk:.2f} "
        f"(Abweichung {log_regression_risk.deviation_std:+.2f} Standardabweichungen von der "
        "langfristigen Trendlinie)."
    ]
    if onchain is None:
        parts.append("MVRV/NUPL nicht verfügbar für einen Cross-Check.")
    else:
        band = _mvrv_band(onchain.mvrv)
        parts.append(f"MVRV: {onchain.mvrv:.2f} ({band}), NUPL: {onchain.nupl:.2f}.")
        risk_high, risk_low = log_regression_risk.risk >= 0.6, log_regression_risk.risk <= 0.4
        mvrv_high, mvrv_low = onchain.mvrv >= 2.0, onchain.mvrv < 1.0
        if (risk_high and mvrv_high) or (risk_low and mvrv_low):
            parts.append("Beide Modelle deuten in dieselbe Richtung (Cross-Check bestätigt).")
        elif (risk_high and mvrv_low) or (risk_low and mvrv_high):
            parts.append("Modelle weichen voneinander ab - keine eindeutige Einordnung, mit Vorsicht behandeln.")

    return log_regression_risk.risk, " ".join(parts)


def _boden_zielzone(
    log_regression_risk: BtcLogRegressionRisk | None,
    deviation_band: tuple[float, float],
    daempfer_staerke: float,
    equities_baermarkt_aktiv: bool | None,
    overlay_shift_std: float,
    asset_label: str,
    vix_wert: float | None = None,
    vix_label: str = "nicht verfügbar",
) -> tuple[float | None, float | None, str]:
    """Boden-Zielzone (AZ-4 Baustein 2, 2026-07-12) - projiziert ein historisches
    Zyklus-Tief-Abweichungsband (siehe indicators/calculations.py::
    BTC_CYCLE_BOTTOM_DEVIATIONS_STD/ETH_CYCLE_BOTTOM_DEVIATIONS_STD) auf die aktuelle
    Log-Regressionslinie. Wahrscheinlichkeits-Zone, KEIN hartes Kursziel (Z-4-
    Transparenz) - `asset_label` sorgt bei ETH fuer einen sichtbaren
    Niedrig-Konfidenz-Hinweis (nur 2 statt 3 historische Vergleichspunkte, siehe
    Modul-Konstante).

    `daempfer_staerke` (Reifegrad-Daempfer, config.yaml boden_zielzone.
    reifegrad_daempfer_staerke): zieht beide Bandkanten um diesen Anteil Richtung 0
    (die Regressionslinie) - mit wachsender Marktkapitalisierung werden Korrekturen
    historisch tendenziell milder, ein starres Band aus frueheren, kleineren Zyklen
    waere sonst zu tief angesetzt.

    `equities_baermarkt_aktiv`/`overlay_shift_std`: wenn Aktien (S&P 500/Nasdaq)
    selbst im Baermarkt sind, wirkt das dem Reifegrad-Daempfer entgegen - die untere
    (negativere) Bandkante wird zusaetzlich vertieft, weil ein gemeinsamer
    Liquiditaetsentzug BTC/ETH zusaetzlich unter die reine Krypto-Zyklus-Zone
    druecken kann (Nutzer-Punkt).

    `vix_wert`/`vix_label` (2026-07-18, Nachtrag nach Detailanalyse - siehe
    Regelwerksmanual): ZWEITER, unabhaengiger ODER-Trigger fuer denselben Overlay-
    Effekt. Recherche gegen die 3 echten BTC-Zyklus-Boeden (2015/2018/2022) zeigte:
    equities_baermarkt_aktiv allein haette nur 1 von 3 mal ausgeloest (2015 und 2018
    waren Aktien noch NICHT im 20%-Drawdown, obwohl BTC schon -61%/-83% stand).
    VIX "gestresst"/"krise" (Baender siehe VIX_BANDS oben, branchenueblich, NICHT aus
    diesen 3 Punkten gefittet - explizit KEIN Overfitting) haette 2018 zusaetzlich
    erfasst (VIX-Peak 36,1 wenige Tage um den Boden) - realistische Trefferquote
    dadurch von 1/3 auf ~2/3, 2015 bleibt weiterhin unerreicht (VIX nur ~21,5). Bei
    n=3 historischen Vergleichspunkten bewusst mit Vorsicht zu behandeln, aber ein
    echter, nicht erfundener Fortschritt. Nutzt DENSELBEN overlay_shift_std wie der
    Aktien-Pfad (kein zweiter, unbelegbar feinjustierter Parameter). Beeinflusst NUR
    diesen Overlay - `regime.aktien_baermarkt`/`equities_baermarkt_aktiv` als
    eigenstaendiger Fakt (von allen 4 Analysten konsumiert) bleibt unveraendert eng
    definiert ("Aktienindex im Drawdown"), um dessen etablierte Bedeutung nicht zu
    verwaessern.

    Gibt (zone_von, zone_bis, begruendung) zurueck - (None, None, ...) wenn die
    zugrundeliegende Regression nicht verfuegbar ist (P-10, kein Fallback-Wert)."""
    if log_regression_risk is None:
        return None, None, f"{asset_label}-Log-Regression nicht verfügbar (Historien-Abruf fehlgeschlagen)."

    vix_ueberlagerung_aktiv = vix_label in ("gestresst", "krise")
    overlay_trigger = bool(equities_baermarkt_aktiv) or vix_ueberlagerung_aktiv

    raw_edges = list(deviation_band)
    effective_edges = [edge * (1 - daempfer_staerke) for edge in raw_edges]
    overlay_wirkte = False
    if overlay_trigger:
        deepest_idx = effective_edges.index(min(effective_edges))
        effective_edges[deepest_idx] -= overlay_shift_std
        overlay_wirkte = True

    prices = [
        log_regression_risk.predicted_price * 10 ** (edge * log_regression_risk.residual_std)
        for edge in effective_edges
    ]
    zone_von, zone_bis = min(prices), max(prices)

    parts = [
        f"{asset_label}-Boden-Zielzone: {zone_von:,.0f}-{zone_bis:,.0f} $ "
        f"(historisches Zyklus-Tief-Band {min(raw_edges):+.2f} bis {max(raw_edges):+.2f} Std., "
        f"Reifegrad-gedaempft auf {min(effective_edges):+.2f} bis {max(effective_edges):+.2f} Std.)."
    ]
    if overlay_wirkte:
        ausloeser = []
        if equities_baermarkt_aktiv:
            ausloeser.append("Aktien-Bärenmarkt (S&P500/Nasdaq-Drawdown)")
        if vix_ueberlagerung_aktiv:
            vix_text = f"VIX {vix_label}" + (f" ({vix_wert:.1f})" if vix_wert is not None else "")
            ausloeser.append(vix_text)
        parts.append(
            f"Overlay aktiv ({' + '.join(ausloeser)}): untere Bandkante um zusätzlich "
            f"{overlay_shift_std:.2f} Std. vertieft (gemeinsamer Liquiditätsentzug/Marktstress)."
        )
    elif equities_baermarkt_aktiv is None and vix_wert is None:
        parts.append("Aktien-Bärenmarkt-Status UND VIX nicht verfügbar - Overlay konnte nicht geprüft werden.")
    elif equities_baermarkt_aktiv is None:
        parts.append("Aktien-Bärenmarkt-Status nicht verfügbar - nur VIX-Pfad konnte geprüft werden (nicht ausgelöst).")
    if asset_label == "ETH":
        parts.append(
            "Niedrige Konfidenz: nur 2 historische ETH-Zyklus-Tiefpunkte verfügbar (statt 3 bei BTC), "
            "die Werte liegen zudem weit auseinander - deutlich unsicherere Schätzung als bei BTC."
        )

    return zone_von, zone_bis, " ".join(parts)


def determine_regime(
    btc_closes: np.ndarray,
    btc_snapshot: TechnicalSnapshot,
    macro_history: list[MacroSnapshot],
    manual_override: str,
    fed_funds_history: list[float] | None = None,
    m2_us_history: list[float] | None = None,
    m2_eurozone_history: list[float] | None = None,
    m2_china_history: list[float] | None = None,
    btc_log_regression_risk: BtcLogRegressionRisk | None = None,
    btc_onchain_reading: OnChainReading | None = None,
    eth_log_regression_risk: BtcLogRegressionRisk | None = None,
    boden_zielzone_daempfer_staerke: float = 0.0,
    equities_baermarkt_aktiv: bool | None = None,
    equities_baermarkt_begruendung: str = "Aktien-Bärenmarkt-Status nicht verfügbar.",
    boden_zielzone_overlay_shift_std: float = 0.0,
    vix_wert: float | None = None,
) -> RegimeResult:
    """Boden-Zielzone-Parameter (AZ-4 Baustein 2, 2026-07-12): bewusst als bereits
    aufgeloeste Werte uebergeben (wie `manual_override`) statt hier config.yaml zu
    lesen - regime.py bleibt komplett config-frei, der Schwellenwert-Vergleich fuer
    `equities_baermarkt_aktiv` passiert in pipeline.py."""
    vix_label = _vix_label(vix_wert)
    m2_trend, m2_detail = _m2_global_trend(
        m2_us_history or [], m2_eurozone_history or [], m2_china_history or []
    )
    fed_direction = _fed_funds_direction(fed_funds_history or [])
    liquiditaets_regime, liquiditaets_regime_begruendung = _liquidity_regime(m2_trend, fed_direction, m2_detail)
    zyklus_risiko, zyklus_risiko_begruendung = _zyklus_risiko(btc_log_regression_risk, btc_onchain_reading)
    btc_zielzone_von, btc_zielzone_bis, btc_zielzone_begruendung = _boden_zielzone(
        btc_log_regression_risk, BTC_CYCLE_BOTTOM_DEVIATIONS_STD, boden_zielzone_daempfer_staerke,
        equities_baermarkt_aktiv, boden_zielzone_overlay_shift_std, "BTC",
        vix_wert=vix_wert, vix_label=vix_label,
    )
    eth_zielzone_von, eth_zielzone_bis, eth_zielzone_begruendung = _boden_zielzone(
        eth_log_regression_risk, ETH_CYCLE_BOTTOM_DEVIATIONS_STD, boden_zielzone_daempfer_staerke,
        equities_baermarkt_aktiv, boden_zielzone_overlay_shift_std, "ETH",
        vix_wert=vix_wert, vix_label=vix_label,
    )
    ema20 = latest_value(btc_snapshot.ema[20])
    ema50 = latest_value(btc_snapshot.ema[50])
    ema200 = latest_value(btc_snapshot.ema[200])
    change_30d = _btc_change_pct(btc_closes)

    if ema20 is not None and ema50 is not None and ema200 is not None:
        if ema20 > ema50 > ema200:
            btc_direction = "aufwaerts"
            btc_trend_label = "aufwärts (EMA20 > EMA50 > EMA200)"
        elif ema20 < ema50 < ema200:
            btc_direction = "abwaerts"
            btc_trend_label = "abwärts (EMA20 < EMA50 < EMA200)"
        else:
            btc_direction = "gemischt"
            btc_trend_label = "gemischt"
    else:
        btc_direction = "unbekannt"
        btc_trend_label = "nicht verfügbar (zu wenig Historie)"

    dominance_direction, _, _ = _dominance_direction(macro_history)
    dominance_trend_label = _dominance_trend_label(macro_history)
    btc_matrix_state, btc_matrix_beschreibung = BTC_MATRIX.get(
        (btc_direction, dominance_direction),
        (
            "nicht_verfuegbar",
            "BTC-Trend und/oder Dominanz-Trend nicht eindeutig genug fuer eine "
            "Matrix-Einordnung (z.B. gemischter Trend oder nur ein Dominanz-Messpunkt).",
        ),
    )

    latest_macro = macro_history[-1] if macro_history else None
    fgi_value = latest_macro.fear_greed_value if latest_macro else None
    fgi_label = latest_macro.fear_greed_label if latest_macro else None

    below_ema200 = bool(len(btc_closes)) and ema200 is not None and btc_closes[-1] < ema200
    above_all = ema20 is not None and ema50 is not None and ema200 is not None and ema20 > ema50 > ema200

    if fgi_label == "Extreme Fear" and below_ema200 and change_30d is not None and change_30d < -20:
        regime = "krise_extrem"
        reason = "Extreme Fear + BTC unter EMA200 + 30-Tage-Rückgang > 20%"
    elif fgi_label == "Extreme Greed" and above_all and change_30d is not None and change_30d > 20:
        regime = "euphorie_extrem"
        reason = "Extreme Greed + BTC über EMA20>EMA50>EMA200 + 30-Tage-Anstieg > 20%"
    elif (ema50 is not None and ema200 is not None and btc_closes[-1] < ema50) or fgi_label in (
        "Fear", "Extreme Fear",
    ):
        regime = "baer"
        reason = "BTC unter EMA50 und/oder Fear&Greed im Angst-Bereich"
    elif (
        ema50 is not None and ema200 is not None and btc_closes[-1] > ema50 > ema200
    ) and fgi_label in ("Greed", "Extreme Greed"):
        regime = "bulle"
        reason = "BTC über EMA50>EMA200 und Fear&Greed im Gier-Bereich"
    else:
        regime = "seitwaerts"
        reason = "keine der Bär-/Bulle-/Extrem-Bedingungen eindeutig erfüllt (Fallback)"

    if manual_override and manual_override != "none":
        return RegimeResult(
            regime=manual_override,
            source="manuell",
            reason=f"Manueller Override ({manual_override}) - regelbasiert wäre '{regime}' gewesen: {reason}",
            btc_trend_label=btc_trend_label,
            dominance_trend_label=dominance_trend_label,
            fear_greed_value=fgi_value,
            fear_greed_label=fgi_label,
            btc_matrix_state=btc_matrix_state,
            btc_matrix_beschreibung=btc_matrix_beschreibung,
            liquiditaets_regime=liquiditaets_regime,
            liquiditaets_regime_begruendung=liquiditaets_regime_begruendung,
            zyklus_risiko=zyklus_risiko,
            zyklus_risiko_begruendung=zyklus_risiko_begruendung,
            btc_boden_zielzone_von=btc_zielzone_von,
            btc_boden_zielzone_bis=btc_zielzone_bis,
            btc_boden_zielzone_begruendung=btc_zielzone_begruendung,
            eth_boden_zielzone_von=eth_zielzone_von,
            eth_boden_zielzone_bis=eth_zielzone_bis,
            eth_boden_zielzone_begruendung=eth_zielzone_begruendung,
            equities_baermarkt_aktiv=equities_baermarkt_aktiv,
            equities_baermarkt_begruendung=equities_baermarkt_begruendung,
            vix_wert=vix_wert,
            vix_label=vix_label,
        )

    return RegimeResult(
        regime=regime,
        source="regelbasiert",
        reason=reason,
        btc_trend_label=btc_trend_label,
        dominance_trend_label=dominance_trend_label,
        fear_greed_value=fgi_value,
        fear_greed_label=fgi_label,
        liquiditaets_regime=liquiditaets_regime,
        liquiditaets_regime_begruendung=liquiditaets_regime_begruendung,
        zyklus_risiko=zyklus_risiko,
        zyklus_risiko_begruendung=zyklus_risiko_begruendung,
        btc_matrix_state=btc_matrix_state,
        btc_matrix_beschreibung=btc_matrix_beschreibung,
        btc_boden_zielzone_von=btc_zielzone_von,
        btc_boden_zielzone_bis=btc_zielzone_bis,
        btc_boden_zielzone_begruendung=btc_zielzone_begruendung,
        eth_boden_zielzone_von=eth_zielzone_von,
        eth_boden_zielzone_bis=eth_zielzone_bis,
        eth_boden_zielzone_begruendung=eth_zielzone_begruendung,
        equities_baermarkt_aktiv=equities_baermarkt_aktiv,
        equities_baermarkt_begruendung=equities_baermarkt_begruendung,
        vix_wert=vix_wert,
        vix_label=vix_label,
    )


def get_last_known_regime_status(conn) -> dict | None:
    """Regime-Status-Anzeige (2026-07-17, Remote-Seite + Desktop-Tab "Regime") -
    rein passiver Lesezugriff auf den zuletzt PERSISTIERTEN Regime-Stand, OHNE
    determine_regime() erneut aufzurufen (kein Live-Recompute, kein Netzwerk-Call).

    Quellen: `signals.regime`/`regime_source` (identisch fuer alle Symbole
    eines Laufs, siehe get_latest_regime_from_signals()) + die zuletzt
    gespeicherte macro_snapshot-Zeile (Fear&Greed/BTC-Dominanz/Zyklus-Risiko/
    Liquiditaetsregime/Boden-Zielzone). `dominance_trend_label` wird NICHT
    gespeichert, sondern hier aus der bereits geladenen macro_snapshot-Historie
    neu berechnet (_dominance_trend_label() ist eine reine Funktion, kein
    Netzwerk-Call).

    Gibt None zurueck, wenn noch nie ein Signal existiert (frischer Datenbestand).
    """
    import database.db as db

    latest = db.get_latest_regime_from_signals(conn)
    if latest is None:
        return None
    regime, regime_source, created_at = latest

    snapshot = db.get_latest_macro_snapshot(conn)
    dominance_trend_label = _dominance_trend_label(db.get_macro_snapshot_history(conn))

    return {
        "regime": regime,
        "regime_source": regime_source,
        "created_at": created_at,
        "regime_reason": snapshot.regime_reason if snapshot else None,
        "btc_trend_label": snapshot.btc_trend_label if snapshot else None,
        "fear_greed_value": snapshot.fear_greed_value if snapshot else None,
        "fear_greed_label": snapshot.fear_greed_label if snapshot else None,
        "btc_dominance_pct": snapshot.btc_dominance_pct if snapshot else None,
        "dominance_trend_label": dominance_trend_label,
        "zyklus_risiko": snapshot.zyklus_risiko if snapshot else None,
        "zyklus_risiko_begruendung": snapshot.zyklus_risiko_begruendung if snapshot else None,
        "liquiditaets_regime": snapshot.liquiditaets_regime if snapshot else None,
        "liquiditaets_regime_begruendung": snapshot.liquiditaets_regime_begruendung if snapshot else None,
        "btc_boden_zielzone_von": snapshot.btc_boden_zielzone_von if snapshot else None,
        "btc_boden_zielzone_bis": snapshot.btc_boden_zielzone_bis if snapshot else None,
        "eth_boden_zielzone_von": snapshot.eth_boden_zielzone_von if snapshot else None,
        "eth_boden_zielzone_bis": snapshot.eth_boden_zielzone_bis if snapshot else None,
    }
