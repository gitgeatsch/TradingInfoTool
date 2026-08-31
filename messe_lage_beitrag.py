# -*- coding: utf-8 -*-
"""G-2': Traegt die LAGE des Assets als Einzeltrade-Beitrag? (29.08.2026)

**Warum dieser Lauf noetig ist, obwohl die Tagewahl "schon gemessen" war:**
Sie wurde ueber Zwei- und Einjahresfenster einer AKKUMULATION mit festen
Betraegen gemessen - Endwert je Fenster, nicht Ertrag je Trade, und im Memory
ausdruecklich "keine Signifikanzaussage". Fuer einen Bewertungsbeitrag brauchen
wir die andere Form:

    Bewegt sich ein Asset, das TIEF steht, aus dieser Lage heraus staerker
    als eines, das HOCH steht - am selben Tag, unter derselben Marktlage?

## Die zwei Lagemerkmale, beide STETIG (nie als Schalter - G4)

  abstand_schnitt   Kurs / 200-Tage-Schnitt - 1     "wie tief unter dem Schnitt"
  rueckgang         Kurs / Jahreshoch - 1           "wie weit unter dem Hoch"

⚠️ Beide sind Aussagen ueber die LAGE zum Bewertungszeitpunkt, nicht ueber das
Asset. Genau die Kategorie, die in allen bisherigen Messungen als einzige
getragen hat (sieben Eigenschaften: null; drei Lagemerkmale: alle drei).

## Die Zielgroesze - und die GESCHWINDIGKEIT

  in_r      Bewegung ueber H Tage / eigene Schwankungsbreite
  je_tag    dasselbe geteilt durch H            <- Entscheidung "c" vom 29.08.

Drei Horizonte (5/20/60) beantworten damit zugleich, WIE SCHNELL die Bewegung
kommt: traegt das Merkmal nur auf 60 Tage, ist es fuer Hebel wertlos.

## Vorab festgelegt, VOR dem Lauf (Methodik 2.58.1)

  traegt        Unterschied oberstes/unterstes Fuenftel in R als MEDIAN
                ungleich null, Vorzeichen ueber die Horizonte stabil,
                Negativkontrolle bei null
  traegt nicht  Median-Unterschied nicht von null zu trennen
  ⚠️ Verworfen wird auch bei nachweisbarem Rangzusammenhang, wenn der
     Median-Unterschied null ist - die Lehre aus dem Volumen-Lauf.
"""
import statistics as st
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_eigenschaft_beitrag as B

SCHNITT = 200
HOCH = 252
MIND_ASSETS = 15


def baue(reihen, horizont):
    je_tag = {}
    for sym, zeilen in reihen.items():
        tage = [z[0] for z in zeilen]
        schluss = np.array([z[1] for z in zeilen])
        hoch = np.array([z[2] for z in zeilen])
        tief = np.array([z[3] for z in zeilen])
        breite = B.spanne(hoch, tief, schluss, B.SCHWANKUNG)
        for i in range(max(SCHNITT, HOCH), len(schluss) - horizont):
            if not np.isfinite(breite[i]) or breite[i] <= 0:
                continue
            schnitt = schluss[i - SCHNITT:i].mean()
            jahreshoch = hoch[i - HOCH:i].max()
            if schnitt <= 0 or jahreshoch <= 0:
                continue
            weg = schluss[i + horizont] - schluss[i]
            je_tag.setdefault(tage[i], []).append({
                "abstand_schnitt": float(schluss[i] / schnitt - 1.0),
                "rueckgang": float(schluss[i] / jahreshoch - 1.0),
                "in_r": float(weg / breite[i]),
                "je_tag": float(weg / breite[i] / horizont)})
    return {t: z for t, z in je_tag.items() if len(z) >= MIND_ASSETS}


def fuenftel(je_tag, tage, merkmal, ziel, mische=False, rng=None):
    """Median des untersten gegen oberstes Fuenftel - je Kalendertag."""
    aus = []
    for tag in tage:
        z = je_tag[tag]
        if len(z) < 20:
            continue
        r = B.rang([x[merkmal] for x in z])
        if mische:
            r = rng.permutation(r)
        tief = [x[ziel] for x, q in zip(z, r) if q <= 0.2]
        hoch = [x[ziel] for x, q in zip(z, r) if q >= 0.8]
        if tief and hoch:
            aus.append(st.median(tief) - st.median(hoch))   # TIEF minus HOCH
    return aus


def urteil(name, werte, einheit="R"):
    if len(werte) < 2:
        print("    %-38s zu wenige Tage" % name)
        return
    m, sd = st.mean(werte), st.stdev(werte)
    t = m / (sd / len(werte) ** 0.5) if sd else 0.0
    pos = sum(1 for x in werte if x > 0)
    print("    %-38s %+.4f %-5s t = %+5.2f   %3d von %3d Tagen positiv (%.0f %%)"
          % (name, m, einheit, t, pos, len(werte), 100 * pos / len(werte)))


def main():
    reihen = B.lade()
    print("=" * 82)
    print("G-2' — TRAEGT DIE LAGE ALS EINZELTRADE-BEITRAG?")
    print("=" * 82)
    print("523 Reihen · Merkmale STETIG · Rangplatz quer je Kalendertag")
    print("Gelesen wird: TIEF stehende Assets minus HOCH stehende.")
    print("Ein POSITIVER Wert heiszt: tief stehen war besser.")
    rng = np.random.default_rng(20260829)
    for horizont in (5, 20, 60):
        je_tag = baue(reihen, horizont)
        if not je_tag:
            continue
        ohne = sorted(je_tag)[::horizont]      # keine ueberlappenden Anker
        print()
        print("-" * 82)
        print("HORIZONT %d Handelstage — %d nicht ueberlappende Anker"
              % (horizont, len(ohne)))
        print("-" * 82)
        for merkmal, klar in (("abstand_schnitt", "ABSTAND ZUM 200-TAGE-SCHNITT"),
                              ("rueckgang", "RUECKGANG VOM JAHRESHOCH")):
            print("  %s" % klar)
            urteil("Bewegung in R", fuenftel(je_tag, ohne, merkmal, "in_r"))
            urteil("⚠️ je Tag  (Entscheidung c)",
                   fuenftel(je_tag, ohne, merkmal, "je_tag"), "R/T")
            urteil("Negativkontrolle (gemischt)",
                   fuenftel(je_tag, ohne, merkmal, "in_r", True, rng))
            print()


if __name__ == "__main__":
    main()
