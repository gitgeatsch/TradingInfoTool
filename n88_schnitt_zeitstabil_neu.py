# -*- coding: utf-8 -*-
"""N-88 — `schnitt`s ZEITSTABILITÄT, neu entschieden (09.09.2026)

## Warum das jetzt kommt — die Abbruchbedingung

Das Kandidatenregister haelt fuer `schnitt` fest:

> ⚠️ **Offen und Abbruchbedingung:** die Zeitstabilitaet (N-60) ist
> unentschieden. **Wer vor ihrer Klaerung baut, wiederholt den
> 31.08.-Fehler.**

Und der Stand vom 07.09. lautet woertlich:

> „Praktisch bleibt er unbaubar, aber weil **nichts davon entscheidbar**
> ist, nicht weil er widerlegt waere."

⚠️⚠️ **Unentscheidbar war es, weil die MESSANLAGE es nicht hergab.**
Seither sind SECHS Fehler in genau dieser Anlage behoben und der
Nullbezug gegen bekannte Wahrheit geeicht (Methodik 2.216). Die Frage ist
damit moeglicherweise entscheidbar geworden - und sie ist der erste
Knoten der Kette:

    Messstandard -> schnitt zeitstabil? -> Sperre baubar -> R-R9
                 -> Bewertung besser (O4) -> Hebel erreicht 2-5x (K1)

## ⚠️ Der bekannte Haken: der Unterschied DREHT MIT DER MENGE

    +0,2238 bei 20 %      -0,0647 bei 10 %

Bei `funding` und `zufall` tut er das NICHT. **Deshalb wird hier ueber
ALLE Mengen gemessen, nicht auf einer.** Eine Aussage auf einer einzelnen
Menge waere genau der Fehler, der schon zweimal passiert ist.

## Die Frage, richtig gestellt

Nicht *„traegt er in A?"* UND *„traegt er in B?"* - zwei halbierte Tests.
Sondern **eine**: *ist (A − B) von null zu trennen?*, auf der ganzen
Reihe. Der zweite Test ist auch dann aussagekraeftig, wenn keiner der
Einzeltests es ist (N-68).

⚠️ Der Nullbezug aus dem Messstandard gilt hier NICHT: geprueft wird ein
UNTERSCHIED gegen null, kein Effekt gegen eine gemischte Welt. Unter „die
Zeit aendert nichts" ist der Erwartungswert exakt null.

⚠️ Gemessen wird auf der ENTZERRTEN Reihe (echte Wirkung minus Nullwert
desselben Tages) - sonst traegt der Tagesnullwert in beide Haelften mit
hinein.

## Die Kontrollen

    zufall     darf keinen Unterschied zeigen
    funding    zeigte am 07.09. keinen - er ist der Bezugsfall
    ⚠️ Der Test erklaert zu OFT einen Unterschied (18 % Fehlalarm statt
       10 %, auf Kunstdaten gemessen). Ein gefundener Unterschied ist
       deshalb VORSICHTIG zu lesen, ein Nullbefund dagegen STARK.

## Die Vorhersage, VOR dem Lauf (Methodik 2.80)

    Erwartung   `schnitt` bleibt UNENTSCHIEDEN - der Mengenwechsel des
                Vorzeichens ist ein Zeichen dafuer, dass zu wenig Signal
                da ist, und daran aendert ein besserer Nullbezug nichts
    Gegenthese  ueber alle Mengen zeigt sich ein einheitliches Bild -
                dann ist die Abbruchbedingung erfuellt und die Sperre
                baubar

⚠️ Faellt es einheitlich aus, ist das eine BAUENTSCHEIDUNG mit R-R9 im
Gefolge - nicht das Ende der Pruefung.

    python n88_schnitt_zeitstabil_neu.py
"""
from __future__ import annotations

import sys
import time

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_eigenschaft_beitrag as B                        # noqa: E402
import messe_kandidaten_als_regel as K                       # noqa: E402
import messmenge                                              # noqa: E402
import messnorm as N                                          # noqa: E402
from messe_alle_kandidaten import HORIZONT, zusatzquellen    # noqa: E402
from messe_beitrag_auf_auswahl import momentum250            # noqa: E402
from messnorm import _block                                   # noqa: E402
from messnorm_auswahl import MENGEN                           # noqa: E402
# ⚠️ DIE ECHTEN Funktionen, keine Kopien - `entzerrte_reihe` und die
# Bandrechnung stammen aus N-68/N-70 und haben dort ihre Kontrollen.
from n68_zeitstabilitaet import entzerrte_reihe, unterschied  # noqa: E402

KANDIDATEN = ("schnitt", "funding", "zufall")
PRUEFEN = ("5%", "10%", "20%", "50%", "frei")


def main() -> int:
    t0 = time.time()
    reihen = B.lade()
    mom = momentum250(reihen)
    zus = zusatzquellen()
    block = _block(HORIZONT)

    print("=" * 104)
    print("N-88 — `schnitt`s Zeitstabilitaet, ueber ALLE Mengen")
    print("=" * 104)
    print("  %s" % messmenge.zeile())
    print("  %s" % N.standardzeile())
    print("  ⚠️ Der Nullbezug gilt hier NICHT - geprueft wird ein "
          "UNTERSCHIED gegen null.")
    print("  ⚠️ Der Test erklaert zu OFT einen Unterschied (18 %% statt "
          "10 %%): ein Nullbefund")
    print("     ist STARK, ein gefundener Unterschied VORSICHTIG zu lesen.")
    print()
    print("  %-10s %-6s %9s %9s %10s %24s  %s"
          % ("Kandidat", "Menge", "erste", "zweite", "Diff", "Band",
             "Urteil"))

    erg = {}
    for kand in KANDIDATEN:
        try:
            je = K.baue(reihen, kand, zus.get(kand), horizont=HORIZONT)
        except Exception as exc:                             # noqa: BLE001
            print("  %-10s -> %s" % (kand, str(exc)[:60]))
            continue
        for menge in PRUEFEN:
            try:
                e = entzerrte_reihe(je, mom, MENGEN[menge])
            except Exception as exc:                         # noqa: BLE001
                print("  %-10s %-6s -> %s" % (kand, menge, str(exc)[:44]))
                continue
            tage = sorted(e)
            if len(tage) < 4 * block:
                print("  %-10s %-6s ⚠️ nur %d Tage (%d Bloecke) - zu wenig"
                      % (kand, menge, len(tage), len(tage) // block))
                continue
            mitte = tage[len(tage) // 2]
            # ⚠️ `unterschied` erwartet die VOLLE Reihe plus zwei
            # TAGESMENGEN - nicht zwei Woerterbuecher.
            mA = {t for t in e if t < mitte}
            mB = {t for t in e if t >= mitte}
            try:
                d = unterschied(e, mA, mB, block)
            except Exception as exc:                         # noqa: BLE001
                print("  %-10s %-6s -> %s" % (kand, menge, str(exc)[:44]))
                continue
            if d is None:
                print("  %-10s %-6s ⚠️ zu wenige Bloecke je Haelfte"
                      % (kand, menge))
                continue
            ma, mb = d["A"], d["B"]
            trennt = not (d["unten"] <= 0.0 <= d["oben"])
            erg[(kand, menge)] = (ma, mb, d, trennt)
            print("  %-10s %-6s %+9.4f %+9.4f %+10.4f [%+.4f .. %+.4f]  %s"
                  % (kand, menge, ma, mb, d["diff"], d["unten"], d["oben"],
                     "⚠️ UNTERSCHIED" if trennt else "kein Unterschied"),
                  flush=True)
        print()

    # ---- Urteil ---------------------------------------------------------
    print("=" * 104)
    print("IST `schnitt` ZEITSTABIL - EINHEITLICH UEBER DIE MENGEN?")
    print("=" * 104)
    for kand in KANDIDATEN:
        z = [(m, erg[(kand, m)]) for m in PRUEFEN if (kand, m) in erg]
        if not z:
            continue
        diffs = [d["diff"] for _m, (_a, _b, d, _t) in z]
        trennend = [m for m, (_a, _b, _d, t) in z if t]
        vorzeichen = {np.sign(x) for x in diffs if abs(x) > 1e-9}
        print("  %-10s %d Mengen · Differenzen %s"
              % (kand, len(z), " ".join("%+.3f" % x for x in diffs)))
        if len(vorzeichen) > 1:
            print("             ⚠️⚠️ DAS VORZEICHEN DREHT ueber die Mengen "
                  "- kein einheitliches Bild.")
        if trennend:
            print("             ⚠️ Unterschied trennbar auf: %s"
                  % ", ".join(trennend))
        else:
            print("             ✔ auf KEINER Menge ein trennbarer "
                  "Unterschied - und ein Nullbefund ist hier STARK.")
    print()
    print("  ⚠️ Ein einheitlicher Nullbefund bei `schnitt` erfuellt die "
          "Abbruchbedingung")
    print("     aus dem Kandidatenregister - dann waere die SPERRE baubar, "
          "mit R-R9 im Gefolge.")
    print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
