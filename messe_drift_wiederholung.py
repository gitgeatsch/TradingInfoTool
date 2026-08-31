# -*- coding: utf-8 -*-
"""S2 wiederholt: gibt es eine DRIFT? (29.08.2026)

## Warum diese Wiederholung

Der Kernbefund des Projekts ist arithmetisch: *ein Barrierensystem auf einem
driftfreien Pfad hat brutto Erwartungswert NULL - fuer JEDE Geometrie.* Genau
drei Wege koennen das Vorzeichen drehen: **Drift**, **Nachrichten**, **Kosten**.
Kosten sind vom Zielbild ausgeschlossen (Regel 2). Nachrichten sammeln noch.
Bleibt die Drift.

Am 11.08. gemessen - trug nicht. ABER:

  1. gemessen in EINER Marktphase (Baermarkt); seit dem 22.08. ist die Phase
     eine andere
  2. BTC hatte damals EIN Jahr Historie, seit dem 19.08. sind es neun
  3. die Messung lief gegen die Watchlist (~26 verwertbare Reihen), nicht
     gegen `messdaten.db` (523 Reihen, 485 davon >= 500 Handelstage)

## Was hier gemessen wird

    Ist die Bewegung ueber H Tage systematisch von null verschieden - und
    zwar so, dass sie die Barrierengeometrie ins Plus drehen kann?

Gemessen in **R** (an der eigenen Schwankungsbreite normiert), weil nur das
die Frage beantwortet: eine Drift in Prozent nuetzt nichts, wenn der Stop
mitwaechst.

## ⚠️ DIE EHRLICHE EINHEIT IST DIE MARKTEPISODE (Methodik 2.84 + Kapitel 103.8)

523 Reihen sind keine 523 Ziehungen - Krypto laeuft synchron. Die Kontrolle
ist deshalb ein **Block-Bootstrap**: ganze Zeitbloecke von 250 Handelstagen,
Grenzen wandern je Lauf (Kapitel 103.7 - bei festen Grenzen reisen immer
dieselben Anker gemeinsam und die Verteilung wird zu schmal).

## Vorab festgelegt, VOR dem Lauf

  traegt        Median-Bewegung in R ungleich null gegen die Blockprobe,
                UND in beiden Marktphasen dasselbe Vorzeichen
  traegt nicht  von null nicht zu trennen
  ⚠️ nur eine Phase -> KEIN Befund, sondern die Wiederholung des Fehlers
     von 2026-08-11 mit anderem Vorzeichen
"""
import statistics as st
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_eigenschaft_beitrag as B

BLOCK = 250
LAEUFE = 40


def anker(reihen, horizont):
    """Je Reihe: Bewegung in R, Phase, Position in der Zeit."""
    aus = []
    for sym, zeilen in reihen.items():
        tage = [z[0] for z in zeilen]
        schluss = np.array([z[1] for z in zeilen])
        hoch = np.array([z[2] for z in zeilen])
        tief = np.array([z[3] for z in zeilen])
        breite = B.spanne(hoch, tief, schluss, B.SCHWANKUNG)
        for i in range(200, len(schluss) - horizont):
            if not np.isfinite(breite[i]) or breite[i] <= 0:
                continue
            schnitt = schluss[i - 200:i].mean()
            if schnitt <= 0:
                continue
            aus.append({
                "sym": sym, "tag": tage[i], "i": i,
                "in_r": float((schluss[i + horizont] - schluss[i]) / breite[i]),
                "steigend": bool(schluss[i] > schnitt)})
    return aus


def blockprobe(werte, lagen, rng):
    """Verschiebt ganze Zeitbloecke zirkulaer - Grenzen wandern je Lauf."""
    aus = []
    for _ in range(LAEUFE):
        versatz = int(rng.integers(0, BLOCK))
        gedreht = []
        for w, i in zip(werte, lagen):
            # Blocknummer mit wanderndem Anfang, dann Vorzeichen des Blocks
            # zufaellig drehen - das ist die Nullhypothese "keine Richtung"
            b = (i + versatz) // BLOCK
            gedreht.append(w * (1 if (b * 2654435761 + versatz) % 2 else -1))
        aus.append(st.median(gedreht))
    return aus


def urteil(name, werte, lagen, rng):
    if len(werte) < 100:
        print("    %-30s zu wenige Anker" % name)
        return
    m = st.median(werte)
    null = blockprobe(werte, lagen, rng)
    unten, oben = np.quantile(null, [0.025, 0.975])
    haelt = m < unten or m > oben
    print("    %-30s Median %+.4f R   Blockprobe [%+.4f .. %+.4f]   %s"
          % (name, m, unten, oben, "✔ traegt" if haelt else "⚠️ traegt nicht"))
    print("    %-30s (%d Anker, %d Bloecke, %d Laeufe)"
          % ("", len(werte), max(lagen) // BLOCK + 1, LAEUFE))


def main():
    reihen = B.lade()
    print("=" * 84)
    print("S2 WIEDERHOLT — GIBT ES EINE DRIFT?  (523 Reihen, %d Handelstage je Block)"
          % BLOCK)
    print("=" * 84)
    rng = np.random.default_rng(20260829)
    for horizont in (5, 20, 60):
        a = anker(reihen, horizont)
        print()
        print("HORIZONT %d Handelstage — %d Anker" % (horizont, len(a)))
        for name, teil in (("ALLE Lagen", a),
                           ("Kurs UEBER dem Schnitt", [x for x in a if x["steigend"]]),
                           ("Kurs UNTER dem Schnitt", [x for x in a if not x["steigend"]])):
            urteil(name, [x["in_r"] for x in teil], [x["i"] for x in teil], rng)


if __name__ == "__main__":
    main()
