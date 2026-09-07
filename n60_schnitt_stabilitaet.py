# -*- coding: utf-8 -*-
"""N-60 — HÄLT `schnitt` ÜBER DIE ZEIT? Nach BTC-Trend statt nach Hälften (07.09.)

## Die Lage

N-59 (2.145): `schnitt` trägt auf der selektierten Menge mit **+0,1707 R**
[+0,0723 .. +0,2781] bei 20 %, deckt **516/516 Symbole** ab und ist kaum
redundant (r -0,097 zu funding, -0,168 zu turnover). **Der beste Kandidat,
den dieses Projekt bisher hatte.**

⚠️ **Aber die Historienhälften klaffen:**

    erste Haelfte    +0,3483   nur 17 Bloecke - kein Befund
    zweite Haelfte   +0,0375   traegt nicht bis 0,10 R

Beides ist untermächtig. **Die Halbierung halbiert auch die Blöcke** - sie
kann die Frage nicht beantworten, die sie stellt.

## ⚠️⚠️ Warum NICHT die Streuungs-Schichtung — ein Einwand aus dem eigenen Plan

Naheliegend wäre „Marktphasen statt Hälften". Der Gesamtplan warnt aber
(N20, Abschnitt Marktphasen):

> *„HOCH liegt überwiegend vor 2022, niedrig überwiegend nach 2024 —
> **Schichter und Epoche sind teilweise verwechselbar.**"*

**Das trifft `schnitt` genau**: er war in der ERSTEN Hälfte stark. Eine
Streuungs-Schichtung würde denselben Zeiteffekt nur anders benennen und
wie ein neuer Befund aussehen.

> **Brauchbar ist allein der BTC-TREND** (BTC über/unter seinem
> 200-Tage-Schnitt), weil sich Bull- und Bärphasen **abwechseln**. Dort
> sind Schichter und Epoche getrennt.

⚠️ Die Einteilung wird IMPORTIERT (`messe_h_als_filter.btc_ueber_schnitt`),
nicht neu gebaut - sie ist bereits korrekt rückwärtsgerichtet.

## ⚠️ Die Blockregel entscheidet mit, und sie wird VORHER geprüft

    Block  = 3 x Horizont = 60 Tage bei H20
    Grenze = 20 Bloecke   -> mindestens 1.200 Tage JE PHASE

**Reicht eine Phase nicht, ist das Ergebnis dort kein Befund, sondern
Untermacht.** Das steht vor der Messung fest, nicht danach.

## Was gemessen wird

    1  Wieviele Tage/Bloecke hat jede Phase? (VOR der Deutung)
    2  `schnitt` je Phase, Menge 20 % - dieselbe wie in N-59
    3  Als Gegenprobe: `funding` je Phase. Es traegt bekanntermassen -
       bricht es hier zusammen, liegt es an der Schichtung, nicht an
       `schnitt`.
    4  Und `zufall` je Phase - er darf nirgends tragen.

    python n60_schnitt_stabilitaet.py
"""
from __future__ import annotations

import sys
import time

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_eigenschaft_beitrag as B                        # noqa: E402
import messe_funding_niveau as F                             # noqa: E402
import messe_kandidaten_als_regel as K                       # noqa: E402
import messnorm as N                                          # noqa: E402
from messe_beitrag_auf_auswahl import momentum250            # noqa: E402
from messe_h_als_filter import btc_ueber_schnitt             # noqa: E402
from messnorm_auswahl import pruefe_auswahl                  # noqa: E402

# ⚠️ H5 STATT H20 (07.09., nach dem ersten Lauf).
#
# Bei H20 ist der Block 60 Tage. Die BAER-Phase hat 1.198 Tage -> 19
# Bloecke, unter der Grenze von 20. Die eingebaute Gegenprobe hat es
# gefangen: `funding`, ein bekannt tragender Beitrag, traegt dort in
# KEINER Phase. Das war ein Befund ueber die SCHICHTUNG, nicht ueber
# `schnitt`.
#
# Bei H5 ist der Block 15 Tage -> BAER 79 Bloecke. Und H5 liegt naeher am
# Betriebshorizont (3-5 Tage) als H20.
#
# ⚠️ ES IST EINE ANDERE BASIS als N-59 (H20). Der Gesamtwert wird deshalb
# MITGEMESSEN, damit die Verschiebung sichtbar bleibt statt unterzugehen.
HORIZONT, MENGE = 5, "20%"
BLOCK = 3 * HORIZONT
MIN_BLOECKE = 20


def main() -> int:
    t0 = time.time()
    print("=" * 96)
    print("N-60 — haelt `schnitt` ueber die ZEIT? Nach BTC-Trend")
    print("=" * 96)
    print("  Lade Reihen ...", flush=True)
    reihen = B.lade()
    mom = momentum250(reihen)
    trend = btc_ueber_schnitt()
    lage = N.Lage(instrument="spot", strategie="einstieg")

    kandidaten = (("schnitt", None), ("funding", F.lade_funding()),
                  ("zufall", None))
    welten = {a: K.baue(reihen, a, z, horizont=HORIZONT)
              for a, z in kandidaten}

    # ---- 1: die Blockzahl je Phase, VOR der Deutung --------------------
    print()
    print("  1  DIE BLOCKZAHL JE PHASE — vor der Deutung")
    print("     Block %d Tage (3 x H%d) · Grenze %d Bloecke"
          % (BLOCK, HORIZONT, MIN_BLOECKE))
    je = welten["schnitt"]
    tage = sorted(je)
    bull = [t for t in tage if trend.get(t) is True]
    baer = [t for t in tage if trend.get(t) is False]
    ohne = [t for t in tage if t not in trend]
    print("     %-12s %6d Tage -> %3d Bloecke  %s"
          % ("BULL", len(bull), len(bull) // BLOCK,
             "✔" if len(bull) // BLOCK >= MIN_BLOECKE else "⚠️ UNTERMAECHTIG"))
    print("     %-12s %6d Tage -> %3d Bloecke  %s"
          % ("BAER", len(baer), len(baer) // BLOCK,
             "✔" if len(baer) // BLOCK >= MIN_BLOECKE else "⚠️ UNTERMAECHTIG"))
    if ohne:
        print("     %-12s %6d Tage (kein BTC-Schnitt - fallen weg)"
              % ("ohne Phase", len(ohne)))
    # ⚠️ Wechseln sich die Phasen ab? Sonst waere es doch eine Epoche.
    folge = [trend.get(t) for t in tage if t in trend]
    wechsel = sum(1 for i in range(1, len(folge)) if folge[i] != folge[i - 1])
    print("     ⚠️ Phasenwechsel: %d — %s"
          % (wechsel,
             "die Phasen WECHSELN SICH AB, Schichter und Epoche sind "
             "getrennt ✔" if wechsel >= 6 else
             "⚠️ ZU WENIGE Wechsel - der Schichter waere eine Epoche"))

    # ---- 2/3/4: je Kandidat und Phase ----------------------------------
    print()
    print("  2  DIE MESSUNG — Menge %s, dieselbe wie in N-59" % MENGE)
    print("     %-10s %-6s %10s %24s  %s"
          % ("Kandidat", "Phase", "Wirkung", "Band", "Urteil"))
    erg = {}
    for art in ("schnitt", "funding", "zufall"):
        w = welten[art]
        for lab, menge_tage in (("GANZ", None), ("BULL", set(bull)),
                                ("BAER", set(baer))):
            teil = w if menge_tage is None else {t: z for t, z in w.items()
                                                 if t in menge_tage}
            rng = np.random.default_rng(20260907)
            try:
                b = pruefe_auswahl(art, teil, mom, lage=lage, menge=MENGE,
                                   rng=rng, horizont=HORIZONT,
                                   hypothese="Stabilitaet nach BTC-Trend",
                                   verwendung="Beitrag")
            except Exception as exc:                         # noqa: BLE001
                print("     %-10s %-6s -> %s" % (art, lab, exc))
                continue
            erg[(art, lab)] = b
            print("     %-10s %-6s %+9.4f R [%+.4f .. %+.4f]  %s"
                  % (art, lab, b.wirkung, b.unten, b.oben, b.urteil[:46]),
                  flush=True)
        print()

    # ---- Urteil ---------------------------------------------------------
    print("=" * 96)
    print("WAS DAS HEISST")
    print("=" * 96)
    zf = [erg.get(("zufall", p)) for p in ("GANZ", "BULL", "BAER")]
    if any(b is not None and b.traegt for b in zf):
        print("  ⚠️⚠️ `zufall` TRAEGT in mindestens einer Phase - der Aufbau")
        print("     ist kaputt, alles Weitere waertlos.")
        print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
        return 1
    print("  ✔ `zufall` traegt in keiner Phase.")
    fu = [(p, erg.get(("funding", p))) for p in ("BULL", "BAER")]
    fu_ok = [p for p, b in fu if b is not None and b.traegt]
    print("  Gegenprobe `funding`: traegt in %s"
          % (", ".join(fu_ok) if fu_ok else "KEINER Phase ⚠️"))
    if not fu_ok:
        print("     ⚠️ Dann zerlegt die Schichtung die Aussagekraft so weit,")
        print("        dass auch ein bekannter Beitrag verschwindet. Das ist")
        print("        ein Befund ueber die SCHICHTUNG, nicht ueber `schnitt`.")
    print()
    sb, sr = erg.get(("schnitt", "BULL")), erg.get(("schnitt", "BAER"))
    if sb is not None and sr is not None:
        if sb.traegt and sr.traegt:
            print("  ✔✔ `schnitt` TRAEGT IN BEIDEN PHASEN - er haelt ueber")
            print("     die Zeit. Damit ist er registrierungsreif, sobald")
            print("     R-R9 (Neukalibrierung) mitgezogen wird.")
        elif sb.traegt or sr.traegt:
            p = "BULL" if sb.traegt else "BAER"
            print("  ⚠️ `schnitt` traegt NUR in %s. Das ist kein Nullbefund," % p)
            print("     sondern eine BEDINGUNG: er waere ein Beitrag, der")
            print("     nur in einer Marktlage gilt. Ob die Kette das")
            print("     abbilden kann, ist eine ENTWURFSfrage.")
        else:
            print("  ⚠️ `schnitt` traegt in KEINER Phase einzeln.")
            print("     ⚠️ Vor der Deutung: liegt es an der Untermacht?")
            print("        Trennschaerfe BULL %s · BAER %s"
                  % (sb.trennschaerfe, sr.trennschaerfe))
            print("        Traegt `funding` hier ebenfalls nicht, ist es die")
            print("        Schichtung - nicht der Kandidat.")
    print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
