# -*- coding: utf-8 -*-
"""Wie weit kann sich der Kurs bewegen? (19.08.2026, Umbauplan Kapitel 93 A)

DIE EINE AUSSAGE, DIE DIESES SYSTEM EHRLICH TREFFEN KANN.

Die GROESSE einer Bewegung ist prognostizierbar, die RICHTUNG nicht - einer
der robustesten Befunde der Finanzoekonometrie: Volatilitaet clustert und ist
autokorreliert, Renditen sind es nicht. Deshalb liefert dieses Modul einen
TRICHTER und keine Kurve.

    in 5 Tagen liegt der Kurs mit 80 % zwischen X und Y

Was daraus folgt, ist die halbe Entscheidung: ob ein Stop ausserhalb der
ueblichen Schwankung liegt, ob ein Ziel in der Zeit ueberhaupt erreichbar
ist, wie lange man warten muss. Alles, was bisher geschaetzt wurde.

⚠️ DIE FAKTOREN SIND GEMESSEN, NICHT AUS DEM LEHRBUCH.

Die uebliche Zuordnung "1 Standardabweichung = 68 %" gilt hier NICHT. An
30.116 Ankern gemessen deckt 1,0 x ATR x sqrt(t) rund 81 % ab statt 68 % -
der Trichter waere zu weit.

DER GRUND IST KEINE MARKTEIGENSCHAFT, SONDERN EINE VERWECHSLUNG: ATR misst
die TAGESSPANNE (True Range, inklusive Luecken und Intraday-Extremen), der
Trichter aber die Aenderung von SCHLUSS zu SCHLUSS. Zwei verschiedene
Groessen; die erste ist systematisch groesser.

GEMESSEN (Quantile von |Schlussaenderung| / (ATR x sqrt(t))):

    Horizont      68 %    80 %    90 %    95 %
       5 Tage     0,72    0,96    1,32    1,69     n = 30.116
      20 Tage     0,73    0,98    1,34    1,74     n = 29.826
      60 Tage     0,76    1,01    1,41    1,88     n = 29.060

DIE WURZEL-ZEIT-SKALIERUNG TRAEGT: ueber einen zwoelffachen Horizont bewegen
sich die Faktoren um wenige Hundertstel. Deshalb genuegt EIN Faktor je
Wahrscheinlichkeit; die leichte Verbreiterung nach hinten ist die bekannte
Anhaeufung schwerer Raender und wird bewusst NICHT wegmodelliert - sie macht
den Trichter nach hinten leicht zu eng, und das ist die vorsichtige Seite.

⚠️ UEBERLEBENSVERZERRUNG. Die Reihen enthalten nur, was es noch gibt. Ein
Coin, der auf null ging, fehlt - der echte Trichter ist also breiter als der
gemessene. Wer ihn als Sicherheit liest, liest ihn falsch.
"""
from __future__ import annotations

import math

# Vielfaches von ATR x sqrt(t) je Wahrscheinlichkeit. Median ueber die drei
# gemessenen Horizonte, auf zwei Stellen.
FAKTOR = {0.68: 0.73, 0.80: 0.98, 0.90: 1.35, 0.95: 1.75}

# Die Horizonte, die in die Mail gehen. Fuenf Tage ist das Hebelfenster
# (die intensivste Phase einer Ausdehnung dauert laut Literatur 2-5
# Sitzungen), zwanzig das Swing-Fenster, sechzig die lange Sicht.
HORIZONTE = (5, 20, 60)

# Die Messgrundlage, damit sie nicht in einem Kommentar verloren geht.
ANKER_GEMESSEN = 30116
STAND = "2026-08-19"


class TrichterUnbekannt(RuntimeError):
    """Ohne Kurs oder ATR gibt es keine Spanne - und keine geratene."""


def spanne(kurs: float, atr: float, horizont: int,
           anteil: float = 0.80) -> dict:
    """Die Spanne, in der der Kurs nach `horizont` Handelstagen liegt.

    ⚠️ WIRFT, STATT ZU RATEN. Ein Trichter ohne Volatilitaet waere eine
    erfundene Zahl - und eine erfundene Spanne ist schlimmer als keine, weil
    Stop und Groesse daran haengen."""
    if not kurs or kurs <= 0 or not atr or atr <= 0:
        raise TrichterUnbekannt("Kurs oder ATR fehlt")
    if int(horizont) <= 0:
        raise TrichterUnbekannt(f"Horizont {horizont!r} ist nicht positiv")
    if anteil not in FAKTOR:
        raise TrichterUnbekannt(
            f"fuer {anteil!r} ist kein Faktor GEMESSEN - bekannt: "
            f"{sorted(FAKTOR)}. Zwischenwerte zu interpolieren hiesse, eine "
            f"Zahl zu erfinden, die nie geprueft wurde")
    weite = FAKTOR[anteil] * float(atr) * math.sqrt(int(horizont))
    return {"horizont": int(horizont), "anteil": float(anteil),
            "weite_eur": weite, "weite_relativ": weite / float(kurs),
            "unten_eur": float(kurs) - weite,
            "oben_eur": float(kurs) + weite}


def saetze(kurs: float, atr: float, anteil: float = 0.80,
           horizonte=HORIZONTE, stop_relativ: float | None = None,
           ) -> list[str]:
    """Die Zeilen fuer die Mail. Leer, wenn nichts berechenbar ist.

    KEINE RICHTUNG, KEINE MEINUNG. Der Satz sagt, wie weit - nicht wohin.
    Wer ihn als Prognose liest, liest mehr hinein, als dasteht; deshalb steht
    die Wahrscheinlichkeit im Satz und nicht im Kleingedruckten.

    ⚠️ DAS WORT "SCHWANKUNGSBREITE" IST IN DIESER MAIL BEREITS VERGEBEN.
    Weiter oben heisst es "der Widerstand liegt 0,7 Schwankungsbreiten
    hoeher" - dort ist EIN ATR als Massstab fuer Abstaende gemeint, die
    Tagesspanne. Der Trichter misst etwas anderes: die Aenderung von Schluss
    zu Schluss ueber MEHRERE Tage. Dasselbe Wort fuer zwei Groessen in einer
    Mail waere eine Falle, deshalb heisst es hier "uebliche Kursbewegung".
    """
    from agent.schreibweise import de

    try:
        werte = [spanne(kurs, atr, h, anteil) for h in horizonte]
    except TrichterUnbekannt:
        return []
    aus = [f"Uebliche Kursbewegung ({de(100 * anteil, 0)} % der Faelle, "
           f"Richtung offen):"]
    for w in werte:
        aus.append(f"   in {w['horizont']:>3} Handelstagen "
                   f"+/- {de(100 * w['weite_relativ'], 1)} %")

    # DIE BESCHREIBUNG (Nutzerwunsch 19.08.2026). Eine neue Zahl ohne Satz
    # daneben ist eine Zumutung: der Leser muss raten, ob sie eine Prognose,
    # eine Garantie oder eine Schaetzung ist. Hier ist sie keins davon.
    kurz = werte[0]
    aus.append(
        f"   Was das heisst: In {de(100 * anteil, 0)} von 100 vergleichbaren "
        f"Faellen blieb die Kursaenderung binnen "
        f"{kurz['horizont']} Handelstagen innerhalb dieser Spanne - nach oben "
        f"wie nach unten. In {de(100 - 100 * anteil, 0)} von 100 nicht.")
    aus.append(
        "   Der Trichter sagt WIE WEIT, nicht WOHIN. Er ist keine Prognose "
        "und wird breiter mit der Wurzel der Zeit, nicht linear.")

    # ⚠️ DER EINE SATZ, DER DEN TRICHTER NUETZLICH MACHT.
    #
    # Ein Stop innerhalb der ueblichen Bewegung wird vom gewoehnlichen Rauschen
    # getroffen - ohne dass die These widerlegt waere. Das ist die Frage, die
    # dieses Projekt seit dem Deadloop umkreist, und sie ist hier reine
    # Arithmetik aus zwei Zahlen, die ohnehin in der Mail stehen.
    if stop_relativ and stop_relativ > 0:
        eng = float(stop_relativ) < kurz["weite_relativ"]
        aus.append(
            f"   Ihr Stop liegt {de(100 * float(stop_relativ), 1)} % entfernt "
            + (f"und damit INNERHALB dieser Bewegung - er wird auch ohne "
               f"Gegenargument getroffen." if eng else
               f"und damit ausserhalb - gewoehnliches Schwanken allein "
               f"erreicht ihn nicht."))

    aus.append("   Gemessen an " + de(ANKER_GEMESSEN, 0) + " Ankern der "
               "eigenen Reihen (Umbauplan 93 A). Nicht zu verwechseln mit "
               "'Schwankungsbreiten' weiter oben - das ist die Tagesspanne "
               "als Massstab fuer Abstaende.")
    return aus
