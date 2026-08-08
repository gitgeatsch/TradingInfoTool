"""Wie viele GLEICHZEITIGE Anfragen laesst der freie Nvidia-Endpunkt zu?

Warum das die Latenzfrage entscheidet: 48 s je Signal sind nur dann ein
Ausschlussgrund, wenn seriell gearbeitet wird. Bei vier parallelen Anfragen
sinkt die Zeit fuer vier Signale von 192 s auf ~50 s - dann ist der Abstand zu
Gemini kein Faktor 9 mehr, sondern gut zwei.

Das Muster gibt es im Projekt schon: api/zai.py haelt ein
threading.Semaphore(2), weil Z.ai ein dokumentiertes Concurrency-Limit von 2
hat. Fuer OpenRouter ist keine Zahl dokumentiert - also messen.

BEWUSST MIT KURZER FRAGE. Gemessen wird das Anfrage-Limit, nicht der Durchsatz;
eine kurze Frage haelt die Messung sauber und das Kontingent klein. Ob die
gefundene Stufe auch beim vollen Prompt haelt, ist eine EIGENE Messung - die
Token-Last kann eine andere Grenze treffen.
"""
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor

import requests
from dotenv import load_dotenv

load_dotenv()

MODELL = sys.argv[1] if len(sys.argv) > 1 else "nvidia/nemotron-3-super-120b-a12b:free"
H = {"Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}",
     "HTTP-Referer": "https://github.com/gitgeatsch/TradingInfoTool",
     "X-Title": "TradingInfoTool"}
MSG = [{"role": "user", "content": "Nenne genau eine Primzahl zwischen 10 und 20."}]


def einer(_):
    t = time.monotonic()
    try:
        r = requests.post("https://openrouter.ai/api/v1/chat/completions",
                          json={"model": MODELL, "messages": MSG, "temperature": 0.2,
                                "reasoning": {"exclude": True, "effort": "low"}},
                          headers=H, timeout=120)
        j = r.json()
        if "choices" in j:
            return ("OK", time.monotonic() - t, "")
        fehler = j.get("error") or {}
        return (str(fehler.get("code") or r.status_code), time.monotonic() - t,
                str(fehler.get("message"))[:70])
    except Exception as exc:  # noqa: BLE001
        return ("EXC", time.monotonic() - t, f"{type(exc).__name__}: {str(exc)[:60]}")


print(f"Modell: {MODELL}\n")
for stufe in (1, 2, 4, 6, 8):
    t = time.monotonic()
    with ThreadPoolExecutor(max_workers=stufe) as ex:
        res = list(ex.map(einer, range(stufe)))
    gesamt = time.monotonic() - t
    ok = sum(1 for s, _, _ in res if s == "OK")
    zeiten = [d for s, d, _ in res if s == "OK"]
    schnitt = sum(zeiten) / len(zeiten) if zeiten else 0
    fehler = {}
    for s, _, m in res:
        if s != "OK":
            fehler[s] = fehler.get(s, 0) + 1
    print(f"  {stufe} parallel: {ok}/{stufe} OK  "
          f"Wanduhr {gesamt:>5.1f}s  Einzelschnitt {schnitt:>5.1f}s"
          + (f"  Fehler {fehler}" if fehler else ""), flush=True)
    for s, d, m in res:
        if s != "OK" and m:
            print(f"       {s}: {m}")
    time.sleep(20)   # Erholung, damit die naechste Stufe nicht die vorige misst
