# -*- coding: utf-8 -*-
"""KONSISTENZPRÜFUNG aller Befunde vom 06.09.2026

**Nutzervorgabe:** *„prüfe alle heutigen Messungen und Entscheidungen, ob
diese alle keinen Widerspruch oder Fehler haben, damit wir ab hier ohne
Fehlmessungen weitermachen können."*

## Die vier Stellen, die sich widersprechen KÖNNTEN

  W1  2.115 sagt: ein im Rang GEFALLENES Asset hat mehr Randpotential.
      2.133 sagt: HOHE Volatilitaet senkt die Barrieren-Quote.
      ⚠️ Ein gefallenes Asset ist meist volatil. Widersprechen sich die
      beiden Befunde?

  W2  2.126 sagt: die Momentum-Auswahl trifft zu 74,8 % das oberste
      vola-Fuenftel. 2.133 sagt: das oberste vola-Fuenftel ist das
      SCHLECHTESTE.
      ⚠️ Waehlt die Auswahl systematisch die von `vola` schlecht
      bewerteten Werte?

  W3  2.127 misst `vola` am RANDMASS, 2.133 an der BARRIEREN-Quote.
      ⚠️ Zeigen beide in dieselbe Richtung? Wenn nicht, ist einer falsch.

  W4  (nur Doku) 2.130 meldet „vola: 4 von 4 Nachbarpaaren, Kontrolle
      flach". 2.132 hat das widerlegt. Traegt 2.130 einen Vermerk?
      -> getrennt geprueft, keine Messung noetig

    python pruefe_konsistenz_06_09.py
"""
from __future__ import annotations

import sys
import time

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_eigenschaft_beitrag as B                        # noqa: E402
import messe_kandidaten_als_regel as K                       # noqa: E402
import messe_regel_wirksamkeit as W                          # noqa: E402
from messe_beitrag_auf_auswahl import momentum250            # noqa: E402

CRV, BRUCH, H = 2.0, 5.0, 5
ZURUECK = 180


def gleit(x, n):
    c = np.concatenate(([0.0], np.cumsum(x)))
    a = np.full(len(x), np.nan)
    a[n:] = (c[n:-1] - c[:-n - 1]) / n
    return a


def main() -> int:
    t0 = time.time()
    print("Lade Reihen ...", flush=True)
    reihen = B.lade()
    mom = momentum250(reihen)

    # Basis: je Tag Symbol, vola-Kennzahl, Umsatzrang, Barrierenausgang
    daten: dict = {}
    for sym, z in reihen.items():
        tage = [x[0] for x in z]
        c = np.array([x[1] for x in z], float)
        h = np.array([x[2] for x in z], float)
        t = np.array([x[3] for x in z], float)
        v = np.array([x[4] for x in z], float)
        br = B.spanne(h, t, c, B.SCHWANKUNG)
        u = gleit(v * c, 252)
        vh = c[1:] / np.maximum(c[:-1], 1e-12)
        bruch = (vh > BRUCH) | (vh < 1.0 / BRUCH)
        for i in range(260, len(c) - H):
            if not np.isfinite(br[i]) or br[i] <= 0 or not np.isfinite(u[i]):
                continue
            if u[i] <= 0 or bruch[i:i + H].any():
                continue
            ziel, stop = c[i] + CRV * br[i], c[i] - 1.0 * br[i]
            aus = 0
            for j in range(i + 1, i + H + 1):
                if t[j] <= stop:
                    aus = -1
                    break
                if h[j] >= ziel:
                    aus = +1
                    break
            daten.setdefault(tage[i], []).append({
                "sym": sym, "umsatz": float(u[i]),
                "vola": float(br[i] / np.median(br[i - 250:i + 1])),
                "treffer": 1.0 if aus > 0 else 0.0})
    tage = sorted(t for t, z in daten.items() if len(z) >= 50)
    rang = {t: {q["sym"]: r for r, q in
                enumerate(sorted(daten[t], key=lambda x: -x["umsatz"]))}
            for t in tage}
    idx = {t: i for i, t in enumerate(tage)}
    print("  %d Tage" % len(tage))

    # ---------------- W1  gefallen gegen vola ----------------------------
    print()
    print("=" * 92)
    print("W1  Ist ein im Rang GEFALLENES Asset auch hochvolatil?")
    print("=" * 92)
    paare = []
    for t in tage:
        i = idx[t]
        if i < ZURUECK:
            continue
        alt = rang[tage[i - ZURUECK]]
        w = [q for q in daten[t] if q["sym"] in alt]
        if len(w) < 20:
            continue
        d = np.array([rang[t][q["sym"]] - alt[q["sym"]] for q in w], float)
        vo = np.array([q["vola"] for q in w], float)
        if d.std() > 1e-9 and vo.std() > 1e-9:
            paare.append(float(np.corrcoef(W.rang(d), W.rang(vo))[0, 1]))
    r1 = float(np.median(paare))
    print("  Rangkorrelation (Rangaenderung gegen vola), Median ueber "
          "%d Tage: %+.3f" % (len(paare), r1))
    print("  p10 %+.3f · p90 %+.3f"
          % (np.percentile(paare, 10), np.percentile(paare, 90)))
    print("  -> %s"
          % ("⚠️ GEFALLENE sind systematisch volatiler - die Befunde"
             " ueberschneiden sich" if r1 > 0.2 else
             "✔ kaum Zusammenhang - 2.115 und 2.133 messen VERSCHIEDENES"))

    # ---------------- W2  Auswahl gegen vola -----------------------------
    print()
    print("=" * 92)
    print("W2  Waehlt die Momentum-Auswahl die von `vola` SCHLECHT")
    print("    bewerteten Werte?")
    print("=" * 92)
    print("  %-14s %12s %14s  %s"
          % ("Auswahl", "Trefferquote", "alle", "Differenz"))
    for menge in (1.00, 0.20, 0.10, 0.05):
        q_sel, q_all = [], []
        for t in tage:
            mt = mom.get(t)
            if not mt:
                continue
            w = [q for q in daten[t] if q["sym"] in mt]
            if len(w) < 20:
                continue
            mw = np.array([mt[q["sym"]] for q in w], float)
            k = max(1, int(round(len(w) * menge)))
            sel = np.argsort(mw)[-k:]
            y = np.array([q["treffer"] for q in w], float)
            q_sel.append(float(y[sel].mean()))
            q_all.append(float(y.mean()))
        if not q_sel:
            continue
        a, b = 100 * np.mean(q_sel), 100 * np.mean(q_all)
        print("  %-14s %11.2f%% %13.2f%%  %+.2f Punkte  %s"
              % ("%.0f %%" % (100 * menge), a, b, a - b,
                 "⚠️ SCHLECHTER" if a - b < -0.2 else
                 "besser" if a - b > 0.2 else "gleich"), flush=True)
    print()
    print("  ⚠️ Traegt die Auswahl NEGATIV bei, waehlt sie systematisch")
    print("     die schlechteren Werte - dann ist sie nicht nur wirkungslos")
    print("     (F-180), sondern schaedlich.")

    # ---------------- W3  Randmass gegen Barriere ------------------------
    print()
    print("=" * 92)
    print("W3  Zeigen RANDMASS und BARRIEREN-Quote fuer `vola` in dieselbe")
    print("    Richtung?")
    print("=" * 92)
    je_tag = K.baue(reihen, "vola", None, horizont=H)
    for lab, feld in (("Barriere (Ziel vor Stop)", None),
                      ("Randmass > +2 R", "rand")):
        st = []
        quelle = daten if feld is None else je_tag
        for i in range(3):
            werte = []
            for t in (tage if feld is None else sorted(je_tag)):
                z = quelle.get(t) or []
                if len(z) < 12:
                    continue
                if feld is None:
                    w = np.array([q["vola"] for q in z], float)
                    y = np.array([q["treffer"] for q in z], float)
                else:
                    w = np.array([q["kennzahl"] for q in z], float)
                    y = (np.array([q["in_r"] for q in z], float) > 2.0
                         ).astype(float)
                f = np.minimum((W.rang(w) * 3).astype(int), 2)
                m = f == i
                if m.sum() >= 3:
                    werte.append(float(y[m].mean()) - float(y.mean()))
            st.append(100 * float(np.mean(werte)) if werte else float("nan"))
        print("  %-26s %s" % (lab, " · ".join("%+7.3f" % x for x in st)))
    print()
    print("  ⚠️ Zeigen beide dasselbe Vorzeichenmuster (unten gut, oben")
    print("     schlecht), sind 2.127 und 2.133 vertraeglich.")
    print()
    print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
