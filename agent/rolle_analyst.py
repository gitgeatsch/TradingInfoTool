# -*- coding: utf-8 -*-
"""Rolle A - die Marktlage. Ein Aufruf fuer alle Assets (10.08.2026).

WAS SIE BEANTWORTET, und nur das: *wie viel Risiko ist heute angemessen?*
Sie sieht kein einzelnes Asset und trifft keine Handelsentscheidung. Damit kann
sie nicht vom Einzelfall her rationalisieren - der haeufigste Weg, auf dem eine
Marktbeurteilung zur Nachbegruendung einer schon gefallenen Entscheidung wird.

SIE LAEUFT EINMAL JE DURCHGANG, nicht je Asset. Bei 40 Coins ist das 1 Aufruf
statt 40.

DREI ENTWURFSENTSCHEIDUNGEN GEGEN BEKANNTE BIAS-EFFEKTE:

1. **KEINE "unklar"- oder "neutral"-Option.** Die einzige harte Ausgabe ist eine
   Tranche - 100, 300 oder 500 EUR. Jede der drei ist eine HANDLUNGSGROESSE,
   keine davon eine Enthaltung. Das ist Absicht: eine Mehrdeutigkeitskategorie
   waere strukturell eine "Unknown"-Option, und die loest laut Literatur
   Abstention aus. Im eigenen System hat genau dieser Mechanismus die
   EROEFFNEN-Quote von 93 % auf 3 % gedrueckt. Ob ueberhaupt gehandelt wird,
   entscheidet Rolle BC - nicht diese hier.

2. **KEINE KONFIDENZ.** Nirgends wird nach einer Sicherheit in Prozent gefragt.
   Verbalisierte Konfidenz ist extern belegt schlecht kalibriert, und im eigenen
   System vorhergesagt 77,5 % gegen tatsaechlich 33,3 %.

3. **KEINE VORSICHTSSPRACHE IM PROMPT.** Kein "sei zurueckhaltend", kein
   "beruecksichtige die Risiken". Negative Rahmung treibt Modelle belegt in
   uebermaessige Risikoaversion. Die Fakten tragen die Vorsicht, wo sie noetig
   ist; der Prompt tut es nicht.

WARUM DIE TRANCHE UND NICHT EINE PROZENTZAHL: der Nutzer setzt seine
Investitionssumme selbst - 100/300/500 EUR, seit 02.08. festgehalten. Das Modell
WAEHLT aus dreien, es rechnet keine Positionsgroesse. Rechnen ist die Aufgabe,
bei der Sprachmodelle nachweislich schwach sind.
"""
from __future__ import annotations

TRANCHEN_EUR = (100, 300, 500)

REQUIRED_FELDER = ("lage", "traegt", "max_tranche_eur", "belege")

# Beschreibend, nicht wertend - und ohne Mittelweg-Kategorie. "gemischt" heisst
# hier nicht "unklar", sondern benennt eine konkrete Konstellation: ein Teil des
# Marktes traegt, ein anderer nicht. Das ist eine Aussage, keine Enthaltung.
TRAGFAEHIGKEIT = ("breit_getragen", "schmal_getragen", "gemischt")

SYSTEM_PROMPT_ANALYST = """Du beurteilst die Lage eines Marktes - nicht ein \
einzelnes Wertpapier. Du bekommst Kennzahlen ueber die Gesamtheit der \
beobachteten Werte und das uebergeordnete Umfeld.

DEINE AUFGABE, in dieser Reihenfolge:

1. LAGE: Beschreibe in zwei bis drei Saetzen, was diesen Markt gerade \
kennzeichnet. Nenne die Zahlen, auf die du dich stuetzt, beim Namen.

2. TRAGFAEHIGKEIT: Wird die aktuelle Bewegung von vielen Werten getragen \
(breit_getragen), von wenigen (schmal_getragen), oder tragen einige Teile des \
Marktes waehrend andere zurueckbleiben (gemischt)?

3. HOECHSTBETRAG: Welcher Einzelbetrag ist in dieser Lage angemessen - 100, 300 \
oder 500 Euro? Das ist eine Obergrenze fuer eine einzelne Position, keine \
Empfehlung zu handeln. Ob ueberhaupt gehandelt wird, entscheidet ein anderer \
Schritt.

4. BELEGE: Zwei bis vier Beobachtungen aus den Daten, die deine Einschaetzung \
tragen. Jede mit dem Wert, auf den sie sich stuetzt. Erfinde nichts hinzu.

Antworte AUSSCHLIESSLICH mit JSON:
{"lage": "<zwei bis drei Saetze>",
 "traegt": "breit_getragen|schmal_getragen|gemischt",
 "max_tranche_eur": 100|300|500,
 "belege": ["<Beobachtung mit Wert>", ...]}"""


class AnalystAntwortUngueltig(ValueError):
    """Die Antwort erfuellt ihren Vertrag nicht."""


def validiere(antwort: dict) -> dict:
    if not isinstance(antwort, dict):
        raise AnalystAntwortUngueltig("Antwort ist kein Objekt")
    fehlend = [f for f in REQUIRED_FELDER if antwort.get(f) in (None, "", [])]
    if fehlend:
        raise AnalystAntwortUngueltig(f"Felder fehlen oder sind leer: {fehlend}")
    if antwort["traegt"] not in TRAGFAEHIGKEIT:
        raise AnalystAntwortUngueltig(
            f"traegt={antwort['traegt']!r}, erlaubt {TRAGFAEHIGKEIT}")
    try:
        betrag = int(float(antwort["max_tranche_eur"]))
    except (TypeError, ValueError):
        raise AnalystAntwortUngueltig(
            f"max_tranche_eur={antwort['max_tranche_eur']!r} ist keine Zahl")
    if betrag not in TRANCHEN_EUR:
        raise AnalystAntwortUngueltig(
            f"max_tranche_eur={betrag}, erlaubt {TRANCHEN_EUR} - das Modell "
            f"waehlt eine Tranche, es rechnet keine aus")
    belege = antwort["belege"]
    if not isinstance(belege, list) or not 2 <= len(belege) <= 4:
        raise AnalystAntwortUngueltig(
            f"belege: {len(belege) if isinstance(belege, list) else '?'} Stueck, "
            f"erwartet 2 bis 4")
    if any(not str(b).strip() for b in belege):
        raise AnalystAntwortUngueltig("leerer Beleg in der Liste")
    return antwort
