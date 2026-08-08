"""Prueft den Schema-Bauer (agent/llm_schema.py) - Teil des Format-Umstiegs.

WAS HIER WIRKLICH GEPRUEFT WIRD: dass Schema und Validator DIESELBEN Regeln
tragen. Ein Schema, das vom Validator abweicht, ist schlimmer als keines - es
erzwingt dann ein Vokabular, das der Validator hinterher ablehnt, und erzeugt
Fehler, statt sie zu verhindern.

Deshalb vergleicht dieser Test nicht gegen erwartete Literale, sondern gegen
die Konstanten, die der Validator selbst benutzt. Ein Test mit abgeschriebenen
Erwartungswerten waere eine dritte Quelle und damit ein drittes Driftrisiko.

KEIN Netzwerk, keine LLM-Calls.
"""
import importlib
import sys

from agent.llm_schema import (
    SchemaLuecke, als_response_format, baue_konsistenz_schema,
    baue_richtung_schema, baue_signal_schema,
)

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

print("A) ALLE SECHS SIGNAL-FORMEN LASSEN SICH BAUEN")
schemata = {}
for name, pfad in ANALYSTEN.items():
    modul = importlib.import_module(pfad)
    try:
        schemata[name] = (baue_signal_schema(modul), modul)
        pruefe(True, f"A {name} gebaut",
               f"{len(schemata[name][0]['required'])} Pflichtfelder")
    except Exception as exc:  # noqa: BLE001
        pruefe(False, f"A {name} gebaut", str(exc)[:120])

print("\nB) PFLICHTFELDER STIMMEN MIT DEM VALIDATOR UEBEREIN")
for name, (schema, modul) in schemata.items():
    erwartet = list(getattr(modul, "REQUIRED_HEBEL_TOP_LEVEL_FIELDS", None)
                    or getattr(modul, "REQUIRED_TOP_LEVEL_FIELDS"))
    pruefe(schema["required"] == erwartet, f"B {name} required == Validator",
           f"{len(erwartet)} Felder")
    pruefe(set(schema["properties"]) == set(erwartet),
           f"B {name} keine Form ohne Pflichtfeld und umgekehrt")

print("\nC) DIE VOKABULARE KOMMEN AUS DEN VALIDATOR-KONSTANTEN")
for name, (schema, modul) in schemata.items():
    actions = getattr(modul, "REQUIRED_HEBEL_ACTIONS", None) \
        or getattr(modul, "REQUIRED_ACTIONS")
    pruefe(schema["properties"]["action"]["enum"] == sorted(actions),
           f"C {name} action-Enum == REQUIRED_ACTIONS", f"{len(actions)} Werte")
    hk = schema["properties"]["halte_kriterium"]["properties"]["bucket"]["enum"]
    pruefe(hk == sorted(modul._HALTE_KRITERIUM_BUCKETS),
           f"C {name} halte_kriterium.bucket-Enum erzwungen", str(hk))
    tg = schema["properties"]["top_gruende"]["items"]["properties"]["kategorie"]["enum"]
    pruefe(tg == sorted(modul.TOP_GRUENDE_KATEGORIEN),
           f"C {name} top_gruende.kategorie-Enum == Validator")

print("\nD) DIE STELLE, AN DER 3 VON 4 FEHLSCHLAEGEN LAGEN")
# Im 20er-Durchsatztest vom 08.08. war `halte_kriterium.bucket` dreimal None
# statt "kurz"|"mittel"|"lang". Genau das muss das Schema unmoeglich machen.
hebel_schema = schemata["hebel"][0]
bucket = hebel_schema["properties"]["halte_kriterium"]
pruefe("bucket" in bucket["required"], "D bucket ist PFLICHT, nicht optional")
pruefe(bucket["properties"]["bucket"]["type"] == "string",
       "D bucket kann nicht null sein", "None war der reale Fehlschlag")

print("\nE) EINE LUECKE FAELLT AUF, STATT PERMISSIV DURCHZURUTSCHEN")


class _MitNeuemFeld:
    __name__ = "attrappe_analyst"
    REQUIRED_TOP_LEVEL_FIELDS = ("action", "voellig_neues_feld")
    REQUIRED_ACTIONS = ("KAUFEN", "HALTEN")
    TOP_GRUENDE_KATEGORIEN = ("technisch",)
    _HALTE_KRITERIUM_BUCKETS = ("kurz",)
    _EIGENE_EINSCHAETZUNG_FOLGEN_WERTE = ("ja",)


try:
    baue_signal_schema(_MitNeuemFeld())
    pruefe(False, "E unbekanntes Pflichtfeld wirft SchemaLuecke",
           "es wurde still durchgelassen - genau das darf nicht passieren")
except SchemaLuecke as exc:
    pruefe("voellig_neues_feld" in str(exc),
           "E unbekanntes Pflichtfeld wirft SchemaLuecke", "mit Feldnamen in der Meldung")
except Exception as exc:  # noqa: BLE001
    pruefe(False, "E unbekanntes Pflichtfeld wirft SchemaLuecke",
           f"falscher Fehlertyp: {type(exc).__name__}")

print("\nF) DIE ZWEI GEGENPRUEFUNGS-FORMEN")
import agent.krypto.gegenpruefung as G  # noqa: E402

k = baue_konsistenz_schema(G)
r = baue_richtung_schema(G)
pruefe(k["properties"]["urteil"]["enum"] == sorted(G._GUELTIGE_URTEILE),
       "F konsistenz-Enum == _GUELTIGE_URTEILE", str(k["properties"]["urteil"]["enum"]))
pruefe(r["properties"]["eigene_richtung"]["enum"] == sorted(G._GUELTIGE_RICHTUNGEN),
       "F richtung-Enum == _GUELTIGE_RICHTUNGEN", str(r["properties"]["eigene_richtung"]["enum"]))

print("\nG) VERPACKUNG FUER DIE ENDPUNKTE")
rf = als_response_format(hebel_schema, "hebel_signal")
pruefe(rf["type"] == "json_schema", "G type == json_schema")
pruefe(rf["json_schema"]["strict"] is True, "G strict ist gesetzt",
       "ohne strict ist das Schema ein Vorschlag, keine Vorgabe")
pruefe(rf["json_schema"]["schema"] is hebel_schema, "G Schema unveraendert durchgereicht")

print("\n" + ("ALLE TESTS BESTANDEN" if not fehler else f"{len(fehler)} FEHLER: {fehler}"))
sys.exit(1 if fehler else 0)
