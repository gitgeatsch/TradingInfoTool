# -*- coding: utf-8 -*-
"""Phase 3, Schritt 1b: das NORMURTEIL zu den drei Beitraegen (18.09.2026).

Die Reproduktion (`phase3_reproduktion.py`) hat gezeigt, dass der Aufbau die
registrierten Zahlen wiederfindet. Sie liefert aber nur die ROHE Wirkung -
kein Urteil. Dieses Skript legt den Messstandard an:

    Nullpunkt   Mittelwert der Nullwelten aus 40 Ziehungen (seit 09.09.)
    Band        ueber Bloecke, Blocklaenge aus dem Horizont
    Trennschaerfe  gegen den NULLPUNKT, nicht gegen null
    Positivkontrolle  gepflanzte Leiter bis 0,40 R

⚠️ GEMESSEN WIRD AB 2023 (Vorgabe ZEITFENSTER-AB-2023): die 7-Jahres-Tabelle
mittelt eine gute und eine schlechte Haelfte (+8,64 gegen +2,77). Das volle
Fenster steht in der Reproduktion daneben - dort gehoert es hin, hier nicht.

⚠️ STELLVERTRETERMENGE (Nutzerentscheidung N3 b): jedes Urteil hier gilt
ausdruecklich nur auf dieser Menge als validiert, NICHT auf der Live-Menge
(Blocker A8, Befund 2.273). Die Kennzeichnung steht im Messkopf und in jeder
Zeile der Ausgabe.

⚠️ NUR LESEND, am Desktop. Kein LLM, kein Kontingent.
"""
from __future__ import annotations

import sys
import time

import numpy as np

import messnorm
import messnorm_auswahl as MA
import messmenge
import phase3_reproduktion as R
from messe_beitrag_auf_auswahl import momentum250

AB_2023 = "2023-01-01"
# ⚠️ Die Beitraege wirken auf der SELEKTIERTEN Menge - dort entscheidet die
# Kette auch (Stufe 5: oberste 20 % nach 250-Tage-Momentum).
MENGE = "20%"
LAGE = messnorm.Lage("spot", "einstieg")
VORBEHALT = ("gilt auf der Stellvertretermenge, NICHT auf der Live-Menge "
             "(N3 b, Blocker A8)")


def urteile(name: str, je_tag: dict, mom: dict, menge: str):
    """Ein Normurteil auf der SELEKTIERTEN Menge, unter der Tagesklammer.

    ⚠️ 18.09.: mein erster Aufruf ging auf die FREIE Menge - und die Norm hat
    ihn zurueckgewiesen (F-212: dort wirken die Beitraege auf 1,5 % der
    Anker, ein Nullbefund waere vorprogrammiert). Genau dafuer steht die
    Regel im Code und nicht in der Doku."""
    rng = np.random.default_rng(messnorm.SAAT)
    try:
        return MA.pruefe_auswahl(name, je_tag, mom, lage=LAGE, menge=menge,
                                 rng=rng, horizont=R.HORIZONT,
                                 zielgroesse="bewegung_r")
    except ValueError as x:
        print("    ⚠️ %s: %s" % (name, x))
        return None


def main() -> int:
    # ⚠⚠ `--quelle frei` misst turnover auf der NAEHERUNGSmenge
    # (P2, 22.09.2026). Ohne Angabe bleibt es `gesamt` - also genau die
    # Basis von 2.460-norm, damit die Reproduktion moeglich bleibt (R-R11).
    args = sys.argv[1:]
    quelle = "gesamt"
    if "--quelle" in args:
        i = args.index("--quelle")
        quelle = args[i + 1]
        args = args[:i] + args[i + 2:]
    nur = args or ["funding", "turnover", "oi_aenderung"]
    print("=" * 100)
    print("PHASE 3 · SCHRITT 1b - NORMURTEIL ZU DEN DREI BEITRAEGEN")
    print("=" * 100)
    print("  " + messmenge.zeile())
    print("  " + messnorm.standardzeile().replace("\n", "\n  "))
    print("  Fenster: ab %s · Horizont H%d · Menge %s (selektiert, Tagesklammer)"
          % (AB_2023, R.HORIZONT, MENGE))
    print("  ⚠️ %s" % VORBEHALT)
    print("\n  Kursreihen laden ...")
    reihen = R.B.lade("krypto", "V1")
    print("  %d Reihen geladen" % len(reihen))
    print("  Momentum-Auswahl (250 Tage) vorbereiten ...")
    mom = momentum250(reihen)
    print("  %d Tage mit Auswahl" % len(mom))

    for art in nur:
        t0 = time.time()
        je_tag = R._ab(R.K.baue(reihen, art, R._zusatz(art, quelle),
                                horizont=R.HORIZONT), AB_2023)
        print("\n" + "-" * 100)
        print("  %s - %d Tage ab %s%s"
              % (art.upper(), len(je_tag), AB_2023,
                 ("  \u26a0 QUELLE: %s" % quelle)
                 if art == "turnover" else ""))
        b = urteile(art, je_tag, mom, MENGE)
        if b is None:
            continue
        print("   " + b.zeile())
        if getattr(b, "urteil", None) is not None:
            print("   Urteil: %s" % b.urteil)
        print("   ⚠️ %s" % VORBEHALT)
        print("   (%.0f s)" % (time.time() - t0))
    print("\n" + "=" * 100)
    return 0


if __name__ == "__main__":
    sys.exit(main())
