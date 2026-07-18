"""LLM-Synthese fuer Einzelaktien (2026-07-15, Non-Krypto-Agent-Pipeline Phase 1) -
mirror von agent/krypto/analyst.py, aber eigenstaendig statt einer verallgemeinerten
Engine (siehe Basisinfos/Spezifikation.md:814-878, "Zielarchitektur fuer Multi-Asset-
Erweiterbarkeit" - explizite fruehere Entscheidung: eigene Agent-Logik pro
Assetklasse statt einer aufgeblaehten If/Else-Kaskade oder eines verwaesserten
kleinsten gemeinsamen Nenners).

Entfernt gegenueber der Krypto-Version: Bitpanda-Listing-Veto-Sonderregel, TAUSCHEN-
Aktion (oesterreichische Krypto-Tausch-Steuerneutralitaet hat kein Aktien-Aequivalent -
Verkauf einer Aktie ist immer ein steuerlich relevantes Ereignis), BTC-Matrix/
Altseason-Regel, Zyklus-Risiko/MVRV-NUPL (kein Aequivalent fuer Einzelaktien),
antizyklische Funding-Rate/Open-Interest-Regel (keine Optionen-/Futures-
Positionierungsdaten fuer Einzelaktien verfuegbar), AZ-4-Tranchen (Phase 1 bewusst
minimal gehalten).

Neu gegenueber der Krypto-Version: Fundamentaldaten-Kontext (KGV, Sektor,
Marktkapitalisierung, naechstes Earnings-Datum, siehe api/yfinance_client.py::
fetch_fundamentals()) + eine Bewertungs-/Bubble-Risiko-Regel."""
from __future__ import annotations

import json
import logging

import numpy as np

from agent.krypto.regime import RegimeResult
from agent.krypto.risk_gate import RiskPreCheckResult
from importer.bitpanda_avg_cost import compute_cost_basis_view
from indicators.calculations import ConfluenceSummary, TechnicalSnapshot, latest_value

logger = logging.getLogger(__name__)

# Kein TAUSCHEN (siehe Modul-Docstring) - vier statt fuenf Aktionen.
REQUIRED_ACTIONS = ("KAUFEN", "VERKAUFEN", "HALTEN", "NACHKAUFEN")

SYSTEM_PROMPT = """Du bist ein Trading-Analyst fuer ein privates Aktien-Advisory-Tool. \
Deine Rolle ist rein beratend (P-7) - du fuehrst NIEMALS einen Trade aus, du gibst nur \
eine Empfehlung, die der Nutzer manuell umsetzen oder ablehnen kann. Formuliere nichts \
als bereits ausgefuehrte Handlung.

REGELN (strikt einhalten):
1. Nutze AUSSCHLIESSLICH die im Fakten-JSON gelieferten Zahlen und Informationen. \
Erfinde keine Kurse, Indikatorwerte, Fundamentaldaten, Nachrichten oder Ereignisse.
2. Wenn `risiko_check.kauf_erlaubt` == false ist, darfst du NIEMALS "KAUFEN" oder \
"NACHKAUFEN" empfehlen - schlage stattdessen "HALTEN" vor und nenne den Veto-Grund.
3. Bei "KAUFEN"/"NACHKAUFEN" ist ein Stop-Loss PFLICHT und das Chance-Risiko-Verhaeltnis \
MUSS mindestens 2.0 betragen, konservativ gerechnet ueber die Zonen-Grenzen aus Regel 11: \
((take_profit.usd_von - entry_mitte) / (entry_mitte - stop_loss.usd_von)), wobei \
entry_mitte = (entry.usd_von + entry.usd_bis) / 2. Deine Zonen muessen so gewaehlt sein, \
dass diese konservative Rechnung >= 2.0 ergibt - sonst wird der Vorschlag nachtraeglich \
deterministisch auf HALTEN korrigiert. Zusaetzlich MUSS `position_size.usd` <= \
`risiko_check.max_positionsgroesse_usd` sein (analog `position_size.eur` <= \
`risiko_check.max_positionsgroesse_eur`), falls diese Obergrenze nicht null ist - \
schlaegst du dennoch mehr vor, wird die Positionsgroesse nachtraeglich deterministisch \
auf die Obergrenze gekuerzt (keine Ablehnung der Kauf-Idee, nur eine Korrektur der \
Groesse). WICHTIG: `max_positionsgroesse_usd/eur` ist eine harte Obergrenze, KEIN \
Zielwert - schlage nicht automatisch die volle Obergrenze vor. Bei `confidence_pct` \
nahe der fuer dieses Regime geltenden Mindestschwelle (siehe `risiko_check` bzw. \
Fakten-JSON) ist das die am wenigsten ueberzeugende noch zulaessige Empfehlung und \
sollte deutlich UNTER der Obergrenze liegen; nur bei hoher Konfidenz (nahe 100%) ist \
eine Positionsgroesse nahe der vollen Obergrenze gerechtfertigt. Die Obergrenze selbst \
wird zusaetzlich serverseitig nach Konfidenz skaliert (deterministisch, nicht von dir \
zu berechnen) - eine konfidenz-bewusste eigene Einschaetzung vermeidet unnoetige \
nachtraegliche Kuerzungen.
4. Berechne den prozentualen Abstand jeder Zonen-Grenze (von UND bis) von Entry/Stop-Loss/ \
Take-Profit zum aktuellen Kurs EINMAL und wende ihn auf USD- UND EUR-Kurs gleichermassen an \
(keine unabhaengig erfundenen Werte je Waehrung).
5. `disclaimers` zeigt an, ob Makro/Sentiment einbezogen sind. Sind sie es nicht, muss \
das Feld `long_reasoning.makro` das explizit sagen - erfinde keine Makro-Einschaetzung.
6. Bei `asset.rolle == "core"` ODER einem taktischen Beobachtungs-/Wiedereinstiegs- \
Kandidaten (`asset.rolle == "taktisch"`, `asset.wird_aktuell_gehalten == false`, \
`asset.beobachtungsstatus == "beobachtung"` - 2026-07-16, Klassifikations-Redesign: \
gilt jetzt auch fuer taktische Kandidaten mit einer bewussten Wiedereinstiegs- oder \
Erstkauf-These, nicht mehr nur fuer Core) wird KEINE aktive Trading-Position verfolgt, \
sondern eine langfristige Kernposition gehalten bzw. eine bewusste These beobachtet. \
Bewerte hier ZWEI GETRENNTE Ebenen: (a) die kurz-/mittelfristige technische Lage wie bei \
jedem Asset, UND (b) den Status der grundlegenden langfristigen Investment-These (ist \
sie noch intakt, oder gibt es einen echten fundamentalen Bruch - z.B. ein \
Bilanzskandal, ein branchenweiter regulatorischer Umbruch, ein struktureller \
Wettbewerbsverlust? Kurzfristige Kursschwaeche oder ein schwacher technischer Trend \
allein sind KEIN Bruch). Empfiehl VERKAUFEN (bzw. bei einem noch nicht gehaltenen \
Beobachtungs-Kandidaten: rate explizit von einem Einstieg ab) nur, wenn (b) \
tatsaechlich gebrochen ist. Ist nur (a) schwach, aber (b) intakt, empfiehl HALTEN \
(bzw. weiter Beobachten) trotz kurzfristiger Schwaeche. Nenne im Feld \
`long_reasoning.fundamental` IMMER explizit, ob die langfristige These aus deiner \
Sicht intakt ist und warum - unabhaengig davon, was `action` letztlich ist.
7. Ordne den aktuellen Kurs EXPLIZIT relativ zu `technische_analyse.fibonacci` \
(Fibonacci-Retracement-Level) und `technische_analyse.support_resistance` ein - \
z.B. "Kurs nahe dem 61,8%-Retracement bei X - historisch oft eine Unterstuetzungs-/ \
Widerstandszone". Nenne das konkret im Feld `long_reasoning.technisch`, nicht nur die \
Standard-Indikatoren (EMA/MACD/RSI/Bollinger).
8. Beziehe `regime.liquiditaets_regime` (expansiv/restriktiv/gemischt/widerspruechlich/ \
unbekannt) als ZUSAETZLICHEN Kontext in `long_reasoning.makro` ein - beschreibende \
Einordnung ("globale Liquiditaet expandiert/kontrahiert aktuell laut M2-Trend + \
Fed-Kurs"), keine harte Regel. Bei `unbekannt` (zu wenig Historie) einfach nicht \
erwaehnen. Beziehe zusaetzlich `regime.aktien_baermarkt.aktiv` ein, falls true - ein \
breiter Liquiditaetsentzug am Aktienmarkt (S&P500/Nasdaq-Drawdown) ist relevanter \
Kontext fuer JEDE Einzelaktie, nicht nur ein Zusatzfakt.
9. Fundamentaldaten-Bewertungsregel: vergleiche `fundamentaldaten.kgv` (trailing) MIT \
`fundamentaldaten.forward_kgv` UND den Wachstumsraten `gewinnwachstum_prozent`/ \
`umsatzwachstum_prozent`, bevor du ein hohes KGV als Risiko einordnest - ein hohes \
trailing-KGV bei gleichzeitig deutlich niedrigerem forward_kgv UND hohem Wachstum \
(z.B. > 30%) ist ANDERS zu bewerten als ein hohes KGV OHNE erkennbares Wachstum. Nur \
wenn das KGV hoch ist (grobe Orientierung: > 60) UND die Wachstumsraten das NICHT \
erkennbar rechtfertigen, weise das EXPLIZIT als Bewertungs-/Bubble-Risiko in \
`key_risks` oder `long_reasoning.fundamental` aus - erfinde dabei KEINE konkreten \
historischen Vergleichszahlen, die nicht im Fakten-JSON stehen. Sind Wachstumsraten \
`null` (nicht verfuegbar), sage das explizit statt Wachstum anzunehmen ODER zu \
verneinen. Ist `naechstes_earnings_datum` innerhalb von 14 Tagen, nenne das als \
moeglichen Volatilitaets-Faktor in `key_risks` (analog zu FOMC-Naehe bei Makro-Events).
10. `fundamentaldaten.dividendenrendite_prozent` (falls nicht null und > 0) ist \
niedrig gewichteter Zusatzkontext in `long_reasoning.fundamental` - erwaehne bei \
dividendenstarken Werten kurz, dass ein Teil der Bewertung durch Ausschuettungen \
gestuetzt sein kann, besonders in Kombination mit `regime.liquiditaets_regime` \
(z.B. hohe Zinsen machen dividendenstarke Aktien als Anleihen-Alternative weniger \
attraktiv). Bei null/0: nicht erwaehnen.
11. `fundamentaldaten.analysten_konsens`/`analysten_kursziel_usd` sind eine \
DRITTMEINUNG (Analysten-Konsens), KEINE eigene Bewertung und KEINE Garantie - \
erwaehne sie NUR als niedrig gewichteten Kontext in `long_reasoning.fundamental` \
(z.B. "Analysten-Konsens: buy, Kursziel X USD, entspricht ca. Y% Abstand zum \
aktuellen Kurs laut `fundamentaldaten.kursziel_potential_prozent`") - uebernimm sie \
NIE als eigene Meinung/Begruendung fuer `action`, das bleibt deine eigenstaendige \
Einschaetzung basierend auf den UEBRIGEN Fakten. Bei null: nicht erwaehnen.
12. `action` MUSS EXAKT einer dieser vier Werte sein (Grossbuchstaben, keine Variante): \
KAUFEN, VERKAUFEN, HALTEN, NACHKAUFEN.
13. Entry/Stop-Loss/Take-Profit sind Kurszonen (von <= bis), abgeleitet aus echten, \
gelieferten Referenzpunkten (`technische_analyse.atr.wert`, \
`technische_analyse.support_resistance`, `technische_analyse.fibonacci`) - KEINE frei \
geratene Bandbreite. Siehe Regel 3 fuer die daran gekoppelte CRV-Pflicht.
14. Fuelle zusaetzlich zu `long_reasoning` das Feld `top_gruende` mit GENAU 5 Eintraegen, \
sortiert von der staerksten zur schwaechsten Begruendung (rang 1 = staerkste, rang 5 = \
schwaechste, jede Zahl 1-5 genau einmal). Jeder Eintrag hat `rang` (1-5), `kategorie` \
(EXAKT einer von: technisch, fundamental, makro, risiko) und `text` (ein praegnanter \
Satz). `top_gruende` ersetzt NICHT `long_reasoning`, das weiterhin die volle \
Begruendung je Kategorie enthaelt.
15. Fuelle `halte_kriterium` zusaetzlich zum groben `bucket` (kurz|mittel|lang) mit \
mindestens EINEM konkreten, ueberpruefbaren Kriterium: einem Ziel-Kurs \
(`ziel_preis_usd`/`ziel_preis_eur`), einem Ziel-Datum (`ziel_datum`, Format YYYY-MM-DD) \
und/oder einer Bedingung als Text (`bedingung_text`). Mindestens eines der drei Felder \
MUSS gesetzt sein.
16. Antworte AUSSCHLIESSLICH mit einem einzigen JSON-Objekt gemaess dem vorgegebenen \
Schema. Kein Markdown, keine Code-Fences, kein Text ausserhalb des JSON.
17. `haltung.gewinn_verlust_pct` (falls nicht null) ist der aktuelle Gewinn/Verlust der \
bestehenden Position gegenueber dem echten Anschaffungspreis - niedrig gewichteter \
Kontext, KEINE harte Regel und KEIN Ersatz fuer die Stop-Loss-/CRV-Pflicht (Regel 3). \
Bei null: nicht erwaehnen.
18. Fuelle `gegenargument` IMMER zuerst aus, BEVOR du `confidence_pct` festlegst - formuliere \
darin das STAERKSTE Argument GEGEN deinen eigenen Vorschlag (nicht ein schwaches \
Feigenblatt-Gegenargument). Typische Quellen: widersprechen sich Indikatoren \
(`technische_analyse.confluence.gesamttendenz` == "gemischt")? Ist das Chance-Risiko-\
Verhaeltnis nur knapp ueber der Pflichtgrenze von 2.0? Beruht `long_reasoning.fundamental` \
oder `.makro` nur auf allgemeinen, nicht assetspezifischen Aussagen? `confidence_pct` MUSS \
das dort formulierte Gegenargument widerspiegeln - ein GENUIN starkes Gegenargument darf \
NICHT mit hoher Konfidenz (>75%) kombiniert werden.
19. Ist `historische_erfolgsquote` NICHT null, gibt sie die bisherige Trefferquote frueherer \
Signale wieder (`trefferquote_pct`, `anzahl_ausgewertete_signale`). Beziehe diese Zahl grob \
in deine `confidence_pct`-Kalibrierung mit ein, aber NUR als schwaches Zusatzindiz - lies \
den mitgelieferten `hinweis` zur Stichprobengroesse und ueberschaetze die Aussagekraft bei \
kleiner Stichprobe nicht. Eine niedrige historische Trefferquote sollte die Konfidenz eher \
daempfen, eine hohe historische Trefferquote ersetzt aber NICHT die eigenstaendige Analyse \
des aktuellen Falls.
20. Ist `historischer_makro_vergleich` NICHT null, listet er historische Kalendermonate mit \
einer AEHNLICHEN Makro-Konstellation (Dollarstaerke, Zinsen, Anleiherenditen, Oelpreis, \
Aktienbewertung) wie heute samt bekanntem weiteren Verlauf des S&P 500 (`top_analoge`, je \
Eintrag `spx_forward_6m_prozent`/`spx_forward_12m_prozent`) UND einem Aggregat-Feld \
(`spx_median_forward_6m_prozent`/`spx_median_forward_12m_prozent`) ueber alle gelisteten \
Analoge. Dieses Aggregat darf als grobe Orientierung fuer deine `confidence_pct`-\
Kalibrierung dienen - ist die historische Streuung der einzelnen Analoge aber gross \
(sehr unterschiedliche `spx_forward_*`-Werte), sollte das die Konfidenz eher daempfen statt \
falsche Praezision zu suggerieren. Lies den mitgelieferten `hinweis` fuer weitere Details.

SCHEMA:
{
  "action": "KAUFEN|VERKAUFEN|HALTEN|NACHKAUFEN",
  "gegenargument": "<das staerkste Argument GEGEN diesen Vorschlag, siehe Regel 18>",
  "confidence_pct": <0-100>,
  "short_reasoning": "<1-2 Saetze>",
  "top_gruende": [
    {"rang": 1, "kategorie": "technisch|fundamental|makro|risiko", "text": "<Text>"},
    {"rang": 2, "kategorie": "technisch|fundamental|makro|risiko", "text": "<Text>"},
    {"rang": 3, "kategorie": "technisch|fundamental|makro|risiko", "text": "<Text>"},
    {"rang": 4, "kategorie": "technisch|fundamental|makro|risiko", "text": "<Text>"},
    {"rang": 5, "kategorie": "technisch|fundamental|makro|risiko", "text": "<Text>"}
  ],
  "long_reasoning": {"technisch": "<Text>", "fundamental": "<Text>", "makro": "<Text>"},
  "position_size": {"usd": <Zahl oder null>, "eur": <Zahl oder null>, "note": "<Text>"},
  "entry": {"usd_von": <Zahl oder null>, "usd_bis": <Zahl oder null>, "eur_von": <Zahl oder null>, "eur_bis": <Zahl oder null>},
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
  }
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
    """Mirror von agent/krypto/analyst.py::_build_haltung_facts() - importer/
    bitpanda_avg_cost.py::compute_cost_basis_view() ist bereits assetklassen-neutral
    (arbeitet nur mit holding.quantity/Einstandspreis, kein Krypto-Bezug)."""
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
    risk_result: RiskPreCheckResult,
    fundamentals,
    price_age_minutes: float | None,
    historische_erfolgsquote: dict | None = None,
    historischer_makro_vergleich: dict | None = None,
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

    # Klassifikations-Redesign (2026-07-16): "wird_aktuell_gehalten" live aus
    # dem uebergebenen holding-Objekt abgeleitet statt eines gespeicherten
    # Status-Felds - kann dadurch nie veralten (siehe config.py::
    # WatchlistAsset-Docstring).
    wird_aktuell_gehalten = bool(
        holding and ((holding.quantity or 0.0) + (holding.staked_quantity or 0.0)) > 0.0
    )
    facts = {
        "asset": {
            "symbol": asset.symbol,
            "name": asset.name,
            "rolle": asset.rolle,
            "wird_aktuell_gehalten": wird_aktuell_gehalten,
            "beobachtungsstatus": asset.beobachtungsstatus,
        },
        "preis": {
            "usd": _native(latest_price.price_usd) if latest_price else None,
            "eur": _native(latest_price.price_eur) if latest_price else None,
            "aktualisiert_vor_min": price_age_minutes,
        },
        "haltung": _build_haltung_facts(holding, latest_price),
        "historische_erfolgsquote": historische_erfolgsquote,
        "historischer_makro_vergleich": historischer_makro_vergleich,
        "fundamentaldaten": {
            "kgv": _native(fundamentals.kgv) if fundamentals else None,
            "forward_kgv": _native(fundamentals.forward_kgv) if fundamentals else None,
            "gewinnwachstum_prozent": _native(fundamentals.gewinnwachstum_pct) if fundamentals else None,
            "umsatzwachstum_prozent": _native(fundamentals.umsatzwachstum_pct) if fundamentals else None,
            "dividendenrendite_prozent": _native(fundamentals.dividendenrendite_pct) if fundamentals else None,
            "analysten_konsens": fundamentals.analysten_konsens if fundamentals else None,
            "analysten_kursziel_usd": _native(fundamentals.analysten_kursziel_usd) if fundamentals else None,
            # Deterministisch vorberechnet (nicht vom LLM erwartet auszurechnen,
            # analog zu anderen Prozent-Ableitungen im Projekt) - None wenn Kursziel
            # oder aktueller Kurs fehlt.
            "kursziel_potential_prozent": (
                _native((fundamentals.analysten_kursziel_usd - latest_price.price_usd) / latest_price.price_usd * 100)
                if fundamentals and fundamentals.analysten_kursziel_usd and latest_price and latest_price.price_usd
                else None
            ),
            "marktkapitalisierung_usd": _native(fundamentals.market_cap_usd) if fundamentals else None,
            "sektor": fundamentals.sektor if fundamentals else None,
            "naechstes_earnings_datum": fundamentals.naechstes_earnings_datum if fundamentals else None,
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
            "liquiditaets_regime": regime_result.liquiditaets_regime,
            "liquiditaets_regime_begruendung": regime_result.liquiditaets_regime_begruendung,
            "aktien_baermarkt": {
                "aktiv": regime_result.equities_baermarkt_aktiv,
                "begruendung": regime_result.equities_baermarkt_begruendung,
            },
        },
        "risiko_check": {
            "kauf_erlaubt": risk_result.kauf_erlaubt,
            "veto_grund": risk_result.veto_reason,
            "max_positionsgroesse_usd": _native(risk_result.max_position_size_usd),
            "max_positionsgroesse_eur": _native(risk_result.max_position_size_eur),
            "stop_loss_abstand_prozent": _native(risk_result.stop_loss_distance_pct),
            "cash_reserve_aktuell_prozent": _native(risk_result.cash_reserve_pct_current),
            "allokation_asset_aktuell_prozent": _native(risk_result.allocation_pct_current),
        },
        "disclaimers": {
            "makro_einbezogen": "teilweise",
            "sentiment_einbezogen": False,
            "hinweis": (
                "Makro ist NUR teilweise einbezogen: Fed-Funds-Rate-Richtung + globaler "
                "M2-Trend fliessen ueber regime.liquiditaets_regime ein, sowie ein "
                "S&P500/Nasdaq-Drawdown-Indikator. Sentiment (X/YouTube/Analysten-"
                "Konsens) ist in diesem System noch nicht implementiert."
            ),
        },
    }
    return facts


REQUIRED_TOP_LEVEL_FIELDS = (
    "action", "gegenargument", "confidence_pct", "short_reasoning", "top_gruende", "long_reasoning",
    "position_size", "entry", "stop_loss", "take_profit", "halte_kriterium",
    "key_risks", "forecast",
)

TOP_GRUENDE_KATEGORIEN = ("technisch", "fundamental", "makro", "risiko")
_HALTE_KRITERIUM_BUCKETS = ("kurz", "mittel", "lang")

# Halluzinations-Absicherung (mirror agent/krypto/analyst.py::_pruefe_kreuzkontamination(),
# 2026-07-14-Fund) - hier gegen faelschlich referenzierte Krypto-Konzepte, die im
# Aktien-Facts-JSON nie vorkommen (Bitpanda-Listing, Krypto-Tausch/TAUSCHEN, BTC-Matrix/
# Altseason, On-Chain MVRV/NUPL, Funding-Rate/Open-Interest).
_KRYPTO_KONTAMINATIONS_BEGRIFFE = (
    "bitpanda gelistet", "bitpanda-listing", "altseason", "btc-season", "baer_flucht",
    "mvrv", "nupl", "funding rate", "funding-rate", "open interest", "tauschen_target",
)


def _pruefe_kreuzkontamination(data: dict) -> None:
    freitexte: list[str] = [str(data.get("short_reasoning") or "")]
    long_reasoning = data.get("long_reasoning")
    if isinstance(long_reasoning, dict):
        freitexte.extend(str(v) for v in long_reasoning.values())
    key_risks = data.get("key_risks")
    if isinstance(key_risks, list):
        freitexte.extend(str(r) for r in key_risks)
    top_gruende = data.get("top_gruende")
    if isinstance(top_gruende, list):
        freitexte.extend(str(e.get("text") or "") for e in top_gruende if isinstance(e, dict))
    halte_kriterium = data.get("halte_kriterium")
    if isinstance(halte_kriterium, dict):
        freitexte.append(str(halte_kriterium.get("bedingung_text") or ""))
        freitexte.append(str(halte_kriterium.get("reasoning") or ""))

    gesamt_text = " ".join(freitexte).lower()
    for begriff in _KRYPTO_KONTAMINATIONS_BEGRIFFE:
        if begriff in gesamt_text:
            raise AnalystResponseInvalid(
                f"Antwort erwaehnt Krypto-Konzept '{begriff}' - existiert nicht im "
                "Aktien-Facts-JSON (Kreuzkontamination/Halluzination)"
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

    gegenargument = str(data.get("gegenargument", "")).strip()
    if len(gegenargument) < 15:
        raise AnalystResponseInvalid(f"gegenargument fehlt oder zu kurz: {data.get('gegenargument')!r}")
    data["gegenargument"] = gegenargument

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

    _pruefe_kreuzkontamination(data)

    return data


def call_llm_for_signal(llm_client, facts: dict, max_retries: int = 2) -> dict:
    """Ruft den LLM-Client auf, validiert die Antwort - mirror agent/krypto/analyst.py::
    call_groq_for_signal() (identisches Retry-/Fail-Loud-Muster). `llm_client` duck-typed
    (Groq/Cerebras/Gemini teilen dasselbe .chat()-Interface, siehe agent/krypto/
    llm_provider.py)."""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": json.dumps(facts, ensure_ascii=False)},
    ]

    last_error: Exception | None = None
    for attempt in range(max_retries + 1):
        raw = llm_client.chat(
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
            logger.info("LLM-Antwort ungültig (Versuch %d): %s", attempt + 1, exc)
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
