# -*- coding: utf-8 -*-
"""QUOTE oder KRITERIUM? Wie viele kommen durch, und wie gut sind sie?

⚠️ DIE NUTZERKRITIK, DIE DAS AUSGELOEST HAT (23.08.2026):

    "Aus hunderten von Signalen pro Tag wird nun 1 oder 0, und die Auswahl
     wird auf 2 Coins festbetoniert - fuer eine Zeit? Ohne Ruecksicht auf
     Strategie und Bestand? ... Meine Vorstellung ist: die zu handelnden
     Assets werden laufend gemessen, ALLE, und selektiv sollen jene Coins zum
     Zug kommen, welche das hoechste POTENTIAL aufweisen. Warum werden 2 Coins
     fuer x Stunden gewaehlt - ist der falsche Grund. Korrekt waere: weil aus
     aktueller Sicht jener Coin mit dieser Strategie das hoechste Potential
     hat."

ER HAT RECHT, UND DER FEHLER IST BENENNBAR. Ich habe eine QUOTE gebaut ("die
besten 2 passieren") und im selben Dokument vorher aufgeschrieben, dass genau
das die versteckteste Annahme ist: eine Rangliste hat IMMER einen Sieger.

    QUOTE       genau k passieren - auch wenn keiner taugt, und der Dritte
                bleibt draussen, auch wenn er genauso gut ist.
    KRITERIUM   wer die Bedingung erfuellt, passiert - null, wenn keiner sie
                erfuellt, fuenf, wenn fuenf sie erfuellen.

⚠️ UND DIE ZEITBINDUNG IST DER ZWEITE FEHLER. Ein Wert kommt heute durch, weil
er heute vorn liegt - nicht, weil er vor drei Stunden gewaehlt wurde. Der
Cooldown darf die Wiederholung derselben FRAGE bremsen, nicht die AUSWAHL
festhalten.

WAS HIER GEMESSEN WIRD - fuenf Verfahren auf denselben Terminen:

    quote_1     Rang 1                          (feste Zahl)
    quote_2     Rang 1 und 2                    (feste Zahl - der Ist-Stand)
    kriterium_median   eigene 250-Tage-Rendite ueber dem Gruppenmedian
    kriterium_positiv  ... und zusaetzlich absolut positiv
    kriterium_fuenftel oberstes Fuenftel und absolut positiv

Fuer jedes: WIE VIELE kommen im Schnitt durch, WIE OFT kommt keiner durch, und
was die Gewaehlten ueber den Horizont gebracht haetten - barrierenfrei und
brutto, Kosten daneben.

⚠️ DIE ENTSCHEIDENDE SPALTE IST "keiner". Ein Kriterium, das an 80 % der Tage
niemanden durchlaesst, ist kein Filter mehr, sondern eine Sperre - und dann
waere die Sorge des Nutzers berechtigt.
"""
from __future__ import annotations

import argparse

import numpy as np

from messe_drift import _newey_west, _reihen, _tafel

RUECKBLICK = 250
HORIZONTE = (5, 20)
MIND_SYMBOLE = 10
VERFAHREN = ("quote_1", "quote_2", "kriterium_median", "kriterium_positiv",
             "kriterium_fuenftel")


def waehlt(rueck: np.ndarray, art: str) -> np.ndarray:
    """Bool-Maske: wer passiert? Nur aus der Vergangenheit."""
    n = len(rueck)
    ordnung = np.argsort(-rueck)
    maske = np.zeros(n, dtype=bool)
    if art == "quote_1":
        maske[ordnung[:1]] = True
    elif art == "quote_2":
        maske[ordnung[:2]] = True
    elif art == "kriterium_median":
        maske = rueck > float(np.median(rueck))
    elif art == "kriterium_positiv":
        maske = (rueck > float(np.median(rueck))) & (rueck > 0)
    elif art == "kriterium_fuenftel":
        grenze = float(np.percentile(rueck, 80))
        maske = (rueck >= grenze) & (rueck > 0)
    else:
        raise ValueError(art)
    return maske


def lauf(tafel, horizont: int, art: str) -> dict:
    _n, T = tafel.shape
    je_termin, anzahl, leer, markt = [], [], 0, []
    for t in range(RUECKBLICK, T - horizont):
        gut = (~np.isnan(tafel[:, t]) & ~np.isnan(tafel[:, t - RUECKBLICK])
               & ~np.isnan(tafel[:, t + horizont]))
        if gut.sum() < MIND_SYMBOLE:
            continue
        rueck = tafel[:, t][gut] / tafel[:, t - RUECKBLICK][gut] - 1.0
        vor = tafel[:, t + horizont][gut] / tafel[:, t][gut] - 1.0
        if not (np.all(np.isfinite(rueck)) and np.all(np.isfinite(vor))):
            continue
        m = waehlt(rueck, art)
        anzahl.append(int(m.sum()))
        markt.append(float(np.mean(vor)))
        if not m.any():
            leer += 1
            continue
        je_termin.append(float(np.mean(vor[m])))
    if len(je_termin) < 30:
        return {}
    a = np.array(je_termin)
    mk = np.array(markt[:len(a)]) if len(markt) >= len(a) else np.array(markt)
    n = min(len(a), len(mk))
    abstand = a[:n] - mk[:n]
    se = _newey_west(abstand, max(1, len(abstand) // 400))
    return {"termine": len(anzahl), "leer": leer,
            "im_schnitt": float(np.mean(anzahl)),
            "hoechstens": int(np.max(anzahl)),
            "rendite": float(a.mean()), "markt": float(mk.mean()),
            "abstand": float(abstand.mean()),
            "t": float(abstand.mean() / se) if se > 0 else float("nan")}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--db", default="data/tradinginfotool.db")
    p.add_argument("--klasse", default="krypto")
    args = p.parse_args()

    reihen = _reihen(args.db, args.klasse)
    termine, tafel, symbole = _tafel(reihen)
    print(f"{args.klasse}: {len(symbole)} Symbole · {termine[0]} bis "
          f"{termine[-1]}\nMass: Vorwaertsrendite, barrierenfrei und brutto. "
          f"'keiner' = Termine ohne jede Auswahl.\n")
    for h in HORIZONTE:
        print(f"=== Horizont {h} Handelstage ===")
        print(f"{'Verfahren':20} {'Termine':>8} {'keiner':>7} {'im Schnitt':>11} "
              f"{'max':>5} {'Auswahl':>9} {'Markt':>9} {'Abstand':>9} {'t':>7}")
        for art in VERFAHREN:
            e = lauf(tafel, h, art)
            if not e:
                print(f"{art:20} {'zu wenige Termine':>30}")
                continue
            print(f"{art:20} {e['termine']:8} "
                  f"{100*e['leer']/e['termine']:6.0f}% {e['im_schnitt']:11.1f} "
                  f"{e['hoechstens']:5} {100*e['rendite']:8.2f}% "
                  f"{100*e['markt']:8.2f}% {100*e['abstand']:8.2f}% "
                  f"{e['t']:7.2f}")
        print()
    print("⚠️ Eine QUOTE laesst immer genau k durch - auch wenn keiner taugt.\n"
          "   Ein KRITERIUM laesst durch, wer die Bedingung erfuellt - und "
          "niemanden,\n   wenn sie niemand erfuellt. Die Spalte 'keiner' ist "
          "der Preis dafuer.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
