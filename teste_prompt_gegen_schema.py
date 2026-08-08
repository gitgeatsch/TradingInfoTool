"""Stimmt die JSON-Vorlage im Prompt mit den Validator-Konstanten ueberein?

DER VORFALL, DER DAZU FUEHRT (2026-08-09, aus dem Notebook-Log):

    Hebel-LLM-Antwort ungueltig (Versuch 1):
    top_gruende.kategorie ungueltig: 'antizyklisch'

Die Prompt-Vorlage bot fuenf Kategorien an, die Konstante erlaubte vier. Das
Modell tat, was der Prompt sagte, und wurde dafuer abgelehnt. Der Commit vom
26.07. hatte die Konstante bereinigt und die Vorlage vergessen.

WARUM EIN TEST UND NICHT NUR DER EINE FIX: ich habe EIN Feld geprueft. Es gibt
vier bis fuenf Enum-Felder je Analyst und sechs Analysten - also rund dreissig
Stellen, an denen dieselbe Divergenz entstehen kann, und jede kostet im Betrieb
einen Zweitversuch (doppelte Latenz, doppeltes Kontingent) oder erzeugt ein
HALTEN, das nie aufloest.

WAS DER TEST NICHT PRUEFT: ob die Vorlage inhaltlich sinnvoll ist. Nur, ob sie
dasselbe Vokabular nennt wie der Validator - und damit wie das strikte Schema,
das aus denselben Konstanten gebaut wird (agent/llm_schema.py).

KEIN Netzwerk, keine LLM-Calls.
"""
import importlib
import re
import sys

fehler = []


def pruefe(bedingung, text, info=""):
    if bedingung:
        print(f"  OK   {text}  {info}")
    else:
        print(f"  FEHL {text}  {info}")
        fehler.append(text)


ANALYSTEN = {
    "krypto_spot": "agent.krypto.analyst",
    "hebel": "agent.krypto.hebel_analyst",
    "aktien": "agent.aktien.analyst",
    "rohstoffe": "agent.rohstoff.analyst",
    "themen_etf": "agent.themen_etf.analyst",
    "hedge": "agent.hedge.analyst",
}

# Feldname in der Vorlage -> Konstantenname(n) im Analysten. Der erste
# vorhandene gewinnt (Hebel fuehrt seine unter abweichendem Namen).
FELDER = {
    "action": ("REQUIRED_HEBEL_ACTIONS", "REQUIRED_ACTIONS"),
    "kategorie": ("TOP_GRUENDE_KATEGORIEN",),
    "bucket": ("_HALTE_KRITERIUM_BUCKETS",),
    "folgen": ("_EIGENE_EINSCHAETZUNG_FOLGEN_WERTE",),
    "trade_thesis_typ": ("_TRADE_THESIS_TYPEN",),
}


def vorlage_werte(prompt: str, feld: str) -> set | None:
    """Die Werte, die die JSON-Vorlage fuer `feld` anbietet.

    Gesucht wird `"feld": "a|b|c"`. Platzhalter wie `"..."` (Folgezeilen der
    top_gruende-Liste) werden uebersprungen - sie verweisen auf die erste
    Zeile und sind keine eigene Aussage."""
    treffer = re.findall(rf'"{re.escape(feld)}":\s*"([^"]+)"', prompt)
    kandidaten = [t for t in treffer if "|" in t]
    if not kandidaten:
        return None
    # Alle Nennungen muessen identisch sein - zwei verschiedene Listen im
    # selben Prompt waeren ein Widerspruch fuer sich.
    mengen = {frozenset(k.split("|")) for k in kandidaten}
    if len(mengen) > 1:
        return {"__WIDERSPRUCH__": [sorted(m) for m in mengen]}
    return set(kandidaten[0].split("|"))


print("PROMPT-VORLAGE GEGEN VALIDATOR-KONSTANTEN")
print("=" * 74)

gesamt_geprueft = 0
for name, pfad in ANALYSTEN.items():
    modul = importlib.import_module(pfad)
    prompt = getattr(modul, "SYSTEM_PROMPT", None)
    if prompt is None:
        pruefe(False, f"{name}: SYSTEM_PROMPT nicht gefunden")
        continue
    print(f"\n{name}")
    for feld, konstanten in FELDER.items():
        konstante = next((k for k in konstanten if hasattr(modul, k)), None)
        aus_vorlage = vorlage_werte(prompt, feld)
        if konstante is None and aus_vorlage is None:
            continue                      # Feld gibt es hier schlicht nicht
        if konstante is None:
            pruefe(False, f"{name}.{feld}: Vorlage nennt Werte, es gibt keine Konstante",
                   str(sorted(aus_vorlage)))
            continue
        if aus_vorlage is None:
            # Konstante da, Vorlage nennt die Werte nicht - kein Fehler, aber
            # das Modell kennt das Vokabular dann nur aus dem Fliesstext.
            print(f"  --   {name}.{feld}: Vorlage nennt keine Werte "
                  f"(Konstante {konstante} vorhanden)")
            continue
        if "__WIDERSPRUCH__" in aus_vorlage:
            pruefe(False, f"{name}.{feld}: Vorlage nennt ZWEI verschiedene Listen",
                   str(aus_vorlage["__WIDERSPRUCH__"]))
            continue
        erlaubt = set(getattr(modul, konstante))
        gesamt_geprueft += 1
        zuviel = aus_vorlage - erlaubt
        zuwenig = erlaubt - aus_vorlage
        if zuviel:
            pruefe(False, f"{name}.{feld}: Vorlage bietet an, was der Validator ABLEHNT",
                   f"ueberzaehlig: {sorted(zuviel)}")
        elif zuwenig:
            # Kein Fehlschlag im Betrieb, aber das Modell erfaehrt nie, dass es
            # diese Werte waehlen darf - eine stille Einschraenkung.
            pruefe(False, f"{name}.{feld}: Vorlage VERSCHWEIGT erlaubte Werte",
                   f"fehlt: {sorted(zuwenig)}")
        else:
            pruefe(True, f"{name}.{feld}", f"{len(erlaubt)} Werte, deckungsgleich")

print("\n" + "=" * 74)
print(f"{gesamt_geprueft} Feld/Analyst-Kombinationen verglichen.")
print("ALLE TESTS BESTANDEN" if not fehler else f"{len(fehler)} ABWEICHUNG(EN): {fehler}")
sys.exit(1 if fehler else 0)
