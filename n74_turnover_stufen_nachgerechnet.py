# -*- coding: utf-8 -*-
"""N-74 — `turnover`s STUFEN nachgerechnet (N-7, 07.09.2026)

## Der Anlass

N-73: auf seiner zulaessigen Menge (50 %) traegt `turnover` mit **+0,0909
R [+0,0433 .. +0,1454]** - rund **48 % staerker** als der registrierte
Wert von der freien Menge (+0,0616). Die live laufende Stufentabelle
(+3,15 / +0,83 / +0,22 / -1,79 / -2,40) stammt aber von der freien Menge.

⚠️ Sie traegt die **groessten Stufen des Systems**. Wenn sie um die
Haelfte danebenliegt, liegt jede Bewertung mit ihr daneben.

## ⚠️ R-R11 IST ERFUELLT, BEVOR HIER GEMESSEN WIRD

`rechne_turnover_beitrag.py` reproduziert die registrierte Tabelle exakt:
+3,15 / +0,83 / +0,22 / -1,79 / -2,40 aus 2.636 Kalendertagen.

## ⚠️⚠️ Und die Mengenfrage stellt sich hier ANDERS als bei der Wirkung

Die Ableitung laeuft auf dem **vollen Tagesquerschnitt** - ohne Auswahl.
Das ist kein Versehen, sondern richtig: `marktrang` bildet den Rang in
der Produktion ebenfalls ueber die MESSBASIS, nicht ueber die Auswahl
(sonst dreht das Vorzeichen, gemessen 31.08.).

> **Der RANG kommt aus dem vollen Querschnitt. Die FRAGE, wieviel eine
> Rangstufe wert ist, betrifft aber nur die Werte, die bis zur Bewertung
> kommen.** Beides ist zu messen, und die Zahlen duerfen auseinandergehen.

Deshalb laufen hier zwei Ableitungen nebeneinander:

    QUERSCHNITT   wie bisher - alle Werte des Tages
    AUSWAHL       Rang aus dem vollen Querschnitt, dann auf 50 %
                  verengt (turnovers zulaessige Menge, N-73)

## Was gegenueber der alten Ableitung dazukommt

    1  BESETZUNG je Fuenftel, VOR jeder Deutung. N-65: bei unter zwei
       Ankern je Gruppe ist der Median Rauschen, und die Verzerrung
       (+0,10 bis +0,16 R) uebersteigt jeden gesuchten Effekt.
    2  ENTZERRUNG. Dieselbe Rechnung mit GEMISCHTEN Raengen, 20
       Ziehungen; der Nullwert wird je Fuenftel abgezogen.
       ⚠️ Die alte Ableitung hat das nicht - sie rechnet gegen den
       Mittelwert der fuenf Fuenftel, was einen Teil der Verzerrung
       aufhebt, aber nicht den ungleichen Rest.
    3  ZUFALLSKONTROLLE als eigene Spalte.

## Vorab festgelegt — woertlich aus `rechne_turnover_beitrag.py`

> *"nutzbar: die Stufen sind MONOTON ueber die Fuenftel und die Spanne
> ist groesser als null. nicht nutzbar: sonst."*

⚠️ Und die HALBIERUNG bleibt: die Zahlen sind weiter in-sample, und die
Vorsicht war der Grund. Wer sie fallen laesst, muss das eigens begruenden.

    python n74_turnover_stufen_nachgerechnet.py
"""
from __future__ import annotations

import sys
import time

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_bewertungskennzahl as MB                        # noqa: E402
import messe_eigenschaft_beitrag as B                        # noqa: E402
import messe_kandidaten_als_regel as K                       # noqa: E402
import messnorm_auswahl as MA                                # noqa: E402
from messe_beitrag_auf_auswahl import (_auswahl_maske,       # noqa: E402
                                       momentum250)

HORIZONT, CRV = 20, 2.0
FAKTOR = 1.0 / (1.0 + CRV)      # d(quote) = d(Potential) / (1 + CRV)
SCHRUMPF = 2.0                  # in-sample-Vorsicht, wie 30.08.
ZIEH, SAAT = 20, 20260907
MIND_JE_GRUPPE = 2              # ⚠️ N-65: darunter ist der Median Rauschen


def fuenftel(je_tag, mom, anteil, mische=None):
    """Je Fuenftel die mittlere Tagesbewegung - und die Besetzung.

    ⚠️ Der RANG kommt aus dem vollen Tagesquerschnitt, auch wenn danach
    verengt wird. Genau so rechnet `marktrang` in der Produktion; ueber
    die Auswahl gerangt dreht das Vorzeichen (gemessen 31.08.).
    """
    sammel = {k: [] for k in range(5)}
    besetzt = {k: [] for k in range(5)}
    for tag, z in je_tag.items():
        if len(z) < 15:
            continue
        w = np.array([x["kennzahl"] for x in z], float)
        y = np.array([x["in_r"] for x in z], float)
        r = np.argsort(np.argsort(w)) / max(len(w) - 1, 1)
        if mische is not None:
            r = mische.permutation(r)
        if anteil < 1.0:
            m = _auswahl_maske(z, mom.get(tag) or {}, anteil, None)
            if m is None or not m.any():
                continue
        else:
            m = np.ones(len(z), bool)
        for k in range(5):
            g = m & (r >= k / 5) & ((r < (k + 1) / 5) if k < 4 else (r <= 1.0))
            besetzt[k].append(int(g.sum()))
            if g.sum() >= MIND_JE_GRUPPE:
                sammel[k].append(float(np.median(y[g])))
    return sammel, besetzt


def tabelle(je_tag, mom, anteil):
    """Punkte je Fuenftel - echt, Null und entzerrt."""
    echt, besetzt = fuenftel(je_tag, mom, anteil)
    w = [float(np.mean(echt[k])) if echt[k] else float("nan")
         for k in range(5)]
    null = {k: [] for k in range(5)}
    for z in range(ZIEH):
        n, _ = fuenftel(je_tag, mom, anteil,
                        mische=np.random.default_rng(SAAT + z))
        for k in range(5):
            if n[k]:
                null[k].append(float(np.mean(n[k])))
    nw = [float(np.mean(null[k])) if null[k] else 0.0 for k in range(5)]
    # ⚠️ Der Bezugspunkt ist der Mittelwert der fuenf - wie in der alten
    # Ableitung. Er wird fuer echt und null GETRENNT gebildet, sonst
    # verschoebe die Entzerrung alle Stufen um denselben Betrag und
    # aenderte nichts.
    me, mn = float(np.mean(w)), float(np.mean(nw))
    punkte, punkte_roh = [], []
    for k in range(5):
        roh = 100.0 * (w[k] - me) * FAKTOR
        ent = 100.0 * ((w[k] - me) - (nw[k] - mn)) * FAKTOR
        punkte_roh.append(roh)
        punkte.append(ent)
    return {"bewegung": w, "null": nw, "roh": punkte, "entzerrt": punkte,
            "punkte_roh": punkte_roh, "besetzt": besetzt,
            "tage": sum(1 for z in je_tag.values() if len(z) >= 15),
            "entzerrt_punkte": punkte}


def main() -> int:
    t0 = time.time()
    print("=" * 100)
    print("N-74 — `turnover`s Stufen nachgerechnet: Querschnitt gegen Auswahl")
    print("=" * 100)
    reihen = B.lade()
    mom = momentum250(reihen)
    menge = MB.reihe("data/onchain_historie.db", "splycur")
    je = K.baue(reihen, "turnover", menge, horizont=HORIZONT)
    zf = K.baue(reihen, "zufall", None, horizont=HORIZONT)
    zul = MA.zulaessige_mengen(je, mom, horizont=HORIZONT)
    print("  %d Kalendertage . H%d . CRV %.1f . zulaessig: %s"
          % (sum(1 for z in je.values() if len(z) >= 15), HORIZONT, CRV,
             ", ".join(zul)))

    varianten = [("QUERSCHNITT", 1.0), ("AUSWAHL 50%", 0.50)]
    erg = {}
    for lab, anteil in varianten:
        print()
        print("  %s" % lab)
        t = tabelle(je, mom, anteil)
        erg[lab] = t
        print("     %-9s %10s %10s %10s %11s %11s"
              % ("Fuenftel", "Anker/Tag", "Bewegung", "Null", "Punkte roh",
                 "GESCHRUMPFT"))
        for k in range(5):
            b = float(np.mean(t["besetzt"][k]))
            print("     %-9d %10.1f %+10.4f %+10.4f %+11.2f %+11.2f"
                  % (k, b, t["bewegung"][k], t["null"][k],
                     t["punkte_roh"][k], t["entzerrt"][k] / SCHRUMPF),
                  flush=True)
        knapp = [k for k in range(5)
                 if float(np.mean(t["besetzt"][k])) < MIND_JE_GRUPPE]
        print("     %s"
              % ("⚠️⚠️ Fuenftel %s unter %d Ankern je Tag - dort ist der "
                 "Median Rauschen" % (", ".join(map(str, knapp)),
                                      MIND_JE_GRUPPE)
                 if knapp else "✔ jedes Fuenftel hat >= %d Anker je Tag"
                 % MIND_JE_GRUPPE))

    # ---- KONTROLLE ------------------------------------------------------
    print()
    print("  KONTROLLE `zufall` — dieselbe Rechnung, entzerrt")
    tz = tabelle(zf, mom, 0.50)
    print("     %s" % "  ".join("%+.2f" % (x / SCHRUMPF)
                                for x in tz["entzerrt"]))
    gross = max(abs(x / SCHRUMPF) for x in tz["entzerrt"])
    print("     groesste Stufe %.2f Punkte - %s"
          % (gross, "✔ vernachlaessigbar" if gross < 0.5
             else "⚠️⚠️ AUFFAELLIG, der Aufbau traegt selbst"))

    # ---- URTEIL ---------------------------------------------------------
    print()
    print("=" * 100)
    print("WAS DAS HEISST")
    print("=" * 100)
    registriert = (+3.15, +0.83, +0.22, -1.79, -2.40)
    print("  %-14s %s" % ("registriert",
                          "  ".join("%+6.2f" % x for x in registriert)))
    for lab, _a in varianten:
        p = [x / SCHRUMPF for x in erg[lab]["entzerrt"]]
        mono = all(p[i] >= p[i + 1] - 1e-9 for i in range(4))
        print("  %-14s %s   %s"
              % (lab, "  ".join("%+6.2f" % x for x in p),
                 "✔ monoton" if mono else "⚠️⚠️ NICHT MONOTON"))
    print()
    q = [x / SCHRUMPF for x in erg["QUERSCHNITT"]["entzerrt"]]
    a5 = [x / SCHRUMPF for x in erg["AUSWAHL 50%"]["entzerrt"]]
    print("  Spanne (Fuenftel 0 minus 4):")
    print("     registriert  %+.2f" % (registriert[0] - registriert[4]))
    print("     QUERSCHNITT  %+.2f" % (q[0] - q[4]))
    print("     AUSWAHL 50%%  %+.2f" % (a5[0] - a5[4]))
    print()
    print("  ⚠️ Die Halbierung (in-sample-Vorsicht) ist in allen Zahlen")
    print("     oben schon enthalten - wie am 30.08.")
    print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
