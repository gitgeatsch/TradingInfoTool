# -*- coding: utf-8 -*-
"""DEN STANDKOPF SETZEN — welche Dokumente sahen den Umbau nicht?

## ⚠️⚠️⚠️ Nutzervorgabe 10./11.09.2026, zweimal

> *„du musst sauber trennen nach vor und nach dem aktuellen Umbau - das
> gilt fuer Messungen, Dokumente und Code!!!"*
>
> *„alten Code, Messungen und Doku von neuem Umbau trennen damit nichts
> vermischt wird."*

Fuer **Code** gibt es die Trennung (`REGISTER_Werkzeuge`, nach
Methodikstand), fuer **Messungen** auch (`Befundlage.basis` und
`bestand.umbauseite`). Fuer **Dokumente** war sie nur eine Zaehlung in
`soll_ist.umbaugrenze()` — im Dokument selbst stand nichts.

**Das ist die gefaehrlichste der drei Luecken**, denn ein Dokument wird
geoeffnet und gelesen, nicht abgefragt. 29 von 48 Vor-Umbau-Dokumenten
tragen Messwerte, die wie aktuelle aussehen.

## ⚠️⚠️ DIE FALLE, die dieses Werkzeug umgeht

`umbaugrenze()` klassifiziert Dokumente nach dem **Aenderungsdatum**.
Einen Kopf zu setzen **aendert genau dieses Datum** — danach saehen alle
29 wie Nach-Umbau-Dokumente aus, und die Trennung waere zerstoert.

Deshalb traegt der Kopf das **urspruengliche** Datum maschinenlesbar
mit:

    <!-- STAND: 2026-08-30 · VOR dem Messstandard vom 2026-09-09 -->

`soll_ist.umbaugrenze()` liest diese Zeile und zieht sie dem
Dateidatum vor.

## Was der Kopf sagt — und was NICHT

Er ist **kein Sperrvermerk**. Ein altes Ergebnis kann richtig sein. Er
sagt: es ist unter anderen Regeln entstanden, gehoert vor einem Widerruf
reproduziert (R-R11), und ist nicht als aktueller Stand zu zitieren.

⚠️ Das Werkzeug ist **wiederholbar**: ein vorhandener Kopf wird erkannt
und nicht verdoppelt. Erzeugte Register bekommen keinen Kopf — sie
werden aus `bestand.py` neu geschrieben.

    python markiere_dokumente.py --zeigen    nur auflisten
    python markiere_dokumente.py             setzen
"""
from __future__ import annotations

import glob
import io
import os
import re
import sys
import time

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

GRENZE = "2026-09-09"          # messnorm.MESSSTANDARD_AB
MARKE = re.compile(r"^<!-- STAND: (\d{4}-\d{2}-\d{2}) ", re.M)
# ⚠️ Erzeugte Blaetter bekommen keinen Kopf - `bestand.py` schreibt sie neu.
ERZEUGT = ("REGISTER_Kandidaten.md", "REGISTER_Befunde.md",
           "REGISTER_Werkzeuge.md", "REGISTER_Methodik_Themen.md",
           "REGISTER_Fakten.md")
# Zaehlt Messwerte: R-Zahlen, Baender, Trage-Urteile.
MESSWERT = re.compile(r"[+−-]0,0\d{2,}|\[\s*[+−-]?0,\d+\s*\.\.|"
                      r"tr[aä]e?gt nicht|R \[")


def kopf(datum: str, messwerte: int) -> str:
    """⚠️ ZWEI STUFEN, und die Abstufung ist Absicht.

    Ein sichtbarer Warnblock auf der `Tailscale-Setup-Anleitung` waere
    Laerm - der Messstandard beruehrt sie nicht. Ein Dokument OHNE
    Messwerte bekommt deshalb nur die maschinenlesbare Zeile: die
    Einstufung bleibt erhalten, die Seite bleibt lesbar.

    > **Wer ueberall warnt, warnt nirgends.**
    """
    if messwerte == 0:
        return ("<!-- STAND: %s · VOR dem Messstandard vom %s · "
                "keine Messwerte, deshalb ohne sichtbaren Kopf -->\n"
                % (datum, GRENZE))
    stark = messwerte >= 20
    return (
        "<!-- STAND: %s · VOR dem Messstandard vom %s -->\n"
        "\n"
        "> %s **DIESES DOKUMENT SAH DEN UMBAU NICHT.** Zuletzt geaendert\n"
        "> **%s**; der Messstandard gilt ab **%s**.\n"
        ">\n"
        "> Seine Messwerte sind unter **anderen Regeln** entstanden:\n"
        "> anderer Nullpunkt (Maximum ueber fuenf Ziehungen statt\n"
        "> 90. Perzentil ueber 40), andere Trennschaerfe (gegen null statt\n"
        "> gegen den Nullpunkt), kuerzere Leiter (bis 0,10 statt 0,40).\n"
        ">\n"
        "> **Kein Sperrvermerk** — ein altes Ergebnis kann richtig sein. Es\n"
        "> heisst: vor einem Widerruf **reproduzieren** (R-R11), und nicht\n"
        "> als aktuellen Stand zitieren. Was gilt, steht in\n"
        "> `REGISTER_Befunde.md`.\n"
        "%s"
        "\n---\n\n"
        % (datum, GRENZE,
           "⚠️⚠️" if stark else "⚠️",
           datum, GRENZE,
           (">\n> ⚠️⚠️ **%d Messwerte** in diesem Dokument — hier ist die\n"
            "> Verwechslungsgefahr am groessten.\n" % messwerte)
           if stark else ""))


def stand(pfad: str) -> tuple:
    """(Datum, aus_dem_Kopf?) — der Kopf schlaegt das Dateidatum."""
    try:
        t = io.open(pfad, encoding="utf-8", errors="replace").read(4096)
    except OSError:
        t = ""
    m = MARKE.search(t)
    if m:
        return (m.group(1), True)
    try:
        return (time.strftime("%Y-%m-%d",
                              time.localtime(os.stat(pfad).st_mtime)), False)
    except OSError:
        return ("?", False)


def main() -> int:
    nur = "--zeigen" in sys.argv
    print("=" * 92)
    print("DER STANDKOPF — welche Dokumente sahen den Umbau nicht?")
    print("=" * 92)
    print("  Grenze: der Messstandard vom %s" % GRENZE)
    print("  ⚠️ Der Kopf traegt das URSPRUENGLICHE Datum mit - sonst")
    print("     zerstoert das Setzen die Klassifikation, die es "
          "herstellen soll.")
    print()
    gesetzt = vorhanden = neu = 0
    print("  %-50s %-11s %6s  %s"
          % ("Dokument", "Stand", "Messw.", "Kopf"))
    for pfad in sorted(glob.glob("Basisinfos/*.md")):
        name = os.path.basename(pfad)
        if name in ERZEUGT:
            continue
        datum, aus_kopf = stand(pfad)
        if datum >= GRENZE and not aus_kopf:
            continue                       # nach dem Umbau - kein Kopf
        t = io.open(pfad, encoding="utf-8", errors="replace").read()
        n = len(MESSWERT.findall(t))
        if aus_kopf:
            vorhanden += 1
            print("  %-50s %-11s %6d  ✔ vorhanden" % (name[:50], datum, n))
            continue
        neu += 1
        if nur:
            print("  %-50s %-11s %6d  → zu setzen" % (name[:50], datum, n))
            continue
        io.open(pfad, "w", encoding="utf-8").write(kopf(datum, n) + t)
        gesetzt += 1
        print("  %-50s %-11s %6d  ✔ GESETZT" % (name[:50], datum, n))
    print()
    print("  %d vorhanden · %d %s"
          % (vorhanden, neu, "zu setzen" if nur else "gesetzt"))
    if not nur and gesetzt:
        print()
        print("  ⚠️ Das Aenderungsdatum dieser Dateien ist jetzt HEUTE -")
        print("     die Einstufung kommt ab sofort aus dem Kopf, nicht "
              "aus der Datei.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
