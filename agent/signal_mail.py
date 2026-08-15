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
    return f"{wert:,.{stellen}f}".translate(str.maketrans(",.", ".,"))


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


def _abschnitt(titel: str, zeilen: list[str]) -> list[str]:
    if not zeilen:
        return []
    return [f"--- {titel} ---", *zeilen, ""]


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
              gegenpruefung: list | None = None) -> tuple[str, str]:
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
               + (" (Hebel)" if instrument == "hebel" else ""))

    kopf = [titel,
            f"Kurs {preis(kurs_eur)} EUR"
            + (f" · {zeitpunkt}" if zeitpunkt else "")
            + (f" · Modell {modell}" if modell else ""),
            f"{instrument.capitalize()} / {strategie.capitalize()}",
            ""]

    # 1. DER COIN. Was der Wert gerade tut - ohne Empfehlung, ohne Wertung.
    #
    # REIHENFOLGE NACH NUTZERVORGABE (12.08.): *"Das fuer mich wichtige zuerst,
    # also Widerstand 62K Euro und danach die 3,9 Schwankung."* Erst der
    # Bestand (habe ich das ueberhaupt?), dann die Marken in Euro, dann der
    # gemessene Faktenblock, zuletzt das Umfeld. Absolute Zahlen vor
    # relativen - das ist die Regel der NUTZER-Schiene, nicht die des Modells.
    eins = []
    if bestand:
        eins.append(bestand)
    if marken:
        eins += marken
    if faktenblock:
        eins += ([""] if eins else []) + faktenblock
    eins += list(coin_fakten or [])
    if lage_fakten:
        eins += ["", "Umfeld:"] + [f"  {z}" for z in lage_fakten]

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
        zwei += ["Bestehende Position:"] + [f"  {z}" for z in AR.saetze(ausstieg)]
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
            f"  {z}" if ausstieg else z for z in ER.saetze(rechnung)]
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
        drei += ["", f"Widerlegt waere das durch: {urteil['umgeworfen_durch']}"]
    belege = urteil.get("belege") or []
    if belege:
        n = urteil.get("unabhaengige_faktoren")
        drei += ["", f"Belege ({len(belege)}, davon {n} unabhaengige Faktoren):"
                 if n else f"Belege ({len(belege)}):"]
        zeichen = {"dafuer": "+", "dagegen": "-", "neutral": "o"}
        for b in belege:
            drei.append(f"  {zeichen.get(b.get('richtung'), '?')} "
                        f"{b.get('fakt', '')} [{b.get('gewicht', '?')}]")

    text = "\n".join(
        kopf
        + _abschnitt("1. DER COIN", eins)
        + _abschnitt("2. DIE POSITION" if ausstieg else "2. DIE RECHNUNG", zwei)
        + _abschnitt("3. DAS URTEIL DES MODELLS", drei)
        + _abschnitt("4. EINORDNUNG", list(einordnung or []))
        # EIGENE UEBERSCHRIFT (Nutzervorgabe 16.08.2026). Die Zeilen der
        # zweiten Stufe standen bisher hinten in der EINORDNUNG - dort
        # sahen sie aus wie ein Nachsatz unserer eigenen Rechnung. Sie
        # sind aber die Aussage einer ANDEREN Quelle und gehoeren
        # entsprechend abgesetzt.
        + _abschnitt("5. GEGENPRUEFUNG (zweites Modell)",
                     list(gegenpruefung or []))
        + [TRENNER,
           "Ausfuehrung manuell ueber die Bitpanda-App. Details im Hebel-Tab."
           if instrument == "hebel" else
           "Ausfuehrung manuell ueber die Bitpanda-App."])
    return betreff, text
