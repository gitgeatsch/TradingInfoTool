"""R-5.6 Groq-Synthese (Spezifikation Kap. 5, Ausgabeformat P-5) - der eigentliche
"echte KI"-Schritt: eine deterministische Fakten-Schicht (Indikatoren, Regime,
Risiko-Check) wird zu JSON zusammengefasst, Groq synthetisiert daraus die
Empfehlung inkl. Begruendung in natuerlicher Sprache. Groq darf NICHTS ausserhalb
der gelieferten Fakten erfinden (Prompt-Klausel) UND wird trotzdem nie blind
vertraut: agent/risk_gate.py::post_check() erzwingt die harten Regeln nachtraeglich
nochmal deterministisch, unabhaengig davon ob das Modell sie befolgt hat.

Zwei Fehlerklassen (siehe Plan): (a) kaputtes/unvollstaendiges JSON -> hier per
Retry+Fail-Loud behandelt (AnalystResponseInvalid). (b) wohlgeformt aber regelwidrig
(z.B. KAUFEN trotz Veto) -> wird bewusst NICHT hier behandelt, sondern deterministisch
von risk_gate.post_check() korrigiert - vermeidet doppelte Veto-Logik in zwei Dateien.
"""
from __future__ import annotations

import json
import logging

import numpy as np

from agent.anticyclic import AnticyclicContext
from agent.regime import RegimeResult
from agent.risk_gate import RiskPreCheckResult
from indicators.calculations import ConfluenceSummary, TechnicalSnapshot, latest_value

logger = logging.getLogger(__name__)

REQUIRED_ACTIONS = ("KAUFEN", "VERKAUFEN", "TAUSCHEN", "HALTEN", "NACHKAUFEN")

SYSTEM_PROMPT = """Du bist ein Trading-Analyst fuer ein privates Krypto-Advisory-Tool. \
Deine Rolle ist rein beratend (P-7) - du fuehrst NIEMALS einen Trade aus, du gibst nur \
eine Empfehlung, die der Nutzer manuell umsetzen oder ablehnen kann. Formuliere nichts \
als bereits ausgefuehrte Handlung.

REGELN (strikt einhalten):
1. Nutze AUSSCHLIESSLICH die im Fakten-JSON gelieferten Zahlen und Informationen. \
Erfinde keine Kurse, Indikatorwerte, Nachrichten oder Ereignisse.
2. Wenn `risiko_check.kauf_erlaubt` == false ist, darfst du NIEMALS "KAUFEN" oder \
"NACHKAUFEN" empfehlen - schlage stattdessen "HALTEN" vor und nenne den Veto-Grund.
3. Bei "KAUFEN"/"NACHKAUFEN" ist ein Stop-Loss PFLICHT und das Chance-Risiko-Verhaeltnis \
((take_profit-entry)/(entry-stop_loss)) MUSS mindestens 2.0 betragen.
4. Berechne den prozentualen Abstand von Entry/Stop-Loss/Take-Profit zum aktuellen Kurs \
EINMAL und wende ihn auf USD- UND EUR-Kurs gleichermassen an (keine unabhaengig \
erfundenen Werte je Waehrung).
5. `disclaimers` zeigt an, ob Makro/Sentiment einbezogen sind. Sind sie es nicht, muss \
das Feld `long_reasoning.makro` das explizit sagen (z.B. "Makrodaten sind in diesem \
System noch nicht integriert") - erfinde keine Makro-Einschaetzung.
6. Bevorzuge bei strategisch gleichwertigen Alternativen "TAUSCHEN" (in einen \
Stablecoin/anderes Asset) statt "VERKAUFEN", da Krypto-zu-Krypto-Tausch in Oesterreich \
bis zur Fiat-Auszahlung steuerneutral ist - nenne dann `tauschen_target_symbol`.
7. `action` MUSS EXAKT einer dieser fuenf Werte sein (Grossbuchstaben, keine Variante): \
KAUFEN, VERKAUFEN, TAUSCHEN, HALTEN, NACHKAUFEN.
8. Antworte AUSSCHLIESSLICH mit einem einzigen JSON-Objekt gemaess dem vorgegebenen \
Schema. Kein Markdown, keine Code-Fences, kein Text ausserhalb des JSON.

SCHEMA:
{
  "action": "KAUFEN|VERKAUFEN|TAUSCHEN|HALTEN|NACHKAUFEN",
  "confidence_pct": <0-100>,
  "short_reasoning": "<1-2 Saetze>",
  "long_reasoning": {"technisch": "<Text>", "fundamental": "<Text>", "makro": "<Text>"},
  "position_size": {"usd": <Zahl oder null>, "eur": <Zahl oder null>, "note": "<Text>"},
  "entry": {"usd": <Zahl oder null>, "eur": <Zahl oder null>},
  "stop_loss": {"usd": <Zahl oder null>, "eur": <Zahl oder null>},
  "take_profit": {"usd": <Zahl oder null>, "eur": <Zahl oder null>},
  "holding_duration": {"bucket": "kurz|mittel|lang", "reasoning": "<Text>"},
  "key_risks": ["<Text>", ...],
  "forecast": {
    "bull": {"scenario": "<Text>", "probability_pct": <0-100>},
    "base": {"scenario": "<Text>", "probability_pct": <0-100>},
    "bear": {"scenario": "<Text>", "probability_pct": <0-100>}
  },
  "tauschen_target_symbol": "<Symbol oder null>"
}"""


class AnalystResponseInvalid(Exception):
    pass


def _native(value):
    if isinstance(value, (np.floating,)):
        return None if np.isnan(value) else float(value)
    if isinstance(value, (np.integer,)):
        return int(value)
    return value


def _last(arr: np.ndarray) -> float | None:
    valid = arr[~np.isnan(arr)]
    return float(valid[-1]) if len(valid) else None


def build_facts(
    asset,
    latest_price,
    holding,
    technical_snapshot: TechnicalSnapshot,
    confluence: ConfluenceSummary,
    regime_result: RegimeResult,
    regime_profile: dict,
    risk_result: RiskPreCheckResult,
    anticyclic_context: AnticyclicContext,
    strategien_aktiv: list[str],
    price_age_minutes: float | None,
) -> dict:
    macd_val = technical_snapshot.macd
    macd_facts = None
    if macd_val.available:
        macd_facts = {
            "macd": _last(macd_val.value["macd"]),
            "signal": _last(macd_val.value["signal"]),
            "histogram": _last(macd_val.value["histogram"]),
        }

    bollinger_facts = None
    if technical_snapshot.bollinger.available:
        bv = technical_snapshot.bollinger.value
        bollinger_facts = {
            "upper": _last(bv["upper"]),
            "middle": _last(bv["middle"]),
            "lower": _last(bv["lower"]),
        }

    nicht_verfuegbar = []
    for period, r in technical_snapshot.ema.items():
        if not r.available:
            nicht_verfuegbar.append(f"EMA-{period}: {r.reason}")
    for name, r in (
        ("MACD", technical_snapshot.macd),
        ("RSI-14", technical_snapshot.rsi),
        ("Bollinger Bands", technical_snapshot.bollinger),
        (technical_snapshot.swing_label, technical_snapshot.swing),
        (technical_snapshot.atr_label, technical_snapshot.atr),
    ):
        if not r.available:
            nicht_verfuegbar.append(f"{name}: {r.reason}")

    facts = {
        "asset": {
            "symbol": asset.symbol,
            "name": asset.name,
            "typ": asset.typ,
            "status": asset.status,
        },
        "preis": {
            "usd": _native(latest_price.price_usd) if latest_price else None,
            "eur": _native(latest_price.price_eur) if latest_price else None,
            "aktualisiert_vor_min": price_age_minutes,
        },
        "haltung": {
            "menge": _native(holding.quantity) if holding else 0.0,
            "wert_usd": _native(holding.quantity * latest_price.price_usd)
            if holding and latest_price and latest_price.price_usd
            else 0.0,
        },
        "technische_analyse": {
            "ema": {str(p): _native(latest_value(r)) for p, r in technical_snapshot.ema.items()},
            "macd": macd_facts,
            "rsi_14": _native(latest_value(technical_snapshot.rsi)),
            "bollinger": bollinger_facts,
            "atr": {
                "wert": _native(latest_value(technical_snapshot.atr)),
                "label": technical_snapshot.atr_label,
                "quelle": technical_snapshot.atr_source,
            },
            "support_resistance": technical_snapshot.support_resistance.value
            if technical_snapshot.support_resistance.available
            else [],
            "fibonacci": {str(k): _native(v) for k, v in (technical_snapshot.fibonacci or {}).items()},
            "confluence": {
                "bullish": confluence.bullish_count,
                "bearish": confluence.bearish_count,
                "neutral": confluence.neutral_count,
                "nicht_verfuegbar": confluence.unavailable_count,
                "gesamttendenz": confluence.overall_bias,
                "details": [
                    {"indikator": i.indicator, "bias": i.bias, "detail": i.detail}
                    for i in confluence.items
                    if i.available
                ],
            },
            "nicht_verfuegbar": nicht_verfuegbar,
        },
        "regime": {
            "wert": regime_result.regime,
            "quelle": regime_result.source,
            "begruendung": regime_result.reason,
            "btc_trend": regime_result.btc_trend_label,
            "btc_dominanz_trend": regime_result.dominance_trend_label,
            "fear_greed": {
                "wert": regime_result.fear_greed_value,
                "einstufung": regime_result.fear_greed_label,
            },
        },
        "regime_profil": regime_profile,
        "risiko_check": {
            "kauf_erlaubt": risk_result.kauf_erlaubt,
            "veto_grund": risk_result.veto_reason,
            "max_positionsgroesse_usd": _native(risk_result.max_position_size_usd),
            "max_positionsgroesse_eur": _native(risk_result.max_position_size_eur),
            "stop_loss_abstand_prozent": _native(risk_result.stop_loss_distance_pct),
            "cash_reserve_aktuell_prozent": _native(risk_result.cash_reserve_pct_current),
            "allokation_asset_aktuell_prozent": _native(risk_result.allocation_pct_current),
            "small_cap_budget_prozent": _native(risk_result.small_cap_budget_pct_applicable),
            "drawdown_notbremse_geprueft": False,
        },
        "antizyklisch": {
            "funding_rate_aktuell": _native(anticyclic_context.funding_rate_current),
            "funding_rate_extrem": anticyclic_context.funding_rate_extreme,
            "kursaenderung_letzte_tage_prozent": _native(anticyclic_context.recent_drop_pct),
            "moeglicher_flush": anticyclic_context.possible_flush,
            "bestaetigung_gate_erfuellt": anticyclic_context.confirmation_gate_passed,
            "grund": anticyclic_context.reason,
        },
        "strategien_aktiv": strategien_aktiv,
        "disclaimers": {
            "makro_einbezogen": False,
            "sentiment_einbezogen": False,
            "hinweis": (
                "Leitzinsen/ISM/CPI/Trueflation (Makro) und X/YouTube (Sentiment) sind in "
                "diesem System noch nicht implementiert (Spezifikation Kap. 16 offen bzw. "
                "Kap. 11 Roadmap Phase 4)."
            ),
        },
    }
    return facts


REQUIRED_TOP_LEVEL_FIELDS = (
    "action", "confidence_pct", "short_reasoning", "long_reasoning", "position_size",
    "entry", "stop_loss", "take_profit", "holding_duration", "key_risks", "forecast",
)


def _validate(data: dict) -> dict:
    if not isinstance(data, dict):
        raise AnalystResponseInvalid("Antwort ist kein JSON-Objekt")

    missing = [f for f in REQUIRED_TOP_LEVEL_FIELDS if f not in data]
    if missing:
        raise AnalystResponseInvalid(f"Pflichtfelder fehlen: {missing}")

    action = str(data["action"]).strip().upper()
    if action not in REQUIRED_ACTIONS:
        raise AnalystResponseInvalid(f"Ungültige action: {data['action']!r}")
    data["action"] = action

    try:
        data["confidence_pct"] = float(data["confidence_pct"])
    except (TypeError, ValueError):
        raise AnalystResponseInvalid(f"confidence_pct nicht numerisch: {data['confidence_pct']!r}")
    if not (0 <= data["confidence_pct"] <= 100):
        raise AnalystResponseInvalid(f"confidence_pct außerhalb 0-100: {data['confidence_pct']}")

    for field_name in ("long_reasoning", "position_size", "entry", "stop_loss", "take_profit", "holding_duration", "forecast"):
        if not isinstance(data[field_name], dict):
            raise AnalystResponseInvalid(f"{field_name} ist kein Objekt")

    if not isinstance(data["key_risks"], list):
        raise AnalystResponseInvalid("key_risks ist keine Liste")

    return data


def call_groq_for_signal(groq_client, facts: dict, max_retries: int = 1) -> dict:
    """Ruft Groq auf, validiert die Antwort. Bei kaputtem/unvollstaendigem JSON wird
    einmal mit Korrektur-Hinweis retryed, danach fail-loud (AnalystResponseInvalid) -
    der Aufrufer (agent/pipeline.py) faengt das ab und erzeugt ein HALTEN-Signal."""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": json.dumps(facts, ensure_ascii=False)},
    ]

    last_error: Exception | None = None
    for attempt in range(max_retries + 1):
        raw = groq_client.chat(
            messages,
            temperature=0.2,
            response_format={"type": "json_object"},
        )
        try:
            parsed = json.loads(raw)
            validated = _validate(parsed)
            validated["_raw_response"] = raw
            return validated
        except (json.JSONDecodeError, AnalystResponseInvalid) as exc:
            last_error = exc
            logger.info("Groq-Antwort ungültig (Versuch %d): %s", attempt + 1, exc)
            messages.append({"role": "assistant", "content": raw})
            messages.append(
                {
                    "role": "user",
                    "content": (
                        f"Deine letzte Antwort war ungültig: {exc}. Antworte erneut, "
                        "ausschließlich mit einem korrekten JSON-Objekt gemäß Schema."
                    ),
                }
            )

    raise AnalystResponseInvalid(f"Nach {max_retries + 1} Versuchen weiterhin ungültig: {last_error}")
