# -*- coding: utf-8 -*-
"""Unterscheiden sich die vier Struktur-Zellen im AUSGANG? Vollauswertung.

DIE FRAGE. Die gezogene Population (baue_ankerpopulation.py) zeigt bei n = 8 je
Zelle praktisch identische Ausgaenge - 1/8, 1/8, 0/8, 1/8. Das ist zu wenig fuer
eine Aussage. Hier laufen ALLE Kandidaten, ohne einen einzigen Modellaufruf.

Beantwortet werden zwei Fragen:

    1. Traegt das Struktur-Etikett Information ueber den weiteren Verlauf?
       Wenn ja, muessten sich die Zellen unterscheiden.
    2. Wie hoch ist die Basisrate in TRENDENDEN Lagen? Die 9,4 % der gezogenen
       32 lagen unter den 22,5 % aus Abschnitt 6 - moeglicherweise, weil die
       Zellen |60-Tage| >= Schwelle verlangen und damit trendende Lagen waehlen.

WAS DIESE MESSUNG RICHTIG MACHEN MUSS, und woran frueher gescheitert wurde:

  UEBERLAPPUNG   Benachbarte Anker teilen ihr Auswertungsfenster - der 24.06.
                 und der 25.06. schauen auf fast dieselbe Zukunft. Zehntausend
                 Anker sind deshalb KEINE zehntausend Beobachtungen. Ein
                 naives Konfidenzintervall waere um ein Vielfaches zu eng
                 (Methodik 2.19.1). Hier: Cluster-Bootstrap ueber SYMBOLE -
                 gezogen werden ganze Symbole mit Zuruecklegen, nicht einzelne
                 Anker. Damit traegt die Unsicherheit die Symbolzahl, nicht
                 die Ankerzahl.
  SCHWELLE       wird NICHT gewaehlt, sondern als Kurve berichtet. Ein
                 Ergebnis, das nur bei einer Schwelle haelt, ist Rauschen.
  REFERENZREIHEN raus - wir handeln den ETC, nicht den Future (siehe
                 baue_ankerpopulation.py).
  BASISLINIE     mitgerechnet. Ohne sie sagt "22 % Zielquote" nichts.

    python messe_zellen_ausgang.py --db <pfad>
"""
from __future__ import annotations

import argparse
import random
import sys
from collections import defaultdict

import numpy as np

from agent.lagebeschreibung import FENSTER_SWING
from backtest_llm1_historisch import lade_reihen_aus_db

W = FENSTER_SWING
VORLAUF = 220
ZUKUNFT = 40
ZIEL_ATR, STOP_ATR = 3.0, 1.5
SCHWELLEN = (5.0, 10.0, 20.0, 30.0)
BOOTSTRAP = 2000
SEED = 20260811


def _fraktale(h, l):
    hi, lo = [], []
    for i in range(W, len(h) - W):
        if h[i] == h[i - W:i + W + 1].max():
            hi.append(i)
        if l[i] == l[i - W:i + W + 1].min():
            lo.append(i)
    return hi, lo


def _etiketten(h, l, n: int) -> list:
    """Etikett je Index, mit fortlaufendem Zeiger statt Neuberechnung."""
    hi_all, lo_all = _fraktale(h, l)
    aus = [None] * n
    ph = pl = 0
    for i in range(n):
        grenze = i - W
        while ph < len(hi_all) and hi_all[ph] <= grenze:
            ph += 1
        while pl < len(lo_all) and lo_all[pl] <= grenze:
            pl += 1
        if ph < 2 or pl < 2:
            continue
        hoch = h[hi_all[ph - 1]] > h[hi_all[ph - 2]]
        tief = l[lo_all[pl - 1]] > l[lo_all[pl - 2]]
        if hoch and tief:
            aus[i] = "aufwaerts"
        elif not hoch and not tief:
            aus[i] = "abwaerts"
    return aus


def _erstdurchgang(h, l, c, atr, i: int) -> str:
    """Ziel, Stop oder offen - Stop gewinnt bei Gleichstand am selben Tag."""
    a = atr[i]
    if not np.isfinite(a) or a <= 0:
        return "unbestimmt"
    ein = c[i]
    ziel, stop = ein + ZIEL_ATR * a, ein - STOP_ATR * a
    for j in range(i + 1, min(i + ZUKUNFT + 1, len(c))):
        if l[j] <= stop:
            return "STOP"
        if h[j] >= ziel:
            return "ZIEL"
    return "offen"


def main() -> int:
    import config
    from indicators.calculations import atr_wilder
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--db", default="data/tradinginfotool.db")
    args = p.parse_args()

    reihen = lade_reihen_aus_db(args.db)
    handelbar = {a.symbol for a in config.get_watchlist()}
    reihen = {s: r for s, r in reihen.items() if s in handelbar}
    print(f"{len(reihen)} handelbare Tagesreihen\n")

    # --- eine Zeile je Anker, alles ohne Modellaufruf ----------------------
    zeilen = []
    for sym, r in reihen.items():
        if len(r) < VORLAUF + ZUKUNFT + 1:
            continue
        c = np.array([k.close for k in r], dtype=float)
        h = np.array([k.high for k in r], dtype=float)
        l = np.array([k.low for k in r], dtype=float)
        atr = np.asarray(atr_wilder(h, l, c).value, dtype=float)
        et = _etiketten(h, l, len(c))
        for i in range(VORLAUF, len(c) - ZUKUNFT):
            if et[i] is None:
                continue
            zeilen.append((sym, et[i], 100.0 * (c[i] / c[i - 60] - 1.0),
                           _erstdurchgang(h, l, c, atr, i)))
    print(f"{len(zeilen)} Anker ueber {len({z[0] for z in zeilen})} Symbole\n")

    def quote(auswahl) -> float | None:
        entschieden = [z for z in auswahl if z[3] in ("ZIEL", "STOP")]
        return (100.0 * sum(1 for z in entschieden if z[3] == "ZIEL")
                / len(entschieden)) if entschieden else None

    # --- Basislinie: ALLE Anker, ohne Zellenbedingung ---------------------
    basis = quote(zeilen)
    print(f"BASISLINIE ueber alle Anker: {basis:.1f} % erreichen das Ziel")
    print(f"   (Breakeven bei 3 / 1,5 ATR liegt bei 33,3 %)\n")

    # --- Cluster-Bootstrap ueber Symbole ----------------------------------
    #
    # TEMPO, vor dem Start geprueft: Die erste Fassung zog in jeder der 2.000
    # Runden alle Rohzeilen neu (70.000 je Runde, 16 Zellen) - das haette
    # Stunden gedauert. Gebraucht werden aber nur ZWEI ZAHLEN je Symbol und
    # Zelle: wie viele Anker entschieden sind und wie viele davon das Ziel
    # erreichten. Der Bootstrap summiert dann 48 Zaehlerpaare je Runde.
    # Das Ergebnis ist identisch, die Laufzeit Sekunden statt Stunden.
    symbole = sorted({z[0] for z in zeilen})
    rng = random.Random(SEED)

    def zaehler(bedingung) -> dict:
        """(Ziel, entschieden) je Symbol - einmal, statt 2.000-mal."""
        aus = defaultdict(lambda: [0, 0])
        for sym, et, bew, erg in zeilen:
            if erg not in ("ZIEL", "STOP"):
                continue
            if not bedingung((sym, et, bew, erg)):
                continue
            aus[sym][1] += 1
            if erg == "ZIEL":
                aus[sym][0] += 1
        return aus

    def ci(bedingung) -> tuple:
        z = zaehler(bedingung)
        if not z:
            return (None, None)
        werte = []
        for _ in range(BOOTSTRAP):
            ziel = ent = 0
            for _ in range(len(symbole)):
                a, b = z.get(rng.choice(symbole), (0, 0))
                ziel += a
                ent += b
            if ent:
                werte.append(100.0 * ziel / ent)
        if not werte:
            return (None, None)
        werte.sort()
        return (werte[int(0.025 * len(werte))], werte[int(0.975 * len(werte))])

    print("ZIELQUOTE JE ZELLE, mit Cluster-Bootstrap ueber Symbole")
    print("(gezogen werden ganze Symbole - die Unsicherheit traegt die")
    print(" Symbolzahl, nicht die Ankerzahl)\n")
    print(f"{'Schwelle':>9} {'Zelle':6} {'Anker':>7} {'Ziel %':>8} "
          f"{'95 %-Intervall':>18}   Bedeutung")
    print("-" * 78)
    for s in SCHWELLEN:
        zellen = {
            "A": lambda z, s=s: z[1] == "abwaerts" and z[2] >= s,
            "B": lambda z, s=s: z[1] == "abwaerts" and z[2] <= -s,
            "C": lambda z, s=s: z[1] == "aufwaerts" and z[2] <= -s,
            "D": lambda z, s=s: z[1] == "aufwaerts" and z[2] >= s,
        }
        bedeutung = {"A": "Etikett falsch (abwaerts bei Anstieg)",
                     "B": "Etikett zu Recht",
                     "C": "Etikett falsch (aufwaerts bei Rueckgang)",
                     "D": "Etikett zu Recht"}
        for name, bed in zellen.items():
            teil = [z for z in zeilen if bed(z)]
            q = quote(teil)
            u, o = ci(bed)
            qs = f"{q:.1f}" if q is not None else "-"
            iv = f"[{u:.1f} .. {o:.1f}]" if u is not None else "-"
            print(f"{s:8.0f}% {name:6} {len(teil):7} {qs:>8} {iv:>18}   "
                  f"{bedeutung[name]}")
        print()

    print("LESART: Ueberlappen sich die Intervalle der vier Zellen, traegt das")
    print("Struktur-Etikett keine Information ueber den weiteren Verlauf - dann")
    print("war der Defekt aus 7.9 zwar echt, aber ohne Folgen fuer das Ergebnis.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
