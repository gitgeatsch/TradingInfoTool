"""Gegenhypothese zu den 488 s: liegt es am Anbieter - oder an einem Regler,
den wir nie gesetzt haben?

`openai/gpt-oss-20b` fuehrt `reasoning_effort` in `supported_parameters`. Es ist
ein Reasoning-Modell; ohne Vorgabe denkt es per Voreinstellung lang. Bei ~12.600
Eingabe-Token kann das die Antwortzeit dominieren, ohne dass der Anbieter
"langsam" waere. Wer das nicht ausschliesst, verwirft einen Anbieter fuer einen
Fehler in der eigenen Konfiguration.

Drei Varianten auf DEMSELBEN echten Faktensatz, roher HTTP-Call (kein
Client-Ratelimiter dazwischen), mit Ausgabe der OpenRouter-Nutzungszahlen -
`reasoning_tokens` beantwortet die Frage direkt.
"""
import json
import os
import pathlib
import sys
import time

from dotenv import load_dotenv

load_dotenv()
import requests

sys.path.insert(0, r"D:\CLAUDE_Projects\SoftwareProjekte\TradingInfoTool")
from agent.krypto.hebel_analyst import SYSTEM_PROMPT  # noqa: E402

SCRATCH = pathlib.Path(__file__).parent
daten = json.load(open(SCRATCH / "fakten_hebel_faktensaetze.json", encoding="utf-8"))
eintraege = sorted((e for e in daten["eintraege"] if e.get("facts_json")),
                   key=lambda e: e["created_at"], reverse=True)
fall = eintraege[0]
facts = json.loads(fall["facts_json"])
messages = [{"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(facts, ensure_ascii=False)}]

MODELL = "openai/gpt-oss-20b:free"
h = {"Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}",
     "HTTP-Referer": "https://github.com/gitgeatsch/TradingInfoTool",
     "X-Title": "TradingInfoTool"}

varianten = [
    ("wie heute (nichts gesetzt)", {}),
    ("reasoning_effort=low", {"reasoning": {"effort": "low"}}),
    ("reasoning aus", {"reasoning": {"exclude": True, "effort": "low"},
                       "max_tokens": 2000}),
]

print(f"Fall: {fall['symbol']} {fall['action']} ({fall['created_at'][:16]})")
print(f"Eingabe: {len(SYSTEM_PROMPT) + len(fall['facts_json']):,} Zeichen\n")

for name, extra in varianten:
    payload = {"model": MODELL, "messages": messages, "temperature": 0.2,
               "response_format": {"type": "json_object"}, **extra}
    t = time.monotonic()
    try:
        r = requests.post("https://openrouter.ai/api/v1/chat/completions",
                          json=payload, headers=h, timeout=600)
        d = time.monotonic() - t
        j = r.json()
        if "choices" not in j:
            print(f"{name:<28} {d:>7.1f}s  FEHL {str(j.get('error') or j)[:110]}")
            continue
        u = j.get("usage") or {}
        det = u.get("completion_tokens_details") or {}
        inhalt = j["choices"][0]["message"]["content"] or ""
        try:
            json.loads(inhalt)
            gueltig = "JSON ok"
        except Exception:
            gueltig = f"KEIN JSON ({len(inhalt)} Zeichen)"
        print(f"{name:<28} {d:>7.1f}s  {gueltig:<22} "
              f"prompt {u.get('prompt_tokens')}, completion {u.get('completion_tokens')}"
              f", davon reasoning {det.get('reasoning_tokens')}")
    except Exception as exc:  # noqa: BLE001
        print(f"{name:<28} {time.monotonic()-t:>7.1f}s  EXC {type(exc).__name__}: {str(exc)[:90]}")
    time.sleep(4)
