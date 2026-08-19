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

Die uebliche Zuordnung "1 Standardabweichung = 68 %" gilt hier NICHT. DER
GRUND IST KEINE MARKTEIGENSCHAFT, SONDERN EINE VERWECHSLUNG: ATR misst die
TAGESSPANNE (True Range, inklusive Luecken und Intraday-Extremen), der
Trichter aber die Aenderung von SCHLUSS zu SCHLUSS. Zwei verschiedene
Groessen; die erste ist systematisch groesser.

⚠️ UND ES GIBT KEINEN FAKTOR FUER ALLE (Korrektur 19.08.2026, Fallstrick A2).

Die erste Fassung lieferte EINEN Faktor 0,98 fuer jeden Wert. Die
Trefferquotenmessung (`messe_trichter_treffer.py`) hat ihn widerlegt: er
passt auf keine einzige Anlageklasse.

    Klasse    Reihen   Anker   Quote mit 0,98   eigener Faktor (80 %)
    krypto        34  23.343      87,5 %              0,79
    aktien         2   3.875      83,8 %              0,91
    etf            4   8.877      72,7 %              1,18

Der Unterschied ist ueber einen ZWOELFFACHEN Horizont stabil (5/20/60 Tage)
- das ist keine Streuung, sondern eine Klasseneigenschaft. Fuer Krypto war
der Trichter rund ein Viertel zu weit, fuer ETF deutlich zu eng.

⚠️ ZWEI FEHLER STECKTEN IN DER ERSTEN KALIBRIERUNG:

1. Vier interne HILFSREIHEN (_THEMEN_ETF_BENCHMARK_SPY und drei
   _ROHSTOFF_FUTURES) waren mitgezaehlt. Fuer sie entsteht nie eine Mail,
   aber sie reichen bis 2001 zurueck und stellten die HAELFTE aller Anker.
   Der Faktor 0,98 ist zur Haelfte auf Werten gewachsen, die das System
   nicht handelt.
2. Der scheinbare Anstieg der Trefferquote in 2025/26 (86 % statt 80 %) sah
   nach ALTERUNG aus und war ZUSAMMENSETZUNG: die juengeren Bloecke sind
   kryptolastig. Auf konstanter Besetzung gemessen war die Quote dort
   NIEDRIGER, nicht hoeher.

⚠️ UEBERLEBENSVERZERRUNG BLEIBT. Die Reihen enthalten nur, was es noch gibt.
Ein Coin, der auf null ging, fehlt - der echte Trichter ist also breiter als
der gemessene. Wer ihn als Sicherheit liest, liest ihn falsch.

NACHPRUEFEN: `python messe_trichter_treffer.py` - Walk-Forward, Gegenprobe
auf konstanter Besetzung und Quote je Klasse. Der Lauf endet mit Rueckgabe 2,
wenn der Trichter nicht mehr traegt.
"""
from __future__ import annotations

import math

# Vielfaches von ATR x sqrt(t) je Wahrscheinlichkeit UND Anlageklasse.
# Median ueber die drei gemessenen Horizonte, auf zwei Stellen.
FAKTOR_JE_KLASSE = {
    "krypto": {0.68: 0.59, 0.80: 0.79, 0.90: 1.11, 0.95: 1.51},
    "aktien": {0.68: 0.68, 0.80: 0.91, 0.90: 1.28, 0.95: 1.76},
    "etf":    {0.68: 0.88, 0.80: 1.18, 0.90: 1.61, 0.95: 2.03},
}

# RUECKFALL fuer Klassen ohne eigene Messung - ueber alle handelbaren Reihen,
# OHNE die vier Hilfsreihen. Rohstoffe landen heute hier: sie haben in der
# Datenbank keine eigene Kursreihe mit genug Historie.
#
# ⚠️ Ein Rueckfall ist kein Messwert fuer diese Klasse. Die Mail sagt das
# ausdruecklich, statt eine fremde Zahl als eigene auszugeben.
FAKTOR = {0.68: 0.66, 0.80: 0.90, 0.90: 1.27, 0.95: 1.71}

# Die Messgrundlage je Klasse: (Reihen, Anker auf 5 Tage). Sie steht in der
# Mail, weil eine Zahl aus zwei Reihen anders zu lesen ist als eine aus 34.
GRUNDLAGE = {"krypto": (34, 23343), "aktien": (2, 3875), "etf": (4, 8877)}
# Wie die Klasse im Satz heisst - "Etf-Reihen" liest sich wie ein Tippfehler.
NAME = {"krypto": "Krypto", "aktien": "Aktien", "etf": "ETF"}
ANKER_GEMESSEN = 36095
REIHEN_GEMESSEN = 40

# Ab wie vielen Reihen taugt eine Klassenmessung als eigenstaendige Aussage?
# Unter fuenf Reihen ist sie eher die Eigenart weniger Werte als die der
# Klasse - das gehoert dazugesagt, nicht verschwiegen.
SCHMALE_GRUNDLAGE_REIHEN = 5

# Die Horizonte, die in die Mail gehen. Fuenf Tage ist das Hebelfenster
# (die intensivste Phase einer Ausdehnung dauert laut Literatur 2-5
# Sitzungen), zwanzig das Swing-Fenster, sechzig die lange Sicht.
HORIZONTE = (5, 20, 60)

STAND = "2026-08-19"


class TrichterUnbekannt(RuntimeError):
    """Ohne Kurs oder ATR gibt es keine Spanne - und keine geratene."""


def faktoren(klasse: str | None = None) -> tuple[dict, str | None]:
    """Die Faktoren fuer diese Anlageklasse - und WELCHE es geworden sind.

    Gibt (Faktoren, Klassenname oder None) zurueck. None heisst: fuer diese
    Klasse liegt keine eigene Messung vor, es gilt der Rueckfall. Der Aufrufer
    MUSS das unterscheiden koennen, sonst verkauft er einen Rueckfall als
    Messwert."""
    k = str(klasse or "").strip().lower()
    if k in FAKTOR_JE_KLASSE:
        return FAKTOR_JE_KLASSE[k], k
    return FAKTOR, None


def spanne(kurs: float, atr: float, horizont: int,
           anteil: float = 0.80, klasse: str | None = None) -> dict:
    """Die Spanne, in der der Kurs nach `horizont` Handelstagen liegt.

    ⚠️ WIRFT, STATT ZU RATEN. Ein Trichter ohne Volatilitaet waere eine
    erfundene Zahl - und eine erfundene Spanne ist schlimmer als keine, weil
    Stop und Groesse daran haengen."""
    if not kurs or kurs <= 0 or not atr or atr <= 0:
        raise TrichterUnbekannt("Kurs oder ATR fehlt")
    if int(horizont) <= 0:
        raise TrichterUnbekannt(f"Horizont {horizont!r} ist nicht positiv")
    tabelle, gemessen = faktoren(klasse)
    if anteil not in tabelle:
        raise TrichterUnbekannt(
            f"fuer {anteil!r} ist kein Faktor GEMESSEN - bekannt: "
            f"{sorted(tabelle)}. Zwischenwerte zu interpolieren hiesse, eine "
            f"Zahl zu erfinden, die nie geprueft wurde")
    weite = tabelle[anteil] * float(atr) * math.sqrt(int(horizont))
    return {"horizont": int(horizont), "anteil": float(anteil),
            "klasse": gemessen, "faktor": tabelle[anteil],
            "weite_eur": weite, "weite_relativ": weite / float(kurs),
            "unten_eur": float(kurs) - weite,
            "oben_eur": float(kurs) + weite}


def _grundlage_satz(klasse: str | None) -> str:
    """Woher die Zahl stammt - und wie belastbar sie ist."""
    from agent.schreibweise import de

    if not klasse:
        return ("   Fuer diese Anlageklasse liegt KEINE eigene Messung vor - "
                "es gilt der Wert ueber alle " + de(REIHEN_GEMESSEN, 0)
                + " eigenen Reihen (" + de(ANKER_GEMESSEN, 0) + " Anker).")
    reihen, anker = GRUNDLAGE[klasse]
    satz = ("   Gemessen an " + de(anker, 0) + " Ankern aus " + de(reihen, 0)
            + " eigenen " + NAME[klasse] + "-Reihen.")
    if reihen < SCHMALE_GRUNDLAGE_REIHEN:
        satz += (" Nur " + de(reihen, 0) + " Reihen - das ist eher die "
                 "Eigenart dieser Werte als die der Anlageklasse.")
    return satz


def saetze(kurs: float, atr: float, anteil: float = 0.80,
           horizonte=HORIZONTE, stop_relativ: float | None = None,
           klasse: str | None = None) -> list[str]:
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
        werte = [spanne(kurs, atr, h, anteil, klasse) for h in horizonte]
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

    aus.append(_grundlage_satz(kurz["klasse"]))
    aus.append("   Nicht zu verwechseln mit 'Schwankungsbreiten' weiter oben "
               "- das ist die Tagesspanne als Massstab fuer Abstaende.")
    return aus
