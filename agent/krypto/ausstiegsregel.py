"""Ausstiegsregel: Trailing-Stop ab +1R (2026-08-04, Punkt 3.2).

DER BEFUND, DER SIE AUSLOEST. 50 % der Signale standen einmal bei +1R, aber
nur 17,6 % kamen am Ziel an. Positionen geben Gewinne regelmaessig zurueck -
das ist der groesste gemessene, bis heute ungenutzte Hebel des Systems.

DIE REGEL. Sobald die Position +1R im Plus stand (MFE >= ausloese_r), wird der
Stop auf `MFE - abstand_r` nachgezogen und nie wieder zurueckgenommen.

WAS SIE NICHT IST: ein Breakeven-Lock. Der wurde am 01.08. gemessen und
VERWORFEN - er kostet 63 % der Gewinner, weil der Kurs nach dem ersten
Antippen von +1R regelmaessig noch einmal unter den Einstand laeuft, bevor er
das Ziel nimmt. Der Trailing-Stop mit 1R Abstand laesst genau diesen Ruecklauf
zu und greift erst, wenn die Bewegung wirklich dreht.

GEMESSEN an 495 echten aufgeloesten Signalen (Hebel + Spot, Export 04.08.):

    IST (halten bis Barriere)          EW -0,176 R   SQN -3,07   PF 0,74
    Trailing ab 1,0 R, Abstand 1,0 R   EW -0,084 R   SQN -1,59   PF 0,85

Verbesserung +0,092 R je Signal, das SQN-Defizit halbiert sich. Gegengeprueft
nach Methodik:

  - Beitrags-Konzentration (2.5.5): 35 Symbole, groesstes traegt 16 % -
    kein Einzelsymbol traegt den Effekt
  - gepaarter Block-Bootstrap ueber Symbole: 95 %-Intervall
    [+0,051; +0,131] R, 100 % der Ziehungen positiv - gesichert
  - Split-Sample: erste Haelfte +0,120 R, zweite +0,076 R - haelt in beiden

Zum Vergleich die ebenfalls geprueften, schwaecheren Varianten: Teilverkauf
50 % bei +1R ergab nur +0,032 R, Trailing erst ab +1,5 R nur +0,038 R.

OFFENER VORBEHALT, ausdruecklich: alle Zahlen stammen aus EINER Marktphase
(Baerenregime). In einer Aufwaertsphase koennte ein Trailing-Stop Gewinner zu
frueh beenden - dort laufen Bewegungen weiter statt zu drehen. Die Regel ist
deshalb ueber die Config abschaltbar und ihre Parameter sind einstellbar,
ohne Codeaenderung.

ADVISORY-ONLY (P-7): dieses Modul rechnet nur. Es fuehrt nichts aus und
aendert keine Position - es liefert die Stop-Empfehlung, die angezeigt und
gemeldet wird.
"""
from __future__ import annotations

from agent.schreibweise import de as _de

from dataclasses import dataclass

# Gemessene Bestwerte, siehe Modul-Docstring. Ueber config.yaml
# risiko.ausstieg_* ueberschreibbar.
AUSLOESE_R = 1.0
ABSTAND_R = 1.0


@dataclass
class Stopempfehlung:
    """Ergebnis der Regel fuer EINE Position."""

    aktiv: bool                    # hat die Regel gegriffen?
    stop_empfohlen: float | None   # absoluter Kurs, None wenn nicht aktiv
    mfe_r: float                   # bisher hoechster Buchgewinn in R
    gesicherte_r: float            # was der nachgezogene Stop mindestens sichert
    begruendung: str


def stopempfehlung_aus_mfe(entry: float, stop_original: float, mfe_r: float,
                           ist_short: bool = False,
                           stop_aktuell: float | None = None,
                           ausloese_r: float = AUSLOESE_R,
                           abstand_r: float = ABSTAND_R) -> Stopempfehlung | None:
    """Wie stopempfehlung(), aber mit dem MFE direkt statt dem Hoechstkurs.

    WOFUER. Das Backward-Tracking schreibt seit dem 02.08. bei JEDEM Lauf
    `outcome_max_realisiertes_crv` fort - auch fuer noch offene Signale. Das
    IST der hoechste erreichte Buchgewinn in R, also genau die Eingabe dieser
    Regel. Sie muss deshalb nichts neu berechnen und braucht keine Kursreihe;
    der Wert steht bereits in der Zeile.

    Die Kursvariante bleibt fuer Aufrufer, die nur Kurse haben."""
    if not entry or entry <= 0 or stop_original is None or mfe_r is None:
        return None
    risiko = (stop_original - entry) if ist_short else (entry - stop_original)
    if risiko <= 0:
        return None
    if mfe_r < ausloese_r:
        return Stopempfehlung(
            aktiv=False, stop_empfohlen=None, mfe_r=mfe_r, gesicherte_r=0.0,
            begruendung=(f"noch nicht ausgeloest: hoechster Buchgewinn "
                         f"{mfe_r:.2f} R unter der Schwelle {ausloese_r:.1f} R"))
    hoechstkurs = (entry - risiko * mfe_r) if ist_short else (entry + risiko * mfe_r)
    return stopempfehlung(entry, stop_original, hoechstkurs, ist_short,
                          stop_aktuell, ausloese_r, abstand_r)


def stopempfehlung(entry: float, stop_original: float, hoechstkurs: float,
                   ist_short: bool = False, stop_aktuell: float | None = None,
                   ausloese_r: float = AUSLOESE_R,
                   abstand_r: float = ABSTAND_R) -> Stopempfehlung | None:
    """Nachgezogener Stop nach dem hoechsten erreichten Kurs.

    `hoechstkurs` ist bei einer LONG-Position das bisherige Hoch seit
    Eroeffnung, bei SHORT das bisherige Tief - also der jeweils GUENSTIGSTE
    erreichte Kurs, nicht der aktuelle.

    `stop_aktuell` verhindert ein Zurueckziehen: liegt bereits ein hoeherer
    Stop, bleibt er. Ein Trailing-Stop darf sich nie verschlechtern, sonst ist
    er keiner.

    Gibt None zurueck, wenn die Eingaben unbrauchbar sind - bewusst kein
    Ersatzwert. Eine geratene Stop-Empfehlung waere gefaehrlicher als keine."""
    if not entry or entry <= 0 or stop_original is None or hoechstkurs is None:
        return None
    risiko = (stop_original - entry) if ist_short else (entry - stop_original)
    if risiko <= 0:
        return None

    mfe_r = ((entry - hoechstkurs) if ist_short else (hoechstkurs - entry)) / risiko
    if mfe_r < ausloese_r:
        return Stopempfehlung(
            aktiv=False, stop_empfohlen=None, mfe_r=mfe_r, gesicherte_r=0.0,
            begruendung=(f"noch nicht ausgeloest: hoechster Buchgewinn "
                         f"{mfe_r:.2f} R unter der Schwelle {ausloese_r:.1f} R"))

    gesichert = mfe_r - abstand_r
    neuer = (entry - risiko * gesichert) if ist_short else (entry + risiko * gesichert)
    # Nie zurueckziehen - weder hinter den Originalstop noch hinter einen
    # bereits nachgezogenen.
    grenzen = [stop_original] + ([stop_aktuell] if stop_aktuell is not None else [])
    neuer = min([neuer] + grenzen) if ist_short else max([neuer] + grenzen)

    tatsaechlich = ((entry - neuer) if ist_short else (neuer - entry)) / risiko
    return Stopempfehlung(
        aktiv=True, stop_empfohlen=neuer, mfe_r=mfe_r, gesicherte_r=tatsaechlich,
        # DEUTSCH, WIE DER REST DER MAIL (17.08.2026). Dieser Satz steht
        # unter der Stopzeile und schrieb als einziger dort "1.90 R"
        # neben "+1,70 R" zwei Zeilen hoeher.
        begruendung=(f"Position stand bei {_de(mfe_r, 2)} R - Stop auf "
                     f"{_de(neuer, 4)} nachziehen, sichert "
                     f"{_de(tatsaechlich, 2, True)} R "
                     f"(Trailing ab {_de(ausloese_r, 1)} R, Abstand "
                     f"{_de(abstand_r, 1)} R)"))


def parameter_aus_config(config: dict) -> tuple[float, float, bool]:
    """(ausloese_r, abstand_r, aktiv) aus der Konfiguration.

    `aktiv=False` bei ausloese_r <= 0 - so laesst sich die Regel abschalten,
    ohne Code zu aendern. Das ist kein Komfort, sondern Vorsorge: die
    Kalibrierung stammt aus einer einzigen Marktphase."""
    risiko = config.get("risiko", {}) if isinstance(config, dict) else {}
    ausloese = risiko.get("ausstieg_trailing_ausloese_r", AUSLOESE_R)
    abstand = risiko.get("ausstieg_trailing_abstand_r", ABSTAND_R)
    try:
        ausloese, abstand = float(ausloese), float(abstand)
    except (TypeError, ValueError):
        return AUSLOESE_R, ABSTAND_R, True
    return ausloese, abstand, ausloese > 0 and abstand > 0
