# -*- coding: utf-8 -*-
"""N-62 — Haengt die Wirkung des Akkumulationsmasses an der TIEFE? (07.09.)

## Warum diese Frage und nicht die naheliegende

N-61 hat gemessen: das Mass traegt auf 504 Werten (+0,0292, p 0,000), auf
BTC+ETH+SOL nicht (-0,0283, **p 0,833**).

⚠️ **p 0,833 ist kein Gegenbefund, sondern Untermacht.** Drei Reihen mit 8
bis 12 Bloecken koennen die Frage nicht beantworten - egal welche Zahl
herauskommt. Wer aus -0,0283 eine Umkehr liest, deutet Rauschen.

N-61 hat aber einen belastbaren ZAEHLBEFUND geliefert (3.003 Tage, keine
Untermacht): **BTC liegt an 2,0 % der Tage unter -40 % vom eigenen
200-Schnitt, das uebrige Universum an 20,6 %.** Zehnfacher Unterschied.

> **Die messbare Frage lautet deshalb nicht "wirkt es bei BTC", sondern:
> haengt die Wirkung des Masses davon ab, WIE OFT ein Wert tief faellt?**

Die ist auf allen 507 Reihen zu stellen - also mit Aussagekraft.

## ⚠️ Ein Vorbefund steht dagegen und wird mitgeprueft

`project_eigenschaften_erklaeren_den_vorsprung_nicht`: keine
Asset-Eigenschaft hat den Vorsprung bisher erklaert. **Faellt diese
Messung ebenfalls flach, ist das die Reproduktion eines bekannten
Befundes - kein neuer Nullbefund.** Das steht VOR der Messung hier, damit
es hinterher nicht wie eine Ausrede klingt.

## Der Aufbau

    Schichter   Anteil der Tage unter -40 % zum eigenen 200-Schnitt
                (aus der Reihe selbst, rueckwaertsgerichtet)
    Fuenftel    je ~101 Reihen - statt 3
    Gemessen    UNTER_SMA je Fuenftel, H = 90
    Kontrolle   WOCHENTAG je Fuenftel - darf nirgends tragen

⚠️ **Regel 3 ist nicht beruehrt.** Hier entsteht keine Rangfolge von
Assets fuer den Hebel, sondern die Frage, unter welcher BEDINGUNG ein Mass
wirkt. Wo BTC/ETH/SOL landen, wird am Ende nur ABGELESEN.

    python n62_wirkung_nach_tiefe.py
"""
from __future__ import annotations

import sys

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from messe_akkumulationsmass import (VORLAUF, lade_reihen,   # noqa: E402
                                     messe)

DB, H, TIEF = "data/messdaten.db", 90, -0.40
KERN = ("BTC", "ETH", "SOL")


def tiefanteil(c: np.ndarray) -> float | None:
    """Anteil der Tage unter TIEF zum eigenen 200-Schnitt - aus der Reihe."""
    if len(c) < 200 + H + 1:
        return None
    sma = np.convolve(c, np.ones(200) / 200.0, mode="valid")
    bis = min(len(sma), len(c) - 199 - H)
    if bis <= 0:
        return None
    return float((c[199:199 + bis] / sma[:bis] - 1.0 < TIEF).mean())


def main() -> int:
    print("=" * 96)
    print("N-62 — haengt die Wirkung an der TIEFE, die ein Wert erreicht?")
    print("=" * 96)
    reihen, start, achse = lade_reihen(DB, VORLAUF + H + 60)
    anteil = {s: tiefanteil(np.asarray(reihen[s], dtype=float))
              for s in reihen}
    anteil = {s: v for s, v in anteil.items() if v is not None}
    print("  %d Reihen mit gueltigem Schichter" % len(anteil))

    ordnung = sorted(anteil, key=lambda s: anteil[s])
    k = len(ordnung) // 5
    fuenftel = [ordnung[i * k:(i + 1) * k if i < 4 else len(ordnung)]
                for i in range(5)]

    print()
    print("  1  DIE SCHICHTUNG — vor der Messung")
    print("     %-10s %7s %14s %10s" % ("Fuenftel", "Reihen", "Tiefanteil",
                                        "Bloecke ges."))
    for i, g in enumerate(fuenftel):
        tage = sum(len(reihen[s]) for s in g)
        print("     %-10s %7d  %5.1f .. %5.1f %% %10d"
              % ("%d (%s)" % (i + 1, "flachste" if i == 0 else
                              "tiefste" if i == 4 else "-"),
                 len(g), 100 * anteil[g[0]], 100 * anteil[g[-1]],
                 tage // (3 * H)))
    print("     ⚠️ Der Schichter kommt aus der Reihe selbst und sieht keine")
    print("        Zukunft - er zaehlt nur, wie oft sie tief lag.")

    print()
    print("  2  DIE MESSUNG je Fuenftel")
    print("     %-10s %-10s %10s %8s   %s"
          % ("Fuenftel", "Zustand", "Rang", "p", "Urteil"))
    erg = {}
    for i, g in enumerate(fuenftel):
        teil = {s: reihen[s] for s in g}
        st = {s: start[s] for s in g}
        for name in ("UNTER_SMA", "WOCHENTAG"):
            rng = np.random.default_rng(20260907)
            try:
                e = messe(teil, st, achse, name, H, rng)
            except Exception as exc:                         # noqa: BLE001
                print("     %-10d %-10s -> %s" % (i + 1, name, exc))
                continue
            erg[(i, name)] = e
            print("     %-10d %-10s %+9.4f %8.3f   %s"
                  % (i + 1, name, e["vorsprung"], e["p"],
                     "traegt" if e["p"] < 0.05 else "traegt nicht"),
                  flush=True)

    print()
    print("=" * 96)
    print("WAS DAS HEISST")
    print("=" * 96)
    wo = [erg.get((i, "WOCHENTAG")) for i in range(5)]
    if any(e is not None and e["p"] < 0.05 for e in wo):
        print("  ⚠️⚠️ `WOCHENTAG` traegt in einem Fuenftel - der Aufbau ist")
        print("     kaputt, alles Weitere wertlos.")
        return 1
    print("  ✔ `WOCHENTAG` traegt in keinem Fuenftel.")
    us = [erg.get((i, "UNTER_SMA")) for i in range(5)]
    traegt = [i + 1 for i, e in enumerate(us) if e is not None and e["p"] < 0.05]
    werte = [e["vorsprung"] for e in us if e is not None]
    print("  `UNTER_SMA` traegt in Fuenftel: %s"
          % (", ".join(map(str, traegt)) if traegt else "KEINEM"))
    if len(werte) == 5:
        steigt = all(werte[i] <= werte[i + 1] + 1e-9 for i in range(4))
        faellt = all(werte[i] >= werte[i + 1] - 1e-9 for i in range(4))
        print("  Verlauf: %s"
              % ("MONOTON STEIGEND - je tiefer ein Wert faellt, desto "
                 "staerker wirkt das Mass" if steigt else
                 "MONOTON FALLEND - umgekehrt" if faellt else
                 "nicht monoton - der Schichter erklaert die Wirkung NICHT"))
        if not (steigt or faellt):
            print("     ⚠️ Das REPRODUZIERT den Vorbefund "
                  "(`eigenschaften_erklaeren_den_vorsprung_nicht`) -")
            print("        es ist kein neuer Nullbefund.")
    print()
    print("  WO LIEGEN DIE KERNWERTE? — abgelesen, nicht bewertet")
    for s in KERN:
        if s not in anteil:
            print("     %-6s nicht in der Basis" % s)
            continue
        i = next(j for j, g in enumerate(fuenftel) if s in g)
        e = erg.get((i, "UNTER_SMA"))
        print("     %-6s Tiefanteil %5.1f %% -> Fuenftel %d (%s)"
              % (s, 100 * anteil[s], i + 1,
                 "dort %+.4f, p %.3f" % (e["vorsprung"], e["p"])
                 if e else "-"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
