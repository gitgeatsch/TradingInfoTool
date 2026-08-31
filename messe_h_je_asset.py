# -*- coding: utf-8 -*-
"""H als ZEITPUNKT-Merkmal je Asset — Verwendung 2 (30.08.2026)

## Die drei Verwendungen, und warum nur diese hier offen war

    1  ASSET-AUSWAHL   "welches Asset heute?"
                       H-Asset gegen andere Assets DESSELBEN Tages
                       -> gemessen: -0,047 im eigenen Mass, negativ

    2  TIMING JE ASSET "ist heute ein guter Tag fuer BTC?"
                       H-Tage von BTC gegen Nicht-H-Tage von BTC
                       -> ⚠️ DIESE MESSUNG. Nie gemacht - weder hier noch in
                          den Kapiteln 108-122

    3  MARKT-TIMING    "ist heute ein guter Tag ueberhaupt?"
                       Tage mit vielen H gegen Tage mit wenigen
                       -> Hinweis: +0,47 R, nicht monoton, ungeprueft

## ⚠️ WARUM DIE MARKTBEREINIGUNG HIER ENTSCHEIDET

H hat einen belegten TAGES-Effekt: an Tagen mit vielen H-Ankern bewegt sich
der Markt besser. Eine rohe Je-Asset-Messung wuerde diesen Tages-Effekt
mitzaehlen und H gut aussehen lassen, obwohl es nur den Markt beschreibt.

    ROH             H-Tage gegen Nicht-H-Tage desselben Symbols
    MARKTBEREINIGT  dasselbe, nachdem von jedem Anker der Median ALLER
                    Anker desselben Kalendertags abgezogen wurde

⚠️ Genau dieser Test hat bei Funding entschieden: roh +0,169 R, marktbereinigt
-0,076 R - dort war es Markt-Timing. Traegt H auch marktbereinigt, ist es
etwas anderes als der Tages-Effekt.

## Vorab festgelegt, VOR der ersten Zahl

  traegt asset-eigen   MARKTBEREINIGT von null zu trennen (Bootstrap ueber
                       die Symbole), beide Historienhaelften gleiches
                       Vorzeichen, Positivkontrolle bestanden
  nur Markt-Timing     nur die rohe Variante traegt
  traegt nicht         keine von beiden
"""
import io
import json
import statistics as st
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CACHE = "anker_h_2026_08_30.json"
MIND_JE_GRUPPE = 30      # H-Tage und Nicht-H-Tage je Symbol
ZIEHUNGEN = 20000


def lade():
    anker = json.loads(io.open(CACHE, encoding="utf-8").read())
    # Markt = Median aller Anker desselben Kalendertags
    je_tag = {}
    for a in anker:
        je_tag.setdefault(a["datum"], []).append(a)
    markt_r, markt_ziel = {}, {}
    for tag, z in je_tag.items():
        markt_r[tag] = float(np.median([a["in_r"] for a in z]))
        mit = [a["ziel"] for a in z if a["ziel"] is not None]
        if mit:
            markt_ziel[tag] = float(np.mean(mit))
    return anker, markt_r, markt_ziel


def je_symbol(anker, markt, feld, bereinigt):
    """Je Symbol: Mittel(H-Tage) minus Mittel(Nicht-H-Tage)."""
    gruppen = {}
    for a in anker:
        w = a.get(feld)
        if w is None:
            continue
        if bereinigt:
            m = markt.get(a["datum"])
            if m is None:
                continue
            w = w - m
        gruppen.setdefault(a["sym"], ([], []))[0 if a["h"] else 1].append(w)
    aus = {}
    for sym, (mit_h, ohne_h) in gruppen.items():
        if len(mit_h) >= MIND_JE_GRUPPE and len(ohne_h) >= MIND_JE_GRUPPE:
            # Median: robust gegen die Schiefe von 2,68
            aus[sym] = st.median(mit_h) - st.median(ohne_h)
    return aus


def urteil(titel, werte, rng):
    if len(werte) < 10:
        print("    %-34s zu wenige Symbole (%d)" % (titel, len(werte)))
        return None
    w = np.array(list(werte.values()))
    n = len(w)
    boot = np.array([w[rng.integers(0, n, n)].mean() for _ in range(ZIEHUNGEN)])
    u, o = np.quantile(boot, [0.025, 0.975])
    traegt = u > 0
    print("    %-34s %+.4f  [%+.4f .. %+.4f]  %3d/%3d Symbole +  %s"
          % (titel, w.mean(), u, o, int((w > 0).sum()), n,
             "TRAEGT" if traegt else ("UMGEKEHRT" if o < 0 else "nicht trennbar")))
    return traegt


def main():
    anker, markt_r, markt_ziel = lade()
    rng = np.random.default_rng(20260830)
    n_h = sum(1 for a in anker if a["h"])
    print("=" * 94)
    print("VERWENDUNG 2 — TRAEGT H ALS ZEITPUNKT-MERKMAL JE ASSET?")
    print("=" * 94)
    print("%d Anker, davon %d mit H (%.1f %%)" % (len(anker), n_h,
                                                  100 * n_h / len(anker)))
    print("Gelesen: H-Tage MINUS Nicht-H-Tage desselben Symbols, Median je Gruppe.")
    print("Mindestens %d Anker je Gruppe, sonst faellt das Symbol heraus."
          % MIND_JE_GRUPPE)

    for feld, markt, klar in (("in_r", markt_r, "BEWEGUNG IN R"),
                              ("ziel", markt_ziel, "ZIEL VOR STOP (H's eigenes Mass)")):
        print()
        print("-" * 94)
        print("  %s" % klar)
        print("-" * 94)
        roh = je_symbol(anker, markt, feld, False)
        ber = je_symbol(anker, markt, feld, True)
        urteil("roh (Markt NICHT kontrolliert)", roh, rng)
        urteil("⚠️ marktbereinigt (entscheidend)", ber, rng)

        # Zeitstabilitaet der bereinigten Variante
        mitte = sorted({a["datum"] for a in anker})[len(
            {a["datum"] for a in anker}) // 2]
        for name, bed in (("davon erste Haelfte", lambda d: d < mitte),
                          ("davon zweite Haelfte", lambda d: d >= mitte)):
            teil = [a for a in anker if bed(a["datum"])]
            urteil(name, je_symbol(teil, markt, feld, True), rng)

    # ---- POSITIVKONTROLLE ----
    print()
    print("-" * 94)
    print("  POSITIVKONTROLLE — welche Effektgroesse findet diese Messung?")
    print("-" * 94)
    for staerke in (0.05, 0.10, 0.20, 0.40):
        gepflanzt = [{**a, "in_r": a["in_r"] + (staerke if a["h"] else 0.0)}
                     for a in anker]
        urteil("gepflanzt %+.2f R auf H-Tage" % staerke,
               je_symbol(gepflanzt, markt_r, "in_r", True), rng)

    # ---- NEGATIVKONTROLLE ----
    print()
    print("-" * 94)
    print("  NEGATIVKONTROLLE — H je Symbol zufaellig vertauscht")
    print("-" * 94)
    gemischt = []
    je_sym = {}
    for a in anker:
        je_sym.setdefault(a["sym"], []).append(a)
    for sym, z in je_sym.items():
        marken = rng.permutation([a["h"] for a in z])
        for a, h in zip(z, marken):
            gemischt.append({**a, "h": bool(h)})
    urteil("gemischt (muss bei null liegen)",
           je_symbol(gemischt, markt_r, "in_r", True), rng)


if __name__ == "__main__":
    main()
