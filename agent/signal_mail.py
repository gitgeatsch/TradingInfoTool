# -*- coding: utf-8 -*-
"""Die E-Mail an den Nutzer - vier Abschnitte, in der Reihenfolge des Lesens.

ANGELEHNT AN DIE BESTEHENDE HEBEL-MAIL (`scheduler/background.py`, Abschnitt
"1. MATHEMATISCH BERECHNET / 2. LLM-BEWERTUNG / 3. KONKLUSION"). Die
Dreiteilung hat sich bewaehrt und bleibt; sie trennt sauber, was gerechnet und
was beurteilt wurde. Nutzer am 12.08.: *"hier denke ich sollten wir uns zum
Teil an den bestehenden eMail anhalten - Info Teil zum Coin und dann die
wichtigen Abschnitte."*

WAS SICH GEGENUEBER DER ALTEN MAIL AENDERT, und warum:

  Konfidenz in Prozent      RAUS. Im eigenen System 77,5 % vorhergesagt gegen
                            33,3 % tatsaechlich. An ihre Stelle tritt die Zahl
                            der UNABHAENGIGEN Belege - was drei Belege wert
                            sind, die dreimal dasselbe sagen, ist eine
                            Sprachfrage und damit die Aufgabe des Modells.
  Risikofaktoren-Legende    RAUS aus der Mail. 36 von 202 Reglern waren beim
                            Audit am 04.08. wirkungslos; eine Legende fuer
                            Faktoren, die nichts bewirken, ist Fuellstoff.
  Info-Teil zum Coin        NEU nach vorn. Die alte Mail begann mit Zahlen und
                            erklaerte den Wert nirgends.
  Einordnung                NEU am Schluss. Was die Empfehlung wert ist, stand
                            bisher nirgends - und das ist die Frage, die der
                            Nutzer am Ende stellt.

DIE REIHENFOLGE IST EINE AUSSAGE. Erst der Wert (worum geht es), dann die
Rechnung (was waere zu tun), dann das Urteil (warum), dann die Einordnung (was
ist es wert). Wer nach zwei Abschnitten aufhoert zu lesen, hat das Wichtigste.

ABLAUFKETTE UND WARTEFREQUENZEN (Nutzerhinweis 13.08.2026).

DIESE DATEI BAUT NUR DEN TEXT. Wer sie verschickt, muss die Reihenfolge der
Aufrufe kennen - sonst geht die Mail raus, bevor die Ergebnisse da sind, die
sie zeigen soll. Genau das ist in der ALTEN Kette zweimal passiert: Screenshot-
Fund 26.07. bei Hebel, Nutzer-Fund 28.07. bei Krypto-Spot - dort gab es GAR
KEINEN Wartemechanismus.

Die Zahlen, an der Quelle abgelesen:

    Gemini            10 Aufrufe/Minute (api/gemini.RATE_LIMIT_PER_MINUTE)
    OpenRouter        Mindestabstand 3 s -> hoechstens 20/Minute
    Z.ai              120/Minute, aber 150 s Timeout JE CALL
    Z.ai je Signal    DREI sequenzielle Calls (1 Konsistenz + 2 positionsrobust)
    E-Mail wartet     240 s, Poll alle 3 s (_ZAI_EMAIL_WARTE_MAX_SEKUNDEN)

ZWEI FOLGERUNGEN, BEIDE UNBEQUEM:

1. DIE WARTEZEIT DECKT DEN SCHLIMMSTEN FALL NICHT. 3 x 150 s = 450 s gegen
   240 s. Das ist KEIN Defekt, sondern eine Entscheidung (P-8): bei einem
   Z.ai-Timeout geht die Mail OHNE die Gegenpruefungszeilen raus statt gar
   nicht. Typisch sind 12-25 s je Call, also 36-75 s - der Normalfall passt
   bequem. Wer die Timeouts aendert, muss diese Rechnung mitziehen.

2. DIE ROLLEN-KETTE IST DURCH GEMINI GETAKTET, nicht durch Z.ai. Rolle A
   laeuft EINMAL je Lauf, Rolle BC einmal je Asset - bei 40 Assets sind das
   41 Aufrufe und damit mindestens 4,1 Minuten, bevor das letzte Signal
   ueberhaupt existiert.

DIESE DATEI HAT KEINE EIGENE WARTEMECHANIK - und behaelt auch keine. Sie
formatiert, sie wartet nicht. Seit dem 13.08. steht die Wartestufe dort, wo die
Reihenfolge ohnehin liegt:

    agent/zweite_meinung.py   ruft Z.ai und deckelt die Wartezeit
    agent/rollen_lauf.py      schreiben -> Z.ai -> warten -> BAUEN -> senden

Der Bauplan wird deshalb erst aufgerufen, wenn die Zeilen der zweiten Meinung
vorliegen. Anders als in der alten Kette wird NICHT gepollt: dort startet der
Z.ai-Thread anderswo und der Versand hat keinen Griff darauf, hier gehoeren
beide Seiten demselben Aufrufer.

WER DIESE DATEI KUENFTIG WOANDERS EINHAENGT, muss dieselbe Reihenfolge nehmen -
sonst kehrt der Fund vom 28.07. zurueck: die Mail ging ohne die
Gegenpruefungszeilen raus, obwohl das Urteil zum Versandzeitpunkt vorlag.
"""
from __future__ import annotations

from agent import ausstiegsrechnung as AR
from agent import entscheidungsrechnung as ER

TRENNER = "-" * 68

# Nur bei diesen Aktionen wird ueberhaupt eine Position eroeffnet oder
# vergroessert - nur dort ergibt eine Einstiegsrechnung Sinn.
#
# ERÖFFNEN ERGAENZT (Gesamtpruefung 13.08.). Paket 13 hat dem Hebel sieben
# Aktionen gegeben, aber diese Liste kannte weiter nur die Spot-Woerter -
# ein Hebel-Einstieg haette in der Mail gestanden als "Kein Einstieg
# geplant", mit ausgerechneter Zone daneben im Nichts. Gefunden nicht beim
# Bauen von 13, sondern erst beim Abgleich ALLER Pakete gegeneinander.
AKTIONEN_MIT_EINSTIEG = ("KAUFEN", "NACHKAUFEN", "ERÖFFNEN")


def eur(wert: float, stellen: int = 0) -> str:
    """Deutsche Schreibweise: Punkt als Tausender, Komma als Dezimaltrenner.

    Python formatiert mit `,` als Tausendertrenner - in einer deutschen Mail
    liest sich "55,500.00 EUR" als fuenfundfuenfzigeinhalb. Die erste Fassung
    der Mail hatte genau das."""
    # AUS `agent/schreibweise.py` - die vierte Kopie dieser Zeile ist damit
    # weg. Die Vorgabe fuer die Stellenzahl bleibt hier, sie gehoert zum
    # Verwendungszweck.
    from agent.schreibweise import de as _s_de

    return _s_de(wert, stellen)


def preis(wert: float) -> str:
    """Ein KURS in deutscher Schreibweise - mit so vielen Stellen, wie er
    braucht.

    DER FUND, DER DIESE FUNKTION ERZWUNGEN HAT (14.08.2026, erste echte
    Produktionsmail, PLUME bei 0,0119 EUR):

        Einstiegszone   0 bis 0 EUR
        Stop            0 EUR  (5,5 % - ...)
        Take-Profit     0 bis 0 EUR

    Die Rechnung war richtig, die Darstellung hat sie vernichtet. `_eur()`
    hatte eine FESTE Stellenzahl - null fuer Kurse, zwei im Kopf der Mail. Bei
    einem Wert unter einem Cent bleibt davon nichts uebrig, und der Nutzer
    bekommt eine Kaufempfehlung ohne Einstieg, ohne Stop und ohne Ziel.

    DASS ES NIEMANDEM AUFFIEL, hat einen Grund: die Zahlen im Urteilstext
    stammen vom Modell und werden NICHT durch diesen Formatierer geschickt -
    dort stand korrekt "Widerstand bei 0.0119 EUR". In derselben Mail. Zwei
    Zahlenwege, einer davon kaputt.

    DIE REGEL: mindestens vier signifikante Stellen, hoechstens acht
    Nachkommastellen, und nie weniger als zwei. Ein Bitcoin-Kurs bleibt damit
    "61.234,50", ein Sub-Cent-Wert wird "0,011900" statt "0".

    NICHT NUR EIN KRYPTO-THEMA: dieselbe Falle trifft jeden Wert unter einem
    Euro, also auch Small Caps und jeden Cent-Wert im Aktienteil."""
    import math as _m

    w = abs(float(wert))
    if w >= 1.0 or w == 0:
        # Ab einem Euro sind zwei Stellen die gewohnte Schreibweise - mehr
        # waere Genauigkeit, die niemand braucht ("2,340 EUR" liest sich falsch).
        stellen = 2
    else:
        # Darunter zaehlen SIGNIFIKANTE Stellen, nicht Nachkommastellen: bei
        # 0,0119 sind vier davon fuenf Nachkommastellen, bei 0,000043 acht.
        stellen = min(8, 4 - 1 - int(_m.floor(_m.log10(w))))
    return f"{float(wert):,.{stellen}f}".translate(str.maketrans(",.", ".,"))


# --- WAS DER NUTZER LIEST, IST NICHT WAS DAS MODELL LIEST (17.08.2026) ---
#
# NUTZERFRAGE, die das ausgeloest hat: *"was soll mir die Einordnung -
# im gewohnten Bereich - sagen? Der Nutzen ist mir nicht klar."*
#
# Er hat recht, und zwar strukturell. `_einordnung()` kennt drei Woerter
# mit Schwellen bei 90 und 10 - **79 von 100 moeglichen Perzentilwerten**
# landen auf "im gewohnten Bereich". Der Satz ist per Konstruktion in vier
# von fuenf Faellen derselbe. In der gemeldeten SOL-Mail standen VIER
# Perzentilzeilen, alle vier "im gewohnten Bereich".
#
# Das ist ein konstantes Feld (R-T6) - genau das, was beim Regime
# entfernt wurde (2.549 von 2.549 identisch).
#
# ⚠️ DIE EINORDNUNG WAR NIE FUER DEN NUTZER GEBAUT. R-T11 ("kein
# Perzentil ohne Einordnung") entstand fuer das MODELL: ein Sprachmodell
# kann mit einer nackten Zahl nicht umgehen. Sie ist in die Mail
# durchgerutscht, weil Nutzertext und Modelltext aus denselben Saetzen
# gebaut werden.
#
# DAS MODELL BEHAELT ALLES. Diese Funktion wirkt NUR auf dem Weg zur
# Mail. Dem Modell die Einordnung wegzunehmen waere eine Aenderung
# seiner Grundlage, keine Darstellungsfrage.
GEWOHNT = "im gewohnten Bereich"


def auffaellige(zeilen) -> list:
    """Die Perzentilzeilen, die NICHT im gewohnten Bereich liegen.

    P1 aus Umbauplan Kapitel 91 (19.08.2026). Die Schwelle wird nicht
    erfunden: `marktlage._einordnung` teilt bereits in gewohnt und
    auffaellig, und gemessen sind 79 von 101 moeglichen Perzentilwerten
    "gewohnt" - also rund ein Fuenftel auffaellig. Genau die Groessenordnung,
    die die Literatur als "Extreme" meint.

    ⚠️ KENNZEICHNUNG, KEINE ENTSCHEIDUNG. Ein Signal mit auffaelligem
    Funding wird nicht eher versendet und keines ohne unterdrueckt. Erst
    dadurch wird ueberhaupt MESSBAR, ob die dokumentierte Vorhersagekraft
    der Extreme (Granger-Tests ueber 35,7 Mio. Minutenbeobachtungen) auch
    bei UNS gilt - und erst danach darf daraus eine Unterscheidung werden.
    Die Umkehrung dieser Reihenfolge hat den Deadloop erzeugt."""
    return [z for z in (zeilen or [])
            if "Perzentil" in z and GEWOHNT not in z]


def ohne_gewohntes(zeilen: list | None, was: str = "Angaben") -> list[str]:
    """Nur was auffaellt - plus EIN Satz fuer den Rest.

    "Nichts Auffaelliges" ist nicht wertlos: dass die Gegenpruefung nichts
    gefunden hat, ist eine Aussage. Aber dafuer reicht ein Satz fuer den
    ganzen Abschnitt, nicht vier gleichlautende Zeilen.

    Zeilen OHNE Perzentil bleiben unangetastet - sie tragen ihre eigene
    Aussage ("Am 16.08. flossen mehr Bitcoin von den Boersen herunter als
    auf sie") und haben mit dieser Frage nichts zu tun.

    ALLE oder NUR EINIGE - der Sammelsatz sagt es. Bleibt keine auffaellige
    Zeile uebrig, war wirklich nichts; bleibt eine, waeren "3 weitere" der
    richtige Ausdruck. Ein Satz, der beides gleich nennt, laesst den Leser
    im Unklaren, ob er etwas uebersehen hat."""
    zeilen = list(zeilen or [])
    behalten, gewohnt, auffaellig = [], 0, 0
    for z in zeilen:
        if "Perzentil" not in z:
            behalten.append(z)
        elif GEWOHNT in z:
            gewohnt += 1
        else:
            auffaellig += 1
            behalten.append(z)
    if gewohnt:
        # ⚠️ IM SINGULAR WIRD DAS HAUPTWORT GAR NICHT BENUTZT. `was` ist
        # ein Plural ("Angaben zur Positionierung"); "Die Angaben zum
        # Umfeld LIEGT" war die erste Fassung, und eine Mail, die so
        # schreibt, wirkt auf den Rest genauso sorgfaeltig.
        if gewohnt == 1:
            behalten.append("Eine weitere Angabe dazu liegt im gewohnten "
                            "Bereich." if auffaellig else
                            "Die einzige Angabe dazu liegt im gewohnten "
                            "Bereich.")
        elif auffaellig:
            behalten.append(f"{gewohnt} weitere {was} liegen im gewohnten "
                            f"Bereich.")
        else:
            behalten.append(f"Alle {gewohnt} {was} liegen im gewohnten "
                            f"Bereich.")
    return behalten


# WOHER DIE ANGABEN EINES ABSCHNITTS STAMMEN (17.08.2026).
#
# NUTZERVORSCHLAG: *"je eMail-Bereich die tatsaechliche Quelle angeben -
# eigene Berechnung deterministisch, oder nur Daten einer Datenquelle,
# LLM1 und LLM2."*
#
# UMGESETZT AUF DER ACHSE "WIE WISSEN WIR DAS", nicht "wer hat geredet".
# Der Modellname sagt nichts darueber, ob ein Satz nachpruefbar ist;
# "gemessen" oder "behauptet" sagt es. Und die beiden Modelle sind nicht
# dieselbe Art Aussage: Rolle BC faellt ein URTEIL, Rolle G erhebt einen
# EINWAND AUS EINER ANDEREN QUELLE - sie "LLM1/LLM2" zu nennen machte sie
# zu Geschwistern, die sie ausdruecklich nicht sein sollen.
#
# ⚠️ GEMISCHT IST DER EHRLICHE FALL. Der Stop ist arithmetisch exakt und
# ruht auf einem Prozentsatz, den eine Regel aus einer MODELLAUSSAGE
# abgeleitet hat. Ihn "eigene Berechnung" zu nennen waere falsche
# Sicherheit - genau das, was die Angabe verhindern soll.
HERKUNFT = {
    "wert": "GEMESSEN - Kurse und Fremdquellen",
    "position": "GERECHNET aus Ihren Zahlen, Zone und Stop teils aus einer "
                "Modellangabe",
    "rechnung": "GERECHNET aus Ihren Zahlen, Zone und Stop teils aus einer "
                "Modellangabe",
    "urteil": "BEHAUPTET - Rolle Haendler",
    "einordnung": "GERECHNET aus der gemessenen Erfahrungsrate",
    "gegenpruefung": "BEHAUPTET - andere Quelle: Terminmarkt und Kette",
}


def _abschnitt(titel: str, zeilen: list[str],
               herkunft: str | None = None) -> list[str]:
    if not zeilen:
        return []
    kopf = f"--- {titel} ---"
    return ([kopf] + ([f"    [{herkunft}]"] if herkunft else [])
            + list(zeilen) + [""])


# Wie der erste Abschnitt heisst. Frueher fest "DER COIN" - siehe die Notiz
# an der Verwendungsstelle. "DER WERT" traegt fuer alles, die Absicherung
# bekommt ihren eigenen Namen, weil sie ausdruecklich KEIN Trade ist
# (`rolle_trader._HANDELN["absicherung"]`: "Du entscheidest ueber eine
# ABSICHERUNG, nicht ueber einen Trade").
UEBERSCHRIFT_WERT = {
    "absicherung": "1. DIE ABSICHERUNG",
}


def _ueberschrift_wert(instrument: str | None) -> str:
    return UEBERSCHRIFT_WERT.get(str(instrument or ""), "1. DER WERT")


def baue_mail(*, symbol: str, name: str | None, kurs_eur: float,
              instrument: str, strategie: str,
              rechnung: dict, urteil: dict,
              ausstieg: dict | None = None,
              coin_fakten: list[str] | None = None,
              faktenblock: list[str] | None = None,
              marken: list[str] | None = None,
              lage_fakten: list[str] | None = None,
              bestand: str | None = None,
              einordnung: list[str] | None = None,
              modell: str | None = None,
              zeitpunkt: str | None = None,
              gegenpruefung: list | None = None,
              marken_werte: dict | None = None,
              umgeworfen_preis_eur: float | None = None,
              # 93 C: was an Nutzung und Entwicklung messbar ist - MIT
              # Warnhinweis, solange die eigene Reihe zu kurz ist. Kein
              # Urteil, kein Gate: diese Zeilen sperren nichts.
              lebendigkeit: list[str] | None = None,
              # V1 (22.08.2026): das Merkmal H als SCHATTEN. Es sperrt
              # nichts und aendert nichts - es steht in der Mail, damit der
              # Nutzer vier Wochen lang SIEHT, was ein spaeterer Filter
              # weggenommen haette, bevor er weggenommen wird.
              vorfilter: list[str] | None = None,
              # 22.08.2026: die ZUSAMMENFUEHRUNG. Sie gehoert VOR alles
              # andere - der Leser soll die Zahl sehen, bevor er die
              # Einzelteile liest, aus denen sie entsteht.
              wahrscheinlichkeit: list[str] | None = None,
              assetklasse: str | None = None) -> tuple[str, str]:
    """Betreff und Text. Reine Formatierung - hier wird nichts gerechnet.

    `rechnung` kommt aus `entscheidungsrechnung.rechne()`, `urteil` ist die
    gepruefte Antwort der Rolle BC. Beide werden NICHT nachbearbeitet: was der
    Rechnung widerspricht, gehoert in die Rechnung korrigiert, nicht in die
    Darstellung."""
    titel = f"{name or symbol} ({symbol})"
    aktion = urteil.get("aktion", "?")
    dringend = (ausstieg or {}).get("empfehlung", "")
    # DER BETREFF SAGT, WAS DIESE MAIL EMPFIEHLT (15.08.2026).
    #
    # Hier stand `dringend if dringend.startswith(SCHLIESSEN) else aktion` -
    # ohne Ruecksicht darauf, ob die Mail ueberhaupt von einem Ausstieg
    # handelt. Gemessen am Produktionslauf desselben Tages, zweimal:
    #
    #     Signalzeile: TURBO  EROEFFNEN  Hebel 3,8  500 EUR
    #     Betreff:     TradingInfoTool: TURBO - SCHLIESSEN (Hebel)
    #
    # Der Nutzer liest "schliessen" und findet im Text einen Plan, 500 EUR
    # gehebelt zu eroeffnen. Der Betreff ist das, wonach gehandelt wird - er
    # darf nicht die Empfehlung einer ANDEREN Rechnung tragen.
    #
    # DIE DRINGLICHKEIT BLEIBT ERHALTEN, aber nur dort, wo sie die Aussage
    # dieser Mail IST: bei HALTEN und NICHTS_TUN beschreibt die
    # Ausstiegsempfehlung tatsaechlich, was zu tun ist. Bei einem Einstieg
    # beschreibt sie das Gegenteil. Sie steht dann weiterhin im Text, unter
    # "Bestehende Position" - sichtbar, nur nicht als Ueberschrift.
    #
    # SEIT O-37 KOMMT DIESER FALL OHNEHIN KAUM NOCH VOR: die Kette erzeugt
    # keine Einstiegsmail mehr, wenn der Ausstieg auf SCHLIESSEN steht. Die
    # Bedingung bleibt trotzdem hier - eine Darstellung, die sich auf eine
    # Vorbedingung an anderer Stelle verlaesst, bricht beim naechsten Umbau.
    _dringend_im_betreff = (dringend.startswith(AR.SCHLIESSEN)
                            and aktion not in AKTIONEN_MIT_EINSTIEG)
    betreff = (f"TradingInfoTool: {symbol} - "
               + (dringend if _dringend_im_betreff else aktion)
               # ⚠️ DER BETREFF FOLGT DER ZAHL, NICHT DEM LAUF (19.08.2026).
               #
               # Vorher stand hier `instrument == "hebel"` - also das
               # Etikett des LAUFS. Seit S5 faellt in vier von fuenf Faellen
               # Hebel 1,0 an, und der Betreff behauptete trotzdem ein
               # Hebelgeschaeft. Drei Stellen sagten "Hebel", die Rechnung
               # sagte nein.
               #
               # VORGEZOGEN AUS S6. Dort folgt das ganze Etikett der Zahl -
               # Toepfe, Cooldowns, Datenbankwerte. Hier nur der Betreff,
               # weil der Widerspruch sonst in jeder Mail steht.
               + (" (Hebel)"
                  if float((rechnung or {}).get("hebel") or 1.0) > 1.0
                  else ""))

    kopf = [titel,
            f"Kurs {preis(kurs_eur)} EUR"
            + (f" · {zeitpunkt}" if zeitpunkt else "")
            + (f" · Modell {modell}" if modell else ""),
            # ⚠️ A6, TEIL 1 (23.08.2026): DAS ERGEBNIS-ETIKETT, NICHT DAS
            # DES LAUFS. Im Simulationslauf stand im Betreff "(Hebel)"
            # und zwei Zeilen darunter "Spot / Einstieg" - fuer dasselbe
            # Signal. Der Betreff hatte recht: seit A1/A2 faellt der
            # Hebel aus der RECHNUNG an (verlustanteil / stop_rel), und
            # diese Zeile druckte weiter das Etikett des LAUFS.
            #
            # DIESELBE QUELLE WIE DER BETREFF, damit beide nicht wieder
            # auseinanderlaufen koennen.
            f"{('Hebel' if float((rechnung or {}).get('hebel') or 1.0)
                > 1.0 else instrument.capitalize())}"
            f" / {strategie.capitalize()}",
            ""]

    # 1. DER WERT. Was er gerade tut - ohne Empfehlung, ohne Wertung.
    #
    # REIHENFOLGE NACH NUTZERVORGABE (12.08.): *"Das fuer mich wichtige zuerst,
    # also Widerstand 62K Euro und danach die 3,9 Schwankung."* Erst der
    # Bestand (habe ich das ueberhaupt?), dann die Marken in Euro, dann der
    # gemessene Faktenblock, zuletzt das Umfeld. Absolute Zahlen vor
    # relativen - das ist die Regel der NUTZER-Schiene, nicht die des Modells.
    eins = []
    # ⚠️ GANZ NACH OBEN, NOCH VOR DEN BESTAND. Bis heute stand hier eine
    # Strichliste ("1 dafuer, 1 dagegen, 2 nicht bewertbar") - sie liess die
    # Zusammenfuehrung beim Leser. Die gerechnete Zahl ersetzt sie nicht,
    # sie steht davor: erst das Ergebnis, dann die Bestandteile.
    if wahrscheinlichkeit:
        eins += list(wahrscheinlichkeit)
    if bestand:
        eins += ([""] if eins else []) + [bestand]
    if marken:
        eins += marken
    if faktenblock:
        eins += ([""] if eins else []) + faktenblock
    eins += list(coin_fakten or [])
    if lebendigkeit:
        eins += ([""] if eins else []) + list(lebendigkeit)
    # ⚠️ EIGENER ABSATZ, NICHT ANS LAGEBILD ANGEHAENGT. Der Schatten sagt
    # etwas ueber UNSERE Auswahl, nicht ueber den Wert - wer ihn zwischen
    # die Marktmerkmale mischt, liest ihn als weiteren Marktfakt.
    if vorfilter:
        eins += ([""] if eins else []) + list(vorfilter)
    if lage_fakten:
        eins += ["", "Umfeld:"] + [
            f"  {z}" for z in ohne_gewohntes(lage_fakten,
                                             "Angaben zum Umfeld")]

    # 2. DIE RECHNUNG. Alle Zahlen, jede mit ihrer Regel dahinter.
    #
    # ABER NUR, WENN GEHANDELT WIRD. Die erste Fassung zeigte bei NICHTS_TUN
    # eine vollstaendige Einstiegsplanung - Zone, Stop, Ziel, Betrag, Hebel -
    # unter einer Ueberschrift, die "tu nichts" sagt. Das ist derselbe
    # Widerspruch zwischen zwei Bloecken, den R-T8 fuer die Fakten verbietet,
    # und er wiegt hier schwerer: eine ausgerechnete Zone liest sich wie eine
    # Empfehlung, egal was darueber steht.
    # BEI EINER GEHALTENEN POSITION STEHT DER AUSSTIEG ZUERST. Das ist keine
    # Formfrage: 50 % der Signale standen einmal bei +1 R, 17,6 % kamen an -
    # bei einem Bestand ist die dringendere Frage, was mit ihm geschieht, und
    # nicht, ob man noch mehr davon kauft.
    zwei = []
    if ausstieg:
        # GEHALTEN ODER NUR VERFOLGT - die Ueberschrift sagt es jetzt
        # (17.08.2026, Nutzervorgabe: *"es sollte unterscheidbar sein, was
        # tatsaechlich gehalten wird und was nur als Signal getrackt wird -
        # das brauchen wir beim Kauf, Halten und Verkauf, sonst verwirrt der
        # Inhalt."*).
        #
        # DER FALL, DER ES AUSGELOEST HAT. Eine SOL-Mail sagte oben "SOL ist
        # nicht im Bestand" und zwanzig Zeilen tiefer "Bestehende Position:
        # HALTEN, +0.43 R". Beide Saetze stimmten fuer sich - der erste kam
        # aus `holdings`, der zweite aus einer Zeile je SIGNAL. Wer das liest,
        # muss glauben, er halte etwas.
        #
        # DIE UNTERSCHEIDUNG GAB ES LAENGST: `ist_bestand` trennt seit dem
        # 13.08. die offene Position von der alten Signalzeile ("von 45
        # Signal-Symbolen lagen 28 gar nicht im Bestand"). Sie stand nur
        # nirgends in der Mail.
        # DREI ZUSTAENDE, NICHT ZWEI (17.08.2026, Nutzerfund an einer
        # BTC-Hebelmail). Die Mail sagte oben "In BTC besteht keine offene
        # Hebelposition" und zwanzig Zeilen tiefer "Bestehende Position" -
        # weil BTC im SPOT liegt und `ist_bestand` beide Toepfe
        # verschmolz. Jetzt sagt die Ueberschrift, WORAUF sich die
        # Empfehlung bezieht:
        #
        #   dieses Instrument   "Bestehende Position"
        #   die andere Seite    "Ihr Bestand auf der anderen Seite"
        #   nur verfolgt        "Verfolgter Einstiegsvorschlag"
        #
        # Die andere Seite wird BENANNT statt verschwiegen - sie gehoert
        # dem Leser, nur eben nicht unter der ersten Ueberschrift.
        # Dieselbe Entscheidung wie bei `rollen_eingabe.gegenbestand_satz`.
        # ⚠️ ZWEI FESTE SAETZE STATT EINES BAUSTEINS. Mein erster Entwurf
        # setzte "eine {_andere}" zusammen und schrieb "eine
        # Spot-Bestand" - eine Mail, die so schreibt, wirkt auf den Rest
        # genauso sorgfaeltig. Deutsche Artikel lassen sich nicht
        # zusammenstecken.
        _gegen = ("Sie halten diesen Wert im Spot, aber keine "
                  "Hebelposition darauf" if instrument == "hebel" else
                  "Sie halten eine Hebelposition auf diesen Wert, aber "
                  "keinen Bestand im Spot")
        if ausstieg.get("ist_bestand"):
            _kopf = "Bestehende Position:"
        elif ausstieg.get("ist_bestand_gegenseite"):
            _kopf = f"Verfolgter Einstiegsvorschlag - {_gegen}:"
        else:
            _kopf = "Verfolgter Einstiegsvorschlag (NICHT im Bestand):"
        zwei += [_kopf] + [f"  {z}" for z in AR.saetze(ausstieg)]
        # ZWEI ZAHLEN UNTER EINEM WORT (17.08.2026, Nutzerpruefung).
        #
        # Die SOL-Mail nannte "die Unterstuetzung" dreimal - zweimal bei
        # 63,44 EUR (unsere Markenrechnung) und einmal bei 63,64 EUR (der
        # Widerlegungspreis, den das Modell genannt hat). Wer das liest,
        # kann nicht wissen, welche gilt.
        #
        # BEIDE BLEIBEN STEHEN. Die Zahl des Modells ist seine Bedingung -
        # sie zu ueberschreiben hiesse, sein Urteil zu veraendern (R-5.x:
        # kein deterministischer Eingriff in das Werturteil). Was fehlte,
        # war die Einordnung: WESSEN Zahl ist das, und wie steht sie zu
        # unserer.
        _u = (marken_werte or {}).get("unterstuetzung") or {}
        _up = _u.get("preis_eur")
        # EIN PROMILLE, NICHT EIN HALBES PROZENT. Mein erster Entwurf nahm
        # 0,5 % - und schwieg damit ausgerechnet im gemeldeten Fall: 63,44
        # gegen 63,64 sind 0,32 %. Auf einen Stop, der 2,5 % entfernt liegt,
        # ist das ein Achtel des Risikos, also keine Rundung.
        if (ausstieg.get("umgeworfen_durch") and umgeworfen_preis_eur
                and _up and abs(float(umgeworfen_preis_eur) - float(_up))
                > 0.001 * float(_up)):
            zwei.append(f"    Unsere Markenrechnung sieht die Unterstuetzung "
                        f"bei {preis(_up)} EUR "
                        f"({_u.get('beruehrungen', 0)}-mal beruehrt) - das "
                        f"Modell nennt {preis(float(umgeworfen_preis_eur))} "
                        f"EUR. Zwei Zahlen, zwei Quellen.")
    # KEIN NACHKAUF AUF EINE POSITION, DIE GESCHLOSSEN GEHOERT. In der ersten
    # Fassung standen beide untereinander: "Stop auf 59.100 nachziehen" und
    # daneben "Einstiegszone 57.581 bis 58.419" - zwei Anweisungen fuer
    # dasselbe Asset, die einander ausschliessen.
    ausstieg_dringend = (ausstieg or {}).get("empfehlung", "").startswith(AR.SCHLIESSEN)
    if ausstieg_dringend and aktion in AKTIONEN_MIT_EINSTIEG:
        zwei += ["", f"Kein zusaetzlicher Einstieg: der Ausstieg steht auf "
                     f"{AR.SCHLIESSEN}, das Modell sagt {aktion}. Solange die "
                     f"bestehende Position faellig ist, wird nicht nachgelegt."]
    elif aktion in AKTIONEN_MIT_EINSTIEG:
        zwei += ([""] if zwei else []) + (
            ["Zusaetzlicher Einstieg:"] if ausstieg else []) + [
            f"  {z}" if ausstieg else z
            # ⚠️ DER NAME NUR FUER KRYPTO SPOT UND HEBEL (17.08.2026,
            # Nutzerentscheidung). "Liquiditaetszone" traegt eine Deutung
            # - Stop-Hunt, Marketmaker -, die am 23.07. ausdruecklich auf
            # den 24/7-Markt mit hohem Retail- und Hebelanteil begrenzt
            # wurde. Die Marken selbst gibt es ueberall; sie bei einem
            # WisdomTree-Zertifikat so zu nennen hiesse, eine Annahme
            # mitzuimportieren, die dort nie geprueft wurde.
            #
            # OBEN ODER UNTEN: bei SHORT liegt das Ziel unter dem Kurs,
            # im Weg stehen dann die Unterstuetzungen.
            for z in ER.saetze(
                rechnung,
                (marken_werte or {}).get(
                    "unten" if str(urteil.get("richtung")) == "SHORT"
                    else "oben"),
                liquiditaetszonen=(str(assetklasse or "").lower()
                                   == "krypto"))]
    elif not ausstieg:
        zwei = [f"Kein Einstieg geplant - die Empfehlung lautet {aktion}.",
                "Zone, Stop und Ziel werden erst gerechnet, wenn gehandelt wird."]

    # 3. DAS URTEIL. Der Text des Modells, unveraendert. Die Belege zuletzt -
    # sie sind Beleg, nicht Aussage.
    drei = [f"Aktion: {aktion}", ""]
    if urteil.get("begruendung"):
        drei.append(urteil["begruendung"])
    if urteil.get("was_dagegen"):
        drei += ["", f"Was dagegen spricht: {urteil['was_dagegen']}"]
    if urteil.get("umgeworfen_durch"):
        # ⚠️ WAS IST "DAS"? (17.08.2026, Nutzerpruefung einer BTC-Mail).
        # Die beiden Saetze standen direkt untereinander:
        #
        #     Was dagegen spricht: Die negative Kursentwicklung ...
        #     Widerlegt waere DAS durch: Schlusskurs unter 53.274 EUR
        #
        # Gemeint ist die ENTSCHEIDUNG des Modells - der Leser muss aber
        # raten, ob die Schwaeche widerlegt wird, die eine Zeile hoeher
        # steht. Ein Fuerwort, dessen Bezug man erraten muss, ist in einer
        # Handelsempfehlung eines zu viel.
        drei += ["", f"Die Entscheidung {aktion} waere widerlegt durch: "
                     f"{urteil['umgeworfen_durch']}"]
    belege = urteil.get("belege") or []
    if belege:
        n = urteil.get("unabhaengige_faktoren")
        drei += ["", f"Belege ({len(belege)}, davon {n} unabhaengige Faktoren):"
                 if n else f"Belege ({len(belege)}):",
                 # Dieselbe Legende wie in der alten Mail - der Renderer
                 # erkennt sie an "Warnsignal" und setzt sie kursiv grau.
                 "(▲ spricht dafuer · ● neutral · ▼ Warnsignal/spricht dagegen)"]
        # ⚠️ DIE MARKER DES RENDERERS, NICHT EIGENE (17.08.2026,
        # Nutzerhinweis mit einem Beispiel aus der ALTEN Mail).
        #
        # Die Mail geht laengst als HTML raus - `api/email_notify` haengt
        # `ui.formatting.render_detail_html` davor, und der faerbt ▲ gruen,
        # ▼ rot, ● grau und macht Abschnittskoepfe blau und fett. Die neue
        # Kette schrieb aber "+/-/o" - Zeichen, die der Renderer nicht
        # kennt. Die Farbe war nie weg; der Text hat nur aufgehoert, sie
        # anzufordern.
        zeichen = {"dafuer": "▲", "dagegen": "▼", "neutral": "●"}
        for b in belege:
            drei.append(f"  {zeichen.get(b.get('richtung'), '?')} "
                        f"{b.get('fakt', '')} [{b.get('gewicht', '?')}]")

    text = "\n".join(
        kopf
        # ⚠️ NICHT MEHR FEST "DER COIN" (16.08.2026). Die Ueberschrift stand
        # aus der Zeit, als die Kette nur Krypto bediente - seit dem
        # Vollumstieg stand sie ueber einem WisdomTree-Zertifikat (OD7H) und
        # ueber einem inversen S&P-ETF (DBPK). Gefunden, als die Simulation
        # zum ersten Mal Rohstoffe und Absicherung durchlaufen liess.
        #
        # Kein Defekt der Kette - aber ein Etikett, das dem Leser etwas
        # anderes sagt, als vor ihm liegt. Dieselbe Regel wie bei den
        # Faktensaetzen: was dasteht, muss stimmen.
        + _abschnitt(_ueberschrift_wert(instrument), eins,
                     HERKUNFT["wert"])
        + _abschnitt("2. DIE POSITION" if ausstieg else "2. DIE RECHNUNG",
                     zwei,
                     HERKUNFT["position" if ausstieg else "rechnung"])
        + _abschnitt("3. DAS URTEIL DES MODELLS", drei,
                     HERKUNFT["urteil"])
        + _abschnitt("4. EINORDNUNG", list(einordnung or []),
                     HERKUNFT["einordnung"])
        # EIGENE UEBERSCHRIFT (Nutzervorgabe 16.08.2026). Die Zeilen der
        # zweiten Stufe standen bisher hinten in der EINORDNUNG - dort
        # sahen sie aus wie ein Nachsatz unserer eigenen Rechnung. Sie
        # sind aber die Aussage einer ANDEREN Quelle und gehoeren
        # entsprechend abgesetzt.
        # DIE PERZENTILE, DIE NICHTS UNTERSCHEIDEN, FALLEN HIER WEG
        # (17.08.2026). Vier gleichlautende Zeilen "im gewohnten Bereich"
        # werden zu einer. Das MODELL hat sie alle bekommen - hier steht
        # nur, was der Nutzer liest.
        + _abschnitt("5. GEGENPRUEFUNG (zweites Modell)",
                     ohne_gewohntes(gegenpruefung,
                                    "Angaben zur Positionierung"),
                     HERKUNFT["gegenpruefung"])
        + [TRENNER,
           "Ausfuehrung manuell ueber die Bitpanda-App. Details im Hebel-Tab."
           if instrument == "hebel" else
           "Ausfuehrung manuell ueber die Bitpanda-App."])

    # ⚠️ "PERZENTIL" EINMAL ERKLAEREN - AN DER ERSTEN STELLE (20.08.2026).
    #
    # Nutzerrueckmeldung: die Perzentile seien "zum Teil nicht oder schwierig
    # einzuordnen". Zu Recht - das Wort steht an 141 Stellen im System und
    # wird an keiner erklaert. Und es ist mehrdeutig, wenn man die Konvention
    # nicht kennt: heisst "7. Perzentil" sieben Prozent daruber oder darunter?
    #
    # DIE ANTWORT STEHT IM CODE, nicht in der Vermutung: `marktlage._perzentil`
    # rechnet `Anteil der Vergleichswerte, die UNTER dem aktuellen liegen`.
    # Sieben heisst also: nur sieben von hundert lagen tiefer.
    #
    # Eine Zeile je Mail, an der ERSTEN Fundstelle - nicht 141 Umschreibungen
    # und keine Legende am Ende, die niemand liest. Dieselbe Bauform wie beim
    # Gesamtbild: der fertige Text wird gelesen, nichts neu gerechnet.
    try:
        _z = text.split("\n")
        _i = next((k for k, z in enumerate(_z) if "Perzentil" in z), None)
        if _i is not None:
            _z.insert(_i + 1,
                      "   (Perzentil = Rangplatz in der eigenen Geschichte "
                      "dieses Werts. \"7. Perzentil\" heisst: nur 7 von 100 "
                      "Vergleichswerten lagen tiefer, 93 lagen hoeher.)")
            text = "\n".join(_z)
    except Exception:                                        # noqa: BLE001
        pass

    # 93 E: DAS GESAMTBILD GANZ NACH OBEN (20.08.2026).
    #
    # Es liest die FERTIGE Mail und zaehlt die Etiketten, die weiter unten
    # ohnehin stehen. Damit gibt es KEINE zweite Rechnung, die von der
    # ersten abweichen koennte - genau der Fehler, der am 18.08. vier
    # Kopien derselben Stopzeile hinterlassen hat.
    #
    # ⚠️ ES SPERRT NICHTS (Fallstrick E1). Auch "3 dagegen" ist eine
    # Zusammenfassung, kein Veto.
    try:
        from agent import gesamtbild as _GB
        zeilen = text.split("\n")
        kopf = _GB.saetze(zeilen)
        if kopf:
            # Unter die drei Kopfzeilen (Titel, Kurs, Instrument), vor den
            # ersten Abschnitt - "das fuer mich Wichtige zuerst".
            text = "\n".join(zeilen[:3] + [""] + kopf + zeilen[3:])
    except Exception:                                        # noqa: BLE001
        pass
    return betreff, text
