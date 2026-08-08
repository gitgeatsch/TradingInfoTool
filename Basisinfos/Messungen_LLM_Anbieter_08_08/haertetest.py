"""HAERTETEST: traegt ein OpenRouter-Modell den ECHTEN Hebel-Signal-Prompt?

Der Unterschied zum bisherigen `teste_openrouter_live.py`: dort lief der
schlanke Gegenpruefungs-Faktensatz (~10 Felder). Hier laeuft der vollstaendige
SYSTEM_PROMPT (36.496 Zeichen, ~9.124 Token) plus ein ECHTER Faktensatz aus dem
Notebook-Export - also genau die Last, die die Signal-Kette erzeugt.

Gemessen wird gegen `call_llm_for_hebel_signal()`, also die echte
Validierung (`_validate_hebel`) statt einer nachgebauten Feldliste.

Die Faktensaetze kommen aus der Export-JSON im Scratchpad. Eine DB wird
trotzdem angefasst - `@track_api_health` oeffnet bei JEDEM Client-Call eine
Verbindung ueber `db.DB_PATH`. Deshalb wird der Pfad hier VOR dem ersten
Import auf eine Kopie umgebogen (stehende Vorgabe, siehe Memory
feedback_desktop_kein_produktivstart: "kein echter LLM-Call" ist nicht
dasselbe wie "kein echter DB-Schreibzugriff" - hier sogar umgekehrt).

Aufruf:  python -u haertetest.py <faelle> [modell-index|alle|gemini]
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
print(f"DB umgebogen auf {_KOPIE}")

from agent.krypto.hebel_analyst import call_llm_for_hebel_signal  # noqa: E402
from api.openrouter import FREE_MODELLE, OpenRouterClient  # noqa: E402

SCRATCH = pathlib.Path(
    r"C:\Users\Geatsch\AppData\Local\Temp\claude"
    r"\D--CLAUDE-Projects-SoftwareProjekte-TradingInfoTool"
    r"\a51e0ce8-8568-4daa-bcd2-9c2b6bc3aec7\scratchpad"
)

N = int(sys.argv[1]) if len(sys.argv) > 1 else 5
WAHL = sys.argv[2] if len(sys.argv) > 2 else "alle"


class Zaehlend:
    """Duennes Huellblatt: zaehlt, wie oft die Pipeline nachfassen musste.
    Ohne das saehe ein Modell, das erst im zweiten Anlauf gueltiges JSON
    liefert, genauso aus wie eines, das es sofort kann - bei dreifachem
    Zeit- und Kontingentverbrauch."""

    def __init__(self, inner, model=None):
        self.inner = inner
        self.model = model
        self.calls = 0

    def chat(self, messages, **kw):
        self.calls += 1
        if self.model is not None:
            kw["model"] = self.model
        return self.inner.chat(messages, **kw)


daten = json.load(open(SCRATCH / "fakten_hebel_faktensaetze.json", encoding="utf-8"))
eintraege = [e for e in daten["eintraege"] if e.get("facts_json")]
# Neueste zuerst, aber ueber die actions gestreut - 20x HALTEN waere eine
# Messung EINER Situation, nicht des Modells.
eintraege.sort(key=lambda e: e["created_at"], reverse=True)
gestreut, gesehen = [], {}
for e in eintraege:
    k = e["action"]
    if gesehen.get(k, 0) < max(2, N // 3):
        gestreut.append(e)
        gesehen[k] = gesehen.get(k, 0) + 1
faelle = (gestreut + [e for e in eintraege if e not in gestreut])[:N]

print(f"{len(faelle)} echte Faelle "
      f"({', '.join(sorted({f['action'] for f in faelle}))})")
print(f"Faktensatz-Groesse: Median "
      f"{sorted(len(f['facts_json']) for f in faelle)[len(faelle)//2]:,} Zeichen\n")

kandidaten = []
if WAHL == "gemini":
    from api.gemini import GeminiClient

    kandidaten = [("gemini", GeminiClient(api_key=os.environ["GEMINI_API_KEY"]), None)]
else:
    key = os.environ["OPENROUTER_API_KEY"]
    if "/" in WAHL:                      # vollstaendige Modell-ID direkt
        liste = (WAHL,)
    elif WAHL == "alle":
        liste = FREE_MODELLE
    else:
        liste = (FREE_MODELLE[int(WAHL)],)
    kandidaten = [(m, OpenRouterClient(api_key=key), m) for m in liste]

alles = {}
for name, client, modell in kandidaten:
    print(f"--- {name}")
    zeilen = []
    for i, f in enumerate(faelle, 1):
        facts = json.loads(f["facts_json"])
        huelle = Zaehlend(client, modell)
        t = time.monotonic()
        try:
            r = call_llm_for_hebel_signal(huelle, facts, max_retries=1)
            d = time.monotonic() - t
            zeilen.append({"symbol": f["symbol"], "ok": True, "dauer": d,
                           "versuche": huelle.calls, "action": r["action"],
                           "richtung": r["richtung"],
                           "konfidenz": r.get("confidence_pct"),
                           "referenz_action": f["action"]})
            print(f"  {i:>2}. {f['symbol']:<9} OK   {d:>6.1f}s  {huelle.calls} Versuch(e)  "
                  f"{r['richtung']}/{r['action']:<12} {r.get('confidence_pct')}%")
        except Exception as exc:  # noqa: BLE001
            d = time.monotonic() - t
            zeilen.append({"symbol": f["symbol"], "ok": False, "dauer": d,
                           "versuche": huelle.calls,
                           "grund": f"{type(exc).__name__}: {exc}"[:150],
                           "referenz_action": f["action"]})
            print(f"  {i:>2}. {f['symbol']:<9} FEHL {d:>6.1f}s  {huelle.calls} Versuch(e)  "
                  f"{type(exc).__name__}: {str(exc)[:90]}")
    ok = [z for z in zeilen if z["ok"]]
    dd = sorted(z["dauer"] for z in ok)
    print(f"  => {len(ok)}/{len(zeilen)} gueltig"
          + (f", Median {dd[len(dd)//2]:.1f}s, langsamster {dd[-1]:.1f}s"
             f", {sum(z['versuche'] for z in ok)/len(ok):.2f} Versuche/Fall" if ok else "")
          + "\n")
    alles[name] = zeilen

ziel = SCRATCH / f"haertetest_{WAHL.replace('/', '_')}_{len(faelle)}.json"
json.dump(alles, open(ziel, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"geschrieben: {ziel.name}")
