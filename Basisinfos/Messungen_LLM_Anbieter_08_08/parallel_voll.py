"""VOLLLAST-PARALLELMESSUNG: halten 8 gleichzeitige Anfragen auch bei
16.656 Token je Anfrage?

Warum die Kurzfragen-Messung dafuer nicht reicht: dort ging es um das
ANFRAGE-Limit (8/8 OK, Wanduhr 3,2 s). Token bringen eine zweite, unabhaengige
Achse ins Spiel - Speicher und Rechenzeit am Endpunkt. 8 x 16.656 Token
gleichzeitig koennen an einer voellig anderen Grenze scheitern als 8 x 20.

Gemessen wird gegen die ECHTE Validierung (`call_llm_for_hebel_signal`), nicht
nur gegen "HTTP 200" - unter Last kann ein Modell antworten und trotzdem
Schrott liefern. Jeder Slot bekommt einen ANDEREN echten Faktensatz, damit
serverseitiges Caching identischer Prompts das Ergebnis nicht schoenrechnet.

Die Kennzahl, auf die es ankommt, ist nicht die Einzeldauer, sondern
SIGNALE PRO MINUTE - danach entscheidet sich, ob der Anbieter in der Kette
neben Gemini bestehen kann.

KEINE Produktiv-DB (db.DB_PATH auf eine Kopie umgebogen).
"""
import json
import os
import pathlib
import shutil
import sys
import time
from concurrent.futures import ThreadPoolExecutor

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
from api.openrouter import OpenRouterClient  # noqa: E402

SCRATCH = pathlib.Path(__file__).parent
MODELL = sys.argv[1] if len(sys.argv) > 1 else "nvidia/nemotron-3-super-120b-a12b:free"

daten = json.load(open(SCRATCH / "fakten_hebel_faktensaetze.json", encoding="utf-8"))
alle = sorted((e for e in daten["eintraege"] if e.get("facts_json")),
              key=lambda e: e["created_at"], reverse=True)

# WICHTIG: eine eigene Client-Instanz je Slot. Der gemeinsame Client haelt ein
# Lock mit MIN_ABSTAND_SEKUNDEN=3 - der wuerde die Parallelitaet serialisieren
# und damit genau das wegmessen, was hier gemessen werden soll.
KEY = os.environ["OPENROUTER_API_KEY"]


class Fest:
    def __init__(self, model):
        self.inner = OpenRouterClient(api_key=KEY)
        self.model, self.calls = model, 0

    def chat(self, messages, **kw):
        self.calls += 1
        kw["model"] = self.model
        return self.inner.chat(messages, **kw)


def einer(i):
    fall = alle[i % len(alle)]
    h = Fest(MODELL)
    t = time.monotonic()
    try:
        call_llm_for_hebel_signal(h, json.loads(fall["facts_json"]), max_retries=1)
        return ("OK", time.monotonic() - t, h.calls, "")
    except Exception as exc:  # noqa: BLE001
        return (type(exc).__name__, time.monotonic() - t, h.calls, str(exc)[:100])


print(f"Modell: {MODELL}")
print(f"Prompt je Anfrage: ~16.656 Token (echter SYSTEM_PROMPT + echter Faktensatz)\n")
for stufe in (2, 4, 8):
    t = time.monotonic()
    with ThreadPoolExecutor(max_workers=stufe) as ex:
        res = list(ex.map(einer, range(stufe)))
    wand = time.monotonic() - t
    ok = [r for r in res if r[0] == "OK"]
    zeiten = sorted(r[1] for r in ok)
    med = zeiten[len(zeiten) // 2] if zeiten else 0
    pro_min = len(ok) / (wand / 60) if wand else 0
    print(f"  {stufe} parallel: {len(ok)}/{stufe} gueltig   Wanduhr {wand:>6.1f}s   "
          f"Median einzeln {med:>5.1f}s   => {pro_min:>4.1f} gueltige Signale/Minute",
          flush=True)
    for s, d, c, m in res:
        if s != "OK":
            print(f"       {s} nach {d:.1f}s ({c} Versuche): {m}")
    if stufe != 8:
        time.sleep(45)     # Erholung, sonst misst die naechste Stufe die vorige

print("\nVERGLEICHSMASSSTAB")
print("  Gemini seriell: 5,5 s je Signal  =>  10,9 Signale/Minute")
print("  Der Anbieter muss nicht schnell sein, sondern genug DURCHSATZ haben.")
