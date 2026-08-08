"""Nur die Schema-Definition - KEIN Testlauf.

Warum eigene Datei: `rueckspiel.py` braucht dasselbe Schema. Ein
`from schema_test import SCHEMA` haette den kompletten Schema-Test erneut
ausgefuehrt, weil schema_test.py ein flaches Skript ohne __main__-Schutz ist -
also 10 echte LLM-Calls als Nebenwirkung eines Imports.
"""
import agent.krypto.hebel_analyst as H

S = lambda *_: {"type": "string"}          # noqa: E731
NUM = {"type": ["number", "null"]}
TXT = {"type": "string"}
TXTN = {"type": ["string", "null"]}
SPANNE = {"type": "object", "properties": {
    "usd_von": NUM, "usd_bis": NUM, "eur_von": NUM, "eur_bis": NUM}}
SZEN = {"type": "object", "properties": {
    "scenario": TXT, "probability_pct": {"type": "number"}}}

SCHEMA = {
    "type": "object",
    "properties": {
        "richtung": {"type": "string", "enum": ["LONG", "SHORT"]},
        "action": {"type": "string", "enum": sorted(H.REQUIRED_HEBEL_ACTIONS)},
        "gegenargument": TXT,
        "confidence_pct": {"type": "number"},
        "short_reasoning": TXT,
        "hebel_vorschlag": NUM,
        "trade_thesis_typ": {"type": "string",
                             "enum": sorted(getattr(H, "_TRADE_THESIS_TYPEN", ("einmaltrade", "swing")))},
        "top_gruende": {"type": "array", "minItems": 5, "maxItems": 5, "items": {
            "type": "object",
            "properties": {
                "rang": {"type": "integer", "minimum": 1, "maximum": 5},
                "kategorie": {"type": "string", "enum": sorted(H.TOP_GRUENDE_KATEGORIEN)},
                "text": TXT},
            "required": ["rang", "kategorie", "text"]}},
        "long_reasoning": {"type": "object"},
        "entry": SPANNE, "stop_loss": SPANNE, "take_profit": SPANNE,
        "halte_kriterium": {
            "type": "object",
            "properties": {
                # GENAU HIER lag der Fehlschlag - jetzt erzwungen statt erbeten.
                "bucket": {"type": "string", "enum": sorted(H._HALTE_KRITERIUM_BUCKETS)},
                "ziel_preis_usd": NUM, "ziel_preis_eur": NUM,
                "ziel_datum": TXTN, "bedingung_text": TXTN, "reasoning": TXT},
            "required": ["bucket", "reasoning"]},
        "key_risks": {"type": "array", "items": TXT},
        "forecast": {"type": "object", "properties": {
            "bull": SZEN, "base": SZEN, "bear": SZEN},
            "required": ["bull", "base", "bear"]},
        "eigene_einschaetzung": {"type": "object", "properties": {
            "folgen": {"type": "string", "enum": sorted(H._EIGENE_EINSCHAETZUNG_FOLGEN_WERTE)},
            "kurzfazit": TXT},
            "required": ["folgen", "kurzfazit"]},
    },
    "required": list(H.REQUIRED_HEBEL_TOP_LEVEL_FIELDS),
}

