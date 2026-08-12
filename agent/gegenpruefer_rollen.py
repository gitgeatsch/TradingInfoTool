# -*- coding: utf-8 -*-
"""Z1 - der TREUE-Pruefer der neuen Rollen-Kette (12.08.2026).

STAND: GEBAUT, NICHT VERDRAHTET. Kein Aufrufer. Wer ihn einhaengt, muss
entscheiden, was ein Verstoss ausloest - dieses Modul entscheidet es nicht.

NAME KORRIGIERT NACH NUTZEREINWAND. Er hiess hier zuerst "der Gegenpruefer der
neuen Kette". Das war vereinnahmend: der Gegenpruefer dieses Projekts ist die
Z.ai-Pruefung (`agent/krypto/gegenpruefung.py`), und sie macht etwas anderes.

    Z1 hier   prueft die TREUE zur Eingabe. Kostenlos, kann sich nicht irren,
              faengt Erfindung
    Z.ai      prueft das URTEIL - wo ist die schwaechste Stelle. Ein Aufruf,
              kann sich irren, faengt Denkfehler

Beide ersetzen einander NICHT. Details im Abgleich, Faktenmappe Kapitel 13.

DIE LUECKE. Die alte Kette hatte einen Gegenpruefer: `szenario_gegenpruefer.py`,
ein zweiter LLM-Aufruf als "Anwalt des Gegenteils". Die neue Kette hatte
nichts - beide Rollen antworteten ungeprueft.

WARUM DIESER HIER NICHT AUS EINEM LLM BESTEHT. Drei Gruende, alle gemessen:

    Ein pruefendes Modell kann selbst erfinden. Es haette dieselbe Schwaeche
    wie das gepruefte und keinen Festpunkt ausserhalb.

    LLM-Qualitaet ist bei uns vorab nicht messbar (Memory: Mistral -27,38 R
    ueber 38 Faelle, ohne dass ein Vorab-Test es gezeigt haette). Ein
    Gegenpruefer, dessen eigene Guete unbekannt ist, verschiebt das Problem.

    Er kostet je Anker einen Aufruf. Bei 20/min und 1.000/Tag ist das die
    knappste Ressource des Projekts.

WAS ER STATTDESSEN PRUEFT: die Zusagen, die im Prompt STEHEN. Der Prompt der
Rolle Lagebild sagt woertlich *"Erfinde nichts hinzu"* und *"Nenne die Zahlen,
auf die du dich stuetzt, beim Namen"*. Beides ist nachpruefbar, ohne zu raten -
und genau das war bisher nie geprueft.

    Z-1  ZAHLENDECKUNG   Jede Zahl in der Ausgabe muss in der Eingabe stehen.
                         Das ist die woertliche Pruefung von "erfinde nichts".
    Z-2  RICHTUNGSTREUE  Behauptet die Ausgabe Gleich- oder Gegenlauf, muss das
                         zum gerechneten `gleichlauf` passen.
    Z-3  ZUSPITZUNG      Delegiert an `waechter_zuspitzung` - ein Grad ohne
                         Deckung in den Perzentilen der Eingabe.
    Z-4  LEERLAUF        Sagt die Ausgabe ueber viele Anker hinweg dasselbe,
                         ist sie ein konstantes Feld (R-T6) und unterscheidet
                         nichts. Wird ueber einen Lauf gezaehlt, nicht je Fall.

ABGRENZUNG ZU DEN BESTEHENDEN WAECHTERN. `enthaelt_werturteile` und
`finde_konstanten` pruefen EINGABEN. `waechter_zuspitzung` prueft die Ausgabe
auf unbelegte Grade. Dieser hier prueft die Ausgabe auf **Deckung in der
Eingabe** - eine dritte Frage: nicht "zu stark formuliert", sondern "steht das
ueberhaupt da".

WAS ER NICHT KANN, ehrlich benannt: er prueft die TREUE zur Eingabe, nicht die
GUETE des Urteils. Ob "uneinheitliche Maerkte" ein guter Grund ist, nichts zu
tun, sagt er nicht - das entscheidet eine Wirkungsmessung, kein Waechter.
"""
from __future__ import annotations

import re

# Zahlen mit Dezimaltrenner in beiden Schreibweisen, mit optionalem Vorzeichen.
_ZAHL = re.compile(r"[-+]?\d{1,3}(?:[.,]\d+)?|\d{4,}")

# Woerter, mit denen eine Ausgabe Gleich- oder Gegenlauf BEHAUPTET. Nur diese
# werden gegen `gleichlauf` gehalten - alles andere ist keine Richtungsaussage.
_GLEICH = ("gleichschritt", "im einklang", "gleichlaeufig", "gleichlaufend",
           "parallel", "durchweg", "alle drei", "saemtliche maerkte",
           "auf breiter front", "ausnahmslos")
_GEGEN = ("gegenlaeufig", "auseinander", "uneinheitlich", "waehrend",
          "im gegensatz", "divergenz", "divergieren", "entgegengesetzt")

# Wieviel Abweichung eine genannte Zahl haben darf, um noch als "aus der
# Eingabe" zu gelten. Modelle runden 39,0 auf 39 - das ist kein Erfinden.
TOLERANZ = 0.55

# Zahlen, die keine Aussage tragen und deshalb nicht gedeckt sein muessen:
# Jahreszahlen, Aufzaehlungen, Fenstergroessen aus dem Prompt selbst.
_HARMLOS = {0, 1, 2, 3, 4, 5, 10, 21, 50, 60, 100, 200, 250}


def _normal(t: str) -> str:
    t = (t or "").lower()
    for a, b in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss")):
        t = t.replace(a, b)
    return t


def _zahlen(text: str) -> list[float]:
    aus = []
    for roh in _ZAHL.findall(text or ""):
        try:
            aus.append(float(roh.replace(",", ".")))
        except ValueError:
            continue
    return aus


def pruefe_zahlendeckung(ausgabe: dict, eingabe) -> dict:
    """Z-1: steht jede genannte Zahl auch in der Eingabe?

    Die Toleranz ist Absicht, nicht Nachlaessigkeit. Ein Modell, das aus
    "39,0 % unter seinem Schlusskurs" den Satz "rund 39 % im Minus" macht, hat
    nichts erfunden - es hat gerundet, wie es soll. Was diese Pruefung fangen
    soll, ist die Zahl, die NIRGENDS steht: der klassische Beleg mit erfundenem
    Wert, der sich sonst durch die ganze Kette traegt."""
    quelle = " ".join(eingabe) if isinstance(eingabe, (list, tuple)) else str(eingabe)
    vorhanden = _zahlen(quelle)
    text = " ".join([str(ausgabe.get("lage") or "")]
                    + [str(b) for b in (ausgabe.get("belege") or [])])
    ungedeckt = []
    for z in _zahlen(text):
        if abs(z) in _HARMLOS or abs(z) != abs(z):      # NaN-sicher
            continue
        if not any(abs(z - v) <= TOLERANZ for v in vorhanden):
            ungedeckt.append(z)
    return {"regel": "Z-1", "ungedeckt": ungedeckt,
            "verstoss": bool(ungedeckt),
            "grund": (f"{len(ungedeckt)} Zahl(en) stehen nicht in der Eingabe: "
                      f"{ungedeckt}") if ungedeckt else "alle Zahlen gedeckt"}


def pruefe_richtungstreue(ausgabe: dict, gleichlauf_wert: str | None) -> dict:
    """Z-2: passt eine behauptete Richtung zum gerechneten Gleichlauf?

    Nur wenn die Ausgabe ueberhaupt etwas behauptet. Schweigen ist kein
    Verstoss - der Prompt verlangt keine Richtungsaussage."""
    if not gleichlauf_wert or gleichlauf_wert == "unbekannt":
        return {"regel": "Z-2", "verstoss": False,
                "grund": "kein gerechneter Gleichlauf - kein Festpunkt"}
    t = _normal(str(ausgabe.get("lage") or ""))
    sagt_gleich = any(w in t for w in _GLEICH)
    sagt_gegen = any(w in t for w in _GEGEN)
    if not (sagt_gleich or sagt_gegen):
        return {"regel": "Z-2", "verstoss": False,
                "grund": "die Ausgabe behauptet keine Richtung"}
    ist_gleich = gleichlauf_wert.startswith("gleichlaeufig")
    # Beides zugleich zu sagen ist kein Widerspruch, sondern der Normalfall
    # bei `uneinheitlich` ("BTC faellt, WAEHREND Aktien steigen").
    if sagt_gleich and sagt_gegen:
        widerspruch = False
    else:
        widerspruch = (sagt_gleich and not ist_gleich) or (sagt_gegen and ist_gleich)
    return {"regel": "Z-2", "verstoss": widerspruch,
            "gerechnet": gleichlauf_wert,
            "behauptet": "gleichlaeufig" if sagt_gleich else "gegenlaeufig",
            "grund": (f"Ausgabe sagt {'Gleich' if sagt_gleich else 'Gegen'}lauf, "
                      f"gerechnet ist {gleichlauf_wert}") if widerspruch
                     else "Richtung passt zum gerechneten Gleichlauf"}


def pruefe(ausgabe: dict, eingabe, gleichlauf_wert: str | None = None) -> dict:
    """Alle Einzelpruefungen zu einem Befund - Z-1, Z-2 und Z-3.

    `verstoss` ist wahr, sobald EINE harte Pruefung anschlaegt. Der Aufrufer
    entscheidet, was er damit tut: eine Messung zaehlt, der Betrieb verwirft.
    Diese Trennung ist Absicht - ein Waechter, der selbst verwirft, macht seine
    eigene Wirkung unsichtbar."""
    from agent.waechter_zuspitzung import pruefe as pruefe_zuspitzung
    text = " ".join([str(ausgabe.get("lage") or "")]
                    + [str(b) for b in (ausgabe.get("belege") or [])])
    z1 = pruefe_zahlendeckung(ausgabe, eingabe)
    z2 = pruefe_richtungstreue(ausgabe, gleichlauf_wert)
    z3 = pruefe_zuspitzung(text, eingabe)
    z3["regel"] = "Z-3"
    einzeln = [z1, z2, z3]
    return {"verstoss": any(p.get("verstoss") for p in einzeln),
            "verletzt": [p["regel"] for p in einzeln if p.get("verstoss")],
            "einzeln": einzeln}


def zaehle_leerlauf(ausgaben: list[dict]) -> dict:
    """Z-4: sagt die Rolle ueber viele Anker hinweg dasselbe?

    NICHT je Fall pruefbar - ein einzelnes Lagebild kann nicht 'konstant' sein.
    Deshalb steht das hier getrennt und wird ueber einen ganzen Lauf gerechnet.

    Gemessen wird an den ZAHLEN der Ausgabe, nicht am Wortlaut. Zwei
    Formulierungen derselben Lage sollen als gleich zaehlen; zwei verschiedene
    Lagen mit denselben Zahlen waeren dagegen der Befund, den wir suchen."""
    if not ausgaben:
        return {"regel": "Z-4", "faelle": 0, "verstoss": False,
                "grund": "keine Ausgaben"}
    schluessel = [tuple(sorted(_zahlen(
        " ".join([str(a.get("lage") or "")]
                 + [str(b) for b in (a.get("belege") or [])]))))
        for a in ausgaben]
    verschieden = len(set(schluessel))
    anteil = verschieden / len(ausgaben)
    return {"regel": "Z-4", "faelle": len(ausgaben),
            "verschiedene": verschieden, "anteil": round(anteil, 3),
            "verstoss": verschieden <= 1,
            "grund": (f"{verschieden} verschiedene Ausgaben auf "
                      f"{len(ausgaben)} Anker")}
