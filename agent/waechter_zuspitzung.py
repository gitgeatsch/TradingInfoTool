# -*- coding: utf-8 -*-
"""Waechter fuer ZWISCHENAUSGABEN - findet Zuspitzungen ohne Deckung.

WOZU, und warum es dafuer einen zweiten Waechter braucht.

`szenario_fakten.enthaelt_werturteile()` prueft FELDNAMEN in einem
Faktensatz-Dict (`*einordnung*`, `*bewertung*`, `*_label`). Das ist die richtige
Pruefung fuer strukturierte Eingaben - und sie greift nicht bei dem, was hier
passiert ist.

DER BEFUND VOM 11.08. (Arbeitsstand 7.13). Das Lagebild bekam:

    "Von 13 beobachteten Coins stehen 1 ueber ihrer 50-Tage-Linie (8 %).
     In den letzten 250 Handelstagen war dieser Anteil in 46 % DER FAELLE
     NIEDRIGER."

Also ein knapp durchschnittlicher Wert - der Kalibrierungssatz sagt es
ausdruecklich. Ausgegeben wurde:

    "Der Gesamtmarkt befindet sich in einer EXTREMEN SCHIEFLAGE mit starkem
     Abwaertsdruck."

Und dieser Satz erreichte die Entscheidungs-Rolle als Beleg mit Gewicht HOCH.

DIE LUECKE IST ARCHITEKTONISCH, nicht sprachlich: Wir haben Werturteile aus den
EINGABEN verbannt. Die Ausgabe des Lagebilds ist die EINGABE der Entscheidung -
und niemand prueft sie. B2 ist damit nicht behoben, sondern verschoben: das
Urteil entsteht jetzt im System selbst.

Nutzer am 11.08.: *"Die Ablaufkette muss von Anfang bis zum Ende wie ein Uhrwerk
funktionieren - ein Ausrutscher innerhalb der Kette kann im worst case das ganze
System kippen, oder als U-Boot unterschwellig massive Verschiebung erzeugen."*
Genau diese Sorte: es stuerzt nichts ab, es NEIGT alles.

ZWEI STUFEN, weil ein Waechter, der staendig feuert, ignoriert wird:

    HART    Woerter, die einen Grad behaupten, den keine Zahl hergibt.
            Sie gehoeren nie in eine Beschreibung ohne ausdrueckliche Deckung.
    WEICH   Woerter, die je nach Kontext berechtigt sein koennen. Werden
            gezaehlt und berichtet, aber nicht als Verstoss gewertet.

DECKUNG. Ein Grad ist gedeckt, wenn die EINGABE ihn hergibt - bei uns ueber den
historischen Bezug ("in P % der Faelle war dieser Anteil niedriger"). Liegt P im
mittleren Band, ist die Lage unauffaellig und ein hartes Wort unbelegt. Fehlt
der Bezug ganz, ist JEDES harte Wort unbelegt: dann gibt es keinen Massstab.
"""
from __future__ import annotations

import re

# Behaupten einen Grad. Ohne Deckung in der Eingabe sind sie erfunden.
HART = (
    "extrem", "massiv", "dramatisch", "drastisch", "gravierend", "alarmierend",
    "katastrophal", "panisch", "panik", "euphorisch", "euphorie", "ueberwaeltigend",
    "beispiellos", "rekord", "aeusserst", "hoechst", "enorm", "kollaps",
    "absturz", "einbruch", "crash", "ausverkauf", "kapitulation",
)

# Kontextabhaengig. Werden gezaehlt, aber nicht als Verstoss gewertet.
WEICH = (
    "stark", "schwach", "deutlich", "erheblich", "klar", "eindeutig", "kaum",
    "sehr", "ausgepraegt", "spuerbar",
)

# Ausserhalb dieses Bandes darf ein Grad behauptet werden - dann IST die Lage
# aussergewoehnlich. Innerhalb ist sie es nicht.
BAND_UNAUFFAELLIG = (15, 85)

# ZWEI SCHREIBWEISEN, weil das Lagebild seine Sprache gewechselt hat (12.08.).
#
#   1  Die Marktbreite sagte "in 66 % der Faelle war dieser Anteil niedriger".
#      Sie wird mit L1 gestrichen - das Muster bleibt, damit aeltere Laeufe und
#      gespeicherte Faelle weiter pruefbar sind.
#   2  `agent/marktlage.py` sagt "im 97. Perzentil der letzten 250 Handelstage".
#
# WARUM DAS EINE PFLICHTAENDERUNG WAR und keine Kosmetik: ohne Muster 2 haette
# `deckung()` nach der Streichung LEER zurueckgegeben, und leer heisst hier
# "kein Massstab" - also gilt jedes Gradwort als unbelegt. Das scheitert sicher,
# aber falsch: bei einem echten 97. Perzentil DARF das Modell deutlich werden.
# Ein Waechter, der auch das Wahre verbietet, wird umgangen statt befolgt.
_BEZUG = re.compile(
    r"in\s+(\d{1,3})\s*%\s+der\s+Faelle\s+niedriger"     # alte Marktbreite
    r"|im\s+(\d{1,3})\.\s*perzentil",                    # marktlage.py
    re.I)


def _normal(text: str) -> str:
    t = (text or "").lower()
    for a, b in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss")):
        t = t.replace(a, b)
    return t


def finde_grade(text: str) -> tuple[list[str], list[str]]:
    """Welche harten und weichen Gradwoerter stehen im Text?"""
    t = _normal(text)
    return ([w for w in HART if w in t], [w for w in WEICH if w in t])


def deckung(eingabe) -> list[int]:
    """Die Perzentile, die die Eingabe nennt. Leer heisst: kein Massstab."""
    text = " ".join(eingabe) if isinstance(eingabe, (list, tuple)) else str(eingabe)
    # `findall` liefert je Treffer ein Tupel mit einer gefuellten Gruppe -
    # welche, haengt von der Schreibweise ab.
    return [int(g) for treffer in _BEZUG.findall(_normal(text))
            for g in (treffer if isinstance(treffer, tuple) else (treffer,)) if g]


def pruefe(ausgabe: str, eingabe) -> dict:
    """Traegt die Eingabe den Grad, den die Ausgabe behauptet?

    Rueckgabe mit `verstoss=True`, wenn ein hartes Gradwort ohne Deckung steht.
    Das ist bewusst die einzige harte Aussage - alles andere wird berichtet."""
    hart, weich = finde_grade(ausgabe)
    perzentile = deckung(eingabe)
    if not perzentile:
        gedeckt = False
        grund = "die Eingabe nennt keinen historischen Bezug - kein Massstab"
    else:
        aussen = [p for p in perzentile
                  if p < BAND_UNAUFFAELLIG[0] or p > BAND_UNAUFFAELLIG[1]]
        gedeckt = bool(aussen)
        grund = (f"Perzentil(e) {perzentile} - "
                 + ("aussergewoehnlich, Grad gedeckt" if aussen
                    else f"im unauffaelligen Band {BAND_UNAUFFAELLIG}"))
    return {
        "hart": hart,
        "weich": weich,
        "perzentile": perzentile,
        "gedeckt": gedeckt,
        "grund": grund,
        "verstoss": bool(hart) and not gedeckt,
    }
