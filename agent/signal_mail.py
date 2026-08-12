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
"""
from __future__ import annotations

from agent import entscheidungsrechnung as ER

TRENNER = "-" * 68

# Nur bei diesen Aktionen wird ueberhaupt eine Position eroeffnet oder
# vergroessert - nur dort ergibt eine Einstiegsrechnung Sinn.
AKTIONEN_MIT_EINSTIEG = ("KAUFEN", "NACHKAUFEN")


def eur(wert: float, stellen: int = 0) -> str:
    """Deutsche Schreibweise: Punkt als Tausender, Komma als Dezimaltrenner.

    Python formatiert mit `,` als Tausendertrenner - in einer deutschen Mail
    liest sich "55,500.00 EUR" als fuenfundfuenfzigeinhalb. Die erste Fassung
    der Mail hatte genau das."""
    return f"{wert:,.{stellen}f}".translate(str.maketrans(",.", ".,"))


def _abschnitt(titel: str, zeilen: list[str]) -> list[str]:
    if not zeilen:
        return []
    return [f"--- {titel} ---", *zeilen, ""]


def baue_mail(*, symbol: str, name: str | None, kurs_eur: float,
              instrument: str, strategie: str,
              rechnung: dict, urteil: dict,
              coin_fakten: list[str] | None = None,
              faktenblock: list[str] | None = None,
              marken: list[str] | None = None,
              lage_fakten: list[str] | None = None,
              bestand: str | None = None,
              einordnung: list[str] | None = None,
              modell: str | None = None,
              zeitpunkt: str | None = None) -> tuple[str, str]:
    """Betreff und Text. Reine Formatierung - hier wird nichts gerechnet.

    `rechnung` kommt aus `entscheidungsrechnung.rechne()`, `urteil` ist die
    gepruefte Antwort der Rolle BC. Beide werden NICHT nachbearbeitet: was der
    Rechnung widerspricht, gehoert in die Rechnung korrigiert, nicht in die
    Darstellung."""
    titel = f"{name or symbol} ({symbol})"
    aktion = urteil.get("aktion", "?")
    betreff = (f"TradingInfoTool: {symbol} - {aktion}"
               f"{' (Hebel)' if instrument == 'hebel' else ''}")

    kopf = [titel,
            f"Kurs {eur(kurs_eur, 2)} EUR"
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
    zwei = ER.saetze(rechnung) if aktion in AKTIONEN_MIT_EINSTIEG else [
        f"Kein Einstieg geplant - die Empfehlung lautet {aktion}.",
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
        + _abschnitt("2. DIE RECHNUNG", zwei)
        + _abschnitt("3. DAS URTEIL DES MODELLS", drei)
        + _abschnitt("4. EINORDNUNG", list(einordnung or []))
        + [TRENNER,
           "Ausfuehrung manuell ueber die Bitpanda-App. Details im Hebel-Tab."
           if instrument == "hebel" else
           "Ausfuehrung manuell ueber die Bitpanda-App."])
    return betreff, text
