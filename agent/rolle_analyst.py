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
    """Prueft die Marktlage-Antwort. KORRIGIERT Formfehler, lehnt Sinnfehler ab.

    Der Unterschied (Nutzereinwand 10.08.: "damit wir nichts blocken"): wer
    "breit" statt "breit_getragen" sagt oder 250 statt 300, hat die Aufgabe
    verstanden und die Konvention verfehlt. Das wird zurechtgerueckt und
    protokolliert. Abgelehnt wird nur, was in sich unbrauchbar ist."""
    from agent.antwort_normalisierung import (Protokoll, naechste_tranche,
                                              naechstes_wort, kuerze_liste)

    if not isinstance(antwort, dict):
        raise AnalystAntwortUngueltig("Antwort ist kein Objekt")
    fehlend = [f for f in REQUIRED_FELDER if antwort.get(f) in (None, "", [])]
    if fehlend:
        raise AnalystAntwortUngueltig(f"Felder fehlen oder sind leer: {fehlend}")

    prot = Protokoll()

    wort, hinweis = naechstes_wort(antwort["traegt"], TRAGFAEHIGKEIT)
    if wort is None:
        # Keine Aehnlichkeit zu einer der drei Kategorien: das Modell hat eine
        # eigene erfunden. Das ist ein Sinnfehler, kein Tippfehler.
        raise AnalystAntwortUngueltig(
            f"traegt={antwort['traegt']!r} passt zu keiner Kategorie {TRAGFAEHIGKEIT}")
    antwort["traegt"] = wort
    prot.dazu(hinweis)

    betrag, hinweis = naechste_tranche(antwort["max_tranche_eur"], TRANCHEN_EUR)
    if betrag is None:
        raise AnalystAntwortUngueltig(hinweis or "max_tranche_eur unbrauchbar")
    antwort["max_tranche_eur"] = betrag
    prot.dazu(hinweis)

    belege = antwort["belege"]
    if not isinstance(belege, list):
        raise AnalystAntwortUngueltig("belege ist keine Liste")
    belege = [b for b in belege if str(b).strip()]
    if not belege:
        raise AnalystAntwortUngueltig("kein einziger brauchbarer Beleg")
    # Zu WENIGE Belege werden NICHT abgelehnt - eine duenne Begruendung kann
    # richtig sein, und der Nutzer sieht die Zahl ohnehin. Zu viele werden
    # gekuerzt, nicht verworfen.
    if len(belege) < 2:
        prot.dazu(f"nur {len(belege)} Beleg statt der erbetenen zwei")
    belege, hinweis = kuerze_liste(belege, 4, "Belege")
    prot.dazu(hinweis)
    antwort["belege"] = belege

    if prot:
        antwort["_korrekturen"] = str(prot)
    return antwort
