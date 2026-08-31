# -*- coding: utf-8 -*-
"""Gegenpruefung zu K-2 — zwei Verdachtsmomente in der eigenen Messung.

## Verdacht 1: der Bootstrap ist kaputt

In der Aufwaerts-Auswertung lag der Punktschaetzer AUSSERHALB seines eigenen
95-%-Intervalls (-0,0356 gegen [-0,1917 .. -0,1708]). Das ist unmoeglich,
wenn der Bootstrap stimmt.

Ursache-Verdacht: `bootstrap()` mittelt die BLOCKMITTEL ungewichtet. Bei
gleich langen Bloecken ist das dasselbe wie das Gesamtmittel - aber die
Phasenfilter (steigend/fallend) zerreiszen die Bloecke, und dann haben sie
sehr verschiedene Laengen. Das Mittel der Blockmittel ist dann NICHT das
Gesamtmittel.

## Verdacht 2: der Befund ist ein Ausreiszer

"OHNE ZIEL +1,52 R gegen ZIEL 2,0 +0,036 R" waere Faktor 42. Bei Horizont 60
liegt der groeszte Einzelwert bei +6.870 R. Ein Mittelwert, den ein einzelner
Anker traegt, ist keine Erwartung.

Geprueft wird deshalb:
  - wieviel Prozent des Mittelwerts stammen aus dem obersten 1 % / 0,1 %
  - wie sieht der Vergleich mit GETRIMMTEM Mittel aus (oberste 1 % weg)
  - wie sieht er auf der Ebene aus, die praktisch zaehlt: je Reihe
"""
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_eigenschaft_beitrag as B
import messe_zielregel as Z


def main():
    reihen = B.lade()
    zeilen = Z.ergebnisse(reihen)
    print("=" * 84)
    print("GEGENPRUEFUNG ZU K-2")
    print("=" * 84)

    # ---- Verdacht 1 -----------------------------------------------------
    print()
    print("VERDACHT 1 — mittelt der Bootstrap korrekt?")
    for name in ("ZIEL 2,0", "OHNE ZIEL"):
        for titel, teil in (("alle", zeilen),
                            ("nur aufwaerts", [z for z in zeilen if z["steigend"]])):
            w = np.array([z[name] for z in teil])
            bl = Z.bloecke_bilden(teil, name)
            laengen = np.array([len(b) for b in bl])
            mittel_der_bloecke = float(np.mean([b.mean() for b in bl]))
            print("  %-10s %-14s Gesamtmittel %+8.4f   Mittel der Blockmittel %+8.4f   %s"
                  % (name, titel, w.mean(), mittel_der_bloecke,
                     "OK" if abs(w.mean() - mittel_der_bloecke) < 0.01 else "ABWEICHUNG"))
            print("  %-25s Bloecke: %d, Laenge min %d / median %d / max %d"
                  % ("", len(bl), laengen.min(), int(np.median(laengen)), laengen.max()))

    # ---- Verdacht 2 -----------------------------------------------------
    print()
    print("VERDACHT 2 — traegt ein Ausreiszer den Befund?")
    print("  %-11s %10s %10s %10s %10s %10s"
          % ("Variante", "Mittel", "getrimmt", "Median", "Top-1 %", "groesster"))
    for name, _ in Z.VARIANTEN:
        w = np.array([z[name] for z in zeilen])
        s = np.sort(w)
        k = max(1, len(s) // 100)
        getrimmt = s[:-k].mean()
        anteil_top1 = 100.0 * s[-k:].sum() / s.sum() if s.sum() != 0 else float("nan")
        print("  %-11s %+10.4f %+10.4f %+10.4f %9.1f %% %10.1f"
              % (name, w.mean(), getrimmt, np.median(w), anteil_top1, s[-1]))

    # ---- die Ebene, die praktisch zaehlt --------------------------------
    print()
    print("JE REIHE — wieviele Reihen profitieren wirklich vom Weglassen des Ziels?")
    je_reihe = {}
    for z in zeilen:
        je_reihe.setdefault(z["sym"], []).append(z["OHNE ZIEL"] - z["ZIEL 2,0"])
    mittel = {s: float(np.mean(v)) for s, v in je_reihe.items()}
    med = {s: float(np.median(v)) for s, v in je_reihe.items()}
    pos_m = sum(1 for v in mittel.values() if v > 0)
    pos_med = sum(1 for v in med.values() if v > 0)
    print("  nach MITTEL  : %d von %d Reihen positiv (%.0f %%)"
          % (pos_m, len(mittel), 100 * pos_m / len(mittel)))
    print("  nach MEDIAN  : %d von %d Reihen positiv (%.0f %%)"
          % (pos_med, len(med), 100 * pos_med / len(med)))
    beste = sorted(mittel.items(), key=lambda x: -x[1])[:5]
    print("  staerkste Reihen: %s"
          % ", ".join("%s %+.1f" % (s, v) for s, v in beste))
    ohne_top = [v for s, v in mittel.items() if s not in dict(beste)]
    print("  Mittel ueber die Reihen: %+.4f R   ohne die fuenf staerksten: %+.4f R"
          % (float(np.mean(list(mittel.values()))), float(np.mean(ohne_top))))
    print("  MEDIAN ueber die Reihen: %+.4f R   <- die robuste Zahl"
          % float(np.median(list(mittel.values()))))


if __name__ == "__main__":
    main()
