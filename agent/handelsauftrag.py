# -*- coding: utf-8 -*-
"""Was ueberhaupt gehandelt wird: Instrument und Strategie (Paket 2, 12.08.2026).

DIE LUECKE, die das schliesst. Bis heute kamen `strategie`, `hebel`, `spot` und
`instrument` in der neuen Rollen-Kette **null Mal** vor. Der Trader urteilte,
ohne zu wissen, WORUEBER er urteilt - und deshalb liess sich die Frage des
Nutzers ("Long 3x, Einstieg bei ca., TP bei ca.") gar nicht beantworten.

Ein echter Haendler entscheidet bei 3x Hebel anders als bei einem
Spot-Einmalkauf: dieselben Fakten, anderer Trade. Diese Bedingung fehlte
vollstaendig.

VORGABE, NICHT FRAGE. Der Aufrufer weiss immer, worum es geht - `krypto/pipeline`
und `krypto/hebel_pipeline` sind getrennte Pipelines. Also wird es uebergeben,
nicht erfragt. Dieselbe Linie wie beim Betrag (R-A2): was feststeht, geben wir
vor; ein Modell danach zu fragen fuegt nur eine Fehlerquelle hinzu.

WARUM EIN EIGENES MODUL. Zwei Stellen brauchen dieselbe Definition - der PROMPT
(`rolle_trader`) und der FAKTENSATZ (`rollen_eingabe`). Zwei Kopien einer Liste
laufen auseinander, und dann fragt der Prompt nach etwas, das die Eingabe nicht
kennt. Genau dieser Fehler ist am 12.08. schon einmal passiert: die Marktbreite
war aus den Fakten raus, die Frage danach stand noch im Prompt.

WAS HIER NOCH NICHT STEHT: Richtung (LONG/SHORT) und Hebelfaktor. Die gehoeren
zu Paket 13 - erst wenn Spot durchgemessen ist, wissen wir, ob die Kette traegt.
`hebel` ist hier bereits vorgesehen, damit die Kosten-Fakten schon jetzt richtig
zugeordnet werden.
"""
from __future__ import annotations

INSTRUMENTE = ("spot", "hebel", "absicherung")

# STRATEGIE heisst hier: wie wird eingestiegen und woran wird der Erfolg
# gemessen - nicht, in welche Richtung.
#
#   einstieg      ein Zeitpunkt, ein Ziel, ein Stop. Erfolg = Ziel vor Stop
#   swing         wie einstieg, aber mit Haltekriterium und nachgezogenem Stop
#   akkumulation  gestaffelt ueber Zeit. Sie hat SEHR WOHL ein Ziel - nur
#                 kein nahes: gekauft wird in der Erwartung hoeherer Kurse auf
#                 lange Sicht (Nutzerkorrektur 12.08.: "bei Akkumulation gibt
#                 es eigentlich kein NICHT-Ziel, sondern nur kein NAHES Ziel").
#
#                 Was fehlt, ist nicht die Erwartung, sondern der ABBRUCH: ein
#                 fallender Kurs beendet die Position nicht, er verbilligt sie.
#                 Ein Stop wuerde die Strategie in ihrem besten Moment
#                 abbrechen. Deshalb kein Stop und kein einzelner Zeitpunkt -
#                 und deshalb ein ANDERES Erfolgsmass: Durchschnittskurs und
#                 Endvermoegen statt "Ziel vor Stop".
#
#                 FOLGE, die leicht zu uebersehen ist: `umgeworfen_durch` ist
#                 hier nicht ein Feld unter vielen, sondern das EINZIGE
#                 Ausstiegskriterium. Wo Einstieg und Swing einen Stop haben,
#                 hat die Akkumulation nur die Frage "wann traegt die Erwartung
#                 nicht mehr".
STRATEGIEN = ("einstieg", "swing", "akkumulation")

# WELCHE PAARE SINNVOLL SIND, und warum die uebrigen fehlen:
#
#   hebel x akkumulation   Die Finanzierung kostet JEDEN Tag. Eine Strategie,
#                          die bewusst lange laeuft, zahlt genau diese Kosten
#                          am laengsten - das ist keine Frage der Meinung,
#                          sondern der Kostenrechnung.
#   absicherung x swing    Absicherung folgt dem Portfolio, nicht einem
#                          Kursverlauf. Ein nachgezogener Stop auf einem
#                          Short-Produkt sichert den Schutz weg, den man
#                          aufgebaut hat.
#   absicherung x akkum.   Entschieden am 12.08. (E1a): Absicherung bekommt
#                          keine Tranchen - die Staffelungsregel wirkte dort
#                          mit umgekehrtem Vorzeichen.
ERLAUBTE_PAARE = {
    "spot": ("einstieg", "swing", "akkumulation"),
    "hebel": ("einstieg", "swing"),
    "absicherung": ("einstieg",),
}

# Braucht diese Kombination einen Einstiegskurs und einen STOP?
#
# Die Frage ist NICHT "gibt es ein Ziel" - das hat auch die Akkumulation, nur
# kein nahes. Die Frage ist, ob es einen einzelnen Zeitpunkt und einen Abbruch
# gibt. Bei Akkumulation nicht: ein Stop wuerde die Staffelung genau dann
# aufheben, wenn sie am guenstigsten kauft.
_MIT_KURSEN = {("spot", "akkumulation"): False}


class AuftragUngueltig(ValueError):
    """Instrument und Strategie passen nicht zusammen."""


def pruefe(instrument: str, strategie: str) -> tuple[str, str]:
    """Wirft, statt still auf einen Vorgabewert zu fallen.

    Ein stiller Rueckfall waere hier besonders teuer: er wuerde einen
    Hebel-Trade als Spot-Trade bewerten - mit denselben Fakten, aber ohne die
    Finanzierungskosten, die ihn erst teuer machen."""
    i = str(instrument or "").strip().lower()
    s = str(strategie or "").strip().lower()
    if i not in INSTRUMENTE:
        raise AuftragUngueltig(f"Instrument {instrument!r} - erlaubt {INSTRUMENTE}")
    if s not in STRATEGIEN:
        raise AuftragUngueltig(f"Strategie {strategie!r} - erlaubt {STRATEGIEN}")
    if s not in ERLAUBTE_PAARE[i]:
        raise AuftragUngueltig(
            f"{i} + {s} ist keine vorgesehene Kombination - erlaubt fuer {i}: "
            f"{ERLAUBTE_PAARE[i]}")
    return i, s


def mit_kursen(instrument: str, strategie: str) -> bool:
    """Werden Einstiegskurs und Stop ueberhaupt gebraucht?"""
    return _MIT_KURSEN.get((instrument, strategie), True)


# Der Satz, der im Faktensatz steht. Er nennt die BEDINGUNG, unter der geurteilt
# wird - keine Aufforderung und keine Wertung (R-T3).
_SATZ_INSTRUMENT = {
    "spot": "Gehandelt wird der Wert selbst, ohne Hebel und ohne laufende "
            "Kosten.",
    "hebel": "Gehandelt wird eine gehebelte Position. Die Finanzierung faellt "
             "an JEDEM Tag an, in dem die Position offen ist, und ein "
             "Rueckschlag kann zur Zwangsaufloesung fuehren.",
    "absicherung": "Gehandelt wird ein Absicherungsinstrument. Es soll das "
                   "uebrige Portfolio abfedern, nicht selbst Gewinn erzielen.",
}
_SATZ_STRATEGIE = {
    "einstieg": "Es geht um einen einzelnen Einstieg mit einem Ziel und einem "
                "Ausstiegskurs.",
    "swing": "Die Position soll ueber mehrere Wochen gehalten und laufend "
             "nachgezogen werden.",
    "akkumulation": "Es wird ueber die Zeit gestaffelt gekauft, in der "
                    "Erwartung hoeherer Kurse auf lange Sicht. Ein fallender "
                    "Kurs beendet diese Position nicht - er verbilligt sie. "
                    "Deshalb gibt es hier keinen einzelnen Einstiegszeitpunkt "
                    "und keinen Stop; beendet wird sie erst, wenn die "
                    "Erwartung selbst nicht mehr traegt.",
}


def beschreibe(instrument: str, strategie: str) -> list[str]:
    """Zwei Saetze fuer den Faktensatz - Bedingung, nicht Anweisung.

    DIESES FELD IST EIN KONSTANTES FELD, und `finde_konstanten()` meldet es
    auch. Das ist kein Versehen und wird NICHT durch eine Ausnahme im Waechter
    stillgelegt (Gegenpruefung 12.08.):

      * Es ist konstant je LAUF, nicht ueber Laeufe hinweg. Ein Hebel-Lauf und
        ein Spot-Lauf tragen verschiedene Saetze - genau das ist der Zweck.
      * R-T6 richtet sich gegen Felder, die nicht unterscheiden KOENNEN und
        trotzdem eine Richtung nahelegen. Dieses hier soll nicht zwischen
        Assets unterscheiden; es ist die BEDINGUNG, unter der sie alle
        beurteilt werden.

    DAS RESTRISIKO IST TROTZDEM REAL und gehoert benannt: der Hebel-Satz nennt
    laufende Kosten und die Zwangsaufloesung. Beides ist wahr, aber es koennte
    JEDE Hebel-Beurteilung gleichfoermig daempfen - und eine gleichfoermige
    Daempfung sieht aus wie Vorsicht und ist keine.

    MESSPUNKT, nicht Annahme: eine gepaarte Messung auf denselben Ankern, ein
    Arm spot und einer hebel, zeigt es. Faellt die Handlungsquote im
    Hebel-Arm deutlich staerker, als die Kostenrechnung hergibt, ist der Satz
    zu stark formuliert - und dann wird der SATZ geaendert, nicht der Waechter.
    """
    i, s = pruefe(instrument, strategie)
    return [_SATZ_INSTRUMENT[i], _SATZ_STRATEGIE[s]]
