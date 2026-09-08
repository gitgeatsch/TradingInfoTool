# -*- coding: utf-8 -*-
"""N-82 — DIE BEITRAGSLAGE UNTER BEIDEN NULLREGELN (08.09.2026)

## Warum es das gibt

2.188: `null_oben` ist heute das **Maximum ueber fuenf** Nullziehungen.
N-81 hat gezeigt, dass ein Maximum kein Schaetzer ist - es waechst mit
der Ziehungszahl (auf Kunstdaten UND echt) und hat keinen Grenzwert.

> **Die Folge: das Urteil 'TRAEGT' haengt an einer unbegruendbaren Zahl.**
> `funding` bei 50 % traegt mit fuenf Ziehungen (Abstand +0,0002 R) und
> faellt ab zehn.

## Was hier gemessen wird

Jeder Kandidat auf jeder zulaessigen selektierten Menge - **zweimal**:

    alt   ZIEHUNGEN=5, null_oben = MAXIMUM      (der heutige Stand)
    neu   40 Ziehungen, null_oben = 90. PERZENTIL

⚠️ **Die Vorgabewerte von `pruefe_auswahl` sind unveraendert.** Die alte
Spalte ist keine Nachbildung, sondern derselbe Aufruf wie bisher - gegen
die vorherige Fassung Ziffer fuer Ziffer geprueft.

## Die Vorhersage, VOR dem Lauf (Methodik 2.80)

    Wer mit grossem Abstand traegt, traegt weiter    (schnitt)
    Wer knapp traegt, faellt                          (funding 50 %)
    Der Zufall traegt unter KEINER Regel

⚠️ Traegt `zufall` unter der neuen Regel, ist die neue Regel schlechter
und dieser Lauf beendet den Vorschlag - nicht das Gegenteil.

## ⚠️ Was hier NICHT geaendert wurde

Die TRENNSCHAERFE prueft weiter `pb["unten"] > 0`, also gegen NULL statt
gegen `null_oben` (2.188-inkonsistenz). Das ist ein zweiter, eigener
Punkt. Zwei Aenderungen in einem Lauf waeren nicht mehr zuzuordnen.

    python n82_beitragslage_beide_nullregeln.py
"""
from __future__ import annotations

import sys
import time

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_bewertungskennzahl as MB                        # noqa: E402
import messe_eigenschaft_beitrag as B                        # noqa: E402
import messe_funding_niveau as F                             # noqa: E402
import messe_kandidaten_als_regel as K                       # noqa: E402
import messnorm as N                                          # noqa: E402
import messnorm_auswahl as MA                                # noqa: E402
from messe_alle_kandidaten import (HORIZONT, KANDIDATEN,     # noqa: E402
                                   SELEKTIERT, zusatzquellen)

NULL_ZIEHUNGEN = 40
NULL_PERZENTIL = 90.0


def urteil_gesamt(paare: list) -> str:
    """Dasselbe Kriterium wie `messe_alle_kandidaten` - unveraendert."""
    aussagen = []
    for m, b in paare:
        if b.traegt:
            aussagen.append((m, True))
        elif b.urteil.upper().startswith("TRAEGT NICHT BIS"):
            aussagen.append((m, False))
    ja = [m for m, w in aussagen if w]
    nein = [m for m, w in aussagen if not w]
    if not aussagen:
        return "NICHT ENTSCHEIDBAR"
    if ja and nein:
        return "WIDERSPRUCH (%s / %s)" % (",".join(ja), ",".join(nein))
    return "TRAEGT" if ja else "TRAEGT NICHT"


def main() -> int:
    t0 = time.time()
    reihen = B.lade()
    mom = momentum = None
    from messe_beitrag_auf_auswahl import momentum250
    mom = momentum250(reihen)
    lage = N.Lage(instrument="spot", strategie="einstieg")
    zus = zusatzquellen()
    print("=" * 110)
    print("N-82 — die Beitragslage unter BEIDEN Nullregeln")
    print("=" * 110)
    print("  alt: %d Ziehungen, MAXIMUM   ·   neu: %d Ziehungen, %.0f. PERZENTIL"
          % (MA.ZIEHUNGEN, NULL_ZIEHUNGEN, NULL_PERZENTIL))
    print("  Basis: %d Krypto-Reihen · H%d · bewegung_r" % (len(reihen), HORIZONT))
    print()
    print("  %-15s %-5s %9s %10s %10s %9s %9s   %s"
          % ("Kandidat", "Menge", "Band u.", "null alt", "null neu",
             "Abst.alt", "Abst.neu", "alt -> neu"))

    alt_p, neu_p = {}, {}
    for a in KANDIDATEN:
        try:
            je = K.baue(reihen, a, zus.get(a), horizont=HORIZONT)
        except Exception as exc:                             # noqa: BLE001
            print("  %-15s -> %s" % (a, str(exc)[:60]))
            continue
        if not je:
            continue
        mengen = [m for m in MA.zulaessige_mengen(je, mom, horizont=HORIZONT)
                  if m in SELEKTIERT]
        if not mengen:
            print("  %-15s   ⚠️ keine zulaessige selektierte Menge" % a)
            alt_p[a] = neu_p[a] = []
            continue
        for m in mengen:
            try:
                ba = MA.pruefe_auswahl(a, je, mom, lage=lage, menge=m,
                                       rng=np.random.default_rng(20260908),
                                       horizont=HORIZONT,
                                       hypothese="N-82 alte Nullregel",
                                       verwendung="Beitrag")
                bn = MA.pruefe_auswahl(a, je, mom, lage=lage, menge=m,
                                       rng=np.random.default_rng(20260908),
                                       horizont=HORIZONT,
                                       hypothese="N-82 neue Nullregel",
                                       verwendung="Beitrag",
                                       null_ziehungen=NULL_ZIEHUNGEN,
                                       null_perzentil=NULL_PERZENTIL)
            except Exception as exc:                         # noqa: BLE001
                print("  %-15s %-5s -> %s" % (a, m, str(exc)[:50]))
                continue
            alt_p.setdefault(a, []).append((m, ba))
            neu_p.setdefault(a, []).append((m, bn))
            wa = "T" if ba.traegt else "-"
            wn = "T" if bn.traegt else "-"
            marke = "" if wa == wn else "   ⚠️ KIPPT"
            print("  %-15s %-5s %+9.4f %+10.4f %+10.4f %+9.4f %+9.4f   %s->%s%s"
                  % (a, m, ba.unten, ba.null_oben, bn.null_oben,
                     ba.unten - max(0.0, ba.null_oben),
                     bn.unten - max(0.0, bn.null_oben), wa, wn, marke),
                  flush=True)

    print()
    print("=" * 110)
    print("DAS GESAMTURTEIL JE REGEL")
    print("=" * 110)
    print("  %-15s %-34s %s" % ("Kandidat", "alte Regel (5, max)",
                                "neue Regel (40, p90)"))
    ua, un = {}, {}
    for a in KANDIDATEN:
        if a not in alt_p:
            continue
        ua[a] = urteil_gesamt(alt_p[a])
        un[a] = urteil_gesamt(neu_p[a])
        marke = "" if ua[a] == un[a] else "   ⚠️"
        print("  %-15s %-34s %s%s" % (a, ua[a], un[a], marke))

    print()
    za, zn = ua.get("zufall", "?"), un.get("zufall", "?")
    ok = True
    for name, z in (("alt", za), ("neu", zn)):
        if z.startswith(("TRAEGT NICHT", "NICHT ENTSCHEIDBAR")):
            print("  ✔ Kontrolle `zufall` (%s): %s" % (name, z))
        else:
            print("  ⚠️⚠️ Kontrolle `zufall` (%s): %s — die Regel taugt nicht."
                  % (name, z))
            ok = False
    print()
    for name, u in (("alt (5, max) ", ua), ("neu (40, p90)", un)):
        t = [a for a, v in u.items() if v == "TRAEGT" and a != "zufall"]
        print("  TRAGEND, %s: %s" % (name, ", ".join(t) if t else "⚠️ KEINER"))
    print()
    print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
