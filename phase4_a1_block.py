# -*- coding: utf-8 -*-
"""Phase 4, A1 / Schritt E1: IST DER BLOCK AUF `barriere` ZU KURZ? (20.09.2026)

⚠️⚠️ A1 IST KEIN MARKTPROBLEM, SONDERN EIN ANLAGENPROBLEM. Befund 2.238:

    "bei rund 250 Ankern je Tag und 48 Bloecken muesste das Band etwa
     ±0,0023 breit sein - beobachtet sind ±0,0006, also VIERMAL ZU ENG.
     Ein zu enges Band laesst jede Winzigkeit 'tragen', und genau das tut
     `zufall` hier."

Solange das offen ist, ist jede Hebelmessung wertlos.

## Warum DIESE Pruefung zuerst

`messnorm._block` schreibt seit dem Bau vor, dass die Blocklaenge je
Messung NACHGEPRUEFT wird. Ist die Autokorrelation der Tageswirkung beim
Blockabstand zu hoch, ist der Block zu kurz - und ein zu kurzer Block
macht das Band ZU ENG. Das ist genau das beobachtete Symptom.

➔ Findet diese Pruefung die Ursache, ist A1 beantwortet, ohne dass ein
einziger Selbsttest laufen muss. Findet sie nichts, ist die Ursache
woanders - und auch das ist ein Ergebnis, weil es die Suche eingrenzt.

## ⚠️ Die Barriere wird NICHT nachgebaut

`k1c_hebel_barriere.barriere_je_tag` rechnet sie auf der
PRODUKTIONSGEOMETRIE - min(25 %, max(5 %, 0,75 x ATR)), CRV 2,0. Dieselbe
Funktion, mit der 2.238 entstanden ist. Ein Nachbau hier waere ein
zweiter Massstab und wuerde den Vergleich mit dem Befund zerstoeren
(R-R11: wer die Basis aendert, hat etwas anderes gemessen).

## Was verglichen wird

    bewegung_r   die stetige Zielgroesse - dort ist die Anlage geeicht
                 (Selbsttest 08.09., 0 von 50 Fehlalarmen)
    barriere     die binaere - hier steht der Verdacht

Beide auf DENSELBEN Tagen, mit DEMSELBEN Kandidaten. Weicht nur die
Autokorrelation ab, ist die Ursache gefunden.

⚠️ Stellvertretermenge (N3 b), nur lesend, kein LLM.
"""
from __future__ import annotations

import sys
import time

import numpy as np

import k1c_hebel_barriere as K1C
import messnorm as N
import messmenge
import phase3_reproduktion as R
from messe_beitrag_auf_auswahl import momentum250

AB = "2023-01-01"
KANDIDATEN = ("funding", "zufall")
# ⚠️ `zufall` IST DER ZEUGE. Er darf NIE tragen; tut er es doch, ist die
# Anlage kaputt und nicht der Markt. Genau daran ist A1 aufgefallen.
VORBEHALT = "gilt auf der Stellvertretermenge (N3 b)"


def tageswirkung(je_tag: dict, anteil: float = 0.20) -> dict:
    """tag -> Wirkung des obersten Fuenftels, mit der Statistik der Norm.

    ⚠️ DIE STATISTIK KOMMT AUS DEM REGISTER, nicht aus dieser Datei:
    `bewegung_r` rechnet MEDIAN, `barriere` rechnet MITTEL - und zwar weil
    der Ausgang binaer ist und ein Median dort 0 oder 1 waere. Wer sie hier
    frei setzt, misst eine andere Groesse als die Norm."""
    import messe_regel_wirksamkeit as RW

    aus = {}
    for tag, zeilen in je_tag.items():
        if tag < AB or len(zeilen) < 12:
            continue
        kz = np.array([x["kennzahl"] for x in zeilen], float)
        y = np.array([x["in_r"] for x in zeilen], float)
        ok = np.isfinite(kz) & np.isfinite(y)
        if ok.sum() < 12:
            continue
        kz, y = kz[ok], y[ok]
        oben = RW.rang(kz) >= RW.GRENZE
        if oben.sum() < 2 or (~oben).sum() < 2:
            continue
        aus[tag] = float(np.mean(y[~oben]) - np.mean(y[oben]))
    return aus


def zeile(name: str, d: dict, block: int) -> None:
    bp = N.pruefe_block(d, block)
    x = np.array([d[t] for t in sorted(d)], float)
    print("     %-26s %5d Tage · Streuung %.5f · AK(%d) %+.3f · %s"
          % (name, len(d), float(np.std(x)) if len(x) else float("nan"),
             block, bp["ak"], bp["grund"]))
    return bp


def main() -> int:
    t0 = time.time()
    print("=" * 112)
    print("PHASE 4 · A1 / E1 - IST DER BLOCK AUF `barriere` ZU KURZ?")
    print("=" * 112)
    print("  " + messmenge.zeile())
    print("  " + N.standardzeile().replace("\n", "\n  "))
    print("  Geometrie: die PRODUKTIONSGEOMETRIE aus "
          "`k1c_hebel_barriere` - nicht nachgebaut")
    print("  ⚠️ %s" % VORBEHALT)

    print("\n  Kursreihen laden ...")
    reihen = R.B.lade("krypto", "V1")
    mom = momentum250(reihen)
    block = N._block(R.HORIZONT)
    print("  %d Reihen · Horizont H%d · Blocklaenge %d (%.0f s)"
          % (len(reihen), R.HORIZONT, block, time.time() - t0))

    for art in KANDIDATEN:
        print("\n  %s" % ("-" * 108))
        print("  KANDIDAT `%s`" % art)
        je = R.K.baue(reihen, art, R._zusatz(art), horizont=R.HORIZONT)
        d_stetig = tageswirkung(je)
        je_bar, anteil = K1C.barriere_je_tag(je, reihen, R.HORIZONT)
        d_binaer = tageswirkung(je_bar)
        print("     Anteil der Anker, die sich im Fenster AUFLOESEN: "
              "%.1f %%" % (100 * anteil))
        b1 = zeile("bewegung_r (stetig)", d_stetig, block)
        b2 = zeile("barriere (binaer)", d_binaer, block)
        # ⚠️ DER VERGLEICH IST DIE AUSSAGE, nicht die Einzelzahl.
        print("     ➔ Autokorrelation binaer minus stetig: %+.3f"
              % (b2["ak"] - b1["ak"]))
        if b2["ok"] and not b1["ok"]:
            print("     ⚠️ umgekehrt als vermutet - der STETIGE Block ist "
                  "der zu kurze")
        elif not b2["ok"]:
            print("     ⚠️⚠️ DER BLOCK IST AUF `barriere` ZU KURZ - das "
                  "erklaert ein zu enges Band")
        else:
            print("     ✔ beide Bloecke halten - die Ursache fuer das enge "
                  "Band liegt NICHT hier")

    # ---- ⚠️⚠️ R-R11: 2.238 REPRODUZIEREN, BEVOR IRGENDETWAS FOLGT ------
    #
    # Der Befund sagt "viermal zu eng". Ein Band laesst sich aber nur gegen
    # eine ERWARTUNG beurteilen, und die haengt an der Streuung der
    # Tageswirkung und an der Zahl unabhaengiger Bloecke:
    #
    #     Standardfehler ~ Tagesstreuung / Wurzel(Bloecke)
    #     Band (95 %)    ~ 1,96 x Standardfehler
    #
    # ⚠️ DAS IST EINE GROBE ERWARTUNG, KEINE EXAKTE FORMEL - der
    # Blockbootstrap rechnet anders, und die Tageswerte sind nicht
    # gleichgewichtig. Sie taugt, um eine GROESSENORDNUNG zu pruefen,
    # nicht um eine Nachkommastelle zu streiten. Genau so ist sie in 2.238
    # auch benutzt worden.
    from n64_schnitt_stufen import band as _band

    print()
    print("  %s" % ("=" * 108))
    print("  ⚠️⚠️ R-R11 - IST DAS BAND WIRKLICH ZU ENG?")
    print("     %-26s %11s %11s %8s   %s"
          % ("Kandidat/Zielgroesse", "Band(halb)", "erwartet", "Faktor",
             "Urteil"))
    for art in KANDIDATEN:
        je = R.K.baue(reihen, art, R._zusatz(art), horizont=R.HORIZONT)
        je_bar, _ = K1C.barriere_je_tag(je, reihen, R.HORIZONT)
        for name, d in (("%s / bewegung_r" % art, tageswirkung(je)),
                        ("%s / barriere" % art, tageswirkung(je_bar))):
            b = _band(d, block)
            if not b:
                print("     %-26s kein Band" % name)
                continue
            halb = (b[2] - b[1]) / 2.0
            x = np.array([d[t] for t in sorted(d)], float)
            bloecke = max(1, len(x) // block)
            # ⚠️⚠️ ZWEI ERWARTUNGEN, UND DER UNTERSCHIED IST DER GANZE
            # STREIT (korrigiert 20.09.2026 im Lauf).
            #
            # Meine erste Fassung rechnete durch die Wurzel der BLOCKZAHL
            # und bekam Faktoren von 3,9 bis 12,5 - also "zu eng" auf
            # BEIDEN Zielgroessen. Das war falsch, und zwar so:
            #
            # `band()` bootstrappt ein MITTEL ueber alle Tage. Die
            # Blockstruktur zaehlt nur, SOWEIT die Tage voneinander
            # abhaengen. Oben gemessen: Autokorrelation rund 0,02 - sie
            # haengen praktisch NICHT voneinander ab. Dann ist der
            # Standardfehler sigma/Wurzel(TAGE), nicht sigma/Wurzel
            # (BLOECKE). Der Unterschied ist genau Wurzel(Block) = 7,75 -
            # und das ist die Groessenordnung, die als "viermal zu eng"
            # gelesen wurde.
            #
            # ⚠️ 1,645 UND NICHT 1,96: `band()` nimmt die Perzentile 5 und
            # 95, bildet also ein 90-%-Band. Auch das habe ich zuerst
            # falsch angesetzt.
            erw_tage = 1.645 * float(np.std(x)) / (len(x) ** 0.5)
            erw_bloecke = 1.645 * float(np.std(x)) / (bloecke ** 0.5)
            faktor = erw_tage / halb if halb > 0 else float("inf")
            urteil = ("⚠️ ZU ENG" if faktor >= 2.0 else
                      "⚠️ zu weit" if faktor <= 0.5 else "passt")
            print("     %-26s %11.5f %11.5f %8.2f   %s   (je Block "
                  "%.5f -> Faktor %.1f)"
                  % (name, halb, erw_tage, faktor, urteil, erw_bloecke,
                     erw_bloecke / halb if halb > 0 else float("inf")))
    print("     ⚠️ Faktor = erwartet geteilt durch beobachtet. Ueber 2 "
          "heisst ZU ENG.")
    print("     ⚠️⚠️ DIE SPALTE RECHTS IST DIE FALSCHE RECHNUNG - sie steht "
          "hier, weil sie")
    print("        vermutlich in 2.238 steckt. Bei unabhaengigen Tagen ist "
          "sie um")
    print("        Wurzel(Block) = %.2f zu gross." % (block ** 0.5))
    print("     ⚠️⚠️⚠️ UND AUCH DIE LINKE IST NUR EINE ERWARTUNG. Zwei "
          "Formeln, zwei")
    print("        Ergebnisse - entschieden wird das NICHT mit einer Formel, "
          "sondern")
    print("        mit der FEHLALARMQUOTE auf Nullwelten (E2).")
    print("     ⚠️⚠️ Der Vergleich der beiden ZIELGROESSEN ist die Aussage - "
          "eine")
    print("        absolute Bandbreite sagt nichts, solange die Skala eine "
          "andere ist.")

    print("\n  LESEART")
    print("     Die Autokorrelation der TAGESWIRKUNG beim Blockabstand.")
    print("     Ueber 0,15 heisst: der Block ist kuerzer als die")
    print("     Abhaengigkeit, und dann ist das Band ZU ENG.")
    print("     ⚠️ `zufall` ist der Zeuge - er darf nie tragen.")
    print("\n  ⚠️ %s" % VORBEHALT)
    print("  (%.0f s)" % (time.time() - t0))
    print("=" * 112)
    return 0


if __name__ == "__main__":
    sys.exit(main())
