# -*- coding: utf-8 -*-
"""Verwendung 3 — traegt H als MARKTMERKMAL? (30.08.2026)

## Warum diese Messung

Verwendung 1 (Asset-Auswahl) und 2 (Timing je Asset) sind gemessen und tragen
nicht. Alle vier bisherigen H-Zahlen erklaeren sich durch EINEN Mechanismus:

    H gegen alle Anker gepoolt        +4,5     H tritt an guten Tagen auf
    H gegen Assets desselben Tages    -0,047   innerhalb des Tages kein Vorteil
    H je Asset, roh                   +0,177   H-Tage SIND gute Markttage
    H je Asset, marktbereinigt        -0,066   ohne Markt bleibt nichts
    Tage mit viel H gegen wenig H     +0,47 R  ⚠️ hier sitzt der Effekt

Bleibt die Frage, ob der letzte Punkt ein Befund ist oder ein Artefakt.

## Die Frage, praezise

    Sagt der H-ANTEIL eines Tages die Marktbewegung der naechsten 20 Tage
    voraus - ueber das hinaus, was der Marktzustand ohnehin sagt?

⚠️ KEIN LOOKAHEAD: Der H-Anteil steht am Tag t fest, die Bewegung laeuft
t .. t+20.

## Die drei Verdachtsmomente, vorab benannt

  V1 MITLAEUFER    Ist der H-Anteil nur eine Umschreibung des Marktzustands?
                   H = "Weg frei nach oben, Boden gedeckt" - das ist nach
                   einem Anstieg haeufiger. Dann waere es Momentum in neuen
                   Kleidern, und Momentum ist geprueft (traegt nicht).
  V2 UEBERLAPPUNG  Benachbarte Tage teilen sich 19 von 20 Vorwaertstagen.
                   -> Block-Bootstrap, Bloecke > Horizont.
  V3 MONOTONIE     Der erste Blick zeigte -0,33 / -0,79 / -0,21 / -0,47 /
                   +0,15 - nur das oberste Fuenftel sticht heraus. Ein
                   Sprung an einer Stelle ist schwaecher als ein Verlauf.

## Vorab festgelegt

  traegt       Bootstrap ueber Bloecke schliesst die Null nicht ein, beide
               Haelften gleiches Vorzeichen, UND der Effekt bleibt bestehen,
               wenn man fuer Momentum kontrolliert
  traegt nicht sonst
"""
import io
import json
import statistics as st
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_bewertungskennzahl as MB

CACHE = "anker_h_2026_08_30.json"
BLOCK = 250            # > Horizont 20 (Kapitel 103.6)
MIND_ANKER = 20
ABSCHNITTE = (("2018-2020", "2018-01-01", "2020-12-31"),
              ("2021-2023", "2021-01-01", "2023-12-31"),
              ("2024-2026", "2024-01-01", "2026-12-31"))


def tagestabelle():
    """Je Kalendertag: H-Anteil, Median-Bewegung, Markt-Momentum."""
    anker = json.loads(io.open(CACHE, encoding="utf-8").read())
    je_tag = {}
    for a in anker:
        je_tag.setdefault(a["datum"], []).append(a)
    tage = sorted(t for t, z in je_tag.items() if len(z) >= MIND_ANKER)
    bewegung = {t: float(np.median([a["in_r"] for a in je_tag[t]])) for t in tage}
    anteil = {t: sum(1 for a in je_tag[t] if a["h"]) / len(je_tag[t]) for t in tage}
    # ⚠️ V1: das Markt-Momentum der letzten 20 Tage - ruecksichtsvoll
    # gerechnet, also nur aus VERGANGENEN Tagesbewegungen.
    momentum = {}
    for i, t in enumerate(tage):
        if i >= 20:
            momentum[t] = float(np.mean([bewegung[x] for x in tage[i - 20:i]]))
    return tage, anteil, bewegung, momentum


def wirkung(tage, anteil, bewegung, grenze=0.8, mische=None, rng=None,
            block=BLOCK, ziehungen=20000):
    """Hohe-H-Tage gegen niedrige - JE BLOCK gerechnet, dann gebootstrapt.

    ⚠️ ERSTE FASSUNG WAR FALSCH (30.08.2026). Sie uebergab nur die hohen Tage
    an den Bootstrap; die verteilen sich ueber wenige Bloecke, und in einem
    Zeitabschnitt blieb oft EIN Block uebrig - daher Intervalle der Breite
    null. Die Positivkontrolle fand daraufhin nicht einmal +0,40 R, und die
    Negativkontrolle lieferte fast denselben Wert wie die echte Messung.

    Richtig: In JEDEM Block wird der Unterschied zwischen hohen und niedrigen
    Tagen gebildet. Gebootstrapt werden dann diese Blockwerte.
    """
    if len(tage) < 200:
        return None
    werte = np.array([anteil[t] for t in tage])
    if mische is not None:
        werte = mische.permutation(werte)
    schwelle = float(np.quantile(werte, grenze))
    bloecke = []
    for anfang in range(0, len(tage), block):
        teil = list(zip(tage[anfang:anfang + block], werte[anfang:anfang + block]))
        hoch = [bewegung[t] for t, w in teil if w >= schwelle]
        tief = [bewegung[t] for t, w in teil if w < schwelle]
        if len(hoch) >= 10 and len(tief) >= 10:
            bloecke.append(float(np.median(hoch) - np.median(tief)))
    if len(bloecke) < 4:
        return None
    b = np.array(bloecke)
    n = len(b)
    r = rng if rng is not None else np.random.default_rng(1)
    boot = np.array([b[r.integers(0, n, n)].mean() for _ in range(ziehungen)])
    u, o = np.quantile(boot, [0.025, 0.975])
    return {"wert": float(b.mean()), "u": float(u), "o": float(o),
            "bloecke": n, "positiv": int((b > 0).sum())}


def zeige(titel, e):
    if e is None:
        print("  %-24s zu wenige Bloecke" % titel)
        return
    print("  %-24s %+.4f R  [%+.4f .. %+.4f]  %d/%d Bloecke +  %s"
          % (titel, e["wert"], e["u"], e["o"], e["positiv"], e["bloecke"],
             "TRAEGT" if e["u"] > 0 else
             ("UMGEKEHRT" if e["o"] < 0 else "nicht trennbar")))


def main():
    tage, anteil, bewegung, momentum = tagestabelle()
    rng = np.random.default_rng(20260830)
    print("=" * 94)
    print("VERWENDUNG 3 — TRAEGT H ALS MARKTMERKMAL?")
    print("=" * 94)
    print("%d Kalendertage mit mindestens %d Ankern" % (len(tage), MIND_ANKER))
    print("H-Anteil je Tag: Median %.1f %%, oberstes Fuenftel ab %.1f %%"
          % (100 * st.median(list(anteil.values())),
             100 * float(np.quantile(list(anteil.values()), 0.8))))

    print()
    print("### V3 — ist der Verlauf MONOTON? ###")
    werte = [anteil[t] for t in tage]
    grenzen = np.quantile(werte, [0, 0.2, 0.4, 0.6, 0.8, 1.0])
    vorher = None
    monoton = True
    for i in range(5):
        teil = [bewegung[t] for t in tage
                if grenzen[i] <= anteil[t] <= grenzen[i + 1]]
        m = st.median(teil)
        print("  Fuenftel %d (%4.1f .. %4.1f %%)  %5d Tage   Median %+.4f R"
              % (i, 100 * grenzen[i], 100 * grenzen[i + 1], len(teil), m))
        if vorher is not None and m < vorher - 0.05:
            monoton = False
        vorher = m
    print("  -> %s" % ("monoton steigend" if monoton
                       else "⚠️ NICHT monoton - nur ein Sprung, kein Verlauf"))

    print()
    print("### V2 — Block-Bootstrap ueber Kalendertage ###")
    for name, teil in [("gesamt", tage)] + [
            (n, [t for t in tage if v <= t <= b]) for n, v, b in ABSCHNITTE]:
        zeige(name, wirkung(teil, anteil, bewegung, rng=rng))
    mitte = tage[len(tage) // 2]
    for name, teil in (("erste Haelfte", [t for t in tage if t < mitte]),
                       ("zweite Haelfte", [t for t in tage if t >= mitte])):
        zeige(name, wirkung(teil, anteil, bewegung, rng=rng))

    print()
    print("### V1 — MITLAEUFER: ist der H-Anteil nur Markt-Momentum? ###")
    gemeinsam = [t for t in tage if t in momentum]
    a = np.array([anteil[t] for t in gemeinsam])
    m = np.array([momentum[t] for t in gemeinsam])
    print("  Korrelation H-Anteil <-> Momentum der letzten 20 Tage: %+.3f"
          % float(np.corrcoef(a, m)[0, 1]))
    print("  Der Test: H-Anteil INNERHALB gleicher Momentum-Schicht")
    r = np.argsort(np.argsort(m)) / max(len(m) - 1, 1)
    for schicht, name in ((0, "schwaches Momentum"), (1, "mittleres"),
                          (2, "starkes")):
        teil = [t for t, q in zip(gemeinsam, r)
                if schicht / 3 <= q < (schicht + 1) / 3]
        zeige("  " + name, wirkung(teil, anteil, bewegung, rng=rng,
                                    block=120))

    print()
    print("### NEGATIVKONTROLLE — H-Anteil ueber die Tage gemischt ###")
    zeige("gemischt", wirkung(tage, anteil, bewegung, mische=rng, rng=rng))

    print()
    print("### POSITIVKONTROLLE — welche Effektgroesse waere sichtbar? ###")
    for staerke in (0.05, 0.10, 0.20, 0.40):
        schwelle = float(np.quantile([anteil[t] for t in tage], 0.8))
        gepflanzt = {t: bewegung[t] + (staerke if anteil[t] >= schwelle else 0.0)
                     for t in tage}
        zeige("gepflanzt %+.2f R" % staerke,
              wirkung(tage, anteil, gepflanzt, rng=rng))


if __name__ == "__main__":
    main()
