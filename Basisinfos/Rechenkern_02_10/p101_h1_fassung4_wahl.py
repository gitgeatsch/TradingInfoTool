"""P101 Wahl des Instruments fuer Messplan H-1 Fassung 4 - NUR auf kuenstlichen Zustaenden (kein echtes Ergebnis). Nur lesend.

    python -X utf8 Basisinfos/Rechenkern_02_10/p101_h1_fassung4_wahl.py

Anlass: Selbsttest Fassung 2/3 NICHT bestanden (Fehlalarm ~2x Nennniveau, Aufloesung bricht in unverzerrt_3 ein). Ursache gemessen:
Ausreisser (Woelbung D72 958 in unverzerrt_3, ALPACA +537 % in 72 h). Verglichen werden vier Fassungen auf den beiden
auffaelligsten Mengen (bestand, unverzerrt_3): einfache oder Log-Differenz x Perzentil-Bootstrap oder cluster-robustes t-Band.
Vorab-Regel der Wahl: die Fassung mit hoechster mittlerer Fundquote bei 1 Pp UNTER der Bedingung, dass KEIN S1/S2-Wert ueber 5 %
liegt; bei Gleichstand die einfachere (t vor boot, einfach vor log).
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p101_h1_basis as B  # noqa: E402
from p101_h1_selbsttest import quote  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass

FASSUNGEN = (("einfach+boot", False, "boot"), ("log+boot", True, "boot"), ("einfach+t", False, "t"), ("log+t", True, "t"))


def main():
    rng = np.random.default_rng(4)
    print("P101 FASSUNG-4-WAHL · kuenstliche Zustaende auf echten Renditen 2025-26 · kein echtes Ergebnis\n")
    bilanz = {}
    for fname, lg, bd in FASSUNGEN:
        B.LOG, B.BAND = lg, bd
        s12, f1 = [], []
        for menge in ("bestand", "unverzerrt_3"):
            U = B.tabelle(menge)
            U = U[U.jahr >= 2025].reset_index(drop=True)
            for teil, hyps, zst in (("H-1b", B.H1B, "a"), ("H-1c", B.H1C, "extrem")):
                p = float(U[zst].mean())
                for name, lang, kurz in hyps:
                    d = B.delta(U, lang, kurz)
                    ok = np.isfinite(d)
                    tg, dd = U.tag.to_numpy()[ok], d[ok]
                    bb = (tg - tg.min()) // B.N._block(5)
                    n = len(tg)
                    s1 = lambda r, n=n: (r.random(n) < p).astype(float)                       # noqa: E731

                    def s2(r, bb=bb, n=n):
                        ub = np.unique(bb)
                        pb = dict(zip(ub, np.where(r.random(len(ub)) < 0.5, 0.10, 0.50)))
                        return (r.random(n) < np.array([pb[x] for x in bb])).astype(float)
                    q1 = quote(tg, dd, len(hyps), s1, 200, rng, richtung=0)
                    q2 = quote(tg, dd, len(hyps), s2, 100, rng, richtung=0)
                    fu = {k: quote(tg, dd, len(hyps), s1, 50, rng, k=k) for k in (0.005, 0.01, 0.02)}
                    s12 += [q1, q2]
                    f1.append(fu[0.01])
                    print("   %-13s %-13s %s %-5s S1 %4.1f %% · S2 %4.1f %% · Fund 0,5/1/2 Pp %3.0f / %3.0f / %3.0f %%" % (
                        fname, menge, teil, name, 100 * q1, 100 * q2, 100 * fu[0.005], 100 * fu[0.01], 100 * fu[0.02]))
        bilanz[fname] = (max(s12), float(np.mean(s12)), float(np.mean(f1)))
        print("   -> %s: S1/S2 hoechstens %.1f %% (Mittel %.1f %%), Fundquote bei 1 Pp im Mittel %.0f %%\n" % (
            fname, 100 * bilanz[fname][0], 100 * bilanz[fname][1], 100 * bilanz[fname][2]))
    zul = [f for f, _l, _b in FASSUNGEN if bilanz[f][0] <= 0.05]
    reihe = ["einfach+t", "log+t", "einfach+boot", "log+boot"]
    wahl = max(zul, key=lambda f: (round(bilanz[f][2], 2), -reihe.index(f))) if zul else None
    print("WAHL nach Vorab-Regel: %s" % (wahl or "KEINE Fassung haelt S1/S2 <= 5 % - Ursache weiter suchen"))
    return 0 if wahl else 1


if __name__ == "__main__":
    sys.exit(main())
