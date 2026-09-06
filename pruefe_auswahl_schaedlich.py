# -*- coding: utf-8 -*-
"""W2 — IST DIE MOMENTUM-AUSWAHL SCHÄDLICH? Mit Band (06.09.2026)

Die Konsistenzprüfung zeigte Punktschätzer:

    Auswahl 100 %   17,80 %   Referenz
    Auswahl  20 %   17,03 %   -0,77 Punkte
    Auswahl  10 %   16,91 %   -0,89 Punkte
    Auswahl   5 %   17,38 %   -0,42 Punkte

⚠️ **Ohne Band.** Genau der Fehler, der an diesem Tag dreimal passiert ist.
Hier mit Blockbootstrap und Zufallskontrolle (fuenf Mischungen).

## Warum das wichtig ist

F-180/F-182 hat gemessen, die Auswahl trage **null zusaetzliche Werte**
bei - sie waehlt praktisch nur, was ohnehin Bestand hat. **Traegt sie
zusaetzlich NEGATIV bei, ist sie nicht nur wirkungslos, sondern
schaedlich** - und dann ist die 9. Trichterstufe eine Verschlechterung.

    python pruefe_auswahl_schaedlich.py
"""
from __future__ import annotations

import sys
import time

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_bewertungskennzahl as MB                        # noqa: E402
import messe_eigenschaft_beitrag as B                        # noqa: E402
from messe_beitrag_auf_auswahl import momentum250            # noqa: E402

CRV, BRUCH, H, BLOCK = 2.0, 5.0, 5, 15
MISCHUNGEN = 5


def main() -> int:
    t0 = time.time()
    print("Lade Reihen ...", flush=True)
    reihen = B.lade()
    mom = momentum250(reihen)

    daten: dict = {}
    for sym, z in reihen.items():
        tage = [x[0] for x in z]
        c = np.array([x[1] for x in z], float)
        h = np.array([x[2] for x in z], float)
        t = np.array([x[3] for x in z], float)
        br = B.spanne(h, t, c, B.SCHWANKUNG)
        vh = c[1:] / np.maximum(c[:-1], 1e-12)
        bruch = (vh > BRUCH) | (vh < 1.0 / BRUCH)
        for i in range(B.SCHWANKUNG, len(c) - H):
            if not np.isfinite(br[i]) or br[i] <= 0 or bruch[i:i + H].any():
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
            daten.setdefault(tage[i], []).append(
                {"sym": sym, "treffer": 1.0 if aus > 0 else 0.0})

    def reihe(menge, mische=None):
        """Je Tag: Trefferquote der Gewaehlten minus die aller."""
        aus = {}
        for tag, z in daten.items():
            mt = mom.get(tag)
            if not mt:
                continue
            w = [q for q in z if q["sym"] in mt]
            if len(w) < 20:
                continue
            mw = np.array([mt[q["sym"]] for q in w], float)
            if mische is not None:
                mw = mische.permutation(mw)
            k = max(1, int(round(len(w) * menge)))
            sel = np.argsort(mw)[-k:]
            y = np.array([q["treffer"] for q in w], float)
            aus[tag] = float(y[sel].mean()) - float(y.mean())
        return aus

    def band(d, zieh=2000, saat=20260906):
        rng = np.random.default_rng(saat)
        x = np.array([d[q] for q in sorted(d)], float)
        n = len(x)
        if n < BLOCK + 30:
            return None
        nb = max(1, n // BLOCK)
        st = np.arange(n - BLOCK + 1)
        a = np.empty(zieh)
        for j in range(zieh):
            s = rng.choice(st, nb)
            a[j] = np.concatenate([x[i:i + BLOCK] for i in s]).mean()
        return (float(x.mean()), float(np.percentile(a, 2.5)),
                float(np.percentile(a, 97.5)))

    print()
    print("=" * 96)
    print("TRAEGT DIE MOMENTUM-AUSWAHL NEGATIV BEI?  (Barrieren-Quote, H%d)"
          % H)
    print("=" * 96)
    print("  %-10s %6s %11s %24s  %s"
          % ("Auswahl", "Tage", "Differenz", "Band", "Kontrolle (erw. 0,25)"))
    for menge in (0.20, 0.10, 0.05):
        d = reihe(menge)
        b = band(d)
        if b is None:
            print("  %-10s   zu wenige Tage" % ("%.0f %%" % (100 * menge)))
            continue
        falsch = 0
        for s in range(MISCHUNGEN):
            nb = band(reihe(menge, np.random.default_rng(9100 + s)))
            if nb and (nb[1] > 0 or nb[2] < 0):
                falsch += 1
        urteil = ("⚠️ SCHAEDLICH - Band ganz im Minus" if b[2] < 0 else
                  "hilft - Band ganz im Plus" if b[1] > 0 else
                  "nicht trennbar")
        print("  %-10s %6d %+10.4f  [%+.4f .. %+.4f]  %d von %d   %s"
              % ("%.0f %%" % (100 * menge), len(d), 100 * b[0],
                 100 * b[1], 100 * b[2], falsch, MISCHUNGEN, urteil),
              flush=True)
    print()
    print("  ⚠️ Ein Band ganz im Minus heisst: die Auswahl senkt die")
    print("     Trefferquote nachweisbar. Dann ist die 9. Trichterstufe")
    print("     keine Verbesserung, sondern eine Verschlechterung -")
    print("     und das waere ein Befund ueber das LAUFENDE System.")
    print()
    print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
