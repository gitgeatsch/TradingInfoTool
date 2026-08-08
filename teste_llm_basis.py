"""Prueft Teil A des Anbieter-Umbaus (2026-08-09): gemeinsamer Antwort-Extraktor
und thread-sichere Drossel in ALLEN fuenf LLM-Clients.

Keine Netzwerk-Calls, keine DB. Laeuft in Sekunden.
"""
import io
import threading
import time

from api.llm_basis import (
    LLMAntwortOhneInhalt,
    Mindestabstand,
    Minutenfenster,
    extrahiere_inhalt,
)
from agent.provider_sperre import ist_dauerhafter_fehler

fehler = 0


def pruefe(name, bedingung, hinweis=""):
    global fehler
    if bedingung:
        print(f"  OK   {name}" + (f"  {hinweis}" if hinweis else ""))
    else:
        fehler += 1
        print(f"  FEHL {name}" + (f"  {hinweis}" if hinweis else ""))


print("A) DER EXTRAKTOR NENNT DEN GRUND STATT EINES FELDNAMENS")
pruefe("A1 normale Antwort geht durch",
       extrahiere_inhalt({"choices": [{"message": {"content": "hallo"}}]}, "X") == "hallo")

try:
    extrahiere_inhalt({"error": {"message": "Provider timed out after 24566ms",
                                 "code": 504}}, "OpenRouter/m")
    pruefe("A2 HTTP 200 ohne choices wirft", False)
except LLMAntwortOhneInhalt as exc:
    pruefe("A2 HTTP 200 ohne choices wirft", True)
    pruefe("A3 der Grund steht im Text", "timed out" in str(exc), str(exc)[:70])
    pruefe("A4 der Anbieter steht im Text", "OpenRouter/m" in str(exc))

# DER EIGENTLICHE ZWECK: der Circuit Breaker stuft anhand des Fehlertextes ein.
# Bei einem KeyError: 'choices' stand dort nur ein Feldname - ein 402 waere als
# voruebergehend durchgegangen und dreimal wiederholt worden.
try:
    extrahiere_inhalt({"error": {"message": "402 Payment Required", "code": 402}}, "Mistral")
except LLMAntwortOhneInhalt as exc:
    pruefe("A5 Breaker erkennt 402 als DAUERHAFT", ist_dauerhafter_fehler(str(exc)),
           "genau dafuer ist der eigene Fehlertyp da")
pruefe("A6 KeyError haette der Breaker NICHT erkannt",
       not ist_dauerhafter_fehler("'choices'"), "der Zustand vor dem Umbau")

try:
    extrahiere_inhalt({"choices": []}, "X")
    pruefe("A7 leere choices-Liste wirft", False)
except LLMAntwortOhneInhalt:
    pruefe("A7 leere choices-Liste wirft", True, "IndexError wird mitgefangen")

print("\nB) DIE DROSSEL IST THREAD-SICHER")
f = Minutenfenster(5)
durch = []
def feuern():
    f.warte_auf_slot()
    durch.append(time.monotonic())
threads = [threading.Thread(target=feuern) for _ in range(5)]
start = time.monotonic()
[t.start() for t in threads]
[t.join() for t in threads]
pruefe("B1 5 Threads bei Limit 5 laufen sofort durch",
       len(durch) == 5 and time.monotonic() - start < 2.0,
       f"{time.monotonic()-start:.2f}s")

f2 = Minutenfenster(2)
f2.warte_auf_slot(); f2.warte_auf_slot()
pruefe("B2 das Fenster fuehrt Buch", len(f2._zeitpunkte) == 2)
pruefe("B3 Zugriff ist gelockt", isinstance(f2._lock, type(threading.Lock())))

m = Mindestabstand(0.3)
t0 = time.monotonic(); m.warte_auf_slot(); m.warte_auf_slot()
pruefe("B4 Mindestabstand wartet", time.monotonic() - t0 >= 0.3,
       f"{time.monotonic()-t0:.2f}s")

print("\nC) ALLE FUENF CLIENTS BENUTZEN DIE GEMEINSAME BASIS")
for datei, name in (("api/gemini.py", "Gemini"), ("api/groq.py", "Groq"),
                    ("api/mistral.py", "Mistral"), ("api/zai.py", "Z.ai"),
                    ("api/openrouter.py", "OpenRouter")):
    src = io.open(datei, encoding="utf-8").read()
    pruefe(f"C-{name} kein blinder choices-Zugriff mehr",
           'data["choices"]' not in src and 'daten["choices"]' not in src)
    pruefe(f"C-{name} importiert aus llm_basis", "from api.llm_basis import" in src)

for name, modul, klasse in (("gemini", "api.gemini", "GeminiClient"),
                            ("groq", "api.groq", "GroqClient"),
                            ("mistral", "api.mistral", "MistralClient"),
                            ("zai", "api.zai", "ZaiClient"),
                            ("openrouter", "api.openrouter", "OpenRouterClient")):
    C = getattr(__import__(modul, fromlist=[klasse]), klasse)
    c = C("test-key")
    pruefe(f"C-{name} hat eine gelockte Drossel",
           isinstance(c._drossel, (Minutenfenster, Mindestabstand)),
           type(c._drossel).__name__)

print("\n" + ("ALLE TESTS BESTANDEN" if not fehler else f"FEHLER: {fehler}"))
raise SystemExit(1 if fehler else 0)
