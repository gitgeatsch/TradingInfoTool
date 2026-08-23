# -*- coding: utf-8 -*-
"""Trennt die Umkehr-Bedingung die Assets AM SELBEN TAG? (23.08.2026)

⚠️ DIE NUTZERKRITIK, DIE DIESES WERKZEUG AUSGELOEST HAT:

    "Der Nullbefund ist kein Tausch, sondern ein IST-Zustand, der sofort
     geaendert werden muss. Wir messen immer im breiten Bereich und die
     Signale kommen im breiten Bereich - HYPE zehnmal kaufen am Tag, LINK
     zehnmal - aber nie selektiv auf Assetebene. Der HANDEL passiert aber auf
     Assetebene. Das ist der Auftrag und das Ziel."

UND ER HAT RECHT - AUCH GEGEN MEINE EIGENE MESSUNG. Der Vorsprung gegen den
quotengleichen Zufall haelt das SYMBOL FEST und wuerfelt nur die Tage. Diese
Bauform kann eine Auswahl UNTER Symbolen gar nicht finden:

    gemessen wurde   "WANN kaufe ich innerhalb eines Wertes"
    gebraucht wird   "WELCHEN Wert kaufe ich heute"

Der Nullbefund auf Assetebene war deshalb zum Teil eine Eigenschaft des
Messaufbaus, nicht des Marktes. Das gehoert benannt und nicht weggeredet.

DIE RICHTIGE BAUFORM STEHT SEIT DEM 19.08. IM PROJEKT: `messe_drift.py` misst
eine RANGLISTE QUER UEBER DIE SYMBOLE AM SELBEN TAG. Sie wurde nur nie auf die
Umkehr angewandt, sondern nur auf Momentum.

    Nicht: "Krypto faellt"          - das ist keine Auswahl.
    Sondern: "DIESE fuenf stehen tiefer unter ihrem Schnitt als JENE fuenf"
             - das ist eine.

ZWEI MERKMALE, VORAB BENANNT - beide sind die Bedingung, die am 23.08.
innerhalb der Symbole getragen hat:

    unter_sma    Kurs / 200-Tage-Schnitt - 1     (je negativer, desto tiefer)
    rueckgang    1 - Kurs / Hoch der letzten 252 Tage

DAS ERFOLGSMASS IST DAS POTENTIAL, nicht die Zielerreichung (Nutzervorgabe
23.08.): die Vorwaertsrendite ueber einen FESTEN Horizont, barrierenfrei und
brutto. Kein Stop, kein Ziel, keine Kostenhuerde davor - die Kosten stehen
DANEBEN, damit sichtbar bleibt, was uebrig bliebe.

⚠️ SIGNIFIKANZ UEBER TERMINE, NICHT UEBER ANKER: an einem Tag bewegt sich
alles gemeinsam. Gerechnet wird je Termin EINE Zahl - der Abstand zwischen
bestem und schlechtestem Fuenftel - und der t-Wert ueber die Termine, mit
Newey-West gegen die Ueberlappung. Beides uebernommen aus `messe_drift`, damit
die Zahlen vergleichbar sind.

⚠️ UND DIE SCHWELLE KOMMT AUS DEM PLACEBO, nicht aus der Tabelle: `--placebo N`
zerwuerfelt die Rangliste. Was dann noch anschlaegt, ist der Fehler der
Methode. Fuer `messe_drift` lag die empirische Schwelle bei |t| >= 3,05 - die
Tabellenschwelle waere zu milde gewesen.
"""
from __future__ import annotations

import argparse

import numpy as np

from messe_drift import _newey_west, _reihen, _tafel

MERKMALE = ("unter_sma", "rueckgang")
HORIZONTE = (5, 20, 60)
SMA = 200
HOCH_FENSTER = 252
MIND_SYMBOLE = 10
FUENFTEL = 5


def merkmal(tafel, t: int, gut, art: str):
    """Der Wert, nach dem sortiert wird - nur aus der Vergangenheit."""
    jetzt = tafel[:, t][gut]
    if art == "unter_sma":
        fenster = tafel[:, t - SMA + 1:t + 1][gut]
        schnitt = np.nanmean(fenster, axis=1)
        return jetzt / schnitt - 1.0
    fenster = tafel[:, t - HOCH_FENSTER + 1:t + 1][gut]
    return -(1.0 - jetzt / np.nanmax(fenster, axis=1))


def messe(tafel, art: str, horizont: int, rng=None) -> dict:
    """Abstand zwischen tiefstem und hoechstem Fuenftel, je Termin."""
    n, T = tafel.shape
    vorlauf = max(SMA, HOCH_FENSTER)
    abstaende, tief, hoch = [], [], []
    for t in range(vorlauf, T - horizont):
        gut = (~np.isnan(tafel[:, t]) & ~np.isnan(tafel[:, t - vorlauf + 1])
               & ~np.isnan(tafel[:, t + horizont]))
        if gut.sum() < MIND_SYMBOLE:
            continue
        w = merkmal(tafel, t, gut, art)
        vor = tafel[:, t + horizont][gut] / tafel[:, t][gut] - 1.0
        if not np.all(np.isfinite(w)) or not np.all(np.isfinite(vor)):
            continue
        ordnung = np.argsort(w)                 # aufsteigend: tiefster zuerst
        if rng is not None:
            rng.shuffle(ordnung)                # PLACEBO
        k = max(1, len(ordnung) // FUENFTEL)
        u = float(np.mean(vor[ordnung[:k]]))    # am tiefsten unter dem Schnitt
        o = float(np.mean(vor[ordnung[-k:]]))   # am hoechsten darueber
        tief.append(u)
        hoch.append(o)
        abstaende.append(u - o)
    if len(abstaende) < 30:
        return {}
    a = np.array(abstaende)
    se = _newey_west(a, horizont)
    return {"termine": len(a), "abstand": float(a.mean()),
            "t": float(a.mean() / se) if se > 0 else float("nan"),
            "tief": float(np.mean(tief)), "hoch": float(np.mean(hoch))}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--db", default="data/tradinginfotool.db")
    p.add_argument("--klasse", default="krypto")
    p.add_argument("--placebo", type=int, default=0)
    p.add_argument("--kosten", type=float, default=3.0,
                   help="Handelskosten in Prozent, nur zum Danebenstellen")
    args = p.parse_args()

    reihen = _reihen(args.db, args.klasse)
    termine, tafel, symbole = _tafel(reihen)
    print(f"{args.klasse}: {len(symbole)} Symbole · {len(termine)} Tage "
          f"({termine[0]} bis {termine[-1]})")
    print(f"Mass: Vorwaertsrendite ueber einen festen Horizont - "
          f"barrierenfrei und BRUTTO. Kosten {args.kosten:.1f} % daneben.\n")

    print(f"{'Merkmal':12} {'Horizont':>8} {'Termine':>8} {'tiefstes':>10} "
          f"{'hoechstes':>10} {'Abstand':>9} {'t':>7}")
    ergebnisse = {}
    for art in MERKMALE:
        for h in HORIZONTE:
            e = messe(tafel, art, h)
            if not e:
                print(f"{art:12} {h:8} {'zu wenige Termine':>28}")
                continue
            ergebnisse[(art, h)] = e
            traegt = "  <-- ueber den Kosten" if (
                100 * e["abstand"] >= args.kosten and e["t"] >= 3.05) else ""
            print(f"{art:12} {h:8} {e['termine']:8} "
                  f"{100*e['tief']:9.2f}% {100*e['hoch']:9.2f}% "
                  f"{100*e['abstand']:8.2f}% {e['t']:7.2f}{traegt}")

    if args.placebo:
        print(f"\nPLACEBO - {args.placebo} Laeufe mit zerwuerfelter Rangliste")
        rng = np.random.RandomState(20260823)
        werte = []
        for i in range(args.placebo):
            for art in MERKMALE:
                for h in HORIZONTE:
                    e = messe(tafel, art, h, rng=rng)
                    if e:
                        werte.append(abs(e["t"]))
        if werte:
            werte = np.array(werte)
            print(f"   {len(werte)} Felder · |t| >= 2,0 in "
                  f"{100*np.mean(werte >= 2.0):.1f} % (erwartet ~5 %) · "
                  f"groesster {werte.max():.2f} · 95. Perzentil "
                  f"{np.percentile(werte, 95):.2f}")
            print("   ⚠️ Die empirische Schwelle ist das 95. Perzentil, "
                  "nicht der Tabellenwert.")

    print("\n⚠️ Das tiefste Fuenftel ist die UMKEHR-Wette: am weitesten unter "
          "dem eigenen Schnitt\n   bzw. am tiefsten unter dem Jahreshoch. Ein "
          "positiver Abstand heisst, es holt auf.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
