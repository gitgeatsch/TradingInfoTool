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

print("\nE) ROTATION - Ausfall eines Modells darf kein Ausfall des Anbieters sein")
from api.openrouter import FREE_MODELLE

pruefe("E1 die Liste hat mehrere Modelle", len(FREE_MODELLE) >= 3, str(len(FREE_MODELLE)))
pruefe("E2 JEDER Eintrag ist :free - auch die Reserve",
       all(m.endswith(":free") for m in FREE_MODELLE),
       "ein vergessenes Suffix waere eine Zeitbombe, die erst beim Rueckfall zuendet")
pruefe("E3 keine Doppelten", len(set(FREE_MODELLE)) == len(FREE_MODELLE))


def probe_client(scheitern_bei):
    """Rotation ohne Netz - aber mit der ECHTEN Klasse.

    Bewusst keine Unterklasse: `llm_model_label()` erkennt den Anbieter am
    Modulnamen, und eine im Testskript definierte Unterklasse lebt in
    `__main__` - der Test wuerde dann etwas anderes pruefen als den Produktivfall.
    (Diese Modulnamen-Erkennung ist eine bekannte Sproedigkeit von
    llm_provider.py, hier nur umgangen, nicht behoben.)
    """
    c = OpenRouterClient("test")
    c.versuche = []

    def _ein_call(messages, model, temperature, response_format):
        c.versuche.append(model)
        if model in scheitern_bei:
            raise RuntimeError("404 unavailable for free")
        c.letztes_modell = model
        return '{"bewertung":"konsistent"}'

    c._ein_call = _ein_call
    return c


p2 = probe_client(FREE_MODELLE[:2])
antwort = p2.chat([{"role": "user", "content": "x"}])
pruefe("E4 rotiert der Reihe nach weiter",
       p2.versuche == list(FREE_MODELLE[:3]), str(p2.versuche))
pruefe("E5 liefert die Antwort des Modells, das getragen hat",
       antwort == '{"bewertung":"konsistent"}')
pruefe("E6 das Label nennt das TATSAECHLICHE Modell, nicht den Listenkopf",
       llm_model_label(p2) == f"openrouter:{FREE_MODELLE[2]}",
       llm_model_label(p2) + "  - sonst waere jede Provider-Auswertung gelogen")

try:
    probe_client(set(FREE_MODELLE)).chat([{"role": "user", "content": "x"}])
    pruefe("E7 alle Modelle tot -> Fehler", False, "kein Fehler geworfen")
except RuntimeError as exc:
    pruefe("E7 alle Modelle tot -> Fehler mit Anzahl",
           str(len(FREE_MODELLE)) in str(exc),
           "erst DANN sieht der Circuit Breaker einen Anbieter-Ausfall")

p3 = probe_client(())
p3.chat([{"role": "user", "content": "x"}], model=FREE_MODELLE[2])
pruefe("E8 mit ausdruecklichem model wird NICHT rotiert",
       p3.versuche == [FREE_MODELLE[2]],
       "Vergleichslaeufe muessen genau das messen, was sie angeben")

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
