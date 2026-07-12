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

from agent.krypto.anticyclic import AnticyclicContext
from agent.krypto.regime import RegimeResult
from agent.krypto.risk_gate import RiskPreCheckResult
from importer.bitpanda_avg_cost import compute_cost_basis_view
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
"NACHKAUFEN" empfehlen - schlage stattdessen "HALTEN" vor und nenne den Veto-Grund. \
Ist `asset.bitpanda_gelistet` explizit false, ist das bei Krypto-Assets der typischste \
Veto-Grund - benenne das explizit (z.B. in `top_gruende`/`key_risks`), auch wenn \
`action` wegen einer bestehenden Position VERKAUFEN/TAUSCHEN statt HALTEN ist.
3. Bei "KAUFEN"/"NACHKAUFEN" ist ein Stop-Loss PFLICHT und das Chance-Risiko-Verhaeltnis \
MUSS mindestens 2.0 betragen, konservativ gerechnet ueber die Zonen-Grenzen aus Regel 16: \
((take_profit.usd_von - entry_mitte) / (entry_mitte - stop_loss.usd_von)), wobei \
entry_mitte = (entry.usd_von + entry.usd_bis) / 2. Deine Zonen muessen so gewaehlt sein, \
dass diese konservative Rechnung >= 2.0 ergibt - sonst wird der Vorschlag nachtraeglich \
deterministisch auf HALTEN korrigiert. Zusaetzlich MUSS `position_size.usd` <= \
`risiko_check.max_positionsgroesse_usd` sein (analog `position_size.eur` <= \
`risiko_check.max_positionsgroesse_eur`), falls diese Obergrenze nicht null ist - \
schlaegst du dennoch mehr vor, wird die Positionsgroesse nachtraeglich deterministisch \
auf die Obergrenze gekuerzt (keine Ablehnung der Kauf-Idee, nur eine Korrektur der \
Groesse).
4. Berechne den prozentualen Abstand jeder Zonen-Grenze (von UND bis) von Entry/Stop-Loss/ \
Take-Profit zum aktuellen Kurs EINMAL und wende ihn auf USD- UND EUR-Kurs gleichermassen an \
(keine unabhaengig erfundenen Werte je Waehrung).
5. `disclaimers` zeigt an, ob Makro/Sentiment einbezogen sind. Sind sie es nicht, muss \
das Feld `long_reasoning.makro` das explizit sagen (z.B. "Makrodaten sind in diesem \
System noch nicht integriert") - erfinde keine Makro-Einschaetzung.
6. Bevorzuge bei strategisch gleichwertigen Alternativen "TAUSCHEN" (in einen \
Stablecoin/anderes Asset) statt "VERKAUFEN", da Krypto-zu-Krypto-Tausch in Oesterreich \
bis zur Fiat-Auszahlung steuerneutral ist - nenne dann `tauschen_target_symbol`.
7. Bei `asset.typ == "core"` (aktuell BTC/ETH) wird eine langfristige Kernposition \
gehalten, kein kurzfristiges Trading-Vehikel. Bewerte hier ZWEI GETRENNTE Ebenen: \
(a) die kurz-/mittelfristige technische Lage wie bei jedem Asset, UND (b) den Status \
der grundlegenden langfristigen These (ist sie noch intakt, oder gibt es einen echten \
fundamentalen Bruch - z.B. ein technisches/protokollarisches Versagen, eine global \
durchsetzbare Verbots-Regulierung? Kurzfristige Kursschwaeche oder ein schwacher \
technischer Trend allein sind KEIN Bruch). Empfiehl VERKAUFEN/TAUSCHEN fuer \
Core-Assets nur, wenn (b) tatsaechlich gebrochen ist. Ist nur (a) schwach, aber (b) \
intakt, empfiehl HALTEN trotz kurzfristiger Schwaeche. Nenne im Feld \
`long_reasoning.fundamental` IMMER explizit, ob die langfristige These aus deiner \
Sicht intakt ist und warum - unabhaengig davon, was `action` letztlich ist.
8. Bei `asset.typ != "core"` (taktische Assets/Altcoins) beachte `regime.btc_matrix` \
bei der Einschaetzung bullischer technischer Signale: bei `btc_season` oder \
`baer_flucht` sind Alt-Kaufsignale (z.B. Ausbrueche, bullische Konfluenz) mit erhoehter \
Skepsis zu behandeln, auch wenn die Technik fuer sich genommen positiv aussieht - nenne \
das explizit in `long_reasoning.technisch`. Bei `altseason` duerfen bullische Alt-Signale \
mit normalem/hoeherem Vertrauen bewertet werden. Bei `nicht_verfuegbar` ignoriere diesen \
Punkt. Diese Regel gilt NICHT fuer Core-Assets (die werden nach Regel 7 bewertet).
9. Ordne den aktuellen Kurs EXPLIZIT relativ zu `technische_analyse.fibonacci` \
(Fibonacci-Retracement-Level) und `technische_analyse.support_resistance` ein - \
z.B. "Kurs nahe dem 61,8%-Retracement bei X - historisch oft eine Unterstuetzungs-/ \
Widerstandszone" oder "Kurs zwischen dem 38,2%- und 50%-Level, kein unmittelbares \
Fibonacci-Level in der Naehe". Nenne das konkret im Feld `long_reasoning.technisch`, \
nicht nur die Standard-Indikatoren (EMA/MACD/RSI/Bollinger) - diese Level werden \
sonst systematisch ignoriert, obwohl sie geliefert werden.
10. Beziehe `regime.liquiditaets_regime` (expansiv/restriktiv/gemischt/widerspruechlich/ \
unbekannt) als ZUSAETZLICHEN Kontext in `long_reasoning.makro` ein - NICHT als harte \
Regel wie regime.btc_matrix, sondern als beschreibende Einordnung ("globale \
Liquiditaet expandiert/kontrahiert aktuell laut M2-Trend + Fed-Kurs"). Bei \
`unbekannt` (zu wenig Historie) einfach nicht erwaehnen, keine Luecke erfinden.
11. Beziehe `regime.zyklus_risiko` (0-1, hoeher = naeher an einem historischen \
Bewertungsextrem laut Log-Regression-Modell) UND `regime.zyklus_risiko_begruendung` \
(enthaelt bereits den MVRV/NUPL-Cross-Check) in `long_reasoning.fundamental` ein - \
als BTC-weite Zyklus-Einordnung, relevant fuer ALLE Assets (nicht nur BTC selbst), \
da Alts historisch am staerksten leiden, wenn BTC nahe einem Zyklus-Top steht. Bei \
`null`/nicht verfuegbar einfach nicht erwaehnen.
12. Wenn `antizyklisch.moeglicher_flush` true ist, nenne das explizit in \
`long_reasoning.technisch` oder `key_risks` und beziehe `antizyklisch.grund` \
(enthaelt bereits Funding-Rate, Kursaenderung und - falls verfuegbar - Open Interest/ \
Long-Short-Ratio als Cross-Check) mit ein. Das ist ein grober Hinweis, KEINE \
gesicherte Klassifikation (keine unabhaengige Nachrichtenquelle) - formuliere \
entsprechend vorsichtig ("moeglicherweise", "Hinweis auf", nicht "ist ein Flush").
13. `markt_kontext` ist NIEDRIG gewichteter Zusatzkontext, keine harte Regel: \
`btc_exchange_flow_netto_btc` und `stablecoin_supply_gesamt_usd` gehoeren eher in \
`long_reasoning.makro` (nutze `btc_exchange_flow_hinweis` fuer die Interpretations- \
richtung). `praesidentschaftszyklus` ist rein deskriptiv - nenne die historische \
Tendenz NUR mit einem klaren Vorbehalt, dass sie keine Prognose-Garantie ist, falls \
du sie erwaehnst. Ist ein Eintrag in `naechste_fomc_sitzungen` weniger als 14 Tage \
entfernt, nenne das als moeglichen Volatilitaets-Faktor in `key_risks`. Erfinde KEINE \
Werte fuer leere/null Felder, erzwinge auch keine Erwaehnung.
14. `action` MUSS EXAKT einer dieser fuenf Werte sein (Grossbuchstaben, keine Variante): \
KAUFEN, VERKAUFEN, TAUSCHEN, HALTEN, NACHKAUFEN.
15. Fuelle zusaetzlich zu `long_reasoning` das Feld `top_gruende` mit GENAU 5 Eintraegen, \
sortiert von der staerksten zur schwaechsten Begruendung (rang 1 = staerkste, rang 5 = \
schwaechste, jede Zahl 1-5 genau einmal). Jeder Eintrag hat `rang` (1-5), `kategorie` \
(EXAKT einer von: technisch, fundamental, makro, risiko, antizyklisch) und `text` (ein \
praegnanter Satz). `top_gruende` ist eine RANGIERTE ZUSAMMENFASSUNG der wichtigsten \
Treiber - sie darf auch fundamentale/makro Gruende enthalten, die nicht Teil der \
technischen Konfluenz sind. Sie ersetzt NICHT `long_reasoning`, das weiterhin die volle \
Begruendung je Kategorie enthaelt.
16. Entry/Stop-Loss/Take-Profit sind KEINE Einzelkurse mehr, sondern Kurszonen (von <= \
bis). Leite jede Zone aus echten, gelieferten Referenzpunkten ab \
(`technische_analyse.atr.wert`, `technische_analyse.support_resistance`, \
`technische_analyse.fibonacci`) - KEINE frei geratene Bandbreite. Beispiel: Kauf-Zone um \
ein Support-/Fibonacci-Level +/- einen Bruchteil der ATR; Stop-Loss-Zone knapp unterhalb \
der naechsten Unterstuetzung; Take-Profit-Zone um den naechsten Widerstand/ein hoeheres \
Fibonacci-Level. Siehe Regel 3 fuer die daran gekoppelte CRV-Pflicht.
17. Fuelle `halte_kriterium` zusaetzlich zum groben `bucket` (kurz|mittel|lang) mit \
mindestens EINEM konkreten, ueberpruefbaren Kriterium: einem Ziel-Kurs (`ziel_preis_usd`/ \
`ziel_preis_eur`), einem Ziel-Datum (`ziel_datum`, Format YYYY-MM-DD) und/oder einer \
Bedingung als Text (`bedingung_text`, z.B. "RSI faellt unter 30" oder "Kurs bricht unter \
Unterstuetzung X"). Mindestens eines der drei Felder MUSS gesetzt sein (nicht alle drei \
null). Dieses Kriterium wird bei jedem manuellen Pipeline-Lauf neu bewertet - es ist \
KEIN automatischer Trigger, der Nutzer entscheidet weiterhin manuell.
18. Antworte AUSSCHLIESSLICH mit einem einzigen JSON-Objekt gemaess dem vorgegebenen \
Schema. Kein Markdown, keine Code-Fences, kein Text ausserhalb des JSON.
19. `haltung.gewinn_verlust_pct` (falls nicht null) ist der aktuelle Gewinn/Verlust der \
bestehenden Position gegenueber dem echten Anschaffungspreis (`haltung.einstandspreis_eur`, \
EUR, KEINE steuerliche Kostenbasis) - niedrig gewichteter Kontext fuer die Halten/ \
Verkaufen-Abwaegung (z.B. bei einer bereits stark gescheiterten These), KEINE harte Regel \
und KEIN Ersatz fuer die Stop-Loss-/CRV-Pflicht (Regel 3). Ist `einstandspreis_quelle` \
"unbekannt" oder `menge_ohne_bekannten_einstandspreis` > 0, erwaehne diese Unsicherheit \
knapp, statt den Gewinn/Verlust als vollstaendig sicher darzustellen. Bei null: nicht \
erwaehnen, keine Luecke erfinden.
20. NUR wenn `tranchen_erlaubt` true ist, darfst du zusaetzlich zu `entry` das optionale \
Feld `tranchen` fuellen (AZ-4, gestaffelter Kauf/Verkauf statt einer einzigen Zone) - bei \
`tranchen_erlaubt` false lasse `tranchen` immer null. Gilt symmetrisch fuer KAUFEN/ \
NACHKAUFEN UND VERKAUFEN/TAUSCHEN. 2 bis 5 Eintraege, jeder mit `rang` (aufsteigend, \
1 = naechste/hoechste Zone, hoehere Zahl = tiefere/spaetere Zone), `anteil_prozent` \
(Summe ALLER Eintraege muss exakt 100 ergeben), einer eigenen `zone` (gleiches Format wie \
`entry`) und optional `trigger_bedingung` als Freitext (z.B. "Bodenbestaetigung laut \
Regime-/Risiko-Modell"). `entry` selbst bleibt dabei die GESAMTSPANNE ueber alle Tranchen \
(niedrigste bis hoechste Zone). `tranchen` ist eine reine Zusatz-Information fuer den \
Nutzer, KEINE separate Positionsgroessen-Vorgabe - die eine `position_size` bleibt \
unveraendert die Gesamtgroesse.

SCHEMA:
{
  "action": "KAUFEN|VERKAUFEN|TAUSCHEN|HALTEN|NACHKAUFEN",
  "confidence_pct": <0-100>,
  "short_reasoning": "<1-2 Saetze>",
  "top_gruende": [
    {"rang": 1, "kategorie": "technisch|fundamental|makro|risiko|antizyklisch", "text": "<Text>"},
    {"rang": 2, "kategorie": "technisch|fundamental|makro|risiko|antizyklisch", "text": "<Text>"},
    {"rang": 3, "kategorie": "technisch|fundamental|makro|risiko|antizyklisch", "text": "<Text>"},
    {"rang": 4, "kategorie": "technisch|fundamental|makro|risiko|antizyklisch", "text": "<Text>"},
    {"rang": 5, "kategorie": "technisch|fundamental|makro|risiko|antizyklisch", "text": "<Text>"}
  ],
  "long_reasoning": {"technisch": "<Text>", "fundamental": "<Text>", "makro": "<Text>"},
  "position_size": {"usd": <Zahl oder null>, "eur": <Zahl oder null>, "note": "<Text>"},
  "entry": {"usd_von": <Zahl oder null>, "usd_bis": <Zahl oder null>, "eur_von": <Zahl oder null>, "eur_bis": <Zahl oder null>},
  "tranchen": null oder [
    {"rang": 1, "anteil_prozent": <Zahl>, "zone": {"usd_von": <Zahl>, "usd_bis": <Zahl>, "eur_von": <Zahl>, "eur_bis": <Zahl>}, "trigger_bedingung": "<Text oder null>"},
    ...
  ],
  "stop_loss": {"usd_von": <Zahl oder null>, "usd_bis": <Zahl oder null>, "eur_von": <Zahl oder null>, "eur_bis": <Zahl oder null>},
  "take_profit": {"usd_von": <Zahl oder null>, "usd_bis": <Zahl oder null>, "eur_von": <Zahl oder null>, "eur_bis": <Zahl oder null>},
  "halte_kriterium": {
    "bucket": "kurz|mittel|lang",
    "ziel_preis_usd": <Zahl oder null>,
    "ziel_preis_eur": <Zahl oder null>,
    "ziel_datum": "<YYYY-MM-DD oder null>",
    "bedingung_text": "<Text oder null>",
    "reasoning": "<Text>"
  },
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


def _build_haltung_facts(holding, latest_price) -> dict:
    """Einstandspreis-Kontext (2026-07-11, Nutzer-Wunsch) - echter Marktpreis aus
    Bitpanda-Trades, EUR, KEINE steuerliche Kostenbasis (siehe importer/
    bitpanda_avg_cost.py Modul-Docstring). menge_ohne_bekannten_einstandspreis
    macht sichtbar, wenn ein Teil des Bestands nicht bepreist werden konnte
    (Staking-Gutschriften/externe Einzahlungen) - wird nie stillschweigend mit
    eingepreist (P-10)."""
    menge = _native(holding.quantity) if holding else 0.0
    wert_usd = (
        _native(holding.quantity * latest_price.price_usd)
        if holding and latest_price and latest_price.price_usd
        else 0.0
    )
    if not holding:
        return {"menge": menge, "wert_usd": wert_usd, "einstandspreis_eur": None,
                 "einstandspreis_quelle": "unbekannt", "menge_ohne_bekannten_einstandspreis": 0.0,
                 "gewinn_verlust_pct": None}

    price_eur = latest_price.price_eur if latest_price else None
    view = compute_cost_basis_view(holding, price_eur)
    return {
        "menge": menge,
        "wert_usd": wert_usd,
        "einstandspreis_eur": _native(view.effective_avg_price_eur),
        "einstandspreis_quelle": view.source,
        "menge_ohne_bekannten_einstandspreis": _native(view.unknown_quantity),
        "gewinn_verlust_pct": _native(view.pl_pct),
    }


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
    market_context: dict,
    bitpanda_gelistet: bool | None,
    tranchen_erlaubt: bool = False,
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
            "bitpanda_gelistet": bitpanda_gelistet,
        },
        "preis": {
            "usd": _native(latest_price.price_usd) if latest_price else None,
            "eur": _native(latest_price.price_eur) if latest_price else None,
            "aktualisiert_vor_min": price_age_minutes,
        },
        "haltung": _build_haltung_facts(holding, latest_price),
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
            "btc_matrix": regime_result.btc_matrix_state,
            "btc_matrix_hinweis": regime_result.btc_matrix_beschreibung,
            "liquiditaets_regime": regime_result.liquiditaets_regime,
            "liquiditaets_regime_begruendung": regime_result.liquiditaets_regime_begruendung,
            "zyklus_risiko": _native(regime_result.zyklus_risiko),
            "zyklus_risiko_begruendung": regime_result.zyklus_risiko_begruendung,
            # Boden-Zielzone (AZ-4 Baustein 2, 2026-07-12) - deterministisch berechnete
            # Fakten (wie zyklus_risiko oben), KEIN Groq-Ausgabefeld, daher keine
            # SCHEMA-/_validate()-Aenderung noetig.
            "boden_zielzone_btc": {
                "von": _native(regime_result.btc_boden_zielzone_von),
                "bis": _native(regime_result.btc_boden_zielzone_bis),
                "begruendung": regime_result.btc_boden_zielzone_begruendung,
            },
            "boden_zielzone_eth": {
                "von": _native(regime_result.eth_boden_zielzone_von),
                "bis": _native(regime_result.eth_boden_zielzone_bis),
                "begruendung": regime_result.eth_boden_zielzone_begruendung,
                "hinweis": "Niedrige Konfidenz - nur 2 historische ETH-Zyklus-Tiefpunkte verfügbar.",
            },
            "equities_baermarkt": {
                "aktiv": regime_result.equities_baermarkt_aktiv,
                "begruendung": regime_result.equities_baermarkt_begruendung,
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
            "open_interest_binance": _native(anticyclic_context.open_interest_binance),
            "open_interest_bybit": _native(anticyclic_context.open_interest_bybit),
            "open_interest_okx_usd": _native(anticyclic_context.open_interest_okx_usd),
            "long_short_ratio_binance": _native(anticyclic_context.long_short_ratio),
            "long_konten_anteil_prozent": _native(anticyclic_context.long_account_pct),
            "retail_long_bias_extrem": anticyclic_context.retail_long_bias_extreme,
            "grund": anticyclic_context.reason,
        },
        "markt_kontext": {
            "btc_exchange_flow_netto_btc": (
                _native(market_context["exchange_flow"].net_flow_btc)
                if market_context["exchange_flow"] else None
            ),
            "btc_exchange_flow_hinweis": (
                "positiv = mehr Zufluss als Abfluss (potenzieller Verkaufsdruck), "
                "negativ = Nettoabfluss (Akkumulation/Self-Custody)"
            ),
            "stablecoin_supply_gesamt_usd": (
                _native(market_context["stablecoin_supply"].total_usd)
                if market_context["stablecoin_supply"] else None
            ),
            "praesidentschaftszyklus": {
                "jahr_im_zyklus": market_context["presidential_cycle"].year_in_cycle,
                "einordnung": market_context["presidential_cycle"].label,
                "historische_tendenz": market_context["presidential_cycle"].historical_bias,
            },
            "naechste_fomc_sitzungen": [
                {"name": e.name, "in_tagen": e.days_until} for e in market_context["upcoming_fomc"]
            ],
        },
        "strategien_aktiv": strategien_aktiv,
        "tranchen_erlaubt": tranchen_erlaubt,
        "disclaimers": {
            "makro_einbezogen": "teilweise",
            "sentiment_einbezogen": False,
            "hinweis": (
                "Makro ist NUR teilweise einbezogen: Fed-Funds-Rate-Richtung + globaler "
                "M2-Trend (USA/Eurozone/China) fliessen ueber regime.liquiditaets_regime "
                "ein (siehe Nutzungs-Diskussion 2026-07-08). CPI/ISM-Ersatz/Trueflation/ "
                "einzelne Leitboersen sind weiterhin NICHT einbezogen (Spezifikation "
                "Kap. 16 offen). Sentiment (X/YouTube) ist in diesem System noch nicht "
                "implementiert (Kap. 11 Roadmap Phase 4)."
            ),
        },
    }
    return facts


REQUIRED_TOP_LEVEL_FIELDS = (
    "action", "confidence_pct", "short_reasoning", "top_gruende", "long_reasoning",
    "position_size", "entry", "stop_loss", "take_profit", "halte_kriterium",
    "key_risks", "forecast",
)

TOP_GRUENDE_KATEGORIEN = ("technisch", "fundamental", "makro", "risiko", "antizyklisch")
_HALTE_KRITERIUM_BUCKETS = ("kurz", "mittel", "lang")


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

    for field_name in ("long_reasoning", "position_size", "entry", "stop_loss", "take_profit", "halte_kriterium", "forecast"):
        if not isinstance(data[field_name], dict):
            raise AnalystResponseInvalid(f"{field_name} ist kein Objekt")

    if not isinstance(data["key_risks"], list):
        raise AnalystResponseInvalid("key_risks ist keine Liste")

    top_gruende = data["top_gruende"]
    if not isinstance(top_gruende, list) or len(top_gruende) != 5:
        raise AnalystResponseInvalid(f"top_gruende muss genau 5 Einträge enthalten: {top_gruende!r}")
    ranks_seen = set()
    for eintrag in top_gruende:
        if not isinstance(eintrag, dict):
            raise AnalystResponseInvalid(f"top_gruende-Eintrag ist kein Objekt: {eintrag!r}")
        rang = eintrag.get("rang")
        if rang not in (1, 2, 3, 4, 5) or rang in ranks_seen:
            raise AnalystResponseInvalid(f"top_gruende.rang ungültig oder doppelt: {rang!r}")
        ranks_seen.add(rang)
        kategorie = str(eintrag.get("kategorie", "")).strip().lower()
        if kategorie not in TOP_GRUENDE_KATEGORIEN:
            raise AnalystResponseInvalid(f"top_gruende.kategorie ungültig: {eintrag.get('kategorie')!r}")
        eintrag["kategorie"] = kategorie
        if not str(eintrag.get("text") or "").strip():
            raise AnalystResponseInvalid("top_gruende.text fehlt/leer")

    for field_name in ("entry", "stop_loss", "take_profit"):
        obj = data[field_name]
        for currency in ("usd", "eur"):
            von, bis = obj.get(f"{currency}_von"), obj.get(f"{currency}_bis")
            if von is None and bis is None:
                continue
            if von is None or bis is None:
                raise AnalystResponseInvalid(f"{field_name}.{currency}_von/{currency}_bis: nur einer gesetzt")
            try:
                von, bis = float(von), float(bis)
            except (TypeError, ValueError):
                raise AnalystResponseInvalid(f"{field_name}.{currency}_von/{currency}_bis nicht numerisch")
            if von > bis:
                raise AnalystResponseInvalid(f"{field_name}.{currency}_von > {currency}_bis ({von} > {bis})")
            obj[f"{currency}_von"], obj[f"{currency}_bis"] = von, bis

    halte = data["halte_kriterium"]
    bucket = str(halte.get("bucket", "")).strip().lower()
    if bucket not in _HALTE_KRITERIUM_BUCKETS:
        raise AnalystResponseInvalid(f"halte_kriterium.bucket ungültig: {halte.get('bucket')!r}")
    halte["bucket"] = bucket
    if (
        halte.get("ziel_preis_usd") is None
        and not str(halte.get("ziel_datum") or "").strip()
        and not str(halte.get("bedingung_text") or "").strip()
    ):
        raise AnalystResponseInvalid(
            "halte_kriterium: mindestens eines von ziel_preis_usd/ziel_datum/bedingung_text muss gesetzt sein"
        )

    # AZ-4-Tranchen (2026-07-12): rein informativ, KEIN Pflichtfeld und KEIN harter
    # Validierungsfehler bei Verstoss - es gibt ohnehin keine Moeglichkeit, den
    # tatsaechlichen Order-Status ueber die Bitpanda-API zu verfolgen (siehe
    # Regelwerksmanual Kap. 4), die Info bleibt bewusst unverbindlich. Ein fehlerhafter
    # Tranchen-Vorschlag darf deshalb nicht das sonst valide Gesamtsignal scheitern lassen.
    tranchen = data.get("tranchen")
    if tranchen is not None:
        try:
            if not isinstance(tranchen, list) or not (2 <= len(tranchen) <= 5):
                raise ValueError(f"tranchen muss 2-5 Einträge enthalten: {tranchen!r}")
            ranks_seen = set()
            anteil_summe = 0.0
            for eintrag in tranchen:
                if not isinstance(eintrag, dict):
                    raise ValueError(f"tranchen-Eintrag ist kein Objekt: {eintrag!r}")
                rang = eintrag.get("rang")
                if not isinstance(rang, int) or rang in ranks_seen:
                    raise ValueError(f"tranchen.rang ungültig oder doppelt: {rang!r}")
                ranks_seen.add(rang)
                anteil = float(eintrag.get("anteil_prozent"))
                anteil_summe += anteil
                eintrag["anteil_prozent"] = anteil
                zone = eintrag.get("zone")
                if not isinstance(zone, dict):
                    raise ValueError(f"tranchen.zone fehlt/kein Objekt: {zone!r}")
                for currency in ("usd", "eur"):
                    von, bis = zone.get(f"{currency}_von"), zone.get(f"{currency}_bis")
                    if von is None or bis is None:
                        raise ValueError(f"tranchen.zone.{currency}_von/{currency}_bis fehlt")
                    von, bis = float(von), float(bis)
                    if von > bis:
                        raise ValueError(f"tranchen.zone.{currency}_von > {currency}_bis ({von} > {bis})")
                    zone[f"{currency}_von"], zone[f"{currency}_bis"] = von, bis
            if not (99.5 <= anteil_summe <= 100.5):
                raise ValueError(f"tranchen.anteil_prozent-Summe nicht ~100: {anteil_summe}")
        except (ValueError, TypeError) as exc:
            logger.warning("tranchen-Vorschlag verworfen (fehlerhaft, kein Signal-Fehler): %s", exc)
            data["tranchen"] = None

    return data


def call_groq_for_signal(groq_client, facts: dict, max_retries: int = 2) -> dict:
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
