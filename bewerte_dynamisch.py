"""Ergebnis unter der LIVE gefahrenen Ausstiegsregel statt starrer Barrieren.

WARUM ES DAS BRAUCHT. Das statische Halten bis zur Barriere wurde am 06.08.
ausdruecklich als falsches Instrument verworfen
(`Konstruktion_Zeitskalen_06_08.md`, V3): der Median-Trade ist nach 1-2 Tagen
entschieden, aber 26 bis 45 % erreichen ihren Bestwert erst NACH Tag 5. Ein
fester Horizont muesste fuer den Median viel zu lang sein, um dem Viertel
gerecht zu werden. Live laeuft seit dem 05.08. stattdessen die
**Ausstiegsregel: Trailing-Stop ab +1R** (`agent/krypto/ausstiegsregel.py`).

Wer Signale gegen starre Barrieren bewertet, misst deshalb ein Verfahren, das
die Produktion nicht faehrt. Genau das habe ich am 09.08. getan und darauf
Zufallsvergleich, Nachweisrahmen und Verlustzerlegung gestellt.

DIE REGEL, wortgleich zur Produktion: sobald der hoechste Buchgewinn (MFE) die
Schwelle `ausloese_r` erreicht hat, wird der Stop auf `MFE - abstand_r`
nachgezogen und NIE zurueckgenommen. Gemessene Wirkung an 495 aufgeloesten
Signalen: Erwartungswert -0,176 -> -0,084 R, SQN -3,07 -> -1,59.

ZWEI KONVENTIONEN, die beide konservativ sind und beide begruendet:

  1. STOP SCHLAEGT ZIEL am selben Tag. Aus einer Tageskerze ist die Reihenfolge
     innerhalb des Tages nicht rekonstruierbar; Kapitalerhalt vor Gewinn.
     Identisch zu `check_hebel_signal_outcome()` und `simuliere_signal()`.
  2. DER TRAILING-STOP WIRD AM TAGESENDE NACHGEZOGEN, geprueft wird er ab dem
     FOLGETAG. Wuerde man das Tageshoch verwenden, um den Stop zu setzen, und
     ihn dann gegen das Tief DESSELBEN Tages pruefen, waere das ein Blick in
     den Tagesverlauf, den man real nicht hat. Diese Reihenfolge kostet
     Ergebnis - und ist die einzige ehrliche.

WAS DIESES MODUL NICHT TUT: die UEBERHOLUNG durch eine neuere Analyse
nachbilden. 30,3 % der abgeschlossenen Hebel-Signale und 67,6 % der
Spot-Signale enden so. Sie ist kein Marktereignis, sondern ein
Betriebsereignis aus unserer eigenen Neubewertungs-Kadenz - sie zu simulieren
hiesse, unsere kuenftigen Entscheidungen zu simulieren, um unsere
Entscheidungen zu bewerten. Das ist zirkulaer.

Stattdessen `kappung_tage`: die Haltedauer auf die in der Produktion gemessene
mediane Zeit-bis-Ueberholung begrenzen. Das verwandelt eine nicht messbare
Groesse in eine BEKANNTE Abschneidung. Wer sie setzt, bekommt eine
konservative Untergrenze; wer sie weglaesst, die Frage "was haette das Signal
gebracht, wenn es haette laufen duerfen".
"""
from __future__ import annotations

from dataclasses import dataclass

from agent.krypto.ausstiegsregel import ABSTAND_R, AUSLOESE_R


@dataclass
class DynamischesErgebnis:
    ausgang: str          # ziel / trailing / stop / zensiert / gekappt
    r: float
    mfe_r: float
    tag: int
    stop_am_ende: float
    trailing_aktiv: bool


def _r(entry: float, kurs: float, risiko: float, ist_short: bool) -> float:
    return ((entry - kurs) if ist_short else (kurs - entry)) / risiko


def bewerte_mit_trailing(zonen: dict, kerzen: list, horizont: int = 14,
                         ausloese_r: float = AUSLOESE_R,
                         abstand_r: float = ABSTAND_R,
                         kappung_tage: int | None = None) -> DynamischesErgebnis | None:
    """`kerzen` sind die Tage NACH dem Signaltag, chronologisch.

    `zonen` braucht entry, stop, ziel, risiko, ist_short - genau die Form, die
    `_zonen()` und `_zonen_absolut()` liefern. Eine eigene Zonenrechnung waere
    die dritte Fassung derselben Formel und driftet garantiert weg.
    """
    entry = zonen.get("entry")
    stop0 = zonen.get("stop")
    ziel = zonen.get("ziel")
    risiko = zonen.get("risiko")
    kurz = bool(zonen.get("ist_short"))
    if not entry or entry <= 0 or stop0 is None or ziel is None:
        return None
    if not risiko or risiko <= 0:
        return None

    grenze = horizont if kappung_tage is None else min(horizont, kappung_tage)
    stop_eff = stop0
    mfe_r = 0.0
    trailing_aktiv = False
    tag = 0

    for tag, k in enumerate(kerzen[:grenze], start=1):
        hoch, tief = k.high, k.low
        if hoch is None or tief is None:
            continue
        ungueneig = hoch if kurz else tief
        guenstig = tief if kurz else hoch

        # 1) STOP ZUERST - mit dem Stand VOM VORTAG. Der heute nachgezogene
        #    Stop darf den heutigen Tag nicht mehr betreffen (Konvention 2).
        getroffen = (ungueneig >= stop_eff) if kurz else (ungueneig <= stop_eff)
        if getroffen:
            r = _r(entry, stop_eff, risiko, kurz)
            return DynamischesErgebnis(
                ausgang="trailing" if trailing_aktiv else "stop",
                r=r, mfe_r=mfe_r, tag=tag, stop_am_ende=stop_eff,
                trailing_aktiv=trailing_aktiv)

        # 2) ZIEL
        erreicht = (tief <= ziel) if kurz else (hoch >= ziel)
        if erreicht:
            return DynamischesErgebnis(
                ausgang="ziel", r=_r(entry, ziel, risiko, kurz), mfe_r=max(
                    mfe_r, _r(entry, ziel, risiko, kurz)),
                tag=tag, stop_am_ende=stop_eff, trailing_aktiv=trailing_aktiv)

        # 3) MFE fortschreiben und Stop nachziehen - GILT AB MORGEN
        mfe_r = max(mfe_r, _r(entry, guenstig, risiko, kurz))
        if mfe_r >= ausloese_r:
            gesichert = mfe_r - abstand_r
            neuer = (entry - risiko * gesichert) if kurz else (entry + risiko * gesichert)
            # Nie zurueckziehen - sonst ist es kein Trailing-Stop.
            stop_eff = min(stop_eff, neuer) if kurz else max(stop_eff, neuer)
            trailing_aktiv = True

    letzte = kerzen[min(grenze, len(kerzen)) - 1] if kerzen else None
    schluss = getattr(letzte, "close", None) if letzte is not None else None
    return DynamischesErgebnis(
        ausgang="gekappt" if (kappung_tage is not None and grenze < horizont)
                else "zensiert",
        r=_r(entry, schluss, risiko, kurz) if schluss else 0.0,
        mfe_r=mfe_r, tag=tag, stop_am_ende=stop_eff,
        trailing_aktiv=trailing_aktiv)


def breakeven_trefferquote(crv: float) -> float:
    """1/(1+CRV) - die Latte, gegen die eine Trefferquote gehoert.

    NICHT der Muenzwurf. Bei CRV 2,0 liegt sie bei 33,3 %, bei 3,0 bei 25,0 %.
    Eine Quote von 40 % ist bei CRV 1,0 schlecht und bei CRV 3,0 sehr gut -
    ohne diese Bezugsgroesse ist jede Trefferquote bedeutungslos."""
    if crv is None or crv <= 0:
        return float("nan")
    return 1.0 / (1.0 + crv)
