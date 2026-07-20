"""LLM-Synthese fuer Rohstoff-ETCs (2026-07-18, Multi-Asset-Roadmap Phase 2, siehe
Memory project_multi_asset_erweiterbarkeit.md) - mirror von agent/aktien/analyst.py,
aber eigenstaendig statt einer verallgemeinerten Engine (gleiche Architektur-
Entscheidung wie dort, siehe Basisinfos/Spezifikation.md "Zielarchitektur fuer
Multi-Asset-Erweiterbarkeit").

Entfernt gegenueber der Aktien-Version: das komplette Fundamentaldaten-Kapitel
(KGV/Wachstum/Dividende/Analysten-Kursziel/Earnings-Datum) - fuer physische
Rohstoffe gibt es kein KGV-Aequivalent, ein Terminkontrakt/ETC hat keine
Unternehmensbilanz.

Neu gegenueber der Aktien-Version: `makro_ueberlagerung` (Realrendite/Dollar-
Index/Industrieproduktion via FRED, api/macro.py) + `positionierung` (CFTC-COT-
"Managed Money"-Netto-Positionierung, api/cftc_cot.py) als Ersatz fuer das
Fundamentaldaten-Kapitel - siehe Regelwerksmanual-Nachtrag fuer die Build-vs-Buy-
Recherche der Datenquellen (LME-Lagerbestaende/EIA-Erdgas-Lager/ETF-Gold-Bestaende
bewusst NICHT in dieser Runde, siehe dortige Begruendung)."""
from __future__ import annotations

import json
import logging

import numpy as np

from agent.krypto.regime import RegimeResult
from agent.krypto.risk_gate import RiskPreCheckResult
from agent.krypto.wiederholungs_erkennung import build_wiederholung_fact
from importer.bitpanda_avg_cost import compute_cost_basis_view
from indicators.calculations import ConfluenceSummary, TechnicalSnapshot, latest_value

logger = logging.getLogger(__name__)

# Kein TAUSCHEN (kein Krypto-Steuervorteil-Aequivalent) - vier Aktionen wie bei Aktien.
REQUIRED_ACTIONS = ("KAUFEN", "VERKAUFEN", "HALTEN", "NACHKAUFEN")

# Wiederholungs-Erkennung (2026-07-18, Multi-Asset-Vollstaendigkeitspruefung -
# siehe agent/krypto/wiederholungs_erkennung.py).
_WIEDERHOLUNG_RELEVANTE_AKTIONEN = ("VERKAUFEN",)

SYSTEM_PROMPT = """Du bist ein Trading-Analyst fuer ein privates Rohstoff-Advisory-Tool \
(handelbar ueber ETCs - Exchange Traded Commodities, physisch/synthetisch besicherte \
Terminkontrakt-Nachbildungen). Deine Rolle ist rein beratend (P-7) - du fuehrst NIEMALS \
einen Trade aus, du gibst nur eine Empfehlung, die der Nutzer manuell umsetzen oder \
ablehnen kann. Formuliere nichts als bereits ausgefuehrte Handlung.

REGELN (strikt einhalten):
1. Nutze AUSSCHLIESSLICH die im Fakten-JSON gelieferten Zahlen und Informationen. \
Erfinde keine Kurse, Indikatorwerte, Positionierungsdaten, Nachrichten oder Ereignisse.
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
Zielwert. Bei `confidence_pct` nahe der fuer dieses Regime geltenden Mindestschwelle \
(siehe `risiko_check` bzw. Fakten-JSON) ist das die am wenigsten ueberzeugende noch \
zulaessige Empfehlung und sollte deutlich UNTER der Obergrenze liegen; nur bei hoher \
Konfidenz (nahe 100%) ist eine Positionsgroesse nahe der vollen Obergrenze gerechtfertigt. \
Die Obergrenze selbst wird zusaetzlich serverseitig nach Konfidenz skaliert \
(deterministisch, nicht von dir zu berechnen).
4. Berechne den prozentualen Abstand jeder Zonen-Grenze (von UND bis) von Entry/Stop-Loss/ \
Take-Profit zum aktuellen Kurs EINMAL und wende ihn auf USD- UND EUR-Kurs gleichermassen an \
(keine unabhaengig erfundenen Werte je Waehrung).
5. `disclaimers` zeigt an, ob Makro/Sentiment einbezogen sind. Sind sie es nicht, muss \
das Feld `long_reasoning.makro` das explizit sagen - erfinde keine Makro-Einschaetzung.
6. Bei `asset.rolle == "core"` ODER einem taktischen Beobachtungs-/Wiedereinstiegs- \
Kandidaten (`asset.rolle == "taktisch"`, `asset.wird_aktuell_gehalten == false`, \
`asset.beobachtungsstatus == "beobachtung"`) wird KEINE aktive Trading-Position \
verfolgt, sondern eine langfristige Kernposition gehalten bzw. eine bewusste These \
beobachtet. Bewerte hier ZWEI GETRENNTE Ebenen: (a) die kurz-/mittelfristige technische \
Lage wie bei jedem Asset, UND (b) den Status der grundlegenden langfristigen Investment- \
These. Fuer Rohstoffe ist ein echter Bruch von (b) z.B.: ein struktureller Nachfrage- \
Einbruch durch Substitution (z.B. Kupfer durch Aluminium in bestimmten Anwendungen), \
ein grundlegendes Ende einer Angebotsverknappung, oder ein Emittenten-/Kontrahenten- \
Risiko beim ETC selbst (falls in den Fakten erwaehnt). Kurzfristige Kursschwaeche, \
ein schwacher technischer Trend, oder eine einzelne COT-Positionierungs-Verschiebung \
allein sind KEIN Bruch. Empfiehl VERKAUFEN (bzw. bei einem noch nicht gehaltenen \
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
Einordnung, keine harte Regel. Bei `unbekannt` (zu wenig Historie) einfach nicht \
erwaehnen. Beziehe zusaetzlich `regime.aktien_baermarkt.aktiv` ein, falls true - ein \
Aktien-Baermarkt geht historisch oft mit erhoehter Safe-Haven-Nachfrage nach Gold/ \
Silber einher (fuer Kupfer/Erdgas dagegen eher neutral bis leicht belastend, da \
Aktien-Baermaerkte oft mit schwaecherer Industriekonjunktur zusammenfallen) - \
gewichte je nach `asset.symbol` entsprechend unterschiedlich, wie bei Fakt 9. Beziehe \
zusaetzlich `regime.vix.wert`/`regime.vix.label` ein, falls `label` nicht "nicht \
verfuegbar" ist - ein VORLAUFENDES Optionsmarkt-Stimmungssignal (im Gegensatz zum \
nachlaufenden `aktien_baermarkt`-Drawdown-Flag). "gestresst"/"krise" verstaerkt bei \
Gold/Silber tendenziell die Safe-Haven-Logik oben, bei Kupfer/Erdgas eher neutral - \
formuliere vorsichtig, keine harte Kausalitaet behaupten.
9. `makro_ueberlagerung`-Regel: `realrendite_10j_prozent` (10-Jahres-TIPS-Realrendite) \
ist historisch der staerkste Preistreiber fuer Gold/Silber - eine STEIGENDE Realrendite \
ist tendenziell belastend (Opportunitaetskosten des zinslosen Haltens steigen), eine \
FALLENDE/negative Realrendite tendenziell stuetzend. `dxy_proxy` (Dollar-Index) wirkt \
INVERS auf alle USD-notierten Rohstoffe (staerkerer Dollar = tendenziell belastend). \
`industrieproduktion_index` ist ein grober Nachfrage-Proxy speziell fuer INDUSTRIELLE \
Rohstoffe (Kupfer) - fuer Gold/Silber weniger relevant (primaer Wertspeicher-/ \
Absicherungs-Nachfrage, nicht Industrienachfrage), fuer Erdgas nur bedingt relevant \
(Nachfrage primaer heizungs-/wetterabhaengig, nicht industriell). Gewichte diesen Fakt \
je nach Rohstoff (`asset.symbol`) entsprechend unterschiedlich.
10. `positionierung`-Regel (CFTC-COT-Report, woechentlich, ca. 3 Tage Verzug bis \
Veroeffentlichung): `managed_money_long_anteil_oi_prozent` zeigt, wie stark grosse \
spekulative Fonds bereits long positioniert sind. Eine SEHR HOHE Zahl (grobe \
Orientierung: > 40%) deutet auf bereits "ueberfuellte" Long-Positionierung hin - ein \
Umkehr-/Enttaeuschungsrisiko bei negativen Nachrichten ist dann hoeher, da viele \
Positionen gleichzeitig glattgestellt werden koennten. Eine SEHR NIEDRIGE Zahl \
(< 15%) deutet auf wenig spekulatives Interesse hin - weder eindeutig bullisch noch \
bearisch allein, aber ein Kontext-Fakt. WICHTIG: dies ist ein GROBES Sentiment-Indiz, \
KEIN praezises Timing-Signal - extreme Positionierung kann sich ueber Monate halten, \
bevor sich der Kurs dreht. Nutze es als einen von mehreren Faktoren, nie als alleinige \
Kauf-/Verkaufs-Begruendung.
11. `action` MUSS EXAKT einer dieser vier Werte sein (Grossbuchstaben, keine Variante): \
KAUFEN, VERKAUFEN, HALTEN, NACHKAUFEN.
12. Entry/Stop-Loss/Take-Profit sind Kurszonen (von <= bis), abgeleitet aus echten, \
gelieferten Referenzpunkten (`technische_analyse.atr.wert`, \
`technische_analyse.support_resistance`, `technische_analyse.fibonacci`) - KEINE frei \
geratene Bandbreite. Siehe Regel 3 fuer die daran gekoppelte CRV-Pflicht.
13. Fuelle zusaetzlich zu `long_reasoning` das Feld `top_gruende` mit GENAU 5 Eintraegen, \
sortiert von der staerksten zur schwaechsten Begruendung (rang 1 = staerkste, rang 5 = \
schwaechste, jede Zahl 1-5 genau einmal). Jeder Eintrag hat `rang` (1-5), `kategorie` \
(EXAKT einer von: technisch, positionierung, makro, risiko) und `text` (ein praegnanter \
Satz). `top_gruende` ersetzt NICHT `long_reasoning`, das weiterhin die volle \
Begruendung je Kategorie enthaelt.
14. Fuelle `halte_kriterium` zusaetzlich zum groben `bucket` (kurz|mittel|lang) mit \
mindestens EINEM konkreten, ueberpruefbaren Kriterium: einem Ziel-Kurs \
(`ziel_preis_usd`/`ziel_preis_eur`), einem Ziel-Datum (`ziel_datum`, Format YYYY-MM-DD) \
und/oder einer Bedingung als Text (`bedingung_text`). Mindestens eines der drei Felder \
MUSS gesetzt sein.
15. Antworte AUSSCHLIESSLICH mit einem einzigen JSON-Objekt gemaess dem vorgegebenen \
Schema. Kein Markdown, keine Code-Fences, kein Text ausserhalb des JSON.
16. `haltung.gewinn_verlust_pct` (falls nicht null) ist der aktuelle Gewinn/Verlust der \
bestehenden Position gegenueber dem echten Anschaffungspreis - niedrig gewichteter \
Kontext, KEINE harte Regel und KEIN Ersatz fuer die Stop-Loss-/CRV-Pflicht (Regel 3). \
Bei null: nicht erwaehnen.
17. Fuelle `gegenargument` IMMER zuerst aus, BEVOR du `confidence_pct` festlegst - formuliere \
darin das STAERKSTE Argument GEGEN deinen eigenen Vorschlag (nicht ein schwaches \
Feigenblatt-Gegenargument). Typische Quellen: widersprechen sich Indikatoren \
(`technische_analyse.confluence.gesamttendenz` == "gemischt")? Ist das Chance-Risiko-\
Verhaeltnis nur knapp ueber der Pflichtgrenze von 2.0? Ist die Managed-Money- \
Positionierung bereits ueberfuellt in dieselbe Richtung wie dein Vorschlag (siehe \
Regel 10)? `confidence_pct` MUSS das dort formulierte Gegenargument widerspiegeln - \
ein GENUIN starkes Gegenargument darf NICHT mit hoher Konfidenz (>75%) kombiniert werden.
18. Ist `historische_erfolgsquote` NICHT null, gibt sie die bisherige Trefferquote frueherer \
Signale wieder (`trefferquote_pct`, `anzahl_ausgewertete_signale`). Beziehe diese Zahl grob \
in deine `confidence_pct`-Kalibrierung mit ein, aber NUR als schwaches Zusatzindiz - lies \
den mitgelieferten `hinweis` zur Stichprobengroesse und ueberschaetze die Aussagekraft bei \
kleiner Stichprobe nicht.
19. Ist `historischer_makro_vergleich` NICHT null, listet er historische Kalendermonate mit \
einer AEHNLICHEN Makro-Konstellation (Dollarstaerke, Zinsen, Anleiherenditen, Oelpreis, \
Aktienbewertung) wie heute samt bekanntem weiteren Verlauf des S&P 500. Fuer Rohstoffe \
gilt dasselbe wie fuer Krypto: `spx_median_forward_*` beschreibt nur die Aktienmarkt- \
Tendenz der Analoge, ist bestenfalls ein grober Makro-Hintergrund (z.B. ueber die \
Dollarstaerke-Dimension der Konstellation indirekt relevant fuer Gold/Silber), KEIN \
direktes Rohstoff-Signal. Lies den mitgelieferten `hinweis`.
20. Ist `vorherige_empfehlung` NICHT null, wurde die letzte VERKAUFEN-Empfehlung fuer \
dieses Asset nachweislich nicht umgesetzt (Position wird laut `haltung` weiterhin gehalten). \
Wiederhole die Empfehlung nicht unveraendert, ohne diesen Umstand explizit in \
`long_reasoning` oder `key_risks` zu benennen - entweder nenne einen NEUEN, zusaetzlichen \
Grund, der seit der letzten Empfehlung hinzugekommen ist, oder erklaere ausdruecklich, \
warum die Empfehlung trotz Nicht-Umsetzung unveraendert bestehen bleibt.
21. `lagerbestaende` ist NUR fuer Erdgas gesetzt (sonst null - fuer Gold/Silber/Kupfer \
IMMER ignorieren, kein Erdgas-Aequivalent existiert dort). `letzte_woechentliche_aenderung_bcf` \
zeigt Build (positiv, tendenziell preisdaempfend) oder Draw (negativ, tendenziell \
preisstuetzend) - beziehe das NUR als schwachen Zusatzkontext ein, NICHT als \
alleinige Begruendung: ohne den fehlenden 5-Jahres-Saisonvergleich (siehe `hinweis`) \
laesst sich aus einem einzelnen Wert allein nicht sicher ableiten, ob eine Aenderung \
saisonal normal oder ungewoehnlich ist. Nutze bevorzugt den `verlauf_8_wochen`-Trend \
(z.B. mehrere Draws in Folge trotz Sommer) statt eines Einzelwerts.
18. Ist `these_abgleich` NICHT null, hat der Nutzer fuer die Kategorie dieses Assets \
(`these_abgleich.kategorie`) bewusst eine These gesetzt (`these_abgleich.richtung` + \
`these_abgleich.begruendung_nutzer`). `these_abgleich.objektive_einschaetzung` \
("gestuetzt"/"neutral"/"widerspricht"/"nicht_pruefbar") ist eine UNABHAENGIGE, \
FAKTENBASIERTE Gegenpruefung dieser These (siehe `objektive_begruendung` fuer die \
konkreten Rohwerte) - NICHT die Meinung des Nutzers selbst nachgeplappert. Kommentiere \
explizit, ob das aktuelle Setup die Nutzer-These stuetzt oder ihr widerspricht. \
WICHTIG: eine aktive These ist NIEMALS ein Grund, `action` staerker in Richtung der \
These zu verschieben, als es die uebrigen Fakten hergeben - besonders wichtig bei \
"widerspricht": das ist ein Warnsignal, keine zu ignorierende Nebeninfo.

SCHEMA:
{
  "action": "KAUFEN|VERKAUFEN|HALTEN|NACHKAUFEN",
  "gegenargument": "<das staerkste Argument GEGEN diesen Vorschlag, siehe Regel 17>",
  "confidence_pct": <0-100>,
  "short_reasoning": "<1-2 Saetze>",
  "top_gruende": [
    {"rang": 1, "kategorie": "technisch|positionierung|makro|risiko", "text": "<Text>"},
    {"rang": 2, "kategorie": "technisch|positionierung|makro|risiko", "text": "<Text>"},
    {"rang": 3, "kategorie": "technisch|positionierung|makro|risiko", "text": "<Text>"},
    {"rang": 4, "kategorie": "technisch|positionierung|makro|risiko", "text": "<Text>"},
    {"rang": 5, "kategorie": "technisch|positionierung|makro|risiko", "text": "<Text>"}
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
    """Mirror agent/aktien/analyst.py::_build_haltung_facts() - identisch, da
    compute_cost_basis_view() bereits assetklassen-neutral ist."""
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
    makro_ueberlagerung: dict | None,
    positionierung: dict | None,
    price_age_minutes: float | None,
    historische_erfolgsquote: dict | None = None,
    historischer_makro_vergleich: dict | None = None,
    letztes_signal=None,
    lagerbestaende: dict | None = None,
    these_abgleich: dict | None = None,
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

    wird_aktuell_gehalten = bool(
        holding and ((holding.quantity or 0.0) + (holding.staked_quantity or 0.0)) > 0.0
    )
    vorherige_empfehlung_fact = build_wiederholung_fact(
        letztes_signal, wird_aktuell_gehalten, relevante_aktionen=_WIEDERHOLUNG_RELEVANTE_AKTIONEN,
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
        "vorherige_empfehlung": vorherige_empfehlung_fact,
        "historische_erfolgsquote": historische_erfolgsquote,
        "historischer_makro_vergleich": historischer_makro_vergleich,
        "makro_ueberlagerung": makro_ueberlagerung,
        "positionierung": positionierung,
        "lagerbestaende": lagerbestaende,
        # Kategorie-These-Abgleich (2026-07-19, Release 2) - siehe
        # agent/kategorie_thesen.py::build_these_abgleich_fact().
        "these_abgleich": these_abgleich,
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
            # Nachtrag 2026-07-18: fehlte urspruenglich (Krypto/Aktien/Hedge geben
            # diesen Fakt bereits weiter) - fuer Gold/Silber als "Krisen-/Safe-Haven"-
            # Rohstoffe eine relevante Zusatzeinordnung, siehe SYSTEM_PROMPT Regel 8.
            "aktien_baermarkt": {
                "aktiv": regime_result.equities_baermarkt_aktiv,
                "begruendung": regime_result.equities_baermarkt_begruendung,
            },
            # VIX-Fruehindikator (2026-07-18) - siehe SYSTEM_PROMPT Regel 8.
            "vix": {
                "wert": _native(regime_result.vix_wert),
                "label": regime_result.vix_label,
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
            "sentiment_einbezogen": True,
            "hinweis": (
                "Makro ist NUR teilweise einbezogen: Realrendite/Dollar-Index/"
                "Industrieproduktion (makro_ueberlagerung) + globaler Liquiditaets-Trend "
                "(regime.liquiditaets_regime). Positionierung (CFTC-COT, woechentlich, "
                "~3 Tage Verzug) ist ein Sentiment-Proxy, kein Nachrichten-Sentiment. "
                "Lagerbestaende sind NUR fuer Erdgas einbezogen (EIA Weekly Storage "
                "Report, siehe lagerbestaende) - LME-/COMEX-Metallvorraete und ETF-"
                "Gold-/Silber-Bestandsfluesse sind weiterhin NICHT einbezogen (siehe "
                "Regelwerksmanual-Nachtrag - bewusst zurueckgestellt). WICHTIG: "
                "technische_analyse basiert auf dem liquiden Futures-Kontrakt, den "
                "dieses ETC nachbildet (nicht auf der eigenen, duenn gehandelten "
                "Boersennotierung des ETC selbst, fuer die keine Kurshistorie verfuegbar "
                "ist) - preis.usd/eur ist dagegen der ECHTE ETC-Kurs. Kleine "
                "Tracking-Differenzen (Rollkosten, Waehrungsabsicherung, Emittenten-"
                "Marge) zwischen Future und ETC sind moeglich - Entry/Stop/Take-Profit-"
                "Zonen sind daher als PROZENTUALER Abstand vom aktuellen ETC-Kurs zu "
                "verstehen (siehe Regel 4), nicht als literale Future-Preise."
            ),
        },
    }
    return facts


REQUIRED_TOP_LEVEL_FIELDS = (
    "action", "gegenargument", "confidence_pct", "short_reasoning", "top_gruende", "long_reasoning",
    "position_size", "entry", "stop_loss", "take_profit", "halte_kriterium",
    "key_risks", "forecast",
)

TOP_GRUENDE_KATEGORIEN = ("technisch", "positionierung", "makro", "risiko")
_HALTE_KRITERIUM_BUCKETS = ("kurz", "mittel", "lang")

# Halluzinations-Absicherung (mirror agent/aktien/analyst.py) - Begriffe, die im
# Rohstoff-Facts-JSON nie vorkommen (weder Krypto- noch Aktien-Konzepte).
_FREMDE_KONTAMINATIONS_BEGRIFFE = (
    "bitpanda-listing", "altseason", "btc-season", "baer_flucht", "mvrv", "nupl",
    "tauschen_target", "kgv", "forward-kgv", "dividendenrendite", "analysten-konsens",
    "earnings",
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
    for begriff in _FREMDE_KONTAMINATIONS_BEGRIFFE:
        if begriff in gesamt_text:
            raise AnalystResponseInvalid(
                f"Antwort erwaehnt fremdes Konzept '{begriff}' - existiert nicht im "
                "Rohstoff-Facts-JSON (Kreuzkontamination/Halluzination)"
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
    """Mirror agent/aktien/analyst.py::call_llm_for_signal() - identisches Retry-/
    Fail-Loud-Muster."""
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
