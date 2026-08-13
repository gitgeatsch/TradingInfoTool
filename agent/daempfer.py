# -*- coding: utf-8 -*-
"""Welche Positionsgroessen-Daempfer noch wirken - und welche nur noch zaehlen.

NUTZERVORSCHLAG 13.08.: *"ich wuerde u.U. sogar andenken die vorhandenen
Daempfer vorerst sauber stillzulegen"*.

MEINE ERSTE ANTWORT WAR ZU PAUSCHAL, und die Korrektur steht im Code selbst.
`risk_gate.py` dokumentiert eine Messung an **298 Spot-Signalen** zur
stufenlosen CRV-Abstufung:

    SQN         +0,63  ->  +1,36
    Summe       +9,8 R ->  +23,1 R
    Rueckschlag  36,3 R ->  27,1 R

Besseres Ergebnis bei KLEINEREM Risiko. Dieser Daempfer ist gemessen und er
wirkt - ihn stillzulegen hiesse, eine belegte Verbesserung wegzuwerfen.

DIE REGEL, DIE DARAUS FOLGT:

    Stillgelegt wird NUR, was auf einer Groesse beruht, die wir als wertlos
    GEMESSEN haben. Alles andere bleibt wirksam und wird gezaehlt.

Das trifft heute genau zwei:

    Konfidenz-Skalierung        Die Konfidenz haengt mit dem Ergebnis nicht
                                zusammen (r = +0,073, n = 92) und ist faktisch
                                konstant. Ein Daempfer auf einer konstanten
                                Groesse daempft immer gleich - er ist ein
                                verkleideter Pauschalabschlag.
    Regime-Richtungs-Konflikt   Das Regime war ueber 1.022 Faelle konstant
                                "baer". Ein Konflikt mit einer Konstanten ist
                                keine Information ueber den Markt, sondern eine
                                ueber die Richtung des Signals.

WAS BEWUSST WIRKSAM BLEIBT, obwohl ungemessen: Gegenszenario, technischer
Konflikt, Retail-Konsens, AZ-7-Kontra. Sie verkleinern nur - eine
Ueberexposition koennen sie nicht erzeugen - und sie abzuschalten waere eine
Verhaltensaenderung an einer LAUFENDEN Kette, die Aktien, Rohstoffe, Themen-ETF
und Hedge bedient. Sie bekommen einen Zaehler, damit in einigen Wochen
entschieden werden kann statt behauptet.

DER ZAEHLER SCHREIBT IN VORHANDENE SPALTEN. `hebel_signals.
eigenkapital_deckel_hinweis` und `hebel_korrektur_hinweis` existieren und sind
in ALLEN Zeilen leer - der Platz war da und wurde nie benutzt. (Meine erste
Fassung dieses Befunds sagte "wird nirgends aufgezeichnet"; richtig ist "der
Platz ist da und leer".)
"""
from __future__ import annotations

# Der Schluessel ist der ANFANG des Grundtextes, wie ihn die Gates bauen. Eine
# Pruefung stellt sicher, dass jeder Name dort auch woertlich vorkommt - sonst
# waere eine Umbenennung im Gate eine stille Wiederaktivierung.
STILLGELEGT: dict[str, str] = {
    "Konfidenz-Skalierung":
        "Konfidenz haengt mit dem Ergebnis nicht zusammen (r = +0,073, n = 92)",
    "Regime-Richtungs-Konflikt":
        "Regime war ueber 1.022 Faelle konstant 'baer'",
}


def ist_stillgelegt(grund: str) -> bool:
    """Wirkt dieser Daempfer noch? Vergleich ueber den Anfang des Grundtextes."""
    text = str(grund or "")
    return any(text.startswith(name) for name in STILLGELEGT)


def teile(kandidaten: list) -> tuple[list, list]:
    """Zerlegt die Deckel-Kandidaten in wirksame und nur gezaehlte.

    GIBT BEIDE ZURUECK, nie nur die wirksamen. Ein Daempfer, der ohne Spur
    verschwindet, ist genau der unsichtbare Filter, gegen den dieses Projekt
    sonst argumentiert - nur diesmal in die andere Richtung."""
    wirksam = [k for k in (kandidaten or []) if not ist_stillgelegt(k[0])]
    gezaehlt = [k for k in (kandidaten or []) if ist_stillgelegt(k[0])]
    return wirksam, gezaehlt


def vermerk(bindender_grund: str | None, alle_kandidaten: list,
            gezaehlt: list) -> str | None:
    """Eine Zeile fuer die Datenbank: was gegriffen hat und was gegriffen haette.

    KOMPAKT UND MASCHINENLESBAR GENUG. Der Vermerk landet in einer Textspalte;
    eine spaetere Auswertung soll ihn zerlegen koennen, ohne ihn zu raten -
    deshalb feste Trennzeichen statt Fliesstext."""
    teile_: list[str] = []
    if bindender_grund:
        teile_.append(f"bindend={bindender_grund}")
    haetten = [g for g, _ in gezaehlt]
    if haetten:
        teile_.append("stillgelegt_haetten_gegriffen=" + "; ".join(haetten))
    weitere = [g for g, _ in (alle_kandidaten or [])
               if g != bindender_grund and not ist_stillgelegt(g)]
    if weitere:
        teile_.append("weitere_kandidaten=" + "; ".join(weitere))
    return " | ".join(teile_) or None
