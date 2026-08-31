# -*- coding: utf-8 -*-
"""WIRKSAMKEIT statt Merkmalsmessung (30.08.2026).

## Die Nutzerkorrektur, die dieses Werkzeug ausgeloest hat

    *"du sollst nicht alte messungen wiederholen sondern diese auf Wirksamkeit
    bei praktischer Anwendung pruefen - halte dich daran sonst misst du wieder
    nur unser System."*

⚠️ Sie trifft. Alle Messungen dieser Serie fragten: *traegt das Merkmal in
MEINEM Aufbau?* - Querschnitt, Terzile, Median in R, Horizont 20. Das ist
mein Messrahmen, nicht die Anwendung. Der Befund "+0,132 R zwischen unterstem
und oberstem Fuenftel" beantwortet NICHT, was eine Regel bewirkt.

## Was hier stattdessen gefragt wird

    Wenn wir eine REGEL anwenden - "nimm keinen Einstieg, dessen Funding
    heute im obersten Fuenftel des Marktes liegt" - was aendert das?

Drei Zahlen, und nur die dritte ist die Wirkung:

    WIEVIELE   Anteil der Einstiege, die die Regel verhindert
    WAREN SIE SCHLECHTER   Ertrag der verhinderten gegen die uebrigen
    NETTO      Ertrag MIT Regel minus Ertrag OHNE - auf denselben Ankern

⚠️ Die dritte Zahl ist typischerweise VIEL kleiner als der Merkmalsbefund.
Eine Regel, die 20 % der Faelle sperrt, kann hoechstens 20 % des Unterschieds
heben - und nur, wenn die gesperrten wirklich die schlechteren waren.

## Und die Regel wird als GANZE gerechnet, nicht als Terzilvergleich

Kein Median zweier Extremgruppen, sondern: alle Einstiege, wie sie im Betrieb
anfielen, einmal mit und einmal ohne Regel. Gepaart auf denselben Ankern -
es gibt keine Zuordnung, die eine Permutation zerstoeren koennte, also
Bootstrap (Methodik 2.55).

## Vorab festgelegt

  wirksam        Netto-Unterschied positiv, Bootstrap ueber Bloecke von
                 Kalendertagen schliesst die Null nicht ein, beide Haelften
                 gleiches Vorzeichen
  nicht wirksam  sonst
  ⚠️ Auch ein wirksamer Befund ist erst dann eine Empfehlung, wenn die
     GROESSE ihn rechtfertigt - eine Regel, die 20 % der Signale kostet und
     +0,01 R bringt, ist keine Verbesserung.
"""
import statistics as st
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_bewertungskennzahl as M
import messe_eigenschaft_beitrag as B
import messe_funding_niveau as F

HORIZONT = 20
SPERREN = (0.80, 0.90)          # ab welchem Rangplatz gesperrt wird


def anker(reihen, funding):
    """Alle Einstiege mit Funding-Rangplatz des Tages."""
    je_tag = {}
    for sym, roh in reihen.items():
        f = funding.get(sym.upper())
        if not f:
            continue
        tage = [z[0] for z in roh]
        c = np.array([z[1] for z in roh])
        h = np.array([z[2] for z in roh])
        t_ = np.array([z[3] for z in roh])
        breite = B.spanne(h, t_, c, B.SCHWANKUNG)
        for i in range(60, len(c) - HORIZONT):
            r = breite[i]
            if not np.isfinite(r) or r <= 0 or tage[i] not in f:
                continue
            je_tag.setdefault(tage[i], []).append(
                {"sym": sym, "funding": f[tage[i]],
                 "in_r": float((c[i + HORIZONT] - c[i]) / r)})
    return {t: z for t, z in je_tag.items() if len(z) >= 10}


def wirkung(je_tag, grenze):
    """Je Kalendertag: Ertrag MIT Regel minus OHNE, plus Sperrquote."""
    differenz, gesperrt_anteil, gesperrt_ertrag, uebrig_ertrag = {}, [], [], []
    for tag, z in je_tag.items():
        w = np.array([x["funding"] for x in z])
        y = np.array([x["in_r"] for x in z])
        rang = np.argsort(np.argsort(w)) / max(len(w) - 1, 1)
        frei = rang < grenze
        if frei.sum() < 3 or (~frei).sum() < 1:
            continue
        differenz[tag] = float(np.median(y[frei]) - np.median(y))
        gesperrt_anteil.append(float((~frei).mean()))
        gesperrt_ertrag.append(float(np.median(y[~frei])))
        uebrig_ertrag.append(float(np.median(y[frei])))
    return differenz, gesperrt_anteil, gesperrt_ertrag, uebrig_ertrag


def main():
    reihen = B.lade()
    funding = F.lade_funding()
    je_tag = anker(reihen, funding)
    rng = np.random.default_rng(20260830)
    n = sum(len(z) for z in je_tag.values())
    print("=" * 90)
    print("WIRKSAMKEIT DER FUNDING-REGEL — was aendert sie an echten Einstiegen?")
    print("=" * 90)
    print("%d Anker, %d Kalendertage, Horizont %d" % (n, len(je_tag), HORIZONT))
    print()
    for grenze in SPERREN:
        d, anteil, gesperrt, uebrig = wirkung(je_tag, grenze)
        print("-" * 90)
        print("REGEL: kein Einstieg ab Funding-Rangplatz %.0f %%" % (grenze * 100))
        print("-" * 90)
        print("  wieviele werden gesperrt      %.1f %% der Einstiege"
              % (100 * st.mean(anteil)))
        print("  Ertrag der GESPERRTEN         %+.4f R (Median je Tag)"
              % st.mean(gesperrt))
        print("  Ertrag der UEBRIGEN           %+.4f R" % st.mean(uebrig))
        M.urteil_tage("  NETTO mit Regel minus ohne", d, rng, 90)
        tage = sorted(d)
        mitte = tage[len(tage) // 2]
        M.urteil_tage("    davon erste Haelfte",
                      {t: v for t, v in d.items() if t < mitte}, rng, 90)
        M.urteil_tage("    davon zweite Haelfte",
                      {t: v for t, v in d.items() if t >= mitte}, rng, 90)
        print()


if __name__ == "__main__":
    main()
