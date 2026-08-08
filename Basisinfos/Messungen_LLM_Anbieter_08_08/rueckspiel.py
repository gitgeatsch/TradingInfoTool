"""HISTORISCHER RUECKTEST: dieselben Faktensaetze, andere Modelle, bekannter Ausgang.

DIE IDEE (Nutzer, 08.08.): wir haben 38 echte Hebel-Entscheidungen, die Mistral
getroffen hat und deren Ausgang feststeht - 35 Verlierer, 3 Gewinner, Summe
-27,38 R. Wir spielen exakt dieselben Faktensaetze durch die Kandidaten und
sehen, wer welche Falle vermieden haette.

DIE FALLE IM TEST SELBST: bei 35 Verlierern gegen 3 Gewinner gewinnt ein
Modell, das IMMER "HALTEN" sagt, mit 0,00 R gegen -27,38 R - und waere
trotzdem wertlos. Dieselbe Familie wie "MFE >= 1R belohnt enge Stops".
Deshalb vier Kennzahlen statt einer, und die HALTEN-Quote steht gleichwertig
daneben, nicht im Kleingedruckten.

ZWEI EINSCHRAENKUNGEN, die ins Ergebnis gehoeren:
  * Gespielt wird mit dem HEUTIGEN SYSTEM_PROMPT. Die Antwort lautet also
    "was entscheidet das heutige System mit Modell X", nicht "was haette
    Mistral anders gemacht". Fuer die Anbieterwahl ist das die nuetzlichere
    Frage - aber es ist eine andere.
  * Die 35:3-Schieflage ist ein Auswertungsartefakt (Verlierer laufen in den
    Stop und sind fertig, Gewinner bleiben offen). Gemessen wird damit vor
    allem "schlechte Einstiege vermeiden", nicht "gute finden".

GLEICHE ZUEGEL FUER ALLE: alle Modelle bekommen dasselbe response_format.
Bekaeme OpenRouter ein erzwungenes Schema und Gemini nicht, wuerde der
Vergleich zum Teil den Unterschied der Zuegel messen statt den der Modelle.

KEINE Produktiv-DB.
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

from agent.krypto.hebel_analyst import call_llm_for_hebel_signal  # noqa: E402
from api.gemini import GeminiClient  # noqa: E402
from api.openrouter import OpenRouterClient  # noqa: E402

SCRATCH = pathlib.Path(__file__).parent
sig = {s["id"]: s for s in json.load(open(SCRATCH / "fakten_hebel_signals.json", encoding="utf-8"))}
fak = json.load(open(SCRATCH / "fakten_hebel_faktensaetze.json", encoding="utf-8"))["eintraege"]
GOLD = [f for f in fak
        if f.get("facts_json") and sig.get(f["id"], {}).get("outcome_realisiertes_crv") is not None]

MISTRAL_R = sum(sig[f["id"]]["outcome_realisiertes_crv"] for f in GOLD)


class Fest:
    def __init__(self, inner, model=None, rf=None):
        self.inner, self.model, self.rf, self.calls = inner, model, rf, 0

    def chat(self, messages, **kw):
        self.calls += 1
        if self.model:
            kw["model"] = self.model
        if self.rf:
            kw["response_format"] = self.rf
        return self.inner.chat(messages, **kw)


def gemini_kann_schema() -> bool:
    """Nimmt Geminis OpenAI-kompatibler Endpunkt ein json_schema an? Entscheidet,
    welches Format ALLE bekommen - gemischt waere der Vergleich wertlos."""
    try:
        g = GeminiClient(api_key=os.environ["GEMINI_API_KEY"])
        g.chat([{"role": "user", "content": 'Gib {"a":1} zurueck.'}],
               response_format={"type": "json_schema", "json_schema": {
                   "name": "t", "strict": True,
                   "schema": {"type": "object", "properties": {"a": {"type": "integer"}},
                              "required": ["a"]}}})
        return True
    except Exception as exc:  # noqa: BLE001
        print(f"  Gemini nimmt json_schema NICHT an ({str(exc)[:90]})")
        return False


NUTZE_SCHEMA = "--schema" in sys.argv and gemini_kann_schema()
if NUTZE_SCHEMA:
    from hebel_schema import SCHEMA  # eigene Datei - ein Import von schema_test
                                     # haette den kompletten Schema-Test erneut
                                     # ausgefuehrt (flaches Skript, kein __main__)
    RF = {"type": "json_schema", "json_schema": {"name": "hebel_signal",
                                                 "strict": True, "schema": SCHEMA}}
else:
    RF = {"type": "json_object"}

or_key = os.environ["OPENROUTER_API_KEY"]
KANDIDATEN = [
    ("gemini", lambda: Fest(GeminiClient(api_key=os.environ["GEMINI_API_KEY"]), None, RF)),
    ("nemotron-super-120b",
     lambda: Fest(OpenRouterClient(api_key=or_key), "nvidia/nemotron-3-super-120b-a12b:free", RF)),
    ("laguna-xs-2.1",
     lambda: Fest(OpenRouterClient(api_key=or_key), "poolside/laguna-xs-2.1:free", RF)),
]

print(f"{len(GOLD)} Faelle mit bekanntem Ausgang, alle von Mistral, alle EROEFFNEN")
print(f"Mistral tatsaechlich: {MISTRAL_R:+.2f} R  <- die Zahl zum Schlagen")
print(f"response_format fuer ALLE: {RF['type']}\n")

ergebnis = {}
for name, bauen in KANDIDATEN:
    print(f"--- {name}", flush=True)
    zeilen = []
    for i, f in enumerate(GOLD, 1):
        s = sig[f["id"]]
        crv = s["outcome_realisiertes_crv"]
        h = bauen()
        t = time.monotonic()
        try:
            r = call_llm_for_hebel_signal(h, json.loads(f["facts_json"]), max_retries=1)
            eroeffnet = r["action"] == "ERÖFFNEN"
            zeilen.append({"symbol": f["symbol"], "ok": True, "action": r["action"],
                           "richtung": r["richtung"], "konfidenz": r.get("confidence_pct"),
                           "eroeffnet": eroeffnet, "crv": crv,
                           "beitrag": crv if eroeffnet else 0.0,
                           "dauer": time.monotonic() - t})
            print(f"  {i:>2}. {f['symbol']:<9} {r['richtung']}/{r['action']:<12} "
                  f"{str(r.get('confidence_pct')):>5}%  ist {crv:+.2f} R  "
                  f"-> {'NIMMT' if eroeffnet else 'meidet'}", flush=True)
        except Exception as exc:  # noqa: BLE001
            zeilen.append({"symbol": f["symbol"], "ok": False, "crv": crv,
                           "grund": f"{type(exc).__name__}: {str(exc)[:80]}"})
            print(f"  {i:>2}. {f['symbol']:<9} FEHL {type(exc).__name__}", flush=True)
    ergebnis[name] = zeilen

    gueltig = [z for z in zeilen if z["ok"]]
    if gueltig:
        genommen = [z for z in gueltig if z["eroeffnet"]]
        verlierer = [z for z in gueltig if z["crv"] < 0]
        gewinner = [z for z in gueltig if z["crv"] > 0]
        print(f"\n  Auswertbar        {len(gueltig)}/{len(GOLD)}")
        print(f"  Hypothetische R   {sum(z['beitrag'] for z in genommen):+.2f} R   "
              f"(Mistral {MISTRAL_R:+.2f} R)")
        print(f"  Verluste vermieden {sum(1 for z in verlierer if not z['eroeffnet'])}"
              f"/{len(verlierer)}")
        print(f"  Gewinne verpasst   {sum(1 for z in gewinner if not z['eroeffnet'])}"
              f"/{len(gewinner)}")
        print(f"  HALTEN-Quote       {sum(1 for z in gueltig if not z['eroeffnet'])/len(gueltig):.0%}"
              f"   <- bei 100 % ist die R-Zahl wertlos")
        print(f"  Median Dauer       {sorted(z['dauer'] for z in genommen or gueltig)[len(gueltig)//2]:.1f}s\n",
              flush=True)

json.dump({"mistral_r": MISTRAL_R, "format": RF["type"], "ergebnis": ergebnis},
          open(SCRATCH / "rueckspiel.json", "w"), ensure_ascii=False, indent=1)
print("geschrieben: rueckspiel.json")
