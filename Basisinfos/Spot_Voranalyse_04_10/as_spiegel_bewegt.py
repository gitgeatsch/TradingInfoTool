"""Vorschlag Spiegelprobe 'bewegungsgleich' (Voranalyse_Spot §19.4) - NUR Selbsttest der Probe, kein Merkmal wird gemessen.

    python Basisinfos/Spot_Voranalyse_04_10/as_spiegel_bewegt.py

Idee: Ein Merkmal, das nur BEWEGUNG misst, hebt mit der Chance (R2) auch das Absturzrisiko (D2). Verglichen wird deshalb mit Bewegungswelten
f = s*(R2+D2) + N(0,1), deren Lift(R2) dem des Merkmals ENTSPRICHT: Besteht, wer bei gleichem Anheben der Chance ein Lift(D2) UNTER dem
2,5. Perzentil dieser Bewegungswelten hat. Gitter s = 0 .. 2,0 in 0,1, je 40 Ziehungen, je Epoche (Lauf 1); Lauf 2 feiner: AS_SCHRITT=0.05 AS_ZIEH=100;
Lauf 3: AS_METHODE=nachbarn (Vergleich mit den 200 Bewegungswelten mit dem naechstliegenden BEOBACHTETEN Lift(R2)).

Selbsttest der Probe:
  (1) frische Bewegungswelten (s 0,15 / 0,3 / 0,6 / 1,0, je 40): duerfen hoechstens zu 2,5 % je Epoche bestehen
  (2) Richtungswelten f = s*R2 + N(0,1) (s 0,15 / 0,3 / 0,6): s 0,3 (der gepflanzte Fall aus as_messung) soll in BEIDEN Epochen bestehen
  (3) Zufallsmerkmale (40): hoechstens 2,5 % je Epoche
"""
import os
import sys

import numpy as np

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
import as_messung as M  # noqa: E402

RNG = np.random.default_rng(20261012)
SCHRITT = float(os.environ.get("AS_SCHRITT", "0.1"))   # Lauf 2: 0.05
ZIEH = int(os.environ.get("AS_ZIEH", "40"))              # Lauf 2: 100
EP = ("E2", "E3")


def gitter(Z, basis):
    g = {}
    for s in np.round(np.arange(0, 2.01, SCHRITT), 2):
        w = {e: [] for e in EP}
        for _ in range(ZIEH):
            o = M.bewerte(Z, s * basis + RNG.normal(size=len(Z.D)), "oben", null=False, ep_liste=EP)
            for e in EP:
                w[e].append((o[e]["lift_r2"], o[e]["lift_d2"]))
        g[s] = {e: np.array(v) for e, v in w.items()}
    return g


METHODE = os.environ.get("AS_METHODE", "mittel")         # Lauf 3: "nachbarn"


def besteht(g, o, e):
    if METHODE == "nachbarn":
        # Lauf 3 (06.10.): Vergleich mit den 200 Bewegungswelten, deren BEOBACHTETES Lift(R2) am naechsten liegt (alle Staerken gepoolt) -
        # die Zuordnung ueber den Mittelwert je Staerke (Lauf 1/2) verglich zufaellig hohe Lifts mit zu starker Bewegung
        pts = np.vstack([g[k][e] for k in g])
        nb = pts[np.argsort(np.abs(pts[:, 0] - o[e]["lift_r2"]))[:200]]
        return o[e]["lift_d2"] < np.percentile(nb[:, 1], 2.5), None
    s = min(g, key=lambda k: abs(g[k][e][:, 0].mean() - o[e]["lift_r2"]))
    return o[e]["lift_d2"] < np.percentile(g[s][e][:, 1], 2.5), s


def main():
    D = M.paare(365).reset_index(drop=True)
    Z = M.Zellen(D)
    bew = Z.r2 + Z.d2
    g = gitter(Z, bew)
    print("Spiegelprobe 'bewegungsgleich' - Selbsttest (§19.4) · %d Coin-Anker\n" % len(D))
    print("Gitter (Mittel Lift R2 / 2,5. Perzentil Lift D2):")
    for s in (0.0, 0.3, 0.6, 1.0, 1.5, 2.0):
        s = min(g, key=lambda k: abs(k - s))
        print("  s %.1f  E2 %.3f / %.3f · E3 %.3f / %.3f" % (s, g[s]["E2"][:, 0].mean(), np.percentile(g[s]["E2"][:, 1], 2.5), g[s]["E3"][:, 0].mean(),
                                                         np.percentile(g[s]["E3"][:, 1], 2.5)))
    for name, basis, st in (("(1) Bewegung", bew, (0.15, 0.3, 0.6, 1.0)), ("(2) Richtung", Z.r2, (0.15, 0.3, 0.6)), ("(3) Zufall", None, (0.0,))):
        for s in st:
            z = {e: 0 for e in EP}; beide = 0
            for _ in range(40):
                f = (s * basis if basis is not None else 0) + RNG.normal(size=len(D))
                o = M.bewerte(Z, f, "oben", null=False, ep_liste=EP)
                b = {e: besteht(g, o, e)[0] for e in EP}
                for e in EP:
                    z[e] += b[e]
                beide += b["E2"] and b["E3"]
            print("  %-13s s %.2f  besteht E2 %3.0f %% · E3 %3.0f %% · beide %3.0f %%" % (name, s, 100 * z["E2"] / 40, 100 * z["E3"] / 40, 100 * beide / 40))


if __name__ == "__main__":
    main()
