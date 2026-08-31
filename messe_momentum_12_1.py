# -*- coding: utf-8 -*-
"""Momentum in der STANDARDFORM: 12 Monate minus letzter Monat (30.08.2026).

## Warum diese Messung nachzuholen ist

Die Durchsicht vom 30.08. hat gezeigt: drei Messungen prueften die falsche
FORM einer Groesse. Momentum ist der vierte Fall - und der gewichtigste, denn:

    Der klassische Momentum-Faktor (Jegadeesh/Titman 1993, seither in
    praktisch jeder Anlageklasse repliziert) ist die Rendite der letzten
    ZWOELF Monate OHNE den letzten Monat.

Das Auslassen des letzten Monats ist kein Detail, sondern der Kern: kurzfristig
herrscht UMKEHR (Mean Reversion), mittelfristig Fortsetzung. Wer beides
zusammenwirft, misst die Summe zweier gegenlaeufiger Effekte - und findet
nichts.

⚠️ **Genau das haben wir getan.** Im Projekt wurde Momentum bisher nur als
20-Tage-Rendite geprueft (`messe_konjunktion.KANAELE`) - also exakt der
Monat, den die Standardform AUSLAESST.

## Die drei Formen, nebeneinander

    12_1     Kurs[t-21] / Kurs[t-252] - 1     die Standardform
    12_0     Kurs[t]    / Kurs[t-252] - 1     ohne Auslassung (Kontrolle)
    1M       Kurs[t]    / Kurs[t-21]  - 1     nur der letzte Monat (Umkehr?)

Traegt 12_1 und 12_0 nicht, ist die Auslassung der Wirkstoff. Traegt 1M mit
UMGEKEHRTEM Vorzeichen, ist die kurzfristige Umkehr belegt - und erklaert,
warum die alte 20-Tage-Messung nichts fand.

## Aufbau (unveraendert, viermal bewaehrt)

Querschnitt je Kalendertag · Fuenftel · Bewegung in R · Median ·
Bootstrap ueber Bloecke von Kalendertagen (Block > Horizont).

## Vorab festgelegt

  traegt        Bootstrap schliesst die Null nicht ein, beide Haelften
                gleiches Vorzeichen, Negativkontrolle bei null
  traegt nicht  sonst
"""
import statistics as st
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_bewertungskennzahl as M
import messe_eigenschaft_beitrag as B

FORMEN = (("12_1", 252, 21, "12 Monate OHNE den letzten (Standardform)"),
          ("12_0", 252, 0, "12 Monate MIT dem letzten (Kontrolle)"),
          ("1M", 21, 0, "nur der letzte Monat (kurzfristige Umkehr?)"))


def baue(reihen, horizont, lang, auslassen):
    je_tag = {}
    for sym, roh in reihen.items():
        tage = [z[0] for z in roh]
        c = np.array([z[1] for z in roh])
        h = np.array([z[2] for z in roh])
        t_ = np.array([z[3] for z in roh])
        breite = B.spanne(h, t_, c, B.SCHWANKUNG)
        for i in range(lang + 10, len(c) - horizont):
            r = breite[i]
            if not np.isfinite(r) or r <= 0:
                continue
            frueher = c[i - lang]
            spaeter = c[i - auslassen] if auslassen else c[i]
            if frueher <= 0 or spaeter <= 0:
                continue
            je_tag.setdefault(tage[i], []).append({
                "sym": sym,
                "kennzahl": spaeter / frueher - 1.0,
                "in_r": float((c[i + horizont] - c[i]) / r)})
    return {t: z for t, z in je_tag.items() if len(z) >= 15}


def main():
    reihen = B.lade()
    rng = np.random.default_rng(20260830)
    print("=" * 94)
    print("MOMENTUM IN DER STANDARDFORM — 12 Monate minus letzter Monat")
    print("=" * 94)
    print("⚠️ Leserichtung: HOHES Momentum minus NIEDRIGES.")
    print("   Der Faktor behauptet: hohes Momentum laeuft weiter -> positiv erwartet.")
    for horizont in (20, 60):
        print()
        print("#" * 94)
        print("HORIZONT %d HANDELSTAGE" % horizont)
        print("#" * 94)
        for name, lang, auslassen, klar in FORMEN:
            je_tag = baue(reihen, horizont, lang, auslassen)
            if not je_tag:
                continue
            n = sum(len(z) for z in je_tag.values())
            syms = len({x["sym"] for z in je_tag.values() for x in z})
            print()
            print("  %-6s %s" % (name, klar))
            print("  %d Anker, %d Symbole, %d Kalendertage" % (n, syms, len(je_tag)))
            block = max(90, horizont * 3)
            # ⚠️ Vorzeichen drehen: je_tag_quer liefert NIEDRIG minus HOCH,
            # der Faktor behauptet aber HOCH minus NIEDRIG.
            gedreht = {t: -v for t, v in M.je_tag_quer(je_tag).items()}
            M.urteil_tage("    hoch minus niedrig", gedreht, rng, block)
            M.urteil_tage("    Negativkontrolle",
                          {t: -v for t, v in M.je_tag_quer(je_tag, rng).items()},
                          rng, block)
            tage = sorted(je_tag)
            mitte = tage[len(tage) // 2]
            for titel, bed in (("davon erste Haelfte", lambda t: t < mitte),
                               ("davon zweite Haelfte", lambda t: t >= mitte)):
                teil = {t: z for t, z in je_tag.items() if bed(t)}
                M.urteil_tage("    " + titel,
                              {t: -v for t, v in M.je_tag_quer(teil).items()},
                              rng, block)


if __name__ == "__main__":
    main()
