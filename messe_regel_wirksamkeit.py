# -*- coding: utf-8 -*-
"""Die fuenf Kandidaten als REGEL, nicht als Merkmal (30.08.2026).

## Warum dieses Werkzeug

Nutzerkorrektur vom 30.08.: *"du sollst nicht alte messungen wiederholen
sondern diese auf Wirksamkeit bei praktischer Anwendung pruefen - sonst misst
du wieder nur unser System."* Bei Funding war der Unterschied Faktor 5,5:
Merkmal +0,132 R, Regel +0,024 R.

Deshalb misst dieses Werkzeug **keine Merkmale**. Es beantwortet fuer jeden
Kandidaten dieselben drei Fragen:

    WIEVIELE    Anteil der Einstiege, den die Regel sperrt
    SCHLECHTER  waren die Gesperrten wirklich die schlechteren
    NETTO       was bleibt uebrig - gepaart auf denselben Ankern

⚠️ Nur die dritte Zahl ist die Wirkung.

## Die Richtung wird VORAB festgelegt, nicht gesucht

Beide Richtungen zu pruefen verdoppelt den Suchpreis. Die Literatur gibt sie
vor - und wenn sie sich als falsch erweist, ist DAS der Befund:

  turnover    hoher Umschlag = viel Aufmerksamkeit = eher ueberbewertet
              -> OBEN sperren
  amihud      hohe Illiquiditaet = Illiquiditaetspraemie (Amihud 2002)
              -> theoretisch UNTEN sperren; praktisch sind illiquide Werte
                 kaum handelbar, deshalb wird OBEN als Gegenrichtung notiert
  momentum    hohes Momentum laeuft weiter (Jegadeesh/Titman 1993)
              -> UNTEN sperren
  funding     hohes Funding = ueberhitzt  -> OBEN sperren  (Kontrolle: der
              bereits belegte Fall, muss +0,024 R reproduzieren)

## Gegenpruefungen, die jedesmal mitlaufen

  Negativkontrolle   Rangplaetze innerhalb des Tages gemischt
  Zeitstabilitaet    beide Haelften der Historie
  Positivkontrolle   eingepflanzter Effekt - wie gross muss er sein
  Blocklaenge        Bootstrap ueber Bloecke > Horizont
"""
import statistics as st
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_bewertungskennzahl as M
import messe_eigenschaft_beitrag as B

HORIZONT = 20
GRENZE = 0.80          # 20 % werden gesperrt - wie bei Funding


def rang(werte):
    return np.argsort(np.argsort(np.asarray(werte, float))) / max(len(werte) - 1, 1)


def wirkung(je_tag, oben_sperren=True, mische=None, pflanze=0.0):
    """Je Kalendertag: Median MIT Regel minus Median OHNE."""
    aus, anteil, gesperrt, uebrig = {}, [], [], []
    for tag, z in je_tag.items():
        w = np.array([x["kennzahl"] for x in z])
        y = np.array([x["in_r"] for x in z])
        r = rang(w)
        if mische is not None:
            r = mische.permutation(r)
        frei = (r < GRENZE) if oben_sperren else (r >= 1.0 - GRENZE)
        if frei.sum() < 3 or (~frei).sum() < 1:
            continue
        # ⚠️ DIE PFLANZUNG GEHT AUF DIE GESPERRTEN, nicht auf die Behaltenen.
        # Erster Versuch (30.08.) pflanzte auf `frei` - und die machen 80 %
        # des Vergleichsmedians aus, der Effekt hob sich selbst fast auf:
        # +0,05 R gepflanzt kamen als +0,0085 an, "nicht trennbar". Eine
        # Kontrolle, die den eigenen Effekt frisst, belegt gar nichts.
        # Richtig ist die Frage: waeren die Gesperrten WIRKLICH schlechter,
        # wuerde die Regel es finden?
        y2 = y.copy()
        if pflanze:
            y2[~frei] -= pflanze
        aus[tag] = float(np.median(y2[frei]) - np.median(y2))
        anteil.append(float((~frei).mean()))
        gesperrt.append(float(np.median(y[~frei])))
        uebrig.append(float(np.median(y[frei])))
    return aus, anteil, gesperrt, uebrig


def bericht(name, je_tag, oben_sperren, rng, mit_positivkontrolle=True):
    n = sum(len(z) for z in je_tag.values())
    syms = len({x["sym"] for z in je_tag.values() for x in z})
    print()
    print("=" * 92)
    print("%s  —  REGEL: kein Einstieg im %s %d %%"
          % (name, "obersten" if oben_sperren else "untersten",
             round((1 - GRENZE) * 100)))
    print("=" * 92)
    print("  %d Anker · %d Symbole · %d Kalendertage" % (n, syms, len(je_tag)))
    d, anteil, gesperrt, uebrig = wirkung(je_tag, oben_sperren)
    if not d:
        print("  keine verwertbaren Tage")
        return
    print("  gesperrt: %.1f %%   Ertrag gesperrt %+.4f R   Ertrag uebrig %+.4f R"
          % (100 * st.mean(anteil), st.mean(gesperrt), st.mean(uebrig)))
    block = max(90, HORIZONT * 3)
    M.urteil_tage("  NETTO (die Wirkung)", d, rng, block)
    n0, _, _, _ = wirkung(je_tag, oben_sperren, mische=rng)
    M.urteil_tage("  Negativkontrolle", n0, rng, block)
    tage = sorted(d)
    mitte = tage[len(tage) // 2]
    M.urteil_tage("    erste Haelfte",
                  {t: v for t, v in d.items() if t < mitte}, rng, block)
    M.urteil_tage("    zweite Haelfte",
                  {t: v for t, v in d.items() if t >= mitte}, rng, block)
    if mit_positivkontrolle:
        for s in (0.02, 0.05):
            p, _, _, _ = wirkung(je_tag, oben_sperren, pflanze=s)
            M.urteil_tage("  Positivkontrolle %+.2f R" % s, p, rng, block)
