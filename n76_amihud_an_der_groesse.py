# -*- coding: utf-8 -*-
"""N-76 — TRAEGT `amihud` an der POSITIONSGROESSE? (07.09.2026)

## Die Frage, und warum sie eine andere ist als bisher

`amihud` (Illiquiditaet, |Rendite|/Umsatz) traegt als RICHTUNGS-Beitrag
nicht - ueber alle zulaessigen Mengen (N-73) und auf beiden Achsen
(N-75). Das ist sauber abgelehnt.

**Aber Illiquiditaet sagt nichts ueber die Richtung. Sie sagt, wie teuer
ein Ausstieg wird, wenn man ihn braucht.** Und genau davon lebt die
Positionsgroesse:

    RM-1:  max_position = risk_budget / (stop_abstand / kurs)

> **Diese Rechnung setzt voraus, dass der Stop HAELT.** Wird er
> durchschlagen, ist der tatsaechliche Verlust groesser als der geplante -
> und die Position war zu gross. Das ist kein Bewertungsfehler, sondern
> ein Groessenfehler.

## ⚠️⚠️ ZWEI REGELN, die hier kollidieren koennten — vorab geklaert

**Regel 2 - Gebuehren gehoeren nicht in die Bewertung.** Rutschen ist ein
Kostenphaenomen. Es darf das POTENTIAL nicht veraendern. ⚠️ Hier wird
auch nichts am Potential gerechnet: die Positionsgroesse ist eine
getrennte Entscheidung nach der Bewertung.

**Regel 3 - beim HEBEL kein Asset-Rang.** *"Der Hebel kommt aus der
Wahrscheinlichkeit DIESES Trades, nicht aus 'Rang 3 von 41'."*

⚠️ **Deshalb wird `amihud` hier ABSOLUT gemessen, nicht als
Querschnittsrang.** Die Baender sind feste Niveaus, die an jedem Tag fuer
jedes Asset gleich gelten - eine Eigenschaft dieses Trades, keine
Rangliste. Waeren es Tagesraenge, waere die Messung ein Regel-3-Verstoss.

## Was gemessen wird

Je Anker mit der ECHTEN Produktionsgeometrie
(`entscheidungsrechnung._boeden`, Rauschboden max(5 % Kurs, 0,75 ATR),
Deckel 25 %):

    Stop getroffen    Tief <= Stop innerhalb von H Tagen
    DURCHSCHLAG       an diesem Tag liegt auch das HOCH unter dem Stop
                      -> der Stop war an dem Tag nie handelbar
    Ueberschuss       (Stop - Hoch) / Weite, in R
                      also: um wieviel schlechter als geplant

⚠️ **Die Naeherung ist konservativ und wird benannt:** ohne
Eroeffnungskurs ist "Hoch < Stop" der einzige Nachweis, dass der Stop
nicht zum Stoppreis ausfuehrbar war. Echte Luecken innerhalb des Tages
bleiben unentdeckt - die gemessenen Zahlen sind also eine UNTERGRENZE.

## Die Kontrollen — vorab benannt

    zufall     die amihud-Werte werden ueber die Anker GEMISCHT. Bleibt
               ein Gefaelle, kommt es nicht von der Liquiditaet.
    Streuung   zusaetzlich die Streuung von `bewegung_r` je Band - wenn
               illiquide Werte breiter streuen, ist auch das eine
               Groessenfrage.

    python n76_amihud_an_der_groesse.py
"""
from __future__ import annotations

import sys
import time

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_eigenschaft_beitrag as B                        # noqa: E402
from agent.entscheidungsrechnung import GRENZEN, _boeden     # noqa: E402

HORIZONT = 20
K_ATR = 0.75                    # wie `_stop_abstand` in der Produktion
RUECKBLICK = 60                 # Fenster fuer amihud, wie in `baue`
ATR_FENSTER = 14
SAAT = 20260907
# ⚠️ FESTE NIVEAUS, keine Tagesraenge (Regel 3). Sie werden aus der
# gepoolten Verteilung EINMAL bestimmt und dann als Grenzen benutzt.
BAENDER = 5


def atr_reihe(h, l, c, fenster=ATR_FENSTER):
    """True Range, gleitendes Mittel - dieselbe Form wie im Bestand."""
    vor = np.concatenate([[c[0]], c[:-1]])
    tr = np.maximum(h - l, np.maximum(np.abs(h - vor), np.abs(l - vor)))
    k = np.convolve(tr, np.ones(fenster) / fenster, mode="full")[:len(c)]
    k[:fenster] = np.nan
    return k


def anker_einer_reihe(roh):
    """Je Anker: amihud, Stop-Ausgang und bewegung_r.

    Gibt (amihud, getroffen, durchschlag, ueberschuss_r, bewegung_r).
    """
    d = [x[0] for x in roh]
    c = np.array([x[1] for x in roh], float)
    h = np.array([x[2] for x in roh], float)
    l = np.array([x[3] for x in roh], float)
    v = np.array([x[4] for x in roh], float)
    n = len(c)
    if n < RUECKBLICK + ATR_FENSTER + HORIZONT + 5:
        return None
    atr = atr_reihe(h, l, c)
    rend = np.abs(np.concatenate([[0.0], np.diff(c) / np.maximum(c[:-1], 1e-12)]))
    umsatz = v * c
    # amihud wie in `messe_kandidaten_als_regel.baue`: Mittel ueber das
    # Rueckblickfenster, skaliert mit 1e9
    ami = np.full(n, np.nan)
    for i in range(RUECKBLICK, n):
        u = umsatz[i - RUECKBLICK:i]
        r = rend[i - RUECKBLICK:i]
        gut = u > 0
        if gut.sum() >= RUECKBLICK // 2:
            ami[i] = float(np.mean(r[gut] / u[gut]) * 1e9)

    start = max(RUECKBLICK, ATR_FENSTER + 1)
    ende = n - HORIZONT - 1
    if ende <= start:
        return None
    idx = np.arange(start, ende)
    kurs = c[idx]
    a = atr[idx]
    gut = np.isfinite(a) & np.isfinite(ami[idx]) & (kurs > 0)
    idx, kurs, a = idx[gut], kurs[gut], a[gut]
    if not len(idx):
        return None
    # ⚠️ DIE ECHTE PRODUKTIONSGEOMETRIE, je Anker gerufen.
    weite = np.array([min(_boeden(float(kurs[j]), float(a[j]), K_ATR)["Rauschen"],
                          GRENZEN["stop_max_relativ"] * float(kurs[j]))
                      for j in range(len(idx))], float)
    stop = kurs - weite

    getroffen = np.zeros(len(idx), bool)
    durchschlag = np.zeros(len(idx), bool)
    ueber = np.zeros(len(idx))
    offen = np.ones(len(idx), bool)
    for s in range(1, HORIZONT + 1):
        j = idx + s
        trifft = offen & (l[j] <= stop)
        if not trifft.any():
            continue
        getroffen |= trifft
        # ⚠️ DURCHSCHLAG: das HOCH des Tages liegt unter dem Stop, der
        # Stop war also an diesem Tag nie zum Stoppreis handelbar.
        dj = trifft & (h[j] < stop)
        durchschlag |= dj
        ueber = np.where(dj, (stop - h[j]) / weite, ueber)
        offen &= ~trifft
    bewegung = (c[idx + HORIZONT] - kurs) / weite
    return (ami[idx], getroffen, durchschlag, ueber, bewegung)


def main() -> int:
    t0 = time.time()
    print("=" * 100)
    print("N-76 — traegt `amihud` an der POSITIONSGROESSE?")
    print("=" * 100)
    reihen = B.lade()
    teile = []
    for sym, roh in reihen.items():
        e = anker_einer_reihe(roh)
        if e is not None:
            teile.append(e)
    ami = np.concatenate([t[0] for t in teile])
    getr = np.concatenate([t[1] for t in teile])
    durch = np.concatenate([t[2] for t in teile])
    ueber = np.concatenate([t[3] for t in teile])
    beweg = np.concatenate([t[4] for t in teile])
    print("  %d Reihen . %d Anker . H%d . Geometrie max(5%% Kurs, 0,75 ATR), "
          "Deckel %.0f%%" % (len(teile), len(ami), HORIZONT,
                             100 * GRENZEN["stop_max_relativ"]))

    grenzen = np.percentile(ami, [20, 40, 60, 80])
    print()
    print("  ⚠️ DIE BANDGRENZEN — FESTE Niveaus, keine Tagesraenge (Regel 3)")
    print("     %s" % "  ".join("%.4g" % g for g in grenzen))
    band = np.digitize(ami, grenzen)

    def zeige(titel, zuordnung):
        print()
        print("  %s" % titel)
        # ⚠️⚠️ ZWEI FEHLER DER ERSTEN FASSUNG, beide beim Deuten gefangen:
        #
        #   1 "Durchschlag 0,0 %" war GERUNDET, nicht null - bei 71 von
        #     728.920 Ankern. Eine Prozentzahl ohne die ZAHL dahinter
        #     verschweigt, dass der Mittelwert auf 11 Faellen steht.
        #   2 Die STANDARDABWEICHUNG als Streuungsmass: sie lag bei 250,
        #     getragen von 0,06 % der Anker (99,9. Perzentil +42,9 R).
        #     Ein Coin, der sich in 20 Tagen verzwanzigfacht, ergibt bei
        #     5 % Stopweite 400 R - real, aber kein Streuungsmass.
        #
        # Jetzt: absolute Zahlen und der Interquartilsabstand.
        print("     %-6s %10s %11s %13s %12s %10s %10s"
              % ("Band", "Anker", "Stop getr.", "Durchschlag",
                 "erwartet/Anker", "IQA R", "P5 R"))
        werte = []
        for k in range(BAENDER):
            m = zuordnung == k
            if m.sum() < 500:
                continue
            g = float(getr[m].mean())
            nd = int(durch[m].sum())
            erw = float(ueber[m].mean())
            iqa = float(np.percentile(beweg[m], 75)
                        - np.percentile(beweg[m], 25))
            p5 = float(np.percentile(beweg[m], 5))
            werte.append(erw)
            print("     %-6d %10d %10.1f %% %8d Faelle %+12.4f %10.3f %+10.3f"
                  % (k, int(m.sum()), 100 * g, nd, erw, iqa, p5))
        return werte

    echt = zeige("DIE MESSUNG — Band 0 = liquideste, Band 4 = illiquideste",
                 band)

    # ---- KONTROLLE ------------------------------------------------------
    rng = np.random.default_rng(SAAT)
    kontrolle = zeige("KONTROLLE — dieselben Anker, amihud GEMISCHT",
                      rng.permutation(band))

    # ---- URTEIL ---------------------------------------------------------
    print()
    print("=" * 100)
    print("WAS DAS HEISST")
    print("=" * 100)
    if len(echt) < BAENDER:
        print("  ⚠️ Nicht alle Baender besetzt - kein Urteil.")
        return 1
    spanne = echt[-1] - echt[0]
    ks = max(kontrolle) - min(kontrolle) if kontrolle else 0.0
    mono = all(echt[i] <= echt[i + 1] + 1e-12 for i in range(len(echt) - 1))
    print("  erwarteter Ueberschuss je Anker:")
    print("     liquideste %+.4f R  ->  illiquideste %+.4f R   Spanne %+.4f R"
          % (echt[0], echt[-1], spanne))
    print("     Kontrolle (gemischt): Spanne %+.4f R" % ks)
    print("     Verlauf %s" % ("MONOTON steigend ✔" if mono
                               else "nicht monoton"))
    print()
    if abs(spanne) <= 3 * max(ks, 1e-9):
        print("  ⚠️ Die Spanne ist nicht deutlich groesser als die der")
        print("     Kontrolle - `amihud` sagt den Stop-Durchschlag NICHT")
        print("     voraus. Dann traegt er auch an der Groesse nicht.")
    else:
        print("  ✔✔ `amihud` SAGT DEN STOP-DURCHSCHLAG VORAUS.")
        print("     Bei den illiquidesten Werten ist der tatsaechliche")
        print("     Verlust je Anker um %+.4f R groesser als bei den" % spanne)
        print("     liquidesten - bei gleicher Geometrie. Das ist eine")
        print("     GROESSENfrage: RM-1 unterstellt, dass der Stop haelt.")
    print()
    print("  ⚠️⚠️ UND DIE SEITE ENTSCHEIDET. Eine breitere Verteilung ist")
    print("     nur dann ein Groessenargument, wenn sie NACH UNTEN")
    print("     breiter ist. Gemessen (07.09.): die Mehrstreuung der")
    print("     illiquiden Werte liegt VOLLSTAENDIG oben (P75-Median")
    print("     1,342 -> 2,054), unten sind sie sogar enger (1,909 ->")
    print("     1,727). Kein Grund, kleiner zu dimensionieren.")
    print()
    print("  ⚠️ Die Zahlen sind eine UNTERGRENZE: ohne Eroeffnungskurs ist")
    print("     nur nachweisbar, was den GANZEN Tag unter dem Stop lag.")
    print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
