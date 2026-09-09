# -*- coding: utf-8 -*-
"""DREI KRITERIEN — auf den ECHTEN Daten geprueft (09.09.2026)

## ⚠️⚠️ Warum nicht auf Kunstwelten

Der erste Anlauf (`selbsttest_kriterien.py`) lief auf Kunstwelten. Beim
Gegenpruefen zeigte sich, dass sie die Wirklichkeit nicht treffen:

    Bandbreite   Kunstwelt 0,018      echt `turnover` 0,108   Faktor 6
    Tagesreihe   SD 0,150 / AK1 0,20  echt SD 0,331 / AK1 0,60

Weder Ueberlappung der Zielgroesse noch Beharrlichkeit der Kennzahl noch
Schwankung des Effekts schliessen diese Luecke - zusammen kamen sie auf
SD(Block) 0,031 gegen echte 0,147.

> **Ein Pruefstand, der praeziser ist als die Wirklichkeit, beantwortet
> die Frage nicht** - dort funktioniert jedes Kriterium.

⚠️ Die Kunstwelt weiter zu kalibrieren, bis sie passt, waere Anpassen
durch Probieren - und hinterher nicht mehr auseinanderzuhalten.

## Der bessere Weg: die echten Daten selbst

Eine NULLWELT entsteht durch Mischen der Raenge je Kalendertag. Sie hat
die echte Streuung, die echte Traegheit, die echte Symbolzahl - **von
selbst, ohne Kalibrierung**. Und sie enthaelt per Konstruktion keinen
Zusammenhang zwischen Kennzahl und Ergebnis.

    Jedes "traegt" auf einer Nullwelt ist ein FEHLALARM.

Fuer die Fundquote wird in dieselbe gemischte Welt ein bekannter Effekt
gelegt.

⚠️ **Zur Zirkularitaet:** dieselbe Pflanzung benutzt die Positivkontrolle
der Norm. Das waere ein Problem, wenn hier die Positivkontrolle geprueft
wuerde. Geprueft werden aber die Kriterien A/B/C - sie lesen `unten`,
`null_oben` und `nullpunkt`, von denen keines die Pflanzung beruehrt.

⚠️ **Die Saaten liegen weit weg** von denen, die `pruefe_auswahl`
intern fuer seine eigene Nullkontrolle benutzt (`SAAT + z`, z = 0..39) -
sonst waere eine Testwelt zufaellig eine ihrer eigenen Nullziehungen.

## Die drei Kriterien

    A  unten > max(0, null_oben)     heute gueltig - zwei Baender disjunkt
    B  unten > max(0, nullpunkt)     gegen den VERSATZ statt die Streuung
    C  unten > 0                     das alte Kriterium (Befund 2.162)

Alle drei aus DEMSELBEN Befund - kein Ziehungsunterschied zwischen ihnen.

## Der Sollwert, VOR dem Lauf

Das Band ist ein 95-%-Band, einseitig also **2,5 %** Fehlalarme.

    FA <= 2,5 % UND hohe Fundquote     das richtige Kriterium
    FA > 2,5 %                          zu locker
    FA ~ 0 % und niedrige Fundquote     zu streng

⚠️ **Beide Fehlerarten zaehlen.** Wer nur die Fehlalarme ansieht, waehlt
immer das strengste - und genau das steckt heute in der Anlage.

## Die Vorhersage (Methodik 2.80)

    A  FA nahe 0 · Fundquote bricht ein
    B  FA um 2,5 % · Fundquote deutlich besser
    C  FA deutlich ueber 2,5 %

⚠️ Faellt B's Fehlalarmquote hoch aus, bleibt A zu Recht stehen.

    python selbsttest_kriterien_echt.py [--klein]
"""
from __future__ import annotations

import argparse
import sys
import time

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_eigenschaft_beitrag as B                        # noqa: E402
import messe_kandidaten_als_regel as K                       # noqa: E402
import messnorm as N                                          # noqa: E402
import messnorm_auswahl as MA                                # noqa: E402
from messe_alle_kandidaten import zusatzquellen              # noqa: E402
from messe_beitrag_auf_auswahl import momentum250            # noqa: E402
from messnorm import SAAT                                     # noqa: E402
import messe_regel_wirksamkeit as W                          # noqa: E402

HORIZONT = 20
AB = "2022-01-01"
# ⚠️ Weit weg von `SAAT + z` (z = 0..39), das die Norm intern benutzt.
SAAT_TEST = SAAT + 500000
STAERKEN = (0.20, 0.30, 0.40)
KRITERIEN = ("A null_oben", "B nullpunkt", "C null")
# Die zwei echten Basen: die schmalste und eine breitere.
# ⚠️ GEGENPRUEFUNG 09.09.: `oi_aenderung` als DRITTE, unabhaengige Basis -
# andere Datenquelle (Terminmarkt), andere Menge, andere Symbolzahl (122).
# Haelt B auch dort das Niveau, ist das Ergebnis nicht basisabhaengig.
BASEN = (("oi_aenderung", "20%"),)


def mische_welt(je_tag: dict, rng, pflanze: float = 0.0) -> dict:
    """Eine NULLWELT aus echten Daten: Raenge je Tag gemischt.

    ⚠️ Gemischt wird die KENNZAHL, nicht das Ergebnis - dann bleiben die
    Ergebnisse mit ihrer echten Tagesstruktur genau da, wo sie waren, und
    nur der Zusammenhang zur Kennzahl ist zerstoert.
    """
    neu = {}
    for tag, zeilen in je_tag.items():
        kz = np.array([x["kennzahl"] for x in zeilen], float)
        kz = rng.permutation(kz)
        y = np.array([x["in_r"] for x in zeilen], float)
        if pflanze:
            # Die oberen 20 % nach der GEMISCHTEN Kennzahl werden
            # schlechter - genau die Form, die die Anlage sucht.
            y = y - float(pflanze) * (W.rang(kz) >= W.GRENZE)
        neu[tag] = [{"sym": zeilen[i]["sym"], "kennzahl": float(kz[i]),
                     "in_r": float(y[i])} for i in range(len(zeilen))]
    return neu


def urteile(b) -> tuple:
    return (b.unten > max(0.0, b.null_oben),
            b.unten > max(0.0, b.nullpunkt),
            b.unten > 0.0)


def quote(t: int, n: int) -> str:
    p = t / max(1, n)
    se = (p * (1.0 - p) / max(1, n)) ** 0.5
    return "%2d/%2d %5.1f%% (±%.1f)" % (t, n, 100 * p, 100 * se)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--klein", action="store_true")
    a = ap.parse_args()
    # ⚠️ Das Gewicht liegt auf der FEHLALARMQUOTE: dort trennen sich die
    # Kriterien, und dort entscheidet die Genauigkeit. Die Fundquote war
    # im Kurzlauf schon eindeutig (61 % gegen 100 %).
    n0, n1 = (4, 3) if a.klein else (50, 6)
    t0 = time.time()

    reihen = B.lade()
    mom = momentum250(reihen)
    lage = N.Lage(instrument="spot", strategie="einstieg")
    zus = zusatzquellen()

    print("=" * 104)
    print("DREI KRITERIEN — auf den ECHTEN Daten, Nullwelten durch Mischen")
    print("=" * 104)
    print("  %s" % N.standardzeile())
    print("  Sollwert Fehlalarme: 2,5 %% (95-%%-Band, einseitig).")
    print("  ⚠️ BEIDE Fehlerarten zaehlen - wer nur die Fehlalarme ansieht,")
    print("     waehlt immer das strengste Kriterium.")
    if a.klein:
        print("  ⚠️ KURZLAUF - prueft den Aufbau, liefert KEINE Aussage.")

    erg = {}
    for kand, menge in BASEN:
        je = K.baue(reihen, kand, zus.get(kand), horizont=HORIZONT)
        je = {t: z for t, z in je.items() if str(t) >= AB}
        print()
        print("  BASIS %s auf %s ab %s" % (kand, menge, AB))
        print("     %-14s %10s   %-21s %-21s %s"
              % ("Fall", "Wirkung", KRITERIEN[0], KRITERIEN[1], KRITERIEN[2]))
        for fall, s, n in [("FEHLALARM", 0.0, n0)] + \
                          [("Effekt %.2f" % x, x, n1) for x in STAERKEN]:
            tr, w = [0, 0, 0], []
            for i in range(n):
                welt = mische_welt(je, np.random.default_rng(
                    SAAT_TEST + int(s * 1000) * 977 + i), pflanze=s)
                try:
                    b = MA.pruefe_auswahl(
                        kand, welt, mom, lage=lage, menge=menge,
                        rng=np.random.default_rng(SAAT_TEST + 7 + i),
                        horizont=HORIZONT, staerken=(0.02,),
                        hypothese="Kriterienvergleich echt",
                        verwendung="Beitrag")
                except Exception:                            # noqa: BLE001
                    continue
                for k, v in enumerate(urteile(b)):
                    tr[k] += bool(v)
                w.append(b.wirkung)
            erg[(kand, s)] = (tr, len(w))
            print("     %-14s %+10.4f   %-21s %-21s %s"
                  % (fall, float(np.mean(w)) if w else float("nan"),
                     quote(tr[0], len(w)), quote(tr[1], len(w)),
                     quote(tr[2], len(w))), flush=True)

    # ---- Urteil ---------------------------------------------------------
    print()
    print("=" * 104)
    print("WELCHES KRITERIUM HAELT BEIDE SEITEN?")
    print("=" * 104)
    for k, krit in enumerate(KRITERIEN):
        fa_t = sum(erg[(c, 0.0)][0][k] for c, _m in BASEN)
        fa_n = sum(erg[(c, 0.0)][1] for c, _m in BASEN)
        fq_t = sum(erg[(c, s)][0][k] for c, _m in BASEN for s in STAERKEN)
        fq_n = sum(erg[(c, s)][1] for c, _m in BASEN for s in STAERKEN)
        p = fa_t / max(1, fa_n)
        print("  %-14s Fehlalarme %s  %-22s Fundquote %s"
              % (krit, quote(fa_t, fa_n),
                 "✔ im Sollwert" if p <= 0.025 else "⚠️ ueber dem Sollwert",
                 quote(fq_t, fq_n)))
    print()
    print("  ⚠️ Genauigkeit: %d Nullwelten je Basis -> bei wahren 2,5 %% ein "
          "Standardfehler von %.1f pp."
          % (n0, 100 * (0.025 * 0.975 / max(1, n0)) ** 0.5))
    print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
