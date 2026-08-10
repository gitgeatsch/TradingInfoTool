# -*- coding: utf-8 -*-
"""LLM2 als Anwalt des Gegenteils - Stufe 2 (10.08.2026).

WARUM DIE ALTE ROLLE NICHT TAUGTE. Bis heute leitete LLM2 eine EIGENE RICHTUNG
ab. Gemessen an 1.022 Faellen: es kam genau EINMAL auf LONG (Juli 1 von 463,
August 0 von 559), waehrend das Primaermodell auf denselben Fakten zu 34,9 %
LONG waehlte. Die Ursache lag nicht im Modell, sondern im Faktensatz - `regime`
war auf ALLEN 1.022 Faellen "baer", eine Konstante mit Richtungsaussage in
einem Satz von sechs Feldern. Ein zweiter Blick, der eine Konstante abliest,
ist kein zweiter Blick.

WAS ES STATTDESSEN TUT. Es greift die staerkste Annahme der Schaetzung an.
Diese Aufgabe stammt aus der Praxisarchitektur - dort debattieren Bull- und
Bear-Researcher, und der Trader synthetisiert aus der Debatte. Hier in der
billigsten tragfaehigen Form: EIN Angreifer, EIN Aufruf.

Und sie ist die Aufgabe, in der Sprachmodelle nachweislich stark sind -
Widersprueche zwischen Text und Zahlen finden. Das steht so schon im
Modul-Docstring der alten Gegenpruefung: *"das ist die tatsaechliche,
einzigartige LLM-Faehigkeit, die hier genutzt wird"*. Wir haben sie nur an der
falschen Frage eingesetzt.

WAS ES AUSDRUECKLICH NICHT TUT:

  * KEINE eigene Richtung ableiten - das war der Fehler.
  * KEINE Zahl korrigieren. Es sagt, in WELCHE Richtung die Schaetzung
    danebenliegen koennte, nicht um wie viel. Eine zweite Zahl waere ein
    zweiter Schaetzer, und den wuerden wir mitteln muessen statt ihn zu
    hoeren.
  * KEIN Veto. Sein Urteil geht in die Anzeige und in die Begruendung, nicht
    in die Entscheidungsrechnung. Ein deterministischer Override des
    LLM-Werturteils ist ausdruecklich ausgeschlossen (stehende Vorgabe).
"""
from __future__ import annotations

KORREKTUR_RICHTUNGEN = ("ziel_wahrscheinlicher", "stop_wahrscheinlicher",
                        "keine_korrektur")
STAERKEN = ("stark", "mittel", "schwach")

REQUIRED_GEGENPRUEFUNG_FELDER = (
    "angriff",
    "uebersehener_fakt",
    "korrektur_richtung",
    "staerke",
)

SYSTEM_PROMPT_GEGENPRUEFUNG = """Du bist der Anwalt des Gegenteils. Ein anderes \
Modell hat fuer einen vorgegebenen Handelsaufbau geschaetzt, wie \
wahrscheinlich Ziel, Stop oder keines von beidem zuerst erreicht wird. Du \
bekommst dieselben Fakten und seine Schaetzung.

DEINE AUFGABE ist NICHT, eine eigene Richtung oder eigene Zahlen zu nennen. \
Sie lautet: finde die SCHWAECHSTE STELLE dieser Schaetzung.

1. ANGRIFF: Welche Annahme traegt die Schaetzung, und warum koennte sie falsch \
sein? Beziehe dich auf konkrete Werte aus den Fakten, nicht auf Allgemeines.

2. UEBERSEHENER FAKT: Welcher der gegebenen Fakten spricht gegen die \
Schaetzung und kommt in ihrer Begruendung nicht vor? Steht kein solcher Fakt \
in den Daten, schreibe "keiner" - erfinde nichts.

3. KORREKTUR-RICHTUNG: Wuerde deine Kritik, wenn sie zutrifft, das ZIEL \
wahrscheinlicher machen (ziel_wahrscheinlicher), den STOP wahrscheinlicher \
(stop_wahrscheinlicher), oder aendert sie nichts (keine_korrektur)? Nur die \
Richtung, keine Zahl.

4. STAERKE deines Einwands: stark, mittel oder schwach. Sei ehrlich - ein \
schwacher Einwand als stark ausgegeben macht die Gegenpruefung wertlos.

Antworte AUSSCHLIESSLICH mit JSON:
{"angriff": "<kurz>", "uebersehener_fakt": "<kurz oder 'keiner'>", \
"korrektur_richtung": "ziel_wahrscheinlicher|stop_wahrscheinlicher|keine_korrektur", \
"staerke": "stark|mittel|schwach"}"""


class GegenpruefungUngueltig(ValueError):
    """Die Gegenpruefung erfuellt ihren Vertrag nicht."""


def _validate_gegenpruefung(antwort: dict, symbol: str = "?") -> dict:
    if not isinstance(antwort, dict):
        raise GegenpruefungUngueltig(f"{symbol}: Antwort ist kein Objekt")
    fehlend = [f for f in REQUIRED_GEGENPRUEFUNG_FELDER if f not in antwort]
    if fehlend:
        raise GegenpruefungUngueltig(f"{symbol}: Felder fehlen: {fehlend}")
    if antwort["korrektur_richtung"] not in KORREKTUR_RICHTUNGEN:
        raise GegenpruefungUngueltig(
            f"{symbol}: korrektur_richtung={antwort['korrektur_richtung']!r}, "
            f"erlaubt {KORREKTUR_RICHTUNGEN}")
    if antwort["staerke"] not in STAERKEN:
        raise GegenpruefungUngueltig(
            f"{symbol}: staerke={antwort['staerke']!r}, erlaubt {STAERKEN}")
    for feld in ("angriff", "uebersehener_fakt"):
        if not isinstance(antwort.get(feld), str) or not antwort[feld].strip():
            raise GegenpruefungUngueltig(f"{symbol}: '{feld}' fehlt oder ist leer")
    return antwort


def baue_gegenpruefungs_eingabe(fakten: dict, schaetzung: dict) -> dict:
    """Was der Gegenpruefer sieht: dieselben Fakten UND die Schaetzung.

    ANDERS ALS BEI DER ALTEN GEGENPRUEFUNG bekommt er die Schaetzung
    ABSICHTLICH mit. Dort wurde sie bewusst weggelassen, um einen Echo-Effekt
    zu vermeiden - richtig, solange er eine eigene Richtung ableiten sollte.
    Hier soll er sie ANGREIFEN; ohne sie zu kennen, koennte er das nicht.

    Der Echo-Effekt ist damit kein Risiko mehr, sondern ausgeschlossen: er
    liefert keine Richtung, die er von ihr abschreiben koennte."""
    return {
        "fakten": fakten,
        "zu_pruefende_schaetzung": {
            "szenarien": schaetzung.get("szenarien"),
            "bedingung_ziel": schaetzung.get("bedingung_ziel"),
            "belege": schaetzung.get("belege"),
        },
    }
