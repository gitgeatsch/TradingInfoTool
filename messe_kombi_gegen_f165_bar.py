# -*- coding: utf-8 -*-
"""Erreicht die Kombination die Schwelle, an der F-165 scheiterte? (04.09.2026)

## Warum diese Datei nötig ist — die Korrektur einer eigenen Fehlannahme

Nach F-206 war der erste Reflex, eine neue Bewertungs-Instrument-Achse
("Wegwahl-Gate") zu entwerfen. Das ist bereits geklärt und geschlossen:
**F-163/F-164 zeigen arithmetisch, dass Hebel und Spot gebührenfrei
dieselbe Bewertungszahl liefern** — der EINZIGE legitime Hebel des
Instruments ist der HORIZONT (`Anforderungen_Umbau_28_08.md` 9.5). Es gibt
keinen zweiten Bewertungsweg zu bauen.

**F-165 hat genau diesen Horizont-Weg schon einmal gemessen** — sechs
Kursreihen-Kandidaten gegen dieselbe Zielgröße (Frontloading) — und den
Maßstab dafür gesetzt, wann ein Fund für eine Instrumentwahl AUSREICHT:

    „Die beste Regel verschiebt die Quote von 49 % auf 52 %. Das ist real,
    sauber belegt und zu klein, um eine Instrumentwahl darauf zu gründen…
    ein Schalter, der bei 52 statt 49 von hundert richtig liegt, ist keine
    Begründung im Sinne des übergeordneten Ziels."

Die einzelnen Terminmarkt-Kandidaten aus N-17b liegen in derselben
Größenordnung (`funding_extrem` allein: +1,0 Punkte, F-165). Die offene
Frage aus F-206 ist, ob die KOMBINATION (2,3x reiner als jede Einzelgröße)
diese Schwelle tatsächlich überschreitet — auf DERSELBEN Kennzahl, nicht
auf der anteilgewichteten Wirkung oder der Reinheit, die andere Fragen
beantworten.

## Was hier gerechnet wird

Exakt F-165s Tabelle ("gewählt / frontlastig % / Basis % / Unterschied"),
für die beiden bestätigten Kombinationen aus F-206 — über die ECHTE
Auswahlfunktion (`messe_kandidaten_kombination._auswahl_je_tag`), keine
Neuimplementierung der UND-Logik.

    python messe_kombi_gegen_f165_bar.py
"""
from __future__ import annotations

import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_eigenschaft_beitrag as B                          # noqa: E402
import messe_form_kurz_gegen_lang as FL                        # noqa: E402
import messe_kandidaten_kombination as K2                       # noqa: E402

# ⚠️ DIESELBE ERWARTUNG WIE F-165 (sqrt(KURZ)/(sqrt(KURZ)+sqrt(LANG-KURZ))) -
# eine geschlossene Formel, keine Messlogik. `FL.grundlage()` gibt sie
# selbst nicht zurueck (nur die Basisrate), deshalb hier einmalig benannt
# und gegen den in F-165 dokumentierten Wert 0,296 gegengeprueft.
ERW = float(np.sqrt(FL.KURZ) / (np.sqrt(FL.KURZ) + np.sqrt(FL.LANG - FL.KURZ)))
assert abs(ERW - 0.296) < 0.001, "ERW weicht von F-165s dokumentiertem Wert ab"


def punkte_tabelle(je_tag: dict) -> None:
    alle = [x for z in je_tag.values() for x in z
            if x.get("frontloading") is not None]
    fl_alle = np.array([x["frontloading"] for x in alle])
    basis = float((fl_alle > ERW).mean())
    print("  Basis (alle Anker mit Frontloading): %d, frontlastig %.1f %%"
          % (len(alle), 100 * basis))
    print()
    print("  %-32s %10s %12s %10s %12s" %
          ("Kandidat", "gewaehlt", "frontlastig", "Basis", "Unterschied"))
    for a, b, richtung in K2.KOMBINATIONEN:
        gewaehlt_werte = []
        for zeilen in je_tag.values():
            gewaehlt, d = K2._auswahl_je_tag(zeilen, a, b, richtung)
            if gewaehlt is None:
                continue
            gewaehlt_werte.extend(d[gewaehlt].tolist())
        if not gewaehlt_werte:
            print("  %-32s keine verwertbaren Anker" % f"{a}+{b}")
            continue
        w = np.array(gewaehlt_werte)
        frontlastig = float((w > ERW).mean())
        print("  %-32s %10d %11.1f%% %9.1f%% %+11.1f Pkt" %
              (f"{a}+{b}", len(w), 100 * frontlastig, 100 * basis,
               100 * (frontlastig - basis)))
    print()
    print("  ⚠️ ZUM VERGLEICH, F-165 (Einzelgroessen, dieselbe Tabelle):")
    print("     turnover        +3,2 Punkte   vola            +2,2 Punkte")
    print("     schnitt50       +2,1 Punkte   momentum_kurz   +1,8 Punkte")
    print("     funding_extrem  +1,0 Punkte   -> dort als 'zu klein fuer")
    print("     eine Instrumentwahl' beurteilt (49 -> 52 von 100).")


def einzel_punkte_tabelle(je_tag: dict, basis: float, kandidaten) -> None:
    """Dieselbe Tabelle wie `punkte_tabelle`, aber fuer EINZELNE Kandidaten -
    auf der AKTUELLEN, F-204-bereinigten Basis nachgemessen statt F-165s
    Originalzahlen (vor N-19/F-204) blind uebernommen. Die Auswahl folgt
    EXAKT derselben Regel wie `FL.wahl_je_tag` (Top-ANTEIL je Tag, oberstes
    Fuenftel der Kennzahl) - hier nur auf rohe Frontloading-Werte statt auf
    den Tagesmittelwert angewandt, weil `wahl_je_tag` selbst keinen
    Rohwerte-Ruecksprung anbietet."""
    print()
    print("  ZUM VERGLEICH — F-165s EINZELKANDIDATEN, HEUTE NACHGEMESSEN")
    print("  (F-165 lief vor N-19/F-204 - moeglich kontaminierte Basis;")
    print("   hier auf denselben 516 sauberen Krypto-Symbolen wie oben)")
    print("  %-32s %10s %12s %10s %12s" %
          ("Kandidat", "gewaehlt", "frontlastig", "Basis", "Unterschied"))
    for kandidat in kandidaten:
        gewaehlt_werte = []
        for z in je_tag.values():
            zeilen = [x for x in z if kandidat in x
                      and x.get(kandidat) is not None
                      and x.get("frontloading") is not None]
            if len(zeilen) < FL.MIN_JE_TAG:
                continue
            kz = np.array([float(x[kandidat]) for x in zeilen])
            fl = np.array([x["frontloading"] for x in zeilen])
            k = max(1, int(round(len(zeilen) * FL.ANTEIL)))
            idx = np.argsort(-kz)[:k]
            gewaehlt_werte.extend(fl[idx].tolist())
        if not gewaehlt_werte:
            continue
        w = np.array(gewaehlt_werte)
        frontlastig = float((w > ERW).mean())
        print("  %-32s %10d %11.1f%% %9.1f%% %+11.1f Pkt" %
              (kandidat, len(w), 100 * frontlastig, 100 * basis,
               100 * (frontlastig - basis)))


def main():
    reihen = B.lade()
    zusatz = FL.lade_zusatz()
    je_tag = FL.baue(reihen, zusatz)
    print("%d Kalendertage, ERW=%.3f (Zufallspfad-Erwartung)"
          % (len(je_tag), ERW))
    punkte_tabelle(je_tag)
    alle = [x for z in je_tag.values() for x in z
            if x.get("frontloading") is not None]
    basis = float((np.array([x["frontloading"] for x in alle]) > ERW).mean())
    einzel_punkte_tabelle(je_tag, basis,
                          ("turnover", "vola", "schnitt50", "momentum_kurz",
                           "funding_extrem", "zufall"))


if __name__ == "__main__":
    sys.exit(main() or 0)
