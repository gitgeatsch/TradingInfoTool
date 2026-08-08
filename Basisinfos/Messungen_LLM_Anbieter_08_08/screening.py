"""BREITENMESSUNG: jedes jetzt erreichbare :free-Modell am ECHTEN Signal-Prompt.

Zweck: eine Rangliste, bevor tief getestet wird. Drei Faelle je Modell reichen,
um Totalausfaelle von Kandidaten zu trennen - wer hier 0/3 liefert, braucht
keine 20 Faelle.

Gemessen wird gegen call_llm_for_hebel_signal(), also die echte Validierung.
Zwei Dinge werden bewusst getrennt festgehalten:
  * FORMAT-Fehler (AnalystResponseInvalid) - das Modell kann den Vertrag nicht
  * TRANSPORT-Fehler (HTTP/Timeout)        - der Endpunkt kann gerade nicht
Ein Modell mit 3 Transportfehlern ist nicht widerlegt, nur ungemessen.

KEINE Produktiv-DB: db.DB_PATH wird vor dem ersten Import umgebogen.
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
from api.openrouter import OpenRouterClient  # noqa: E402

SCRATCH = pathlib.Path(__file__).parent
N = int(sys.argv[1]) if len(sys.argv) > 1 else 3

daten = json.load(open(SCRATCH / "fakten_hebel_faktensaetze.json", encoding="utf-8"))
eintraege = sorted((e for e in daten["eintraege"] if e.get("facts_json")),
                   key=lambda e: e["created_at"], reverse=True)
faelle = eintraege[:N]
modelle = json.load(open(SCRATCH / "offen_jetzt.json"))


class Zaehlend:
    def __init__(self, inner, model):
        self.inner, self.model, self.calls = inner, model, 0

    def chat(self, messages, **kw):
        self.calls += 1
        kw["model"] = self.model
        return self.inner.chat(messages, **kw)


client = OpenRouterClient(api_key=os.environ["OPENROUTER_API_KEY"])
tabelle = {}
for m in modelle:
    ok = fmt = transport = 0
    zeiten = []
    for f in faelle:
        h = Zaehlend(client, m)
        t = time.monotonic()
        try:
            call_llm_for_hebel_signal(h, json.loads(f["facts_json"]), max_retries=1)
            ok += 1
            zeiten.append(time.monotonic() - t)
        except Exception as exc:  # noqa: BLE001
            if type(exc).__name__ == "AnalystResponseInvalid":
                fmt += 1
            else:
                transport += 1
    med = f"{sorted(zeiten)[len(zeiten)//2]:.0f}s" if zeiten else "-"
    tabelle[m] = {"ok": ok, "format": fmt, "transport": transport, "median": med}
    print(f"{m:<52} {ok}/{len(faelle)}  Format-Fehl {fmt}  Transport-Fehl {transport}  Median {med}",
          flush=True)

json.dump(tabelle, open(SCRATCH / "screening.json", "w"), ensure_ascii=False, indent=1)
print("\nRANGLISTE (nur Modelle mit mindestens einem gueltigen Ergebnis)")
for m, v in sorted(tabelle.items(), key=lambda x: (-x[1]["ok"], x[1]["median"])):
    if v["ok"]:
        print(f"  {v['ok']}/{len(faelle)}  {v['median']:>5}  {m}")
