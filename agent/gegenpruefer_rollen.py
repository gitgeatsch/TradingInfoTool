# -*- coding: utf-8 -*-
"""Z1 - der TREUE-Pruefer der neuen Rollen-Kette (12.08.2026).

STAND: VERDRAHTET (Paket 12d, 13.08.2026). `pruefe_und_zaehle()` haengt
ihn in die Durchlaessigkeitszaehlung; `satz()` bringt einen Befund in die
Mail. WAS EIN VERSTOSS AUSLOEST, ist damit entschieden: ZAEHLEN, NICHT
VERWERFEN - dieselbe Begruendung wie beim Entscheider und beim Gate. Ein
Waechter, der selbst verwirft, macht seine eigene Wirkung unsichtbar.

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
    ungedeckt, geprueft = [], 0
    for z in _zahlen(text):
        if abs(z) in _HARMLOS or abs(z) != abs(z):      # NaN-sicher
            continue
        geprueft += 1
        if not any(abs(z - v) <= TOLERANZ for v in vorhanden):
            ungedeckt.append(z)
    # WIE VIELE ZAHLEN ES UEBERHAUPT ZU PRUEFEN GAB (15.5a, 13.08.).
    #
    # Ohne diese Angabe ist "kein Verstoss" zweideutig: es kann heissen "alle
    # Zahlen gedeckt" ODER "es stand gar keine Zahl da". Gezaehlt an neun
    # echten Antworten enthielten SECHS keine einzige Zahl im tragenden Satz -
    # die Werte stehen in den Belegen darunter. Diese Regel lief dort also
    # LEER, und die Null-Verstoss-Bilanz der Kette ist entsprechend schwaecher
    # belegt, als sie aussieht.
    #
    # Daraus folgt AUSDRUECKLICH NICHT, dass Begruendungen Zahlen enthalten
    # muessten. Ein Modell zu Zahlen im Fliesstext zu draengen erzeugt genau
    # die vorgetaeuschte Genauigkeit, die dieses Projekt an anderer Stelle
    # gerade entfernt hat. Es folgt nur: die Bilanz muss sagen, worauf sie
    # beruht.
    return {"regel": "Z-1", "ungedeckt": ungedeckt, "geprueft": geprueft,
            "verstoss": bool(ungedeckt),
            "grund": (f"{len(ungedeckt)} Zahl(en) stehen nicht in der Eingabe: "
                      f"{ungedeckt}") if ungedeckt else
                     (f"{geprueft} Zahl(en) gedeckt" if geprueft else
                      "keine Zahl im Text - nichts zu pruefen")}


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


# ---------------------------------------------------------------------------
# VERDRAHTUNG (Paket 12d, 2026-08-13)
#
# Bis hierher stand ueber diesem Modul: "GEBAUT, NICHT VERDRAHTET. Kein
# Aufrufer." Genau das war Paket 12d. Der Modulkopf oben sagt auch, was beim
# Einhaengen zu entscheiden ist: WAS EIN VERSTOSS AUSLOEST. Die Antwort steht
# im selben Absatz - "eine Messung zaehlt, der Betrieb verwirft" - und fuer
# diese Kette lautet sie: ZAEHLEN, NICHT VERWERFEN.
#
# Warum nicht verwerfen: dieselbe Begruendung wie beim Entscheider und beim
# Gate. Ein Waechter, der selbst verwirft, macht seine eigene Wirkung
# unsichtbar - man sieht nur noch, was durchkam, nie was er weggenommen hat.
# Und das System hat monatelang nicht gekauft; ein weiterer stiller Filter ist
# genau das Risiko, das gerade beseitigt wurde.
#
# Was ein Verstoss STATTDESSEN tut: er wird in der Durchlaessigkeit vermerkt
# (Stufe "lagebild" bzw. "urteil") und steht in der Mail. Sichtbar, zaehlbar,
# rueckwirkend pruefbar.
def pruefe_und_zaehle(ausgabe: dict, eingabe, *, symbol: str,
                      durchlauf=None, stufe: str = "lagebild",
                      gleichlauf_wert: str | None = None) -> dict:
    """Z-1 bis Z-3 fuer EINE Ausgabe, plus Eintrag in die Durchlaessigkeit.

    `durchlauf` ist ein `rollen_gate.Durchlauf` oder None. Ohne ihn prueft die
    Funktion nur - das ist der Fall in Messlaeufen, wo es keine Stufenzaehlung
    gibt.

    GIBT DAS ERGEBNIS ZURUECK, VERWIRFT NICHTS. Der Aufrufer sieht `verstoss`
    und entscheidet; hier wird nur festgehalten."""
    ergebnis = pruefe(ausgabe, eingabe, gleichlauf_wert)
    if durchlauf is not None and hasattr(durchlauf, "z1_zahlen"):
        # Auch wenn NICHTS zu pruefen war - gerade dann.
        # DIE STRUKTUR VON `pruefe()` NACHGESEHEN, NICHT GERATEN: sie gibt
        # `{"verstoss", "verletzt", "einzeln"}` - die Regeln stehen unter
        # `einzeln`, nicht unter ihrem Namen auf oberster Ebene.
        _z1 = next((e for e in (ergebnis.get("einzeln") or [])
                    if isinstance(e, dict) and e.get("regel") == "Z-1"), {})
        durchlauf.z1_zahlen(_z1.get("geprueft", 0))
    if durchlauf is not None:
        if ergebnis["verstoss"]:
            # BESTANDEN UND VERMERKT. `verloren()` waere falsch: die Stufe ist
            # durchlaufen, die Ausgabe liegt vor. Ein Treuebruch ist ein
            # BEFUND an ihr, kein Ausscheiden - sonst zaehlte die
            # Durchlaessigkeit etwas anderes als sie behauptet.
            durchlauf.bestanden(symbol, stufe)
            durchlauf.z1_verstoss(symbol, ergebnis["verletzt"])
        else:
            durchlauf.bestanden(symbol, stufe)
    return ergebnis


def satz(ergebnis: dict) -> list[str]:
    """Der Z1-Befund fuer die Mail - nur wenn es etwas zu sagen gibt.

    Eine Fussnote "alle Zahlen gedeckt" unter jeder Nachricht waere Fuellstoff;
    wer nichts findet, schweigt."""
    if not ergebnis or not ergebnis.get("verstoss"):
        return []
    z = ["Treuepruefung der Eingabe (Z1) hat angeschlagen:"]
    for einzeln in ergebnis.get("einzeln", []):
        if einzeln.get("verstoss"):
            z.append(f"  {einzeln['regel']}: {einzeln.get('grund', '')}")
    z.append("  Das ist kein Urteil ueber die Empfehlung, sondern ueber ihre "
             "Treue zu den uebergebenen Zahlen.")
    return z


# ---------------------------------------------------------------------------
# Z.AI AUF DEN FAKTEN DER NEUEN KETTE (Paket 12d, 13.08.2026)
#
# DAS PROBLEM. `gegenpruefung.baue_objektive_fakten()` erwartet das Vokabular
# der ALTEN Kette: `rsi`, `trend_label`, `regime`, `funding_rate_stunde`,
# drei Confluence-Zaehler, `optionsmarkt_skew`. Die neue Kette produziert
# nichts davon - sie liefert SAETZE (Lagebild L1-L6, Befund je Asset). Wer die
# alte Funktion mit der neuen Kette aufruft, bekommt ein fast leeres
# Faktenpaket und einen Richtungsabgleich ohne Grundlage.
#
# DIE LOESUNG IST KEINE UEBERSETZUNG ZURUECK. Aus Saetzen wieder RSI-Zahlen zu
# gewinnen waere Rueckbau; die neue Kette hat die Zahlen bewusst nicht im
# Prompt (Kapitel 11.6). Stattdessen bekommt Z.ai, was die neue Kette WIRKLICH
# hat: die Faktensaetze selbst.
#
# WAS BEWUSST NICHT MITGEHT - dieselbe Anker-Vermeidung wie in der alten
# Fassung: keine `aktion`, keine `richtung`, kein Betrag, keine Zone. Z.ai soll
# aus den Fakten eine EIGENE Richtung ableiten; wer ihr die Antwort zeigt,
# misst nur noch das Echo.
_VERBOTEN_FUER_RICHTUNG = ("aktion", "richtung", "einstieg_eur", "stop_eur",
                           "ziel_eur", "tranche_eur", "betrag_eur",
                           "confidence_pct", "konfidenz", "unabhaengige_faktoren")


def objektive_fakten_aus_rollen(symbol: str, lagebild_saetze, befund_saetze,
                                gleichlauf_wert: str | None = None) -> dict:
    """Faktenpaket fuer `gegenpruefung.leite_eigene_richtung()` aus den Saetzen
    der neuen Kette.

    Gibt bewusst SAETZE statt Kennzahlen zurueck - das ist das Format, das die
    neue Kette hat. Z.ai bekommt damit dieselbe Grundlage wie Rolle BC, nur
    ohne deren Antwort.

    `gleichlauf_wert` ist die einzige GERECHNETE Groesse, die mitgeht: sie ist
    ein Festpunkt ausserhalb des Modells und genau deshalb wertvoll fuer einen
    Gegenpruefer."""
    def sauber(saetze):
        # ERST None AUSSORTIEREN, DANN str(). Andersherum wird aus `None` der
        # String "None" - der ist nicht leer, rutscht durch und stuende dann
        # woertlich in den Fakten, die an Z.ai gehen.
        return [str(s).strip() for s in (saetze or [])
                if s is not None and str(s).strip()]

    fakten = {"symbol": symbol,
              "marktlage": sauber(lagebild_saetze),
              "asset_fakten": sauber(befund_saetze)}
    if gleichlauf_wert:
        fakten["gleichlauf_gerechnet"] = gleichlauf_wert
    return fakten


def enthaelt_anker(fakten: dict) -> list[str]:
    """Welche verbotenen Schluessel stecken drin? Leer = sauber.

    EIN WAECHTER, KEIN FILTER - er entfernt nichts. Wer beim Bauen des
    Faktenpakets eine Aktion mitschickt, soll das sehen, nicht stillschweigend
    korrigiert bekommen: die naechste Stelle wuerde denselben Fehler machen."""
    treffer = []
    for schluessel in _VERBOTEN_FUER_RICHTUNG:
        if schluessel in fakten:
            treffer.append(schluessel)
    # Auch in den Saetzen selbst - eine Aktion im Klartext ist derselbe Anker
    # wie ein Feld, das so heisst.
    # WORTGRENZEN, KEIN SUBSTRING. Die erste Fassung fand "KAUFEN" in
    # "NACHKAUFEN" und meldete zwei Anker, wo einer stand. Ein Waechter, der
    # falsch Alarm schlaegt, wird nach dem dritten Mal ignoriert - und dann
    # auch der richtige Alarm.
    import re

    text = " ".join(str(w) for w in fakten.values() if not isinstance(w, dict)).upper()
    from agent.empfehlung_vertrag import AKTIONEN
    for aktion in AKTIONEN:
        if re.search(rf"\b{aktion}\b", text):
            treffer.append(f"Aktion '{aktion}' im Klartext")
    return treffer
