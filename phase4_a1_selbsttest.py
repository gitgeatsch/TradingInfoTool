# -*- coding: utf-8 -*-
"""Phase 4, A1 / E2-E4: DIE FEHLALARMQUOTE AUF `barriere` (20.09.2026)

⚠️⚠️ DAS IST DIE ENTSCHEIDENDE MESSUNG ZU A1. Befund 2.238 sagt, das Band
sei auf binaeren Daten VIERMAL ZU ENG - und deshalb trage dort sogar
`zufall`. Die Loesung steht seit dem 09.09. benannt da (2.238-klasse):
Fehlalarmquote der Barrieren-Anlage auf Nullwelten, genau das Verfahren,
das damals den Nullbezug entschieden hat.

## ⚠️ WARUM KEINE FORMEL DAS ENTSCHEIDET

Am 20.09. wurde es zweimal versucht (`phase4_a1_block.py`, R-R11-Block):

    sigma / Wurzel(BLOECKE)   ->  Faktor 3,2 bis 10,5   "viermal zu eng"
    sigma / Wurzel(TAGE)      ->  Faktor 0,42 bis 1,35  "passt"

Zwei Formeln, zwei Ergebnisse. Welche stimmt, haengt daran, wie stark die
Tage voneinander abhaengen - und genau das soll die Anlage ja selbst
beruecksichtigen. ⚠️ Eine Anlage mit einer Formel zu pruefen, die
dieselbe Annahme macht wie die Anlage, ist keine Pruefung.

➔ DIE FEHLALARMQUOTE IST DIE ANTWORT. Sie setzt keine Formel voraus: man
baut Welten OHNE Effekt und zaehlt, wie oft die Anlage TRAEGT sagt.

## Der Sollwert steht VOR dem Lauf fest

`band()` bildet die Perzentile 5 und 95, also ein 90-%-Band; einseitig
sind das 5 %. `Befund.traegt` verlangt zusaetzlich `unten > null_oben`
und ist damit STRENGER. Der Selbsttest vom 08.09. hat fuer `bewegung_r`
0 von 50 Fehlalarmen gefunden.

    deutlich UEBER 5 %   die Anlage ist unzuverlaessig - 2.238 bestaetigt
    weit UNTER 5 %       sie ist uebervorsichtig
    dazwischen           sie haelt, was sie verspricht

⚠️ BEIDE AUSGAENGE SIND BEFUNDE.

## ⚠️ Der Vergleichsarm ist Pflicht

Gemessen wird `barriere` UND `bewegung_r` auf DENSELBEN Welten. Ohne den
zweiten Arm waere eine hohe Quote nicht der Zielgroesse zuzuordnen -
sie koennte auch am Pruefstand liegen.

⚠️ 100 Ziehungen statt der 50 vom 08.09.: bei 50 ist die Aufloesung
±3 Prozentpunkte, bei 100 sind es ±2. Fuer "viermal zu eng" reicht
weniger, fuer eine Feinjustierung nicht.

⚠️ `ueberlappung=HORIZONT` ist PFLICHT (selbsttest_welt): ohne sie hat
die Welt rund H mal zu viele unabhaengige Beobachtungen und bescheinigt
der Anlage eine Praezision, die sie nicht hat.

## ⚠️ LIMITS UND DAUER - NACHGEMESSEN, NICHT GESCHAETZT

⚠️ Die stehende Vorgabe verlangt beides VOR dem Lauf. Am 20.09. wurde sie
erst nachgeholt, als der Nutzer schon wartete. Deshalb steht sie jetzt
hier - und im DOCSTRING, nicht in einem Kommentar: `_quelltext` filtert
Kommentarzeilen, und eine Pruefung haette die Angabe dort nie gesehen
(dieselbe Falle wie 2.470-drei-eigene-fehler).

    bewegung_r   22,2 s je Ziehung   ->  100 Ziehungen = 0,6 h
    barriere     19,5 s je Ziehung   ->  100 Ziehungen = 0,5 h
    ------------------------------------------------------------
    gesamt                                              rund 1,1 h

⚠️ WOHER DIE KOSTEN KOMMEN: je Ziehung baut `welt()` 1.500 Tage mit 150
Symbolen, und `pruefe_auswahl` rechnet darauf 40 Nullwelten plus 5
Ziehungen Positivkontrolle - jede mit einem Blockbootstrap ueber 2.000
Wiederholungen (Normvorgabe). Das sind rund 46 Baender je Ziehung.

⚠️⚠️ WER DIE ZIEHUNGSZAHL AENDERT, AENDERT DIE LAUFZEIT LINEAR - und wer
sie unter 50 senkt, verliert die Aufloesung: bei 50 sind es ±3
Prozentpunkte, bei 100 noch ±2. Fuer die Frage "ueber oder unter 5 %" ist
das der Unterschied zwischen Antwort und Vermutung.

Nur lesend, kein LLM, keine Datenbank.
"""
from __future__ import annotations

import sys
import time

import numpy as np

import messnorm as N
import messnorm_auswahl as MA
import selbsttest_welt as SW

HORIZONT = 20
ZIEHUNGEN = 100
MENGE = "20%"
# ⚠️ EINE Staerke fuer die Quotenlaeufe - die Positivkontrolle kostet je
# Staerke fuenf Ziehungen und wird fuer `traegt` nicht gebraucht.
SPAR_LEITER = (0.02,)
CRV = 2.0

# (Name, Lage, Zielgroesse, binaer)
ARME = (
    ("bewegung_r (stetig, Vergleichsarm)",
     N.Lage(instrument="spot", strategie="einstieg"), "bewegung_r", False),
    ("barriere (binaer, die Frage)",
     N.Lage(instrument="hebel", strategie="einstieg", simuliert=True),
     "barriere", True),
)


def einmal(rng, lage, zielgroesse, binaer, staerke=0.0):
    """Eine Welt bauen und mit der ECHTEN Norm messen."""
    je, mom = SW.welt(rng, staerke=staerke, ueberlappung=HORIZONT,
                      binaer=binaer, crv=CRV)
    return MA.pruefe_auswahl(
        "a1_selbsttest", je, mom, lage=lage, menge=MENGE,
        rng=np.random.default_rng(int(rng.integers(1, 10 ** 9))),
        horizont=HORIZONT, staerken=SPAR_LEITER,
        zielgroesse=zielgroesse,
        hypothese="Selbsttest gegen bekannte Wahrheit - es gibt KEINEN "
                  "Effekt, jedes TRAEGT ist ein Fehlalarm",
        verwendung="Eichung der Messanlage (A1)")


def quote(treffer: int, n: int) -> str:
    """Quote MIT Standardfehler - die Ziehungszahl gehoert in die Ausgabe."""
    p = treffer / max(1, n)
    se = (p * (1.0 - p) / max(1, n)) ** 0.5
    return "%3d/%3d = %5.1f %% (± %.1f pp)" % (treffer, n, 100 * p, 100 * se)


def main() -> int:
    t0 = time.time()
    print("=" * 112)
    print("PHASE 4 · A1 / E2 - DIE FEHLALARMQUOTE AUF `barriere`")
    print("=" * 112)
    print("  " + N.standardzeile().replace("\n", "\n  "))
    print("  %d Nullwelten je Arm · Horizont H%d · Menge %s · "
          "Ueberlappung %d · CRV %.1f"
          % (ZIEHUNGEN, HORIZONT, MENGE, HORIZONT, CRV))
    print("  ⚠️ SOLLWERT VORAB: einseitig 5 %% (Band 5./95. Perzentil); "
          "`traegt` ist strenger")
    print("  ⚠️ Der Vergleichsarm ist Pflicht - ohne ihn waere eine hohe "
          "Quote nicht der")
    print("     Zielgroesse zuzuordnen, sondern koennte am Pruefstand "
          "liegen.")

    ergebnis = {}
    for name, lage, ziel, binaer in ARME:
        t1 = time.time()
        rng = np.random.default_rng(N.SAAT)
        treffer, gemessen, bandbreiten = 0, 0, []
        for i in range(ZIEHUNGEN):
            try:
                b = einmal(rng, lage, ziel, binaer)
            except ValueError as x:
                print("     ⚠️ von der Norm zurueckgewiesen: %s" % x)
                break
            gemessen += 1
            if getattr(b, "traegt", False):
                treffer += 1
            bandbreiten.append(float(b.oben - b.unten))
        if not gemessen:
            continue
        ergebnis[name] = (treffer, gemessen)
        print("\n  %s" % ("-" * 108))
        print("  ARM: %s" % name)
        print("     Zielgroesse %-12s Statistik %s"
              % (ziel, N.ZIELGROESSEN[ziel]["statistik"]))
        print("     FEHLALARME  %s" % quote(treffer, gemessen))
        print("     Bandbreite  Mittel %.5f · Median %.5f"
              % (float(np.mean(bandbreiten)), float(np.median(bandbreiten))))
        p = treffer / max(1, gemessen)
        print("     ➔ %s"
              % ("⚠️⚠️ UNZUVERLAESSIG - deutlich ueber 5 %, 2.238 bestaetigt"
                 if p > 0.10 else
                 "⚠️ erhoeht - ueber dem Sollwert, aber nicht dramatisch"
                 if p > 0.05 else
                 "✔ HAELT, WAS SIE VERSPRICHT"
                 if p >= 0.01 else
                 "✔ uebervorsichtig - unter dem Sollwert"))
        print("     (%.0f s)" % (time.time() - t1))

    print("\n  %s" % ("=" * 108))
    print("  DAS URTEIL ZU A1")
    if len(ergebnis) == 2:
        (n1, (t1_, g1)), (n2, (t2_, g2)) = list(ergebnis.items())
        p1, p2 = t1_ / max(1, g1), t2_ / max(1, g2)
        print("     %-38s %s" % (n1.split(" (")[0], quote(t1_, g1)))
        print("     %-38s %s" % (n2.split(" (")[0], quote(t2_, g2)))
        if p2 > 0.10 and p1 <= 0.05:
            print("     ➔ ⚠️⚠️ 2.238 IST BESTAETIGT: die Anlage ist auf der "
                  "BINAEREN Zielgroesse")
            print("        unzuverlaessig, auf der stetigen nicht. A1 bleibt "
                  "offen und braucht")
            print("        eine Korrektur der EICHUNG.")
        elif p2 <= 0.05 and p1 <= 0.05:
            print("     ➔ ✔✔ 2.238 IST WIDERLEGT: die Anlage haelt ihren "
                  "Sollwert auf BEIDEN")
            print("        Zielgroessen. Das Band ist nicht zu eng - die "
                  "Rechnung dahinter war")
            print("        es. ⚠️ Damit faellt A1, und der Hebel ist messbar.")
        else:
            print("     ➔ ⚠️ gemischtes Bild - beide Arme gehoeren einzeln "
                  "gelesen, und die")
            print("        Ursache ist NICHT die Zielgroesse allein.")
    print("\n  ⚠️ Kunstwelt mit bekannter Wahrheit - sie prueft die ANLAGE, "
          "nicht die DATEN.")
    print("  (%.0f s)" % (time.time() - t0))
    print("=" * 112)
    return 0


if __name__ == "__main__":
    sys.exit(main())
