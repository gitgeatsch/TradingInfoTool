"""Kann ein STRIKTES Schema die Dauer senken - und die Fehlschlaege beseitigen?

BEFUND, DER DAZU FUEHRT: im 20er-Durchsatztest scheiterten 3 von 4 Fehlschlaegen
an derselben Stelle - `halte_kriterium.bucket` war `None` statt
"kurz"|"mittel"|"lang". Das ist kein Zufallsfehler, sondern eine Regel, die das
Modell nur aus dem Prompttext kennt. Wir senden heute
`response_format={"type":"json_object"}` - das heisst nur "irgendein gueltiges
JSON", nicht "DIESES Schema".

Der Endpunkt fuehrt `structured_outputs` in seinen unterstuetzten Parametern.
Damit laesst sich das Vokabular erzwingen statt erbitten.

ZWEI WIRKUNGEN WAEREN MOEGLICH, und beide werden hier getrennt gemessen:
  1. weniger Fehlschlaege (die Enum-Verletzung kann nicht mehr entstehen)
  2. weniger DAUER - nicht weil ein Call schneller wird, sondern weil der
     zweite Versuch entfaellt. Bei 1,31 Versuchen/Fall sind rund 24 % der
     Wartezeit reine Wiederholung.

Gegenprobe eingebaut: dieselben Faelle, gleiche Reihenfolge, nur der eine
Parameter verstellt. Ohne die Kontrolle misst der Test sich selbst.
"""
import json
import os
import pathlib
import shutil
import sys
import time

from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, r"D:\CLAUDE_Projects\SoftwareProjekte\TradingInfoTool")
os.chdir(r"D:\CLAUDE_Projects\SoftwareProjekte\TradingInfoTool")

import database.db as db  # noqa: E402

_KOPIE = pathlib.Path(os.environ["TEMP"]) / "tit_haertetest.db"
if not _KOPIE.exists():
    shutil.copy2("data/tradinginfotool.db", _KOPIE)
db.DB_PATH = _KOPIE

import agent.krypto.hebel_analyst as H  # noqa: E402
from api.openrouter import OpenRouterClient  # noqa: E402

SCRATCH = pathlib.Path(__file__).parent
N = int(sys.argv[1]) if len(sys.argv) > 1 else 5
MODELL = sys.argv[2] if len(sys.argv) > 2 else "nvidia/nemotron-3-super-120b-a12b:free"

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

daten = json.load(open(SCRATCH / "fakten_hebel_faktensaetze.json", encoding="utf-8"))
faelle = sorted((e for e in daten["eintraege"] if e.get("facts_json")),
                key=lambda e: e["created_at"], reverse=True)[:N]


class Fest:
    """Erzwingt Modell UND response_format - der Aufrufer (call_llm_for_hebel_
    signal) setzt sonst sein eigenes json_object und ueberschriebe den Test."""

    def __init__(self, inner, model, rf):
        self.inner, self.model, self.rf, self.calls = inner, model, rf, 0

    def chat(self, messages, **kw):
        self.calls += 1
        kw["model"] = self.model
        kw["response_format"] = self.rf
        return self.inner.chat(messages, **kw)


client = OpenRouterClient(api_key=os.environ["OPENROUTER_API_KEY"])
VARIANTEN = [
    ("A json_object (heute)", {"type": "json_object"}),
    ("B json_schema strict", {"type": "json_schema", "json_schema": {
        "name": "hebel_signal", "strict": True, "schema": SCHEMA}}),
]

print(f"Modell: {MODELL}\nFaelle: {len(faelle)}\n")
for name, rf in VARIANTEN:
    zeiten, ok, versuche = [], 0, 0
    gruende = []
    for i, f in enumerate(faelle, 1):
        h = Fest(client, MODELL, rf)
        t = time.monotonic()
        try:
            H.call_llm_for_hebel_signal(h, json.loads(f["facts_json"]), max_retries=1)
            d = time.monotonic() - t
            ok += 1
            zeiten.append(d)
            print(f"  {i:>2}. {f['symbol']:<9} OK   {d:>6.1f}s  {h.calls} Versuch(e)", flush=True)
        except Exception as exc:  # noqa: BLE001
            d = time.monotonic() - t
            gruende.append(f"{type(exc).__name__}: {str(exc)[:90]}")
            print(f"  {i:>2}. {f['symbol']:<9} FEHL {d:>6.1f}s  {h.calls} Versuch(e)  "
                  f"{type(exc).__name__}: {str(exc)[:80]}", flush=True)
        versuche += h.calls
    med = sorted(zeiten)[len(zeiten) // 2] if zeiten else 0
    print(f"  => {name}: {ok}/{len(faelle)} gueltig, Median {med:.1f}s, "
          f"{versuche/len(faelle):.2f} Versuche/Fall\n", flush=True)
