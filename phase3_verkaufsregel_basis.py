# -*- coding: utf-8 -*-
"""V3b-1 / B1 + B2: SCHLIESST EINE BREITERE BASIS DAS BAND? (19.09.2026)

⚠️⚠️ WORUM ES GEHT - UM 0,0019 R.

2.476-verkaufsregel hat `funding` als Verkaufsregel gemessen. Auf der
EIGENTLICHEN Haltefrage (gehalten, heute nicht mehr in der Auswahl) kam
+0,0178 R mit Band [-0,0800 .. +0,0734] gegen eine Nullwelt von -0,0781
(obere Grenze) heraus: NICHT TRENNBAR. Die Wirkung war mit +0,1382 weit
UEBER der Trennschaerfe von 0,02 R - dem Band fehlten 0,0019, um den
Nullpunkt auszuschliessen.

Das ist kein Nullbefund, sondern fehlende Deckung. Zwei Wege koennen sie
liefern, und beide werden hier gemessen statt behauptet:

    B1   HORIZONT H5 statt H20   ->  Block 15 statt 60, rund viermal so
                                     viele Bloecke. ⚠️ H5 ist eine ANDERE
                                     FRAGE (5 Tage statt 20), kein Ersatz.
    B2   HALTEFENSTER 120 statt 60 ->  mehr Werte je Tag in der Teilmenge.
                                     ⚠️ Der Stellvertreter entfernt sich
                                     damit weiter vom echten Bestand.

## ⚠️ R-R11: DIE BASIS WIRD ZUERST REPRODUZIERT

Die erste Zeile jeder Tabelle ist die Lage aus 2.476 (H20, Fenster 60).
Wer die Basis aendert und ein anderes Ergebnis bekommt, hat nichts
widerlegt - er hat etwas anderes gemessen. Weicht die Reproduktion ab,
ist der Lauf ungueltig, nicht der Befund.

## ⚠️ WAS HIER NICHT ENTSCHIEDEN WIRD

Ob V3b-2 auf B1, B2 oder auf der ganzen Haltemenge mit Vorbehalt gebaut
wird, ist eine Nutzerentscheidung. Dieses Modul liefert die Zahlen dazu.

⚠️ Stellvertretermenge (N3 b), nur lesend, kein LLM.
"""
from __future__ import annotations

import sys
import time

import numpy as np

import messnorm
import messmenge
import phase3_reproduktion as R
from messe_beitrag_auf_auswahl import momentum250
from n64_schnitt_stufen import band
from phase3_haltefrage import geteilt, haltemenge
from phase3_verkaufsregel import (KANDIDAT, NULL_ZIEHUNGEN, VORBEHALT,
                                  besetzung, blockpruefung, regel, urteil)

# (Name, Horizont, Haltefenster, Mindestbesetzung der verkauften Seite)
#
# ⚠️⚠️ B3 IST WAEHREND DES LAUFS DAZUGEKOMMEN, und zwar nicht als Idee,
# sondern als Pflicht: die Nullwelt lag in JEDER Variante deutlich im
# Minus (-0,0396 bis -0,1204) statt bei null. Das ist die dokumentierte
# Verzerrung aus der stehenden Vorgabe vom 07.09. - `median(Gruppe) minus
# median(Rest)` bei UNGLEICH grossen Gruppen. Die verkaufte Seite ist das
# oberste Fuenftel, also viermal kleiner. Die erste Fassung liess Tage mit
# einem EINZIGEN verkauften Wert zu; die Vorgabe nennt zwei Anker je Gruppe
# als Untergrenze.
VARIANTEN = (
    ("BASIS  H20 · Fenster 60  · min 1", 20, 60, 1),
    ("B1     H5  · Fenster 60  · min 1", 5, 60, 1),
    ("B2     H20 · Fenster 120 · min 1", 20, 120, 1),
    ("B3     H20 · Fenster 60  · min 3", 20, 60, 3),
    ("B3+B1  H5  · Fenster 60  · min 3", 5, 60, 3),
)

# Die Zielmarken der Reproduktion - aus 2.476-verkaufsregel.
BASIS_SOLL = {
    "ganze Haltemenge": 0.0791,
    "nicht mehr in der Auswahl": 0.0178,
}
TOLERANZ = 0.0005


def messe(je_tag: dict, menge: dict, block: int, mindest: int = 1) -> tuple:
    """Ein Punkt samt Band, Nullwelt und Trennschaerfe - EINE Quelle.

    ⚠️ Ruft `phase3_verkaufsregel.regel` auf, baut sie nicht nach. Eine
    Kopie waere hier besonders teuer: die Vorzeichenkonvention (behalten
    minus verkauft) steht genau einmal, und eine zweite Stelle koennte
    still auseinanderlaufen."""
    echt = regel(je_tag, menge, mindest_verkauft=mindest)
    if len(echt) < 30:
        return echt, [], None
    nullwerte = []
    for i in range(NULL_ZIEHUNGEN):
        n = regel(je_tag, menge, rng=np.random.default_rng(messnorm.SAAT + i),
                  mindest_verkauft=mindest)
        nb = band(n, block, zieh=300, saat=messnorm.SAAT + i)
        if nb:
            nullwerte.append(nb[0])
    oben = (float(np.percentile(nullwerte, messnorm.NULL_PERZENTIL))
            if nullwerte else float("nan"))
    ts = None
    for staerke in messnorm.STAERKEN:
        treffer = 0
        for i in range(messnorm.ZIEHUNGEN):
            pw = regel(je_tag, menge, pflanze=staerke,
                       mindest_verkauft=mindest)
            pb = band(pw, block, zieh=300, saat=messnorm.SAAT + 1000 + i)
            if pb and pb[1] > oben:
                treffer += 1
        if treffer >= max(3, (4 * messnorm.ZIEHUNGEN) // 5):
            ts = staerke
            break
    return echt, nullwerte, ts


# Die Saaten der Stabilitaetsprobe. Fuenf Werte mit ungleichen Abstaenden -
# gerundete Abstaende koennen mit der Blocklaenge in Resonanz gehen.
SAATEN = (0, 7, 13, 23, 37)


def stabilitaet(je_tag: dict, menge: dict, block: int, mindest: int) -> str:
    """⚠️⚠️ TRAEGT DAS URTEIL AUCH MIT EINER ANDEREN SAAT?

    DER ANLASS (19.09.2026): H5 kam auf TRAEGT, aber mit einem Abstand von
    0,0006 R zwischen der Bandunterkante und der oberen Nullgrenze. Zum
    Vergleich: an H20 ist dieselbe Frage um 0,0019 R GESCHEITERT. Ein
    Urteil, das an der dritten Nachkommastelle haengt, ist kein Befund,
    solange nicht gezeigt ist, dass es nicht die Saat ist.

    ⚠️ Die Positivkontrolle bleibt hier aussen vor - sie entscheidet das
    TRAEGT nicht, das tut allein Band gegen Nullgrenze. Wer sie mitzieht,
    verlaengert den Lauf um das Fuenffache ohne Erkenntnisgewinn."""
    treffer, zeilen = 0, []
    echt = regel(je_tag, menge, mindest_verkauft=mindest)
    for k in SAATEN:
        saat = messnorm.SAAT + k
        b = band(echt, block, zieh=300, saat=saat)
        nullwerte = []
        for i in range(NULL_ZIEHUNGEN):
            n = regel(je_tag, menge, rng=np.random.default_rng(saat + i),
                      mindest_verkauft=mindest)
            nb = band(n, block, zieh=300, saat=saat + i)
            if nb:
                nullwerte.append(nb[0])
        oben = (float(np.percentile(nullwerte, messnorm.NULL_PERZENTIL))
                if nullwerte else float("nan"))
        ok = bool(b) and b[1] > oben
        treffer += int(ok)
        zeilen.append("%s%+.4f" % ("OK " if ok else "NEIN",
                                   (b[1] - oben) if b else float("nan")))
    return "%d von %d tragen · Abstand Bandunterkante zu Nullgrenze: %s" % (
        treffer, len(SAATEN), "  ".join(zeilen))


def main() -> int:
    t0 = time.time()
    print("=" * 118)
    print("V3b-1 / B1 + B2 - SCHLIESST EINE BREITERE BASIS DAS BAND?")
    print("=" * 118)
    print("  " + messmenge.zeile())
    print("  " + messnorm.standardzeile().replace("\n", "\n  "))
    print("  Zielgroesse nach 2.472: POSITIV = die Behaltenen liefen besser, "
          "der Verkauf war richtig")
    print("  ⚠️ %s" % VORBEHALT)
    print("  ⚠️ R-R11: die erste Zeile reproduziert 2.476 - weicht sie ab, "
          "ist der LAUF ungueltig, nicht der Befund")

    print("\n  Kursreihen laden ...")
    reihen = R.B.lade("krypto", "V1")
    mom = momentum250(reihen)
    print("  %d Reihen (%.0f s)" % (len(reihen), time.time() - t0))

    je_tag_cache: dict = {}
    reproduziert = {}
    for titel, horizont, fenster, mindest in VARIANTEN:
        if horizont not in je_tag_cache:
            je_tag_cache[horizont] = R.K.baue(reihen, KANDIDAT,
                                              R._zusatz(KANDIDAT),
                                              horizont=horizont)
        je_tag = je_tag_cache[horizont]
        halte = haltemenge(mom, fenster)
        drin, raus = geteilt(mom, halte)
        block = messnorm._block(horizont)

        print("\n  %s" % ("-" * 114))
        print("  %s   ·   Haltemenge %.0f je Tag, davon nicht mehr in der "
              "Auswahl %.0f   ·   Block %d"
              % (titel,
                 float(np.mean([len(v) for v in halte.values() if v])),
                 float(np.mean([len(v) for v in raus.values() if v])), block))
        print("  %s" % ("-" * 114))
        print("     %-30s %9s %-22s %9s %5s   %s"
              % ("Menge", "R", "Band", "Nullwelt", "Tage", "Urteil"))
        for name, menge in (("ganze Haltemenge", halte),
                            ("nicht mehr in der Auswahl", raus),
                            ("noch in der Auswahl", drin)):
            echt, nullwerte, ts = messe(je_tag, menge, block, mindest)
            if len(echt) < 30:
                print("     %-30s zu wenige Tage (%d)" % (name, len(echt)))
                continue
            urteil(name, echt, nullwerte, block, ts)
            # ⚠️ DIE BESETZUNG STEHT VOR DER DEUTUNG, nicht danach -
            # stehende Vorgabe vom 07.09.2026.
            tage, mv, mb, minv = besetzung(je_tag, menge, mindest)
            print("     %-30s Besetzung je Tag: verkauft %.1f (min %d) gegen "
                  "behalten %.1f · Trennschaerfe %s · %s"
                  % ("", mv, minv, mb, ("%.2f R" % ts) if ts else "KEINE",
                     blockpruefung(echt, block)))
            if titel.startswith("BASIS") and name in BASIS_SOLL:
                b = band(echt, block)
                reproduziert[name] = (b[0] if b else float("nan"))

    # ---- Stabilitaetsprobe der knappen Urteile --------------------------
    print()
    print("  %s" % ("=" * 114))
    print("  ⚠️⚠️ STABILITAETSPROBE - die H5-Urteile hingen an 0,0006 bzw. "
          "0,0003 R")
    print("     Dieselbe Messung mit fuenf Saaten. Ein Urteil, das nur mit "
          "EINER Saat steht, ist keins.")
    for titel, horizont, fenster, mindest in VARIANTEN:
        if horizont != 5:
            continue
        je_tag = je_tag_cache[horizont]
        halte = haltemenge(mom, fenster)
        _drin, raus = geteilt(mom, halte)
        block = messnorm._block(horizont)
        print("     %-34s %s"
              % (titel, stabilitaet(je_tag, raus, block, mindest)))

    # ---- R-R11 ----------------------------------------------------------
    print("\n  %s" % ("=" * 114))
    print("  R-R11 - REPRODUKTION DER BASIS (2.476-verkaufsregel)")
    alles_ok = True
    for name, soll in BASIS_SOLL.items():
        ist = reproduziert.get(name, float("nan"))
        ok = abs(ist - soll) <= TOLERANZ
        alles_ok = alles_ok and ok
        print("     %-30s registriert %+.4f · reproduziert %+.4f · %s"
              % (name, soll, ist, "✔ stimmt" if ok else "⚠️ WEICHT AB"))
    if not alles_ok:
        print("     ⚠️⚠️ DER LAUF IST UNGUELTIG - nicht der Befund. "
              "Erst die Abweichung klaeren, dann B1/B2 lesen.")

    print("\n  LESEART")
    print("     R          behalten minus verkauft. POSITIV = der Verkauf war")
    print("                richtig (die Behaltenen liefen besser).")
    print("     ⚠️ B1 misst eine ANDERE FRAGE (5 Tage statt 20) - ein Band")
    print("        dort ersetzt das fehlende bei H20 nicht, es steht daneben.")
    print("     ⚠️ B2 verbreitert den STELLVERTRETER, nicht die Datenlage -")
    print("        wer 120 Tage als gehalten fuehrt, beschreibt kaum noch")
    print("        ein Portfolio.")
    print("\n  ⚠️ %s" % VORBEHALT)
    print("  (%.0f s)" % (time.time() - t0))
    print("=" * 118)
    return 0 if alles_ok else 1


if __name__ == "__main__":
    sys.exit(main())
