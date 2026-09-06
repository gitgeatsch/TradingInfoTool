# -*- coding: utf-8 -*-
"""N19 — IST DIE UMRECHNUNG KORREKT? (06.09.2026)

## Die Frage

`rechne_funding_beitrag.py` rechnet die gemessene Wirkung so in
Beitragspunkte um:

    Potential = quote * CRV - (1 - quote)
    d(Potential) = d(quote) * (1 + CRV)
    -> d(quote) = d(Potential) / (1 + CRV)        Faktor 1/3 bei CRV 2,0

⚠️ **Die Formel ist algebraisch exakt.** Sie ist die Ableitung der
Potentialformel - daran ist nichts zu pruefen.

## ⚠️ Die Annahme steckt im EINGANG

Eingesetzt wird als `d(Potential)` die gemessene **R-Wirkung** - eine
BARRIERENFREIE Bewegungsdifferenz (Median `in_r` mit Regel minus ohne).
`d(Potential)` meint aber die Aenderung des **Erwartungswerts eines
BARRIERENsystems**.

    gemessen      d(Median in_r)        Bewegung, ohne Stop, ohne Ziel
    eingesetzt    d(Potential)          Erwartungswert MIT Barriere

**Diese Gleichsetzung ist nie geprueft worden - und sie traegt die Stufen
von `funding` und `turnover` im laufenden System.**

## Die Pruefung

Fuer DIESELBEN Anker, je Fuenftel:

    1  d(Median in_r)        die Groesse, die gemessen wurde
    2  daraus VORHERGESAGT   d(q) = d(Median in_r) / (1 + CRV)
    3  TATSAECHLICH gemessen d(Barrieren-Quote)
    4  Vergleich 2 gegen 3

    stimmen sie   -> die Umrechnung traegt, die Stufen sind richtig
    weichen ab    -> die Stufen von funding und turnover stehen auf einer
                     falschen Umrechnung, und zwar im LAUFENDEN System

    python n19_umrechnung_geprueft.py
"""
from __future__ import annotations

import sys
import time

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_bewertungskennzahl as MB                        # noqa: E402
import messe_eigenschaft_beitrag as B                        # noqa: E402
import messe_funding_niveau as F                             # noqa: E402
import messe_regel_wirksamkeit as W                          # noqa: E402

CRV, BRUCH, FAECHER = 2.0, 5.0, 5
HORIZONT = 20              # die Basis, auf der funding/turnover kalibriert wurden


def baue(reihen, zusatz, art, horizont):
    """Je Anker: Kennzahl, Median-Ziel (in_r) und Barrieren-Ausgang."""
    je_tag: dict = {}
    for sym, z in reihen.items():
        tage = [x[0] for x in z]
        c = np.array([x[1] for x in z], float)
        h = np.array([x[2] for x in z], float)
        t = np.array([x[3] for x in z], float)
        v = np.array([x[4] for x in z], float)
        br = B.spanne(h, t, c, B.SCHWANKUNG)
        vh = c[1:] / np.maximum(c[:-1], 1e-12)
        bruch = (vh > BRUCH) | (vh < 1.0 / BRUCH)
        je_sym = (zusatz or {}).get(sym.upper()) or {}
        for i in range(B.SCHWANKUNG, len(c) - horizont):
            if not np.isfinite(br[i]) or br[i] <= 0 or bruch[i:i + horizont].any():
                continue
            if art == "vola":
                if i < 260:
                    continue
                kz = float(br[i] / np.median(br[i - 250:i + 1]))
            else:
                w = je_sym.get(tage[i])
                if w is None:
                    continue
                kz = float(w)
            ziel, stop = c[i] + CRV * br[i], c[i] - 1.0 * br[i]
            aus = 0
            for j in range(i + 1, i + horizont + 1):
                if t[j] <= stop:
                    aus = -1
                    break
                if h[j] >= ziel:
                    aus = +1
                    break
            je_tag.setdefault(tage[i], []).append({
                "kennzahl": kz,
                "in_r": float((c[i + horizont] - c[i]) / br[i]),
                "treffer": 1.0 if aus > 0 else 0.0})
    return {t: z for t, z in je_tag.items() if len(z) >= 3 * FAECHER}


def stufen(je_tag, feld, art="median"):
    reihen = [dict() for _ in range(FAECHER)]
    for tag, z in je_tag.items():
        w = np.array([x["kennzahl"] for x in z], float)
        y = np.array([x[feld] for x in z], float)
        f = np.minimum((W.rang(w) * FAECHER).astype(int), FAECHER - 1)
        basis = float(np.median(y)) if art == "median" else float(y.mean())
        for i in range(FAECHER):
            m = f == i
            if m.sum() >= 3:
                wert = float(np.median(y[m])) if art == "median" \
                    else float(y[m].mean())
                reihen[i][tag] = wert - basis
    return reihen


def band(d, block=60, zieh=2000, saat=20260906):
    rng = np.random.default_rng(saat)
    x = np.array([d[k] for k in sorted(d)], float)
    n = len(x)
    if n < block + 30:
        return None
    nb = max(1, n // block)
    st = np.arange(n - block + 1)
    aus = np.empty(zieh)
    for k in range(zieh):
        s = rng.choice(st, nb)
        aus[k] = np.concatenate([x[i:i + block] for i in s]).mean()
    return (float(x.mean()), float(np.percentile(aus, 2.5)),
            float(np.percentile(aus, 97.5)))


def main() -> int:
    t0 = time.time()
    print("Lade Reihen ...", flush=True)
    reihen = B.lade()
    fu = F.lade_funding()
    tu = MB.reihe("data/onchain_historie.db", "splycur")

    for art, zusatz in (("funding", fu), ("turnover", tu), ("vola", None)):
        je_tag = baue(reihen, zusatz, art, HORIZONT)
        if len(je_tag) < 300:
            print("  %-10s zu wenige Tage (%d)" % (art, len(je_tag)))
            continue
        n = sum(len(z) for z in je_tag.values())
        print()
        print("=" * 104)
        print("%s — H%d · CRV %.1f · %d Anker · %d Tage"
              % (art.upper(), HORIZONT, CRV, n, len(je_tag)))
        print("=" * 104)
        r_st = [band(d) for d in stufen(je_tag, "in_r", "median")]
        q_st = [band(d) for d in stufen(je_tag, "treffer", "mittel")]
        print("  %-10s %26s %12s %26s  %s"
              % ("", "d(Median in_r)", "VORHERGES.", "d(Barrieren-Quote)",
                 "Abweichung"))
        vor, ist = [], []
        for i in range(FAECHER):
            if r_st[i] is None or q_st[i] is None:
                print("  Fuenftel %d   zu wenige Tage" % i); continue
            p = r_st[i][0] / (1.0 + CRV)         # die Umrechnung
            m = q_st[i][0]
            vor.append(p); ist.append(m)
            ok = "✔" if q_st[i][1] <= p <= q_st[i][2] else "⚠️ ausserhalb"
            print("  Fuenftel %d  %+8.4f [%+7.4f..%+7.4f] %11.4f  "
                  "%+8.4f [%+7.4f..%+7.4f]  %s"
                  % (i, r_st[i][0], r_st[i][1], r_st[i][2], 100 * p,
                     100 * m, 100 * q_st[i][1], 100 * q_st[i][2], ok),
                  flush=True)
        if len(vor) == FAECHER:
            v, s = np.array(vor), np.array(ist)
            sp_v, sp_i = v.max() - v.min(), s.max() - s.min()
            print()
            print("  Spanne vorhergesagt %.3f Pkt · tatsaechlich %.3f Pkt · "
                  "Faktor %.2f" % (100 * sp_v, 100 * sp_i,
                                   sp_i / sp_v if sp_v else 0))
            print("  Korrelation der Reihen: %+.3f"
                  % float(np.corrcoef(v, s)[0, 1]))
            treffer = sum(1 for i in range(FAECHER)
                          if q_st[i][1] <= vor[i] <= q_st[i][2])
            print("  -> %d von %d Vorhersagen liegen IM gemessenen Band"
                  % (treffer, FAECHER))
    print()
    print("  ⚠️ Liegt die Vorhersage systematisch daneben, stehen die Stufen")
    print("     von `funding` und `turnover` auf einer falschen Umrechnung -")
    print("     und zwar im LAUFENDEN System.")
    print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
