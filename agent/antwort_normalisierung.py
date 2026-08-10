# -*- coding: utf-8 -*-
"""Formfehler korrigieren statt ablehnen (10.08.2026).

DER ANLASS ist ein Einwand des Nutzers gegen meine erste Fassung der
Validatoren: *"einige deiner Beispiele sind eigenartig - 250 EUR oder Tranche
abgelehnt - mir geht es um die Pruefung selbst, damit wir nichts blocken."*

Er hat recht, und der Fehler war grundsaetzlich. Eine Ablehnung ist die
haerteste moegliche Reaktion: sie loest eine Wiederholung aus, im Zweifel einen
Ausfall, und am Ende steht kein Signal. Das ist derselbe Deadloop wie bisher,
nur an einer anderen Stelle - und diesmal haette ich ihn selbst eingebaut.

DIE UNTERSCHEIDUNG, die gefehlt hat:

    FORMFEHLER   Das Modell hat die Aufgabe verstanden und die Konvention
                 verfehlt. "breit" statt "breit_getragen", 250 statt 300,
                 fuenf Belege statt vier. -> KORRIGIEREN.

    SINNFEHLER   Die Antwort ist in sich unbrauchbar. Mehr unabhaengige
                 Faktoren als Belege, ein Stop ueber dem Einstieg, eine
                 Handlung ohne Betrag. -> ABLEHNEN.

    GRENZBRUCH   Die Aussage ist gueltig, verletzt aber eine Vorgabe von
                 aussen. Tranche 500 bei einer Obergrenze von 100.
                 -> KAPPEN, nicht verwerfen.

WAS HIER NICHT KORRIGIERT WIRD: Inhalt. Eine Begruendung, die sich selbst
zurueckzieht, wird nicht umgeschrieben - sie wird abgelehnt. Wer Text
repariert, faelscht die Antwort und misst hinterher sich selbst.

JEDE KORREKTUR WIRD PROTOKOLLIERT. Haeufen sich dieselben Korrekturen, ist das
ein Befund ueber den Prompt, nicht ueber das Modell - dann ist die Frage
schlecht gestellt, und das gehoert repariert statt dauerhaft nachgebessert.
"""
from __future__ import annotations

import difflib


def naechste_tranche(wert, erlaubt: tuple) -> tuple[int | None, str | None]:
    """250 -> 300. Rundet auf die naechste erlaubte Tranche.

    NICHT abrunden und nicht abschneiden: bei gleichem Abstand gewinnt die
    KLEINERE - wer zwischen 100 und 500 genau in der Mitte landet, bekommt die
    vorsichtigere Groesse. Das ist die einzige Stelle, an der hier eine
    Richtung bevorzugt wird, und sie ist bewusst die zurueckhaltende."""
    try:
        z = float(str(wert).replace(",", ".").strip())
    except (TypeError, ValueError):
        return None, f"tranche {wert!r} ist keine Zahl"
    if int(z) in erlaubt:
        return int(z), None
    nah = min(erlaubt, key=lambda t: (abs(t - z), t))
    return nah, f"tranche {z:.0f} auf {nah} gerundet"


def naechstes_wort(wert, erlaubt: tuple) -> tuple[str | None, str | None]:
    """"breit" -> "breit_getragen". Ordnet freie Wortwahl dem Vokabular zu.

    Erst exakt, dann Teilzeichenkette in beide Richtungen, dann Aehnlichkeit.
    Bleibt alles erfolglos, wird NICHT geraten - dann ist es ein Sinnfehler
    (das Modell hat eine Kategorie erfunden) und gehoert abgelehnt."""
    if wert in erlaubt:
        return wert, None
    w = str(wert or "").strip().lower().replace(" ", "_").replace("-", "_")
    if not w:
        return None, None
    for e in erlaubt:
        if w == e.lower():
            return e, f"{wert!r} zu {e!r} vereinheitlicht"
    treffer = [e for e in erlaubt if w in e.lower() or e.lower().startswith(w)]
    if len(treffer) == 1:
        return treffer[0], f"{wert!r} zu {treffer[0]!r} ergaenzt"
    nah = difflib.get_close_matches(w, [e.lower() for e in erlaubt], n=1, cutoff=0.75)
    if nah:
        e = next(x for x in erlaubt if x.lower() == nah[0])
        return e, f"{wert!r} zu {e!r} korrigiert"
    return None, None


def kappe_auf(wert, obergrenze, erlaubt: tuple) -> tuple[int | None, str | None]:
    """500 bei Obergrenze 100 -> 100. Ein Grenzbruch verwirft nicht die Aussage.

    Die Belege und die Begruendung bleiben gueltig, wenn das Modell den Betrag
    zu hoch ansetzt - nur der Betrag war zu hoch. Ihn zu kappen erhaelt die
    Analyse; die Antwort zu verwerfen wirft sie weg."""
    z, hinweis = naechste_tranche(wert, erlaubt)
    if z is None:
        return None, hinweis
    if obergrenze is None or z <= obergrenze:
        return z, hinweis
    erlaubte_unter = [t for t in erlaubt if t <= obergrenze]
    if not erlaubte_unter:
        return None, f"keine Tranche unter der Obergrenze {obergrenze}"
    neu = max(erlaubte_unter)
    return neu, f"tranche {z} auf die Obergrenze {neu} gekappt"


def kuerze_liste(liste, hoechstens: int, was: str) -> tuple[list, str | None]:
    """Fuenf Belege statt vier sind kein Fehler - der fuenfte faellt weg.

    Behalten werden die ERSTEN. Sprachmodelle nennen das Wichtigste zuerst;
    hinten stehen die Nachzuegler."""
    if not isinstance(liste, list) or len(liste) <= hoechstens:
        return liste, None
    return liste[:hoechstens], f"{len(liste)} {was} auf {hoechstens} gekuerzt"


class Protokoll:
    """Sammelt, was korrigiert wurde - je Antwort, nicht global.

    Ein Protokoll ist kein Logeintrag: es geht mit der Antwort weiter und
    landet im Datensatz. Wer spaeter fragt, warum eine Tranche 300 statt 250
    ist, findet die Antwort dort und nicht in einer Logdatei von vorgestern."""

    def __init__(self) -> None:
        self.eintraege: list[str] = []

    def dazu(self, hinweis: str | None) -> None:
        if hinweis:
            self.eintraege.append(hinweis)

    def __bool__(self) -> bool:
        return bool(self.eintraege)

    def __str__(self) -> str:
        return "; ".join(self.eintraege)
