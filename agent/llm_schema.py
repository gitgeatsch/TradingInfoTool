"""Strikte JSON-Schemata, ABGELEITET aus den Validator-Konstanten (2026-08-09).

WARUM ABGELEITET UND NICHT GESCHRIEBEN: es gibt neun Ausgabeformen. Neun von
Hand gepflegte Schemata neben neun Validatoren sind neun Gelegenheiten
auseinanderzulaufen - und ein Schema, das vom Validator abweicht, ERZEUGT
Fehler, statt sie zu verhindern. Es erzwingt dann ein Vokabular, das der
Validator hinterher ablehnt. Deshalb liest dieses Modul dieselben Konstanten,
die auch der Validator benutzt: `REQUIRED_TOP_LEVEL_FIELDS`,
`REQUIRED_ACTIONS`, `TOP_GRUENDE_KATEGORIEN`, `_HALTE_KRITERIUM_BUCKETS`,
`_EIGENE_EINSCHAETZUNG_FOLGEN_WERTE`. Eine Quelle, kein Abgleichproblem.

WAS EIN STRIKTES SCHEMA LEISTET - und was nicht. Es erzwingt Struktur und
Vokabular. Genau dort lagen die realen Fehlschlaege: im 20er-Durchsatztest vom
08.08. scheiterten 3 von 4 Faellen an derselben Stelle, `halte_kriterium.bucket`
war `None` statt "kurz"|"mittel"|"lang" - eine Regel, die das Modell bis dahin
nur aus dem Prompttext kannte. Es leistet NICHT, dass das Urteil besser wird,
und es beseitigt keinen Positions-Bias im EINGABE-Fakten-JSON (siehe
agent/krypto/gegenpruefung.py::leite_eigene_richtung_positionsrobust()) - der
liegt vor dem Output und bleibt unberuehrt.

Die sechs Signal-Analysten (Krypto-Spot, Hebel, Aktien, Rohstoffe, Themen-ETF,
Hedge) folgen strukturell demselben Bauplan und werden von
`baue_signal_schema()` bedient. Die zwei Gegenpruefungs-Formen sind winzig und
haben eigene Bauer. Die Kategorie-Synthese fuehrt keine Pflichtfeld-Konstanten
und ist deshalb bewusst NICHT hier - sie waere geraten, nicht abgeleitet.
"""
from __future__ import annotations

# --- Bausteine --------------------------------------------------------------
TXT = {"type": "string"}
TXTN = {"type": ["string", "null"]}
NUM = {"type": ["number", "null"]}
_SPANNE = {"type": "object", "properties": {
    "usd_von": NUM, "usd_bis": NUM, "eur_von": NUM, "eur_bis": NUM}}
_SZENARIO = {"type": "object", "properties": {
    "scenario": TXT, "probability_pct": {"type": "number"}}}


def _top_gruende(kategorien) -> dict:
    return {
        "type": "array", "minItems": 5, "maxItems": 5,
        "items": {
            "type": "object",
            "properties": {
                "rang": {"type": "integer", "minimum": 1, "maximum": 5},
                "kategorie": {"type": "string", "enum": sorted(kategorien)},
                "text": TXT,
            },
            "required": ["rang", "kategorie", "text"],
        },
    }


def _halte_kriterium(buckets) -> dict:
    return {
        "type": "object",
        "properties": {
            # GENAU HIER lagen 3 von 4 Fehlschlaegen im 20er-Test vom 08.08.
            # Jetzt erzwungen statt erbeten.
            "bucket": {"type": "string", "enum": sorted(buckets)},
            "ziel_preis_usd": NUM, "ziel_preis_eur": NUM,
            "ziel_datum": TXTN, "bedingung_text": TXTN, "reasoning": TXT,
        },
        "required": ["bucket", "reasoning"],
    }


def _eigene_einschaetzung(werte) -> dict:
    return {
        "type": "object",
        "properties": {
            "folgen": {"type": "string", "enum": sorted(werte)},
            "kurzfazit": TXT,
        },
        "required": ["folgen", "kurzfazit"],
    }


_FORECAST = {
    "type": "object",
    "properties": {"bull": _SZENARIO, "base": _SZENARIO, "bear": _SZENARIO},
    "required": ["bull", "base", "bear"],
}
_POSITION_SIZE = {"type": "object", "properties": {
    "usd": NUM, "eur": NUM, "note": TXTN}}
_TRANCHEN = {"type": ["array", "null"], "minItems": 2, "maxItems": 5, "items": {
    "type": "object",
    "properties": {
        "rang": {"type": "integer", "minimum": 1},
        "anteil_prozent": {"type": "number"},
        "zone": _SPANNE,
        "trigger_bedingung": TXTN,
    },
    "required": ["rang", "anteil_prozent", "zone"]}}


class SchemaLuecke(RuntimeError):
    """Ein Pflichtfeld hat keine bekannte Form.

    ABSICHTLICH EIN FEHLER, KEIN STILLER RUECKFALL auf `{}`: ein permissives
    Teilschema fuer ein unbekanntes Feld sieht aus wie Abdeckung und ist keine.
    Wer ein Feld zu REQUIRED_TOP_LEVEL_FIELDS hinzufuegt, soll hier anecken und
    entscheiden, welche Form es hat."""


def baue_signal_schema(analyst_modul) -> dict:
    """Strikte Schema-Definition fuer einen der sechs Signal-Analysten.

    Liest ausschliesslich Konstanten aus `analyst_modul`. Hebel fuehrt seine
    unter abweichenden Namen (`REQUIRED_HEBEL_*`) - beide Schreibweisen werden
    akzeptiert, damit kein Analyst umbenannt werden muss."""
    M = analyst_modul
    pflichtfelder = getattr(M, "REQUIRED_HEBEL_TOP_LEVEL_FIELDS", None) \
        or getattr(M, "REQUIRED_TOP_LEVEL_FIELDS")
    actions = getattr(M, "REQUIRED_HEBEL_ACTIONS", None) \
        or getattr(M, "REQUIRED_ACTIONS")

    bekannt = {
        "action": {"type": "string", "enum": sorted(actions)},
        "richtung": {"type": "string", "enum": ["LONG", "SHORT"]},
        "gegenargument": TXT,
        "confidence_pct": {"type": "number"},
        "short_reasoning": TXT,
        "hebel_vorschlag": NUM,
        "top_gruende": _top_gruende(M.TOP_GRUENDE_KATEGORIEN),
        # Freitext-Struktur, bewusst offen: der Validator prueft hier nur, DASS
        # ein Objekt kommt. Ein erfundenes Teilschema waere strenger als die
        # Regel, die es abbilden soll.
        "long_reasoning": {"type": "object"},
        "position_size": _POSITION_SIZE,
        # OPTIONAL, steht bewusst NICHT in REQUIRED_TOP_LEVEL_FIELDS: `tranchen`
        # darf null sein (und muss es, wenn `tranchen_erlaubt` false ist). Ohne
        # Eintrag hier wuesste ein Modell unter striktem Schema aber nicht,
        # welche Form erlaubt ist.
        "tranchen": _TRANCHEN,
        "entry": _SPANNE, "stop_loss": _SPANNE, "take_profit": _SPANNE,
        "halte_kriterium": _halte_kriterium(M._HALTE_KRITERIUM_BUCKETS),
        "key_risks": {"type": "array", "items": TXT},
        "forecast": _FORECAST,
        "eigene_einschaetzung": _eigene_einschaetzung(M._EIGENE_EINSCHAETZUNG_FOLGEN_WERTE),
    }
    if hasattr(M, "_TRADE_THESIS_TYPEN"):
        bekannt["trade_thesis_typ"] = {
            "type": "string", "enum": sorted(M._TRADE_THESIS_TYPEN)}

    fehlend = [f for f in pflichtfelder if f not in bekannt]
    if fehlend:
        raise SchemaLuecke(
            f"{M.__name__}: keine Form hinterlegt fuer {fehlend}. In "
            f"agent/llm_schema.py::baue_signal_schema() ergaenzen - ein "
            f"permissives Teilschema waere Scheinabdeckung.")

    # OPTIONALE Felder: in `properties`, aber NICHT in `required`. `tranchen`
    # darf null sein und muss es, wenn `tranchen_erlaubt` false ist - es steht
    # deshalb bewusst in keiner REQUIRED_TOP_LEVEL_FIELDS-Liste. Ohne diesen
    # Zusatz fiele es aus dem Schema heraus (properties wird aus den
    # Pflichtfeldern gebaut) und ein Modell unter striktem Schema wuesste die
    # erlaubte Form nicht.
    eigenschaften = {f: bekannt[f] for f in pflichtfelder}
    for optional in ("tranchen",):
        if optional not in eigenschaften:
            eigenschaften[optional] = bekannt[optional]

    return {
        "type": "object",
        "properties": eigenschaften,
        "required": list(pflichtfelder),
    }


def baue_konsistenz_schema(gegenpruefung_modul) -> dict:
    """Konsistenz-Check der Gegenpruefung: {urteil, kurzbegruendung}."""
    return {
        "type": "object",
        "properties": {
            "urteil": {"type": "string",
                       "enum": sorted(gegenpruefung_modul._GUELTIGE_URTEILE)},
            "kurzbegruendung": TXTN,
        },
        "required": ["urteil"],
    }


def baue_richtung_schema(gegenpruefung_modul) -> dict:
    """Richtungs-Abgleich der Gegenpruefung: {eigene_richtung, kurzbegruendung}."""
    return {
        "type": "object",
        "properties": {
            "eigene_richtung": {
                "type": "string",
                "enum": sorted(gegenpruefung_modul._GUELTIGE_RICHTUNGEN)},
            "kurzbegruendung": TXTN,
        },
        "required": ["eigene_richtung"],
    }


def _nullbar(teilschema: dict) -> dict:
    """Macht ein Teilschema null-faehig, ohne es sonst zu veraendern.

    Bei einem `enum` muss `null` MIT in die Liste - sonst waere der Typ zwar
    nullbar, der Wert aber nicht erlaubt, und das Modell haette keine gueltige
    Wahl mehr."""
    t = teilschema.get("type")
    if t is None:
        return teilschema
    typen = list(t) if isinstance(t, list) else [t]
    if "null" in typen:
        return teilschema
    neu = dict(teilschema)
    neu["type"] = typen + ["null"]
    if "enum" in neu and None not in neu["enum"]:
        neu["enum"] = list(neu["enum"]) + [None]
    return neu


def erzwinge_strikt_vertrag(schema: dict) -> dict:
    """Bringt ein Schema in die Form, die `strict: true` verlangt.

    DER VERTRAG, extern belegt (OpenAI Structured Outputs, von Groq und
    OpenRouter uebernommen): *jedes* Objekt braucht `additionalProperties:
    false`, und **alle** Eigenschaften muessen in `required` stehen. Optionale
    Felder werden NICHT durch Weglassen aus `required` abgebildet, sondern
    durch einen null-faehigen Typ - das Modell liefert dann ausdruecklich
    `null` statt das Feld auszulassen.

    WARUM DAS HIER STEHT UND NICHT IN NEUN BAUERN. Es ist eine Eigenschaft des
    TRANSPORTS, nicht der einzelnen Ausgabeform - genau wie `strict: True`
    selbst, das zwei Zeilen tiefer gesetzt wird. Neunmal ausgeschrieben waeren
    es neun Gelegenheiten auseinanderzulaufen.

    DER ANLASS (12.08.2026, Gegenpruefung zu Paket 1). Gemessen ueber alle
    Ausgabeformen:

        Lagebild        0 Verstoesse
        Trader          4
        Krypto-Spot    31 in 11 Objekten
        Hebel          28 in 10
        Aktien         31 in 11
        Hedge          31 in 11

    Betroffen waren vor allem die Kurs-Spannen (`entry`, `stop_loss`,
    `take_profit` mit je vier Feldern und gar keinem `required`), die
    Positionsgroesse und die Tranchen. Ein Anbieter hinter OpenRouter, der den
    Vertrag durchsetzt, weist so ein Schema zurueck - und OpenRouter ist genau
    der Pfad, der produktiv noch nicht sauber gelaufen ist (Nutzerhinweis
    12.08.). Der Fehler war also nicht sichtbar, weil der Weg kaum begangen
    wurde.

    SEMANTISCH AENDERT SICH NICHTS: was vorher weggelassen werden durfte, darf
    jetzt `null` sein. Die Validatoren pruefen ohnehin auf `None` und leere
    Werte, nicht auf Abwesenheit des Schluessels."""
    if not isinstance(schema, dict):
        return schema
    aus = dict(schema)

    items = aus.get("items")
    if isinstance(items, dict):
        aus["items"] = erzwinge_strikt_vertrag(items)

    props = aus.get("properties")
    if isinstance(props, dict):
        pflicht = set(aus.get("required") or [])
        neu_props = {}
        for feld, teil in props.items():
            teil = erzwinge_strikt_vertrag(teil)
            # Nur was vorher OPTIONAL war, wird null-faehig gemacht. Ein echtes
            # Pflichtfeld bleibt unberuehrt - sonst duerfte das Modell es
            # plotzlich weglassen, und der Zwang waere weg.
            neu_props[feld] = teil if feld in pflicht else _nullbar(teil)
        aus["properties"] = neu_props
        aus["required"] = list(props)
        aus["additionalProperties"] = False
    return aus


def als_response_format(schema: dict, name: str) -> dict:
    """Verpackt ein Schema so, wie die OpenAI-kompatiblen Endpunkte es
    erwarten. Alle fuenf Clients reichen `response_format` unveraendert durch.

    Der Strikt-Vertrag wird HIER erzwungen (12.08.2026) - siehe
    `erzwinge_strikt_vertrag()`. Damit kann kein Bauer ihn versehentlich
    verletzen, auch keiner, den es noch nicht gibt."""
    return {"type": "json_schema",
            "json_schema": {"name": name, "strict": True,
                            "schema": erzwinge_strikt_vertrag(schema)}}


def baue_szenario_schema(analyst) -> dict:
    """Das strikte Schema fuer den Szenario-Schaetzer (2026-08-10).

    EIGENER BAUER, nicht `baue_signal_schema()`: die Form ist grundverschieden.
    Der Szenario-Schaetzer waehlt keine Aktion, setzt keine Zonen und vergibt
    keine Konfidenz - er liefert eine VERTEILUNG ueber drei fest vorgegebene
    Ausgaenge. Ein gemeinsamer Bauer muesste beide Formen abdecken und waere
    an jeder Aenderung die schwaechste Stelle.

    ABGELEITET, nicht geschrieben - dieselbe Regel wie oben: Vokabular und
    Pflichtfelder kommen aus den Konstanten des Analysten, die auch sein
    Validator liest. Ein Schema, das vom Validator abweicht, erzeugt Fehler
    statt sie zu verhindern.

    Die Prozentangaben sind hier NICHT nullbar: eine Verteilung mit einem
    fehlenden Ausgang ist keine Verteilung. Bei den Signal-Analysten sind
    Zahlen nullbar, weil dort ein fehlender Wert eine gueltige Aussage ist
    ("kein Kursziel"); hier waere er ein kaputter Vertrag.
    """
    fehlend = [n for n in ("SZENARIEN", "BELEG_RICHTUNGEN", "BELEG_GEWICHTE",
                           "UNSICHERHEIT_WERTE", "MIN_BELEGE", "MAX_BELEGE",
                           "REQUIRED_SZENARIO_TOP_LEVEL_FIELDS")
               if not hasattr(analyst, n)]
    if fehlend:
        raise SchemaLuecke(f"Szenario-Analyst ohne Konstanten: {fehlend}")

    pflicht = list(analyst.REQUIRED_SZENARIO_TOP_LEVEL_FIELDS)
    return {
        "type": "object",
        "additionalProperties": False,
        "required": pflicht,
        "properties": {
            "belege": {
                "type": "array",
                "minItems": analyst.MIN_BELEGE,
                "maxItems": analyst.MAX_BELEGE,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["fakt", "richtung", "gewicht"],
                    "properties": {
                        "fakt": TXT,
                        "richtung": {"type": "string",
                                     "enum": list(analyst.BELEG_RICHTUNGEN)},
                        "gewicht": {"type": "string",
                                    "enum": list(analyst.BELEG_GEWICHTE)},
                    },
                },
            },
            "szenarien": {
                "type": "object",
                "additionalProperties": False,
                "required": list(analyst.SZENARIEN),
                "properties": {k: {"type": "number", "minimum": 0, "maximum": 100}
                               for k in analyst.SZENARIEN},
            },
            "bedingung_ziel": TXT,
            "widerlegung_ziel": TXT,
            "staerkstes_gegenargument": TXT,
            "unsicherheit": {"type": "string",
                             "enum": list(analyst.UNSICHERHEIT_WERTE)},
        },
    }


def baue_gegenpruefungs_schema(analyst) -> dict:
    """Das strikte Schema fuer den Anwalt des Gegenteils (2026-08-10).

    Winzig - vier Felder, zwei davon mit festem Vokabular. Trotzdem ein
    eigener Bauer und nicht in `baue_szenario_schema()` mitgefuehrt: die
    beiden Formen haben nichts gemeinsam ausser dem Anbieter, und ein Bauer
    fuer zwei Formen waere an jeder Aenderung die schwaechste Stelle.

    ABGELEITET aus den Konstanten des Gegenpruefers, wie ueberall hier."""
    fehlend = [n for n in ("KORREKTUR_RICHTUNGEN", "STAERKEN",
                           "REQUIRED_GEGENPRUEFUNG_FELDER")
               if not hasattr(analyst, n)]
    if fehlend:
        raise SchemaLuecke(f"Gegenpruefer ohne Konstanten: {fehlend}")
    return {
        "type": "object",
        "additionalProperties": False,
        "required": list(analyst.REQUIRED_GEGENPRUEFUNG_FELDER),
        "properties": {
            "angriff": TXT,
            "uebersehener_fakt": TXT,
            "korrektur_richtung": {"type": "string",
                                   "enum": list(analyst.KORREKTUR_RICHTUNGEN)},
            "staerke": {"type": "string", "enum": list(analyst.STAERKEN)},
        },
    }


JSON_OBJECT = {"type": "json_object"}

# WELCHER ANBIETER BEKOMMT DAS STRIKTE SCHEMA - gemessen am 2026-08-09, je
# Anbieter drei Arme (A json_object, A' Wiederholung als Rauschpegel,
# B json_schema) auf denselben echten Faktensaetzen.
#
#   OpenRouter  STRIKT. Einziger Anbieter mit echten Formfehlern: 2/38 und 2/20
#               in den json_object-Armen, 0 unter Schema. Die EROEFFNEN-Quote
#               bleibt unberuehrt (100 % / 100 % / 97 %), der Urteilseffekt
#               liegt im Rauschen (1 bewertbare Abweichung bei n=36).
#
#   Gemini      json_object. DISQUALIFIZIERT durch den EROEFFNEN-Waechter: die
#               Quote bricht von 76 % (A und A' identisch) auf 61 % ein, 16 pp.
#               Und es gaebe nichts zu gewinnen - 38/38 formgueltig in allen
#               drei Armen. Bei 35 Verlierern gegen 3 Gewinner sieht "vermeidet
#               Verluste" gut aus und ist doch nur Nichthandeln.
#
#   Z.ai        json_object. Unter Schema 3 bzw. 1 JSONDecodeError statt 0 - es
#               liefert dann GAR KEIN JSON mehr - und bei temperature=0.0 die
#               2,3-fache Dauer. Auf beiden Achsen schlechter.
#
#   Mistral     json_object. Ungemessen (402 bis ca. 31.08.), bleibt beim
#               heutigen Verhalten.
#
# KEIN KOMPLETTUMSTIEG also, sondern strikt genau dort, wo es etwas repariert.
_STRIKT_FUER_MODULE = ("openrouter",)


def baue_lage_schema(analyst) -> dict:
    """Rolle A - die Marktlage (2026-08-10).

    Drei Felder, KEIN Betrag (Umbau 10.08. abends): der Nutzer setzt seine
    Betraege selbst, das Risikomanagement ist deterministisch, und extern
    belegt sind Modelle bei der Positionsgroesse am schwaechsten. Das
    Designmuster der Praxis entkoppelt Richtungslogik von quantitativer
    Groessenbestimmung.

    ZWEI FELDER SEIT DEM 12.08., nicht mehr drei. Hier stand `traegt` mit drei
    festen Werten - eine Marktbreite-Kategorie. Sie ist mit der Marktbreite
    entfallen (Begruendung in `rolle_analyst.py`), und das Schema haette es
    beim naechsten strikten Lauf als erstes gemerkt: `analyst.TRAGFAEHIGKEIT`
    gibt es nicht mehr, die Luecken-Pruefung unten haette abgebrochen.

    DASS SIE ABGEBROCHEN HAETTE, IST DER PUNKT. `SchemaLuecke` ist genau dafuer
    da - ein Schema, das stillschweigend ein Feld weniger verlangt, waere die
    gefaehrlichere Variante gewesen. Der Waechter hat funktioniert; die
    Anpassung hier ist seine Antwort, keine Umgehung.

    Was die frueheren drei Werte begruendete, gilt unveraendert fuer jede
    Kategorie, die hier je wieder auftaucht: KEINE Auffangkategorie. Eine
    Mehrdeutigkeitsoption waere strukturell eine "Unknown"-Wahl, und die loest
    Abstention aus - im eigenen System von 93 % auf 3 % gemessen."""
    if not hasattr(analyst, "REQUIRED_FELDER"):
        raise SchemaLuecke("Rolle A ohne Konstanten: ['REQUIRED_FELDER']")
    if hasattr(analyst, "TRAGFAEHIGKEIT"):
        raise SchemaLuecke(
            "Rolle A traegt wieder TRAGFAEHIGKEIT - das Feld wurde am 12.08. "
            "mit der Marktbreite gestrichen. Wer es zurueckholt, muss auch "
            "dieses Schema und `rollen_eingabe` anfassen.")
    return {
        "type": "object",
        "additionalProperties": False,
        "required": list(analyst.REQUIRED_FELDER),
        "properties": {
            "lage": TXT,
            # Urteil je Assetklasse (Paket 3). `minItems` bewusst NICHT auf die
            # Zahl der Klassen gesetzt: fehlt eine, soll der Validator es
            # VERMERKEN, nicht das Schema die ganze Antwort verwerfen. Das
            # Schema fasst die Form, der Validator den Sinn.
            "klassen": {
                "type": "array", "minItems": 1,
                "maxItems": len(analyst.KLASSEN),
                "items": {
                    "type": "object", "additionalProperties": False,
                    "required": ["klasse", "einstufung", "warum"],
                    "properties": {
                        "klasse": {"type": "string",
                                   "enum": list(analyst.KLASSEN)},
                        "einstufung": {"type": "string",
                                       "enum": list(analyst.EINSTUFUNGEN)},
                        "warum": TXT,
                    },
                },
            },
            "belege": {"type": "array", "minItems": 2, "maxItems": 4,
                       "items": TXT},
        },
    }


def baue_trader_schema(analyst) -> dict:
    """Rolle BC - Aufbau beurteilen und handeln (2026-08-10).

KEIN `tranche_eur` (Umbau 10.08. abends): der Betrag wird aus der Zahl
    unabhaengiger Faktoren abgeleitet, nicht erfragt. Ein Feld im Schema waere
    eine Einladung, ihn doch zu nennen.

    `einstieg_eur` und `stop_eur` sind nur bei einer Handlung noetig - bei
    NICHTS_TUN waeren sie sinnlos. Diese Bedingung ("Pflicht, WENN aktion nicht
    NICHTS_TUN ist") laesst sich in einem Schema nicht ausdruecken; sie steht
    im Validator.

    Dasselbe gilt fuer alles Uebrige, was der Validator prueft und das Schema
    nicht kann: Stop unter Einstieg, unabhaengige Faktoren nicht mehr als
    Belege, Tranche nicht ueber der Obergrenze aus Rolle A, und eine
    Begruendung, die sich nicht selbst zurueckzieht. Das Schema fasst die FORM,
    der Validator den SINN."""
    fehlend = [n for n in ("BELEG_RICHTUNGEN", "BELEG_GEWICHTE",
                           "REQUIRED_FELDER")
               if not hasattr(analyst, n)]
    if fehlend:
        raise SchemaLuecke(f"Rolle BC ohne Konstanten: {fehlend}")
    from agent.empfehlung_vertrag import AKTIONEN
    return {
        "type": "object",
        "additionalProperties": False,
        "required": list(analyst.REQUIRED_FELDER),
        "properties": {
            "belege": {
                "type": "array", "minItems": 2, "maxItems": 8,
                "items": {
                    "type": "object", "additionalProperties": False,
                    "required": ["fakt", "richtung", "gewicht"],
                    "properties": {
                        "fakt": TXT,
                        "richtung": {"type": "string",
                                     "enum": list(analyst.BELEG_RICHTUNGEN)},
                        "gewicht": {"type": "string",
                                    "enum": list(analyst.BELEG_GEWICHTE)},
                    },
                },
            },
            "unabhaengige_faktoren": {"type": "number"},
            "aktion": {"type": "string", "enum": sorted(AKTIONEN)},
            "einstieg_eur": NUM,
            "stop_eur": NUM,
            "begruendung": TXT,
            "was_dagegen": TXT,
            "umgeworfen_durch": TXT,
            # Der Falsifikator, maschinenlesbar (12.08.2026, Paket 1). Der
            # Freitext bleibt fuehrend - diese beiden Felder machen ihn
            # PRUEFBAR. Nur so kann eine spaetere Stufe (V1) beantworten, ob
            # die Entscheidung inzwischen widerlegt ist, statt einen Satz zu
            # lesen. Beide duerfen null sein: nicht jede Beobachtung hat einen
            # Kurs oder ein Datum, und eine erzwungene Zahl waere erfunden.
            "umgeworfen_preis_eur": {"type": ["number", "null"]},
            "umgeworfen_bis": {"type": ["string", "null"]},
        },
    }


def response_format_fuer(llm_client, analyst_modulname: str) -> dict:
    """Das `response_format` fuer DIESEN Client und DIESEN Analysten.

    Warum die Fallunterscheidung hier und nicht an den zehn Aufrufstellen: es
    ist EINE Entscheidung. Zehnmal ausgeschrieben waeren es zehn Gelegenheiten
    auseinanderzulaufen - dasselbe Argument, mit dem die Schemata abgeleitet
    statt geschrieben werden.

    `analyst_modulname` ist `__name__` des aufrufenden Analysten. Ueber
    `sys.modules` aufgeloest, damit dieses Modul die Analysten nicht importieren
    muss (das waere zirkulaer, weil sie es hier importieren).

    Faellt irgendetwas aus - unbekannter Analyst, Schema-Luecke - wird
    `json_object` geliefert. Das ist der heutige Produktivzustand: im
    Zweifelsfall unveraendert weiterlaufen, nicht ausfallen.
    """
    import sys

    modul_des_clients = type(llm_client).__module__
    if not modul_des_clients.rsplit(".", 1)[-1] in _STRIKT_FUER_MODULE:
        return JSON_OBJECT
    analyst = sys.modules.get(analyst_modulname)
    if analyst is None:
        return JSON_OBJECT
    try:
        # Der Szenario-Schaetzer hat eine eigene Form - erkennbar an seiner
        # eigenen Pflichtfeld-Konstante, nicht am Modulnamen.
        # Rolle A und BC werden an EINDEUTIGEN Konstanten erkannt, nicht am
        # Modulnamen - `lage` gibt es nur in den Pflichtfeldern der Marktlage,
        # `unabhaengige_faktoren` nur beim Trader. Der Szenario-Schaetzer fuehrt
        # ebenfalls ein `BELEG_RICHTUNGEN`, deshalb reicht das allein nicht.
        #
        # ERKENNUNGSMERKMAL GEWECHSELT (12.08.2026). Hier stand
        # `hasattr(analyst, "TRAGFAEHIGKEIT")` - und genau diese Konstante wurde
        # am selben Tag mit der Marktbreite entfernt (siehe rolle_analyst.py).
        # Die Folge war kein sanfter Rueckfall, sondern ein AttributeError:
        # Rolle A fiel durch alle Zweige bis zu `baue_signal_schema()`, das
        # `REQUIRED_TOP_LEVEL_FIELDS` verlangt. JEDER strikte Aufruf der
        # Marktlage waere abgestuerzt.
        #
        # `REQUIRED_FELDER` ist das haltbarere Merkmal: es ist die Konstante,
        # aus der das Schema ohnehin gebaut wird. Verschwindet sie, gibt es
        # nichts mehr zu bauen - Merkmal und Inhalt koennen nicht mehr
        # auseinanderlaufen.
        if "lage" in getattr(analyst, "REQUIRED_FELDER", ()):
            schema = baue_lage_schema(analyst)
        elif "unabhaengige_faktoren" in getattr(analyst, "REQUIRED_FELDER", ()):
            schema = baue_trader_schema(analyst)
        elif hasattr(analyst, "REQUIRED_SZENARIO_TOP_LEVEL_FIELDS"):
            schema = baue_szenario_schema(analyst)
        elif hasattr(analyst, "REQUIRED_GEGENPRUEFUNG_FELDER"):
            schema = baue_gegenpruefungs_schema(analyst)
        else:
            schema = baue_signal_schema(analyst)
    except SchemaLuecke:
        # Ein neues Pflichtfeld ohne hinterlegte Form. Lieber json_object als
        # ein Schema, das die Antwort auf ein unvollstaendiges Vokabular
        # zwingt - der Validator wuerde sie hinterher ablehnen.
        return JSON_OBJECT
    except AttributeError as e:
        # DER DOCSTRING VERSPRACH DAS SCHON, DER CODE HIELT ES NICHT (Fund vom
        # 12.08.): "Faellt irgendetwas aus - unbekannter Analyst, Schema-Luecke
        # - wird json_object geliefert." Ein Analystenmodul, dessen Konstanten
        # sich geaendert haben, faellt aber durch alle Zweige bis in
        # `baue_signal_schema()` und stirbt dort an einem fehlenden Attribut.
        #
        # Genau das ist am 12.08. passiert und haette die Marktlage im strikten
        # Modus komplett lahmgelegt. Das Erkennungsmerkmal ist repariert; DIESE
        # Klammer ist das Netz darunter, damit derselbe Fehlertyp beim naechsten
        # Umbau eine Verschlechterung ist und kein Ausfall.
        #
        # Bewusst mit Log: ein stiller Rueckfall auf json_object ist genau die
        # Sorte fail-soft, die als fail-silent endet.
        import logging
        logging.getLogger(__name__).warning(
            "Kein striktes Schema fuer %s (%s: %s) - json_object. Der Analyst "
            "fuehrt nicht die Konstanten, die der Verteiler erwartet.",
            analyst_modulname, type(e).__name__, e)
        return JSON_OBJECT
    return als_response_format(schema, analyst_modulname.rsplit(".", 1)[-1])
