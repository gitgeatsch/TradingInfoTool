# -*- coding: utf-8 -*-
"""Haben wir die passende Datengrundlage? — und wo muss simuliert werden
(06.09.2026)

## Die Frage

Nutzervorgabe: *„pruefe auch fuer die weitere Arbeit, ob wir die passende
Datengrundlage haben. Sowie wann wir bestimmte Messungen sauber simulieren
muessen, wenn wir keine ausreichenden Daten haben."*

Und der Zusatz, der die Antwort erst brauchbar macht:

    *„auch die Simulation muss sauber aufgesetzt sein - in vielen Faellen
     haben wir historische Daten zur Verfuegung. Kunstdaten vs. Marktdaten."*

## ⚠️ Die bindende Grenze ist die BLOCKZAHL, nicht die Ankerzahl

    Block  = 3 x Horizont = 90 Kalendertage   (Methodik 2.95)
    Grenze = 20 Bloecke                        (darunter deckt das Band nicht:
                                                bei 5 Bloecken 19,5 % Fehlalarme)
    also     1.800 Kalendertage MIT Daten

Eine Messung mit 300.000 Ankern auf 800 Tagen ist untermaechtig; eine mit
15.000 Ankern auf 2.400 Tagen nicht.

## Zwei Gruende, warum etwas fehlt — und nur einer laesst sich simulieren

    LAGE fehlt    die Kursreihen sind da, nur die Signale nicht
                  -> aus MARKTDATEN rekonstruierbar
                  (hebel: 0 Signale · short: 0 · akkumulation: 0)

    DATEN fehlen  die Reihe selbst ist zu schmal oder zu kurz
                  -> nur mehr Daten helfen, Kunstdaten waeren Selbstbetrug
                  (turnover: 65 Symbole · Terminmarkt: 122 Tage)

    python pruefe_datengrundlage.py
"""
from __future__ import annotations

import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_bewertungskennzahl as MB                       # noqa: E402
import messe_eigenschaft_beitrag as B                       # noqa: E402
import messe_funding_niveau as F                            # noqa: E402
import messe_kandidaten_als_regel as K                      # noqa: E402
from messe_beitrag_auf_auswahl import momentum250           # noqa: E402
from messnorm_auswahl import datenlage, MENGEN              # noqa: E402

HORIZONT = 20


def main() -> int:
    print("Lade Reihen...", flush=True)
    reihen = B.lade()
    mom = momentum250(reihen)
    print("  %d Reihen · Momentum-Rang fuer %d Kalendertage"
          % (len(reihen), len(mom)), flush=True)

    print("  lade funding ...", flush=True)
    fu = F.lade_funding()
    print("  lade turnover ...", flush=True)
    tu = MB.reihe("data/onchain_historie.db", "splycur")
    print("  lade terminmarkt ...", flush=True)
    try:
        tm = K.lade_terminmarkt()
    except Exception:                                        # noqa: BLE001
        tm = {}

    arten = [("amihud", None), ("vola", None), ("schnitt50", None),
             ("funding", fu), ("turnover", tu)]
    if "oi_aenderung" in tm:
        arten.append(("oi_aenderung", tm["oi_aenderung"]))

    print()
    print("=" * 100)
    print("DIE DATENGRUNDLAGE JE KANDIDAT UND MENGE")
    print("=" * 100)
    print("  %-14s %-6s %6s %5s %9s %8s  %s"
          % ("Kandidat", "Menge", "Tage", "Blk", "Anker", "Symbole", "Urteil"))
    for art, quelle in arten:
        gebaut = K.baue(reihen, art, quelle, horizont=HORIZONT)
        for menge in ("frei", "20%", "10%", "5%"):
            d = datenlage(gebaut, mom, menge, horizont=HORIZONT)
            print("  %-14s %-6s %6d %5d %9d %8d  %s"
                  % (art, menge, d["tage"], d["bloecke"], d["anker"],
                     d["symbole"],
                     "✔ messbar" if d["messbar"] else d["weg"][:52]))
        print()

    print("=" * 100)
    print("WAS DARAUS FOLGT")
    print("=" * 100)
    print("  ✔ messbar        die Frage darf gestellt werden")
    print("  Tage fehlen      Menge weiten oder mehr Historie -")
    print("                   KUNSTDATEN helfen hier NICHT")
    print("  kein Tag uebrig  die Reihe ist zu schmal - eine DATENluecke")
    print()
    print("  ⚠️ Und getrennt davon die LAGEN ohne Signale (hebel, short,")
    print("     akkumulation): dort fehlen nicht die Daten, sondern die")
    print("     Situation. Sie ist aus den Kursreihen REKONSTRUIERBAR -")
    print("     das ist Simulation auf Marktdaten, nicht auf Kunstdaten.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
