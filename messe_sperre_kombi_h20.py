# -*- coding: utf-8 -*-
"""Wuerde `funding_extrem` die LIVE terminmarkt-Sperre verbessern? (04.09.2026)

## Wo das herkommt

F-206 hat `oi_aenderung`+`funding_extrem` auf **H2/Frontloading** gemessen -
der Geometrie der Hebel-Wegwahl (`messe_form_kurz_gegen_lang.py`). Das ist
NICHT dieselbe Frage wie die hier gestellte: die `terminmarkt`-Sperre
(`agent/rollen_gate.py` Stufe 9, N-14) ist die **live laufende** Stufe, und
sie ist auf **H20/R** kalibriert (F-168, `messe_kandidaten_als_regel.py`).
Ein Kombinationsbefund auf H2/Frontloading uebertraegt sich nicht
automatisch auf H20/R - das waere derselbe Fehler wie N-17a's ausgangs-
punkt (Beitraege auf H20 kalibriert, Hebeltrade laeuft H2).

Diese Datei stellt die Frage NEU, auf der Geometrie der Sperre, die sie
tatsaechlich betrifft.

## Zwei Richtungen, nicht eine

    LOCKERN   sperre nur, wer in BEIDEN obersten Fuenfteln liegt (oi UND
              funding_extrem) - weniger Sperren, mehr Durchlass
    VERSCHAERFEN  sperre, wer in EINEM der beiden liegt (oi ODER
              funding_extrem) - mehr Sperren, weniger Durchlass

F-206s Reinheits-Befund (AND = reiner) beantwortet nicht, welche Richtung
hier traegt - das ist eine andere Zielgroesse. Beide werden gemessen.

## Vorab festgelegt

  traegt     Wirkung > 0, Band ausserhalb Null, UND besser als der Status
             quo (oi allein, F-168: +0,0145 R [+0,0097 .. +0,0193])
  traegt nicht   sonst - dann bleibt die Sperre unveraendert

## Kein Selbsttest mit synthetischen Daten

Diese Datei rechnet mit denselben, bereits validierten Bausteinen wie
F-168 (`messe_kandidaten_als_regel.baue/geschichtet`) und F-206
(`messe_form_kurz_gegen_lang.baue` fuer `funding_extrem`, NICHT neu
gerechnet - siehe unten). Statt eines synthetischen Selbsttests dient die
Reproduktion von F-168s Zahl (+0,0145 R) als Positivkontrolle: weicht sie
ab, ist etwas an der Zusammenfuehrung falsch, nicht am Befund.

    python messe_sperre_kombi_h20.py
"""
from __future__ import annotations

import statistics as st
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_bewertungskennzahl as M
import messe_eigenschaft_beitrag as B
import messe_form_kurz_gegen_lang as FL
import messe_kandidaten_als_regel as K
import messe_regel_wirksamkeit as W

HORIZONT = 20
BLOCK = max(90, HORIZONT * 3)


def _funding_extrem_zusatz(reihen: dict) -> dict:
    """`funding_extrem` je Symbol/Tag - AUS DER ECHTEN FUNKTION geholt.

    ⚠️ Keine Neuberechnung. `messe_form_kurz_gegen_lang.baue()` ist die
    Stelle, an der `funding_extrem` (nachlaufender Median/MAD-Abstand,
    kein Lookahead) tatsaechlich entsteht und die F-206 gemessen hat. Eine
    zweite, eigene Rechnung waere genau der Fehler aus G-b/F-206
    (`_reinheit` hatte die Auswahl selbst nachgebaut) ein drittes Mal.
    """
    aus = FL.lade_zusatz()
    je_tag = FL.baue(reihen, aus)
    zusatz: dict = {}
    for tag, zeilen in je_tag.items():
        for e in zeilen:
            fe = e.get("funding_extrem")
            if fe is None:
                continue
            zusatz.setdefault(e["sym"].upper(), {})[tag] = fe
    return zusatz


def main():
    reihen = B.lade()
    rng = np.random.default_rng(20260904)

    print("#" * 92)
    print("# TRAEGT `funding_extrem` DIE LIVE terminmarkt-SPERRE (Stufe 9, N-14)?")
    print("#" * 92)
    print("  Basis: %d Krypto-Symbole (messe_eigenschaft_beitrag.lade, "
          "F-204-gefiltert)" % len(reihen))

    tm = K.lade_terminmarkt()
    fe_zusatz = _funding_extrem_zusatz(reihen)
    print("  `funding_extrem` ueber die ECHTE Funktion gewonnen: %d Symbole"
          % len(fe_zusatz))

    oi_je_tag = K.baue(reihen, "oi_aenderung", tm["oi_aenderung"], horizont=HORIZONT)
    fe_je_tag = K.baue(reihen, "funding", fe_zusatz, horizont=HORIZONT)

    print()
    print("=" * 92)
    print("POSITIVKONTROLLE — reproduziert diese Zusammenfuehrung F-168?")
    print("=" * 92)
    W.bericht("A  oi_aenderung (Reproduktion von F-168)", oi_je_tag,
              True, rng, mit_positivkontrolle=True)
    d_a, *_ = W.wirkung(oi_je_tag, True)
    wirkung_a = st.mean(d_a.values()) if d_a else float("nan")
    print("  F-168 hatte: +0,0145 R [+0,0097 .. +0,0193] auf 126.491 Ankern"
          " — diese Basis: %+.4f R" % wirkung_a)
    if not np.isfinite(wirkung_a) or abs(wirkung_a - 0.0145) > 0.006:
        print("  ⚠️⚠️ ABWEICHUNG > 0,006 R von F-168 - Befund unten NICHT "
              "verwenden, erst die Ursache klaeren.")

    print()
    print("=" * 92)
    print("B  `funding_extrem` ALLEIN, gleiche Geometrie (H20/R)")
    print("=" * 92)
    W.bericht("B  funding_extrem", fe_je_tag, True, rng,
              mit_positivkontrolle=True)

    # ---- gemeinsame Anker fuer die Schichtentests ------------------------
    fu_je_tag = {t: {x["sym"]: x["kennzahl"] for x in z} for t, z in fe_je_tag.items()}
    oi_je_tag_flat = {t: {x["sym"]: x["kennzahl"] for x in z} for t, z in oi_je_tag.items()}
    gem_oi, gem_fe = {}, {}
    for t, z in oi_je_tag.items():
        s = fu_je_tag.get(t) or {}
        a = [x for x in z if x["sym"] in s]
        if len(a) >= K.MIND_JE_TAG:
            gem_oi[t] = a
            gem_fe[t] = [x for x in fe_je_tag[t] if x["sym"] in {y["sym"] for y in a}]
    n = sum(len(z) for z in gem_oi.values())
    ks = []
    for t, z in gem_oi.items():
        s = fu_je_tag[t]
        a = W.rang([x["kennzahl"] for x in z])
        b = W.rang([s[x["sym"]] for x in z])
        if len(a) > 3:
            ks.append(float(np.corrcoef(a, b)[0, 1]))
    print()
    print("  gemeinsame Basis: %d Anker · %d Tage" % (n, len(gem_oi)))
    print("  Rangkorrelation oi/funding_extrem je Tag: Median %+.3f  "
          "(F-205 auf H2/Frontloading: +0,010 - unabhaengige Bestaetigung "
          "auf anderer Zielgroesse)" % np.median(ks))

    print()
    print("=" * 92)
    print("C  oi_aenderung INNERHALB funding_extrem-Fuenfteln - haelt der Befund?")
    print("=" * 92)
    d_c = K.geschichtet(gem_oi, fu_je_tag)
    M.urteil_tage("  NETTO", d_c, rng, BLOCK)
    M.urteil_tage("  Negativkontrolle", K.geschichtet(gem_oi, fu_je_tag, mische=rng),
                  rng, BLOCK)

    print()
    print("=" * 92)
    print("D  funding_extrem INNERHALB oi_aenderung-Fuenfteln")
    print("=" * 92)
    d_d = K.geschichtet(gem_fe, oi_je_tag_flat)
    M.urteil_tage("  NETTO", d_d, rng, BLOCK)
    M.urteil_tage("  Negativkontrolle", K.geschichtet(gem_fe, oi_je_tag_flat, mische=rng),
                  rng, BLOCK)

    print()
    print("=" * 92)
    print("E  DIE SPERRE SELBST — Status quo gegen zwei Varianten")
    print("=" * 92)
    print("  Status quo:  sperre bei oi_aenderung oberstes Fuenftel allein")
    print("  Lockern:     sperre nur bei oi UND funding_extrem beide oben")
    print("  Verschaerfen: sperre bei oi ODER funding_extrem oben")
    quo, locker, scharf = {}, {}, {}
    anteil_quo, anteil_locker, anteil_scharf = [], [], []
    for tag, z in gem_oi.items():
        s = fu_je_tag[tag]
        y = np.array([x["in_r"] for x in z], float)
        ro = W.rang([x["kennzahl"] for x in z])
        rf = W.rang([s[x["sym"]] for x in z])
        frei_quo = ro < W.GRENZE
        frei_locker = ~((ro >= W.GRENZE) & (rf >= W.GRENZE))
        frei_scharf = ~((ro >= W.GRENZE) | (rf >= W.GRENZE))
        if frei_scharf.sum() < 3 or (~frei_quo).sum() < 1:
            continue
        basis = float(np.median(y))
        quo[tag] = float(np.median(y[frei_quo]) - basis)
        locker[tag] = float(np.median(y[frei_locker]) - basis)
        scharf[tag] = float(np.median(y[frei_scharf]) - basis)
        anteil_quo.append(float((~frei_quo).mean()))
        anteil_locker.append(float((~frei_locker).mean()))
        anteil_scharf.append(float((~frei_scharf).mean()))
    print("  gesperrt:  Status quo %.1f %%   Lockern %.1f %%   "
          "Verschaerfen %.1f %%"
          % (100 * st.mean(anteil_quo), 100 * st.mean(anteil_locker),
             100 * st.mean(anteil_scharf)))
    M.urteil_tage("  Status quo (oi allein)", quo, rng, BLOCK)
    M.urteil_tage("  Lockern (oi UND funding_extrem)", locker, rng, BLOCK)
    M.urteil_tage("  Verschaerfen (oi ODER funding_extrem)", scharf, rng, BLOCK)
    print()
    print("  LESART: die Sperre bleibt unveraendert, wenn keine Variante den")
    print("  Status quo schlaegt UND ausserhalb von dessen Band liegt -")
    print("  sonst ist es eine Nutzerentscheidung, welche Richtung.")


if __name__ == "__main__":
    main()
