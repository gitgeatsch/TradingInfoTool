# -*- coding: utf-8 -*-
"""Eine Schreibweise fuer Zahlen - deutsch, an EINER Stelle (17.08.2026).

DER ANLASS, Nutzerpruefung der Mailinhalte: dieselbe Mail schrieb

    Schwankung   2,3 % je Tag                     <- Faktenblock
    Kursentwicklung im selben Rahmen: 5 Tage -1.2 %   <- Lagebeschreibung

Zwei Schreibweisen in einem Text, sechs Zeilen auseinander. Das ist genau
der Fehler, der am 14.08. schon einmal teuer war: `_eur()` formatierte
"55,500.00 EUR", und in einer deutschen Mail liest sich das als
fuenfundfuenfzigeinhalb.

WARUM ES EIN EIGENES MODUL BRAUCHT. Es gab die Funktion schon - VIERMAL:

    faktenblock._de          Vorgabe 0 Stellen
    ausstiegsrechnung._de    Vorgabe 2 Stellen
    trefferbilanz._de        Vorgabe 1 Stelle
    signal_mail.eur          Vorgabe 0 Stellen

Vier Kopien derselben Zeile, die sich nur in der Vorgabe unterscheiden -
und drei Module, die gar keine hatten und deshalb englisch schrieben.
Dieses Projekt hat zweimal erlebt, was zwei Definitionen desselben
Begriffs anrichten (`KURSREIHENBLOECKE` gegen den Matrixtest: 67 % gegen
89 % fuer dieselbe Gruppe). Bei vieren war es nur eine Frage der Zeit.

⚠️ DER ORDNUNGSPUNKT DARF NICHT MITWANDERN. "im 84. Perzentil" ist kein
Dezimalpunkt, sondern eine Ordnungszahl. Ein naives Ersetzen macht daraus
"im 84, Perzentil" - und zerstoert nebenbei die Erkennung in
`pruefe_belege_gegen_fakten.py`, die auf `\\d+\\. Perzentil` steht.
Deshalb formatiert diese Funktion die ZAHL, statt Text zu ersetzen: sie
bekommt nie einen Satz zu sehen.
"""
from __future__ import annotations

# Punkt als Tausender, Komma als Dezimaltrenner - Pythons Vorgabe ist
# genau andersherum, deshalb der Tausch.
_TAUSCH = str.maketrans(",.", ".,")


def de(wert: float, stellen: int = 1, vorzeichen: bool = False) -> str:
    """Eine Zahl in deutscher Schreibweise.

    `vorzeichen=True` schreibt auch das Plus aus - gebraucht ueberall
    dort, wo eine Veraenderung steht und "1,2 %" nicht sagt, in welche
    Richtung.

    KEIN TEXT, NUR ZAHLEN. Wer einen fertigen Satz durchreicht, trifft
    auch Ordnungszahlen und Datumsangaben; genau daran ist die erste
    Fassung der Betragsformatierung gescheitert (Umbauplan 14: "die erste
    Fassung schickte die ganze Zeile durch translate")."""
    zahl = f"{float(wert):{'+' if vorzeichen else ''},.{stellen}f}"
    return zahl.translate(_TAUSCH)
