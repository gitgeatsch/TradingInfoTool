# -*- coding: utf-8 -*-
"""DREI KRITERIEN GEGEN BEKANNTE WAHRHEIT (09.09.2026)

## Die Frage

Befund 2.210: `traegt = unten > null_oben` verlangt, dass die UNTERE
Vertrauensgrenze des Effekts die OBERE der Nullwelt ueberschreitet - zwei
95-%-Baender, die sich nicht ueberlappen. Das entspricht etwa p < 0,005.
Und der Nullpunkt hat kaum Versatz (Mittel +0,007 bis +0,017), aber ein
breites Band - `null_oben` ist also ein STREUMASS, und die Streuung
steckt im Band bereits.

> **Wird die Unsicherheit doppelt gezaehlt?** Das ist entscheidbar, nicht
> diskutierbar - der Pruefstand vom 08.09. kann es beantworten.

## Die drei Kriterien

    A  unten > max(0, null_oben)     heute gueltig - zwei Baender disjunkt
    B  unten > max(0, nullpunkt)     gegen den VERSATZ statt die Streuung
    C  unten > 0                     das alte Kriterium (Befund 2.162)

⚠️ Alle drei lesen sich aus DEMSELBEN Befund - es braucht keine drei
Laeufe. Damit ist der Vergleich auch frei von Ziehungsunterschieden.

## ⚠️⚠️ Die zweite Achse: die BREITE der Welt

Die Kriterien unterscheiden sich genau dort, wo die Baender breit sind.
In der Kunstwelt vom 08.09. (150 Symbole, 1500 Tage) sind sie eng - dort
fiel die Doppelzaehlung kaum auf. Die echten Basen sind schmaler:

    breit    150 Symbole, 1500 Tage, Menge 20 %   (wie 08.09.)
    schmal    66 Symbole, 1700 Tage, Menge 50 %   (wie `turnover`)

**Ohne die schmale Welt beantwortet der Lauf die Frage nicht.**

## Der Sollwert, VOR dem Lauf

Das Band ist ein 95-%-Band, einseitig also **2,5 %** Fehlalarme.

    Kriterium mit FA <= 2,5 % UND hoher Fundquote    das richtige
    Kriterium mit FA > 2,5 %                          zu locker
    Kriterium mit FA ~ 0 % und niedriger Fundquote    zu streng

⚠️ **Beide Fehlerarten zaehlen.** Ein Kriterium nur nach der
Fehlalarmquote zu waehlen, waehlt immer das strengste - und das ist der
Fehler, der heute in der Anlage steckt.

## Die Vorhersage (Methodik 2.80)

    A  FA nahe 0 in beiden Welten · Fundquote in der SCHMALEN Welt bricht ein
    B  FA um 2,5 % · Fundquote deutlich besser, vor allem schmal
    C  FA deutlich ueber 2,5 % - es fehlt die Korrektur des Versatzes

⚠️ Faellt B's Fehlalarmquote hoch aus, bleibt A zu Recht stehen. Das ist
der Ausgang, der den heutigen Standard bestaetigt.

    python selbsttest_kriterien.py [--klein]
"""
from __future__ import annotations

import argparse
import sys
import time

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messnorm as N                                          # noqa: E402
import messnorm_auswahl as MA                                # noqa: E402
import selbsttest_welt as SW                                 # noqa: E402

HORIZONT = 20
SPAR_LEITER = (0.02,)
# (Name, Symbole, Tage, Menge) - die zweite bildet `turnover` nach.
WELTEN = (("breit", 150, 1500, "20%"), ("schmal", 66, 1700, "50%"))
# Gepflanzt so gewaehlt, dass die GEMESSENEN Wirkungen die echten
# umschliessen (+0,044 bis +0,061): 0,20 x s.
STAERKEN = (0.10, 0.20, 0.30)
KRITERIEN = ("A null_oben", "B nullpunkt", "C null")


def urteile(b) -> tuple:
    """Die drei Kriterien, aus EINEM Befund gelesen."""
    return (b.unten > max(0.0, b.null_oben),
            b.unten > max(0.0, b.nullpunkt),
            b.unten > 0.0)


def quote(t: int, n: int) -> str:
    p = t / max(1, n)
    se = (p * (1.0 - p) / max(1, n)) ** 0.5
    return "%2d/%2d %5.1f%% (±%.1f)" % (t, n, 100 * p, 100 * se)


def lauf(name, syms, tage, menge, staerke, n, saat):
    """n Welten -> Treffer je Kriterium, und die mittlere Wirkung."""
    tr = [0, 0, 0]
    w = []
    for i in range(n):
        rng = np.random.default_rng(saat + i)
        je, mom = SW.welt(rng, staerke=staerke, tage=tage, je_tag_n=syms)
        try:
            b = MA.pruefe_auswahl(
                "kriterienprobe", je, mom,
                lage=N.Lage(instrument="spot", strategie="einstieg"),
                menge=menge, rng=np.random.default_rng(saat + 900000 + i),
                horizont=HORIZONT, staerken=SPAR_LEITER,
                hypothese="Kriterienvergleich", verwendung="Beitrag")
        except Exception:                                    # noqa: BLE001
            continue
        for k, v in enumerate(urteile(b)):
            tr[k] += bool(v)
        w.append(b.wirkung)
    return tr, (float(np.mean(w)) if w else float("nan")), len(w)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--klein", action="store_true")
    a = ap.parse_args()
    n0, n1 = (5, 4) if a.klein else (40, 15)
    t0 = time.time()

    print("=" * 104)
    print("DREI KRITERIEN GEGEN BEKANNTE WAHRHEIT")
    print("=" * 104)
    print("  %s" % N.standardzeile())
    print("  Sollwert Fehlalarme: 2,5 %% (das Band ist ein 95-%%-Band).")
    print("  ⚠️ BEIDE Fehlerarten zaehlen - wer nur die Fehlalarme "
          "ansieht, waehlt immer das strengste Kriterium.")
    if a.klein:
        print("  ⚠️ KURZLAUF - prueft den Aufbau, liefert KEINE Aussage.")

    ergebnis = {}
    for name, syms, tage, menge in WELTEN:
        print()
        print("  WELT '%s' — %d Symbole, %d Tage, Menge %s"
              % (name, syms, tage, menge))
        print("     %-14s %10s   %-22s %-22s %s"
              % ("Fall", "Wirkung", KRITERIEN[0], KRITERIEN[1], KRITERIEN[2]))
        tr, w, n = lauf(name, syms, tage, menge, 0.0, n0, 100000)
        ergebnis[(name, 0.0)] = (tr, w, n)
        print("     %-14s %+10.4f   %-22s %-22s %s"
              % ("FEHLALARM", w, quote(tr[0], n), quote(tr[1], n),
                 quote(tr[2], n)), flush=True)
        for s in STAERKEN:
            tr, w, n = lauf(name, syms, tage, menge, s, n1,
                            200000 + int(s * 1000) * 131)
            ergebnis[(name, s)] = (tr, w, n)
            print("     %-14s %+10.4f   %-22s %-22s %s"
                  % ("Effekt %.2f" % s, w, quote(tr[0], n),
                     quote(tr[1], n), quote(tr[2], n)), flush=True)

    # ---- Das Urteil ------------------------------------------------------
    print()
    print("=" * 104)
    print("WELCHES KRITERIUM HAELT BEIDE SEITEN?")
    print("=" * 104)
    for k, krit in enumerate(KRITERIEN):
        fa = [ergebnis[(w[0], 0.0)] for w in WELTEN]
        fa_t = sum(t[k] for t, _w, _n in fa)
        fa_n = sum(n for _t, _w, n in fa)
        fq = [ergebnis[(w[0], s)] for w in WELTEN for s in STAERKEN]
        fq_t = sum(t[k] for t, _w, _n in fq)
        fq_n = sum(n for _t, _w, n in fq)
        p = fa_t / max(1, fa_n)
        marke = ("✔ im Sollwert" if p <= 0.025
                 else "⚠️ ueber dem Sollwert")
        print("  %-14s Fehlalarme %s  %-18s Fundquote %s"
              % (krit, quote(fa_t, fa_n), marke, quote(fq_t, fq_n)))
    print()
    # Die schmale Welt gesondert - dort entscheidet es sich.
    print("  ⚠️ NUR DIE SCHMALE WELT (dort trennen sich die Kriterien):")
    for k, krit in enumerate(KRITERIEN):
        t0_, _w0, n0_ = ergebnis[("schmal", 0.0)]
        fq_t = sum(ergebnis[("schmal", s)][0][k] for s in STAERKEN)
        fq_n = sum(ergebnis[("schmal", s)][2] for s in STAERKEN)
        print("     %-14s Fehlalarme %s   Fundquote %s"
              % (krit, quote(t0_[k], n0_), quote(fq_t, fq_n)))
    print()
    print("  ⚠️ Genauigkeit: %d Nullwelten je Welt -> bei wahren 2,5 %% "
          "ein Standardfehler von %.1f pp."
          % (n0, 100 * (0.025 * 0.975 / max(1, n0)) ** 0.5))
    print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
