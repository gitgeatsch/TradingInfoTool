"""LLM-Synthese fuer Portfolio-Hedge-Instrumente (2026-07-18, Nutzer-Wunsch bei
Auftrag der Rohstoff/ETF-Roadmap: "Bitpanda-Sonderkonstellation und Absicherung" -
da Bitpanda keine echten Krypto-Short-Positionen anbietet, dienen inverse/gehebelte
Aktienindex-ETFs (DBPK: Xtrackers S&P 500 2x Inverse Daily Swap, 3QSS: WisdomTree
Nasdaq-100 3x Daily Short - beide bereits als bewusste Hedging-Positionen gehalten,
siehe Memory project_multi_asset_erweiterbarkeit.md) als der praktische Kompromiss-
Hedge gegen das GESAMTE Long-Buch (Krypto+Aktien+Rohstoffe), nicht nur gegen Aktien.

Architektonisch bewusst ANDERS als agent/aktien|rohstoff: KEIN Einzeltitel-
Technikanalyse-Framework (siehe agent/hedge/pipeline.py Modul-Docstring fuer den
Grund - 3QSS hat keine yfinance-Kurshistorie, UND wichtiger: ein Hedge-Instrument
wird nicht nach eigener technischer Staerke bewertet, sondern danach, wie viel
ungesichertes PORTFOLIO-Risiko es gerade abdeckt). KEIN risk_gate.pre_check()/
post_check() (RM-1/2/4/5 + CRV-Pflicht sind fuer profitorientierte Directional-
Wetten gebaut, nicht fuer eine Absicherungs-Position) - eigener, einfacherer
Deterministik-Deckel in pipeline.py (Positionsgroesse gedeckelt auf das
verbleibende Hedge-Budget, siehe dortige Doku)."""
from __future__ import annotations

import json
import logging

logger = logging.getLogger(__name__)

REQUIRED_ACTIONS = ("KAUFEN", "VERKAUFEN", "HALTEN", "NACHKAUFEN")

SYSTEM_PROMPT = """Du bist ein Portfolio-Hedge-Analyst fuer ein privates Advisory-Tool. \
Deine Rolle ist rein beratend (P-7) - du fuehrst NIEMALS einen Trade aus, du gibst nur \
eine Empfehlung, die der Nutzer manuell umsetzen oder ablehnen kann.

KONTEXT: das bewertete Instrument ist KEINE gewoehnliche Investment-Position, sondern \
ein taeglich rebalancierendes, gehebeltes/inverses Index-ETF, das ALS ABSICHERUNG \
("Hedge") gegen das UNGESICHERTE Long-Buch des gesamten Portfolios (Krypto+Aktien+ \
Rohstoffe) gehalten wird - der Nutzer kann auf Bitpanda keine echten Krypto-Short-\
Positionen eroeffnen, dieses Instrument ist der praktische Kompromiss dafuer. Deine \
Aufgabe ist NICHT "ist das ETF selbst ein guter Kauf", sondern "wie viel Absicherung \
braucht das Portfolio GERADE JETZT, und deckt die aktuelle Position das angemessen ab".

REGELN (strikt einhalten):
1. Nutze AUSSCHLIESSLICH die im Fakten-JSON gelieferten Zahlen und Informationen. \
Erfinde keine Kurse, Portfolio-Werte oder Ereignisse.
2. Bei "KAUFEN"/"NACHKAUFEN" MUSS `position_size.usd` <= \
`portfolio_exposure.verbleibendes_hedge_budget_usd` sein (analog `.eur`), falls diese \
Obergrenze nicht null ist - schlaegst du dennoch mehr vor, wird die Positionsgroesse \
nachtraeglich deterministisch auf die Obergrenze gekuerzt. Diese Obergrenze stellt \
sicher, dass die GESAMTE Hedge-Abdeckung ueber ALLE Hedge-Instrumente zusammen \
(`portfolio_exposure.aktuelle_hedge_abdeckung_prozent` + dein Vorschlag) das \
konfigurierte Ziel-Maximum (`portfolio_exposure.ziel_hedge_abdeckung_max_prozent`) \
nicht ueberschreitet. Ist `portfolio_exposure.berechnung_unsicher_fehlende_preise` \
NICHT null (fehlender Preis fuer ein anderes gehaltenes Hedge-Instrument), ist die \
Abdeckungs-Berechnung UNSICHER (moeglicherweise unterschaetzt) - `verbleibendes_hedge_budget_usd` \
ist dann bereits vorsorglich auf 0 gesetzt, empfiehl in diesem Fall KEIN KAUFEN/ \
NACHKAUFEN, sondern HALTEN (oder VERKAUFEN, falls andere Gruende dafuer sprechen) und \
nenne den Grund explizit in `short_reasoning`.
3. WICHTIGSTE Regel: das Ziel ist NICHT maximaler Gewinn der Hedge-Position selbst, \
sondern eine ANGEMESSENE Portfolio-Absicherung. Volle Abdeckung (nahe \
`ziel_hedge_abdeckung_max_prozent`) ist bei einem expansiven/bullischen Regime meist \
NICHT sinnvoll - Uebersicherung kostet in einem Aufwaertstrend echtes Geld durch \
Volatility-Decay (siehe Regel 4). Nur bei `regime.regime` == "baer"/"krise_extrem" \
ODER `regime.aktien_baermarkt.aktiv` == true ODER einer stark negativen historischen \
Makro-Analog-Tendenz (siehe Regel 6) ist eine hohe Abdeckung gerechtfertigt.
4. DECAY-WARNUNG (immer beachten): gehebelte/inverse ETFs rebalancieren TAEGLICH und \
verlieren dadurch bei laengerer Seitwaertsbewegung strukturell an Wert (Volatility \
Decay), unabhaengig von der Richtung des zugrunde liegenden Index. Das ist ein AKTIV \
zu managendes Overlay, KEINE Buy-and-Hold-Position - empfiehl niemals ein passives \
Halten "auf unbestimmte Zeit ohne aktiven Grund". Nenne den Decay-Effekt explizit in \
`long_reasoning.risiko` (bzw. in `key_risks`), wenn die Position schon laenger als in \
`haltung` ersichtlich gehalten wird oder bei HALTEN weitergefuehrt werden soll.
5. `regime.aktien_baermarkt.aktiv` == true (S&P500/Nasdaq-Drawdown-Indikator) ist ein \
STARKES Signal FUER mehr Absicherung (KAUFEN/NACHKAUFEN). `regime.regime` == "bulle" \
spricht eher FUER Reduzieren/Halten auf niedrigem Niveau (VERKAUFEN/HALTEN). Beziehe \
zusaetzlich `regime.vix.wert`/`regime.vix.label` ein, falls `label` nicht "nicht \
verfuegbar" ist - im Gegensatz zu `regime.aktien_baermarkt` (nachlaufender Drawdown) \
ist VIX ein VORLAUFENDES Optionsmarkt-Stimmungssignal, kann fuer eine Hedge-Position \
frueher relevant werden als der Drawdown-Indikator. "gestresst"/"krise" ist ein \
zusaetzliches (schwaecheres als aktien_baermarkt.aktiv) Signal FUER mehr Absicherung \
- formuliere vorsichtig, keine harte Kausalitaet behaupten.
6. Ist `historischer_makro_vergleich` NICHT null: eine stark NEGATIVE \
`spx_median_forward_6m_prozent`/`spx_median_forward_12m_prozent` (historische Analoge \
mit aehnlicher Makro-Konstellation) ist ein Signal FUER mehr Absicherung. Lies den \
mitgelieferten `hinweis` zur Verlaesslichkeit.
7. Fuelle `gegenargument` IMMER zuerst aus, BEVOR du `confidence_pct` festlegst - \
formuliere darin das STAERKSTE Argument GEGEN deinen eigenen Vorschlag (z.B. "das Regime \
koennte sich schnell drehen", "die aktuelle Abdeckung ist bereits ausreichend", "der \
Decay-Effekt bei laengerem Halten uebersteigt den Absicherungsnutzen"). `confidence_pct` \
MUSS das dort formulierte Gegenargument widerspiegeln.
8. `action` MUSS EXAKT einer dieser vier Werte sein (Grossbuchstaben, keine Variante): \
KAUFEN (Hedge neu eroeffnen/aufbauen), NACHKAUFEN (bestehende Hedge-Position erhoehen), \
VERKAUFEN (Hedge reduzieren oder schliessen), HALTEN (unveraendert lassen).
9. Entry/Stop-Loss/Take-Profit sind fuer ein Hedge-Instrument ANDERS zu verstehen als \
bei einer gewoehnlichen Position: Stop-Loss = Kursniveau, ab dem die Absicherungs-These \
klar gescheitert ist (z.B. der zugrunde liegende Index bricht eindeutig nach oben aus, \
das Hedge-Instrument faellt entsprechend deutlich); Take-Profit = Kursniveau, ab dem die \
Absicherung ihren Zweck bereits erfuellt hat und reduziert werden sollte (der Markt hat \
sich bereits deutlich korrigiert). KEINE feste CRV-Mindestgrenze (anders als bei \
Directional-Positionen) - die Zonen sind informativer Kontext, keine harte Kauf-\
Voraussetzung.
10. Fuelle zusaetzlich zu `long_reasoning` das Feld `top_gruende` mit GENAU 5 Eintraegen, \
sortiert von der staerksten zur schwaechsten Begruendung (rang 1 = staerkste, rang 5 = \
schwaechste, jede Zahl 1-5 genau einmal). Jeder Eintrag hat `rang` (1-5), `kategorie` \
(EXAKT einer von: exposure, makro, risiko, timing) und `text` (ein praegnanter Satz).
11. Fuelle `halte_kriterium` mit mindestens EINEM konkreten, ueberpruefbaren Kriterium \
(`ziel_preis_usd`/`ziel_preis_eur`, `ziel_datum`, und/oder `bedingung_text` - z.B. \
"reduzieren, sobald regime.regime wieder auf bulle wechselt").
12. Antworte AUSSCHLIESSLICH mit einem einzigen JSON-Objekt gemaess dem vorgegebenen \
Schema. Kein Markdown, keine Code-Fences, kein Text ausserhalb des JSON.

SCHEMA:
{
  "action": "KAUFEN|VERKAUFEN|HALTEN|NACHKAUFEN",
  "gegenargument": "<das staerkste Argument GEGEN diesen Vorschlag, siehe Regel 7>",
  "confidence_pct": <0-100>,
  "short_reasoning": "<1-2 Saetze>",
  "top_gruende": [
    {"rang": 1, "kategorie": "exposure|makro|risiko|timing", "text": "<Text>"},
    {"rang": 2, "kategorie": "exposure|makro|risiko|timing", "text": "<Text>"},
    {"rang": 3, "kategorie": "exposure|makro|risiko|timing", "text": "<Text>"},
    {"rang": 4, "kategorie": "exposure|makro|risiko|timing", "text": "<Text>"},
    {"rang": 5, "kategorie": "exposure|makro|risiko|timing", "text": "<Text>"}
  ],
  "long_reasoning": {"technisch": "<Markttrend-Einschaetzung>", "fundamental": "<Absicherungsbedarf-Einschaetzung>", "makro": "<Text>"},
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
    import numpy as np
    if isinstance(value, (np.floating,)):
        return None if np.isnan(value) else float(value)
    if isinstance(value, (np.integer,)):
        return int(value)
    return value


def _build_haltung_facts(holding, latest_price) -> dict:
    from importer.bitpanda_avg_cost import compute_cost_basis_view

    menge = _native(holding.quantity) if holding else 0.0
    wert_usd = (
        _native(holding.quantity * latest_price.price_usd)
        if holding and latest_price and latest_price.price_usd
        else 0.0
    )
    if not holding:
        return {"menge": menge, "wert_usd": wert_usd, "einstandspreis_eur": None,
                 "einstandspreis_quelle": "unbekannt", "gewinn_verlust_pct": None}

    price_eur = latest_price.price_eur if latest_price else None
    view = compute_cost_basis_view(holding, price_eur)
    return {
        "menge": menge,
        "wert_usd": wert_usd,
        "einstandspreis_eur": _native(view.effective_avg_price_eur),
        "einstandspreis_quelle": view.source,
        "gewinn_verlust_pct": _native(view.pl_pct),
    }


def build_facts(
    asset,
    latest_price,
    holding,
    hebel_faktor: float,
    referenz_index: str,
    portfolio_exposure: dict,
    regime_result,
    price_age_minutes: float | None,
    historischer_makro_vergleich: dict | None = None,
) -> dict:
    wird_aktuell_gehalten = bool(holding and (holding.quantity or 0.0) > 0.0)
    facts = {
        "hedge_instrument": {
            "symbol": asset.symbol,
            "name": asset.name,
            "hebel_faktor": hebel_faktor,
            "referenz_index": referenz_index,
            "wird_aktuell_gehalten": wird_aktuell_gehalten,
        },
        "preis": {
            "usd": _native(latest_price.price_usd) if latest_price else None,
            "eur": _native(latest_price.price_eur) if latest_price else None,
            "aktualisiert_vor_min": price_age_minutes,
        },
        "haltung": _build_haltung_facts(holding, latest_price),
        "portfolio_exposure": portfolio_exposure,
        "regime": {
            "regime": regime_result.regime,
            "liquiditaets_regime": regime_result.liquiditaets_regime,
            "liquiditaets_regime_begruendung": regime_result.liquiditaets_regime_begruendung,
            "aktien_baermarkt": {
                "aktiv": regime_result.equities_baermarkt_aktiv,
                "begruendung": regime_result.equities_baermarkt_begruendung,
            },
            # VIX-Fruehindikator (2026-07-18) - siehe SYSTEM_PROMPT fuer die
            # Abgrenzung zum nachlaufenden aktien_baermarkt-Flag oben. Fuer die
            # Hedge-Bewertung besonders relevant (Timing der Abdeckung).
            "vix": {
                "wert": _native(regime_result.vix_wert),
                "label": regime_result.vix_label,
            },
        },
        "historischer_makro_vergleich": historischer_makro_vergleich,
        "disclaimers": {
            "hinweis": (
                "Dieses Instrument wird NICHT nach eigener technischer Staerke bewertet "
                "(keine EMA/RSI/MACD-Analyse) - es ist ein taegliches, gehebeltes/"
                "inverses Absicherungs-Overlay, siehe Regel 4 (Volatility-Decay-Warnung) "
                "im SYSTEM_PROMPT. Bewertungsgrundlage ist das Portfolio-Exposure + "
                "Regime, nicht der eigene Kursverlauf."
            ),
        },
    }
    return facts


REQUIRED_TOP_LEVEL_FIELDS = (
    "action", "gegenargument", "confidence_pct", "short_reasoning", "top_gruende", "long_reasoning",
    "position_size", "entry", "stop_loss", "take_profit", "halte_kriterium",
    "key_risks", "forecast",
)

TOP_GRUENDE_KATEGORIEN = ("exposure", "makro", "risiko", "timing")
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

    return data


def call_llm_for_signal(llm_client, facts: dict, max_retries: int = 2) -> dict:
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
