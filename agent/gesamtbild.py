# -*- coding: utf-8 -*-
"""Die Zusammenfuehrung (Umbauplan 93 E, 20.08.2026)

⚠️ FALLSTRICK E1 IST DER WICHTIGSTE DES GANZEN KAPITELS, und er lautet:

    Jede Stufe kann zur Bremse werden, wenn sie zur BEDINGUNG wird. Kein
    Kriterium darf ein Urteil verhindern. Es darf nur bestimmen, welcher Art
    das Urteil ist.

Deshalb ist dieses Modul KEINE Note und KEIN Filter. Es rechnet nichts neu,
es entscheidet nichts, und es kann keinen Einstieg verhindern.

DER TRICK: ES LIEST DIE MAIL, DIE OHNEHIN ENTSTEHT.

Alle vier Stufen setzen bereits ein Etikett - "GUENSTIG", "UNGUENSTIG",
"NOCH KEINE BEWERTUNG MOEGLICH". Dieses Modul zaehlt sie und stellt das
Ergebnis nach vorn. Es gibt also KEINE zweite Rechnung, die von der ersten
abweichen koennte - der Fehler, der dieses Projekt am 18.08. zwei Vormittage
gekostet hat (vier Kopien derselben Stopzeile).

    Vier Merkmale: 1 spricht dafuer, 1 dagegen, 2 noch nicht bewertbar.

⚠️ "NOCH NICHT BEWERTBAR" IST DIE HAEUFIGSTE ANTWORT, und das ist ehrlich.
Die Lebendigkeitsreihe ist erst ab Ende September auswertbar, der Rangplatz
hat gemessen keinen handelbaren Vorteil. Wer daraus eine Note baute, bekaeme
eine Zahl, die Sicherheit vortaeuscht, wo keine ist.

WAS DAS FUER DEN LESER TUT. Die Mail hat sechs Abschnitte und ist lang. Diese
drei Zeilen stehen ganz oben und sagen, wie viel Boden unter der Empfehlung
ist - bevor er die erste Zahl liest.
"""
from __future__ import annotations

# Die Etiketten, die die vier Stufen setzen. Sie stehen hier NICHT als Kopie,
# sondern als das, wonach gesucht wird - wer eines umbenennt, muss hier
# nachziehen, und eine Paketpruefung haelt das fest.
DAFUER = "GUENSTIG"
DAGEGEN = "UNGUENSTIG"
UNBEKANNT = ("NOCH KEINE BEWERTUNG MOEGLICH", "KEIN HANDELBARER VORTEIL",
             "KEINE eigene Messung")

# Die vier Merkmale und die Zeile, an der man sie erkennt. Reihenfolge wie im
# Plan: Trichter (immer), Drift (gemessen), Lebendigkeit (Merkmal), Anlass.
MERKMALE = (
    ("Schwankungsbreite und Stop", "Uebliche Kursbewegung"),
    ("Rangplatz in der Anlageklasse", "Rangplatz nach"),
    ("Lebendigkeit des Projekts", "Lebendigkeit des Projekts"),
    ("Bekannte Termine", "Bekannte Termine"),
)


def _urteil(zeilen: list[str], anfang: str) -> str | None:
    """dafuer / dagegen / unbekannt - oder None, wenn es den Block nicht gibt.

    ⚠️ NUR DIE ZEILEN DIESES BLOCKS. Ein "UNGUENSTIG" aus dem Trichter darf
    nicht dem Terminblock zugerechnet werden; die Bloecke sind durch
    Leerzeilen getrennt und beginnen mit ihrer Ueberschrift."""
    gefunden, block = False, []
    for z in zeilen:
        if z.startswith(anfang):
            gefunden, block = True, []
            continue
        if gefunden:
            if not z.strip():
                break
            block.append(z)
    if not gefunden:
        return None
    text = "\n".join(block)
    if DAGEGEN in text:
        return "dagegen"
    if any(w in text for w in UNBEKANNT):
        return "unbekannt"
    if DAFUER in text:
        return "dafuer"
    return "unbekannt"


def bewerte(zeilen: list[str]) -> dict:
    """Was sagen die vier Merkmale? ZAEHLT NUR, RECHNET NICHT."""
    je = {}
    for name, anfang in MERKMALE:
        u = _urteil(list(zeilen or []), anfang)
        if u is not None:
            je[name] = u
    return {"je_merkmal": je,
            "dafuer": sum(1 for v in je.values() if v == "dafuer"),
            "dagegen": sum(1 for v in je.values() if v == "dagegen"),
            "unbekannt": sum(1 for v in je.values() if v == "unbekannt"),
            "vorhanden": len(je)}


def saetze(zeilen: list[str]) -> list[str]:
    """Die drei Zeilen fuer den Kopf der Mail.

    ⚠️ SIE SPERREN NICHTS. Auch "3 dagegen, 0 dafuer" ist kein Veto - es ist
    eine Zusammenfassung dessen, was weiter unten ohnehin steht."""
    from agent.schreibweise import de

    b = bewerte(zeilen)
    if not b["vorhanden"]:
        return []
    teile = []
    if b["dafuer"]:
        teile.append(f"{de(b['dafuer'], 0)} spricht dafuer")
    if b["dagegen"]:
        teile.append(f"{de(b['dagegen'], 0)} dagegen")
    if b["unbekannt"]:
        teile.append(f"{de(b['unbekannt'], 0)} noch nicht bewertbar")
    aus = [f"Auf einen Blick: von {de(b['vorhanden'], 0)} pruefbaren "
           f"Merkmalen " + ", ".join(teile) + "."]
    # ⚠️ WAS DAGEGEN SPRICHT, GEHOERT AN DEN ANFANG DER ZEILE - sonst liest
    # es niemand. Und es ist eine Warnung, keine Sperre.
    dagegen = [n for n, v in b["je_merkmal"].items() if v == "dagegen"]
    if dagegen:
        aus.append("⚠️ Dagegen spricht: " + ", ".join(dagegen)
                   + ". Das ist ein Hinweis, keine Sperre - die Einzelheiten "
                     "stehen unten.")
    aus.append("   Diese Zeile fasst nur zusammen, was weiter unten steht. "
               "Sie verhindert keine Empfehlung und ersetzt keine.")
    return aus
