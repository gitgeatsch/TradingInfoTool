# -*- coding: utf-8 -*-
"""V-0 / N-7 KORRIGIERT: Traegt die heutige Rollen-Kette?

Die erste Fassung (messe_n7_kette.py) hatte einen Konstruktionsfehler:
der Zufallsarm zog aus der GANZEN Reihe (2017-2026), waehrend die Kette
nur Tage im August 2026 waehlte. Der Signalzeitraum war um +0,704 Punkte
besser als der Schnitt -- damit war der Vorsprung groesstenteils Zeitraum.

Diese Fassung zieht jede Kontrolle aus DEMSELBEN Fenster und trennt
zusaetzlich zwei Quellen, die die erste Fassung vermischt hat:

  KALENDERTAG   traf die Kette gute Tage?   -> gemeinsam ueber alle Symbole
  ASSET         traf sie das richtige Asset am Tag?

Der zweite Teil ist der eigentliche Nachweis: er haelt den Kalendertag
exakt fest, indem er die eigenen Signaltage gegen die Signaltage ALLER
anderen Symbole im selben Fenster stellt.

Vorab festgelegt am 29.08.2026, vor dem Lauf:
  Kette schlaegt Zufall UND Regel     -> die Kette traegt, V-1..V-6 sinnvoll
  Kette schlaegt den Zufall NICHT     -> eine Bewertungsstufe filtert
                                         Rauschen nach Rauschen; V-1..V-6
                                         auszusetzen, bis die Kette traegt
"""
import statistics as st
import sys

import numpy as np

import messe_n7_kette as M

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

VON, BIS = "2026-08-14", "2026-08-26"


def lade():
    reihen = M.lade_reihen("data/messdaten.db")
    je = {}
    for symbol, tag in M.lade_signale(M.NB_EXPORT):
        if symbol in reihen:
            je.setdefault(symbol, set()).add(tag)
    return reihen, je


def fenster(reihen, symbol, horizont):
    """Tage im Messfenster, die noch `horizont` Folgetage haben."""
    daten, kurse = reihen[symbol]
    bewegung = M.bewegung(kurse, horizont)
    lagen = [i for i, d in enumerate(daten[:len(bewegung)]) if VON <= d <= BIS]
    return daten, bewegung, lagen


def messe(reihen, je, horizont):
    rng = np.random.default_rng(20260829)
    symbole = sorted(je)
    eigen, fremd, zufall = [], [], []
    for symbol in symbole:
        daten, bewegung, lagen = fenster(reihen, symbol, horizont)
        if len(lagen) < 4:
            continue
        gewaehlt = [i for i in lagen if daten[i] in je[symbol]]
        if not 2 <= len(gewaehlt) < len(lagen):
            continue          # ohne Auswahl kein Vergleich
        rang = M.rang(bewegung[lagen])
        platz = {t: i for i, t in enumerate(lagen)}
        eigen.append(float(rang[[platz[t] for t in gewaehlt]].mean()) - 0.5)
        zufall.append(float(np.mean([
            float(rang[rng.choice(len(rang), len(gewaehlt), replace=False)].mean()) - 0.5
            for _ in range(200)])))
        andere = []
        for f in symbole:
            if f == symbol:
                continue
            tage = [platz[t] for t in lagen if daten[t] in je[f]]
            if 2 <= len(tage) < len(lagen):
                andere.append(float(rang[tage].mean()) - 0.5)
        fremd.append(st.mean(andere) if andere else None)
    return eigen, fremd, zufall


def t_wert(werte):
    if len(werte) < 2:
        return 0.0
    streuung = st.stdev(werte)
    return st.mean(werte) / (streuung / len(werte) ** 0.5) if streuung else 0.0


def main():
    reihen, je = lade()
    print("=" * 74)
    print("V-0 / N-7 KORRIGIERT -- Fenster %s .. %s" % (VON, BIS))
    print("=" * 74)
    for horizont in (1, 2):
        eigen, fremd, zufall = messe(reihen, je, horizont)
        if not eigen:
            continue
        gegen_zufall = [a - b for a, b in zip(eigen, zufall)]
        paare = [(a, b) for a, b in zip(eigen, fremd) if b is not None]
        gegen_fremd = [a - b for a, b in paare]
        print()
        print("HORIZONT %d Tag(e) -- %d Symbole" % (horizont, len(eigen)))
        print("  eigene Signaltage        %+.4f" % st.mean(eigen))
        print("  quotengleicher Zufall    %+.4f   (gleiches Fenster)" % st.mean(zufall))
        print("    Unterschied            %+.4f   t = %+.2f"
              % (st.mean(gegen_zufall), t_wert(gegen_zufall)))
        print("  fremde Signaltage        %+.4f   (Signaltage der ANDEREN Symbole)"
              % st.mean([b for _, b in paare]))
        print("    ASSET-EIGENER Anteil   %+.4f   t = %+.2f   %d von %d positiv"
              % (st.mean(gegen_fremd), t_wert(gegen_fremd),
                 sum(1 for x in gegen_fremd if x > 0), len(gegen_fremd)))
    print()
    print("Deutung: der Unterschied gegen den Zufall sitzt im KALENDERTAG,")
    print("den alle Symbole teilen. Der asset-eigene Anteil ist der Nachweis --")
    print("nur er haelt den Tag fest.")


if __name__ == "__main__":
    main()
