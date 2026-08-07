"""Prueft den OpenRouter-Client fuer die Gegenpruefung (07.08.2026).

DER KERN IST A2: eine Modell-ID ohne `:free`-Suffix muss abgewiesen werden,
BEVOR ein Netzwerk-Call stattfindet. Der Nutzer hat ausdruecklich gesagt, eine
frueher geleistete Einmalzahlung sei ein Fehler gewesen - "unnoetig einzahlen"
darf hier nicht durch einen Tippfehler in einer Modell-ID passieren.

UND B1: der Client darf NICHT in der Signal-Kette landen. Die freien Endpunkte
verlangen aktiviertes Logging/Training; freigegeben wurde das nur fuer den
schlanken Gegenpruefungs-Faktensatz, nicht fuer den SYSTEM_PROMPT (~9.100
Token Regelwerk).
"""
import io

from api.openrouter import (
    DEFAULT_MODEL,
    FREE_SUFFIX,
    OpenRouterClient,
    OpenRouterModelNichtFrei,
)
from agent.krypto.llm_provider import llm_model_label, provider_from_label

fehler = []
def pruefe(name, ok, info=""):
    print(("  OK   " if ok else "  FEHL ") + name + ("  " + info if info else ""))
    if not ok:
        fehler.append(name)

client = OpenRouterClient("test-key")

print("A) KEIN GELD AUSGEBEN - der Schutz gegen bezahlte Modelle")
pruefe("A1 das Vorgabemodell ist ein Free-Modell", DEFAULT_MODEL.endswith(FREE_SUFFIX),
       DEFAULT_MODEL)
try:
    client.chat([{"role": "user", "content": "x"}], model="deepseek/deepseek-r1")
    pruefe("A2 bezahlte Modell-ID wird abgewiesen", False, "kein Fehler geworfen")
except OpenRouterModelNichtFrei as exc:
    pruefe("A2 bezahlte Modell-ID wird abgewiesen - VOR dem Netzwerk-Call", True,
           "ein Tippfehler in der ID kostet damit kein Guthaben")
except Exception as exc:  # noqa: BLE001
    pruefe("A2 bezahlte Modell-ID wird abgewiesen", False,
           f"falscher Fehlertyp: {type(exc).__name__} - der Call ist evtl. rausgegangen")

for verdaechtig in ("gpt-4o", "anthropic/claude-sonnet-4", "meta-llama/llama-4-scout"):
    try:
        client.chat([{"role": "user", "content": "x"}], model=verdaechtig)
        pruefe(f"A3 {verdaechtig} abgewiesen", False)
    except OpenRouterModelNichtFrei:
        pruefe(f"A3 {verdaechtig} abgewiesen", True)
    except Exception:
        pruefe(f"A3 {verdaechtig} abgewiesen", False, "anderer Fehler - Call ging evtl. raus")

print("\nB) DER CLIENT GEHOERT NICHT IN DIE SIGNAL-KETTE")
haupt = io.open("main.py", encoding="utf-8").read()
pruefe("B1 wird NICHT als mistral_client/gemini_client uebergeben",
       "mistral_client=gegenpruefung_client" not in haupt
       and "gemini_client=gegenpruefung_client" not in haupt,
       "sonst saehe ein trainings-aktivierter Endpunkt den SYSTEM_PROMPT")
pruefe("B2 wird als Gegenpruefungs-Client uebergeben",
       "zai_client=gegenpruefung_client" in haupt)
pruefe("B3 faellt ohne Key auf Z.ai zurueck",
       "gegenpruefung_client = zai_client" in haupt,
       "ohne OPENROUTER_API_KEY bleibt alles wie bisher")

alloc = io.open("agent/krypto/budget_allocator.py", encoding="utf-8").read()
pruefe("B4 der Budget-Allocator kennt OpenRouter nicht",
       "openrouter" not in alloc.lower(),
       "die Signal-Kette bleibt Mistral -> Gemini")

print("\nC) PROVIDER-KENNZEICHNUNG")
label = llm_model_label(client)
pruefe("C1 Label traegt den Anbieter", label.startswith("openrouter:"), label)
pruefe("C2 Rueckwaerts-Mapping funktioniert",
       provider_from_label(label) == "openrouter",
       "sonst zaehlt compute_provider_performance() die Ergebnisse falsch zu")

print("\nD) DAS INTERFACE PASST ZUR GEGENPRUEFUNG")
gp = io.open("agent/krypto/gegenpruefung.py", encoding="utf-8").read()
pruefe("D1 die Gegenpruefung ruft nur .chat() auf - Duck-Typing traegt",
       gp.count("zai_client.chat(") == gp.count(".chat("),
       "kein anbieterspezifischer Aufruf im Modul")
pruefe("D2 chat() hat dieselbe Signatur wie die uebrigen Clients",
       all(p in io.open("api/openrouter.py", encoding="utf-8").read()
           for p in ("messages: list[dict]", "temperature: float", "response_format")))

print("\n" + ("ALLE TESTS BESTANDEN" if not fehler else f"FEHLER: {fehler}"))
