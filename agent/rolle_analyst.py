# -*- coding: utf-8 -*-
"""Rolle A - die Marktlage. Ein Aufruf fuer alle Assets (10.08.2026).

WAS SIE BEANTWORTET, und nur das: *wie viel Risiko ist heute angemessen?*
Sie sieht kein einzelnes Asset und trifft keine Handelsentscheidung. Damit kann
sie nicht vom Einzelfall her rationalisieren - der haeufigste Weg, auf dem eine
Marktbeurteilung zur Nachbegruendung einer schon gefallenen Entscheidung wird.

SIE LAEUFT EINMAL JE DURCHGANG, nicht je Asset. Bei 40 Coins ist das 1 Aufruf
statt 40.

SIE NENNT KEINEN BETRAG (Umbau 10.08. abends, nach Nutzereinwand). Die erste
Fassung liess sie einen Hoechstbetrag waehlen - 100, 300 oder 500 EUR. Das war
eine erfundene Aufgabe: der Nutzer setzt seine Betraege selbst, und das
Risikomanagement ist deterministisch implementiert (RM-1 bis RM-7,
Cash-Reserve, vier Positionsgroessen-Deckel). Ein Modell einen Betrag waehlen
zu lassen, den ohnehin ein Gate begrenzt, fuegt nichts hinzu ausser einer
Fehlerquelle.

Extern belegt: *"Statt LLMs die Positionsgroesse eigenstaendig bestimmen zu
lassen, sind sie am wirksamsten in hybriden Systemen, die LLM-Schlussfolgerung
mit traditionellen quantitativen Risikoregeln verbinden."* Und das
Designmuster dazu: eine zweistufige Struktur, die **Richtungslogik von der
quantitativen Positionsgroessenbestimmung entkoppelt.**

DREI ENTWURFSENTSCHEIDUNGEN GEGEN BEKANNTE BIAS-EFFEKTE:

1. **KEINE "unklar"-Option.** Die drei Kategorien von `traegt` sind
   Beschreibungen, keine davon eine Enthaltung. Eine Mehrdeutigkeitskategorie
   waere strukturell eine "Unknown"-Option, und die loest laut Literatur
   Abstention aus - im eigenen System von 93 % auf 3 % gemessen.

2. **KEINE KONFIDENZ.** Nirgends wird nach einer Sicherheit in Prozent gefragt.
   Verbalisierte Konfidenz ist extern belegt schlecht kalibriert, und im eigenen
   System vorhergesagt 77,5 % gegen tatsaechlich 33,3 %.

3. **KEINE VORSICHTSSPRACHE IM PROMPT.** Kein "sei zurueckhaltend", kein
   "beruecksichtige die Risiken". Negative Rahmung treibt Modelle belegt in
   uebermaessige Risikoaversion. Die Fakten tragen die Vorsicht, wo sie noetig
   ist; der Prompt tut es nicht.

WAS SIE STATTDESSEN LIEFERT: eine Beschreibung. Sie muss die Zukunft nicht
vorhersagen, um nuetzlich zu sein - dass nur 4 von 20 Coins ueber ihrer
200-Tage-Linie stehen, ist ein Fakt, den der Trader gegen seine anderen Belege
abwaegt. Genau das ist die Sprachaufgabe.
"""
from __future__ import annotations

REQUIRED_FELDER = ("lage", "traegt", "belege")

# Beschreibend, nicht wertend - und ohne Mittelweg-Kategorie. "gemischt" heisst
# hier nicht "unklar", sondern benennt eine konkrete Konstellation: ein Teil des
# Marktes traegt, ein anderer nicht. Das ist eine Aussage, keine Enthaltung.
TRAGFAEHIGKEIT = ("breit_getragen", "schmal_getragen", "gemischt")

_KOPF = """Du beurteilst die Lage eines Marktes - nicht ein einzelnes \
Wertpapier. Du bekommst Kennzahlen ueber die Gesamtheit der beobachteten Werte \
und das uebergeordnete Umfeld.

DEINE AUFGABE, in dieser Reihenfolge:"""

_SCHLUSS = """Antworte AUSSCHLIESSLICH mit JSON:
{"lage": "<zwei bis drei Saetze>",
 "traegt": "breit_getragen|schmal_getragen|gemischt",
 "belege": ["<Beobachtung mit Wert>", ...]}"""

_LAGE = ("LAGE", "Beschreibe in zwei bis drei Saetzen, was diesen Markt gerade "
                 "kennzeichnet. Nenne die Zahlen, auf die du dich stuetzt, beim "
                 "Namen.")
_TRAGFAEHIGKEIT = ("TRAGFAEHIGKEIT",
                   "Wird die aktuelle Bewegung von vielen Werten getragen "
                   "(breit_getragen), von wenigen (schmal_getragen), oder tragen "
                   "einige Teile des Marktes waehrend andere zurueckbleiben "
                   "(gemischt)?")
_BELEGE = ("BELEGE", "Zwei bis vier Beobachtungen aus den Daten, die deine "
                     "Einschaetzung tragen. Jede mit dem Wert, auf den sie sich "
                     "stuetzt. Erfinde nichts hinzu.")

# DER BETRAGSBLOCK IST NICHT GELOESCHT, SONDERN SCHALTBAR (11.08. abends).
#
# Befund: Der Umbau vom 10.08. entfernte das Schemafeld und die Pflichtfelder,
# liess aber DIESEN Prompt-Punkt stehen. Beide Rollen wurden seither bei jedem
# Aufruf aufgefordert, eine Zahl zu nennen, die das Schema nicht entgegennimmt -
# der Modul-Docstring oben ("SIE NENNT KEINEN BETRAG") und der Prompt darunter
# widersprachen einander. R-A2 stand im Regelwerk und war nicht gebaut.
#
# Warum schaltbar statt weg: Diese Fassung ist der VERGLEICHSARM der gepaarten
# Messung, die die Wirkung der Betragsfrage beziffern soll. Wer den Text
# loescht, zerstoert den Arm, bevor er gebraucht wird - derselbe Fehler wie die
# ueberschriebene ANKER-Liste (Arbeitsstand 7.10, K3). Nach der Messung
# entscheidet der Nutzer ueber die endgueltige Entfernung.
_BETRAGSFRAGE = ("HOECHSTBETRAG",
                 "Welcher Einzelbetrag ist in dieser Lage angemessen - 100, 300 "
                 "oder 500 Euro? Das ist eine Obergrenze fuer eine einzelne "
                 "Position, keine Empfehlung zu handeln. Ob ueberhaupt gehandelt "
                 "wird, entscheidet ein anderer Schritt.")


def _baue_prompt(mit_betragsfrage: bool) -> str:
    """Beide Fassungen aus denselben Teilen - sie duerfen sich NUR im
    Betragsblock unterscheiden.

    Von Hand gepflegte Zwillingstexte driften auseinander; dann misst ein
    gepaarter Lauf zwei Unterschiede und schreibt beide dem einen zu."""
    schritte = [_LAGE, _TRAGFAEHIGKEIT, _BELEGE]
    if mit_betragsfrage:
        schritte.insert(2, _BETRAGSFRAGE)   # vor BELEGE, wie die Fassung 10.08.
    teile = [f"{i}. {kopf}: {text}" for i, (kopf, text) in enumerate(schritte, 1)]
    return "\n\n".join([_KOPF, *teile, _SCHLUSS])


SYSTEM_PROMPT_ANALYST = _baue_prompt(mit_betragsfrage=False)

# Nur fuer die gepaarte Messung. NICHT im Betrieb verwenden.
SYSTEM_PROMPT_ANALYST_MIT_BETRAG = _baue_prompt(mit_betragsfrage=True)

# JEDER MESSBEFUND GEHOERT ZU EINEM PROMPT-STAND (Nutzereinwand 11.08.: die
# alte Loesung muss in Doku UND Messbefunden sauber getrennt bleiben). Ein
# Messskript schreibt diesen Wert in seine Ausgabe; ein Befund ohne Stand ist
# nicht zuordenbar und damit nicht wiederverwendbar.
#
#   2026-08-10a  erste Fassung der Rollen-Ebene, Lagebild nennt einen Betrag
#   2026-08-10b  Betrags-Umbau: `max_tranche_eur` aus Schema und Pflichtfeldern
#                entfernt - ABER die Prompt-Frage blieb stehen (unbemerkt).
#                Alle Befunde vom 10./11.08. gehoeren hierher, auch 7.7.
#   2026-08-11   Betragsfrage aus dem Betriebsprompt entfernt, als schaltbarer
#                Vergleichsarm erhalten. R-A2 erstmals tatsaechlich gebaut.
PROMPT_STAND = "2026-08-11"


class AnalystAntwortUngueltig(ValueError):
    """Die Antwort erfuellt ihren Vertrag nicht."""


def validiere(antwort: dict) -> dict:
    """Prueft die Marktlage. LEHNT FAST NICHTS AB - degradiert feldweise.

    Nutzereinwand 10.08., zweite Runde: *"bin fast der Meinung hier noch weniger
    restriktiv zu sein - z.B. wenn statt Bullenmarkt 'bullisch' steht finde ich
    etwas hart."*

    Er hat recht, und "bullisch" ist das beste Beispiel: das ist keine
    Vokabel-Abweichung, sondern eine ANDERE FRAGE beantwortet - Richtung statt
    Breite. Trotzdem koennen `lage` und `belege` brauchbar sein. Die ganze
    Antwort dafuer wegzuwerfen ist unverhaeltnismaessig.

    DESHALB BLEIBT NUR EIN HARTER GRUND: weder Lagebeschreibung noch Belege -
    dann hat diese Rolle nichts geliefert. Alles andere wird zurechtgerueckt,
    ersetzt oder vermerkt.

    (Korrigiert 11.08.: hier stand "ohne einen brauchbaren Betrag ... sie
    existiert, um genau diese eine Zahl zu setzen". Das beschrieb die Fassung
    VOR dem Betrags-Umbau vom 10.08. und widersprach dem Code darunter.)

    `traegt` faellt bei Unzuordenbarkeit auf "gemischt" zurueck. Das ist KEINE
    Unknown-Option durch die Hintertuer: das Modell sieht drei echte Kategorien,
    der Rueckfall passiert im Code und steht im Protokoll."""
    from agent.antwort_normalisierung import (Protokoll, naechstes_wort,
                                              kuerze_liste)

    if not isinstance(antwort, dict):
        raise AnalystAntwortUngueltig("Antwort ist kein Objekt")

    prot = Protokoll()

    # --- Der EINZIGE harte Grund -------------------------------------------
    # Ohne eine Lagebeschreibung hat diese Rolle nichts geliefert. Alles andere
    # wird zurechtgerueckt.
    if not str(antwort.get("lage") or "").strip() and not antwort.get("belege"):
        raise AnalystAntwortUngueltig(
            "weder Lagebeschreibung noch Belege - nichts geliefert")
    # --- Alles andere wird gerettet ----------------------------------------
    wort, hinweis = naechstes_wort(antwort.get("traegt"), TRAGFAEHIGKEIT)
    if wort is None:
        wort = "gemischt"
        hinweis = (f"traegt={antwort.get('traegt')!r} passt zu keiner Kategorie - "
                   f"als 'gemischt' gewertet")
    antwort["traegt"] = wort
    prot.dazu(hinweis)

    if not str(antwort.get("lage") or "").strip():
        antwort["lage"] = ""
        prot.dazu("keine Lagebeschreibung geliefert")

    belege = antwort.get("belege")
    belege = [b for b in belege if str(b).strip()] if isinstance(belege, list) else []
    if not belege:
        prot.dazu("keine Belege geliefert")
    elif len(belege) < 2:
        prot.dazu(f"nur {len(belege)} Beleg statt der erbetenen zwei")
    belege, hinweis = kuerze_liste(belege, 4, "Belege")
    prot.dazu(hinweis)
    antwort["belege"] = belege

    if prot:
        antwort["_korrekturen"] = str(prot)
    return antwort
