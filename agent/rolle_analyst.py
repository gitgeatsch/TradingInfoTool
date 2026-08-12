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

1. **KEINE "unklar"-Option.** Es gibt ueberhaupt keine Kategorie mehr, die
   das Modell waehlen muesste (Umbau 12.08., Begruendung unten bei
   REQUIRED_FELDER). Damit ist die Gefahr, die dieser Punkt abwehren sollte,
   an der Wurzel weg: eine Mehrdeutigkeitskategorie waere strukturell eine
   "Unknown"-Option gewesen, und die loest laut Literatur Abstention aus - im
   eigenen System von 93 % auf 3 % gemessen. Das Verbot gilt weiter fuer jede
   Kategorie, die hier je wieder eingefuehrt wird.

2. **KEINE KONFIDENZ.** Nirgends wird nach einer Sicherheit in Prozent gefragt.
   Verbalisierte Konfidenz ist extern belegt schlecht kalibriert, und im eigenen
   System vorhergesagt 77,5 % gegen tatsaechlich 33,3 %.

3. **KEINE VORSICHTSSPRACHE IM PROMPT.** Kein "sei zurueckhaltend", kein
   "beruecksichtige die Risiken". Negative Rahmung treibt Modelle belegt in
   uebermaessige Risikoaversion. Die Fakten tragen die Vorsicht, wo sie noetig
   ist; der Prompt tut es nicht.

WAS SIE STATTDESSEN LIEFERT: eine Beschreibung. Sie muss die Zukunft nicht
vorhersagen, um nuetzlich zu sein - dass Bitcoin 39 % unter seinem
Vorjahresstand liegt, WAEHREND der breite US-Aktienmarkt 20 % darueber steht,
ist ein Fakt, den der Trader gegen seine anderen Belege abwaegt. Genau das ist
die Sprachaufgabe: aus vier Kennzahlen je Leitmarkt drei Saetze machen, die den
Unterschied benennen.
"""
from __future__ import annotations

REQUIRED_FELDER = ("lage", "klassen", "belege")

# DAS URTEIL JE ASSETKLASSE (Paket 3, 12.08.2026).
#
# WARUM DAS KEIN RUECKFALL ZUR MARKTBREITE IST. Am selben Tag wurde `traegt`
# ENTFERNT - und jetzt kommt ein Kategoriefeld zurueck. Der Unterschied traegt:
#
#   `traegt` fragte nach MARKTBREITE, und in den Fakten stand keine. Das
#           Modell haette erfinden muessen.
#   `klassen` fragt nach genau den Fakten, die dastehen: Trend, Volatilitaet,
#           Liquiditaet und Stimmung je Leitmarkt.
#
# Ein Urteil ueber Vorhandenes ist erlaubt; ein Urteil ueber Fehlendes ist
# Erfindung.
#
# UND ES IST NICHT BERECHENBAR - das ist die zweite Bedingung (Betrags-Lehre
# R-A2: was wir selbst rechnen koennen, geben wir vor). Die RICHTUNG waere
# berechenbar, deshalb fragen wir nicht danach; `gleichlauf` liefert sie
# deterministisch. Gefragt ist die ABWAEGUNG mehrerer Kennzahlen gegeneinander -
# ein steigender Jahrestrend bei duenner Liquiditaet und aengstlicher Stimmung
# ist genau der Fall, den keine Formel entscheidet.
KLASSEN = ("krypto", "aktien", "rohstoffe")

# Beschreibend, drei Stufen, KEINE Enthaltung. "gemischt" heisst hier nicht
# "unklar", sondern benennt eine konkrete Konstellation: ein Teil der Kennzahlen
# spricht dafuer, ein anderer dagegen. Eine Mehrdeutigkeitskategorie waere
# strukturell eine "Unknown"-Option, und die loest laut Literatur Abstention aus
# - im eigenen System von 93 % auf 3 % gemessen.
EINSTUFUNGEN = ("guenstig", "gemischt", "unguenstig")

# DAS FELD `traegt` IST WEG (12.08.2026) - und das ist die Nachbesserung eines
# eigenen halben Schnitts, keine neue Idee.
#
# WAS PASSIERT WAR. L1 hat die Marktbreite aus der EINGABE gestrichen, weil ihr
# Korb zu 25 % aus Nicht-Coins bestand und ihre Bezugsgroesse wanderte
# (Arbeitsstand 7.31). Die FRAGE danach blieb aber im Prompt stehen:
#
#     "TRAGFAEHIGKEIT: Wird die aktuelle Bewegung von vielen Werten getragen
#      (breit_getragen), von wenigen (schmal_getragen) ...?"
#
# Damit stand im selben Prompt eine Pflichtfrage nach Marktbreite, ein
# Faktensatz ohne jede Breite - und drei Zeilen weiter der Satz "Erfinde nichts
# hinzu". Der Prompt widersprach sich selbst und zwang zur Erfindung. Genau die
# Naht, die ein glatter Schnitt nicht haben darf.
#
# WARUM KEIN ERSATZ-ETIKETT. Zwei Faelle, beide sprechen dagegen:
#
#   berechenbar      Ob die drei Benchmarks gleich- oder gegenlaeufig sind,
#                    steht in den Zahlen. Was wir selbst rechnen koennen, geben
#                    wir vor - das ist dieselbe Entscheidung wie beim Betrag
#                    (R-A2): ein Modell etwas waehlen zu lassen, das ohnehin
#                    feststeht, fuegt nur eine Fehlerquelle hinzu.
#   nicht berechenbar  Dann faende das Modell es auch nicht in den Fakten und
#                    muesste es erfinden.
#
# Es bleibt kein Fall uebrig, in dem ein kategorisches Modellurteil hier etwas
# beitraegt. Dazu kommt die Bilanz dieses Projekts mit Kategorien: `regime` war
# ueber 1.022 Faelle konstant "baer", die Marktbreite wirkte INVERS, und das
# Struktur-Etikett hat den Deadloop gebaut. Kein einziges kategorisches Feld hat
# sich bisher als nuetzlich messen lassen.
#
# MESSBAR BLEIBT ES TROTZDEM. `agent/marktlage.py::gleichlauf()` rechnet die
# Konstellation deterministisch aus denselben Fakten - zaehlbar wie ein
# Modellfeld, aber ohne Erfindungsrisiko. Wer spaeter ein Modellurteil hier
# will, muss vorher messen, dass es etwas hinzufuegt.

_KOPF = """Du beurteilst die Lage mehrerer Maerkte - nicht ein einzelnes \
Wertpapier. Du bekommst je Leitmarkt Kennzahlen zu Trend, Schwankungsbreite \
und Handelbarkeit, jeweils im Vergleich zu seiner eigenen Vergangenheit, und \
fuer Bitcoin zusaetzlich die Anlegerstimmung.

DEINE AUFGABE, in dieser Reihenfolge:"""

_SCHLUSS = """Antworte AUSSCHLIESSLICH mit JSON:
{"lage": "<zwei bis drei Saetze>",
 "klassen": [{"klasse": "krypto|aktien|rohstoffe",
              "einstufung": "guenstig|gemischt|unguenstig",
              "warum": "<ein Halbsatz mit der Zahl, die dich traegt>"}],
 "belege": ["<Beobachtung mit Wert>", ...]}"""

_LAGE = ("LAGE", "Beschreibe in zwei bis drei Saetzen, was diese Maerkte "
                 "gerade kennzeichnet - auch, wo sie sich voneinander "
                 "unterscheiden. Nenne die Zahlen, auf die du dich stuetzt, "
                 "beim Namen.")
_KLASSEN = ("JE MARKT", "Sage fuer JEDEN der genannten Leitmaerkte, ob das "
            "Umfeld fuer einen NEUEN Einstieg derzeit guenstig, gemischt oder "
            "unguenstig ist - krypto, aktien und rohstoffe. Dazu ein Halbsatz "
            "mit der Zahl, die dich traegt. Nenne keine Richtung und keine "
            "Prognose; es geht um das Umfeld, nicht um den Kursverlauf.")
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
    schritte = [_LAGE, _KLASSEN, _BELEGE]
    if mit_betragsfrage:
        # An den Platz VOR _BELEGE, wie in der Fassung vom 10.08. Stand hier
        # `insert(2)`, was richtig war, solange die Liste drei Schritte hatte.
        # Seit dem Wegfall von TRAGFAEHIGKEIT sind es zwei - `insert(2)` haette
        # den Block ans ENDE gehaengt und den Vergleichsarm still verschoben.
        schritte.insert(len(schritte) - 1, _BETRAGSFRAGE)
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
#   2026-08-12   Eingabe komplett getauscht (Marktbreite raus, marktlage.py
#                rein) UND die Marktbreite-Frage aus dem Prompt entfernt. Das
#                Feld `traegt` entfaellt. KEIN Befund von vorher ist auf diesen
#                Stand uebertragbar - weder Eingabe noch Frage sind dieselben.
#   2026-08-12b  Paket 3: Urteil je Assetklasse (`klassen`) als drittes
#                Pflichtfeld, und die Anlegerstimmung zu Bitcoin als Fakt im
#                Kryptoblock.
PROMPT_STAND = "2026-08-12b"


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

    `traegt` GIBT ES NICHT MEHR (12.08.). Hier stand eine Regel fuer seinen
    Rueckfall auf "gemischt"; das Feld ist mit dem Marktbreite-Schnitt entfallen
    (Begruendung im Kopf dieser Datei). Kommt es trotzdem in einer Antwort vor -
    etwa weil ein Modell einen alten Prompt gesehen hat - wird es entfernt und
    vermerkt, statt still mitgeschleppt zu werden."""
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
    # --- Urteil je Assetklasse: retten, nicht ablehnen ---------------------
    roh = antwort.get("klassen")
    sauber, gesehen = [], set()
    for eintrag in (roh if isinstance(roh, list) else []):
        if not isinstance(eintrag, dict):
            continue
        k, _ = naechstes_wort(eintrag.get("klasse"), KLASSEN)
        e, _ = naechstes_wort(eintrag.get("einstufung"), EINSTUFUNGEN)
        if k is None or e is None or k in gesehen:
            # Unzuordenbar oder doppelt: WEG, nicht geraten. Eine erfundene
            # Zuordnung waere schlimmer als eine fehlende - die naechste Rolle
            # bekaeme ein Urteil ueber einen Markt, den niemand beurteilt hat.
            prot.dazu(f"Klasseneintrag verworfen: {eintrag!r}")
            continue
        gesehen.add(k)
        sauber.append({"klasse": k, "einstufung": e,
                       "warum": str(eintrag.get("warum") or "").strip()})
    fehlend = [k for k in KLASSEN if k not in gesehen]
    if fehlend:
        prot.dazu(f"ohne Einstufung: {', '.join(fehlend)}")
    antwort["klassen"] = sauber

    if "traegt" in antwort:
        prot.dazu(f"unerwartetes Feld traegt={antwort.pop('traegt')!r} entfernt "
                  f"- die Rolle beurteilt seit 12.08. keine Marktbreite mehr")

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
