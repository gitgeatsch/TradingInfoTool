# -*- coding: utf-8 -*-
"""DIE AUSWAHL IN DER ECHTEN KONSTELLATION — und wo sie WIRKT (06.09.2026)

## Der scheinbare Widerspruch

    A1 (23.08., barrierenfrei und BRUTTO, 40 Symbole, 3.290 Tage):
        k=2   H5: +0,79 % (t 3,29)      H20: +2,74 % (t 4,52)

    meine Messung (BARRIEREN-Trefferquote, H5):
        5 % Auswahl: -0,38 Punkte · 10 %: -0,85 · 20 %: -0,98

**Kein Widerspruch - zwei verschiedene ZIELGROESSEN.** A1 mass die
Rendite, ich die Barrieren-Trefferquote. Beide koennen zugleich stimmen:
die Gewaehlten bringen mehr Rendite, treffen aber oefter zuerst den Stop.

## ⚠️ Die Erklaerung, mechanisch

Die Auswahl trifft zu 74,8 % das oberste vola-Fuenftel (N9). Hohe
Volatilitaet heisst mehr Bewegung - **und bei einem Stop auf -1 R oefter
Stop zuerst.**

**Damit ist die Auswahl nicht schlecht, sondern fuer ein Barrierensystem
falsch parametriert.**

## Nutzervorgabe, die den Zuschnitt bestimmt

*„bevor wir etwas entfernen, muessen wir alles tun, um eine Verbesserung
zu erreichen. Wenn die Werte hier und in dieser Form nicht wirken, dann
u. U. woanders."*

## Was gemessen wird

    1  REPRODUKTION   k=2, barrierenfreie Rendite - kommt A1s +0,79 %
                      zurueck? Ohne das gilt nichts weiter.
    2  DIE STOPWEITE  dieselbe Auswahl, Barrieren-Trefferquote bei
                      Stop -1,0 / -1,5 / -2,0 / -3,0 R (CRV fest 2,0)
                      ⚠️ Kippt sie bei weiterem Stop ins Plus, ist die
                      Antwort nicht "abschalten", sondern "Auswahl und
                      Stopweite gehoeren zusammen".
    3  DER ERWARTUNGSWERT  Treffer und Nicht-Treffer zusammen, in R -
                      denn eine niedrigere Quote bei groesserem Gewinn
                      kann trotzdem besser sein.

    python pruefe_auswahl_produktion.py
"""
from __future__ import annotations

import sys
import time

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_eigenschaft_beitrag as B                        # noqa: E402
from messe_beitrag_auf_auswahl import momentum250            # noqa: E402

BRUCH, BLOCK = 5.0, 15
CRV = 2.0
STOPS = (1.0, 1.5, 2.0, 3.0)
K = 2                        # die ECHTE Auswahl (A1, 23.08.)

# ⚠️⚠️ DIE GRUNDMENGE IST ENTSCHEIDEND (06.09., erste Fassung falsch).
#
# A1 mass `k=2` aus **40 Symbolen der Watchlist**. Die erste Fassung dieses
# Laufs waehlte k=2 aus bis zu **516 Symbolen des Messuniversums** - also
# 0,4 % statt 5 %. Eine voellig andere Auswahl, und die Reproduktion
# misslang entsprechend (+0,10 % gegen A1s +0,79 %).
#
# Die Watchlist-Historie liegt nicht vor. Als Naeherung: die GROESSTEN N
# nach Umsatz je Tag - das ist, wonach eine Watchlist zusammengestellt
# wird (handelbar, liquide). N wird variiert, damit die Abhaengigkeit
# sichtbar bleibt.
GRUNDMENGEN = (40, 80, 160, None)     # None = das ganze Messuniversum


def band(d, block=BLOCK, zieh=2000, saat=20260906):
    rng = np.random.default_rng(saat)
    x = np.array([d[q] for q in sorted(d)], float)
    n = len(x)
    if n < block + 30:
        return None
    nb = max(1, n // block)
    st = np.arange(n - block + 1)
    a = np.empty(zieh)
    for j in range(zieh):
        s = rng.choice(st, nb)
        a[j] = np.concatenate([x[i:i + block] for i in s]).mean()
    return (float(x.mean()), float(np.percentile(a, 2.5)),
            float(np.percentile(a, 97.5)))


def main() -> int:
    t0 = time.time()
    print("Lade Reihen ...", flush=True)
    reihen = B.lade()
    mom = momentum250(reihen)

    for horizont in (5, 20):
        print()
        print("#" * 96)
        print("# HORIZONT %d" % horizont)
        print("#" * 96)
        # Anker mit allem, was gebraucht wird
        daten: dict = {}
        for sym, z in reihen.items():
            tage = [x[0] for x in z]
            c = np.array([x[1] for x in z], float)
            h = np.array([x[2] for x in z], float)
            t = np.array([x[3] for x in z], float)
            v = np.array([x[4] for x in z], float)
            br = B.spanne(h, t, c, B.SCHWANKUNG)
            vh = c[1:] / np.maximum(c[:-1], 1e-12)
            bruch = (vh > BRUCH) | (vh < 1.0 / BRUCH)
            for i in range(B.SCHWANKUNG, len(c) - horizont):
                if not np.isfinite(br[i]) or br[i] <= 0:
                    continue
                if bruch[i:i + horizont].any():
                    continue
                e = {"sym": sym, "umsatz": float(v[i] * c[i]),
                     "rendite": float(c[i + horizont] / c[i] - 1.0)}
                for s in STOPS:
                    ziel, stop = c[i] + CRV * s * br[i], c[i] - s * br[i]
                    aus = 0
                    for j in range(i + 1, i + horizont + 1):
                        if t[j] <= stop:
                            aus = -1
                            break
                        if h[j] >= ziel:
                            aus = +1
                            break
                    e["t%.1f" % s] = 1.0 if aus > 0 else 0.0
                    # Erwartungswert in R: Treffer +CRV, Stop -1, offen roh
                    e["e%.1f" % s] = (CRV if aus > 0 else
                                      -1.0 if aus < 0 else
                                      float((c[i + horizont] - c[i])
                                            / (s * br[i])))
                daten.setdefault(tage[i], []).append(e)

        def reihe(feld, grundmenge):
            """⚠️ Erst die GRUNDMENGE (Watchlist-Naeherung), dann k=2."""
            aus = {}
            for tag, z in daten.items():
                mt = mom.get(tag)
                if not mt:
                    continue
                w = [q for q in z if q["sym"] in mt]
                if grundmenge:
                    w = sorted(w, key=lambda q: -q["umsatz"])[:grundmenge]
                if len(w) < 10:
                    continue
                mw = np.array([mt[q["sym"]] for q in w], float)
                k = min(K, max(1, len(w) - 1))
                sel = np.argsort(mw)[-k:]
                y = np.array([q[feld] for q in w], float)
                aus[tag] = float(y[sel].mean()) - float(y.mean())
            return aus

        print()
        print("  1  REPRODUKTION — k=%d, barrierenfreie RENDITE, je GRUNDMENGE"
              % K)
        print("     A1 mass auf 40 Symbolen: H5 +0,79 %% · H20 +2,74 %%")
        print("     %-16s %11s %24s  %s"
              % ("Grundmenge", "Wirkung", "Band", "Urteil"))
        beste = None
        for g in GRUNDMENGEN:
            b = band(reihe("rendite", g))
            if not b:
                continue
            lab = ("groesste %d nach Umsatz" % g) if g else "alle (516)"
            print("     %-16s %+10.4f %% [%+.4f .. %+.4f]  %s"
                  % (lab, 100 * b[0], 100 * b[1], 100 * b[2],
                     "✔ TRAEGT" if b[1] > 0 else "traegt nicht"), flush=True)
            if b[1] > 0 and beste is None:
                beste = g

        gm = beste if beste is not None else 40
        print()
        print("  2  DIE STOPWEITE — Barrieren-Trefferquote je Stop")
        print("     (Grundmenge: %s)"
              % (("groesste %d nach Umsatz" % gm) if gm else "alle"))
        print("     %-10s %11s %24s  %s"
              % ("Stop", "Differenz", "Band", "Urteil"))
        for s in STOPS:
            b = band(reihe("t%.1f" % s, gm))
            if not b:
                continue
            u = ("⚠️ schaedlich" if b[2] < 0 else
                 "✔ hilft" if b[1] > 0 else "nicht trennbar")
            print("     %-10s %+10.4f  [%+.4f .. %+.4f]  %s"
                  % ("-%.1f R" % s, 100 * b[0], 100 * b[1], 100 * b[2], u),
                  flush=True)

        print()
        print("  3  DER ERWARTUNGSWERT in R — Treffer und Verlust zusammen")
        print("     %-10s %11s %24s  %s"
              % ("Stop", "Differenz", "Band", "Urteil"))
        for s in STOPS:
            b = band(reihe("e%.1f" % s, gm))
            if not b:
                continue
            u = ("⚠️ schaedlich" if b[2] < 0 else
                 "✔ hilft" if b[1] > 0 else "nicht trennbar")
            print("     %-10s %+10.4f R [%+.4f .. %+.4f]  %s"
                  % ("-%.1f R" % s, b[0], b[1], b[2], u), flush=True)

    print()
    print("  ⚠️ Kippt die Auswahl bei weiterem Stop ins Plus, lautet die")
    print("     Antwort nicht 'abschalten', sondern 'Auswahl und Stopweite")
    print("     gehoeren zusammen'.")
    print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
