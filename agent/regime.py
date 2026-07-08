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

from database.models import MacroSnapshot
from indicators.calculations import TechnicalSnapshot, latest_value

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


def determine_regime(
    btc_closes: np.ndarray,
    btc_snapshot: TechnicalSnapshot,
    macro_history: list[MacroSnapshot],
    manual_override: str,
    fed_funds_history: list[float] | None = None,
    m2_us_history: list[float] | None = None,
    m2_eurozone_history: list[float] | None = None,
    m2_china_history: list[float] | None = None,
) -> RegimeResult:
    m2_trend, m2_detail = _m2_global_trend(
        m2_us_history or [], m2_eurozone_history or [], m2_china_history or []
    )
    fed_direction = _fed_funds_direction(fed_funds_history or [])
    liquiditaets_regime, liquiditaets_regime_begruendung = _liquidity_regime(m2_trend, fed_direction, m2_detail)
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
        btc_matrix_state=btc_matrix_state,
        btc_matrix_beschreibung=btc_matrix_beschreibung,
    )
