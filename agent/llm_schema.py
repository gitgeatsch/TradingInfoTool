"""Strikte JSON-Schemata, ABGELEITET aus den Validator-Konstanten (2026-08-09).

WARUM ABGELEITET UND NICHT GESCHRIEBEN: es gibt neun Ausgabeformen. Neun von
Hand gepflegte Schemata neben neun Validatoren sind neun Gelegenheiten
auseinanderzulaufen - und ein Schema, das vom Validator abweicht, ERZEUGT
Fehler, statt sie zu verhindern. Es erzwingt dann ein Vokabular, das der
Validator hinterher ablehnt. Deshalb liest dieses Modul dieselben Konstanten,
die auch der Validator benutzt: `REQUIRED_TOP_LEVEL_FIELDS`,
`REQUIRED_ACTIONS`, `TOP_GRUENDE_KATEGORIEN`, `_HALTE_KRITERIUM_BUCKETS`,
`_EIGENE_EINSCHAETZUNG_FOLGEN_WERTE`. Eine Quelle, kein Abgleichproblem.

WAS EIN STRIKTES SCHEMA LEISTET - und was nicht. Es erzwingt Struktur und
Vokabular. Genau dort lagen die realen Fehlschlaege: im 20er-Durchsatztest vom
08.08. scheiterten 3 von 4 Faellen an derselben Stelle, `halte_kriterium.bucket`
war `None` statt "kurz"|"mittel"|"lang" - eine Regel, die das Modell bis dahin
nur aus dem Prompttext kannte. Es leistet NICHT, dass das Urteil besser wird,
und es beseitigt keinen Positions-Bias im EINGABE-Fakten-JSON (siehe
agent/krypto/gegenpruefung.py::leite_eigene_richtung_positionsrobust()) - der
liegt vor dem Output und bleibt unberuehrt.

Die sechs Signal-Analysten (Krypto-Spot, Hebel, Aktien, Rohstoffe, Themen-ETF,
Hedge) folgen strukturell demselben Bauplan und werden von
`baue_signal_schema()` bedient. Die zwei Gegenpruefungs-Formen sind winzig und
haben eigene Bauer. Die Kategorie-Synthese fuehrt keine Pflichtfeld-Konstanten
und ist deshalb bewusst NICHT hier - sie waere geraten, nicht abgeleitet.
"""
from __future__ import annotations

# --- Bausteine --------------------------------------------------------------
TXT = {"type": "string"}
TXTN = {"type": ["string", "null"]}
NUM = {"type": ["number", "null"]}
_SPANNE = {"type": "object", "properties": {
    "usd_von": NUM, "usd_bis": NUM, "eur_von": NUM, "eur_bis": NUM}}
_SZENARIO = {"type": "object", "properties": {
    "scenario": TXT, "probability_pct": {"type": "number"}}}


def _top_gruende(kategorien) -> dict:
    return {
        "type": "array", "minItems": 5, "maxItems": 5,
        "items": {
            "type": "object",
            "properties": {
                "rang": {"type": "integer", "minimum": 1, "maximum": 5},
                "kategorie": {"type": "string", "enum": sorted(kategorien)},
                "text": TXT,
            },
            "required": ["rang", "kategorie", "text"],
        },
    }


def _halte_kriterium(buckets) -> dict:
    return {
        "type": "object",
        "properties": {
            # GENAU HIER lagen 3 von 4 Fehlschlaegen im 20er-Test vom 08.08.
            # Jetzt erzwungen statt erbeten.
            "bucket": {"type": "string", "enum": sorted(buckets)},
            "ziel_preis_usd": NUM, "ziel_preis_eur": NUM,
            "ziel_datum": TXTN, "bedingung_text": TXTN, "reasoning": TXT,
        },
        "required": ["bucket", "reasoning"],
    }


def _eigene_einschaetzung(werte) -> dict:
    return {
        "type": "object",
        "properties": {
            "folgen": {"type": "string", "enum": sorted(werte)},
            "kurzfazit": TXT,
        },
        "required": ["folgen", "kurzfazit"],
    }


_FORECAST = {
    "type": "object",
    "properties": {"bull": _SZENARIO, "base": _SZENARIO, "bear": _SZENARIO},
    "required": ["bull", "base", "bear"],
}
_POSITION_SIZE = {"type": "object", "properties": {
    "usd": NUM, "eur": NUM, "note": TXTN}}


class SchemaLuecke(RuntimeError):
    """Ein Pflichtfeld hat keine bekannte Form.

    ABSICHTLICH EIN FEHLER, KEIN STILLER RUECKFALL auf `{}`: ein permissives
    Teilschema fuer ein unbekanntes Feld sieht aus wie Abdeckung und ist keine.
    Wer ein Feld zu REQUIRED_TOP_LEVEL_FIELDS hinzufuegt, soll hier anecken und
    entscheiden, welche Form es hat."""


def baue_signal_schema(analyst_modul) -> dict:
    """Strikte Schema-Definition fuer einen der sechs Signal-Analysten.

    Liest ausschliesslich Konstanten aus `analyst_modul`. Hebel fuehrt seine
    unter abweichenden Namen (`REQUIRED_HEBEL_*`) - beide Schreibweisen werden
    akzeptiert, damit kein Analyst umbenannt werden muss."""
    M = analyst_modul
    pflichtfelder = getattr(M, "REQUIRED_HEBEL_TOP_LEVEL_FIELDS", None) \
        or getattr(M, "REQUIRED_TOP_LEVEL_FIELDS")
    actions = getattr(M, "REQUIRED_HEBEL_ACTIONS", None) \
        or getattr(M, "REQUIRED_ACTIONS")

    bekannt = {
        "action": {"type": "string", "enum": sorted(actions)},
        "richtung": {"type": "string", "enum": ["LONG", "SHORT"]},
        "gegenargument": TXT,
        "confidence_pct": {"type": "number"},
        "short_reasoning": TXT,
        "hebel_vorschlag": NUM,
        "top_gruende": _top_gruende(M.TOP_GRUENDE_KATEGORIEN),
        # Freitext-Struktur, bewusst offen: der Validator prueft hier nur, DASS
        # ein Objekt kommt. Ein erfundenes Teilschema waere strenger als die
        # Regel, die es abbilden soll.
        "long_reasoning": {"type": "object"},
        "position_size": _POSITION_SIZE,
        "entry": _SPANNE, "stop_loss": _SPANNE, "take_profit": _SPANNE,
        "halte_kriterium": _halte_kriterium(M._HALTE_KRITERIUM_BUCKETS),
        "key_risks": {"type": "array", "items": TXT},
        "forecast": _FORECAST,
        "eigene_einschaetzung": _eigene_einschaetzung(M._EIGENE_EINSCHAETZUNG_FOLGEN_WERTE),
    }
    if hasattr(M, "_TRADE_THESIS_TYPEN"):
        bekannt["trade_thesis_typ"] = {
            "type": "string", "enum": sorted(M._TRADE_THESIS_TYPEN)}

    fehlend = [f for f in pflichtfelder if f not in bekannt]
    if fehlend:
        raise SchemaLuecke(
            f"{M.__name__}: keine Form hinterlegt fuer {fehlend}. In "
            f"agent/llm_schema.py::baue_signal_schema() ergaenzen - ein "
            f"permissives Teilschema waere Scheinabdeckung.")

    return {
        "type": "object",
        "properties": {f: bekannt[f] for f in pflichtfelder},
        "required": list(pflichtfelder),
    }


def baue_konsistenz_schema(gegenpruefung_modul) -> dict:
    """Konsistenz-Check der Gegenpruefung: {urteil, kurzbegruendung}."""
    return {
        "type": "object",
        "properties": {
            "urteil": {"type": "string",
                       "enum": sorted(gegenpruefung_modul._GUELTIGE_URTEILE)},
            "kurzbegruendung": TXTN,
        },
        "required": ["urteil"],
    }


def baue_richtung_schema(gegenpruefung_modul) -> dict:
    """Richtungs-Abgleich der Gegenpruefung: {eigene_richtung, kurzbegruendung}."""
    return {
        "type": "object",
        "properties": {
            "eigene_richtung": {
                "type": "string",
                "enum": sorted(gegenpruefung_modul._GUELTIGE_RICHTUNGEN)},
            "kurzbegruendung": TXTN,
        },
        "required": ["eigene_richtung"],
    }


def als_response_format(schema: dict, name: str) -> dict:
    """Verpackt ein Schema so, wie die OpenAI-kompatiblen Endpunkte es
    erwarten. Alle fuenf Clients reichen `response_format` unveraendert durch."""
    return {"type": "json_schema",
            "json_schema": {"name": name, "strict": True, "schema": schema}}
