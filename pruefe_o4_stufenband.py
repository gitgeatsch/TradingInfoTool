# -*- coding: utf-8 -*-
"""O4 GEGENPRUEFUNG — hat die MONOTONIE ein Band? (06.09.2026)

Die Aussage *„`vola` ist am Randmassstab ein monotoner Regler"* steht auf
PUNKTSCHAETZERN. Genau dieser Fehler ist heute schon zweimal passiert
(die Breite beim Frontloading, die 43 % Mengeneffekt bei N5).

Geprueft wird:
  G1  BAND je Fuenftel - Blockbootstrap ueber die Tagesreihe
  G2  ZUFALLSKONTROLLE - mit gemischten Raengen muessen alle Stufen
      flach liegen; tun sie das nicht, misst das Verfahren sich selbst
  G3  MONOTONIE MIT BAND - ueberlappen benachbarte Stufen, ist die
      Ordnung nicht belegt
"""
from __future__ import annotations
import sys
import time
import numpy as np
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import messe_eigenschaft_beitrag as B                        # noqa: E402
import messe_kandidaten_als_regel as K                       # noqa: E402
import messe_regel_wirksamkeit as W                          # noqa: E402
import messnorm as N                                         # noqa: E402

H, MARKE, FAECHER = 5, 2.0, 5


def stufen_je_tag(je_tag, marke, mische=None):
    """Je Kalendertag EIN Wert je Fuenftel - das ist die Tagesklammer."""
    reihen = [dict() for _ in range(FAECHER)]
    for tag, z in je_tag.items():
        if len(z) < 3 * FAECHER:
            continue
        w = np.array([x["kennzahl"] for x in z], float)
        y = np.array([x["in_r"] for x in z], float)
        r = W.rang(w)
        if mische is not None:
            r = mische.permutation(r)
        f = np.minimum((r * FAECHER).astype(int), FAECHER - 1)
        basis = float((y > marke).mean())
        for i in range(FAECHER):
            m = f == i
            if m.sum() >= 3:
                reihen[i][tag] = float((y[m] > marke).mean()) - basis
    return reihen


def band(d, block=15, zieh=2000, saat=20260906):
    rng = np.random.default_rng(saat)
    t = sorted(d)
    x = np.array([d[k] for k in t], float)
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
    reihen = B.lade()
    for art in ("vola", "schnitt50"):
        je_tag = K.baue(reihen, art, None, horizont=H)
        print()
        print("=" * 96)
        print("%s — Rand > +%g R, frei, %d Tage" % (art.upper(), MARKE,
                                                    len(je_tag)))
        print("=" * 96)
        for lab, mi in (("ECHT           ", None),
                        ("Zufallskontrolle", np.random.default_rng(4242))):
            rr = stufen_je_tag(je_tag, MARKE, mische=mi)
            werte = []
            print("  %s" % lab)
            for i, d in enumerate(rr):
                b = band(d)
                if b is None:
                    print("    Fuenftel %d   zu wenige Tage" % i); continue
                werte.append(b)
                print("    Fuenftel %d  %+8.4f  [%+8.4f .. %+8.4f]  (%d Tage)"
                      % (i, 100 * b[0], 100 * b[1], 100 * b[2], len(d)),
                      flush=True)
            if len(werte) == FAECHER:
                # Monotonie MIT Band: benachbarte Stufen duerfen sich nicht
                # ueberlappen, sonst ist die Ordnung nicht belegt
                fallend = all(werte[i][1] > werte[i + 1][2]
                              for i in range(FAECHER - 1))
                steigend = all(werte[i][2] < werte[i + 1][1]
                               for i in range(FAECHER - 1))
                getrennt = sum(1 for i in range(FAECHER - 1)
                               if werte[i][1] > werte[i + 1][2]
                               or werte[i][2] < werte[i + 1][1])
                print("    -> %s · %d von 4 Nachbarpaaren getrennt"
                      % ("MONOTON MIT BAND" if (fallend or steigend)
                         else "Ordnung NICHT durchgehend belegt", getrennt))
        print()
    print("  ⚠️ Die Zufallskontrolle MUSS flach liegen. Und die Monotonie")
    print("     gilt nur, wenn benachbarte Baender sich NICHT ueberlappen.")
    print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
